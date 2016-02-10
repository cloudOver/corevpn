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

from django.db.models import Q

from overClusterConf import config as coreConf
from corecluster.utils import validation as v
from corecluster.utils.decorators import register
from corecluster.utils.exception import CoreException
from corecluster.models.vpn.vpn import VPN
from corecluster.models.vpn.connection import Connection
from corecluster.models.core.task import Task
from corecluster.models.core.vm import VM


@register(auth='token', validate={'name': v.is_string()})
def create(context, name):
    """ Create new isolated, vpn based network. Address and mask are only for user information. There is no dhcp in
    such network

    :param address: Network address
    :param mask: Network mask
    """

    vpn = VPN()
    vpn.state = 'init'
    vpn.name = name
    vpn.user_id = context.user_id
    vpn.save()

    task = Task()
    task.state = 'not active'
    task.set_prop('vpn_id', vpn.id)
    task.type = 'vpn'
    task.action = 'create'
    task.addAfter(Task.objects.filter(type='vpn').\
                               exclude(Q(state='ok') | Q(state='canceled') | Q(state='failed')).\
                               all())
    task.addAfter(Task.objects.filter(type='vpn'))

    return vpn.to_dict


@register(auth='token', validate={'vpn_id': v.is_id()})
def delete(context, vpn_id):
    """ Delete vpn network """
    vpn = VPN.get(context.user_id, vpn_id)

    if vpn.connection_set.count() > 0:
        raise CoreException('vpn_in_use')

    task = Task()
    task.state = 'not active'
    task.set_prop('vpn_id', vpn.id)
    task.type = 'vpn'
    task.action = 'delete'
    task.addAfter(Task.objects.filter(type='vpn').\
                               exclude(Q(state='ok') | Q(state='canceled')).\
                               exclude(state='failed').\
                               all())


@register(auth='token', validate={'vpn_id': v.is_id(), 'vm_id': v.is_id()})
def attach(context, vpn_id, vm_id):
    """  """
    vpn = VPN.get(context.user_id, vpn_id)
    vm = VM.get(context.user_id, vm_id)

    if not vpn.in_state('running'):
        raise CoreException('network_not_running')

    if not vm.in_state('stopped') and coreConf.CHECK_STATES:
        raise CoreException('vm_not_stopped')

    connection = Connection()
    connection.vm = vm
    connection.vpn = vpn
    connection.user_id = context.user_id
    connection.save()

    task = Task()
    task.vm = vm
    task.state = 'not active'
    task.set_prop('connection_id', connection.id)
    task.type = 'vpn'
    task.action = 'attach'
    task.ignore_errors = True
    task.addAfter(Task.objects.filter(type__in=['vpn', 'vm', 'node']).filter(Q(node=None) | Q(node=connection.vm.node)))

    return connection.to_dict


@register(auth='token', validate={'connection_id': v.is_id()})
def detach(context, connection_id):
    connection = Connection.get(context.user_id, connection_id)

    if connection.vm == None:
        raise CoreException('not_connected')

    if not connection.vm.in_state('stopped') and coreConf.CHECK_STATES:
        raise CoreException('vm_not_stopped')

    task = Task()
    task.vm = connection.vm
    task.state = 'not active'
    task.set_prop('connection_id', connection.id)
    task.type = 'vpn'
    task.action = 'detach'
    task.ignore_errors = True
    task.addAfter(Task.objects.filter(type__in=['vpn', 'vm', 'node']).filter(Q(node=None) | Q(node=connection.vm.node)))


@register(auth='token')
def get_list(context):
    return [v.to_dict for v in VPN.objects.filter(user=context.user).exclude(state='removed').all()]


@register(auth='token', validate={'vpn_id': v.is_id()})
def get_by_id(context, vpn_id):
    return VPN.get(context.user_id, vpn_id).to_dict


@register(auth='token', validate={'vpn_id': v.is_id()})
def get_connection_list(context, vpn_id):
    """ List all connections related to given vpn """
    vpn = VPN.get(context.user_id, vpn_id)
    return [v.to_dict for v in vpn.connection_set.exclude(state='closed').all()]


@register(auth='token', validate={'vpn_id': v.is_id()})
def client_cert(context, vpn_id):
    vpn = VPN.get(context.user_id, vpn_id)
    return {'cert': vpn.client_crt, 'key': vpn.client_key, 'ca_cert': vpn.ca_crt}
