"""
Copyright (c) 2016 Marta Nabozny

This file is part of CoreCluster project.

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

from corenetwork.network_mixin import NetworkMixin
from corenetwork.os_mixin import OsMixin
from corenetwork.api_mixin import ApiMixin
from corenetwork.config_mixin import ConfigMixin
from corenetwork.hook_interface import HookInterface
from corecluster.cache.task import Task


class Hook(NetworkMixin, OsMixin, ApiMixin, ConfigMixin, HookInterface):
    task = None

    def finish(self):
        super(Hook, self).finish()
        vpn = self.task.get_obj('VPN')
        task = Task()
        task.type = 'vpn'
        task.action = 'delete'
        task.append_to([vpn])
