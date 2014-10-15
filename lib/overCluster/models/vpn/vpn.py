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

    port = models.IntegerField(null=True, help_text='Port used to estabilish connection between node and network node')
    #network = models.ForeignKey('AvailableNetwork')

    ca_crt = models.TextField(null=True)
    client_key = models.TextField(null=True)
    client_crt = models.TextField(null=True)

    openvpn_pid = models.IntegerField(null=True)

    serializable = ['id', 'state', 'port', 'ca_crt', 'client_crt']