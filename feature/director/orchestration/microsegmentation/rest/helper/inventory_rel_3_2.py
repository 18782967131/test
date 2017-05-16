"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaInventory parse va rest response into meaningful information

.. moduleauthor:: ckung@varmour.com
"""
from access import logger
from feature.director.orchestration.microsegmentation.rest.microsegmentation_rest_3_1 import VaMicrosegmentation

class VaInventory(VaMicrosegmentation):
    def va_inventory_get_workload_information_by_host(self, instance, datacenter_name, hostname, portgroup, vlan):
        """
        get workload information with hostname parameter

        :param instance: vcenter instance
        :type instance: str
        :param datacenter_name: datacenter name
        :type datacenter_name: str
        :param hostname: host name
        :type hostname: str
        :param portgroup: port group
        :type portgroup: str
        :param vlan: vlan
        :type vlan: str
        :return: | {
                 |     'totalWorkload': '0',
                 |     'segWorkload': '0',
                 |     'nonsegWorkload': '0'
                 | }
        :type: dict
        """
        params = {'instance': instance, 'domain': datacenter_name}
        result = self.va_rest_get_segmentation_info(params)
        if self._check_failed_message(result):
            return result
        workload_infos = None
        if 'hosts' in result.keys():
            for host in result['hosts']:
                if 'name' in host.keys() and host['name'] == hostname:
                    if not workload_infos:
                        workload_infos = {}
                    workload_infos['totalWorkload'] = host['workload_count']
                    workload_infos['segWorkload'] = '0'
                    workload_infos['nonsegWorkload'] = '0'
                    if 'workloads' in host.keys():
                        for workload in host['workloads']:
                            if 'interfaces' in workload.keys():
                                for interface in workload['interfaces']:
                                    if 'pre-mseg' in interface.keys() and 'vlan' in interface['pre-mseg'].keys():
                                        if interface['pre-mseg']['vlan'] == vlan:
                                            if 'microsegmented' in interface.keys() and interface['microsegmented']:
                                                workload_infos['segWorkload'] = str(
                                                    int(workload_infos['segWorkload']) + 1)
                                            else:
                                                workload_infos['nonsegWorkload'] = str(
                                                    int(workload_infos['nonsegWorkload']) + 1)
        return self._return_result(workload_infos)
