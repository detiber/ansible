#
# (c) 2015 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
"""
This module adds support for Kubernetes to Ansible shared
module_utils.  It builds on module_utils/urls.py.

In order to use this module, include it as part of a custom
module as shown below.

** Note: The order of the import statements does matter. **

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.kubernetes import *

"""

class KubernetesClient(object):
    def __init__(module):
        self.module  = module

    def update_pod(pod_name):
        pass

    def get_pod(pod_name):
        pass

    def create_pod(pod_name):
        pass

    def delete_pod(pod_name):
        pass

def kubernetes_argument_spec(**kwargs):
    spec = dict(
        username = dict(default=None),
        password = dict(default=None),
        kubeconfig = dict(default=None),
        namespace = dict(default=None),
        api_version = dict(default='v1')
    )
    spec.update(kwargs)
    return spec

def kubernetes_module_kwargs(**kwargs):
    ret = {}
    for key in ('mutually_exclusive', 'required_together', 'required_one_of'):
        if key in kwargs:
            if key in ret:
                ret[key].extend(kwargs[key])
            else:
                ret[key] = kwargs[key]
    return ret
