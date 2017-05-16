""" coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Inventory implements the class that abstracts the test inventory and the
vms required to run an automated test.

.. moduleauthor:: ppenumarthy@varmour.com
"""

from vautils import logger
from vautils.exceptions import UnknownDevice
from vautils.resource.delegator import Delegator
from vautils.resource import *  # NOQA

VALID_TYPES = ['dir', 'cp', 'ep', 'epi', 'linux', 'vcenter']


class VaInventory(object):
    """
    Represents the lab setup of a test bed whose information is stored in
    a representable form. It provides an interface to the tests to obtain
    test bed and device information. Currently the information is stored
    in a certain expected fashion in yaml format. If the information
    storage medium changes like a database in the future, the class
    implementation may undergo a little change but the interface will be
    similar (if not same).
    """

    def __init__(self, **kwargs):
        """
        Initialize the test lab and device objects. Test lab consists of
        hypervisors, vswitches, users, vlans, users, and devices. A name
        or a unique-id is used to identify the test lab.
        """
        inventory = kwargs

        self._hypervisor = list()
        self._aci = list()
        self._linux = list()
        self._dir = list()
        self._cp = list()
        self._ep = list()
        self._epi = list()
        self._vcenter = list()
        self._log = logger
        self._uniq_ids = dict()
        self._network = inventory.get('network')

        self._va_make_hypervisor(inventory.get('hypervisor'))
        self._va_make_aci(inventory.get('aci'))

        for vm_type in inventory.keys():
            if vm_type in VALID_TYPES:
                many_vms = inventory.get(vm_type)
                self._va_make_vm(vm_type, many_vms)
            else:
                if vm_type != 'hypervisor' and vm_type != 'network' and\
                    vm_type != 'aci':
                    self._log.warn("Invalid vm type: {}".format(vm_type))

        self._va_categorize_by_uniq_id()

    def va_get_vm(self, vm_type=None, uniq_id=None):
        """
        get a vm of vm_type if specified or a list of all vms.
        """
        if vm_type not in VALID_TYPES:
            raise UnknownDevice(vm_type)

        try:
            attrib = ''.join(('_', "{}".format(vm_type)))
            vms = getattr(self, "{}".format(attrib))
        except AttributeError:
            # TODO: raise DeviceNotSetup(device_type)
            raise
        else:
            if uniq_id:
                for vm in vms:
                    if vm.get_uniq_id() == uniq_id:
                        return vm
            else:
                return vms

    def va_get_hypervisor(self, name=None):
        """
        Get a 'hypervisor' node, if name is specified or a list of all
        hypervisors.

        Kwargs:
            :name (str): hostname of the hypervisor
        """
        if name:
            for hvisor in self._hypervisor:
                if name == hvisor.get_hostname():
                    return hvisor

        return self._hypervisor
    
    def va_get_aci(self, name=None):
        """
        Get an 'aci' node, if name is specified or a list of all acis

        Kwargs:
            :name (str): hostname of the aci
        """
        if name:
            for aci in self._aci:
                if name == aci.get_hostname():
                    return aci

        return self._aci

    def va_get_dir(self, name=None):
        """
        Get a 'director' vm, if name is specified or a list of all
        dirs.

        Kwargs:
            :name (str): hostname of the director
        """
        if name:
            for director in self._dir:
                if name == director.get_hostname():
                    return director

        return self._dir

    def va_get_ep(self, name=None):
        """
        Get a 'ep' vm if name is specified or a list of all eps.

        Kwargs:
            :name (str): hostname of the ep
        """
        if name:
            for ep in self._ep:
                if name == ep.get_hostname():
                    return ep

        return self._ep

    def va_get_cp(self, name=None):
        """
        Get a 'cp' vm if name is specified or a list of all cps.

        Kwargs:
            :name (str): hostname of the cp
        """
        if name:
            for cp in self._cp:
                if name == cp.get_hostname():
                    return cp

        return self._cp

    def va_get_epi(self, name=None):
        """
        Get a 'epi' vm if name is specified or a list of all epis.

        Kwargs:
            :name (str): hostname of the epi
        """
        if name:
            for epi in self._epi:
                if name == epi.get_hostname():
                    return epi

        return self._epi

    def va_get_vcenter(self, name=None):
        """
        Get a 'hypervisor' node, if name is specified or a list of all
        hypervisors.

        Kwargs:
            :name (str): hostname of the hypervisor
        """
        if name:
            for vcenter in self._vcenter:
                if name == vcenter.get_hostname():
                    return vcenter

        return self._vcenter

    def va_get_linux(self, name=None):
        """
        Get a 'linux' vm if name is specified or a list of all linux vms

        Kwargs:
            :name (str): hostname of the pc
        """
        if name:
            for linux in self._linux:
                if name == linux.get_hostname():
                    return linux

        return self._linux

    def va_get_by_uniq_id(self, uniq_id=None, delegator=True, add_nocli_user=False):
        """
        get the vm by unique id

        kwargs:
            uniq_id (str): unique id for the resource vm
            delegator (bool): if delegator version of the resource is
                              needed (default is False)
        """
        if add_nocli_user :
            self._uniq_ids.get(uniq_id).add_nocli_user=add_nocli_user
        if uniq_id in self._uniq_ids:
            if delegator:
                return Delegator(self._uniq_ids.get(uniq_id))
            else:
                return self._uniq_ids.get(uniq_id)
        else:
            # TODO: raise UnknownUniqId(uniq_id)
            # I don't know if raise is needed,
            # you can just let user know uniq id not exists
            logger.warning("unknown uniq_id {}".format(str(uniq_id)))

    def va_get_network_config(self, attribute=None):
        """
        method get the network config by attribute. If attribute is not
        mentioned - return the entire network config.
        """
        if attribute in self._network.keys():
            return self._network.get(attribute)
        else:
            return self._network

    def _va_make_hypervisor(self, hypervisors=None):
        """
        make a hypervisor object - also validates the data provided
        for the device before initializing.

        kwargs:
            :hypervisors (list): list of hypervisors in the lab
        """
        if hypervisors:
            for hypervisor in hypervisors:
                self._hypervisor.append(Esxi(**hypervisor))
        else:
            # TODO: raise DeviceNotFound
            pass

    def _va_make_aci(self, aci=None):
        """
        make an aci object - also validates the data provided for the
        device before initializing.

        kwargs:
            :aci (list): list of aci in the lab
        """
        if aci:
            for each_aci in aci:
                self._aci.append(AciApic(**each_aci))
        else:
            # TODO: raise DeviceNotFound
            pass
    
    def _va_make_vm(self, vm_type=None, vms=None):
        """
        make a specific vm object - also validates the data provided for
        the vm before initializing.

        kwargs:
            :vm_type (str): vm type - dir|ep|epi|linux
            :vms (list): list of specific vms of vm type in the inventory
        """
        for vm in vms:
            vm['type'] = vm_type
            if vm_type in ('dir', 'ep', 'cp', 'epi'):
                vm_rep = VarmourVm(**vm)
            elif vm_type == 'linux':
                vm_rep = LinuxVm(**vm)
            elif vm_type == "vcenter":
                vm_rep = VcenterVm(**vm)
            vm_list = self.va_get_vm(vm_type)
            vm_list.append(vm_rep)

    def _va_categorize_by_uniq_id(self):
        """
        helper method to categorize inventory by unique id's in a dict
        """
        for node_type in VALID_TYPES:
            nodes = self.va_get_vm(node_type)
            for node in nodes:
                uniq_id = node.get_uniq_id()
                self._uniq_ids[uniq_id] = node

        for node in self.va_get_hypervisor():
            uniq_id = node.get_uniq_id()
            self._uniq_ids[uniq_id] = node

        for node in self.va_get_aci():
            uniq_id = node.get_uniq_id()
            self._uniq_ids[uniq_id] = node
    
    def __del__(self):
        self._hypervisor = None
        self._aci = None
        self._dir = None
        self._ep = None
        self._epi = None
        self._pc = None
        self._uniq_ids = None
