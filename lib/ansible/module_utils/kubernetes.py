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
    def __init__(self, module):
        self.module  = module
        self.server = module.params['server']
        self.namespace = module.params['namespace']
        self.api_version = module.params['api_version']

    def kube_request(self, path, method, data):
        url = "{0}/{1}".format(self.server, path)

        if 'auth_token' in self.module.params:
            headers = dict(Authorization="Bearer {0}".format(self.module.params['auth_token']))
        else:
            headers = None

        if 'insecure' in self.module.params:
            validate_certs = not self.module.params['insecure']
        else:
            validate_certs = True

        username = self.module.params.get('username', None)
        password = self.module.params.get('password', None)
        if username is not None and password is not None:
            force_basic_auth = True
        else:
            force_basic_auth = False

        response = open_url(url, data=data, headers=headers, method=method,
                            url_password=password, url_username=username,
                            validate_certs=validate_certs,
                            force_basic_auth=force_basic_auth)
        ret_code = response.getcode()
        ret_obj = self.module.from_json(response.read())
        self.module.exit_json(msg='hi', ret_code=ret_code, ret_obj=ret_obj)

    def pod_definition(self, name, containers):
        ''' create a very simple pod definition '''
        definition = {'apiVersion': self.api_version,
                      'kind': 'Pod',
                      'metadata': {
                          'name': name
                      },
                      'spec': {
                          'containers': containers
                      }
        }
        return definition

    def update_pod(self, name, containers):
        data = self.pod_definition(name, containers)
        path = '/api/{0}/namespaces/{1}/pods'.format(self.api_version, self.namespace)
        pod = self.kube_request(path, 'PUT', data)

    def get_pod(self, name):
        path = "/api/{0}/namespaces/{1}/pods/{2}".format(self.api_version, self.namespace, name)
        pod = self.kube_request(path, 'GET', None)
        return pod

    def create_pod(self, name, containers):
        data = self.pod_definiton(name, containers)
        path = '/api/{0}/namespaces/{1}/pods'.format(self.api_version, self.namespace)
        pod = self.kube_request(path, 'POST', data)

    def delete_pod(self, name):
        path = '/api/{0}/namespaces/{1}/pods/{2}'.format(self.api_version, self.namespace, name)
        pod = self.kube_request(path, 'DELETE', None)

    def service_definition(self, name, selector, ports):
        definition = { 'apiVersion': self.api_version,
                       'kind': 'Service',
                       'metadata': {
                           'name': name
                       },
                       'spec': {
                           'selector': selector,
                           'ports': ports
                       }
        }

    def update_service(self, name, selector, ports):
        data = self.service_definition(name, selector, ports)
        path = '/api/{0}/namespaces/{1}/services/{2}'.format(self.api_version, self.namespace, name)
        service = self.kube_request(path, 'PUT', data)

    def get_service(self, name):
        path = '/api/{0}/namespaces/{1}/services/{2}'.format(self.api_version, self.namespace, name)
        service = self.kube_request(path, 'GET', None)
        return service

    def create_service(self, name, selector, ports):
        data = self.service_definition(name, selector, ports)
        path = '/api/{0}/namespaces/{1}/services'.format(self.api_version, self.namespace)
        service = self.kube_request(path, 'POST', data)

    def delete_service(self, name):
        path = '/api/{0}/namespaces/{1}/services/{2}'.format(self.api_version, self.namespace, name)
        service = self.kube_request(path, 'DELETE', None)

def kubernetes_argument_spec(**kwargs):
    spec = dict(
        username = dict(default=None),
        password = dict(default=None),
        kubeconfig = dict(default=None),
        auth_token = dict(default=None),
        server = dict(default='https://localhost:8443'),
        namespace = dict(default=None),
        api_version = dict(default='v1', choices=['v1']),
        insecure = dict(default=False, type='bool')
    )
    spec.update(kwargs)
    return spec

def kubernetes_module_kwargs(**kwargs):
    ret = dict(
        mutually_exclusive = [
            ['kubeconfig', 'username'],
            ['kubeconfig', 'password'],
            ['kubeconfig', 'auth_token'],
            ['password', 'auth_token']
        ]
    )

    for key in ('mutually_exclusive', 'required_together', 'required_one_of'):
        if key in kwargs:
            if key in ret:
                ret[key].extend(kwargs[key])
            else:
                ret[key] = kwargs[key]
    return ret
