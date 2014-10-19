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

from overCluster.utils.decorators import ci_log
from overCluster.utils import log
from overCluster.models.vpn.connection import Connection
from overCluster.models.vpn.vpn import VPN
from overCluster.models.core.vm import VM
from overCluster.models.core.node import Node
from overCluster.utils.exception import CMException

@ci_log(log=True)
def get_certs(remote_ip, auth_hash, auth_seed, vm_name):
    try:
        node = Node.objects.get(address=remote_ip)
        node.check_auth(auth_hash, auth_seed)
    except:
        raise CMException('node_not_found')


    try:
        user_id = int(vm_name.split('-')[1])
        vm_id = int(vm_name.split('-')[2])

        vm = VM.objects.filter(user_id=user_id).filter(node=node).get(pk=vm_id)
    except:
        log.debug(0, "Unknown vm from hook: %s" % vm_name)
        raise CMException('vm_not_found')

    connection = Connection.objects.get(vm=vm)
    return connection.to_dict