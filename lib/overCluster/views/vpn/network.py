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

from overCluster.utils.decorators import api_log
from overCluster.models.vpn.vpn import VPN
from overCluster.models.vpn.connection import Connection
from overCluster.models.core.available_network import AvailableNetwork
from overCluster.models.core.user import User
from overCluster.models.core.task import Task
from overCluster.models.core.vm import VM
from overCluster.utils.exception import CMException


@api_log(log=True)
def create(caller_id, address, mask):
    """ Create new isolated, vpn based network. Address and mask are only for user information. There is no dhcp in
    such network

    :param address: Network address
    :param mask: Network mask
    """
    user = User.get(caller_id)

    vpn = VPN()
    vpn.state = 'init'
    vpn.user = user
    vpn.save()

    task = Task()
    task.state = 'not active'
    task.set_prop('vpn_id', vpn.id)
    task.type = 'vpn'
    task.action = 'create'
    task.addAfter(Task.objects.filter(type='vpn'))

    return vpn.to_dict


@api_log(log=True)
def delete(caller_id, vpn_id):
    """ Delete vpn network """
    an = VPN.get(caller_id, vpn_id)

    if an.mode != 'isolated':
        raise CMException('network_not_isolated')

    if an.state != 'ok':
        raise CMException('network_not_running')

    task = Task()
    task.state = 'not active'
    task.set_prop('vpn_id', vpn_id)
    task.type = 'vpn'
    task.action = 'delete'
    task.addAfter(Task.objects.filter(type='vpn'))


@api_log(log=True)
def attach(caller_id, vpn_id, vm_id):
    """  """
    vpn = VPN.get(caller_id, vpn_id)
    vm = VM.get(caller_id, vm_id)

    if vpn.mode != 'isolated':
        raise CMException('network_not_isolated')

    if vpn.state != 'ok':
        raise CMException('network_not_running')

    task = Task()
    task.vm = vm
    task.state = 'not active'
    task.set_prop('vpn_id', vpn_id)
    task.type = 'vpn'
    task.action = 'attach'
    task.addAfter(Task.objects.filter(type='vpn'))


@api_log(log=True)
def detach(caller_id, network_id, vm_id):
    vpn = VPN.get(caller_id, network_id)
    vm = VM.get(caller_id, vm_id)

    if vpn.mode != 'isolated':
        raise CMException('network_not_isolated')

    if vpn.state != 'ok':
        raise CMException('network_not_running')

    task = Task()
    task.vm = vm
    task.state = 'not active'
    task.set_prop('vpn_network', network_id)
    task.type = 'vpn'
    task.action = 'detach'
    task.addAfter(Task.objects.filter(type='vpn'))

@api_log(log=True)
def get_client_cert(caller_id, vpn_id):
    vpn = VPN.get(caller_id, vpn_id)
    return {'cert': vpn.client_crt, 'key': vpn.client_key, 'ca_cert': vpn.ca_crt}