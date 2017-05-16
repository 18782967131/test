"""coding: utf-8

Copyright 2017 vArmour Networks private.
All Rights reserved. Confidential

Configure Service related APIs.

.. moduleauthor:: shyang@sigma-rt.com

"""

import sys
import re
import time
import copy
from collections import namedtuple
from feature.common.system.system_3_1 import VaSystem as System
from feature.director.network.network_3_1 import VaNetwork as Network
from feature import logger
from feature.common import VaFeature


class VaService(VaFeature):
    """
        service implements methods that configure service features 
    """
    def va_add_service(self, *args, **kwargs):
        """
            Add service
            
            Param    : kwargs : dict
                       kwargs = {
                                   'name'(str) : define custom service name
                                   'rule'(str)         : rule name
                                   'src_port'(str|int)     : source port range
                                   'dst_port'(str|int)     : destination port range
                                   'protocol'(str|int)     : custom service protocol
                                   'icmp_type'(int)    : ICMP type
                                   'icmp_code'(int)    : ICMP code
                                   'def_app'(str)      : default APP
                                   'timeout'(int)      : service timeout (default: 30)
                                   'is_commit'(boolean)    : Whether commit command (default true)
                                }
            
            Return : Tuple
               True, cmd
               False, error log

            Example     : va_add_service(**kwargs)
                        kwargs = {
                                    'name'           : 'test1'
                                    'rule'           : 'test_rule'
                                    'src_port'       : '2-3|Any|2'
                                    'dst_port'       : '17-20|Any|17'
                                    'protocol'       : 'icmp|udp|tcp|Any'  
                                    'icmp_type'      :  2    
                                    'icmp_code'      :  3
                                    'def_app'        : 'http'
                                    'timeout'        :  10
                                    'is_commit'      :  True|False 
                                }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'name' not in kwargs:
            raise ValueError("name is mandatory parameter!\n")
                
        name = kwargs['name']
        rule = kwargs['rule']
        cmds = []
        set_cmd = "set service {} rule {} ".format(name,rule)

        # Config rule
        if 'rule' in kwargs:
            if 'protocol' in kwargs:                
                proto = str(kwargs['protocol']).lower()
                cmds.append(set_cmd + "protocol {}".format(proto))
                if proto == 'icmp' or proto == '1' :
                    if 'icmp_type' in kwargs:
                        cmds.append(set_cmd+"icmp-type {}".format(kwargs['icmp_type']))            
                    if 'icmp_code' in kwargs:
                        cmds.append(set_cmd + "icmp-code {}".format(kwargs['icmp_code']))
                else:
                    # Configure source port range
                    if 'src_port' in kwargs:
                        if kwargs['src_port'].find('-') == -1 :
                            src_port_strat = kwargs['src_port'].lower()
                            src_port_end = kwargs['src_port'].lower()
                        else:
                            src_port_strat = kwargs['src_port'].split('-')[0]
                            src_port_end = kwargs['src_port'].split('-')[1]
                        cmds.append(set_cmd + "source-port-range {} to {}"\
                        .format(src_port_strat, src_port_end))

                    #Configure destination port range    
                    if 'dst_port' in kwargs:
                        if kwargs['dst_port'].find('-') == -1:
                            dst_port_strat = kwargs['dst_port'].lower()
                            dst_port_end = kwargs['dst_port'].lower()
                        else:
                            dst_port_strat = kwargs['dst_port'].split('-')[0]
                            dst_port_end = kwargs['dst_port'].split('-')[1]
                        cmds.append(set_cmd + "destination-port-range {} to {}" \
                        .format(dst_port_strat, dst_port_end))    

        if 'def_app' in kwargs:
            cmds.append("set service {} default-app {}" \
                .format(name, kwargs['def_app']))

        if 'timeout' in kwargs:
            cmds.append("set service {} timeout {}" \
                .format(name, kwargs['timeout']))
        
        if 'is_commit' not in kwargs:
            is_commit = True
        else:
            is_commit = kwargs['is_commit']

        err_cmd,err_msg = self._access.va_config(cmds,commit=is_commit)

        if err_cmd is not None or err_msg is not None:
            logger.error("Failed to add service {}" .format(name))
            return False,err_msg
        else:
            logger.info("Succeed to add service {}" .format(name))
            return True,cmds

    def va_delete_service(self, *args, **kwargs):
        """
            Delete service 

            Param   : kwargs : dict
                       kwargs = {
                                   'name'(str) : define custom service name
                                   'rule'(str)         : rule name
                                   'icmp_type'(int)    : ICMP type
                                   'icmp_code'(int)    : ICMP code
                                   'def_app'(str)      : default APP
                                   'timeout'(int)      : service timeout (default: 30)
                                   'is_commit'(boolean)    : whether commit command (default True)
                                }
            
            Return : Tuple
               True, cmd
               False, error log

            Example     : va_delete_service(**kwargs)
                        kwargs = {
                                    'name'   : 'test1'
                                    'rule'           : 'test_rule'
                                    'icmp_type'      :  2    
                                    'icmp_code'      :  3
                                    'def_app'        : 'http'
                                    'timeout'        :  10
                                    'is-commit'      :  True|False
                                }        

        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'name' not in kwargs:       
            raise ValueError("name is mandatory parameter!\n")
        
        name = kwargs['name']
        unset_service = "unset service {} ".format(name)
        unset_cmds = []        

        if 'def_app' in kwargs:
            unset_cmds.append(unset_service + "default-app {}" .format(kwargs['def_app']))

        if 'timeout' in kwargs:
            unset_cmds.append(unset_service + "timeout {}" .format(kwargs['timeout']))

        # delete rule
        if 'rule' in kwargs:
            rule = kwargs['rule']
            # delete ICMP type
            if 'icmp_type' in kwargs:
                unset_cmds.append(unset_service + "rule {} icmp-type {}".format(rule, kwargs['icmp_type']))
            # delete ICMP code
            if 'icmp_code' in kwargs:
                unset_cmds.append(unset_service + "rule {} icmp-code {}".format(rule, kwargs['icmp_code']))
            if 'icmp_type' not in kwargs and 'icmp_code' not in kwargs:
                unset_cmds.append(unset_service +"rule {}".format(rule))

        # delete service
        if not 'def_app' in kwargs and not 'timeout' in kwargs and not 'rule' in kwargs:
            unset_cmds.append(unset_service)
        
        if 'is_commit' not in kwargs:
            is_commit = True
        else:
            is_commit = kwargs['is_commit']
        
        err_cmd,err_msg = self._access.va_config(unset_cmds, commit=is_commit)        

        if err_cmd is not None or err_msg is not None:
            logger.error("Failed to delete service {}" .format(name))
            return False,err_msg
        else:
            cmd_str = ','.join(unset_cmds)
            cmds_list = (cmd_str.replace('unset','set')).split(',')
            logger.info("Succeed to delete service {}" .format(name))
            return True,cmds_list
        
    def va_add_service_group(self, *args, **kwargs):
        """
           Add service group
            
           Param   : kwargs : dict
                       kwargs = {
                                   'name'(str) : 'Define custom service name'
                                   'member'(str|list)             : 'member service(s) to service group'
                                   'is_commit'(boolean)          : 'Whether commit command' (default true)

           Return : Tuple
               True, cmd
               False, error log

           Example     : va_add_service_group(**kwargs)
                         kwargs = {
                                    'name'                  : 'test1'
                                    'member'                : 'TCP-ANY'
                                    'is_commit'             :  True|False
                                }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name) 
   
        if 'name' not in kwargs:
            raise ValueError("name is mandatory parameter!\n")
        
        name = kwargs['name']
        cmds = []        

        if 'member' not in kwargs:
            cmds.append("set service-group {}".format(name))        
        else:
            member = kwargs['member']
            if type(member) != str and type(member) != list:
                raise ValueError("param member must be a list or string\n")
            if type(member) == str:
                member = member.split()
            if type(member) == list:
                for member_list in member:
                    cmds.append("set service-group {} member {}" \
                    .format(name,member_list))
        
        if 'is_commit' not in kwargs:
            is_commit = True
        else:
            is_commit = kwargs['is_commit']
            
        err_cmd,err_msg = self._access.va_config(cmds, commit=is_commit)        
            
        if err_cmd is not None or err_msg is not None:
            logger.error("Failed to add service-group {}" .format(name))
            return False,err_msg
        else:
            logger.info("Succeed to add service-group {}" .format(name))
            return True,cmds


