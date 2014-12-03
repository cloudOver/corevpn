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

import libvirt
from overCluster.models.core.device import Device
from overCluster.models.core.task import Task

def task_finished(task):
    for connection in task.vm.connection_set.all():
        detach = Task()
        detach.vm = task.vm
        detach.state = 'not active'
        detach.set_prop('connection_id', connection.id)
        detach.type = 'vpn'
        detach.action = 'detach'
        detach.ignore_errors = True
        detach.addAfter(Task.objects.filter(type__in=['vpn', 'vm']))
