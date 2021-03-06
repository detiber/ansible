#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nxos_vlan
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Manages VLAN resources and attributes.
description:
    - Manages VLAN configurations on NX-OS switches.
author: Jason Edelman (@jedelman8)
options:
    vlan_id:
        description:
            - Single VLAN ID.
        required: false
        default: null
    vlan_range:
        description:
            - Range of VLANs such as 2-10 or 2,5,10-15, etc.
        required: false
        default: null
    name:
        description:
            - Name of VLAN.
        required: false
        default: null
    vlan_state:
        description:
            - Manage the vlan operational state of the VLAN
              (equivalent to state {active | suspend} command.
        required: false
        default: active
        choices: ['active','suspend']
    admin_state:
        description:
            - Manage the VLAN administrative state of the VLAN equivalent
              to shut/no shut in VLAN config mode.
        required: false
        default: up
        choices: ['up','down']
    mapped_vni:
        description:
            - The Virtual Network Identifier (VNI) ID that is mapped to the
              VLAN. Valid values are integer and keyword 'default'.
        required: false
        default: null
        version_added: "2.2"
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']

'''
EXAMPLES = '''
- name: Ensure a range of VLANs are not present on the switch
  nxos_vlan:
    vlan_range: "2-10,20,50,55-60,100-150"
    host: 68.170.147.165
    username: cisco
    password: cisco
    state: absent
    transport: nxapi

- name: Ensure VLAN 50 exists with the name WEB and is in the shutdown state
  nxos_vlan:
    vlan_id: 50
    host: 68.170.147.165
    admin_state: down
    name: WEB
    transport: nxapi
    username: cisco
    password: cisco

- name: Ensure VLAN is NOT on the device
  nxos_vlan:
    vlan_id: 50
    host: 68.170.147.165
    state: absent
    transport: nxapi
    username: cisco
    password: cisco
'''

RETURN = '''

proposed_vlans_list:
    description: list of VLANs being proposed
    returned: when debug enabled
    type: list
    sample: ["100"]
existing_vlans_list:
    description: list of existing VLANs on the switch prior to making changes
    returned: when debug enabled
    type: list
    sample: ["1", "2", "3", "4", "5", "20"]
end_state_vlans_list:
    description: list of VLANs after the module is executed
    returned: when debug enabled
    type: list
    sample:  ["1", "2", "3", "4", "5", "20", "100"]
proposed:
    description: k/v pairs of parameters passed into module (does not include
                 vlan_id or vlan_range)
    returned: when debug enabled
    type: dict or null
    sample: {"admin_state": "down", "name": "app_vlan",
            "vlan_state": "suspend", "mapped_vni": "5000"}
existing:
    description: k/v pairs of existing vlan or null when using vlan_range
    returned: when debug enabled
    type: dict
    sample: {"admin_state": "down", "name": "app_vlan",
             "vlan_id": "20", "vlan_state": "suspend", "mapped_vni": ""}
end_state:
    description: k/v pairs of the VLAN after executing module or null
                 when using vlan_range
    returned: when debug enabled
    type: dict or null
    sample: {"admin_state": "down", "name": "app_vlan", "vlan_id": "20",
             "vlan_state": "suspend", "mapped_vni": "5000"}
updates:
    description: command string sent to the device
    returned: always
    type: list
    sample: ["vlan 20", "vlan 55", "vn-segment 5000"]
commands:
    description: command string sent to the device
    returned: always
    type: list
    sample: ["vlan 20", "vlan 55", "vn-segment 5000"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''
from ansible.module_utils.nxos import get_config, load_config, run_commands
from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule

import re

from ansible.module_utils.nxos import nxos_argument_spec, check_args
from ansible.module_utils.nxos import run_commands, load_config, get_config
from ansible.module_utils.basic import AnsibleModule

def vlan_range_to_list(vlans):
    result = []
    if vlans:
        for part in vlans.split(','):
            if part == 'none':
                break
            if '-' in part:
                a, b = part.split('-')
                a, b = int(a), int(b)
                result.extend(range(a, b + 1))
            else:
                a = int(part)
                result.append(a)
        return numerical_sort(result)
    return result


def numerical_sort(string_int_list):
    """Sort list of strings (VLAN IDs) that are digits in numerical order.
    """

    as_int_list = []
    as_str_list = []
    for vlan in string_int_list:
        as_int_list.append(int(vlan))
    as_int_list.sort()
    for vlan in as_int_list:
        as_str_list.append(str(vlan))
    return as_str_list


def build_commands(vlans, state):
    commands = []
    for vlan in vlans:
        if state == 'present':
            command = 'vlan {0}'.format(vlan)
            commands.append(command)
        elif state == 'absent':
            command = 'no vlan {0}'.format(vlan)
            commands.append(command)
    return commands


def get_vlan_config_commands(vlan, vid):
    """Build command list required for VLAN configuration
    """

    reverse_value_map = {
        "admin_state": {
            "down": "shutdown",
            "up": "no shutdown"
        }
    }

    if vlan.get('admin_state'):
        # apply value map when making change to the admin state
        # note: would need to be a loop or more in depth check if
        # value map has more than 1 key
        vlan = apply_value_map(reverse_value_map, vlan)

    VLAN_ARGS = {
        'name': 'name {0}',
        'vlan_state': 'state {0}',
        'admin_state': '{0}',
        'mode': 'mode {0}',
        'mapped_vni': 'vn-segment {0}'
    }

    commands = []

    for param, value in vlan.items():
        if param == 'mapped_vni' and value == 'default':
            command = 'no vn-segment'
        else:
            command = VLAN_ARGS.get(param).format(vlan.get(param))
        if command:
            commands.append(command)

    commands.insert(0, 'vlan ' + vid)
    commands.append('exit')

    return commands


def get_list_of_vlans(module):
    body = run_commands(module, ['show vlan | json'])
    vlan_list = []
    vlan_table = body[0].get('TABLE_vlanbrief')['ROW_vlanbrief']

    if isinstance(vlan_table, list):
        for vlan in vlan_table:
            vlan_list.append(str(vlan['vlanshowbr-vlanid-utf']))
    else:
        vlan_list.append('1')

    return vlan_list


def get_vni(vlanid, module):
    flags = str('all | section vlan.{0}'.format(vlanid)).split(' ')
    body = get_config(module, flags=flags)
    #command = 'show run all | section vlan.{0}'.format(vlanid)
    #body = execute_show_command(command, module, command_type='cli_show_ascii')[0]
    value = ''
    if body:
        REGEX = re.compile(r'(?:vn-segment\s)(?P<value>.*)$', re.M)
        if 'vn-segment' in body:
            value = REGEX.search(body).group('value')
    return value


def get_vlan(vlanid, module):
    """Get instance of VLAN as a dictionary
    """
    command = 'show vlan id %s | json' % vlanid
    body = run_commands(module, [command])

    #command = 'show vlan id ' + vlanid
    #body = execute_show_command(command, module)

    try:
        vlan_table = body[0]['TABLE_vlanbriefid']['ROW_vlanbriefid']
    except (TypeError, IndexError):
        return {}

    key_map = {
        "vlanshowbr-vlanid-utf": "vlan_id",
        "vlanshowbr-vlanname": "name",
        "vlanshowbr-vlanstate": "vlan_state",
        "vlanshowbr-shutstate": "admin_state"
    }

    vlan = apply_key_map(key_map, vlan_table)

    value_map = {
        "admin_state": {
            "shutdown": "down",
            "noshutdown": "up"
        }
    }

    vlan = apply_value_map(value_map, vlan)
    vlan['mapped_vni'] = get_vni(vlanid, module)
    return vlan


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = str(value)
    return new_dict


def apply_value_map(value_map, resource):
    for key, value in value_map.items():
        resource[key] = value[resource.get(key)]
    return resource

def main():
    argument_spec = dict(
        vlan_id=dict(required=False, type='str'),
        vlan_range=dict(required=False),
        name=dict(required=False),
        vlan_state=dict(choices=['active', 'suspend'], required=False),
        mapped_vni=dict(required=False, type='str'),
        state=dict(choices=['present', 'absent'], default='present',
                       required=False),
        admin_state=dict(choices=['up', 'down'], required=False),
        include_defaults=dict(default=False),
        config=dict(),
        save=dict(type='bool', default=False)
    )

    argument_spec.update(nxos_argument_spec)


    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[['vlan_range', 'name'],
                                               ['vlan_id', 'vlan_range']],
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)


    warnings = list()
    check_args(module, warnings)

    vlan_range = module.params['vlan_range']
    vlan_id = module.params['vlan_id']
    name = module.params['name']
    vlan_state = module.params['vlan_state']
    admin_state = module.params['admin_state']
    mapped_vni = module.params['mapped_vni']
    state = module.params['state']

    changed = False

    if vlan_id:
        if not vlan_id.isdigit():
            module.fail_json(msg='vlan_id must be a valid VLAN ID')

    args = dict(name=name, vlan_state=vlan_state,
                admin_state=admin_state, mapped_vni=mapped_vni)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    proposed_vlans_list = numerical_sort(vlan_range_to_list(
        vlan_id or vlan_range))
    existing_vlans_list = numerical_sort(get_list_of_vlans(module))
    commands = []
    existing = {}

    if vlan_range:
        if state == 'present':
            # These are all of the VLANs being proposed that don't
            # already exist on the switch
            vlans_delta = list(
                set(proposed_vlans_list).difference(existing_vlans_list))
            commands = build_commands(vlans_delta, state)
        elif state == 'absent':
            # VLANs that are common between what is being proposed and
            # what is on the switch
            vlans_common = list(
                set(proposed_vlans_list).intersection(existing_vlans_list))
            commands = build_commands(vlans_common, state)
    else:
        existing = get_vlan(vlan_id, module)
        if state == 'absent':
            if existing:
                commands = ['no vlan ' + vlan_id]
        elif state == 'present':
            if (existing.get('mapped_vni') == '0' and
                    proposed.get('mapped_vni') == 'default'):
                proposed.pop('mapped_vni')
            delta = dict(set(proposed.items()).difference(existing.items()))
            if delta or not existing:
                commands = get_vlan_config_commands(delta, vlan_id)

    end_state = existing
    end_state_vlans_list = existing_vlans_list

    if commands:
        if existing.get('mapped_vni') and state != 'absent':
            if (existing.get('mapped_vni') != proposed.get('mapped_vni') and
                    existing.get('mapped_vni') != '0' and proposed.get('mapped_vni') != 'default'):
                commands.insert(1, 'no vn-segment')
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            load_config(module, commands)
            changed = True
            end_state_vlans_list = numerical_sort(get_list_of_vlans(module))
            if 'configure' in commands:
                commands.pop(0)
            if vlan_id:
                end_state = get_vlan(vlan_id, module)

    results = {
        'commands': commands,
        'updates': commands,
        'changed': changed,
        'warnings': warnings
    }

    if module._debug:
        results.update({
            'proposed_vlans_list': proposed_vlans_list,
            'existing_vlans_list': existing_vlans_list,
            'proposed': proposed,
            'existing': existing,
            'end_state': end_state,
            'end_state_vlans_list': end_state_vlans_list
        })

    module.exit_json(**results)


if __name__ == '__main__':
    main()

