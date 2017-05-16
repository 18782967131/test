"""
coding: utf-8
Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

vCenterHost class is representing vim.HostSystem ESXi Host objects and its
methods. class methods either return string or managed objects.

.. moduleauthor::jpatel@varmour.com
"""

from vautils.orchestration.vcenter.vcenter_connector import VcenterConnector
from vautils import logger
from vautils.exceptions import HostNotFound


class VcenterHost(VcenterConnector):
    """
    vCenterHost class is representing vim.HostSystem objects and its methods.
    class methods either return string or managed objects.Users can extend
    this class by adding more VirtualHostSystem related methods.
    ParentClass: vCenterConnector
    ChildClass : vCenterHostAction
    """

    def _get_host_object_by_name(self, hostname):
        """
        method find host object from list return by _get_content
        Args:
            :hostname (str): name of host that user wants to abstract from
                             net object list
        Return:
            host object( vim.HostSystem)
        Raise:
            HostNotFound
        """
        host_found = False
        host_object_list = self._get_content("host")
        for host in host_object_list:
            if host.name == hostname:
                host_found = True
                return host
        if not (host_found):
            raise HostNotFound(hostname)

    def _get_host_name(self):
        """
        method get host name in vCenter and return list
        Args:
        Return:
            host name list
        """
        all_hosts = list()
        host_object_list = self._get_content("host")
        for host in host_object_list:
            all_hosts.append(host.name)
        return all_hosts

    def is_network_in_host(self, net, hostname):
        """
        method that check given network is in vcenter or not.
        Args:
            :net(str):      name of network that user wants to check.
            :hostname(str): name of host on user wants to check.
        Returns:
            :bool  True:  if network name found in given host.
                   False: if network name is not found in given host.
        """
        host_obj = self._get_host_object_by_name(hostname)
        netObj = host_obj.network
        for network in netObj:
            if network.name == net:
                return True
        return False

    def get_vms_by_hostname(self, hostname):
        """
        method give vm list by host
        Args:
            :hostname   (str) : name of host on user wants to check.
        Returns:
            :vmlist     (list[(str)]) : list of vm by name.
        """
        vm_list = []
        host_obj = self._get_host_object_by_name(hostname)
        vmObjs = host_obj.vm
        for vms in vmObjs:
            vm_list.append(vms.name)
        return vm_list

    def get_templates_by_hostname(self, hostname):
        """
        method give templates list by host
        Args:
            :hostname   (str) : name of host on user wants to check.
        Returns:
            template_list     (list[(str)]) : list of templates by name.
        """
        template_list = []
        host_obj = self._get_host_object_by_name(hostname)
        vmObjs = host_obj.vm
        for vms in vmObjs:
            if vms.config.template:
                template_list.append(vms.name)
        return template_list


    def is_double_parking_in_host(self, hostname, inline_prefix='va'):
        """
        method that check double parking issue in a given host.
        Args:
            :hostname(str): name of host on user wants to check
            doubleparking.
        Returns:
            :True(boolean):  if double parking found on host
            :False(boolean): if double parking not found on host
        """
        host_obj = self._get_host_object_by_name(hostname)
        netObjs = host_obj.network
        for network in netObjs:
            if (inline_prefix+"-" in network.name) and \
                    ("overflow" not in network.name) \
                    and ("quarantine" not in network.name)\
                    and ('epi' not in network.name):
                if len(network.vm) >= 2:
                    connected_host = []
                    for vms in network.vm:
                        if vms.summary.runtime.host.name \
                                not in connected_host:
                            connected_host.append(
                                vms.summary.runtime.host.name)
                        else:
                            logger.debug("Double Parking found in host\
                             {} and portgroup {}".format(
                                hostname, network.name))
                            return True
        return False

    def get_double_parked_portgroup(self, hostname, inline_prefix='va'):
        """
        method that gives name of double parked portgroup.
        Args:
            :hostname(str): name of host on user wants to check
                doubleparking.
        Returns:
            :portgroup(list): name of double parked portgroup.
        """
        host_obj = self._get_host_object_by_name(hostname)
        netObjs = host_obj.network
        double_parked_portgroup = []
        for network in netObjs:
            if (inline_prefix+"-" in network.name) \
                    and ("overflow" not in network.name) \
                    and ("quarantine" not in network.name)\
                    and ('epi' not in network.name):
                if len(network.vm) >= 2:
                    connected_host = []
                    for vms in network.vm:
                        if vms.summary.runtime.host.name \
                                not in connected_host:
                            connected_host.append(
                                vms.summary.runtime.host.name)
                        else:
                            logger.debug("Double Parking found in host"\
                             "{} and portgroup {}".format(
                                hostname, network.name))
                            double_parked_portgroup.append(network.name)
        return double_parked_portgroup

    def is_vswitch_in_host(self, hostname, vswitch):
        """
        method that gives boolean based on vswitch is in a given
        host or not.
        Args:
            :hostname    (str): name of a host.
            :vswitch     (str): name of vswitch.
        Returns:
            :True        (boolean): if given switch is in given host.
            :False       (boolean): if given switch not found in host.
        """
        switch_list = []
        host_obj = self._get_host_object_by_name(hostname)
        for switch in host_obj.config.network.vswitch:
            switch_list.append(switch.name)
        return vswitch in switch_list

    def get_host_uuid(self, hostname):
        """
        method that gives host uuid.

        Args:
            :hostname (str): name of a host.
        Returns:
            :uuid (str): uuid of given host.
        """
        host_obj = self._get_host_object_by_name(hostname)
        uuid = host_obj.hardware.systemInfo.uuid
        return uuid


    def remove_inline_vswitch(self, hostname, switchname='va-inline-01'):
        """
        method that remove inline switch created by microsegmentation
        before removing switch, make sure all portgroups are empty
        Args:
            :hostname      (str): any host that connected with switch.
            :switchname  (str): inline switch name
        """
        host_obj = self._get_host_object_by_name(hostname)
        try:
            host_obj.configManager.networkSystem.RemoveVirtualSwitch(switchname)
        #TODO
        except:
            pass

    def check_promiscuous_portgroup(self, hostname, portgroup="va-01-epi"):
        """
        method that check portgroup has promiscuous mode on or not.
        checking for va-01-epi default.
        Args:
            : hostname (str): name of a host.
            : portgroup (str): name of port group that user wants to check.
        Returns:
            :boolean   (bool): True if promiscuous mode on.
                             : False if promiscuous mode off.

        """

        host_obj = self._get_host_object_by_name(hostname)
        portgroup_list = host_obj.config.network.portgroup
        for pg in portgroup_list:
            if pg.spec.name == portgroup:
                return pg.computedPolicy.security.allowPromiscuous

        proxy_list = host_obj.config.network.proxySwitch
        for proxy in proxy_list:
            dvsuuid = proxy.dvsUuid
            dvs_obj = self._get_content('content').dvSwitchManager.QueryDvsByUuid(dvsuuid)
            dvs_portgroups = dvs_obj.portgroup
            for dvs_portgroup in dvs_portgroups:
                if dvs_portgroup.config.name == portgroup:
                    return dvs_portgroup.config.defaultPortConfig.securityPolicy.allowPromiscuous.value


    def check_host_ha_status(self, hostname):
        """
        method that check host HA status.
        Args:
            :hostname (str): name of a host
        Returns:
            :HA status (str): HA status
            Total four possible status 'connectedToMaster',master'
            'networkIsolated' and 'fdmUnreachable'
        """
        host_obj = self._get_host_object_by_name(hostname)
        try:
            ha_status = host_obj.runtime.dasHostState.state
            return ha_status
        except AttributeError:
            logger.warn("HA on host {} is not enabled".format(hostname))
            return None

    def enter_into_maintainance_mode(self,hostname,power_off_vms = True):
        """
        method for entering host into maintainance mode.
        Args:
            :hostname (str): name of a host
            :power_off_vms (boolean): before going to maintainance mode
            User wants to evacuate all vms (including powered off ones)

        Note: any of vm on the host is powered on, host will not go into maintainance mode.
        and timed out.
        """
        try:
            host_obj = self._get_host_object_by_name(hostname)
            maintainance_mode_task = host_obj.EnterMaintenanceMode_Task(timeout=240,
                                                                    evacuatePoweredOffVms=power_off_vms)
            logger.info("Host {} is ENTERING into maintenance mode".format(hostname))

            self._wait_for_tasks([maintainance_mode_task],
                                        task_name="Enter Maintenance Mode")
        except Exception as error:
            logger.error("Exception raise {}".format(error.msg))


    def exit_from_maintainance_mode(self,hostname):
        """
        method for exiting host from maintainance mode.
        Args:
            :hostname (str): name of a host
        Returns:
        """
        try:
            host_obj = self._get_host_object_by_name(hostname)
            exit_maintainance_mode_task = host_obj.ExitMaintenanceMode_Task(timeout=240)
            logger.info("Host {} is EXISTING from maintenance mode".format(hostname))

            self._wait_for_tasks([exit_maintainance_mode_task],
                                        task_name="Exit Maintenance Mode")
        except Exception as error:
            logger.error("Exception raised {}".format(error.msg))

    def disconnect_host_by_name(self,hostname):
        """
        method for disconnect host by hostname.
        Args:
            :hostname (str): name of a host
        Returns:
        """
        try:
            if hostname not in self._get_host_name():
                logger.error('Not found disconnected host')
                return False
            host_obj = self._get_host_object_by_name(hostname)
            disconnect_task = host_obj.DisconnectHost_Task()
            logger.info("Host {} is disconnected".format(hostname))

            self._wait_for_tasks([disconnect_task],
                                 task_name="Disconnect host")
            return True
        except Exception as error:
            logger.error("Exception raise {}".format(error.msg))
            return False

    def reconnect_host_by_name(self,hostname):
        """
        method for reconnect host by hostname.
        Args:
            :hostname (str): name of a host
        Returns:
        """
        try:
            if hostname not in self._get_host_name():
                logger.error('Not found reconnected host')
                return False
            host_obj = self._get_host_object_by_name(hostname)
            reconnect_task = host_obj.ReconnectHost_Task()
            logger.info("Host {} is reconnected".format(hostname))

            self._wait_for_tasks([reconnect_task],
                                 task_name="Reconnect host")
            return True
        except Exception as error:
            logger.error("Exception raise {}".format(error.msg))
            return False
