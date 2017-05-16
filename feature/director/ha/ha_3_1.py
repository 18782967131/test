"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

High availability abstracts high availability related features. 
A superset of features apply to the product 'dir', while a subset 
of features apply to other products cp, ep, epi. It inherits from 
class VaFeature, where all the common features are implemented.

.. moduleauthor:: ppenumarthy@varmour.com, mzhao@varmour.com
"""

import sys
import re
import time

from feature import logger
from feature.common import VaFeature
from feature import Controller
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines

class VaHa(VaFeature):
    """
    High availability implements methods to configure or view the high 
    availablity related features.
    """
    def __init__(self, resource=None):
        """
        instantiate the feature object by calling parent's init. then
        setup controller to create feature objects for other features
        to be used within this feature. Also set the common system
        instance to the parent attribute - instead of inheriting it
        and complicating the dependency we are holding a link to the
        common system feature and routing calls to it through getattr.

        kwargs:
            resource - VaResource object
        """
        super(VaHa, self).__init__(resource)
        self._parent = None

        other_features = ['network', 'system-common']
        self.controller = Controller(resource, other_features)

        common = '_'.join(('', 'system-common'))
        if common in self.controller.__dict__.keys():
            self._parent = self.controller.__dict__.get(common)

    def va_config_ha(self, *args, **kwargs):
        """
        API to configure HA, both support to create HA and update HA. For create HA,
        user must pass local_address and remote_address data.
        param   : kwargs : dict
        kwargs = {
                    'local_address'  : Configure HA Interface IPV4 address,IPv4 address and netmask,\
                                       for example : 8.8.8.1/24
                    'remote_address' : Configure peer HA Interface IPV4 address, for exampe : 8.8.8.2
                    'priority'       : HA priority number for current device <1-255>, for example : 10
                    'preempt'        : HA preemption enable, enable.
                    'mgt-vip'        : Virtual management IP, vip should in same network with mgt ip. eg: 10.11.120.2
                    'fabric-link-ip' :  Fabric monitoring IP, link ip should in same network with fabric. eg:10.0.0.2
                    'track-fabric-down-time': Number of seconds fabric link down to trigger HA state change <1-2>.eg:2
                    'heartbeat-interval': Time interval between heartbeats in milliseconds <100-5000>. for example:100
                    'heartbeat-threshold': Number of missed heartbeats to trigger failover <3-100>, for exampe :10
                    'fabric-probe-num': Number of fabric probes to send during failover <3-100>. eg: 100
                    'g-arp-num':number of groups of gratuitous arp to send during failover <1-16>, for example:5
                    'is_commit': True|False, True by default
            }
        return: a tuple of True and cmdList on success, False and err_msg on failure
        Example : va_config_ha(**kwargs)
            kwargs = {
                    'local_address'  : '8.8.8.1/24',
                    'remote_address' : '8.8.8.2',
                    'priority'       : 10,
                    'preempt'        : 'enable',
                    'mgt-vip'        : '10.11.120.2',
                    'fabric-link-ip' : '10.0.0.2',
                    'track-fabric-down-time': 2,
                    'heartbeat-interval': 100,
                    'heartbeat-threshold': 100,
                    'fabric-probe-num':10,
                    'g-arp-num':10,
                    'is_commit': True|False, True by default
            }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   

        cmdList = list()
        cmd = "set high-availability"
        cmd1 = cmd+" global"

        is_commit = True
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'local_address' in kwargs and  \
            'remote_address' in kwargs:
            local_address  = kwargs.get('local_address')
            remote_address = kwargs.get('remote_address').split('/')[0]
            cmdList.append('{} local-address {} remote-address {}'.format(cmd,
                local_address, remote_address))

        if 'priority' in kwargs:
            cmdList.append('{} priority {}'.format(cmd, kwargs.get('priority')))

        if 'preempt' in kwargs:
            cmdList.append('{} preempt enable'.format(cmd1))

        if 'mgt-vip' in kwargs:
            cmdList.append('{} mgt-vip {}'.format(cmd1,kwargs.get('mgt-vip')))

        if 'fabric-link-ip' in kwargs:
            cmdList.append('{} fabric-link-ip {}'.format(cmd1,kwargs.get('fabric-link-ip')))

        if 'track-fabric-down-time' in kwargs:
            cmdList.append('{} track-fabric-down-time {}'.format(cmd1,kwargs.get('track-fabric-down-time')))

        if 'heartbeat-interval' in kwargs:
            cmdList.append('{} heartbeat-interval {}'.format(cmd1,kwargs.get('heartbeat-interval')))

        if 'heartbeat-threshold' in kwargs:
            cmdList.append('{} heartbeat-threshold {}'.format(cmd1,kwargs.get('heartbeat-threshold')))

        if 'fabric-probe-num' in kwargs:
            cmdList.append('{} fabric-probe-num {}'.format(cmd1,kwargs.get('fabric-probe-num')))

        if 'g-arp-num' in kwargs:
            cmdList.append('{} g-arp-num {}'.format(cmd1,kwargs.get('g-arp-num')))

        ret_val, err_msg = self._access.va_config(cmdList, commit=is_commit)
        if ret_val is not None:
            return False, err_msg

        logger.info('Succeed to configure HA')
        return True, cmdList 

    def _va_parse_ha_status(self, output=None):
        """
        helper method to parse 'show high-availabe'

        return (dict): look at the following output

        {
            'HA Mode': 'OFF',
            'IF IDX': 'eth2',
            'HA Overlay(AWS)': 'Not Enabled',
            'HA Failover State': 'Failover Not Ready',
            'Preempt': 'Disable'
            'HA STATUS': ['PRIMARY BACKUP 702989293 50 8.8.8.2  1', 
                          'MASTER 691058960 50 8.8.8.1 (self) 2']
        }
        """

        parsed = dict()

        parsed['HA STATUS'] = list()
        for line in va_parse_as_lines(output):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':')
                parsed[key.strip()] = value.strip()
            elif line.startswith('MASTER') or \
                    line.startswith('INIT') or \
                    line.startswith('INELIGIBLE'):
                values = tuple(line.split())
                parsed['HA STATUS'].append(values)
            elif line.startswith('PRIMARY BACKUP'):
                values = list(line.split())
                values[:2] = [' '.join(values[:2])]
                parsed['HA STATUS'].append(tuple(values))
            else:
                continue

        return parsed

    def va_show_ha(self):
        """
        API to show high-availability
        return: 
            :None or dict - refer to output of _va_parse_ha_status
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   

        parser = self._va_parse_ha_status
        cmd = "show high-availability"
        ha_info = self._access.va_cli(cmd)
        if 'ha_info' not in dir():
            logger.error("Failed to get high availability")
            return None

        return parser(ha_info) 

    def va_check_ha_mode(self):
        """
               API to check HA mode is ON/OFF
               Returns:
                   :string - None or ha_mode(ON/OFF)
               """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        ha_mode = None

        ha_info = self.va_show_ha()

        ha_mode = ha_info.get('HA Mode')

        logger.info('The Mode of HA is {}'.format(ha_mode))
        return ha_mode

    def va_check_ha_preempt_enable(self):
        """
        API to check if HA preempt enabled
        Returns:
            :bool - True on enabled or False on disabled:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        ha_info = self.va_show_ha()
        ha_preempt_state = ha_info.get('Preempt')
        if ha_preempt_state != 'Enable':
            logger.info('HA Preempt is not enabled')
            return False
        logger.info('HA Preempt is enabled')
        return True

    def va_check_ha_ready(self):
        """
        API to check if HA ready
        Returns:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   

        ha_info = self.va_show_ha()
        ha_state = ha_info.get('HA Failover State')
        if  ha_state != "Failover Ready":
            logger.error('HA Failover State is not ready')
            return False

        logger.info('HA Failover State is ready')
        return True

    def va_get_ha_role(self):
        """
        API to get role of HA
        return: 
            :string - None or ha_role(master/backup)
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   

        ha_role = None

        ha_info = self.va_show_ha()

        reg = '\s+\d+\s+\d+\s+([\d.]+)\s+\(self\)'
        master_pat = re.compile(r'MASTER{}'.format(reg))
        backup_pat = re.compile(r'PRIMARY BACKUP{}'.format(reg))
        init_pat = re.compile(r'INIT\(reboot\){}'.format(reg))
        ineligible_pat = re.compile(r'INELIGIBLE{}'.format(reg))

        ha_role_info = ha_info.get('HA STATUS')
        for role_info in ha_role_info:
            role_info = ' '.join(role_info)
            if master_pat.search(role_info) is not None:
                ha_role = 'master'
                break
            elif backup_pat.search(role_info) is not None:
                ha_role = 'pb'
                break
            elif init_pat.search(role_info) is not None:
                ha_role = 'init'
                break
            elif ineligible_pat.search(role_info) is not None:
                ha_role = 'ineligible'
                break

        logger.info('The role of HA is {}'.format(ha_role))
        return ha_role

    def va_check_ha_is_master(self):
        """
        API to check if HA is master
        return: 
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   

        ha_role = self.va_get_ha_role()
        if ha_role != 'master':
            logger.error('The role of director is {}'.format(ha_role))
            return False

        logger.info('The role of director is MASTER')
        return True

    def va_check_ha_is_pb(self):
        """
        API to check if HA is pb
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        ha_role = self.va_get_ha_role()
        if ha_role != 'pb':
            logger.error('The role of director is {}'.format(ha_role))
            return False

        logger.info('The role of director is PB')
        return True

    def va_check_ha_is_init(self):
        """
        API to check if HA is init state
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        ha_role = self.va_get_ha_role()
        if ha_role != 'init':
            logger.error('The role of director is {}'.format(ha_role))
            return False

        logger.info('The role of director is INIT')
        return True

    def va_check_ha_is_ineligible(self):
        """
        API to check if HA is ineligible state
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        ha_role = self.va_get_ha_role()
        if ha_role != 'ineligible':
            logger.error('The role of director is {}'.format(ha_role))
            return False

        logger.info('The role of director is INELIGIBLE')
        return True

    def va_do_ha_failover(self):

        """
        API to do HA failover
        return: 
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   

        if not self.va_check_ha_is_master():
            return False

        if not self.va_check_ha_ready():
            return False

        cmd = 'request system failover'
        failover_info = self._access.va_cli(cmd)

        pat = re.compile(r'FAILED HA FAILOVER')
        match_result = pat.search(failover_info)
        if match_result is not None:
            logger.error(failover_info)
            return False

        logger.info('Succeed to do HA failover')
        return True

    def va_remove_ha(self, *args, **kwargs):
        """
        API to remove HA.
        param   : kwargs : dict
        example : va_remove_ha(**kwargs)
            kwargs = {
                    'local_address'  : '8.8.8.1/24',
                    'remote_address' : '8.8.8.2',
                    'priority'       : 10,
                    'preempt'        : enable
                    'is_commit': True|False, True by default
            }
        return: a tuple of True and cmdList on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        is_master = False
        if self.va_check_ha_is_master():
            is_master = True

        if 'local_address' not in kwargs or\
            'remote_address' not in kwargs:
            raise ValueError("local_address and remote_address are \
mandatory parameters!\n")

        is_commit = True
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')

        if not is_master:
            setup_ini_file = '/config-varmour/configuration/varmour_conf/setup.ini'
            intf_info = self._access.va_shell('grep "fabric_interface=" {}'.format(
                setup_ini_file))
            if 'intf_info' not in dir():
                logger.error('Failed to get fabric interface from file {}'.format(
                setup_ini_file))
                return False

            match_result = re.search(r'fabric_interface=(eth\d+)',intf_info,re.I|re.M)
            interface = match_result.group(1)

            mapping_info = self.controller.va_show_interface_mapping(dev_id='1')
            for mapping in mapping_info:
                if interface in mapping:
                    fabric_intf = mapping.varmour_intf
                    break

            cmd = 'set interface {} disable'.format(fabric_intf)
            ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
            if ret_val is not None:
                return False

            time.sleep(1)

        cmdList = list()
        cmd = "unset high-availability"
        local_address  = kwargs.get('local_address')
        remote_address = kwargs.get('remote_address').split('/')[0]
        cmdList.append('{} local-address {} remote-address {}'.format(cmd,
            local_address, remote_address))
        if 'priority' in kwargs:
            cmdList.append('{} priority {}'.format(cmd, kwargs.get('priority')))
        if 'preempt' in kwargs:
            cmdList.append('{} global preempt enable'.format(cmd))
        ret_val, err_msg = self._access.va_config(cmdList, commit=is_commit)
        if ret_val is not None:
            return False

        if not is_master:
            cmd = 'unset interface {} disable'.format(fabric_intf)
            ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
            if ret_val is not None:
                return False, err_msg

        for cmd in cmdList:
            cmdList.remove(cmd)
            cmdList.append(re.sub('^unset', 'set', cmd))

        logger.info('Succeed to remove HA')
        return True, cmdList

    def va_check_mgt_vip(self):
        """
        API to check if HA mgt_vip
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        ha_info = self.va_show_ha()
        ha_mgt_vip = ha_info.get('HA virtual management ip')
        if not ha_mgt_vip:
            logger.info('HA Management vip is not enabled')
            return False
        logger.info('HA Management vip is ' + ha_mgt_vip)
        return True

    def va_check_fabric_monitoring_ip(self):
        """
        API to check if HA fabric monitoring ip
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        ha_info = self.va_show_ha()
        ha_fabric_link_ip = ha_info.get('Fabric monitoring ip')
        if not ha_fabric_link_ip:
            logger.info('HA Fabric monitoring ip is not enabled')
            return False
        logger.info('HA Fabric monitoring ip is ' + ha_fabric_link_ip)
        return True
