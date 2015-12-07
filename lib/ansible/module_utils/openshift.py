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
This module adds support for OpenShift to Ansible shared
module_utils.  It builds on module_utils/urls.py and
module_utils/kubernetes.py.

In order to use this module, include it as part of a custom
module as shown below.

** Note: The order of the import statements does matter. **

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.kubernetes import *
from ansible.module_utils.openshift import *

"""

class OpenShiftClient(KubernetesClient):
    def __init__(self, module):
        self.module  = module
        self.server = module.params['server']
        self.project = module.params['project']
        self.api_version = module.params['api_version']
        KubernetesClient.__init__(self, module)

    def project_definition(self, name):
        definition = { 'apiVersion': self.api_version,
                       'kind': 'Project',
                       'metadata': {
                           'name': name
                       }
        }
        return definition

    def get_project(self):
        path = 'api/{0}/projects/{1}'.format(self.api_version, self.project)
        return self.kube_request(path, 'GET', None)

    def create_project(self):
        data = self.module.jsonify(self.project_definition(self.project))
        path = 'api/{0}/projects/{1}'.format(self.api_version, self.project)
        return self.kube_request(path, 'POST', data)

    def delete_project(self, name):
        path = 'api/{0}/projects/{1}'.format(self.api_version, self.project)
        return self.kube_request(path, 'DELETE', None)

def openshift_argument_spec(**kwargs):
    spec = kubernetes_argument_spec()
    spec.update(kwargs)
    return spec

def openshift_module_kwargs(**kwargs):
    ret = kubernetes_module_kwargs()
    for key in ('mutually_exclusive', 'required_together', 'required_one_of'):
        if key in kwargs:
            if key in ret:
                ret[key].extend(kwargs[key])
            else:
                ret[key] = kwargs[key]
    return ret
