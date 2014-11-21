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
import os

class AgentThread(BaseAgent):
    task_type = 'vpn'
    supported_actions = ['create', 'delete', 'attach', 'detach']

    def init(self):
        super(AgentThread, self).init()
        for vpn in VPN.objects.filter(state='suspended').all():
            self.mk_openvpn(vpn)
            vpn.set_state('running')
            vpn.save()


    def cleanup(self):
        for vpn in VPN.objects.filter(state='running').all():
            vpn.set_state('suspended')
            try:
                subprocess.call(['sudo', 'kill', '-15', str(vpn.openvpn_pid)])
            except:
                pass
            vpn.save()
        super(AgentThread, self).cleanup()


    def task_failed(self, task, exception):
        try:
            vpn = VPN.objects.get(pk=task.get_prop('vpn_id'))
            vpn.set_state('failed')
            vpn.save()
        except:
            pass

        BaseAgent.task_failed(self, task, exception)

    def mk_ca(self, vpn):
        if not os.path.exists('/var/lib/cloudOver/coreVpn/certs/%s' % vpn.id):
            os.mkdir('/var/lib/cloudOver/coreVpn/certs/%s' % vpn.id)

        if os.path.exists('/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id):
            raise Exception('vpn_exists')

        if vpn.ca_crt != '' and vpn.ca_crt != None:
            raise Exception('vpn_ca_exists')

        subprocess.call(['openssl',
                         'genrsa',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id,
                         '2048'])

        subprocess.call(['openssl',
                         'req',
                         '-x509',
                         '-new',
                         '-nodes',
                         '-key', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id,
                         '-days', '3650',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % vpn.id,
                         '-subj', '/CN=CoreVpn-%s/O=CloudOver/OU=CoreVpn' % vpn.id])

        vpn.ca_crt = open('/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % vpn.id, 'r').read(1024*1024)
        vpn.save()


    def mk_cert(self, vpn, key_name):
        if not os.path.exists('/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id):
            raise Exception('vpn_root_ca_not_found')

        # Create key
        subprocess.call(['openssl',
                         'genrsa',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%s/%s.key' % (vpn.id, key_name),
                         '2048'])

        # Create certificate sign request
        subprocess.call(['openssl',
                         'req',
                         '-new',
                         '-key', '/var/lib/cloudOver/coreVpn/certs/%s/%s.key' % (vpn.id, key_name),
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%s/%s.csr' % (vpn.id, key_name),
                         '-subj', '/CN=%s-vpn-%s/O=CloudOver/OU=CoreVpn' % (key_name, vpn.id)])

        subprocess.call(['openssl',
                         'x509',
                         '-req',
                         '-in', '/var/lib/cloudOver/coreVpn/certs/%s/%s.csr' % (vpn.id, key_name),
                         '-CA', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % vpn.id,
                         '-CAkey', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id,
                         '-CAcreateserial',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%s/%s.crt' % (vpn.id, key_name),
                         '-days', '3650'])


    def mk_dh(self, vpn):
        subprocess.call(['openssl',
                         'dhparam',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%s/dh1024.pem' % vpn.id,
                         '1024'])

    def mk_openvpn(self, vpn):
        p = subprocess.Popen(['sudo',
                              'openvpn',
                              '--user', 'cloudover',
                              '--dev', 'corevpn%s' % vpn.id[:6],
                              '--dev-type', 'tap',
                              '--persist-tun',
                              '--mode', 'server',
                              '--persist-key',
                              '--ping', '10',
                              '--ping-restart', '60',
                              '--tls-server',
                              '--proto', 'tcp-server',
                              '--port', str(vpn.port),
                              '--log', '/var/lib/cloudOver/coreVpn/certs/%s/vpn.log' % vpn.id,
                              '--dh', '/var/lib/cloudOver/coreVpn/certs/%s/dh1024.pem' % vpn.id,
                              '--ca', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % vpn.id,
                              '--cert', '/var/lib/cloudOver/coreVpn/certs/%s/server.crt' % vpn.id,
                              '--key', '/var/lib/cloudOver/coreVpn/certs/%s/server.key' % vpn.id,
                              '--client-to-client',
                              '--topology', 'p2p'])
        vpn.openvpn_pid = p.pid


    def create(self, task):
        vpn = VPN.objects.select_for_update().get(pk=task.get_prop('vpn_id'))
        vpn.set_state('init')
        vpn.save()

        # Create CA
        self.mk_ca(vpn)
        self.mk_cert(vpn, 'server')
        self.mk_cert(vpn, 'client')

        vpn.client_crt = open('/var/lib/cloudOver/coreVpn/certs/%s/client.crt' % (vpn.id), 'r').read(1024*1024)
        vpn.client_key = open('/var/lib/cloudOver/coreVpn/certs/%s/client.key' % (vpn.id), 'r').read(1024*1024)

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
        vpn = VPN.objects.get(pk=task.get_prop('vpn_id'))
        if Connection.objects.filter(vpn=vpn).count() > 0:
            raise Exception('vpn_attached')

        vpn.set_state('removing')
        vpn.save()
        try:
            subprocess.call(['sudo', 'kill', '-15', str(vpn.openvpn_pid)])
        except:
            pass
        subprocess.call('rm -rf /var/lib/cloudOver/coreVpn/certs/%s' % vpn.id, shell=True)

        vpn.set_state('removed')
        vpn.save()


    def attach(self, task):
        connection = Connection.objects.get(pk=task.get_prop('connection_id'))

        if not connection.vm.in_state('stopped'):
            raise Exception('vm_vm_not_stopped')

        if not connection.vpn.in_state('running'):
            raise Exception('vpn_not_running')

        if not connection.in_state('init') or connection.client_key != None or connection.client_crt != None:
            raise Exception('connection_in_use')

        key_name = 'vm-%s' % connection.vm.id
        self.mk_cert(connection.vpn, key_name)

        connection.client_key = open('/var/lib/cloudOver/coreVpn/certs/%s/%s.key' % (connection.vpn.id, key_name), 'r').read(1024*1024)
        connection.client_crt = open('/var/lib/cloudOver/coreVpn/certs/%s/%s.crt' % (connection.vpn.id, key_name), 'r').read(1024*1024)
        connection.set_state('running')
        connection.save()


    def detach(self, task):
        conn = Connection.objects.get(pk=task.get_prop('connection_id'))
        conn.set_state('closing')
        conn.save()
