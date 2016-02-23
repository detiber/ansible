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
        if 'data' is not None:
            headers['Content-Type'] = 'application/json'

        auth_token = self.module.params['auth_token']
        if auth_token is not None:
            headers['Authorization'] = "Bearer {0}".format(auth_token)

        username = self.module.params.get('username', None)
        password = self.module.params.get('password', None)
        basic_auth = True if username is not None and password is not None else False

        if 'insecure' in self.module.params:
            validate_certs = not self.module.params['insecure']
        else:
            validate_certs = True

        try:
            r = open_url(url, data=data, headers=headers, method=method,
                         validate_certs=validate_certs, url_username=username,
                         url_password=password, force_basic_auth=basic_auth)

            return self.module.from_json(r.read())
        except urllib2.HTTPError as e:
            ret_code = e.code
            if e.code == 404:
                return None
            else:
                self.module.fail_json(msg="Error code: {0} Reason: {1}".format(ret_code, e.reason, str(e)))
        except Exception as e:
            self.module.fail_json(msg="Exception type: {0}, message: {1}".format(type(e),str(e)))

    def pod_definition(self, name, containers):
        if not isinstance(containers, list):
            self.module.fail_json(msg="containers must be a list")
        if len(containers) == 0:
            self.module.fail_json(msg="A pod must define at last 1 container")

        ''' create a very simple pod definition '''
        definition = {'apiVersion': self.api_version,
                      'kind': 'Pod',
                      'metadata': {
                          'name': name,
                          'namespace': self.namespace
                      },
                      'spec': {
                          'containers': containers
                      }
        }
        return definition

    def get_pod(self, name):
        path = "api/{0}/namespaces/{1}/pods/{2}".format(self.api_version, self.namespace, name)
        return self.kube_request(path, 'GET', None)

    def create_pod(self, name, containers):
        data = self.module.jsonify(self.pod_definition(name, containers))
        path = 'api/{0}/namespaces/{1}/pods'.format(self.api_version, self.namespace)
        return self.kube_request(path, 'POST', data)

    def delete_pod(self, name):
        path = 'api/{0}/namespaces/{1}/pods/{2}'.format(self.api_version, self.namespace, name)
        return self.kube_request(path, 'DELETE', None)

    def service_definition(self, name, labels, selector, ports, service_type=None):
        for port in ports:
            if 'port' in port and not isinstance(port['port'], int):
                port['port'] = int(port['port'])

        definition = { 'apiVersion': self.api_version,
                       'kind': 'Service',
                       'metadata': {
                           'name': name,
                           'labels': labels
                       },
                       'spec': {
                           'selector': selector,
                           'ports': ports
                       }
        }
        if service_type is not None:
            definition['spec']['type'] = service_type

        return definition

    def get_service(self, name):
        path = 'api/{0}/namespaces/{1}/services/{2}'.format(self.api_version, self.namespace, name)
        return self.kube_request(path, 'GET', None)

    def create_service(self, name, labels, selector, ports, service_type=None):
        data = self.module.jsonify(self.service_definition(name, labels, selector, ports, service_type=service_type))
        path = 'api/{0}/namespaces/{1}/services'.format(self.api_version, self.namespace)
        return self.kube_request(path, 'POST', data)

    def delete_service(self, name):
        path = 'api/{0}/namespaces/{1}/services/{2}'.format(self.api_version, self.namespace, name)
        return self.kube_request(path, 'DELETE', None)

    def replication_controller_definition(self, name, containers, labels, replicas, selector):
        if not isinstance(replicas, int):
            replicas = int(replicas)
        for container in containers:
            if 'ports' in container:
                for port in container['ports']:
                    for item in ('hostPort', 'containerPort', 'port'):
                        if item in port and not isinstance(port[item], int):
                            port[item] = int(port[item])

        definition = { "kind": "ReplicationController",
                       "apiVersion": self.api_version,
                       "metadata": {
                           "name": name,
                           "labels": labels
                       },
                       "spec": {
                           "replicas": replicas,
                           "selector": selector,
                           "template": {
                               "metadata": {
                                   "labels": labels
                               },
                               "spec": {
                                   "containers": containers
                               }
                           }
                       }
        }
        #self.module.fail_json(msg=definition)
        return definition


    def get_replication_controller(self, name):
        path = 'api/{0}/namespaces/{1}/replicationcontrollers/{2}'.format(self.api_version, self.namespace, name)
        return self.kube_request(path, 'GET', None)

    def create_replication_controller(self, name, containers, labels, replicas, selector):
        data = self.module.jsonify(self.replication_controller_definition(name, containers, labels, replicas, selector))
        path = 'api/{0}/namespaces/{1}/replicationcontrollers'.format(self.api_version, self.namespace)
        return self.kube_request(path, 'POST', data)

    def delete_replication_controller(self, name):
        path = 'api/{0}/namespaces/{1}/replicationcontrollers/{2}'.format(self.api_version, self.namespace, name)
        return self.kube_request(path, 'DELETE', None)

    def namespace_definition(self, name):
        definition = { 'apiVersion': self.api_version,
                       'kind': 'Namespace',
                       'metadata': {
                           'name': name
                       }
        }
        return definition

    def get_namespace(self):
        path = 'api/{0}/namespaces/{1}'.format(self.api_version, self.namespace)
        return self.kube_request(path, 'GET', None)

    def create_namespace(self):
        data = self.module.jsonify(self.namespace_definition(self.namespace))
        path = 'api/{0}/namespaces'.format(self.api_version)
        return self.kube_request(path, 'POST', data)

    def delete_namespace(self, name):
        path = 'api/{0}/namespaces/{1}'.format(self.api_version, self.namespace)
        return self.kube_request(path, 'DELETE', None)


def kubernetes_argument_spec(**kwargs):
    spec = dict(
        auth_token = dict(default=None),
        username = dict(default=None),
        password = dict(default=None),
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
