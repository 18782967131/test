"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaMicrosegmentation_3_1 provides va orchestration microsegmentation features

.. moduleauthor:: ckung@varmour.com
"""
import time
import datetime
from access import logger
from feature.director.orchestration.microsegmentation.rest.helper.inventory_rel_3_1 import VaInventory


class VaMicrosegmentation(VaInventory):
    """
    | Microsegmentation_3_1 is designed for providing va orchestration microsegmentation features
    |
    | Use the methods after you have instantiate microsegmentation object with VaMicrosegmentationFactory class
    |
    | Example:
    |    inventory_obj = ...
    |    mseg_obj = VaMicrosegmentationFactory.getFeature(inventory_obj)
    |    mseg_obj.va_microsegment(...)
    |
    """

    def va_microsegment(self, **kwargs):
        """
        trigger microsegmentation

        :param kwargs: | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'vlanID': '',
                       |     'segment': '',
                       |     'hostUUID': '',
                       |     'epiUUID': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | vlanID (str) - vlan id
                       | segment (str) - segment
                       | hostUUID (str) - host uuid
                       | epiUUID (str) - epi uuid
        :return: error message
        :type: str
        """
        method_name = 'va_microsegment'
        self._va_message_helper(method_name, 'start')
        postData = {}
        segmentData = kwargs.get('segmentData', None)
        if not segmentData:
            postData['instance'] = kwargs.get('instance', None)
            postData['vlan'] = kwargs.get('vlanID', None)
            postData['endpoint_group'] = kwargs.get('segment', None)
            postData['host'] = kwargs.get('hostUUID', None)
            postData['epi'] = kwargs.get('epiUUID', None)
        else:
            postData['instance'] = segmentData['instance']
            postData['vlan'] = segmentData['vlanID']
            postData['endpoint_group'] = segmentData['segment']
            postData['host'] = segmentData['hostUUID']
            postData['epi'] = segmentData['epiUUID']

        check_input = self._va_check_input_data(method_name, postData)

        if check_input:
            return check_input

        response = self.va_rest_post_microsegmentation(postData)

        if self._check_failed_message(response, method_name):
            return response
        logger.info('... sleep for 30 secs ...')
        time.sleep(30)
        self._va_message_helper(method_name, 'end')

    def va_enable_auto_microsegment(self, **kwargs):
        """
        enable auto microsegmentation

        :param kwargs: | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'datacenter': '',
                       |     'cluster': '',
                       |     'segment': '',
                       |     'vlanID': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | datacenter (str) - datacenter name
                       | cluster (str) - cluster name
                       | segment (str) - portgroup
                       | vlanID (str) - vlan id
        :return: error message if any
        :type: str
        """
        method_name = 'va_enable_auto_microsegment'
        self._va_message_helper(method_name, 'start')

        segmentData = kwargs.get('segmentData', None)
        if not segmentData:
            instance = kwargs.get('instance', None)
            domain = kwargs.get('datacenter', None)
            zone = kwargs.get('cluster', None)
            endpoint_group = kwargs.get('segment', None)
            vlan = kwargs.get('vlanID', None)
        else:
            instance = segmentData['instance']
            domain = segmentData['datacenter']
            zone = segmentData['cluster']
            endpoint_group = segmentData['segment']
            vlan = segmentData['vlanID']
        input_params = [instance, domain, zone, endpoint_group, vlan]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input
        postData = {'instance': instance}
        scope = {'domain': domain, 'zone': zone}
        postData['scope'] = scope
        filter_desc = []
        filter_dict = {'type': 'endpoint_group'}
        value = {'name': endpoint_group, 'vlan': vlan}
        filter_dict['value'] = value
        filter_desc1 = {'filter': filter_dict, 'associated_data': {}}
        filter_desc.append(filter_desc1)
        postData['filter_desc'] = filter_desc

        response = self.va_rest_post_auto_microsegmentation(postData)

        if self._check_failed_message(response, method_name):
            return response

        self._va_message_helper(method_name, 'end')

    def va_disable_auto_microsegment(self, **kwargs):
        """
        disable auto microsegmentation

        :param kwargs: | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'datacenter': '',
                       |     'cluster': '',
                       |     'segment': '',
                       |     'vlanID': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | datacenter (str) - datacenter name
                       | cluster (str) - cluster name
                       | segment (str) - portgroup
                       | vlanID (str) - vlan id
        :return: error message if any
        :type: str
        """
        method_name = 'va_disable_auto_microsegment'
        self._va_message_helper(method_name, 'start')
        segmentData = kwargs.get('segmentData', None)
        if not segmentData:
            instance = kwargs.get('instance', None)
            domain = kwargs.get('datacenter', None)
            zone = kwargs.get('cluster', None)
            endpoint_group = kwargs.get('segment', None)
            vlan = kwargs.get('vlanID', None)
        else:
            instance = segmentData['instance']
            domain = segmentData['datacenter']
            zone = segmentData['cluster']
            endpoint_group = segmentData['segment']
            vlan = segmentData['vlanID']
        input_params = [instance, domain, zone, endpoint_group, vlan]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        postData = {'instance': instance}
        scope = {'domain': domain, 'zone': zone}
        postData['scope'] = scope
        filter_desc = []
        filter_dict = {'type': 'endpoint_group'}
        value = {'name': endpoint_group, 'vlan': vlan}
        filter_dict['value'] = value
        filter_desc1 = {'filter': filter_dict, 'associated_data': {}}
        filter_desc.append(filter_desc1)
        postData['filter_desc'] = filter_desc

        response = self.va_rest_post_disable_auto_microsegmentation(postData)

        if self._check_failed_message(response, method_name):
            return response

        self._va_message_helper(method_name, 'end')

    def va_get_auto_microsegment_info(self, **kwargs):
        """
        get auto microsegmentation information

        :param kwargs: | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'datacenter': '',
                       |     'cluster': '',
                       |     'segment': '',
                       |     'vlanID': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | datacenter (str) - datacenter name
                       | cluster (str) - cluster
                       | segment (str) - segment
                       | vlanID (str) - vlan id
        :return: | error message if any
                 |
                 | else
                 |
                 | response
        :type: str or dict
        """
        method_name = 'va_get_auto_microsegment_info'
        self._va_message_helper(method_name, 'start')
        segmentData = kwargs.get('segmentData', None)
        if not segmentData:
            instance = kwargs.get('instance', None)
            domain = kwargs.get('datacenter', None)
            zone = kwargs.get('cluster', None)
            endpoint_group = kwargs.get('segment', None)
            vlan = kwargs.get('vlanID', None)
        else:
            instance = segmentData['instance']
            domain = segmentData['datacenter']
            zone = segmentData['cluster']
            endpoint_group = segmentData['segment']
            vlan = segmentData['vlanID']
        input_params = [instance, domain, zone, endpoint_group, vlan]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        params = {'instance': instance, 'domain': domain, 'zone': zone, 'filter_type': 'endpoint_group'}

        response = self.va_rest_get_auto_microsegmentation(params)

        if self._check_failed_message(response, method_name):
            return response

        result = None
        if 'filter_desc' in response.keys():
            result = response['filter_desc']

        self._va_message_helper(method_name, 'end', result)
        return result

    def va_rollback(self, **kwargs):
        """
        roll back from microsegmentation

        :param kwargs: | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'vlanID': '',
                       |     'segment': '',
                       |     'hostUUID': '',
                       |     'epiUUID': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | vlanID (str) - vlan id
                       | segment (str) - segment
                       | hostUUID (str) - host uuid
                       | epiUUID (str) - epi uuid
        :return: error message
        :type: str
        """
        method_name = 'va_rollback'
        self._va_message_helper(method_name, 'start')
        postData = {}
        segmentData = kwargs.get('segmentData', None)
        if not segmentData:
            postData['instance'] = kwargs.get('instance', None)
            postData['vlan'] = kwargs.get('vlanID', None)
            postData['endpoint_group'] = kwargs.get('segment', None)
            postData['host'] = kwargs.get('hostUUID', None)
            postData['epi'] = kwargs.get('epiUUID', None)
        else:
            postData['instance'] = segmentData['instance']
            postData['vlan'] = segmentData['vlanID']
            postData['endpoint_group'] = segmentData['segment']
            postData['host'] = segmentData['hostUUID']
            postData['epi'] = segmentData['epiUUID']

        check_input = self._va_check_input_data(method_name, postData)
        if check_input:
            return check_input

        response = self.va_rest_post_revert(postData)

        if self._check_failed_message(response, method_name):
            return response

        logger.info('... sleep for 15 secs ...')
        time.sleep(15)

        self._va_message_helper(method_name, 'end')

    # TODO need to be fixed
    def va_get_segmented_workload(self, **kwargs):
        """
        get number of segmented workloads

        :param kwargs: | params (dict) -
                       | {
                       |     'hostName': '',
                       |     'portGroup': '',
                       |     'dataCenterName': '',
                       |     'instance': '',
                       | }
                       |
                       | or
                       |
                       | hostName (str) - host name
                       | portGroup (str) - port group
                       | dataCenterName (str) - datacenter name
                       | instance (str) - vcenter instance
        :return: | error message if any
                 | or
                 | number of segmented workload
        :type: str or int
        """
        method_name = 'va_get_segmented_workload'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostName', None)
            portgroup = kwargs.get('portGroup', None)
            datacenter_name = kwargs.get('dataCenterName', None)
            instance = kwargs.get('instance', None)
        else:
            hostname = params['hostName']
            portgroup = params['portGroup']
            datacenter_name = params['dataCenterName']
            instance = params['instance']
        input_params = [instance, datacenter_name, hostname, portgroup]

        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        response = self.va_inventory_get_workload_information(instance, datacenter_name, hostname)

        if self._check_failed_message(response, method_name):
            return response

        segmented_count = 0
        if response:
            for workload in response:
                for vnic in workload['interfaces']:
                    if vnic['microsegmented'] and vnic['pre-mseg']['endpoint_group'] == portgroup:
                        segmented_count += 1

        self._va_message_helper(method_name, 'end', segmented_count)
        return segmented_count

    # TODO need to be fixed
    def va_get_non_segmented_workload(self, **kwargs):
        """
        get number of non-segmented workloads

        :param kwargs: | params (dict) -
                       | {
                       |     'hostName': '',
                       |     'portgroup': '',
                       |     'dataCenterName': '',
                       |     'instance': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | dataCenterName (str) - datacenter name
                       | hostName (str) - host name
                       | portGroup (str) - port group
        :return: number of non-segmented workload
        :type: int
        """
        method_name = 'va_get_non_segmented_workload'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostName', None)
            portgroup = kwargs.get('portGroup', None)
            datacenter_name = kwargs.get('dataCenterName', None)
            instance = kwargs.get('instance', None)
        else:
            hostname = params['hostName']
            portgroup = params['portGroup']
            datacenter_name = params['dataCenterName']
            instance = params['instance']
        input_params = [instance, datacenter_name, hostname, portgroup]

        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        response = self.va_inventory_get_workload_information(instance, datacenter_name, hostname)
        if self._check_failed_message(response, method_name):
            return response
        non_segmented_count = 0
        if response:
            for workload in response:
                for vnic in workload['interfaces']:
                    if not vnic['microsegmented'] and vnic['pre-mseg']['endpoint_group'] == portgroup:
                        non_segmented_count += 1
        self._va_message_helper(method_name, 'end', non_segmented_count)
        return non_segmented_count

    def va_get_segment_workload_by_host(self, **kwargs):
        """
        get number of total, segmented and nonsegmented workloads

        :param kwargs: | params (dict) -
                       | {
                       |     'hostname':'',
                       |     'instance':'',
                       |     'domain':'',
                       |     'endpoint_group':'',
                       |     'vlan':'',
                       | }
                       |
                       | or
                       |
                       | hostname (str) - host name
                       | instance (str) - vcenter instance
                       | domain (str) - datacenter name
                       | endpoint_group (str) - portgroup
                       | vlan (str) - vlan
        :return: | {
                 |     'totalWorkload': '',
                 |     'segWorkload': '',
                 |     'nonsegWorkload': '',
                 | }
        :type: dict
        """
        method_name = 'va_get_segment_workload_by_host'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostname', None)
            instance = kwargs.get('instance', None)
            datacenter_name = kwargs.get('domain', None)
            endpoint_group = kwargs.get('endpoint_group', None)
            vlan = kwargs.get('vlan')
        else:
            hostname = params['hostname']
            instance = params['instance']
            datacenter_name = params['domain']
            endpoint_group = params['endpoint_group']
            vlan = params['vlan']

        input_params = [hostname, instance, datacenter_name, endpoint_group, vlan]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        response = self.va_inventory_get_workload_information_by_host(instance, datacenter_name, hostname,
                                                                      endpoint_group, vlan)
        if self._check_failed_message(response, method_name):
            return response

        self._va_message_helper(method_name, 'end', response)
        return response

    def va_configure_orchestration(self, **kwargs):
        """
        configure orchestration connection

        :param kwargs: | vcenter (inventory) - inventory object
                       |
                       | or
                       |
                       | address (str) - vcenter ip
                       | username (str) - vcenter username
                       | password (str) - vcenter password
                       | port (str) - vcenter port
                       | instance (str) - vcenter instance
        :return: error message if any
        :type: str
        """
        method_name = 'va_configure_orchestration'
        self._va_message_helper(method_name, 'start')
        vcenter_object = kwargs.get('vcenter', None)
        if not vcenter_object:
            address = kwargs.get('address', None)
            port = kwargs.get('port', None)
            username = kwargs.get('username', None)
            password = kwargs.get('password', None)
            instance = kwargs.get('instance', None)
        else:
            address = vcenter_object.get_mgmt_ip()
            port = '443'
            username = vcenter_object.get_user().get("name")
            password = vcenter_object.get_user().get("password")
            instance = vcenter_object.get_uniq_id()

        input_params = [instance, address, username, password, port]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        response = self.va_inventory_get_orchestration()
        if self._check_failed_message(response, method_name):
            return response

        if response:
            for info in response:
                if 'name' in info.keys() and instance == info['name']:
                    response = self.va_remove_orchestration(instance, True)
                    if self._check_failed_message(response, method_name):
                        return response

        start_time = datetime.datetime.now().replace(microsecond=0)

        response = self.va_inventory_add_orchestration_configuration(instance, address, username, password)
        if self._check_failed_message(response, method_name):
            return response

        timeout = 30
        while timeout >= 0:
            response = self.va_inventory_get_update_status(instance)
            if self._check_failed_message(response, method_name):
                return response
            if response and type(response) is dict:
                break
            logger.info('waiting for plugin to add {}'.format(instance))
            time.sleep(5)
            timeout -= 1
        end_time = datetime.datetime.now().replace(microsecond=0)
        logger.info('... configure orchestration takes {} secs ...'.format(end_time - start_time))
        if timeout < 0:
            error_message = 'failed to add {} to orchestration\nreason timeout'.format(instance)
            if self._check_failed_message(error_message, method_name):
                return error_message

        self._va_message_helper(method_name, 'end')

    def va_get_plugin_connection_time(self, **kwargs):
        """
        configure orchestration connection

        :param kwargs: | instance (str)  - vcenter instance

        :return: error message if any
        :type: str
        """
        method_name = 'va_check_plugin_connection_time'
        self._va_message_helper(method_name, 'start')
        instance = kwargs.get('instance', None)
        timeout = kwargs.get('timeout', None)
        if not instance:
            error_message = "missing vcenter instance! "
            return error_message
        if not timeout:
            timeout = 120

        start_time = datetime.datetime.now().replace(microsecond=0)

        while timeout >= 0:
            response = self.va_inventory_get_update_status(instance)
            if self._check_failed_message(response, method_name):
                return response
            if response and type(response) is dict:
                break
            logger.info('waiting for plugin to add {}'.format(instance))
            time.sleep(10)
            timeout -= 1
        end_time = datetime.datetime.now().replace(microsecond=0)
        wait_time = end_time - start_time
        logger.info('... plugin ready takes {} secs ...'.format(end_time - start_time))
        if timeout < 0:
            error_message = 'plugin not ready in {} \nreason timeout'.format(wait_time)
            if self._check_failed_message(error_message, method_name):
                return None
        return wait_time
        self._va_message_helper(method_name, 'end')


    def va_check_orchestration_connection(self, **kwargs):
        """
        check orchestration connection status

        :param kwargs: | vcenter (inventory) - inventory object
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
        :return: | True - orchestration is connected
                 | False - orchestration is disconnected
        :type: bool
        """
        method_name = 'va_check_orchestration_connection'
        self._va_message_helper(method_name, 'start')
        response = self.va_inventory_get_orchestration()
        if self._check_failed_message(response, method_name):
            return response
        instance = kwargs.get('name', None)
        vcenter_object = kwargs.get('vcenter', None)
        if vcenter_object:
            instance = vcenter_object.get_uniq_id()

        input_params = [instance]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        for orch_data in response:
            if 'name' in orch_data.keys() and orch_data['name'] == instance:
                if 'enable' in orch_data.keys():
                    self._va_message_helper(method_name, 'end', str(orch_data['enable']))
                    return orch_data['enable']
        self._va_message_helper(method_name, 'end', None)
        return False

    def va_check_epi_status(self):
        """
        check all epi status

        :return: | True - all epis are up
                 | False - all epis are down
        :type: bool
        """
        method_name = 'va_check_epi_status'
        self._va_message_helper(method_name, 'start')
        response = self.va_rest_get_chassis_epi()
        if self._check_failed_message(response, method_name):
            return response

        if response:
            for epi in response:
                if 'state' in epi.keys():
                    self._va_message_helper(method_name, 'end', epi['state'])
                    if epi['state'] == 'up':
                        return True
                    return False
        self._va_message_helper(method_name, 'end', None)

    def va_get_vlan_mapping(self, **kwargs):
        """
        get vlan mapping

        :param kwargs: | params (dict) -
                       | {
                       |     'hostname': '',
                       |     'dataCenterName': '',
                       |     'instance': '',
                       | }
                       |
                       | or
                       |
                       | hostname (str) - host name
                       | dataCenterName (str) - datacenter name
                       | instance (str) - instance
        :return: | vlan mapping of the host
                 | {
                 |     'segment':['vlanID']
                 | }
        :type: dict
        """
        method_name = 'va_get_vlan_mapping'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostname', None)
            datacenter_name = kwargs.get('dataCenterName', None)
            instance = kwargs.get('instance', None)
        else:
            hostname = params['hostname']
            datacenter_name = params['dataCenterName']
            instance = params['instance']
        input_params = [instance, hostname, datacenter_name]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        epiuuid = self.va_inventory_get_epi_uuid_by_host(instance, datacenter_name, hostname)
        if self._check_failed_message(epiuuid, method_name):
            return epiuuid

        response = self.va_rest_get_micro_segmentation()
        if self._check_failed_message(response, method_name):
            return response

        vlanInfo = {}
        for s in response:
            if 'epi' in s.keys():
                if s['epi'].lower() == epiuuid:
                    micro_vlan = s['micro-vlan']
                    segment = s['segment']
                    if not vlanInfo.get(segment):
                        data = []
                        data.append(micro_vlan)
                        vlanInfo[segment] = data
                    else:
                        data = vlanInfo[segment]
                        data.append(micro_vlan)
                        vlanInfo[segment] = data

        if vlanInfo:
            self._va_message_helper(method_name, 'end', vlanInfo)
            return vlanInfo
        self._va_message_helper(method_name, 'end', None)

    def va_delete_all_vlan_mapping(self, **kwargs):
        """
        delete all vlan mapping

        :param kwargs: | params (dict) -
                       | {
                       |     'hostname': '',
                       |     'dataCenterName': '',
                       |     'instance': '',
                       | }
                       |
                       | or
                       |
                       | hostname (str) - host name
                       | dataCenterName (str) - datacenter name
                       | instance (str) - vcenter instance
        :return: error message if any
        :type: str
        """
        method_name = 'va_delete_all_vlan_mapping'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostname', None)
            datacenter_name = kwargs.get('dataCenterName', None)
            instance = kwargs.get('instance', None)
        else:
            hostname = params['hostname']
            datacenter_name = params['dataCenterName']
            instance = params['instance']
        input_params = [instance, hostname, datacenter_name]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        epiuuid = self.va_inventory_get_epi_uuid_by_host(instance, datacenter_name, hostname)
        if self._check_failed_message(epiuuid, method_name):
            return epiuuid

        vlanmapping = self.va_get_vlan_mapping(instance=instance, datacentername=datacenter_name, hostname=hostname)
        path = {'epiuuid': epiuuid}
        for key, value in vlanmapping.items():
            path['segment'] = key
            for vlan in value:
                path['micro-vlan'] = vlan
                response = self.va_rest_delete_micro_segmentation(path)
                if self._check_failed_message(response, method_name):
                    return response
        self._va_message_helper(method_name, 'end')

    def va_get_epi_mode(self, **kwargs):
        """
        get epi mode

        :param kwargs: | params(dict) -
                       | {
                       |     'hostname': '',
                       |     'portgroup': '',
                       |     'dataCenterName': '',
                       |     'instance': '',
                       | }
                       |
                       | or
                       |
                       | hostname (str) - hostname
                       | portgroup (str) - portgroup
                       | dataCenterName (str) - datacenter name
                       | instance (str) - vcenter instance
        :return: epi mode
        :type: str
        """
        method_name = 'va_get_epi_mode'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostname', None)
            portgroup = kwargs.get('portgroup', None)
            datacenter_name = kwargs.get('dataCenterName', None)
            instance = kwargs.get('instance', None)
        else:
            hostname = params['hostname']
            portgroup = params['portgroup']
            datacenter_name = params['dataCenterName']
            instance = params['instance']

        input_params = [instance, datacenter_name, hostname, portgroup]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        params = {'domain': datacenter_name, 'instance': instance}
        response = self.va_rest_get_hosts_inventory(params)
        if self._check_failed_message(response, method_name):
            return response

        if datacenter_name in response.keys():
            for key, value in response[datacenter_name].items():
                for val in value:
                    if val['name'] == hostname:
                        for workload in val['workloads']:
                            for vnic in workload['interfaces']:
                                if vnic['pre-mseg']['endpoint_group'] == portgroup:
                                    for epi in val['epis']:
                                        self._va_message_helper(method_name, 'end', epi['mode'])
                                        return epi['mode']
        self._va_message_helper(method_name, 'end', None)

    def va_change_epi_mode(self, **kwargs):
        """
        change epi mode

        :param kwargs: | params(dict) -
                       | {
                       |     'hostname': '',
                       |     'portgroup': '',
                       |     'instance': '',
                       |     'mode': '',
                       |     'datacenter', '',
                       | }
                       |
                       | or
                       |
                       | hostname (str) - hostname
                       | portgroup (str) - portgroup (optional)
                       | instance (str) - instance
                       | mode (str) - inline, tap, standby
                       | datacenter (str) - datacenter name
        :return: error message if any
        :type: str
        """
        method_name = 'va_change_epi_mode'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostname', None)
            portgroup = kwargs.get('portgroup', None)
            instance = kwargs.get('instance', None)
            mode = kwargs.get('mode', None)
            datacenter_name = kwargs.get('datacenter', None)
        else:
            hostname = params['hostname']
            instance = params['instance']
            mode = params['mode']
            datacenter_name = params['datacenter']
            if 'portgroup' in params.keys():
                portgroup = params['portgroup']

        input_params = [instance, datacenter_name, hostname, mode]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        if portgroup:
            curr_mode = self.va_get_epi_mode(hostname=hostname, portgroup=portgroup, dataCenterName=datacenter_name,
                                             instance=instance)
            if mode == curr_mode:
                return None

        epiuuid = self.va_inventory_get_epi_uuid_by_host(instance, datacenter_name, hostname)
        if self._check_failed_message(epiuuid, method_name):
            return epiuuid

        data = {'hostname': hostname, 'name': epiuuid, 'operation-mode': mode}
        response = self.va_rest_put_config_chassis_epi(data)

        if self._check_failed_message(response, method_name):
            return response
        self._va_message_helper(method_name, 'end')

    def va_cleanup_director(self, **kwargs):
        """
        clean up all vlan mapping, change epi to tap mode and delete orchestration configuration

        :param kwargs: | params(dict) -
                       | {
                       |     'hostname': '',
                       |     'dataCenterName': '',
                       |     'instance', '',
                       | }
                       |
                       | or
                       |
                       | hostname (str) - hostname
                       | dataCenterName (str) - datacenter name
                       | instance (str) - vcenter instance
        :return: error message if any
        :type: str
        """
        method_name = 'va_cleanup_director'
        self._va_message_helper(method_name, 'start')
        params = kwargs.get('params', None)
        if not params:
            hostname = kwargs.get('hostname', None)
            datacenter_name = kwargs.get('dataCenterName', None)
            instance = kwargs.get('instance', None)
        else:
            hostname = params['hostname']
            datacenter_name = params['dataCenterName']
            instance = params['instance']

        input_params = [instance, datacenter_name, hostname]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        # segStats = self.va_rest_get_segmentation_stats()
        hostnames = []
        hostnames.append(hostname)
        params = {'domain': datacenter_name, 'instance': instance}
        response = self.va_rest_get_hosts_inventory(params)
        if self._check_failed_message(response, method_name):
            return response

        if datacenter_name in response.keys():
            for key, value in response[datacenter_name].items():
                for val in value:
                    if val['epis']:
                        hostnames.append(val['name'])

        for hostname in hostnames:
            response = self.va_delete_all_vlan_mapping(instance=instance, dataCenterName=datacenter_name,
                                                       hostname=hostname)
            if self._check_failed_message(response, method_name):
                return response

            response = self.va_change_epi_mode(hostname=hostname, mode='tap')
            if self._check_failed_message(response, method_name):
                return response
        response = self.va_inventory_delete_orchestration_configuration()
        if self._check_failed_message(response, method_name):
            return response
        self._va_message_helper(method_name, 'end')

    def va_get_orchestration_configured(self):
        """
        get orchestration configuration information

        :return: | {
                 |     'password':'',
                 |     'address':'ip_address',
                 |     'endpoint_prefix':'va-',
                 |     'username':'username',
                 |     'name':'vcenter_instance',
                 |     'status_message':'failed message',
                 |     'enable':True/False,
                 |     'status_code':'4',
                 |     'auto_power_switch':True/False,
                 |     'type':'vcenter',
                 |     'port':'443'
                 | }
        :type: dict
        """
        method_name = 'va_get_orchestration_configured'
        self._va_message_helper(method_name, 'start')
        response = self.va_inventory_get_orchestration()
        if self._check_failed_message(response, method_name):
            return response
        self._va_message_helper(method_name, 'end', response)
        return response

    def va_remove_orchestration(self, instance=None, config_orch_helper=False):
        """
        remove orchestration

        :param instance: vcenter instance
        :type instance: str
        :return: error message
        :type: str
        """
        method_name = None
        if not config_orch_helper:
            method_name = 'va_remove_orchestration'
        if not config_orch_helper:
            self._va_message_helper(method_name, 'start')
        start_time = datetime.datetime.now().replace(microsecond=0)
        timeout = 30
        if instance:
            response = self.va_inventory_remove_orchestration_configuration(instance)
            if self._check_failed_message(response, method_name):
                return response

            while timeout >= 0:
                response = self.va_inventory_get_update_status(instance)
                if response and type(response) is str and 'not' in response.lower():
                    break
                logger.info('waiting for plugin to remove {}'.format(instance))
                time.sleep(10)
                timeout -= 1

        else:
            response = self.va_inventory_get_orchestration()
            if self._check_failed_message(response, method_name):
                return response
            instances = []
            if response:
                for info in response:
                    if 'name' in info.keys():
                        instances.append(info['name'])
                        response = self.va_inventory_remove_orchestration_configuration(info['name'])
                        if self._check_failed_message(response, method_name):
                            return response
            if instances:
                while timeout >= 0:
                    for instance in instances:
                        response = self.va_inventory_get_update_status(instance)
                        if self._check_failed_message(response, method_name):
                            return response
                        if response and type(response) is str and 'not' in response.lower():
                            instances.remove(instance)
                    if not instances:
                        break
                    logger.info('waiting for plugin to remove all instance')
                    time.sleep(10)
                    timeout -= 1
        end_time = datetime.datetime.now().replace(microsecond=0)
        logger.info('... delete orchestration takes {} secs ...'.format(end_time - start_time))
        if timeout < 0:
            error_message = 'failed to remove {} from orchestration\nreason timeout'.format(instance)
            if self._check_failed_message(error_message, method_name):
                return error_message

        if not config_orch_helper:
            self._va_message_helper(method_name, 'end')

    def va_check_plugin_status(self, instance):
        """
        check plugin is ready

        :param instance: vcenter instance
        :type instance: str
        :return: | status
                 | or
                 | error message if any
        :type: boolean or str
        """
        method_name = 'va_check_plugin_status'
        self._va_message_helper(method_name, 'start')
        input_params = [instance]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input
        response = self.va_inventory_get_update_status(instance)
        if self._check_failed_message(response, method_name):
            return response
        self._va_message_helper(method_name, 'end', response)
        if response and type(response) is str and 'not' in response.lower():
            return False
        return True

    def va_deployment(self, instance, data):
        """
        deploy va vm

        :param instance: vcenter instance
        :type instance: str
        :param data: message body
        :type data: dict
        :return: (jobid, error message if any)
        :type: (str, str)
        """
        method_name = 'va_dp_deployment'
        self._va_message_helper(method_name, 'start')
        input_params = [instance, data]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input
        params = {'instance': instance}
        response = self.va_post_inventory_deployment(params, data)
        if self._check_failed_message(response, method_name):
            return response, None

        self._va_message_helper(method_name, 'end', response)

        if 'message' in response.keys() and 'status' in response.keys():
            if response['message'] == 'ok' and response['status'] == 'prepare':
                return None, response['jobid']

    def va_reverse_deployment(self, instance, data, jobid=None):
        """
        remove deployment

        :param instance: vcenter instance
        :type instance: str
        :param data: body message
        :type data: dict
        :return: error message if any
        :type: str
        """
        method_name = 'va_reverse_dp_deployment'
        self._va_message_helper(method_name, 'start')
        input_params = [instance, data]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        params = {'instance': instance}
        if jobid:
            params['jobid'] = jobid
        else:
            params['jobid'] = '5636181a702543d4bf14a9d0a80696e4'
            params['ignoreid'] = 'true'
        response = self.va_post_inventory_remove_deployment(params, data)

        if self._check_failed_message(response, method_name):
            return response
        self._va_message_helper(method_name, 'end', response)
        if 'status' in response.keys() and response['status'] == 'removed':
            return None

        return 'Failed to reverse deception deployment on instance {}'.format(instance)

    def va_check_deployment_status(self, jobid=None):
        """
        check deployment status

        :param jobid: job id
        :type jobid: str
        :return:
        """
        method_name = 'va_check_dp_deployment_status'
        self._va_message_helper(method_name, 'start')
        input_params = [jobid]
        check_input = self._va_check_input_data(method_name, input_params)
        if check_input:
            return check_input

        params = {'jobid': jobid}
        response = self.va_get_inventory_deployment(params)
        if self._check_failed_message(response, method_name):
            return response
        ### status could be "complete", "complete with error, or warning"
        self._va_message_helper(method_name, 'end', response)
        if type(response) is list:
            for info in response:
                if 'status' in info.keys():
                    if 'complete' in info['status']:
                        end_time = info['end_time']
                        start_time = info['start_time']
                        total_time = int(end_time) - int(start_time)
                        logger.info("DP Deployment is completed in {} seconds !".format(total_time))
                        return info['status']
                    else:
                        return info['status']
            return 'no status'

    def va_test_rest(self, verb, url, params, data):
        """
        use for testing rest api

        :param verb: http verb
        :type verb: str
        :param url: url
        :type url: str
        :param params: url parameters
        :type params: dict
        :param data: http body message
        :type data: dict
        :return: rest response or error message if any
        :type: (boolean, dict) or str
        """
        method_name = 'va_test_rest'
        auth = self._va_rest_get_auth_key()

        if type(auth) is str:
            return self._va_error_message(method_name, auth)

        status, response = self.__rest_util.request(verb, url, auth=auth, params=params, data=data)

        self._va_rest_del_auth_key(auth)

        return status, response

    def va_print(self):
        print('microseg 3.1')
