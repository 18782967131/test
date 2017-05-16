""" coding: utf-8
Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Test implements the class that provides an interface to parse the test
parameters needed to run the test.

.. moduleauthor:: ppenumarthy@varmour.com
"""
import copy
from vautils.dataparser.yaml import load_yaml
from vautils.resource.inventory import VaInventory
from vautils import logger
from vautils.exceptions import LabInfoError, TestInfoError
from pprint import pprint

class VaTestInfo(object):
    """
    Parses the test params file and provides interface to the inventory.
    """
    def __init__(self, test_yaml=None, topology_yaml=None, add_nocli_user=False):
        """
        Initializes the VaTestInfo object
        """
        if not test_yaml:
            raise TestInfoError()
        self.test_yaml = test_yaml
        self.topology_yaml = topology_yaml
        self._test_params = load_yaml(test_yaml)
        self._top_params = load_yaml(topology_yaml)
        self._inventory = self._top_params.get('inventory_file') 
        self._log = logger
        self._user_params = self._test_params.get('user_params') 
        self._control = self._test_params.get('control')
        self.inventory_file = self._inventory

        self.va_load_inventory()
        self.va_lookup_inventory(add_nocli_user=add_nocli_user)

    def va_load_inventory(self, inventory_yaml=None):
        """
        Loads the lab information provided as a yaml file that contains
        the vm resource information.

        Kwargs:
            :inventory_yaml (str): representation of the inventory info

        Raises:
            :LabInfoError:
        """
        inventory_yaml = self._inventory
        if not inventory_yaml:
            raise LabInfoError()

        self._inventory = VaInventory(**load_yaml(inventory_yaml))

    def va_lookup_inventory(self,add_nocli_user=False):
        """
        Looks up the inventory for the vm devices needed for the test

        TODO: warn may need to be replaced by an exception
        """
        devices = self._top_params.get('devices')
        inv = self._inventory

        for device in devices:
            uniq_id = device.get('uniq_id')
            if not inv.va_get_by_uniq_id(uniq_id,add_nocli_user=add_nocli_user):
                self._log.warn("could not find {} in inventory".format(uniq_id))

    def va_get_test_inventory(self):
        """
        Get the inventory info.
        """
        return self._inventory

    def va_get_test_vms(self):
        """
        Get the vm devices participating in the automated test.

        Returns:
            :dict of device objects indexed by the uniq_id's.
        """
        return self._inventory._uniq_ids

    def va_get_links(self):
        """
        Generates a list of links that represent the connections for
        a test.

        Returns:
            :list of links corresponding to a connection:
        """
        test_info = self._top_params
        test_devices = self.va_get_test_vms()

        links_dict = dict()

        if test_info.get('connections'):
            for link in test_info.get('connections'):
                links_dict[link.get('name')] = dict()
                for device in link.get('devices'):
                    link_info = links_dict[link.get('name')]
                    dev = device.get('dev')
                    link_info[dev] = dict()
                    link_info[dev]['int'] = device.get('int')
                link_info[dev]['vlan'] = link.get('vlan')

        for link in links_dict:
            link_info = links_dict.get(link)
            for dev in link_info.keys():
                dev_info = link_info.get(dev)
                for device in test_devices:
                    test_dev = test_devices.get(device)
                    if dev == test_dev.get_uniq_id():
                        int_name = dev_info.get('int')
                        dev_info['interface'] = test_dev.get_interface(
                                                    int_name
                                                )
                        dev_info['interface']['name'] = dev_info.get('int')
                        del dev_info['int']
                        dev_info['hyp_visor'] = test_dev.get_hypervisor()

        return links_dict

    def va_get_interfaces(self):
        """
        Generates a list of interfaces that represent the connections for
        a test.

        Returns:
            :list of interfaces corresponding to a connection:
        """
        test_info = self._top_params
        test_devices = self.va_get_test_vms()

        interfaces_dict = dict()

        for dev_info in test_info.get('devices'):
            if 'test_interface' in dev_info:
                interface = dev_info.get('test_interface')
                dev = dev_info.get('uniq_id')
                interfaces_dict[dev] = interface

        for interface in interfaces_dict:
            interface_info = interfaces_dict.get(interface)
            for device in test_devices:
                test_dev = test_devices.get(device)
                if interface == test_dev.get_uniq_id():
                    for interface in interface_info:
                        int_name = interface['name']
                        phy_intf = test_dev.get_interface(
                                       int_name)['phy_name']
                        if len(phy_intf.strip()) == 0:
                            phy_intf = int_name
                        interface['phy_name'] = phy_intf

        return interfaces_dict

    def __del__(self):
        """
        unlinking the reference to the inventory instance.
        """
        self._inventory = None

    """
        Melody added following apis  
    """

    def va_get_by_uniq_id(self, uniq_id=None, delegator=True):
        """
        Get the vm by unique id 
        Returns:
            :vm object
        """
        return self._inventory.va_get_by_uniq_id(uniq_id, delegator)

    def va_get_network_config(self, attribute=None):
        """
        Get the network info 
        Returns:
            :dict
        """

        if attribute is not None:
           return self._inventory.va_get_network_config(attribute)
        return self._inventory.va_get_network_config()


    def va_get_vlan_list(self):
        """
        Implementation of get_vlan_id of the topology.

        Returns:
            :vlan id (list):
        """

        vlan_id = self.va_get_network_config('vlan_range')
        new_vlan_id = list()
        if not isinstance(vlan_id, list):
           vlan_id = [vlan_id]

        for vid in vlan_id:
            if not isinstance(vid, str):
                vid = str(vid)
            split_vid_id = vid.split('-')
            if len(split_vid_id) == 2:
                start_id = int(split_vid_id[0])
                end_id = int(split_vid_id[1])
                for id in range(start_id,(end_id +1)):
                    new_vlan_id.append(id)
            else:
                new_vlan_id.append(int(vid))
        return(new_vlan_id)


    def va_get_routes(self):
        """
        Generates a list of routes 
        Returns:
            :list of routes:
        """
        test_info = self._top_params
        test_devices = self.va_get_test_vms()

        routes_dict = dict()

        for dev_info in test_info.get('devices'):
            if 'route' in dev_info:
                routes = dev_info.get('route')
                dev = dev_info.get('uniq_id')
                routes_dict[dev] = routes

        return routes_dict

    def va_get_user_params(self, attribute=None):
        """
        method get the global config by attribute. If attribute is not
        mentioned - return the entire global config.
        """
        if attribute in self._user_params.keys():
            return self._user_params.get(attribute)
        else:
            return self._user_params

    def va_get_switch(self, hv_uniq_id):
        """
        Generates a list of switchs
        Returns:
            :list of switchs:

        Example:
            :va_get_switch('hvisor_1')
        """

        vswitches = []
        inventory_file = self._top_params.get('inventory_file')
        inv_params = load_yaml(inventory_file)
        hvs = inv_params.get('hypervisor')

        #get all switch of all hypervisor
        for hv in hvs :
            if hv['uniq_id'] == hv_uniq_id :
                current_hv = hv
                break

        vswitches = hv['vswitches'].split(' ')

        #delete empty value if exist
        for key in vswitches :
            if ' ' in vswitches:
                vswitches.remove(' ')

        if len(vswitches) == 0 :
            self._log.warn("Not found any switchs of hv {}".format(hv['mgmt_ip']))
        else :
            self._log.info("Succeed to get all switchs of hv {}".format(hv['mgmt_ip']))
            self._log.info("Switchs information is {}".format(str(vswitches)))

        return vswitches

    def va_get_control(self):
        """
        Get data of contole
        Returns:
            :dict:

        Example:
            :va_get_control()
        """
        return self._control

    def va_get_segmentation(self):
        """
        Generates a list of segentations data from test_param and topo file.

        Parameter : None

        Returns:
            :tuple:
             Succeed : True,segmentation
             Failure:  Failure,error_message

        """
        test_info = self._top_params

        if 'Segmentations' in test_info :
            segmentation = copy.deepcopy(test_info.get('Segmentations'))
        else :
            error_msg = 'Not found Segmentation data in {} file'.format(self.topology_yaml)
            logger.error(error_msg)
            return False,error_msg

        if 'Segmentation' in self._test_params.get('user_params'):
            segmentation_test_param = self._test_params.get('user_params').get('Segmentation')
        else :
            error_msg = 'Not found Segmentation data in {} file'.format(self.test_yaml)
            logger.error(error_msg)
            return False,error_msg

        for each_seg_info in segmentation :
            segments =each_seg_info.get('segments')
            for segment in segments:
                segment_name = segment.get('segment')
                segment['segment'] = segmentation_test_param.get(segment_name)

        return True,segmentation