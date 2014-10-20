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

from overCluster.models.core.available_network import AvailableNetwork
from overCluster.models.common_models import CoreModel, UserMixin, StateMixin
from django.db import models


class Connection(StateMixin, UserMixin, CoreModel):
    states = [
        'init',
        'running',
        'closing',
        'closed',
    ]
    default_state = 'init'

    vpn = models.ForeignKey('VPN')
    vm = models.ForeignKey('VM', null=True, blank=True)
    client_key = models.TextField(null=True)
    client_crt = models.TextField(null=True)

    def ca_crt(self):
        return self.vpn.ca_crt

    def port(self):
        return self.vpn.port

    serializable = ['id', 'state', 'vpn', 'vm_id', 'client_key', 'client_crt', ['ca_crt', 'ca_crt'], ['port', 'port']]