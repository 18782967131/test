"""
coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

vCenterVMs class is representing vim.VirtualMachine objects  and its methods.
class methods either return string or managed objects.

.. moduleauthor::jpatel@varmour.com

"""

from vautils.orchestration.vcenter.vcenter_connector import VcenterConnector
from pyVmomi import vim
from vautils import logger
from vautils.exceptions import VmNotFound, VmNicNotAvailable, VmTagNotFound


class VcenterVMs(VcenterConnector):
    """
    vCenterVMs class is representing vim.VirtualMachine objects  and its
    methods.class methods either return string or managed objects.Users
    can extend this class by adding more VirtualMachine related methods.
    ParentClass: vCenterConnector
    ChildClass : vmAction
    """

    def _get_host_portgroups(self):
        hostPgDict = {}
        for host in self.host_obj_list:
            pgs = host.config.network.portgroup
            hostPgDict[host]=pgs
        return hostPgDict


    def _log_all_vm_uuid(self):
        """
        method just printing two types of UUIDs. i) Instance UUID ii)BiOS UUID
        Note: This method returns nothing.This method is a private method and
        logging VM's UUID and BIOS UUID.
        """
        vm_object_list = self._get_content("vm")
        for vms in vm_object_list:
            logger.info(("VM Name: ", vms.name,
                            " BIOS UUID :", vms.summary.config.uuid,
                            " UUID :", vms.summary.config.instanceUuid))

    def _get_vm_object_by_name(self, vmname):
        """
        method find vm object from list return by _get_content
        Args:
            :vmname    (str) :name of vm that user wants to abstract from vm
                              object list

        Return:
            vm object   (vim.VirtualMachine)

        Raise:
            VmNotFound: Upon VM name not found
        """
        vm_found = False
        vm_object_list = self._get_content("vm")
        for vms in vm_object_list:
            if vms.name == vmname:
                vm_found = True
                return vms
        if not (vm_found):
            raise VmNotFound(vmname)

    def get_vm_name_list(self):
        """
        method that list all VMs in
        Return:
            :list all vms in vcenter
        """
        vms_in_vcenter = []
        vm_object_list = self._get_content("vm")
        for vms in vm_object_list:
            vms_in_vcenter.append(vms.name)
        return vms_in_vcenter

    def is_vm_in_vcenter(self, vmname):
        """
        method that check given vm is in vcenter or not.
        Args:
            :vmname    (str) :name of vm that user wants to check.
        Returns:
            :bool  True : if vm name found in venter.
                   False: if vm name is not found in vcenter.
        """
        vm_object_list = self._get_content("vm")
        return vmname in [x.name for x in vm_object_list]

    def is_vm_interface_exists(self, vmname, interface, portgroup):
        """
        method that check given vm interface is connected or not.
        Args:
            :vm    (str):    name of vm that user wants to check.
            :interface(str): name of vm interface that user wants to check
            example eth1 :   "Network Adapter1" eth2:"Network Adapter2"
                             eth3:"Network Adapter3" eth4:"Network Adapter4"
            :portgroup(str): name of portgroup to check against.
        Returns:
            :bool  True:    if vm nic connected with given interface.
                   False:   if vm nic is not connected with given interface.

        """
        nic_info = self.get_vm_vnic_info(vmname)
        if nic_info is None:
            raise VmNicNotAvailable(vmname, interface)
        if interface not in nic_info.keys():
            return False
        else:
            connected_network = nic_info.get(interface)
        if connected_network == portgroup:
            return True
        else:
            return False

    def is_interface_exists_on_vm(self, vmname, interface):
        """
        method that check given vm interface is connected or not.
        Args:
            :vm    (str):    name of vm that user wants to check.
            :interface(str): name of vm interface that user wants to check
            example eth1 :   "Network Adapter1" eth2:"Network Adapter2"
                             eth3:"Network Adapter3" eth4:"Network Adapter4"
        Returns:
            :bool  True:    if vm nic existed
                   False:   if vm nic is not existed

        """
        nic_info = self.get_vm_vnic_info(vmname)
        if nic_info is None:
            raise VmNicNotAvailable(vmname, interface)
        if interface not in nic_info.keys():
            return False
        return True


    def is_vm_interface_connected(self, vmname, interface, portgroup=None):
        """
        method that check given vm interface is connected or not.
        Args:
            :vm    (str):    name of vm that user wants to check.
            :interface(str): name of vm interface that user wants to check
            example eth1 :   "Network Adapter1" eth2:"Network Adapter2"
                             eth3:"Network Adapter3" eth4:"Network Adapter4"
            :portgroup(str): name of portgroup to check against.
        Returns:
            :bool  True:    if vm nic connected with given interface.
                   False:   if vm nic is not connected with given interface.

        """
        vm_vnic = {}
        vm_obj = self._get_vm_object_by_name(vmname)
        device_info = vm_obj.config.hardware.device
        ethernet_card_info_list = []
        for devices in device_info:
            if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                ethernet_card_info_list.append(devices)
        for ethernet_card in ethernet_card_info_list:
            if ethernet_card.connectable.connected == True:
                vm_vnic[ethernet_card.deviceInfo.label] = \
                    ethernet_card.deviceInfo.summary
        nic_info = vm_vnic
        if nic_info is None:
            raise VmNicNotAvailable(vmname, interface)
        if interface not in nic_info.keys():
            return False
        elif portgroup == None:
            #connected_network = nic_info.get(interface)
            return True

        if portgroup!=None:
            connected_network = nic_info.get(interface)
            if connected_network == portgroup:
                return True
            else:
                return False

    def get_vm_interface_portgroup(self, vmname, interface):
        """
        method that check given vm interface is connected or not.
        Args:
            :vm    (str):    name of vm that user wants to check.
            :interface(str): name of vm interface that user wants to check
            example eth1 :   "Network Adapter1" eth2:"Network Adapter2"
                             eth3:"Network Adapter3" eth4:"Network Adapter4"
            :portgroup(str): name of portgroup to check against.
        Returns:
            :bool  True:    if vm nic connected with given interface.
                   False:   if vm nic is not connected with given interface.

        """
        nic_info = self.get_vm_vnic_info(vmname)
        if nic_info and interface in nic_info.keys():
            portgroup = nic_info.get(interface)
            return portgroup
        logger.warn('vm {} does not have interface {}'.format(vmname, interface))
        return None

    def get_vm_power_state(self, vmname):
        """
        method that check given vm power state
        Args:
            :vmname    (str):   name of vm that user wants to check.

        Returns:
            :powerstate (str): return power state in as a string
                                "poweredoff" and "poweron"

        """
        vm_obj = self._get_vm_object_by_name(vmname)
        summary = vm_obj.summary
        powerstate = summary.runtime.powerState
        logger.info("VM is {}".format(powerstate))
        return summary.runtime.powerState

    def is_vm_power_on(self, vmname):
        """
        method that check given vm is power on or not.
        Args:
            :vmname    (str) :name of vm that user wants to check.

        Returns:
            :bool  True : if vm is power on
                   False: if vm is power off
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        summary = vm_obj.summary
        powerstate = str(summary.runtime.powerState)
        if powerstate.lower() == "poweredoff":
            logger.info("vm {} is powered off".format(vmname))
            return False
        elif powerstate.lower() == "poweredon":
            logger.info("vm {} is powered on".format(vmname))
            return True

    def get_vm_varmour_tag_information(self, vmname, inline_prefix ="va"):
        """
        method that check given vm tags inserted after micro-segmentation.
        Args:
            :vm    (str) :name of vm that user wants to get vm tags.
        Returns:
            :vm_tag_values (dict) : return key-value pair information
        Raise:
            :vMtagNotFound Exception
        """
        vm_tag_values = {}
        vm_obj = self._get_vm_object_by_name(vmname)
        extraConfigList = vm_obj.config.extraConfig
        for optionValue in extraConfigList:
            if inline_prefix+"." in optionValue.key:
                vm_tag_values[optionValue.key] = optionValue.value

        if vm_tag_values != {}:
            logger.info("VM tag information is {}".format(vm_tag_values))
            return vm_tag_values
        else:
            logger.info("VM tag information not found!")
            return None

    def change_microvlan_vatag(self, vmname, portgroup, inline_prefix ="va"):
        """
        method for removing metadata from segmented tag.after segmentation
        metadata is inserted into vm.This method can remove that metadata
        aka tag.
        Args:
            :vmname  (str): name of vm that user wants to remove metadata.
            :portgroup (str):destination portgoup that user wants to move.
            :inline_prefix(str): inline switch prefix.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        specification = vim.vm.ConfigSpec()
        opt = vim.option.OptionValue()
        extraConfigList = vm_obj.config.extraConfig
        for optionValue in extraConfigList:
            if inline_prefix + ".mseg.vs" in optionValue.key:
                opt.key = optionValue.key
                opt.value = portgroup
                specification.extraConfig.append(opt)
                opt = vim.option.OptionValue()
        change_tag_task = vm_obj.ReconfigVM_Task(specification)
        self._wait_for_tasks([change_tag_task], "Changing Microvlan VM Tag")

    def get_vm_storage_path(self, vmname):
        """
        method that gives vm storage path of given vm.
        Args:
            :vmname     (str): name of vm that user wants to get storage path.

        Returns:
            :vm storage path (str) : full path of vm storage
                                    Example "/iSCSI/vm-123/vm-123.vmx"
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        summary = vm_obj.summary
        storage_path = summary.config.vmPathName
        logger.info(
            "VM:{} has storage path {} ".format(vmname, storage_path))
        return storage_path

    def get_vm_os_info(self, vmname):
        """
        method that gives vm operating system information.
        Args:
            :vmname     (str): name of vm that user wants to get operating
                               system.

        Returns:
            :os info    (str):operating system information.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        summary = vm_obj.summary
        os = summary.config.guestFullName
        logger.info("VM:{} running on OS {}".format(vmname, os))
        return os

    def get_vm_ip_address(self, vmname):
        """
        method that gives ipaddress of given vm.vm must have vmtool v 1.0
        install to get this info.

        Args:
            :vmname     (str):  name of vm that user wants to get ip address.
        Returns:
            :ipaddress   (str): operating system information.
            :none               if vmtool is not installed.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        summary = vm_obj.summary
        ipaddress = summary.guest.ipAddress
        if ipaddress:
            return ipaddress
        else:
            return None

    def get_vm_cpu_reservation_info(self, vmname):
        """
        method that gives cpu reservation information about given vm
        Args:
            :vmname     (str): name of vm that user wants to get storage path.
        Returns:
            :ipaddress   (str) : operating system information.
            :none              : if vmtool is not installed.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        summary = vm_obj.summary
        cpu_reservation = summary.cpuReservation
        logger.info("VM:{} has \
            CPU Reservation {}%".format(vmname, cpu_reservation))
        return cpu_reservation

    # TODO: This is not used currently
    def get_vm_fault_tolerance_info(self, vmname):
        """
        method that gives FT information about given vm
        Args:
            :vmname     (str): name of vm that user wants to get storage path.
        Returns:
            :
        Raise:
            vMNotFound Exception
        """
        pass

    def get_vm_bios_uuid(self, vmname):
        """
        method that gives bios uuid about given vm
        Args:
            :vmname     (str): name of vm that user wants to get storage path.
        Returns:
            :bios_uuid (str):bios uuid
        Raise:
            vMNotFound Exception
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        summary = vm_obj.summary
        bios_uuid = summary.config.uuid
        logger.info("VM:{} has uuid {}".format(vmname, bios_uuid))
        return bios_uuid


    def get_vm_instance_uuid(self, vmname):
        """
        method that gives uuid about given vm
        Args:
            :vmname     (str): name of vm that user wants to get storage path.
        Returns:
            :uuid (str): uuid of vm
        Raise:
            vMNotFound Exception
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        vm_uuid = vm_obj.config.uuid
        if vm_uuid:
            logger.info("VM:{} has uuid {}".format(vmname, vm_uuid))
            return vm_uuid
        else:
            raise VmNotFound(vmname)

    def get_vm_no_ethernet_card(self, vmname):
        """
        method that gives number of ethernet card attached with vm.
        Args:
            :vmname     (str): name of vm that user wants to get ethernet card.
        Returns:
            :no of ethernet cards (int): no of ethernet cards.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        config = vm_obj.summary.config
        no_of_ethernet_card = int(config.numEthernetCards)
        logger.info("VM:{} has {} vNICs".format(
            vmname, no_of_ethernet_card))
        return no_of_ethernet_card

    def get_vm_no_cpus(self, vmname):
        """
        method that gives number of cpu attached with vm.
        Args:
            :vmname     (str): name of vm that user wants to get
                               no of cpu/cpus.
        Returns:
            :no of cpu  (int): no of cpus are used.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        config = vm_obj.summary.config
        no_of_cpus = int(config.numCpu)
        logger.info("VM:{} has {} CPUs".format(vmname, no_of_cpus))
        return no_of_cpus

    def get_vm_vnic_info(self, vmname):
        """
        method that gives vm nic info.
        Args:
            :vmname     (str): name of vm that user wants to get vnic info.
        Returns:
            :vm_nic (dict): return dictionary has network name and network
                            label
        """
        vm_vnic = {}
        vm_obj = self._get_vm_object_by_name(vmname)
        device_info = vm_obj.config.hardware.device
        ethernet_card_info_list = []
        for devices in device_info:
            if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                ethernet_card_info_list.append(devices)
        for ethernet_card in ethernet_card_info_list:
            # if ethernet_card.connectable.connected == True:
            vm_vnic[ethernet_card.deviceInfo.label] =\
                ethernet_card.deviceInfo.summary
        return vm_vnic

    def get_vm_all_vnic_connection_info(self, vmname):
        """
        method that gives vnic connection info
        Args:
            :vmname     (str): name of vm that user wants to get vnic
                               connection info.
        Returns:
            :vm_nic (dict): return dictionary has vnic connection info.
        Raise:
            VmNicNotAvailable
        """
        vm_vnic_connection = {}
        vm_obj = self._get_vm_object_by_name(vmname)
        device_info = vm_obj.config.hardware.device
        ethernet_card_info_list = []
        for devices in device_info:
            if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                ethernet_card_info_list.append(devices)
        for ethernet_card in ethernet_card_info_list:
            vm_vnic_connection[
                ethernet_card.deviceInfo.label] = \
                ethernet_card.deviceInfo.connectable.connected
        if vm_vnic_connection != {}:
            return vm_vnic_connection
        else:
            raise VmNicNotAvailable(vmname)

    def get_vm_vnic_connection_info(self, vmname, interface):
        """
        method that gives vnic connection info
        Args:
            :vmname     (str): name of vm that user wants to get vnic
                               connection info.
        Returns:
            :vm_nic (dict): return dictionary has vnic connection info.
        Raise:
            VmNicNotAvailable
        """
        vm_vnic_connect_info = None
        vm_obj = self._get_vm_object_by_name(vmname)
        device_info = vm_obj.config.hardware.device
        ethernet_card_info_list = []
        for devices in device_info:
            if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                ethernet_card_info_list.append(devices)
        for ethernet_card in ethernet_card_info_list:
            if ethernet_card.deviceInfo.label == interface:
                vm_vnic_connect_info = ethernet_card.connectable.connected
        if vm_vnic_connect_info != None:
            return vm_vnic_connect_info
        else:
            raise VmNicNotAvailable(vmname)


    def get_vm_vnic_connection_on_power_info(self, vmname, interface):
        """
        method that gives vnic connection power on info
        Args:
            :vmname     (str): name of vm that user wants to get vnic
                               connection info.
            :interface  (str): name of the vm interface that need to get info
        Returns:
            :boolean     True: if connected power on.
                         False : if connected power off.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        device_info = vm_obj.config.hardware.device
        ethernet_card_info_list = []
        for devices in device_info:
            if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                ethernet_card_info_list.append(devices)
        for ethernet_card in ethernet_card_info_list:
            if ethernet_card.deviceInfo.label == interface:
                return ethernet_card.connectable.startConnected

    def get_vm_vnic_mac_address(self, vmname):
        """
        method that gives vnic mac address information.
        Args:
            :vmname     (str): name of vm that user wants to get
                               vnic connection info.
        Returns:
            :vm_vnic_mac_address (dict): return dictionary has
                                         vnic mac address info.
        Raise:
            vMNotFound Exception
        """
        vm_vnic_mac_address = {}
        vm_obj = self._get_vm_object_by_name(vmname)
        device_info = vm_obj.config.hardware.device
        for devices in device_info:
            if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                vm_vnic_mac_address[
                    devices.deviceInfo.label] = devices.macAddress
        if vm_vnic_mac_address != {}:
            return vm_vnic_mac_address
        else:
            raise VmNicNotAvailable(vmname)

    def is_vm_vnic_connected_to_dvs(self, vmname, interface):
        network = self.get_vm_interface_portgroup(vmname, interface)
        if network and 'DVSwitch' in network:
            return True
        if not network:
            logger.warn('vm {} does not have interface {}'.format(vmname, interface))
        return False

    def get_vm_vnic_all_info(self, vmname, interface):
        """
        method that gives vnic vlanID and vSwitch name
        Args:
            :vmname     (str): name of vm that user wants to get
                               vnic connection info.
            :interface  (str): vm's interface name
        Returns:
            : vm_vnic_all_info (dic) vm's interface related info
        Raise:
            vMNicNotFound Exception
        """
        vm_vnic_info = {}
        try:
            host_object_list = self._get_content("host")
            vm_obj = self._get_vm_object_by_name(vmname)
            dvs_connection = self.is_vm_vnic_connected_to_dvs(vmname, interface)
            device_info = vm_obj.config.hardware.device
            ethernet_card_info_list = []
            for devices in device_info:
                if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                    ethernet_card_info_list.append(devices)
            for ethernet_card in ethernet_card_info_list:
                if ethernet_card.deviceInfo.label == interface:
                    connectOnPower = ethernet_card.connectable.startConnected
                    connectStatus = ethernet_card.connectable.connected
                    if not dvs_connection:
                        portGroup = ethernet_card.backing.network.name
                        vmHost = vm_obj.runtime.host
                        host_pos = host_object_list.index(vmHost)
                        viewHost = host_object_list[host_pos]
                        hostPgDict = self._get_host_portgroups()
                        pgs = hostPgDict[viewHost]
                        for p in pgs:
                            getKey = p.key.split('PortGroup-', 1)
                            portGroupKey = getKey[1]
                            if portGroup == portGroupKey:
                                vm_vnic_info['portGroupName'] = portGroup
                                vm_vnic_info['vlanId'] = [str(p.spec.vlanId)]
                                vm_vnic_info['vSwitchName'] = str(p.spec.vswitchName)
                                vm_vnic_info['connectOnPower'] = connectOnPower
                                vm_vnic_info['connectStatus'] = connectStatus
                                break
                    else:
                        portgroup_key = ethernet_card.backing.port.portgroupKey
                        dvs_uuid = ethernet_card.backing.port.switchUuid
                        try:
                            dvs_obj = self._get_content("content").dvSwitchManager.QueryDvsByUuid(dvs_uuid)
                        except:
                            logger.warn('no vnic information on vm {}'.format(vmname))
                            return None
                        else:
                            dvs_portgroup_obj = dvs_obj.LookupDvPortGroup(portgroup_key)
                            vm_vnic_info['vSwitchName'] = dvs_obj.name
                            vm_vnic_info['portGroupName'] = dvs_portgroup_obj.config.name
                            vm_vnic_info['connectOnPower'] = connectOnPower
                            vm_vnic_info['connectStatus'] = connectStatus
                            vm_vnic_info['vlanId'] = []
                            vlan_type = str(type(dvs_portgroup_obj.config.defaultPortConfig.vlan)).split('.')[-1].split('\'')[0]

                            if 'pvlanspec' in vlan_type.lower():
                                vm_vnic_info['vlanType'] = 'private_vlan'
                                pvlan_configs = dvs_obj.config.pvlanConfig
                                vlan_id = dvs_portgroup_obj.config.defaultPortConfig.vlan.pvlanId
                                for i in range(0, len(pvlan_configs)):
                                    if pvlan_configs[i].secondaryVlanId == vlan_id:
                                        vm_vnic_info['pvlanType'] = pvlan_configs[i].pvlanType
                                        vm_vnic_info['primaryVlanId'] = pvlan_configs[i].primaryVlanId
                                        vm_vnic_info['secondaryVlanId'] = pvlan_configs[i].secondaryVlanId
                                        vm_vnic_info['vlanId'] = [str(vlan_id)]
                            elif 'trunkvlanspec' in vlan_type.lower():
                                vm_vnic_info['vlanType'] = 'trunk_vlan'
                                tvlan_configs = dvs_portgroup_obj.config
                                vlan_ids = tvlan_configs.defaultPortConfig.vlan.vlanId
                                vlans = []
                                for i in range(0, len(vlan_ids)):
                                    start = vlan_ids[i].start
                                    end = vlan_ids[i].end + 1
                                    for j in range(start, end):
                                        vlans.append(str(j))
                                vm_vnic_info['vlanId'] = vlans
                                trunk_all = True
                                for i in range(1, 4095):
                                    if str(i) not in vm_vnic_info['vlanId']:
                                        trunk_all = False
                                        break
                                if trunk_all:
                                    vm_vnic_info['vlanId'].append('all')
                            else:
                                vm_vnic_info['vlanType'] = 'vlan'
                                vlan_configs = dvs_portgroup_obj.config.defaultPortConfig.vlan
                                vm_vnic_info['vlanId'] = [str(vlan_configs.vlanId)]
        #TODO: need to catch a specific exception
        except Exception as e:
            logger.error(e.args[0])
            return None
        else:
            if vm_vnic_info:
                return vm_vnic_info
            logger.warn('no vnic information on vm {}'.format(vmname))
            return None

    def get_vm_vnic_complete_info(self, vmname):
        """
        method that gives vnic complete information
        Args:
            :vmname     (str): name of vm that user wants to get vnic
                               connection info.
        Returns:
            :vm_nic_info (dict): return dictionary has vnic connection info.
        """
        vm_vnic_container = {}  # NOQA
        pass

    def get_vm_mac_network_uplink_info(self, vmname):
        """
        method that gives mac,network tag and uplink info
        which can be useful to generate vm_tag
        Args:
            :vmname     (str): name of vm that user wants to get vnic
                               connection info.
        Returns:
            :vm_network_tag_info (dict): return dictionary has vnic connection
                                         info.
        """
        vm_network_tag_info = {}    # NOQA
        vm_obj = self._get_vm_object_by_name(vmname)
        device_info = vm_obj.config.hardware.device
        for devices in device_info:
            pass

    #TODO: Need to Implement after asking Developers.
    def get_excpected_vm_tag_info(self, vm, vswitch):
        """
        method gives expected vm_tag information before micro-segmentation
        Args:
            :vmname     (str): name of vm that user wants to get vnic
                               connection info.
            :vswitch    (str): attached vswitch information.
        Returns:
            :expected_vm_tag (dict): dictionary has tag info.
        """
        expected_vm_tag = {}    # NOQA

    def get_hostname_by_vm(self, vmname):
        """
        methods gives hostname on which vm is reside.
        Args:
            :vmname    (str): name of vm that user wnats to get host.
        Returns:
            :hostname  (str): name of host where vm resides.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        host_by_vm = vm_obj.runtime.host.name
        return host_by_vm

    def convert_vm_to_template(self, vmname):
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            vm_obj.MarkAsTemplate()
        except VmNotFound as e:
            logger.error(e.args[0])
            return e.args[0]
        return None
        