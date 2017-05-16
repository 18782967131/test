"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

zone abstracts zone related features. A superset of features apply
to the product 'dir', while a subset of features apply to other products
- cp, ep, epi. It inherits from class VaFeature, where all the common
features are implemented.

.. moduleauthor:: 
"""

import re
import sys
from collections import namedtuple

from feature.common import VaFeature
from feature import logger
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines


class VaZone(VaFeature):
    """
    Zone  implements methods that configure zone of the
    varmour director product.
    """
    def va_add_zone(self, *args, **kwargs):
        """
        API to add zone
        param      : kwargs: 
                     'name' : name of zone
                     'type' : type of zone, 'L2'|'L3'|'vwire'
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_add_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                         'type' : 'L3',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs:
            raise ValueError(" name is mandatory parameter!\n") 

        type = 'L3'
        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        if 'type' in kwargs :
            type = kwargs.get('type')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'set zone {} type {}'.format(name, type)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to add zone')
            return False, err_msg

        logger.info('Succeed to add zone')
        return True, cmd
 
    def va_delete_zone(self, *args, **kwargs):
        """
        API to delete zone
        param      : kwargs: 
                     'name' : name of zone
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_delete_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs:
            raise ValueError(" name is mandatory parameter!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'unset zone {}'.format(name)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to delete zone')
            return False, err_msg

        cmd = re.sub('^unset', 'set', cmd)
        logger.info('Succeed to delete zone')
        return True, cmd

    def va_bind_interface_to_zone(self, *args, **kwargs):
        """
        API to bind interface to zone
        param      : kwargs: 
                     'name' : name of zone
                     'intf' : interface name, 'xe-3/0/2.1'
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_bind_interface_to_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                         'interface' : 'xe-3/0/2.1',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs or \
            not 'intf' in kwargs:
            raise ValueError(" 'name' and 'intf' are mandatory parameters!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        intf = kwargs.get('intf')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'set zone {} interface {}'.format(name, intf)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to bind interface to zone')
            return False, err_msg

        logger.info('Succeed to bind interface to zone')
        return True, cmd
 
    def va_unbind_interface_from_zone(self, *args, **kwargs):
        """
        API to unbind interface from zone
        param      : kwargs: 
                     'name' : name of zone
                     'intf' : interface name, 'xe-3/0/2.1'
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_bind_interface_to_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                         'interface' : 'xe-3/0/2.1',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs or \
            not 'intf' in kwargs:
            raise ValueError(" 'name' and 'intf' are mandatory parameters!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        intf = kwargs.get('intf')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'unset zone {} interface {}'.format(name,intf)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to unbind interface from zone')
            return False, err_msg
            
        cmd = re.sub('^unset', 'set', cmd)
        logger.info('Succeed to unbind interface from zone')
        return True, cmd

    def va_bind_zone_guard_to_zone(self, *args, **kwargs):
        """
        API to bind zone guard to zone
        param      : kwargs: 
                     'name'  : name of zone,
                     'guard' : name of zone guard,
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_bind_guard_to_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                         'guard' : 'zone_guard',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs or \
            not 'guard' in kwargs:
            raise ValueError(" 'name' and 'guard' are mandatory parameters!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        guard = kwargs.get('guard')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'set zone {} zone-guard {}'.format(name, guard)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to bind zone guard to zone')
            return False, err_msg

        logger.info('Succeed to bind zone guard to zone')
        return True, cmd

    def va_unbind_guard_from_zone(self, *args, **kwargs):
        """
        API to unbind zone guard from zone
        param      : kwargs: 
                     'name'  : name of zone,
                     'guard' : name of zone guard,
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_unbind_guard_from_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                         'guard' : 'zone_guard',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs or \
            not 'guard' in kwargs:
            raise ValueError(" 'name' and 'guard' are mandatory parameters!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        guard = kwargs.get('guard')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'unset zone {} zone-guard {}'.format(name, guard)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to unbind zone gurad from zone')
            return False, err_msg
            
        cmd = re.sub('^unset', 'set', cmd)
        logger.info('Succeed to unbind zone guard from zone')
        return True, cmd

    def va_disable_profile_stateful_inspection(self, *args, **kwargs):
        """
        API to disable stateful inspection of profile
        param      : kwargs: 
                     'name'  : name of stateful inspection,
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_disable_profile_stateful_inspection(**kwargs)
                     kwargs = {
                         'name' : 'test_state',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs:
            raise ValueError(" name is mandatory parameter!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'set profile stateful-inspection {} strict-tcp-check disable'.format(name)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to disable stateful inspection of profile')
            return False, err_msg

        logger.info('Succeed to disable stateful inspection of profile')
        return True, cmd

    def va_enable_profile_stateful_inspection(self, *args, **kwargs):
        """
        API to enable stateful inspection of profile
        param      : kwargs: 
                     'name'  : name of stateful inspection,
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_enable_profile_stateful_inspection(**kwargs)
                     kwargs = {
                         'name' : 'test_state',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs:
            raise ValueError(" name is mandatory parameter!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'unset profile stateful-inspection {} strict-tcp-check disable'.format(name)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to enable stateful inspection of profile')
            return False, err_msg

        logger.info('Succeed to enable stateful inspection of profile')
        return True, cmd[2:]

    def va_bind_stateful_inspection_to_zone(self, *args, **kwargs):
        """
        API to bind stateful inspection to zone
        param      : kwargs: 
                     'name' : name of zone
                     'state_name'  : name of stateful inspection
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_unbind_stateful_inspection_to_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                         'state_name' : 'state_ins',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs or \
            not 'state_name' in kwargs:
            raise ValueError(" 'name' and 'state_name' are mandatory parameters!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        state_name = kwargs.get('state_name')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'set zone {} stateful-inspection {}'.format(name, state_name)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to bind state inspection to zone')
            return False, err_msg

        logger.info('Succeed to bind state inspection to zone')
        return True, cmd

    def va_unbind_stateful_inspection_from_zone(self, *args, **kwargs):
        """
        API to unbind stateful inspection from zone
        param      : kwargs: 
                     'name' : name of zone
                     'state_name'  : name of stateful inspection
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_unbind_stateful_inspection_from_zone(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                         'state_name' : 'state_ins',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs or \
            not 'state_name' in kwargs:
            raise ValueError(" 'name' and 'state_name' are mandatory parameters!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        state_name = kwargs.get('state_name')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'unset zone {} stateful-inspection {}'.format(name, state_name)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to unbind stateful inspection from zone')
            return False, err_msg

        cmd = re.sub('^unset', 'set', cmd)
        logger.info('Succeed to unbind stateful inspection from zone')
        return True, cmd

    def va_enable_zone_asymmetric_routing(self, *args, **kwargs):
        """
        API to enable asymmetric-routing on zone
        param      : kwargs: 
                     'name' : name of zone
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_enable_zone_asymmetric_routing(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs:
            raise ValueError(" name is mandatory parameter!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'set zone {} asymmetric-routing enable'.format(name)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to enable asymmetric-routing on zone')
            return False, err_msg

        logger.info('Succeed to enable asymmetric-routing on zone')
        return True, cmd

    def va_disable_zone_asymmetric_routing(self, *args, **kwargs):
        """
        API to disable asymmetric-routing on zone
        param      : kwargs: 
                     'name' : name of zone
                     'is_negative' : negative test,  True|False, False by default
                     'is_commit'   : submit command, True|False, True by default
        example    : va_disable_zone_asymmetric_routing(**kwargs)
                     kwargs = {
                         'name' : 'testzone',
                     }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs:
            raise ValueError(" name is mandatory parameter!\n")

        is_commit = True
        is_negative = False
        name = kwargs.get('name')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')
        if 'is_negative' in kwargs:
            is_negative = kwargs.get('is_negative')

        cmd = 'unset zone {} asymmetric-routing enable'.format(name)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to disable asymmetric-routing on zone')
            return False, err_msg

        cmd = re.sub('^unset', 'set', cmd)
        logger.info('Succeed to disable asymmetric-routing on zone')
        return True, cmd

    def _va_parse_zone(self, output=None):
        """
        helper method to parse zone
        varmour@vArmour#ROOT(config)> do show zone
        ID              Name    Type    Asymmetric-routing    Interfaces
        --              ----    ----    ------------------    ----------
         1              Null    NULL                    No                  
        16              Intc    Intc                    No                  
        19              test      L3                    No      xe-1/0/3.1
                                                                       xe-1/0/3.3
                                                                       xe-1/0/3.2
        21           example      L2                    No                  
        varmour@vArmour#ROOT(config)>

        return (dict): look at the following output
        [
            Zone(ID='1',  Name='Null', Type='NULL', Asymmetric_routing='No', 
                 Interfaces=''), 
            Zone(ID='16', Name='Intc', Type='Intc', Asymmetric_routing='No', 
                 Interfaces=''), 
            Zone(ID='19', Name='test', Type='L3', Asymmetric_routing='No', 
                 Interfaces='xe-1/0/3.1, xe-1/0/3.3, xe-1/0/3.2'),          
            Zone(ID='21', Name='example', Type='L2', Asymmetric_routing='No', 
                 Interfaces='')
        ]
        """
        parsed = list()
        Zone = namedtuple('Zone', ['ID', 'Name', 'Type', 'Asymmetric_routing',
                                       'Interfaces'])

        for line in va_parse_as_lines(output):
            line = line.lstrip()
            if not line.startswith('ID')\
                    and not line.startswith('-')\
                    and not line.startswith('varmour'):

                if not line.startswith('xe'):
                      values = line.split()
                      if len(values) == 4:
                          values.append('')
                else:
                      if line.startswith('xe'):
                          parsed.remove(Zone(*values))
                          values[-1] += ',{}'.format(line)
                try:
                    parsed.append(Zone(*values))
                except TypeError:
                    pass

        return parsed

    def va_show_zone(self, *args, **kwargs):
        """
        method to get zone
        returns:
            :list: list of namedtuple, see parser method to get detailed
                   info
        """
        cmd = "show zone"
        output = self._access.va_cli(cmd)

        return self._va_parse_zone(output)

    def va_check_zone(self, *args, **kwargs):
        """
        API to check zone
        param      : kwargs: 
                     'name' : name of zone
                     'type' : type of zone, 'L2'|'L3'|'vwire'
                     'intf' : interface name, string or a list
                     'routing' : asymmetric routing, Yes|No
        example    : va_check_zone(**kwargs)
                     kwargs = {
                         'name' : 'test',
                         'type' : 'L3',
                         'intf' : 'xe-3/0/2.1',
                         'routing' : 'Yes',
                     }
        return: True on success, False on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'name' in kwargs:
            raise ValueError(" name is mandatory parameter!\n")

        check_list = list()
        name = kwargs.get('name')

        if 'type' in kwargs :
            type = kwargs.get('type')
            check_list.append('Type')
        if 'routing' in kwargs :
            asymmetric_routing = kwargs.get('routing')
            check_list.append('Asymmetric_routing')
        if 'intf' in kwargs :
            interfaces = kwargs.get('intf')
            check_list.append('Interfaces')

        not_matched = dict()
        zone_info = self.va_show_zone()
        for info in zone_info:
            matched = False
            if info.Name == name:
                for check_name in check_list:
                    matched = True
                    expected_value = eval(check_name.lower())
                    actual_value = eval('info.{}'.format(check_name))
                    if check_name == 'Interfaces':
                        actual_value = actual_value.split(',')
                        if len(set(expected_value) & set(actual_value)) < \
                            len(set(expected_value)):
                            matched = False
                    else:
                        if expected_value != actual_value:
                            matched = False

                    if not matched:
                        logger.error('Expected value: {}, actual value: {}'.format(
                            expected_value, actual_value))
                        not_matched[check_name] = expected_value
                break

        if not matched or len(not_matched) != 0:
            not_matched['Name'] = name
            logger.error('Not matched zone info {}'.format(not_matched))
            return False

        logger.info('Matched all zone info')
        return True
