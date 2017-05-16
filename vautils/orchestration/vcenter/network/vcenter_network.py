"""
coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

vCenterVMs class is representing vim.VirtualMachine objects  and its methods.
class methods either return string or managed objects.

.. moduleauthor::jpatel@varmour.com

"""
from vautils.orchestration.vcenter.vcenter_connector import VcenterConnector
from vautils import logger
from vautils.exceptions import NetworkNotFound


class VcenterNetwork(VcenterConnector):
    """
    vCenterNetwork class is representing vim.VirtualNetwork objects
    and its methods.class methods either return string or managed objects.
    Users can extend this class by adding more VirtualNetwork related
    methods.
    """

    def _get_network_object_by_name(self, net):
        """
        method find network object from list return by _get_content

        Args:
            :network    (str) :name of network that user wants to abstract
            from net object list
        Return:
            net object (vim.Network)
        """
        net_object_list = self._get_content("network")
        net_found = False
        for network in net_object_list:
            if network.name == net:
                net_found = True
                return network
        if not (net_found):
            raise NetworkNotFound(net)

    def _get_dvs_object_by_name(self, net):
        """
        method find dvs switch object from list return by _get_content
        Args:
            :net (str) :name of dvs network.
        Return:
            :dvs object (vim.dVswitch)
        """
        dvs_obj_list = self._get_content("dvs")
        net_found = False
        for network in dvs_obj_list:
            if network.name == net:
                net_found = True
                return network
        if not (net_found):
            raise NetworkNotFound(net)

    # TODO Implement Get VMs by Network Name
    def get_vms_by_network(self, net):
        """
        method that return list of all vms that connected with given network.
        Args:
            :net    (str):  name of network
        Returns:
            :list   (list): list of connected VMs with network.
        """
        pass

    def is_network_in_vcenter(self, net):
        """
        method that check given network is in vcenter or not.
        Args:
            :net    (str) :name of network that user wants to check.

        Returns:
            :bool  True : if network name found in venter.
                   False: if network name is not found in vcenter.
        """
        return net in [x.name for x in self.net_object_list]

    def is_network_connected_to_dvs(self, net):
        """
        methods gives given network is connected to dvs switch or not.
        Args:
            :net    (str):name of network that user wants to check.
        Returns:
            :True   (boolean): if network connected to vds switch.
            :False  (boolean): if network connected to vss switch.
        """
        dvs_obj_list = self._get_content("dvs")
        return net in [x.name for x in dvs_obj_list]
