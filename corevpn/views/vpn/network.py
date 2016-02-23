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

from corecluster.utils import validation as v
from corecluster.utils.decorators import register
from corecluster.utils.exception import CoreException
from corecluster.cache.task import Task
from corecluster.models.core import Subnet

from corevpn.models.vpn.vpn import VPN


@register(auth='token', validate={'name': v.is_string()})
def create(context, name, network_id):
    """
    Create new vpn server attached to isolated network. There is no dhcp
    :param name: Network name
    :param network_id: Isolated network, which should be connected with new VPN server
    """

    network = Subnet.get(context.user_id, network_id)
    if network.network_pool.mode != 'isolated':
        raise CoreException('network_not_isolated')

    vpn = VPN()
    vpn.state = 'init'
    vpn.name = name
    vpn.network = Subnet.get(context.user_id, network_id)
    vpn.user_id = context.user_id
    vpn.save()

    task = Task()
    task.type = 'vpn'
    task.action = 'create'
    task.append_to([vpn, network])

    return vpn.to_dict


@register(auth='token', validate={'vpn_id': v.is_id()})
def delete(context, vpn_id):
    """ Delete vpn network """
    vpn = VPN.get(context.user_id, vpn_id)

    task = Task()
    task.type = 'vpn'
    task.action = 'delete'
    task.append_to([vpn], broadcast=True)


@register(auth='token')
def get_list(context):
    return [v.to_dict for v in VPN.get_list(context.user_id)]


@register(auth='token', validate={'vpn_id': v.is_id()})
def get_by_id(context, vpn_id):
    return VPN.get(context.user_id, vpn_id).to_dict


@register(auth='token', validate={'vpn_id': v.is_id()})
def client_cert(context, vpn_id):
    vpn = VPN.get(context.user_id, vpn_id)
    return {'cert': vpn.client_crt, 'key': vpn.client_key, 'ca_cert': vpn.ca_crt}
