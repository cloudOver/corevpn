"""
Copyright (c) 2014 Maciej Nabozny

This file is part of OverCluster project.

OverCluster is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import signal

from overCluster.agents.base_agent import BaseAgent
from overCluster.models.vpn.vpn import VPN
from overCluster.models.vpn.connection import Connection
import subprocess
import signal
import sys
import os

class AgentThread(BaseAgent):
    task_type = 'vpn'
    supported_actions = ['create', 'delete', 'attach', 'detach']

    def init(self):
        for vpn in VPN.objects.filter(state='suspended').all():
            self.mk_openvpn(vpn)
            vpn.set_state('running')
            vpn.save()


    def cleanup(self):
        for vpn in VPN.objects.filter(state='running').all():
            vpn.set_state('suspended')
            try:
                os.kill(vpn.openvpn_pid, signal.SIGTERM)
            except:
                pass
            vpn.save()


    def task_failed(self, task, exception):
        try:
            vpn = VPN.objects.get(pk=int(task.get_prop('vpn_id')))
            vpn.set_state('failed')
            vpn.save()
        except:
            pass

        BaseAgent.task_failed(self, task, exception)

    def mk_ca(self, vpn):
        if not os.path.exists('/var/lib/cloudOver/coreVpn/certs/%d' % vpn.id):
            os.mkdir('/var/lib/cloudOver/coreVpn/certs/%d' % vpn.id)

        if os.path.exists('/var/lib/cloudOver/coreVpn/certs/%d/rootCA.key' % vpn.id):
            raise Exception('vpn_exists')

        if vpn.ca_crt != '' and vpn.ca_crt != None:
            raise Exception('vpn_ca_exists')

        subprocess.call(['openssl',
                         'genrsa',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%d/rootCA.key' % vpn.id,
                         '2048'])

        subprocess.call(['openssl',
                         'req',
                         '-x509',
                         '-new',
                         '-nodes',
                         '-key', '/var/lib/cloudOver/coreVpn/certs/%d/rootCA.key' % vpn.id,
                         '-days', '3650',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%d/rootCA.crt' % vpn.id,
                         '-subj', '/CN=CoreVpn-%d/O=CloudOver/OU=CoreVpn' % vpn.id])

        vpn.ca_crt = open('/var/lib/cloudOver/coreVpn/certs/%d/rootCA.crt' % vpn.id, 'r').read(1024*1024)
        vpn.save()


    def mk_cert(self, vpn, key_name):
        if not os.path.exists('/var/lib/cloudOver/coreVpn/certs/%d/rootCA.key' % vpn.id):
            raise Exception('vpn_root_ca_not_found')

        # Create key
        subprocess.call(['openssl',
                         'genrsa',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%d/%s.key' % (vpn.id, key_name),
                         '2048'])

        # Create certificate sign request
        subprocess.call(['openssl',
                         'req',
                         '-new',
                         '-key', '/var/lib/cloudOver/coreVpn/certs/%d/%s.key' % (vpn.id, key_name),
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%d/%s.csr' % (vpn.id, key_name),
                         '-subj', '/CN=%s-vpn-%d/O=CloudOver/OU=CoreVpn' % (key_name, vpn.id)])

        subprocess.call(['openssl',
                         'x509',
                         '-req',
                         '-in', '/var/lib/cloudOver/coreVpn/certs/%d/%s.csr' % (vpn.id, key_name),
                         '-CA', '/var/lib/cloudOver/coreVpn/certs/%d/rootCA.crt' % vpn.id,
                         '-CAkey', '/var/lib/cloudOver/coreVpn/certs/%d/rootCA.key' % vpn.id,
                         '-CAcreateserial',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%d/%s.crt' % (vpn.id, key_name),
                         '-days', '3650'])


    def mk_dh(self, vpn):
        subprocess.call(['openssl',
                         'dhparam',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%d/dh1024.pem' % vpn.id,
                         '1024'])

    def mk_openvpn(self, vpn):
        p = subprocess.Popen(['sudo',
                              'openvpn',
                              '--user', 'cloudover',
                              '--dev', 'corevpn%d' % vpn.id,
                              '--dev-type', 'tap',
                              '--persist-tun',
                              '--mode', 'server',
                              '--persist-key',
                              '--ping', '10',
                              '--ping-restart', '60',
                              '--tls-server',
                              '--port', str(vpn.port),
                              '--dh', '/var/lib/cloudOver/coreVpn/certs/%d/dh1024.pem' % vpn.id,
                              '--ca', '/var/lib/cloudOver/coreVpn/certs/%d/rootCA.crt' % vpn.id,
                              '--cert', '/var/lib/cloudOver/coreVpn/certs/%d/server.crt' % vpn.id,
                              '--key', '/var/lib/cloudOver/coreVpn/certs/%d/server.key' % vpn.id,
                              '--client-to-client',
                              '--topology', 'p2p'])
        vpn.openvpn_pid = p.pid


    def create(self, task):
        vpn = VPN.objects.select_for_update().get(pk=int(task.get_prop('vpn_id')))
        vpn.set_state('init')
        vpn.save()

        # Create CA
        self.mk_ca(vpn)
        self.mk_cert(vpn, 'server')
        self.mk_cert(vpn, 'client')

        vpn.client_crt = open('/var/lib/cloudOver/coreVpn/certs/%d/client.crt' % (vpn.id), 'r').read(1024*1024)
        vpn.client_key = open('/var/lib/cloudOver/coreVpn/certs/%d/client.key' % (vpn.id), 'r').read(1024*1024)

        self.mk_dh(vpn)


        port = 1194
        used_ports = []
        for v in VPN.objects.filter(state__in=['running', 'init']):
            used_ports.append(v.port)
        while port in used_ports and port < 10000:
            port = port + 1

        vpn.port = port
        self.mk_openvpn(vpn)

        vpn.set_state('running')
        vpn.save()


    def delete(self, task):
        vpn = VPN.objects.get(pk=int(task.get_prop('vpn_id')))
        if Connection.objects.filter(vpn=vpn).count() > 0:
            raise Exception('vpn_attached')

        vpn.set_state('removing')
        vpn.save()
        try:
            os.kill(vpn.openvpn_pid, signal.SIGTERM)
        except:
            pass
        subprocess.call('rm -rf /var/lib/cloudOver/coreVpn/certs/%d' % vpn.id, shell=True)

        vpn.set_state('removed')
        vpn.save()


    def attach(self, task):
        vpn = VPN.objects.get(pk=int(task.get_prop('vpn_id')))

        if task.vm.state != 'running':
            raise Exception('vpn_vm_not_running')

        key_name = 'vm-%d' % task.vm.id
        self.mk_cert(vpn, key_name)

        conn = Connection()
        conn.set_state('init')
        conn.vpn = vpn
        conn.vm = task.vm
        conn.client_key = open('/var/lib/cloudOver/coreVpn/certs/%d/%s.key' % (vpn.id, key_name), 'r').read(1024*1024)
        conn.client_crt = open('/var/lib/cloudOver/coreVpn/certs/%d/%s.crt' % (vpn.id, key_name), 'r').read(1024*1024)
        conn.save()


    def detach(self, task):
        pass