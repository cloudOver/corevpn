"""
Copyright (c) 2014 Maciej Nabozny

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

from corecluster.utils.decorators import register
from corecluster.models.vpn.connection import Connection
from corecluster.models.core.vm import VM
from corecluster.utils.exception import CoreException

@register(auth="node")
def get_connection(context, vm_name):
    try:
        vm_id = vm_name[3:]
        vm = VM.objects.filter(node=context.node).get(pk=vm_id)
    except:
        context.log.debug("Unknown vm from hook: %s" % vm_name)
        raise CoreException('vm_not_found')

    try:
        connections = Connection.objects.filter(vm=vm)
        return [conn.to_dict for conn in connections]
    except:
        raise CoreException('vm_not_attached')