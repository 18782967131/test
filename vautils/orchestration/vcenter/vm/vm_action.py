"""
coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VmAction class is representing API for various virtual machine related actions
example vmotion,power on vm, power off vm, change vm network etc.
class methods either return string,boolean or managed objects.

.. moduleauthor::jpatel@varmour.com
"""
from pyVmomi import vmodl, vim
from vautils import logger
from vautils.exceptions import VmNicNotAvailable,ClusterNotFound
from vautils.orchestration.vcenter.vm.vcenter_vm import VcenterVMs
from vautils.orchestration.vcenter.host.vcenter_host import VcenterHost
from vautils.orchestration.vcenter.network.\
    vcenter_network import VcenterNetwork


class VmAction(VcenterVMs, VcenterHost, VcenterNetwork):
    """
    VmAction Class is representing appropriate virtual machine operations like
    cloning,vmotion,adding vnic,removing vnic etc.
    """

    def _get_cluster_object_by_name(self, clustername):
        """
        method find cluster object from list return by _get_content
        Args:
            :clustername (str): name of cluster that user wants to abstract from
                             cluster object list
        Return:
            cluster object(vim.ClusterComputeResource)
        Raise:
            ClusterNotFound
        """
        cluster_found = False
        cluster_object_list = self._get_content("cluster")
        for cluster in cluster_object_list:
            if cluster.name == clustername:
                cluster_found = True
                return cluster
        if not (cluster_found):
            raise ClusterNotFound(clustername)

    def _enable_cluster_drs(self, clustername, vmotion_rate = 3):
        """
        method that enable cluster drs .
        Args:
            :hostname  (str): name of host
            :clustername (str): name of DRS cluster where user wants to create vm rule.
            :groupname(str): name of vm group.
        Raise:
            :vmodl Exception.
        """
        try:
            cluster_obj = self._get_cluster_object_by_name(clustername)
            DRSConfig = vim.cluster.DrsConfigInfo()
            #vim.cluster.DrsConfigInfo.DrsBehavior.fullyAutomated
            DRSConfig.enabled = True
            DRSConfig.vmotionRate = vmotion_rate
            DRSConfig.defaultVmBehavior = vim.cluster.DrsConfigInfo.DrsBehavior.fullyAutomated
            clusterSpec = vim.cluster.ConfigSpecEx()
            clusterSpec.drsConfig = DRSConfig
            logger.info("enabling cluster {}".format(clustername))
            enable_task = cluster_obj.ReconfigureEx(spec=clusterSpec, modify=True)
            self._wait_for_tasks([enable_task],
                                        task_name="Enable DRS")

        except vmodl.MethodFault as error:
            logger.error("Exception raise {}".format(error.msg))


    def _disable_cluster_drs(self, clustername):
        """
        method that enable cluster drs .
        Args:
            :hostname  (str): name of host
            :clustername (str): name of DRS cluster where user wants to create vm rule.
            :groupname(str): name of vm group.
        Raise:
            :vmodl Exception.
        """
        try:
            cluster_obj = self._get_cluster_object_by_name(clustername)
            DRSConfig = vim.cluster.DrsConfigInfo()
            DRSConfig.enabled = False
            clusterSpec = vim.cluster.ConfigSpecEx()
            clusterSpec.drsConfig = DRSConfig
            logger.info("enabling cluster {}".format(clustername))
            disable_task = cluster_obj.ReconfigureEx(spec=clusterSpec, modify=True)
            self._wait_for_tasks([disable_task],
                                        task_name="Disable DRS")

        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))

    def _enable_affinity_rule(self,clustername, rule_name, flag = True):
        """
        method that creates DRS affinity rule, i.e vm is staying on the host when
        DRS enable.
        Args:
            :hostname  (str): name of host
            :clustername (str): name of DRS cluster where user wants to create vm rule.
            :hostgroupname(str): name of host group.
            :vmgroupname(str): name of vm group.
            :rule_name (str): name of affinity rule.
        Raise:
            :vmodl Exception.
        """
        try:
            found = False
            cluster_obj = self._get_cluster_object_by_name(clustername)
            rules = cluster_obj.configurationEx.rule
            for rule in rules:
                if rule.name == rule_name:
                    found = True
                    rule_spec = vim.cluster.RuleSpec()
                    rule_spec.operation = "edit"
                    rule_spec.removeKey = rule.key
                    rule_info = vim.cluster.VmHostRuleInfo()
                    rule_info.enabled = flag
                    rule_info.name = rule.name
                    rule_info.key = rule.key
                    rule_info.mandatory = rule.mandatory
                    rule_info.vmGroupName = rule.vmGroupName
                    rule_info.affineHostGroupName = rule.affineHostGroupName
                    rule_info.userCreated = rule.userCreated
                    rule_spec.info = rule_info
                    clusterSpec = vim.cluster.ConfigSpecEx()
                    clusterSpec.rulesSpec.append(rule_spec)
                    if flag:
                        logger.info("Enable affinity rule {} on cluster {}".format(rule_name,clustername))
                    else:
                        logger.info("Disable affinity rule {} on cluster {}".format(rule_name,clustername))

                    enable_rule_task =  cluster_obj.ReconfigureEx(spec=clusterSpec, modify=True)

                    return self._wait_for_tasks([enable_rule_task],
                                        task_name="Change Rule")
            if not found:
                logger.info("Could not find the rule {} on cluster {}".format(rule_name, clustername))
                return "ERROR"
        except vmodl.MethodFault as error:
            logger.error("Exception raise {}".format(error.msg))


    def _check_drs_rule(self,clustername, rule_name, flag):
        """
        method that check if a rule is on the cluster
        Args:
            :hostname  (str): name of host
            :clustername (str): name of DRS cluster where user wants to create vm rule.
            :rule_name (str): name of affinity rule.
            :flag: True to check it is existed, False to check it is not existed
        Raise:
            :vmodl Exception.
        """
        try:
            found = False
            cluster_obj = self._get_cluster_object_by_name(clustername)
            rules = cluster_obj.configurationEx.rule
            for rule in rules:
                if rule.name == rule_name:
                    found = True
                    logger.info("The rule {} found on cluster {} as expected!".format(rule_name, clustername))
                    if flag:
                        return None
                    else:
                        logger.error("The rule {} found on cluster {}".format(rule_name, clustername))
                        return "ERROR"
            if not found:
                if flag:
                    logger.error("The rule {} NOT found on cluster {}".format(rule_name, clustername))
                    return "ERROR"
                else:
                    logger.info("The rule {} NOT found on cluster {} as expected".format(rule_name, clustername))
                    return None

        except vmodl.MethodFault as error:
            logger.error("Exception in _check_drs_rule: {}".format(error.msg))
            return error.msg

    def _create_cluster_group_by_host(self, hostname, clustername, groupname="host-group-1"):
        """
        method that creates DRS host group.
        Args:
            :hostname  (str): name of host
            :clustername (str): name of DRS cluster where user wants to create host rule.
            :groupname(str): name of host group.
        Raise:
            :vmodl Exception.
        """
        try:
            host_obj = self._get_host_object_by_name(hostname)
            cluster_obj = self._get_cluster_object_by_name(clustername)
            cluster_group_info = vim.cluster.HostGroup()
            cluster_group_info.name = groupname
            cluster_group_info.host = [host_obj]
            group_spec = vim.cluster.GroupSpec()
            group_spec.info = cluster_group_info
            group_spec.operation = 'add'
            group_spec.removeKey = groupname

            clusterSpec = vim.cluster.ConfigSpecEx()
            clusterSpec.groupSpec.append(group_spec)

            logger.info("Creating group {} on the host {}".format(groupname,hostname))
            host_group_task = cluster_obj.ReconfigureEx(spec=clusterSpec, modify=True)
            self._wait_for_tasks([host_group_task],
                                        task_name="Host Group Creation")
        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))


    def _create_cluster_group_by_vms(self, hostname, clustername, groupname = "vm-group-1"):
        """
        method that creates DRS vm group.
        Args:
            :hostname  (str): name of host
            :clustername (str): name of DRS cluster where user wants to create vm rule.
            :groupname(str): name of vm group.
        Raise:
            :vmodl Exception.
        """
        try:

            vm_obj_in_host = []
            host_obj = self._get_host_object_by_name(hostname)
            for vm_obj in host_obj.vm:
                vm_obj_in_host.append(vm_obj)
            cluster_obj = self._get_cluster_object_by_name(clustername)

            cluster_group_info = vim.cluster.VmGroup()
            cluster_group_info.name = groupname
            cluster_group_info.vm = vm_obj_in_host

            group_spec = vim.cluster.GroupSpec()
            group_spec.info = cluster_group_info
            group_spec.operation = 'add'
            group_spec.removeKey = groupname

            clusterSpec = vim.cluster.ConfigSpecEx()
            clusterSpec.groupSpec.append(group_spec)

            logger.info("Creating VM group {} on the host {}".format(groupname,hostname))
            vm_group_task = cluster_obj.ReconfigureEx(spec=clusterSpec, modify=True)
            self._wait_for_tasks([vm_group_task],
                                        task_name="VM Group Creation")
        except vmodl.MethodFault as error:
            logger.error("Exception raise {}".format(error.msg))


    def create_affinity_rule_for_host(self, hostname, clustername,
                                            hostgroupname="host-group-1",
                                            vmgroupname="vm-group-1",
                                            rule_name = "affinity-rule-1"):
        """
        method that creates DRS affinity rule, i.e vm is staying on the host when
        DRS enable.
        Args:
            :hostname  (str): name of host
            :clustername (str): name of DRS cluster where user wants to create vm rule.
            :hostgroupname(str): name of host group.
            :vmgroupname(str): name of vm group.
            :rule_name (str): name of affinity rule.
        Raise:
            :vmodl Exception.
        """
        try:
            cluster_obj = self._get_cluster_object_by_name(clustername)
            self._create_cluster_group_by_host(hostname, clustername,hostgroupname)
            self._create_cluster_group_by_vms(hostname, clustername,vmgroupname)

            vm_host_rule_info = vim.cluster.VmHostRuleInfo()

            vm_host_rule_info.name = rule_name
            vm_host_rule_info.enabled = True
            vm_host_rule_info.mandatory = True
            vm_host_rule_info.vmGroupName = vmgroupname
            vm_host_rule_info.affineHostGroupName = hostgroupname
            rule_spec = vim.cluster.RuleSpec()
            rule_spec.operation = 'add'
            rule_spec.info = vm_host_rule_info
            rule_spec.removeKey = vm_host_rule_info.key


            clusterSpec = vim.cluster.ConfigSpecEx()
            clusterSpec.rulesSpec.append(rule_spec)

            logger.info("Creating affinity rule {} on cluster {}".format(rule_name,clustername))

            affinity_rule_task =  cluster_obj.ReconfigureEx(spec=clusterSpec, modify=True)

            return self._wait_for_tasks([affinity_rule_task],
                                        task_name="Affinity Rule Creation")

        except vmodl.MethodFault as error:
            logger.error("Exception raise {}".format(error.msg))

    def vmotion(self, vmname, hostname):
        """
        method to apply vmware vmotion on vm.
        Args:
            :vmname    (str): name of vm that user wants to abstract from vm
                              object list.
            :hostname  (str): name of destination host where vm
        Return:
            :result (bool) True:  If Successfully completed.
                           False: If vMotion Failed.
        Raise:
            :vmodl Exception.
        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            host_obj = self._get_host_object_by_name(hostname)
            vm_resource_pool = None
            for vms in host_obj.vm:
                if vms.resourcePool is not None:
                    vm_resource_pool = vms.resourcePool
                    break
                else:
                    continue
            if (vm_obj.summary.runtime.powerState != "poweredOn"):
                logger.warning("Vmotion is applying on powered off VM:{}".format(vmname))
            vm_migration_priority = \
                vim.VirtualMachine.MovePriority.defaultPriority
            logger.info("Vmotion Start on VM: {} and destination"
                           "host is {}".format(vmname, hostname))
            vmotion_task = vm_obj.Migrate(host=host_obj,
                                          priority=vm_migration_priority,
                                          pool=vm_resource_pool)
            return self._wait_for_tasks([vmotion_task],
                                        task_name="Vmotion VM")
        except vmodl.MethodFault as error:
            logger.error("Exception raise {}".format(error.msg))

    def change_vm_vnic(self, vmname, interface, network):
        """
        method that change vm's vnic's network(portgroup).
        Args:
            :vmname   (str): name of vm that user wants to change network.
            :interface(str): VM's network interface.
                              example, "Network adapter 1".
            :network   (str): Destination network where user wants to move
                              interface.
        Raise:
              :VmNicNotAvailable,vmodl Exception.
        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            net_obj = self._get_network_object_by_name(network)
            dvs_connection = self.is_network_connected_to_dvs(network)
            vnic_change = []
            for device in vm_obj.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    if device.deviceInfo.label == interface:
                        nic_card_spec = vim.vm.device.VirtualDeviceSpec()
                        nic_card_spec.operation = \
                            vim.vm.device.VirtualDeviceSpec.Operation.edit
                        nic_card_spec.device = device
                        nic_card_spec.device.wakeOnLanEnabled = True
                        if not dvs_connection:   # This is for VSS connection.
                            nic_card_spec.device.backing = vim.vm.device.\
                                VirtualEthernetCard.NetworkBackingInfo()
                            nic_card_spec.device.backing.network = net_obj
                            nic_card_spec.device.backing.deviceName = \
                                net_obj.name
                        else:                    # This is for VDS Connection.
                            net_obj = self._get_dvs_object_by_name(network)
                            dvs_port_connection = vim.dvs.PortConnection()
                            dvs_port_connection.portgroupKey = net_obj.key
                            dvs_port_connection.switchUuid = \
                                net_obj.config.distributedVirtualSwitch.uuid
                            nic_card_spec.device.backing = \
                                vim.vm.device.VirtualEthernetCard.\
                                DistributedVirtualPortBackingInfo()
                            nic_card_spec.device.backing.port = \
                                dvs_port_connection
                        nic_card_spec.device.connectable = \
                            vim.vm.device.VirtualDevice.ConnectInfo()
                        nic_card_spec.device.connectable.startConnected = True
                        nic_card_spec.device.connectable.connected = True
                        nic_card_spec.device.connectable.allowGuestControl = \
                            True
                        vnic_change.append(nic_card_spec)
            if vnic_change != []:
                change_nic_config_spec = \
                    vim.vm.ConfigSpec(deviceChange=vnic_change)
                vnic_change_task = \
                    vm_obj.ReconfigVM_Task(change_nic_config_spec)
                self._wait_for_tasks([vnic_change_task], "Change VNIC")
            else:
                logger.error("VM: {} has no interface name {}."
                                "Please Check Config and Try to change back".
                                format(vmname, interface))
                raise VmNicNotAvailable(vmname, interface)
        except vmodl.MethodFault as error:
            logger.error("Exception raise {}".format(error.msg))

    # Not required now. will be implemented when needed.
    def clone_vm(self, vmname):
        """
        method to clone given vm.
        Args:
            :vmname    (str) :name of vm that user wants to abstract from vm
                              object list
        Return:
            :result (bool) True: If Successfully Cloned.
                           False: If Cloning Failed.
        Raise:
              vMNotFound Exception.
        """
        vm_obj = self._get_vm_object_by_name(vmname)  # NOQA

    def power_on_vm(self, vmname):
        """
        method to power on given VM.
        Args:
            :vmname    (str) :name of vm that user wants to abstract from vm
                              object list
        Return:
            :result (bool) True: If Successfully ON.
                           False: If Fail to VM Power ON.
        Raise:
              vMNotFound Exception.
        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            logger.info("VM {} is \
                {}".format(vmname, vm_obj.runtime.powerState))
            if(self.is_vm_power_on(vm_obj.name)):
                logger.warning(
                    "VM {} is already powered on, Can not perform \
                    this operation".format(vmname))
            else:
                power_on_vm_task = vm_obj.PowerOnVM_Task()
                return self._wait_for_tasks([power_on_vm_task],
                                            task_name="Power On VM")
        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))
            return error.msg

    def power_off_vm(self, vmname):
        """
        method to power off given VM.
        Args:
            :vmname    (str) :name of vm that user wants to abstract
                              from vm object list
        Return:
            :result (bool) True: If Successfully OFF.
                           False: If Fail to VM Power OFF.
        Raise:
              vMNotFound Exception.
        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            logger.info("VM {} is \
                {}".format(vmname, vm_obj.runtime.powerState))
            if(self.is_vm_power_on(vm_obj.name)):
                power_off_vm_task = vm_obj.PowerOffVM_Task()
                return self._wait_for_tasks([power_off_vm_task],
                                            task_name="Power Off VM")
            else:
                logger.warning(
                    "VM {} is already powered off, \
                    Can not perform this operation".format(vmname))
        except vmodl.MethodFault as error:
            logger.error("Exception raise {}".format(error.msg))
            return error.msg

    def reset_vm(self, vmname):
        """
        method to reset given VM.
        Args:
            :vmname    (str) :name of vm that user wants to abstract
                              from vm object list
        Return:
            :result (bool) True: If Successfully reset.
                           False: If Fail to reset.
        Raise:
              vMNotFound Exception.
        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            logger.info("VM {} is"
                           "{}".format(vmname, vm_obj.runtime.powerState))
            reset_vm_task = vm_obj.ResetVM_Task()
            return self._wait_for_tasks([reset_vm_task],
                                        task_name="Reset VM")
        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))
            return error.msg

    # Need To Implement
    def add_vm(self, vmname):
        """
        method to adding new VM.
        Args:
            :vmname    (str) :name of vm that user wants to abstract from
                              vm object list
        Return:
            :result (bool) True: If Successfully added.
                           False: If Fail to add.
        """
        pass

    # Need To Implement
    def remove_vm(self, vmname):
        """
        method to removing  VM.
        Args:
            :vmname    (str) :name of vm that user wants to abstract from
                              vm object list
        Return:
            :result (bool) True: If Successfully removed.
                           False: If Fail to remove.
        """
        try:
            self.power_off_vm(vmname)
            vm_obj = self._get_vm_object_by_name(vmname)
            delete_vm_task = vm_obj.Destroy_Task()
            return self._wait_for_tasks([delete_vm_task],
                                        task_name="Delete VM")
        except vmodl.MethodFault as error:
            self._log.error("Exception raised in remove_vm{}".format(error.msg))
            return error.msg

    def add_vm_vnic(self, vmname, portgroup):
        """
        method to adding new vnic.
        Args:
            :vmname    (str) :name of vm that user wants to abstract from
                              vm object list
        Return:
            :result (bool) True: If Successfully added vnic.
                           False: If Fail to remove vnic.

        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            nic_change = []
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.Operation.add

            nic_spec.device = vim.vm.device.VirtualVmxnet()
            nic_spec.device.deviceInfo = vim.Description()
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_spec.device.backing.useAutoDetect = False

            nic_spec.device.backing.network = \
                self._get_network_object_by_name(portgroup)

            nic_spec.device.backing.deviceName = portgroup

            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nic_spec.device.connectable.startConnected = True
            nic_spec.device.connectable.startConnected = True
            nic_spec.device.connectable.allowGuestControl = True
            nic_spec.device.connectable.connected = False
            nic_spec.device.connectable.status = 'untried'

            nic_spec.device.wakeOnLanEnabled = True
            nic_spec.device.addressType = 'assigned'
            nic_change.append(nic_spec)


            add_nic_spec = \
                    vim.vm.ConfigSpec(deviceChange=nic_change)
            add_nic_task = \
                    vm_obj.ReconfigVM_Task(spec=add_nic_spec)
            self._wait_for_tasks([add_nic_task],
                                     "add nic")

        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))


    def remove_vm_vnic(self, vmname, interface):
        """
        method to removing vnic from vm.
        Args:
            :vmname    (str) :name of vm that user wants to abstract from
                              vm object list
        Return:
            :result (bool) True: If Successfully vnic removed.
                           False: If Fail to remove vnic.
        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            nic_change = []
            for device in vm_obj.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    if device.deviceInfo.label == interface:
                        nic_card_spec = vim.vm.device.VirtualDeviceSpec()
                        nic_card_spec.operation = \
                            vim.vm.device.VirtualDeviceSpec.Operation.remove
                        nic_card_spec.device = device
                        nic_change.append(nic_card_spec)

            if nic_change != []:
                delete_nic_config_spec = \
                    vim.vm.ConfigSpec(deviceChange=nic_change)
                delete_nic_task = \
                    vm_obj.ReconfigVM_Task(spec=delete_nic_config_spec)
                self._wait_for_tasks([delete_nic_task],
                                     "delete nic")
            else:
                logger.error("VM: {} has no interface name {}. "
                                "Please Check Config and Try to change "
                                "back".format(vmname, interface))
                raise VmNicNotAvailable(vmname, interface)
        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))

    def remove_tag_from_vm(self, vmname, inline_prefix="va"):
        """
        method for removing metadata from segmented tag.after segmentation
        metadata is inserted into vm.This method can remove that metadata
        aka tag.
        Args:
            :vmname  (str): name of vm that user wants to remove metadata.
            :inline_prefix (str): inline switch prefix.
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        specification = vim.vm.ConfigSpec()
        opt = vim.option.OptionValue()
        extraConfigList = vm_obj.config.extraConfig
        for optionValue in extraConfigList:
            if inline_prefix +"." in optionValue.key:
                opt.key = optionValue.key
                opt.value = ""
                specification.extraConfig.append(opt)
                opt = vim.option.OptionValue()
        remove_tag_task = vm_obj.ReconfigVM_Task(specification)
        self._wait_for_tasks([remove_tag_task], "Removing VM Tag")

    def change_mseg_tag(self, vmname, mseg_pg, mseg_vlan, inline_prefix="va"):
        """
        method for removing metadata from segmented tag.after segmentation
        metadata is inserted into vm.This method modify microseg portgroup and vlan
        Args:
            :vmname  (str): name of vm that user wants to remove metadata.
            :mseg_pg (str): name of mseg portgoup
            :mseg_vlan(str): vlanID mseg_pg
            :inline_prefix(str): switch prefix
        """
        vm_obj = self._get_vm_object_by_name(vmname)
        specification = vim.vm.ConfigSpec()
        opt = vim.option.OptionValue()
        extraConfigList = vm_obj.config.extraConfig
        for optionValue in extraConfigList:
            if inline_prefix + ".mseg.pg" in optionValue.key:
                opt.key = optionValue.key
                opt.value = mseg_pg
                specification.extraConfig.append(opt)
                opt = vim.option.OptionValue()
            if inline_prefix + ".mseg.vlan" in optionValue.key:
                opt.key = optionValue.key
                opt.value = mseg_vlan
                specification.extraConfig.append(opt)
                opt = vim.option.OptionValue()
        change_tag_task = vm_obj.ReconfigVM_Task(specification)
        self._wait_for_tasks([change_tag_task], "Changing VM Tag")

    def change_vm_nic_mac_address(self, vmname, interface, macaddress):
        """
        method that change vm's vnic's MAC address provided by user.
        Args:
            :vmname   (str): name of vm that user wants to change network.
            :interface(str): VM's network interface.
                              example, "Network adapter 1".
            :macaddress   (str):user assigned mac address
        Raise:
              :VmNicNotAvailable,vmodl Exception.
        """
        try:
            vm_obj = self._get_vm_object_by_name(vmname)
            mac_address_change = []
            for device in vm_obj.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    if device.deviceInfo.label == interface:
                        nic_card_spec = vim.vm.device.VirtualDeviceSpec()
                        nic_card_spec.operation = \
                            vim.vm.device.VirtualDeviceSpec.Operation.edit
                        nic_card_spec.device = device
                        nic_card_spec.device.macAddress = macaddress
                        mac_address_change.append(nic_card_spec)
            if mac_address_change != []:
                change_mac_config_spec = \
                    vim.vm.ConfigSpec(deviceChange=mac_address_change)
                mac_address_change_task = \
                    vm_obj.ReconfigVM_Task(change_mac_config_spec)
                self._wait_for_tasks([mac_address_change_task],
                                     "Change MAC Address")
            else:
                logger.error("VM: {} has no interface name {}. "
                                "Please Check Config and Try to change "
                                "back".format(vmname, interface))
                raise VmNicNotAvailable(vmname, interface)
        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))

    def update_vm_virtual_nic_state(self,vmname,nic,new_nic_state):
        """
        method that change vm's vnic's MAC address provided by user.
        Args:
            :vmname   (str): name of vm that user wants to change network.
            :nic(str): VM's network interface.
                              example, "Network adapter 1".
            :new_nic_state   (str): connect/disconnect/delete
        Raise:
              :VmNicNotAvailable,vmodl Exception.
        """

        try:
            virtual_nic_device = None
            vm_obj = self._get_vm_object_by_name(vmname)
            for dev in vm_obj.config.hardware.device:
                 if isinstance(dev, vim.vm.device.VirtualEthernetCard) \
                    and dev.deviceInfo.label == nic:
                    virtual_nic_device = dev
            if not virtual_nic_device:
                raise RuntimeError('Virtual {} could not be found.'.format(nic))

            virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
            virtual_nic_spec.operation = \
                vim.vm.device.VirtualDeviceSpec.Operation.remove \
                if new_nic_state == 'delete' \
                else vim.vm.device.VirtualDeviceSpec.Operation.edit
            virtual_nic_spec.device = virtual_nic_device
            virtual_nic_spec.device.key = virtual_nic_device.key
            virtual_nic_spec.device.macAddress = virtual_nic_device.macAddress
            virtual_nic_spec.device.backing = virtual_nic_device.backing
            #virtual_nic_spec.device.backing.port = \
                #virtual_nic_device.backing.port
            virtual_nic_spec.device.wakeOnLanEnabled = \
                virtual_nic_device.wakeOnLanEnabled
            connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            if new_nic_state == 'connect':
                connectable.connected = True
                connectable.startConnected = True
            elif new_nic_state == 'disconnect':
               connectable.connected = False
               connectable.startConnected = False
            else:
                connectable = virtual_nic_device.connectable
            virtual_nic_spec.device.connectable = connectable
            dev_changes = []
            dev_changes.append(virtual_nic_spec)
            spec = vim.vm.ConfigSpec()
            spec.deviceChange = dev_changes
            task = vm_obj.ReconfigVM_Task(spec=spec)
            self._wait_for_tasks([task], "Update nic state")
        except vmodl.MethodFault as error:
            logger.error("Exception raised {}".format(error.msg))

    def get_vm_from_portgroup(self, hostname, portgroup):
        """
        methods gives list of vm belong to hostname and portgroup.
        Args:
            :hostname    (str): name of host.
            :portgroup   (str): portgroup name.
        Returns:
            :vm_list  (list): vm list that belong to host and pg.
        """
        vm_list = []
        host_obj = self._get_host_object_by_name(hostname)
        net_obj = self._get_network_object_by_name(portgroup)
        vms_in_host_obj = set(host_obj.vm)
        vms_in_network = set(net_obj.vm)
        vms_in_portgroup = list(vms_in_host_obj.intersection(vms_in_network))
        if len(vms_in_portgroup) != 0:
            for vms in vms_in_portgroup:
                vm_list.append(vms.name)
        else:
            logger.info("There is no VM in portgroup \
                    {} on host {}".format(portgroup,hostname))
        return vm_list


    def change_vm_name(self, oldname, newname):
        try:
            vm_obj = self._get_vm_object_by_name(oldname)
            VM = self.content.searchIndex.FindByUuid(None,vm_obj.config.uuid,
                                               True,
                                               False)

            specification = vim.vm.ConfigSpec(name = newname)
            task = VM.ReconfigVM_Task(specification)
            return self._wait_for_tasks([task],task_name ="Rename VM")
        except Exception as error:
            logger.error("Exception raised {}".format(error.msg))