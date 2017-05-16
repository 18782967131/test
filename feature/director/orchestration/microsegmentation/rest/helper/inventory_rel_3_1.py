"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaInventory parse va rest response into meaningful information

.. moduleauthor:: ckung@varmour.com
"""
from access import logger
from feature.director.orchestration.microsegmentation.rest.helper.rest_api_rel_3_1 import VaRestapi


class VaInventory(VaRestapi):
    """
    VaInventory is designed for parsing inventory information into
    meaningful information
    """
    STARS = '*****'
    DOTS = '...'

    def _va_message_helper(self, method_name, position='start', result=None, success=True):
        """
        print message

        :param method_name: method name
        :type method_name: str
        :param position: beginning or end of message
        :type position: str
        :param success: method runs successful or not
        :type success: bool
        """
        if position == 'start':
            logger.info('%s %s start %s' % (self.STARS, method_name, self.STARS))
        else:
            if result:
                if success:
                    logger.info('%s %s returns - %s %s' % (self.DOTS, method_name, result, self.DOTS))
                else:
                    logger.error('%s %s returns empty result %s' % (self.DOTS, method_name, self.DOTS))
            else:
                if success:
                    logger.info('%s %s succeeded %s' % (self.DOTS, method_name, self.DOTS))
                else:
                    logger.error('%s %s failed %s' % (self.DOTS, method_name, self.DOTS))
            logger.info('%s %s finish %s' % (self.STARS, method_name, self.STARS))

    def _va_check_input_data(self, method_name, input_params=None):
        """
        check input data

        :param method_name: method name
        :type method_name: str
        :param input_data: input data to be checked
        :type input_data: dict or list
        :param show: print message
        :type show: bool
        :return: error message if any
        :type: str
        """
        if input_params and type(input_params) is dict and None in input_params.values():
            self._va_error_message(method_name, 'invalid parameters: ' + str(input_params), True)
            self._va_message_helper(method_name, 'end', None, False)
            return self._va_error_message(method_name, 'invalid parameters: ' + str(input_params))
        if input_params and type(input_params) is list and None in input_params:
            self._va_error_message(method_name, 'invalid parameters: ' + str(input_params), True)
            self._va_message_helper(method_name, 'end', None, False)
            return self._va_error_message(method_name, 'invalid parameters: ' + str(input_params))

    def _check_failed_message(self, result, method_name=None):
        """

        :param result: response
        :type result: dict
        :return:
        """
        if result and type(result) is str and 'fail' in result.lower():
            if method_name:
                self._va_message_helper(method_name, 'end', None, False)
            return True
        return False

    def _return_result(self, result, fail_response=True):
        if result:
            return result
        elif fail_response:
            return 'failed due to empty inventory results'

    def va_inventory_get_datacenters(self, instance):
        """
        get all datacenter names

        :param instance: vcenter instance
        :type instance: str
        :return: all datacenter names
        :type: list
        """
        params = {'instance': instance}
        result = self.va_rest_get_inventory(params)
        if self._check_failed_message(result):
            return result
        datacenters = None
        if result:
            for data in result:
                if not datacenters:
                    datacenters = []
                datacenters.append(data['name'])
        return self._return_result(datacenters)

    def va_inventory_get_hosts_by_datacenter(self, instance, datacenter_name):
        """
        get all hosts information

        :param instance: vcenter instance
        :type instance: str
        :param datacenter_name: datacenter name
        :type datacenter_name: str
        :return: all host information in the datacenter
        :type: list
        """
        params = {'domain': datacenter_name, 'instance': instance}
        result = self.va_rest_get_hosts_inventory(params)
        if self._check_failed_message(result):
            return result
        hosts = None
        if datacenter_name in result.keys():
            if not hosts:
                hosts = []
            for key, value in result[datacenter_name].items():
                for host in value:
                    hosts.append(host['name'])
        return self._return_result(hosts)

    def va_inventory_get_datacenters_by_host(self, instance, hostname):
        """
        get datacenter name with hostname parameter

        :param instance: vcenter instance
        :type instance: str
        :param hostname: hostname
        :type hostname: str
        :return: datacenter
        :type: str
        """
        datacenters = self.va_inventory_get_datacenters(instance)
        if self._check_failed_message(datacenters):
            return datacenters
        datacenter_name = None
        for datacenter in datacenters:
            hostname_res = self.va_inventory_get_hosts_by_datacenter(instance, datacenter)
            if self._check_failed_message(hostname_res):
                return hostname_res
            elif hostname in hostname_res:
                datacenter_name = datacenter
                break
        return self._return_result(datacenter_name)

    def va_inventory_get_epi_uuid_by_host(self, instance, datacenter_name, hostname):
        """
        get epi uuid with datacenter name and host name parameters

        :param instance: vcenter instance
        :type instance: str
        :param datacenter_name: datacenter name
        :type datacenter_name: str
        :param hostname: host name
        :type hostname: str
        :return: epi uuid
        :type: str
        """
        params = {'domain': datacenter_name, 'instance': instance}
        result = self.va_rest_get_hosts_inventory(params)
        if self._check_failed_message(result):
            return result
        epi_uuid = None
        if datacenter_name in result.keys():
            for key, value in result[datacenter_name].items():
                for host in value:
                    if 'name' in host.keys() and host['name'] == hostname:
                        if 'epis' in host.keys():
                            epis = host['epis']
                            if len(epis) == 1:
                                if 'uuid' in epis[0].keys():
                                    epi_uuid = epis[0]['uuid']
                                    break
        return self._return_result(epi_uuid)

    def va_inventory_get_host_uuid(self, instance, datacenter_name, hostname):
        """
        get host uuid

        :param instance: vcenter instance
        :type instance: str
        :param datacenter_name: datacenter name
        :type datacenter_name: str
        :param hostname: host name
        :type hostname: str
        :return: host uuid
        :type: str
        """
        params = {'domain': datacenter_name, 'instance': instance}
        result = self.va_rest_get_hosts_inventory(params)
        if self._check_failed_message(result):
            return result
        host_uuid = None
        if datacenter_name in result.keys():
            for key, value in result[datacenter_name].items():
                for host in value:
                    if 'name' in host.keys() and host['name'] == hostname:
                        if 'uuid' in host.keys():
                            host_uuid = host['uuid']
                            break
        return self._return_result(host_uuid)

    def va_inventory_get_vlan_by_portgroup(self, instance, datacenter_name, hostname, portgroup):
        """
        get vlan information

        :param instance: vcenter instance
        :type instance: str
        :param datacenter_name: datacenter name
        :type datacenter_name: str
        :param hostname: host name
        :type hostname: str
        :param portgroup: port group
        :type portgroup: str
        :return: vlan information
        :type: str
        """
        params = {'domain': datacenter_name, 'instance': instance}
        result = self.va_rest_get_hosts_inventory(params)
        if self._check_failed_message(result):
            return result
        vlan = None
        if datacenter_name in result.keys():
            for key, value in result[datacenter_name].items():
                for host in value:
                    if 'name' in host.keys() and host['name'] == hostname:
                        if 'workloads' in host.keys() and host['workloads']:
                            for workload in host['workloads']:
                                if 'interfaces' in workload.keys():
                                    for vnic in workload['interfaces']:
                                        if 'pre-mseg' in vnic.keys():
                                            if 'endpoint_group' in vnic['pre-mseg'].keys():
                                                if vnic['pre-mseg']['endpoint_group'] == portgroup:
                                                    vlan = vnic['pre-mseg']['vlan']
                                                    break
        return self._return_result(vlan)

    def va_inventory_get_microseg_rollback_input_data(self, instance, datacenter_name, hostname, portgroup):
        """
        get data for using microsegmenation rest api

        :param instance: vcenter instance
        :type instance: str
        :param datacenter_name: datacenter name
        :type datacenter_name: str
        :param hostname: host name
        :type hostname: str
        :param portgroup: port group
        :type portgroup: str
        :return: | {
                 |     'instance' : 'vcenter name'
                 |     'domain':'datacenter name',
                 |     'epi':'epi uuid',
                 |     'host':'host uuid',
                 |     'endpoint_group':'portgroup',
                 |     'vlan':'vlan'
                 | }
        :type: dict
        """
        data = {'instance': instance, 'domain': datacenter_name}
        epi = self.va_inventory_get_epi_uuid_by_host(instance, datacenter_name, hostname)
        if not self._check_failed_message(epi):
            data['epi'] = epi
        host = self.va_inventory_get_host_uuid(instance, datacenter_name, hostname)
        if not self._check_failed_message(host):
            data['host'] = host
        data['endpoint_group'] = portgroup
        vlan = self.va_inventory_get_vlan_by_portgroup(instance, datacenter_name, hostname, portgroup)
        if not self._check_failed_message(vlan):
            data['vlan'] = vlan
        if not None in data.values():
            return self._return_result(data)
        return self._return_result(None)

    def va_inventory_get_workload_information(self, instance, datacenter_name, hostname):
        """
        get workload information

        :param instance: vcenter instance
        :type instance: str
        :param datacenter_name: datacenter name
        :type datacenter_name: str
        :param hostname: host name
        :type hostname: str
        :return: workload information
        :type: list
        """
        params = {'domain': datacenter_name, 'instance': instance}
        result = self.va_rest_get_hosts_inventory(params)
        if self._check_failed_message(result):
            return result
        workloads = None
        if datacenter_name in result.keys():
            for key, value in result[datacenter_name].items():
                for host in value:
                    if 'name' in host.keys() and host['name'] == hostname:
                        if not workloads:
                            workloads = []
                        if 'workloads' in workload.keys():
                            for workload in host['workloads']:
                                workloads.append(workload)
        return self._return_result(workloads)

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
        params = {'instance': instance, 'domain': datacenter_name, 'endpoint_group': portgroup, 'vlan': vlan}
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

    def va_inventory_add_orchestration_configuration(self, instance, address, username, password, port='443',
                                                     enable='enable', orch_type='vcenter'):
        """
        add orchestration instance

        :param instance: vcenter instance
        :type instance: str
        :param address: vcenter ip address
        :type address: str
        :param username: vcenter username
        :type username: str
        :param password: vcenter password
        :type password: str
        :param port: vcenter port
        :type port: str
        :param enable: enable
        :type enable: str
        :param orch_type: vcenter or aci
        :type orch_type: str
        :return: error message if any
        :type: str
        """
        path = {'name': instance}
        data = {
            'name': instance,
            'address': address,
            'user': username,
            'passwd': password,
            'port': port,
            'enable': enable,
            'type': orch_type
        }
        result = self.va_rest_post_config_orchestration(path, data)
        if self._check_failed_message(result):
            return result

    def va_inventory_remove_orchestration_configuration(self, instance):
        """
        remove orchestration instance

        :param instance: vcenter instance
        :type instance: str
        :return: error message if any
        :type: str
        """
        path = {'name': instance}
        result = self.va_rest_delete_config_orchestration(path)
        if self._check_failed_message(result):
            return result

    def va_inventory_get_orchestration(self):
        """
        get all orchestraion information

        :return: | {
                 |     'vcenter_1': {
                 |     'address': '10.123.4.100',
                 |     'port': '443',
                 |     'user': 'root',
                 |     'passwd': '***',
                 |     'type': 'vcenter',
                 |     'enable': 'enable'
                 |     }
                 | }
        :type: dict
        """
        result = self.va_rest_get_orchestration()
        if self._check_failed_message(result):
            return result
        return self._return_result(result, False)

    def va_inventory_get_update_status(self, instance):
        """

        :param instance: vcenter instance
        :type instance: str
        :return: error message if any
        """
        params = {'instance': instance}
        result = self.va_get_inventory_updatestatus(params)
        if self._check_failed_message(result):
            return result
        return self._return_result(result)
