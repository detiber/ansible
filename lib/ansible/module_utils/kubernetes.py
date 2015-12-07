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
        headers = dict()
        if 'auth_token' in self.module.params:
            headers['Authorization'] = "Bearer {0}".format(self.module.params['auth_token'])

        if 'insecure' in self.module.params:
            validate_certs = not self.module.params['insecure']
        else:
            validate_certs = True

        try:
            r = open_url(url, data=data, headers=headers, method=method,
                         validate_certs=validate_certs)
            return self.module.from_json(r.read())
        except urllib2.HTTPError as e:
            ret_code = e.code
            if e.code == 404:
                return None
            else:
                self.module.fail_json(msg="Error code: {0} Reason: {1}".format(ret_code, e.reason))
        except Exception as e:
            self.module.fail_json(msg="Exception type: {0}, message: {1}".format(type(e),str(e)))

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
        auth_token = dict(default=None),
        server = dict(default='https://localhost:8443'),
        namespace = dict(default='default'),
        api_version = dict(default='v1', choices=['v1']),
        insecure = dict(default=False, type='bool')
    )
    spec.update(kwargs)
    return spec

def kubernetes_module_kwargs(**kwargs):
    ret = dict()

    for key in ('mutually_exclusive', 'required_together', 'required_one_of'):
        if key in kwargs:
            if key in ret:
                ret[key].extend(kwargs[key])
            else:
                ret[key] = kwargs[key]
    return ret
