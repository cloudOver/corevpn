"""
Copyright (c) 2014 Maciej Nabozny
              2016 Marta Nabozny

This file is part of CloudOver project.

CloudOver is free software: you can redistribute it and/or modify
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

from corecluster.agents.base_agent import BaseAgent
from corenetwork.utils import system
from corevpn.models.vpn import VPN

import imp
import os
import time


coreVpnConf = imp.load_source('vpnConfig', '/etc/corevpn/config.py')


class AgentThread(BaseAgent):
    task_type = 'vpn'
    supported_actions = ['create', 'delete']

    #TODO: This may be harmful on multi-agent environments. Rewrite it with broadcast tasks
    # def init(self):
    #     super(AgentThread, self).init()
    #     for vpn in VPN.objects.filter(state='suspended').all():
    #         self.mk_openvpn(vpn)
    #         vpn.set_state('running')
    #         vpn.save()
    #
    #
    # def cleanup(self):
    #     for vpn in VPN.objects.filter(state='running').all():
    #         vpn.set_state('suspended')
    #         try:
    #             system.call(['sudo', 'kill', '-15', str(vpn.openvpn_pid)])
    #         except:
    #             pass
    #         vpn.save()
    #     super(AgentThread, self).cleanup()


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

        system.call(['openssl',
                     'genrsa',
                     '-out', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id,
                     str(coreVpnConf.CA_KEY_SIZE)])

        system.call(['openssl',
                     'req',
                     '-x509',
                     '-new',
                     '-nodes',
                     '-key', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id,
                     '-days', str(coreVpnConf.CERTIFICATE_LIFETIME),
                     '-out', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % vpn.id,
                     '-subj', '/CN=CoreVpn-%s/O=CloudOver/OU=CoreVpn' % vpn.id])

        vpn.ca_crt = open('/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % vpn.id, 'r').read(1024*1024)
        vpn.save()


    def mk_cert(self, vpn, key_name):
        if not os.path.exists('/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id):
            raise Exception('vpn_root_ca_not_found')

        # Create key
        system.call(['openssl',
                     'genrsa',
                     '-out', '/var/lib/cloudOver/coreVpn/certs/%s/%s.key' % (vpn.id, key_name),
                     str(coreVpnConf.CLIENT_KEY_SIZE)])

        # Create certificate sign request
        system.call(['openssl',
                     'req',
                     '-new',
                     '-key', '/var/lib/cloudOver/coreVpn/certs/%s/%s.key' % (vpn.id, key_name),
                     '-out', '/var/lib/cloudOver/coreVpn/certs/%s/%s.csr' % (vpn.id, key_name),
                     '-subj', '/CN=%s/O=CloudOver/OU=CoreVpn/' % key_name])

        system.call(['openssl',
                     'x509',
                     '-req',
                     '-in', '/var/lib/cloudOver/coreVpn/certs/%s/%s.csr' % (vpn.id, key_name),
                     '-CA', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % vpn.id,
                     '-CAkey', '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id,
                     '-CAcreateserial',
                     '-out', '/var/lib/cloudOver/coreVpn/certs/%s/%s.crt' % (vpn.id, key_name),
                     '-days', str(coreVpnConf.CERTIFICATE_LIFETIME)])


    def mk_dh(self, vpn):
        system.call(['openssl',
                         'dhparam',
                         '-out', '/var/lib/cloudOver/coreVpn/certs/%s/dh1024.pem' % vpn.id,
                         '1024'])

    def mk_openvpn(self, vpn, network):
        p = system.Popen(['sudo',
                          'openvpn',
                          '--user', 'cloudover',
                          '--dev', vpn.interface_name,
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

        for i in xrange(60):
            if not os.path.exists('/sys/class/net/' + vpn.interface_name):
                time.sleep(1)
                continue
            else:
                system.call(['sudo', 'ip'
                             'link',
                             'set', vpn.interface_name,
                             'netns', network.netns_name])
                break


    def create(self, task):
        network = task.obj_get('Subnet')
        vpn = task.obj_get('VPN')

        vpn.set_state('init')
        vpn.save()

        # Create CA
        self.mk_ca(vpn)
        self.mk_cert(vpn, 'server')
        self.mk_cert(vpn, 'client')

        vpn.client_crt = open('/var/lib/cloudOver/coreVpn/certs/%s/client.crt' % (vpn.id), 'r').read(1024*1024)
        vpn.client_key = open('/var/lib/cloudOver/coreVpn/certs/%s/client.key' % (vpn.id), 'r').read(1024*1024)

        self.mk_dh(vpn)

        port = coreVpnConf.PORT_BASE
        used_ports = []
        for v in VPN.objects.filter(state__in=['running', 'init']):
            used_ports.append(v.port)

        while port in used_ports and port < 10000:
            port = port + 1

        vpn.port = port
        self.mk_openvpn(vpn, network)

        vpn.set_state('running')
        vpn.save()


    def delete(self, task):
        vpn = VPN.objects.get(pk=task.get_prop('vpn_id'))

        vpn.set_state('removing')
        vpn.save()
        try:
            system.call(['sudo', 'kill', '-15', str(vpn.openvpn_pid)])
        except:
            pass
        system.call('rm -rf /var/lib/cloudOver/coreVpn/certs/%s' % vpn.id, shell=True)

        vpn.set_state('removed')
        vpn.save()
