"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Network abstracts network interface related features.

.. moduleauthor:: ppenumarthy@varmour.com

"""

import ipaddress
import time
import sys
import re

from collections import namedtuple
from feature.common import VaFeature
from ipaddress import AddressValueError, NetmaskValueError
from feature import logger
from vautils.dataparser.string import va_parse_as_lines


class VaNetwork(VaFeature):
    """
    Network implements methods that configure networking features of the
    varmour director product.
    """
    def va_set_ipv4(self, address=None, interface=None, commit=False):
        """
        method to configure an ipv4 address for the specified interface.

        Returns:
            :bool - True on success and False on failure

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
            :ParamRequired: if interface is not provided
        """
        if not self.va_show_interface(interface):
            return False

        try:
            configured = ipaddress.IPv4Interface(address)
        except (AddressValueError, NetmaskValueError):
            raise
        else:
            ip = str(configured.ip)
            mask = configured.with_prefixlen.split('/')[1]

            cmd = "set interface {} family ipv4 address {}/{}"\
                  .format(interface, ip, mask)

            self._access.va_config(cmd, commit)

        return self._va_verify_ip(interface, configured)

    def va_show_interface(self, interface=None):
        """
        method to show the parsed interface information of the interface.
        """
        if not interface:
            cmd = "show interface"
            output = self._access.va_cli(cmd)
            return self._va_parse_interfaces(output)
        else:
            cmd = "show interface {}".format(interface)
            output = self._access.va_cli(cmd)
            return self._va_parse_interface(output)

    def va_get_fab_interface(self):
        """
        method to show the parsed interface information of the fab interfaces.

        returns:
            :fab_intf_list (list of dicts): list of parsed fab intferface info
        """
        fab_intf_list = list()
        mode_index, name_index, ignore_prompt = 3, 0, -1
        fab_intf_seen, fab_intf_name = False, None

        intf_list = self.va_show_interface()[:ignore_prompt]

        for intf in intf_list:
            pick_intf = False
            parsed_intf_dict = dict()
            if intf[mode_index] == 'Fbc':
                fab_intf_seen = True
                fab_intf_name = intf[name_index]
                pick_intf = True
            elif fab_intf_seen:
                intf_name = intf[name_index]
                if fab_intf_name in intf_name:
                    fab_intf_name = intf_name
                    pick_intf = True
                else:
                    pick_intf = False

            if pick_intf:
                parsed_intf_dict = self.va_show_interface(fab_intf_name)
                parsed_intf_dict['Name'] = fab_intf_name
                try:
                    parsed_intf_dict['Adm_link'] = intf[mode_index + 1]
                    parsed_intf_dict['Sec_addr'] = intf[mode_index + 2]
                except IndexError:
                    pass
                fab_intf_list.append(parsed_intf_dict)

        return fab_intf_list

    def va_unset_ipv4(self, address=None, interface=None, commit=False):
        """
        method to unset the ip address for the specified interface.

        Returns:
            :bool - True on success or False on failure:

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
            :ParamRequired: if interface is not provided
        """
        if not self.va_show_interface(interface):
            return False

        unset_ip = ipaddress.IPv4Interface('0.0.0.0/0')

        try:
            configured = ipaddress.IPv4Interface(address)
        except (AddressValueError, NetmaskValueError):
            raise
        else:
            ip = str(configured.ip)
            mask = configured.with_prefixlen.split('/')[1]

            cmd = "unset interface {} family ipv4 address {}/{}"\
                  .format(interface, ip, mask)

            self._access.va_config(cmd, commit)

        return self._va_verify_ip(interface, unset_ip)

    def va_set_route(self, address=None, next_hop=None, commit=False):
        """
        method to configure a static route on the device.

        Returns:
            :bool - True on success or False on failure:

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
        """
        try:
            configured = ipaddress.IPv4Interface(address)
            gw = ipaddress.IPv4Address(next_hop)
        except (AddressValueError, NetmaskValueError):
            raise
        else:
            network = configured.with_prefixlen
            gw_addr = str(gw)

            cmd = "set route static {} next-hop {}"\
                  .format(network, gw_addr)
            self._access.va_config(cmd, commit)

        return self._va_verify_route(configured, gw)

    def va_unset_route(self, address=None, commit=False):
        """
        method to remove a configured route from the device.

        Returns:
            :bool - True on success or False on failure:

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
        """
        try:
            configured = ipaddress.IPv4Interface(address)
        except (AddressValueError, NetmaskValueError):
            raise
        else:
            network = configured.with_prefixlen
            cmd = "unset route static {}".format(network)
            self._access.va_config(cmd, commit)

        return (not self._va_verify_route(configured))

    def va_show_route(self):
        """
        Method to parse the show route command on the device

        Returns:
            :dict - parsed out as a dict
        """
        cmd = "show route"
        output = self._access.va_cli(cmd)

        return self._va_parse_route(output)

    def _va_verify_ip(self, interface=None, config=None):
        """
        Helper function to compare ip address that is being
        configured and its actual set value.
        """
        output = self.va_show_interface(interface)
        if not output:
            return False

        if config.with_prefixlen == output['Local address']:
            logger.info("set/unset ip succeeded")
            return True
        else:
            logger.error("set/unset ip failed")
            return False

    def _va_parse_interface(self, output=None):
        """
        parse the output of 'show interface' command and return
        the output as a dict, with the attributes as keys.
        """
        parsed = dict()

        for line in va_parse_as_lines(output):
            line = line.strip()
            if line.startswith('--'):
                attrib, value = line.split('\t')
                attrib = attrib.split(None, 1)[1]
                attrib = attrib.strip()
                value = value.strip()
                parsed[attrib] = value
                continue
            elif line.startswith('MTU'):
                props = line.split(',')
                for prop in props:
                    attrib, value = prop.split(':')
                    attrib = attrib.strip()
                    value = value.strip()
                    parsed[attrib] = value
                continue
            elif line.startswith('OSPF'):
                parsed['ospf'] = line
            else:
                try:
                    line = line.strip()
                    attrib, value = line.split(':', 1)
                    attrib = attrib.strip()
                    value = value.strip()
                    parsed[attrib] = value
                except ValueError:
                    continue

        return parsed

    def _va_parse_interfaces(self, output=None):
        """
        parse the output of 'show interface' command and return
        the output as a dict, with the attributes as keys.
        """
        parsed = list()

        for line in va_parse_as_lines(output):
            line = line.strip()
            if not line.startswith('name') and\
               not line.startswith('-'):
                parsed.append(tuple(line.split()))
        return parsed

    def _va_verify_route(self, config=None, gateway=None):
        """
        Helper function to verify that a route exists on the
        device
        """
        routes = self.va_show_route()
        check_route_tag = 0
        if not routes:
            return False

        for route in routes:
            if config.with_prefixlen == route[1]\
                   and str(gateway) == route[3]:
                logger.info("route configured with id: {}"
                            .format(route[0]))
                check_route_tag = 1
                return True
            else:
                continue

            if not check_route_tag:
                logger.info("route does not exist on {}".format(routes))
                return False

    def _va_parse_route(self, output=None):
        """
        parse the output of 'show route' command and each
        route entry is appended as tuple to the list. The
        components that make up the entry are stored in the
        respective order within the tuple.

        Returns:
            :list of route entries

        ..note: can change to named tuple in future.
        """
        parsed = list()

        starts_withdigits = re.compile('^\d+')
        for line in output.splitlines():
            line = line.strip()
            if starts_withdigits.search(line):
                parsed.append(tuple(line.split()))

        return parsed

    def _va_parse_interface_mapping(self, output=None):
        """
        helper method to parse interface mapping

        [
         Config(varmour_intf='xe-1/0/0', 
         none='--->', 
         vm_intf='eth0', 
         mac='00:0c:29:5a:62:e9', 
         vm_index='6')
         ]
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        parsed = list()
        Config = namedtuple('Config', ['varmour_intf', 'none', 'vm_intf', 
            'mac', 'vm_index'])

        for line in va_parse_as_lines(output):
            line = line.lstrip()
            if line.startswith('xe-'):
                values = line.split()
                try:
                    parsed.append(Config(*values))
                except TypeError:
                   pass

        return parsed

    def va_show_interface_mapping(self, dev_id='all', *args, **kwargs):
        """
        API to show interface mapping
        return: 
            :list - refer to output of _va_parse_interface_mapping
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        parser = self._va_parse_interface_mapping
        cmd = "show interface device {} mapping".format(dev_id)
        mapping_info = self._access.va_cli(cmd)

        return parser(mapping_info) 

    def va_check_interfaces_order(self, *args, **kwargs):
        """
        API to check if interface order
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'dev_obj' not in kwargs or 'dev_ids' not in kwargs:
            raise ValueError("dev_obj and dev_ids are mandatory parameters!\n")
            return False

        dev_obj_list = kwargs.get('dev_obj')
        dev_id_list = kwargs.get('dev_ids')
        if not isinstance(dev_obj_list, list):
            dev_obj_list = [dev_obj_list]
        if not isinstance(dev_id_list, list):
            dev_id_list = [dev_id_list]

        intf_info = self.va_show_interface()

        cmd = 'grep "interface="'
        cmd += ' /config-varmour/configuration/varmour_conf/setup.ini'
        pat_mgt = re.compile(r'management_interface=(eth\d+)')
        pat_fbc = re.compile(r'fabric_interface=(eth\d+)')
        for dev_obj, dev_id in zip(dev_obj_list, dev_id_list):
            try:
                setup_info = dev_obj.va_shell(cmd, exit=True)
            except AttributeError as e:
                logger.error(e)
                return False

            match_result_mgt = pat_mgt.search(setup_info)
            if match_result_mgt is None:
                logger.error('Failed to get management interface from "setup.ini" file')
                return False
            mgt_intf = match_result_mgt.group(1)

            match_result_fbc = pat_fbc.search(setup_info)
            if match_result_fbc is None:
                logger.error('Failed to get fabric interface from "setup.ini" file')
                return False
            fbc_intf = match_result_fbc.group(1)

            mapping_info = self.va_show_interface_mapping(dev_id)
            for mapping in mapping_info:
                if mgt_intf in mapping:
                    dev_intf_mgt = '{}'.format(mapping.varmour_intf)
                    break
            for mapping in mapping_info:
                if fbc_intf in mapping:
                    dev_intf_fbc = '{}'.format(mapping.varmour_intf)
                    break

            for intf in intf_info:
                if re.search(dev_intf_mgt + r"\s", ' '.join(intf)) is not None:
                    intf_mode_mgt = intf[3]
                if re.search(dev_intf_fbc + r"\s", ' '.join(intf)) is not None:
                    intf_mode_fbc = intf[3]

            if intf_mode_mgt != 'Mgt' or intf_mode_fbc != 'Fbc':
                logger.error('Interface order is incorrect')
                return False

        logger.info('All interfaces order are correct')
        return True

    def va_disable_interface(self, *args, **kwargs):
        """
            Disable interface
            
            Param   : kwargs : dict
                     kwargs = {
                                'name'(str)      : interface name
                                'is_commit'(boolean) : True|False (default True)
                                }   
            Return : Tuple
                True,cmd
                False,err log

            Example    : va_disable_interface(**kwargs) 
                        kwargs = {
                                   'name'   : 'xe-4/0/0.1',
                                   'is_commit'  : True
                                }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'name' not in kwargs :
            raise ValueError("name is mandatory parameter!\n")

        name = kwargs['name']
        cmd = 'set interface {} disable'.format(name)

        if "is_commit" not in kwargs:
            is_commit = True
        else :
            is_commit = kwargs['is_commit']

        err_cmd,err_msg = self._access.va_config(cmd,commit=is_commit)

        if err_cmd is not None or err_msg is not None:
            logger.error("Failed to disable interface {}".format(name))
            return False,err_msg
        else:
            logger.info("Succeed to disable interface {}".format(name))
            return True,cmd

    def va_enable_interface(self, *args, **kwargs):
        """
            Enable interface

            Param   : kwargs : dict
                     kwargs = {
                                'name'(str)      : interface name
                                'is_commit'(boolean) : True|False (default True)
                                }   
            Return : Tuple
                True,cmd
                False,err log

            Example    : va_enable_interface(**kwargs) 
                        kwargs = {
                                   'name'   : 'xe-4/0/0.1',
                                   'is_commit'  : True
                                }            
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'name' not in kwargs :
            raise ValueError("name is mandatory parameter!\n")

        name = kwargs['name']
        cmd = 'unset interface {} disable'.format(name)
        check_disable = self.va_show_running_config()

        if "set interface {} disable".format(name) not in check_disable:
            error = "interface {} is not disabled, can't be enabled again".format(name)
            logger.error(error)
            return False.error

        if "is_commit" not in kwargs:
            is_commit = True
        else :
            is_commit = kwargs['is_commit']

        err_cmd,err_msg = self._access.va_config(cmd,commit=is_commit)

        if err_cmd is not None or err_msg is not None:
            logger.error("Failed to enable interface {}" .format(name))
            return False,err_msg
        else:
            logger.info("Succeed to enable interface {}" .format(name))
            cmds = 'set interface {} disable'.format(name)
            return True,cmds

    def va_verify_interface(self, *args, **kwargs):
        """
            Verify interface info,the API can supports physical interface and logical interfaces
            example is a part of parameter,the method supports verify the following:
                'packets sent','Interface index','Local address','Link address',
                'Security token','packets received',Vrouter','Logical interface',
                'bytes received',bytes sent','ospf','flags','Security zone',
                'Logical interface counters','Vrouter','MTU','Allowed in-bound traffic'
                'collisions','frame alignment errors','packets dropped by TX',
                'Current address','transmit errors','Link-level type',Link-mode,
                'Speed','Auto-negotiation','packets with RX overrun','Physical interface',
                'Native vlan id','Physical interface counters','packets with RX overrun',
                'CRC errors','packets dropped by RX','receive errors'

            Param   : kwargs : dict
                     kwargs = {
                                'name' (str)                 : expected to check interface name
                                'packets sent'(str)               : interface packets sent
                                'Interface index'(str)           : interface Interface index
                                'Local address'(str)              : interface local address
                                'Link address'(str)               : interface link address
                                'Security token'(str)             : interface security token
                                'packets received'(str)           : interface packets received
                                'Vrouter'(str)                    : interface vrouter
                                'Logical interface'(str)          : logical interface
                                'bytes received'(str)             : interface bytes received
                                'bytes sent'(str)                 : interface bytes sent
                                'ospf'(str)                       : interface ospf
                                'flags'(str)                      : interface flags
                                'Security zone'(str)              : security zone
                                'Logical interface counters'(str) : logical interface counters
                                'MTU'(str)                        : interface MTU
                                'Allowed in-bound traffic'(str)   : allowed in-bound traffic                                
                            }

            Return  : boolean
                True
                False

            Example     : va_verify_interface(**kwargs)
                         kwargs = {
                                    'name':'xe-3/0/1.1',
                                    'Local address': '10.11.120.46/24',
                                    'Allowed in-bound traffic': '',
                                    'packets sent': '0',
                                    'packets received': '0',
                                    'Security token': '0x000000',
                                    'MTU': '1500',
                                    'flags': '0x0',
                                    'Security zone': 'Null',
                                    'ospf': 'OSPF is not configured',
                                    'bytes received': '0',
                                    'Vrouter': 'vr-default',
                                    'Interface index': '0x801001',
                                    'Logical interface counters': '',
                                    'bytes sent': '0',
                                    'Link address': '0.0.0.0/0',
                                    'Logical interface': 'xe-3/0/1.1, Enabled, Physical link is Up'
                                }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        interface_info_dict = {}
        error_value = []

        if 'name' not in kwargs:
            raise ValueError("name is mandatory parameter!\n")

        name = kwargs['name']
        interface_info_dict = self.va_show_interface(interface=name)
        interface_key_dict = interface_info_dict.keys()
        logger.debug("Actual interface info for {} : {} ".format(name,interface_info_dict))

        for expected_key in kwargs.keys():
            if expected_key == 'name':
                continue
            if expected_key not in interface_key_dict:
                error_value.append("{} is not exist".format(expected_key))
                continue
            if kwargs[expected_key] != interface_info_dict[expected_key]:
                error_value.append(expected_key + "is not right")
                logger.error("Fail,expected {} is {} the actual {} is {}"\
                .format(expected_key,kwargs[expected_key],expected_key,interface_info_dict[expected_key]))

        if len(error_value) > 0:
            logger.error(str(error_value))
            return False
        else:
            logger.info("Succeed to varify interface info")
            return True
