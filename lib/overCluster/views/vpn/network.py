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

import netaddr

from overCluster.utils.decorators import register
from overCluster.models.vpn.vpn import VPN
from overCluster.models.vpn.connection import Connection
from overCluster.models.core.available_network import AvailableNetwork
from overCluster.models.core.task import Task
from overCluster.models.core.vm import VM
from overCluster.utils.exception import CMException


@register(auth='token')
def create(context, address, mask):
    """ Create new isolated, vpn based network. Address and mask are only for user information. There is no dhcp in
    such network

    :param address: Network address
    :param mask: Network mask
    """

    try:
        netaddr.IPAddress(address)
        ipnet = netaddr.IPNetwork(address + '/' + mask)
    except:
        raise CMException('network_format_invalid')

    network = AvailableNetwork()
    network.address = str(ipnet.network)
    network.mask = ipnet.prefixlen
    network.mode = 'isolated'
    network.state = 'ok'
    network.save()

    vpn = VPN()
    vpn.state = 'init'
    vpn.user = context.user
    vpn.network = network
    vpn.save()

    task = Task()
    task.state = 'not active'
    task.set_prop('vpn_id', vpn.id)
    task.type = 'vpn'
    task.action = 'create'
    task.addAfter(Task.objects.filter(type='vpn'))

    return vpn.to_dict


@register(auth='token')
def delete(context, vpn_id):
    """ Delete vpn network """
    vpn = VPN.get(context.user_id, vpn_id)

    task = Task()
    task.state = 'not active'
    task.set_prop('vpn_id', vpn.id)
    task.type = 'vpn'
    task.action = 'delete'
    task.addAfter(Task.objects.filter(type='vpn'))


@register(auth='token')
def attach(context, vpn_id, vm_id):
    """  """
    vpn = VPN.get(context.user_id, vpn_id)
    vm = VM.get(context.user_id, vm_id)

    if not vpn.in_state('running'):
        raise CMException('network_not_running')

    if not vm.in_state('stopped'):
        raise CMException('vm_not_stopped')

    connection = Connection()
    connection.vm = vm
    connection.vpn = vpn
    connection.user = context.user
    connection.save()

    task = Task()
    task.vm = vm
    task.state = 'not active'
    task.set_prop('connection_id', connection.id)
    task.type = 'vpn'
    task.action = 'attach'
    task.addAfter(Task.objects.filter(type__in=['vpn']))

    return connection.to_dict


@register(auth='token')
def detach(context, connection_id):
    connection = Connection.get(context.user_id, connection_id)

    task = Task()
    task.vm = connection.vm
    task.state = 'not active'
    task.set_prop('connection_id', connection.id)
    task.type = 'vpn'
    task.action = 'detach'
    task.addAfter(Task.objects.filter(type__in=['vpn']))


@register(auth='token')
def get_list(context):
    return [v.to_dict for v in VPN.objects.filter(user=context.user).exclude(state='removed').all()]


@register(auth='token')
def get_by_id(context, vpn_id):
    return VPN.get(context.user_id, vpn_id).to_dict


@register(auth='token')
def get_connection_list(context, vpn_id):
    """ List all connections related to given vpn """
    vpn = VPN.get(context.user_id, vpn_id)
    return [v.to_dict for v in vpn.connection_set.all()]


@register(auth='token')
def client_cert(context, vpn_id):
    vpn = VPN.get(context.user_id, vpn_id)
    return {'cert': vpn.client_crt, 'key': vpn.client_key, 'ca_cert': vpn.ca_crt}
