"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaMicrosegmentation_3_1 provides va orchestration microsegmentation features

.. moduleauthor:: ckung@varmour.com
"""

from access import logger
from feature.director.orchestration.microsegmentation.rel_3_0.inventory_rel_3_0 import VaInventory
from feature.exceptions import *


class VaMicrosegmentation_3_0(VaInventory):
    """
    Microsegmentation_3_0 is designed for providing va orchestration
    microsegmentation features
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

    def va_microsegment(self, hostname, portgroup):
        """
        trigger microsegmentation
        Args:
            :hostname (str): hostname
            :portgroup (str): portgroup

        Returns (dict): response from micro-segmentation rest request

        """
        logger.info('*****start micro segmentation*****')
        data = self.va_inventory_get_microseg_rollback_input_data(
            hostName=hostname, portGroup=portgroup)

        logger.info('microseg rest reqeust input data:\n{}'.format(data))
        if len(data) < 5:
            logger.info(
                'cannot generate correct input body '
                'for micro segmentation rest request')
            return
        post_data = dict()
        post_data['datacenter'] = data['datacenter']
        post_data['vlan'] = data['vlan']
        post_data['portgroup'] = data['portgroup']
        post_data['host'] = data['host']
        post_data['epi'] = data['epi']
        logger.info('sending microsegmentation rest request... input data {}\n'.format(post_data))
        response = self.va_rest_post_microsegmentation(data=post_data)
        try:
            if response['duration']:
                logger.info('microsegmentation request success')
        except KeyError:
            raise InvalidKey('va_microsegmentation')
        logger.info('*****finish micro segmentation*****')

    def va_rollback(self, hostname, portgroup):
        """
        rollback from microsegmentation
        Args:
            :hostname (str): hostname
            :portgroup (str): portgroup

        Returns (dict): response from roll back rest request

        """
        logger.info('*****start roll back from segmentation*****')
        data = self.va_inventory_get_microseg_rollback_input_data(
            hostName=hostname, portGroup=portgroup)
        if len(data) < 5:
            logger.info(
                'cannot generate correct input body '
                'for micro segmentation rest request')
            return

        post_data = dict()
        post_data['datacenter'] = data['datacenter']
        post_data['vlan'] = data['vlan']
        post_data['portgroup'] = data['portgroup']
        post_data['host'] = data['host']
        post_data['epi'] = data['epi']
        logger.info('sending rollback rest request... input data:\n{}'.format(post_data))

        response = self.va_rest_post_revert(data=post_data)
        try:
            if response['duration']:
                logger.info('rollback request success')
        except KeyError:
            raise InvalidKey('va_rollback')
        logger.info('*****finish roll back from segmentation*****')

    def va_get_segmented_workload(self, host_name, port_group):
        """
        get number of segmented workloads
        Args:
            :hostName (str): hostname
            :portGroup (str): portgroup

        Returns (int): number of segmented workload

        """
        logger.info('*****start getting segmented workload*****')
        workloads = self.va_inventory_get_workload_information(
            host_name=host_name,
            port_group=port_group)
        count = 0
        try:
            for workload in workloads:
                vnics = workload['vnics']
                for vnic in vnics:
                    if vnic['pre-mseg']['portgroup'] == port_group and vnic['microsegmented'] is True:
                        count += 1
        except KeyError:
            raise InvalidKey('va_get_segmented_workload')
        logger.info('segmented workload on hostname: {} portgroup: {} '
                    'workload: {}'.format(hostName, portGroup, count))
        logger.info('*****finish getting segmented workload*****')
        return count

    def va_get_non_segmented_workload(self, host_name, port_group):
        """
        get number of non segmented workloads
        Args:
            :hostName (str): hostname
            :portGroup (str): portgroup

        Returns (int): number of non segmented workload

        """
        logger.info('*****start getting non segment workload*****')
        workloads = self.va_inventory_get_workload_information(
            host_name=host_name,
            port_group=port_group)
        count = 0
        try:
            for workload in workloads:
                vnics = workload['vnics']
                for vnic in vnics:
                    if vnic['pre-mseg']['portgroup'] == portGroup and vnic['microsegmented'] is False:
                        count += 1
        except KeyError:
            raise InvalidKey('va_get_non_segmented_workload')
        logger.info('not segmented workload on hostname: {} portgroup: {} workload: {}'
                    .format(hostName, portGroup, count))
        logger.info('*****finish getting non segment workload*****')
        return count

    def va_configure_orchestration(self, **kwargs):
        """
        configuration orchestration connection
        Args:
            **kwargs:
                :vcenter (inventory): inventory obj
                or
                :address (str) : vcenter ip
                :username (str) : vcenter username
                :password (str) : vcenter password
                :port (str) : vcenter port

        """
        logger.info('*****start reconfiguring orchestration*****')
        self.va_inventory_delete_orchestration_configuration()
        if kwargs.get('vcenter', None):
            vcenter_object = kwargs.get('vcenter')
            self.va_inventory_set_orchestration_configuration(
                address=vcenter_object.get_mgmt_ip(),
                port='443',
                username=vcenter_object.get_user().get("name"),
                password=vcenter_object.get_user().get("password"))
        else:
            address = kwargs.get('address', None)
            port = kwargs.get('port', None)
            username = kwargs.get('username', None)
            password = kwargs.get('password', None)
            self.va_inventory_set_orchestration_configuration(
                address=address,
                port=port,
                username=username,
                password=password)
        logger.info('*****finish reconfiguring orchestration*****')

    def va_check_orchestration_connection(self):
        """
        check orchestration connection status
        Returns (boolean): True if orchestration is connected,
                           False otherwise

        """
        logger.info('*****start checking orchestration*****')
        responses = self.va_rest_get_orchestration()
        try:
            responses = responses['response']
            for response in responses:
                enable = response['enable']
                if enable:
                    logger.info('orchestration connection status: connected')
                    logger.info('*****finish checking orchestration*****')
                    return True
        except KeyError:
            raise InvalidKey('va_check_orchestration_connection')

        logger.info('orchestration connection status: not connected')
        logger.info('*****finish checking orchestration*****')
        return False

    def va_check_epi_status(self):
        """
        check epi status
        Returns (boolean): True if all epi are up otherwise False

        """
        logger.info('*****start checking epi status*****')
        response = self.va_rest_get_chassis_epi()
        try:
            if response['status'] == 'ok':
                epis = response['response']
                for epi in epis:
                    if epi['state'] != 'up':
                        logger.info('epi status: down')
                        logger.info('*****finish checking epi status*****')
                        return False
                logger.info('epi status: up')
                logger.info('*****finish checking epi status*****')
                return True
            else:
                return False
        except KeyError:
            raise InvalidKey('va_check_epi_status')

    def va_get_vlan_mapping(self, hostname):
        """
        return vlan mapping
        Args:
            :hostname (str): hostname

        Returns (dict): vlan mapping of the host
                        {'segment':['micro-vlans']}

        """
        logger.info('*****start getting all vlan mapping*****')
        epi_uuid = self.va_inventory_get_epi_uuid_by_host(hostName=hostname)
        response = self.va_rest_get_micro_segmentation()
        vlan_info = dict()
        try:
            if response['status'] == 'ok':
                segments = response['response']
                for s in segments:
                    if s['epi'].lower() == epi_uuid:
                        micro_vlan = s['micro-vlan']
                        segment = s['segment']
                        if vlan_info.get(segment) is None:
                            data = list()
                            data.append(micro_vlan)
                            vlan_info[segment] = data
                        else:
                            data = vlan_info[segment]
                            data.append(micro_vlan)
                            vlan_info[segment] = data
        except KeyError:
            raise InvalidKey('va_get_vlan_mapping')
        logger.info('vlan mapping description {\'segment id\' : [\'micro-vlans\']}')
        logger.info('vlan mapping for host {}: {}'.format(hostname, vlanInfo))
        logger.info('*****finish getting all vlan mapping*****')
        return vlanInfo

    def va_delete_all_vlan_mapping(self, hostname):
        """
        delete all vlan mapping
        Args:
            :hostname (str): hostname


        """
        logger.info('*****start delete all vlan mapping*****')
        epiuuid = self.va_inventory_get_epi_uuid_by_host(hostName=hostname)
        vlanmapping = self.va_get_vlan_mapping(hostname=hostname)
        try:
            path = dict()
            path['epiuuid'] = epiuuid
            for key, value in vlanmapping.items():
                path['segment'] = key
                for vlan in value:
                    path['micro-vlan'] = vlan
                    logger.info('deleting vlan {} in segment {}'
                                .format(vlan, key))
                    self.va_rest_delete_micro_segmentation(path=path)
            logger.info('*****finish delete all vlan mapping*****')
        except KeyError:
            raise InvalidKey('va_delete_all_vlan_mapping')

    def va_get_epi_mode(self, hostname, portgroup):
        """
        return epi mode according to provided host name and port group

        Args:
            :hostname (str): hostname
            :portgroup (str): portgroup

        Returns (str): inline, tap or standby

        """
        datacenter = self.va_inventory_get_datacenters_by_host(hostName=hostname)
        params = {'datacenter': datacenter}
        hosts_by_datacenter = self.va_rest_get_hosts_inventory(params=params)
        try:
            hosts_by_datacenter = hosts_by_datacenter['response']
            hosts = []
            clusters = hosts_by_datacenter['clusters']
            for cluster in clusters:
                hosts.append(cluster['hosts'])
            hosts.append(hosts_by_datacenter['hosts'])
            for host in hosts:
                for h in host:
                    if h['name'] == hostname:
                        workloads_data = h['workloads']
                        for workload in workloads_data:
                            vnics = workload['vnics']
                            for vnic in vnics:
                                if vnic['pre-mseg']['portgroup'] == portgroup:
                                    epis = h['epis']
                                    for epi in epis:
                                        logger.info('epi mode for hostname: {}, portgroup {}: mode: {}'
                                                    .format(hostname, portgroup, epi['mode']))
                                        return epi['mode']
        except KeyError:
            raise InvalidKey('va_get_epi_mode')

    def va_change_epi_mode(self, **kwargs):
        """
        change epi mode
        Args:
            **kwargs:
                :hostname (str): hostname
                :portgroup (str): portgroup (optional)
                :mode (str): inline, tap, standby

        """
        logger.info('*****start changing epi mode*****')
        logger.info('changing epi on host {} to {} mode'
                    .format(kwargs.get('hostname', None),
                            kwargs.get('mode', None)))
        if kwargs.get('portgroup', None):
            curr_mode = self.va_get_epi_mode(
                hostname=kwargs.get('hostname', None),
                portgroup=kwargs.get('portgroup'))
            if kwargs.get('mode', None) == curr_mode:
                return

        epi_uuid = self.va_inventory_get_epi_uuid_by_host(
            hostName=kwargs.get('hostname', None))
        path = dict()
        data = dict()
        path['epiuuid'] = epi_uuid
        data['operation-mode'] = kwargs.get('mode', None)
        self.va_rest_put_config_chassis_epi(path=path, data=data)
        logger.info('*****finish changing epi mode*****')

    def va_cleanup_director(self):
        """
        clean up all vlan mapping,
        change epi to tap mode
        and delete orchestration configuration


        """
        logger.info('*****start cleaning director*****')
        seg_stats = self.va_rest_get_segmentation_stats()
        hostnames = []
        try:
            hosts = []
            datacenters = seg_stats['response']['datacenters']
            for datacenter in datacenters:
                clusters = datacenter['cluster']
                for cluster in clusters:
                    hosts.append(cluster['hosts'])
                hosts.append(datacenter['hosts'])
            for host in hosts:
                for h in host:
                    if h['hasEpi']:
                        hostnames.append(h['name'])
            for hostname in hostnames:
                self.va_delete_all_vlan_mapping(hostname=hostname)
                self.va_change_epi_mode(hostname=hostname, mode='tap')

            self.va_inventory_delete_orchestration_configuration()
            logger.info('*****finish cleaning director*****')
        except KeyError:
            raise InvalidKey('va_director_cleanup')
