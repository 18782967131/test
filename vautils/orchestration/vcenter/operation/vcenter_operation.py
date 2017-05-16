"""
coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

this class is doing vcenter related operations like creating backup
move vms to correct place in case of disaster.


.. moduleauthor::jpatel@varmour.com

"""
from vautils.orchestration.vcenter.vm.vm_action import VmAction
from pyVmomi import vim
from vautils import logger
import ast


class VcenterOperation(VmAction):
    """
    VcenterOperation class has methods for creating and applying bcakup.
    in the case of disaster, VcenterOperation class recovers test-bed.
    """

    def take_backup_vcenter(self, filename=None):
        """
        this method is taking snapshot of test-bed and returning file or
        json datastucture as a snapshot of vcenter topology.Note here,
        It takes snapshot of entire vcenter.It also saves returned value
        in a file provide by user.
        Args:
                :filename (str): full path of the file and filename where
                              user wants to save file.
        Returns:
                :data  (list):return data as list of json format so user can
                                store this data for test-bed recovery.
        """
        metadata_for_vcenter = []
        vm_obj_list = self._get_content("vm")
        dvs_obj_list = self._get_content("dvs")
        for vm_obj in vm_obj_list:
            vm_json = {}
            if 'name' not in dir(vm_obj.runtime.host):
                continue
            host = vm_obj.runtime.host.name
            device_info = vm_obj.config.hardware.device
            vm_network_list = []
            for devices in device_info:
                if isinstance(devices, vim.vm.device.VirtualEthernetCard):
                    vm_network = {}
                    if "DVSwitch:" in devices.deviceInfo.summary:
                        port_group_key = devices.backing.port.portgroupKey
                        pg_data = None
                        if list(filter(lambda x: x.key == \
                                port_group_key,dvs_obj_list)) != []:
                            pg_data = list(filter(
                                lambda x: x.key == port_group_key,
                                dvs_obj_list)).pop()
                        summary_for_vds = pg_data.name
                        vm_network[devices.deviceInfo.label] = summary_for_vds
                    else:
                        vm_network[
                            devices.deviceInfo.label] = \
                            devices.deviceInfo.summary
                    vm_network_list.append(vm_network)
            vm_json['name'] = vm_obj.name
            vm_json['host'] = host
            vm_json['network'] = vm_network_list
            metadata_for_vcenter.append(vm_json)
        try:
            if filename:
                fd = open(filename, 'w')
                fd.writelines(str(metadata_for_vcenter))
        except IOError:
            logger.error("Can not Open file {}. Please see filename and\
            path".format(filename))
        return metadata_for_vcenter

    def recover_vcenter_workloads(self, filename=None):
        """
        this method is apply to recover workloads. i.e
        putting workloads to its original state.this method is used
        for disaster recovery.
        Args:
                :original (list): original backup list where,
                 user wants to revert back.
        """
        if not filename:
            return
        original = ''
        try:
            fd = open(filename, 'r')
            for lines in fd.readline():
                original += lines
            fd.close()
        except IOError:
            logger.error("Can not Open file {}. Please see filename and\
                       path".format(filename))

        original_state = ast.literal_eval(original)
        current_state = self.take_backup_vcenter()
        for current_obj in current_state:
            vm = current_obj['name']
            current_host = current_obj['host']
            current_network = current_obj['network']
            for original_obj in original_state:
                if original_obj['name'] == vm:
                    if original_obj['host'] == current_host:
                        logger.info(
                            "Host of VM:{} is the same as "
                            "original. Not changed.".format(vm))
                    else:
                        logger.info(
                            "Host is not the same for VM:{}"
                            "original host was {}, changed "
                            "host is {}."
                            .format(vm, original_obj['host'], current_host))
                        logger.info(
                            "Going to change host for VM:{}...".format(vm))
                        self.vmotion(vm, original_obj['host'])

                    if current_network == original_obj["network"]:
                        logger.info(
                            "Network of VM:{} is the same as original."
                            " Not changed.".format(vm))
                    else:
                        logger.info("Network is not the same for VM:{}"
                                       " original network was {}, "
                                       "changed network is "
                                       "{}".format(vm, original_obj["network"],
                                                   current_network))
                        logger.info("Network is going to change....")
                        logger.info("Removing va-tag..")
                        self.remove_tag_from_vm(vm)
                        for nets in original_obj["network"]:
                            for interface, portgroup in nets.items():
                                self.change_vm_vnic(vm, interface, portgroup)
