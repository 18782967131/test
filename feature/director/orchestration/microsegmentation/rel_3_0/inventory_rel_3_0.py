"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaInventory parse va rest response into meaningful information

.. moduleauthor:: ckung@varmour.com
"""
from access import logger
from feature.director.orchestration.microsegmentation.rel_3_0.rest_api_rel_3_0 import VaRestapi
from feature.exceptions import *


class VaInventory(VaRestapi):
    """
    VaInventory is designed for parsing inventory information into
    meaningful information
    """

    def __init__(self, **kwargs):
        """
        constructor has restUtil objects
        Args:
            **kwargs:
                :inv_object (inventory_object): inventory object
                or
                :ip (str): director ip
                :username (str): director username
                :password (str): director password
                :verbose (boolean): enable/disable logger
        """
        super().__init__(**kwargs)

    def va_inventory_get_datacenters(self):
        """

        Returns (list): all datacenter names

        """
        datacenters = []
        params = {'datacenter': ''}
        data_centers = self.va_rest_get_inventory(params=params)
        if isinstance(data_centers, dict):
            try:
                if data_centers['status'] == 'ok':
                    datacenters_list = data_centers['response']['datacenters']
                    for item in datacenters_list:
                        datacenters.append(str(item['name']))
                else:
                    return None
            except (KeyError, ResponseFailed):
                logger.error('Error Found in Getting Datacenter ' +
                             'from REST API, Please Check')
                raise InvalidKey('va_inventory_get_datacenters')

        else:
            raise InvalidResponseFormat('va_inventory_get_datacenters')
        return datacenters

    def va_inventory_get_hosts_by_datacenter(self, data_center_name):
        """
        return all hosts information according to a data center parameter
        Args:
            :dataCenterName (str): name of the datacenter

        Returns (list): all host information in the datacenter

        """
        clustered_hosts = []
        standalone_hosts = []
        params = {'datacenter': data_center_name}
        hosts_by_datacenter = self.va_rest_get_hosts_inventory(params=params)
        if isinstance(hosts_by_datacenter, dict):
            try:
                for hosts_list_cluster in hosts_by_datacenter['response']['clusters']:
                    for data in hosts_list_cluster['hosts']:
                        clustered_hosts.append(str(data['name']))
                for hosts_list in hosts_by_datacenter['response']['hosts']:
                    standalone_hosts.append(str(hosts_list['name']))
            except KeyError:
                logger.error('Error Found in Getting Hosts from REST API'
                             ',Please Check ')
                raise InvalidKey('va_inventory_get_hosts_by_datacenter')
        else:
            raise InvalidResponseFormat('va_inventory_get_hosts_by_datacenter')
        total_hosts_in_datacenter = clustered_hosts + standalone_hosts
        return total_hosts_in_datacenter

    def va_inventory_get_datacenters_by_host(self, host_name):
        """
        return datacenter name with hostname parameter
        Args:
            :hostName (list): list of hostnames

        Returns (list): datacenter

        """
        data_center = None
        data_center_found = False
        datacenters_in_vcenter = self.va_inventory_get_datacenters()
        if datacenters_in_vcenter:
            for dc in datacenters_in_vcenter:
                if host_name in self.va_inventory_get_hosts_by_datacenter(dc):
                    data_center_found = True
                    data_center = dc
                    break
            if not data_center_found:
                logger.error('datacenter is not found for hostname {}'
                             .format(host_name))
                raise InvalidData('va_inventory_get_datacenters_by_host')
        return data_center

    def va_inventory_get_epi_uuid_by_host(self, host_name):
        """
        returns epi uuid according to host name
        Args:
            :hostName (str): host name

        Returns (str): epi uuid

        """
        data_center_name = self.va_inventory_get_datacenters_by_host(host_name)
        params = {'datacenter': data_center_name}

        hosts_by_datacenter = self.va_rest_get_hosts_inventory(params=params)

        if isinstance(hosts_by_datacenter, dict):
            try:
                for hosts_list_cluster in hosts_by_datacenter['response']['clusters']:
                    for data in hosts_list_cluster['hosts']:
                        if str(data['name']) == host_name:
                            epi_list = data['epis']
                            if len(epi_list) > 1:
                                logger.error(
                                    'Host {} has multiple EPi. '
                                    'We are not supporting Multiple EPi'.formnat(host_name))
                                raise InvalidData('va_inventory_get_epi_uuid_by_host')
                            if len(epi_list) == 0:
                                logger.error(
                                    "Host {} has no Epi, "
                                    "Please Install Epi First "
                                    "and then Microsegmentation".format(host_name))
                                raise InvalidData('va_inventory_get_epi_uuid_by_host')
                            for epi in epi_list:
                                return str(epi['uuid'])
                            break
                for hosts_list in hosts_by_datacenter['response']['hosts']:
                    if str(hosts_list['name']) == host_name:
                        epi_list = hosts_list['epis']
                        if len(epi_list) > 1:
                            logger.error(
                                'Host {} has multiple EPi. '
                                'We are not supporting Multiple EPi'.formnat(host_name))
                            raise InvalidData('va_inventory_get_epi_uuid_by_host')
                        if len(epi_list) == 0:
                            logger.error(
                                'Host {} has no Epi, '
                                'Please Install Epi First and then '
                                'Microsegmentation'.format(host_name))
                            raise InvalidData('va_inventory_get_epi_uuid_by_host')
                        for epi in epi_list:
                            return str(epi['uuid'])
                        break

            except KeyError:
                logger.error('Error Found in Getting EPi from Hosts, '
                             'Please EPi is installed on host ')
                raise InvalidKey('va_inventory_get_epi_uuid_by_host')

    def va_inventory_get_host_uuid(self, host_name):
        """
        return host's uuid
        Args:
            :host_name (str): host name

        Returns (str): uuid of the host

        """
        data_center_name = self.va_inventory_get_datacenters_by_host(host_name)
        params = {'datacenter': data_center_name}
        hosts_by_datacenter = self.va_rest_get_hosts_inventory(params=params)
        if isinstance(hosts_by_datacenter, dict):
            try:
                for hosts_list_cluster in hosts_by_datacenter['response']['clusters']:
                    for data in hosts_list_cluster['hosts']:
                        if data['name'] == host_name:
                            host_uuid = data['uuid']
                            return str(host_uuid)

                for hosts_list in hosts_by_datacenter['response']['hosts']:
                    if hosts_list['name'] == host_name:
                        host_uuid = hosts_list['uuid']
                        return str(host_uuid)

            except KeyError:
                logger.error('Error Found in Getting EPi '
                             'from Hosts,Please EPi is installed on host ')
                raise InvalidKey('va_inventory_get_host_uuid')

    def va_inventory_get_vlan_by_portgroup(self, host_name, port_group):
        """
        return vlan information
        Args:
            :host_name (str): hostname
            :port_group (str): portgroup

        Returns (str): vlan information

        """
        data_center_name = self.va_inventory_get_datacenters_by_host(host_name)
        params = {'datacenter': data_center_name}
        hosts_by_datacenter = self.va_rest_get_hosts_inventory(params=params)
        data = dict()
        if isinstance(hosts_by_datacenter, dict):
            try:
                for hosts_list_cluster in hosts_by_datacenter['response']['clusters']:
                    for data in hosts_list_cluster['hosts']:
                        if str(data['name']) == host_name:
                            workload_list = data['workloads']
                            if workload_list is not None:
                                for workload in workload_list:
                                    for vnic in workload['vnics']:
                                        if vnic['pre-mseg']['portgroup'] == port_group:
                                            return str(vnic['pre-mseg']['vlan'])
                            else:
                                logger.error('Selected host {} '
                                             'has no workloads'
                                             .format(host_name))
                                raise InvalidData('va_inventory_get_vlan_by_portgroup')
                            break

                for hosts_list in hosts_by_datacenter['response']['hosts']:
                    if str(hosts_list['name']) == host_name:
                        workload_list = data['workloads']
                        if workload_list:
                            for workload in workload_list:
                                for vnic in workload['vnics']:
                                    if vnic['pre-mseg']['portgroup'] == port_group:
                                        return str(vnic['pre-mseg']['vlan'])
                        else:
                            logger.error(
                                'Selected host {} has no workloads'.format(host_name))
                            raise InvalidData('va_inventory_get_vlan_by_portgroup')
                        break

            except KeyError:
                logger.error(
                    'Error Found in Getting vlan from provided port group.')
                raise InvalidKey('va_inventory_get_host_uuid')

    def va_inventory_get_microseg_rollback_input_data(self, host_name, port_group):
        """
        return input body data for calling microsegmentation
        or rollback rest call
        Args:
            :host_name (str): host name
            :port_group (str): portgroup

        Returns (dict): {'datacenter':'datacenter name',
                         'epi':'epi uuid',
                         'host':'host uuid',
                         'portgroup':'portgroup',
                         'vlan':'vlan'}

        """
        data = dict()
        data['datacenter'] = self.va_inventory_get_datacenters_by_host(host_name)
        data['epi'] = self.va_inventory_get_epi_uuid_by_host(host_name)
        data['host'] = self.va_inventory_get_host_uuid(host_name)
        data['portgroup'] = port_group
        data['vlan'] = self.va_inventory_get_vlan_by_portgroup(host_name, port_group)
        return data

    def va_inventory_get_workload_information(self, host_name, port_group):
        """
        return workload information
        Args:
            :host_name (str): hostname
            :port_group (str): portgroup

        Returns (list): workload information

        """
        data_center_name = self.va_inventory_get_datacenters_by_host(host_name)
        params = {'datacenter': data_center_name}
        hosts_by_datacenter = self.va_rest_get_hosts_inventory(params=params)
        try:
            hosts_by_datacenter = hosts_by_datacenter['response']
            hosts = []
            clusters = hosts_by_datacenter['clusters']
            for cluster in clusters:
                hosts.append(cluster['hosts'])
            hosts.append(hosts_by_datacenter['hosts'])
            workloads = []
            for host in hosts:
                for h in host:
                    workloads_data = h['workloads']
                    for workload in workloads_data:
                        vnics = workload['vnics']
                        for vnic in vnics:
                            if h['name'] == host_name and vnic['pre-mseg']['portgroup'] == port_group:
                                workloads.append(workload)
                                break
        except KeyError:
            logger.error("Error Found in Getting workload information.")
            raise InvalidKey('va_inventory_get_host_uuid')
        return workloads

    def va_inventory_set_orchestration_configuration(self, **kwargs):
        """
        configure orchestration connection
        vcenter only
        Args:
            **kwargs:
                    :address (str): vcenter address
                    :username (str): vcenter username
                    :password (str): vcenter password
                    :port (str): vcenter port


        """
        data = dict()
        path = dict()
        path['name'] = 'server1'
        data['name'] = path['name']
        data['address'] = kwargs.get('address', None)
        data['port'] = kwargs.get('port', None)
        data['passwd'] = kwargs.get('password', None)
        data['enable'] = 'enable'
        data['type'] = 'vcenter'
        data['user'] = kwargs.get('username', None)
        self.va_rest_post_config_orchestration(path=path, data=data)

    def va_inventory_delete_orchestration_configuration(self):
        """
        delete orchestration configuration


        """
        logger.info('***deleting orchestration configuration***')
        path = dict()
        path['name'] = 'server1'
        self.va_rest_delete_config_orchestration(path=path)
        logger.info('***finish deleting orchestration configuration***')
        return
