""" coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

bootstrap implements the abstraction to model the detail resource
information required to run an automated test.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import os
import re
import yaml

from vautils import logger
from vautils.dataparser import va_parse_basic
from access.shell import LinuxShell
from access.cli.va_os import VaCli


class VaConsole(object):
    """
    Rack implements the class that expands the node information
    """

    VALID_TYPES = ('dir', 'ep', 'epi', 'cp', 'linux', 'hypervisor', 'vcenter', 'aci')

    def __init__(self, name=None, path=None):
        """
        Initialize the rack object
        """
        if not name:
            name = 'rack.yaml'

        self._rack = dict()
        self._rack['network'] = dict()
        self._log = logger
        self._types = list()

        if path:
            self._rackyaml = os.path.join(os.path.abspath(path), name)

        for device in self.VALID_TYPES:
            self._rack[device] = list()

    def va_add_vm(self, vm=None, vm_type=None):
        """
        add vm to the inventory available for test.
        """
        vm_list = self._rack.get(vm_type)
        info = True

        self._types.append(vm_type)

        if vm_type == 'linux':
            bootstrap_info = self._get_linux_release_info(vm)
            if bootstrap_info:
                vm['version'] = bootstrap_info.get('distributor_id')
                vm['version_info'] = bootstrap_info.get('description')
                vm['hostname'] = bootstrap_info.get('hostname')
            else:
                info = False
        elif vm_type in ['dir', 'ep', 'epi', 'cp']:
            bootstrap_info = self._va_get_release_info(vm, vm_type)
            if bootstrap_info:
                version = bootstrap_info.get('software version')
                vm['version'] = version.split('-')[0]
                vm['version_info'] = version
                vm['hostname'] = bootstrap_info.get('hostname')
            else:
                info = False

        try:
            del vm['prompt']
        except KeyError:
            pass

        if not info:
            self._log.info("bootstrap info could not be generated for {} {}"
                           .format(vm_type, vm['mgmt_ip']))

        vm_list.append(vm)

    def va_add_network_config(self, config=None):
        """
        method to add the network settings for the test
        """
        if config:
            self._rack['network'] = config

    def va_add_hypervisor(self, hypervisor=None):
        """
        method to add the hypervisor for the inventory
        """
        self._types.append('hypervisor')

        if hypervisor:
            self._rack['hypervisor'] = hypervisor

    def va_add_aci(self, aci=None):
        """
        method to add the aci for the inventory
        """
        self._types.append('aci')

        if aci:
            self._rack['aci'] = aci
    
    def va_get_vm(self, vm_type=None, uniq_id=None):
        """
        get list of vms's of vm_type. If uniq_id is specified return the vm
        with that uniq_id

        kwargs:
            :vm_type (str): valid vm_type
            :uniq_id (str): valid uniq_id for the vm

        returns:
            :vm list of vm_type or a vm with matching uniq_id of that type
        """
        vm_list = self._rack.get(vm_type)

        if uniq_id:
            for vm in vm_list:
                if vm.get('uniq_id') == uniq_id:
                    return vm
        else:
            return vm_list

    def va_get_inventory(self):
        """
        get the console that has access to the inventory of vms

        returns:
            :inventory dict: keys are vm types and values are list of vms
        """
        return self._rack

    def va_create_inventory(self):
        """
        write the expanded vm inventory information to a yaml file.
        """
        for vm_type in self.VALID_TYPES:
            if vm_type not in self._types:
                del self._rack[vm_type]

        del self._types

        with open(self._rackyaml, 'w') as rackfile:
            rackfile.write(yaml.dump(self._rack, default_flow_style=False))

        self._log.info("device rack file - {}".format(self._rackyaml))

    def _get_linux_release_info(self, target=None):
        """
        helper method to get the linux software version.

        Kwargs:
            :target - (LinuxVm type): target linux resource
        """
        user = target.get('user')

        shell = LinuxShell(
                    host=target.get('mgmt_ip'),
                    user=user.get('name'),
                    pswd=user.get('password')
                )
        info = dict()

        output = shell.exec_command("lsb_release -a")

        for line in output[0].splitlines():
            if not line.startswith('No'):
                line = line.strip()
                key, value = line.split(':', 1)
                key = re.sub(' ', '_', key)
                info[key.lower()] = value.strip()

        output = shell.exec_command("hostname")
        info['hostname'] = output[0].rstrip()

        return info

    def _va_get_release_info(self, target=None, product_type=None):
        """
        helper method to get the software version running on varmour vm.

        Kwargs:
            :target - (VarmourVm type): target varmour resource
            :product_type - (str): varmour product type
        """
        user = target.get('user')
        prompt_type = None

        if target.get('prompt'):
            prompt_type = target.get('prompt')
        else:
            prompt_type = product_type

        target['prompt_type'] = prompt_type

        instance = VaCli(
            host=target.get('mgmt_ip'),
            user=user.get('name'),
            password=user.get('password'),
            prompt=prompt_type
        )

        with instance as cli:
            if (user.get('name') == 'varmour_no_cli') :
                output, match, mode = cli.va_exec_cli("cat /version")
                output1, match1, mode1 = cli.va_exec_cli("hostname")
                return {'software version':output.split('\n')[1],'hostname':output1.split('\n')[1]}
            else :
                output, match, mode = cli.exec_command("show system | grep version")
                output1, match1, mode1 = cli.exec_command("show system | grep hostname")
                output = output + output1

        return va_parse_basic(output)

    def __del__(self):
        """
        unlink the references to any instances created.
        """
        pass
