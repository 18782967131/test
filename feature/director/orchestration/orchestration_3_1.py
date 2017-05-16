"""coding: utf-8

Copyright 2016 r Networks private.
All Rights reserved. 

VaOrchestration provides related feature to configuration or verify. 
A superset of features apply to the product 'dir', while a subset of features
apply to other products
- cp, ep, epi. It inherits from class VaFeature, where all the common
features are implemented.

.. moduleauthor:: xuewang@sigma-rt.com
"""

import re
import sys
from collections import namedtuple

from feature.common import VaFeature
from feature import logger
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines
import uuid

class VaOrchestration(VaFeature):
    """
    Orchestration implement methods that configure orchestration
    of varmour director product.
    """
    def va_show_orchestration(self):
        """
        API to show orchestration info
        Returns: dict: dict of parsed information
                 {'vcenter_1': {'user': 'root',
                                'auto power switch for maintenance mode': ' disabled', 
                                'type': 'vcenter', 'Enable': 'Y', 
                                'Address': '10.11.120.117:443'}, 
                  'vcenter_2': {'user': 'root', 
                                'auto power switch for maintenance mode': ' disabled', 
                                'type': 'vcenter', 'Enable': 'Y', 
                                'Address': '10.11.120.116:443'}
                 }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        cmd = 'show orchestration configured'
        output = self._access.va_cli(cmd)
        info = output.splitlines()
        ret = dict()
        _parse_info = list()

        for idx in range(len(info)-1):
            if not info[idx].strip().startswith('Orchestration') and \
                not info[idx].strip().startswith(cmd):
                if info[idx].startswith('Profile'):
                    for opt in info[idx].split():
                        if opt == 'Profile':
                            continue
                        _parse_info.append(opt)
                else:
                    _parse_info.append(info[idx].strip())

        for idx_1 in range(len(_parse_info)):
            info = _parse_info[idx_1]
            if info.split(':')[0] == 'Name':
                ret[info.split(':')[1]] = dict()
                for idx_2 in range(idx_1+1,len(_parse_info)):
                    if _parse_info[idx_2].split(':')[0] == 'Name':
                        idx_1 = idx_2 + 1
                        break
                    key, value = _parse_info[idx_2].split(':',1)
                    ret[info.split(':')[1]][key] = value
                
        return ret
    
    def va_unset_orchestration(self,**kwargs):
        """
        API to unset orchestration info
        Param:
            kwargs:
            instance: vcenter instance name
            orchestration_flag (list) : Need to unset orchestration option flag
                                       ('enable'|'port'|'inline-switch-name'|'auto-power-switch')
            port : Need to unset port id (default:443)
            is_commit : commit True|False(default:True)
            is_negative : Negative test True|False(default:False)
        Returns: Tuple
                 True,cmd
                 False,err log
        Example:
               va_unset_orchestration(instance='vcenter_1',orchestration_flag='enable')
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        if 'instance' not in kwargs:
            raise ValueError("'instance' is mandatory in kwargs")
        pre_cmd = 'unset orchestration {}'.format(kwargs.get('instance'))
        is_commit = kwargs.get('is_commit',True)
        is_negative = kwargs.get('is_negative',False)
        name_list = ['enable','port','inline-switch-name','auto-power-switch']
        cmds = list()

        if 'orchestration_flag' in kwargs:
            orch_flag = kwargs.get('orchestration_flag')
            if isinstance(orch_flag,str):
                orch_flag = orch_flag.split(',')
            for flag in orch_flag :
                if flag not in name_list:
                    logger.error('Wrong param {}'.format(flag))
                    raise ValueError('Invalid param "{}"'.format(flag))
                elif flag == 'port':
                    port_id = kwargs.get('port','443')
                    cmds.append(pre_cmd + ' port {}'.format(port_id))
                elif flag == 'auto-power-switch':
                    cmds.append(pre_cmd + ' auto-power-switch enable')
                else:
                    cmds.append(pre_cmd + ' {}'.format(flag))
        else:
            cmds.append(pre_cmd)
        
        ret_val, err_msg = self._access.va_config(cmds, commit=is_commit)
        if ret_val is not None:
            if not is_negative:
                logger.error('Failed to unset orchestration')
            else:
                logger.info('Failed to unset orchestration')
            return False, err_msg
        cmd_str = ','.join(cmds)
        cmd_list = re.sub('^unset', 'set', cmd_str)
        logger.info('Succeed to unset orchestration')
        return True, cmd_list

    def va_set_orchestration(self,**kwargs):
        """
        API to change orchestration info
        Param:
            kwargs:
            instance: vcenter instance name
            orchestration_flag (list) : Need to change orchestration option flag
            port : Need to changed port id
            type : Instance type (vcenter|aci)
            username : Instance username
            password : Instance password
            address  : Instance address
            inline-switch-name: Customized inline switch name
            is_commit : commit True|False(default:True)
            is_negative : Negative test True|False(default:False)
        Returns: Tuple
                 True,cmd
                 False,err log
        Example:
               va_set_orchestration(instance='vcenter_2',
                                    name_flag=['address','user','password','enable','port'],
                                    address='10.11.120.116',user='root',
                                    password='varmour',port='440')
               va_unset_orchestration(instance='vcenter_1',orchestration_flag='enable')
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        if 'instance' not in kwargs:
            raise ValueError("'instance' is mandatory in kwargs")
        pre_cmd = 'set orchestration {} '.format(kwargs.get('instance'))
        is_commit = kwargs.get('is_commit',True)
        is_negative = kwargs.get('is_negative',False)
        name_list = ['type','address','password','username','port','inline-switch-name','auto-power-switch','enable']
        cmds = list()
        err_cmd = None
        
        if kwargs.get('orchestration_flag'):
            name_flags = kwargs.get('orchestration_flag')
            if isinstance(name_flags,str):
                name_flags = name_flags.split(',')
            for flag in name_flags:
                if flag not in name_list:
                    logger.error('Wrong param "{}"'.format(flag))
                    raise ValueError('Invalid param "{}"'.format(flag))
                else:
                    if flag == 'enable':
                        cmds.append(pre_cmd + flag)
                    elif flag == 'auto-power-switch':
                        cmds.append(pre_cmd + flag + ' enable')
                    else:
                        if flag not in kwargs.keys():
                            logger.error('Not found param "{}"!! Can not to configure'.format(flag))
                            raise ValueError('Not found param "{}"'.format(flag))
                        elif flag == 'password':
                            passwd = kwargs.get(flag)
                            cmd = pre_cmd + 'passphrase'
                            err_cmd, err_msg1 = self._access.va_config(cmd, **{'handle_password':passwd})
                        else:
                            cmds.append(pre_cmd + '{} {}'.format(flag,kwargs.get(flag)))
        
        ret_val, err_msg2 = self._access.va_config(cmds, commit=is_commit)
        if ret_val is not None or err_cmd is not None:
            if not is_negative:
                logger.error('Failed to set orchestration')
            else:
                logger.info('Failed to set orchestration')
            if err_cmd is not None:
                return False, err_msg1
            return False, err_msg2
        if kwargs.get('password'):
            cmds.append(cmd)
        logger.info('Succeed to set orchestration')
        return True, cmds
