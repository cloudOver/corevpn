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
from corecluster.utils.logger import *
from corenetwork.utils import system
from corenetwork.utils.renderer import render
from corevpn.models.vpn import VPN
import django.conf

import imp
import os
import time


coreVpnConf = imp.load_source('vpnConfig', '/etc/corevpn/config.py')


class AgentThread(BaseAgent):
    task_type = 'vpn'
    supported_actions = ['create', 'delete']

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

        if os.path.exists(vpn.ca_key_file):
            raise Exception('vpn_exists')

        if vpn.ca_crt != '' and vpn.ca_crt != None:
            raise Exception('vpn_ca_exists')

        system.call(['openssl',
                     'genrsa',
                     '-out', vpn.ca_key_file,
                     str(coreVpnConf.CA_KEY_SIZE)])

        system.call(['openssl',
                     'req',
                     '-x509',
                     '-new',
                     '-nodes',
                     '-key', vpn.ca_key_file,
                     '-days', str(coreVpnConf.CERTIFICATE_LIFETIME),
                     '-out', vpn.ca_crt_file,
                     '-subj', '/CN=CoreVpn-%s/O=CloudOver/OU=CoreVpn' % vpn.id])

        vpn.ca_crt = open(vpn.ca_crt_file, 'r').read(1024*1024)
        vpn.save()


    def mk_cert(self, vpn, type='client'):
        if not os.path.exists('/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % vpn.id):
            raise Exception('vpn_root_ca_not_found')

        # Create key
        system.call(['openssl',
                     'genrsa',
                     '-out', vpn.server_key_file,
                     str(coreVpnConf.CLIENT_KEY_SIZE)])

        # Create certificate sign request
        system.call(['openssl',
                     'req',
                     '-new',
                     '-key', vpn.server_key_file,
                     '-out', vpn.server_key_file + '.csr',
                     '-subj', '/CN=server/O=CloudOver/OU=CoreVpn/'])

        system.call(['openssl',
                     'x509',
                     '-req',
                     '-in', vpn.server_key_file + '.csr',
                     '-CA', vpn.ca_crt_file,
                     '-CAkey', vpn.ca_key_file,
                     '-CAcreateserial',
                     '-out', vpn.server_crt_file,
                     '-days', str(coreVpnConf.CERTIFICATE_LIFETIME)])


    def mk_dh(self, vpn):
        system.call(['openssl',
                     'dhparam',
                     '-out', vpn.dh_file,
                     '1024'])


    def mk_config(self, vpn, network):
        try:
            django.conf.settings.configure({'TEMPLATE_DIRS': (
                '/etc/corecluster/templates/',
                '/etc/corenetwork/drivers/',
                '/etc/corevpn/',
            )})
        except:
            pass
        config = render('openvpn.template', {'vpn': vpn, 'network': network})
        f = open(vpn.config_file, 'w')
        f.write(config)
        f.close()


    def mk_openvpn(self, vpn, network):
        p = system.call(['sudo',
                          'openvpn',
                          '--config', vpn.config_file], background=True)
        vpn.openvpn_pid = p
        vpn.save()

        for i in xrange(60):
            if not os.path.exists('/sys/class/net/' + vpn.interface_name):
                time.sleep(1)
                continue
            else:
                system.call(['sudo',
                             'ip',
                             'link',
                             'set', vpn.interface_name,
                             'netns', network.netns_name])
                break


    def create(self, task):
        network = task.get_obj('Subnet')
        vpn = task.get_obj('VPN')

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
        vpn = task.get_obj('VPN')

        vpn.set_state('removing')
        vpn.save()
        try:
            #TODO: Check if this is openvpn process
            pid = int(open('/var/lib/cloudOver/coreVpn/%s.pid' % vpn.id, 'r').read(1024))
            system.call(['sudo', 'kill', '-15', str(pid)])
        except Exception as e:
            syslog(msg='Failed to kill openvpn process', exception=e)

        system.call('rm -rf /var/lib/cloudOver/coreVpn/certs/%s' % vpn.id, shell=True)

        try:
            os.remove('/var/lib/cloudOver/coreVpn/%s.pid' % vpn.id)
        except:
            syslog(msg='Failed to remove pid file', loglevel=LOG_ERR)

        vpn.set_state('removed')
        vpn.save()
