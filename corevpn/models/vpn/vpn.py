"""
Copyright (c) 2014-2015 Maciej Nabozny
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

from django.db import models

from corecluster.models.common_models import CoreModel, UserMixin, StateMixin
from corecluster.models.core import Subnet
from corecluster.settings import networkConfig


class VPN(StateMixin, UserMixin, CoreModel):
    states = [
        'init',         # VPN is beeing created
        'running',      # VPN is running
        'suspended',    # VPN is suspended (vpn agent is not running or was stopped)
        'failed',       # VPN failed
        'removing',     # VPN is beeing removed
        'removed',      # VPN is not running and was cleaned up
    ]
    default_state = 'init'

    address = models.CharField(max_length=256, help_text='Endpoint address')
    port = models.IntegerField(null=True, help_text='Port used to establish connection between node and network node')
    name = models.CharField(max_length=256)
    network = models.ForeignKey(Subnet)


    ca_crt = models.TextField(null=True)
    client_key = models.TextField(null=True)
    client_crt = models.TextField(null=True)

    openvpn_pid = models.IntegerField(null=True)

    serializable = ['id', 'state', 'port', 'ca_crt', 'client_crt', 'access', 'name', 'network_id']
    editable = ['name', ['access', lambda x: x in UserMixin.object_access], ]

    def network_info(self):
        return self.network.to_dict


    @property
    def interface_name(self):
        return str('cv-%s' % self.id)[:networkConfig.IFACE_NAME_LENGTH]


    @property
    def ca_crt_file(self):
        return '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.crt' % self.id


    @property
    def ca_key_file(self):
        return '/var/lib/cloudOver/coreVpn/certs/%s/rootCA.key' % self.id


    @property
    def server_crt_file(self):
        return '/var/lib/cloudOver/coreVpn/certs/%s/server.crt' % self.id


    @property
    def server_key_file(self):
        return '/var/lib/cloudOver/coreVpn/certs/%s/server.key' % self.id


    @property
    def dh_file(self):
        return '/var/lib/cloudOver/coreVpn/certs/%s/dh1024.pem' % self.id


    @property
    def config_file(self):
        return '/var/lib/cloudOver/coreVpn/certs/%s/server.conf' % self.id