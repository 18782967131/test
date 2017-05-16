"""coding: utf-8

Copyright 2017 vArmour auth private.
All Rights reserved. Confidential

auth related features.
.. moduleauthor:: shyang@sigma-rt.com
"""
from collections import namedtuple
import copy
import sys
import re
from feature.director.system.system_3_1 import VaSystem as System
from feature import logger
from feature.common import VaFeature
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines


class VaAuth(VaFeature):
    """
        Configure auth
    """
    def va_set_admin_auth(self, *args, **kwargs):
        """
            Set the admin-auth policy and admin-auth remote mode
            Param    : kwargs : dict
                       kwargs = {
                                    'mode'(str)         : 'admin-auth remote mode' (radius|ladp|ad)
                                    'policy'(str|list)  : 'Admin user authentication policy' (fallback-to-next|fallback-if-down)
                                    'is_commit'(boolean): True|False (default:True)
                                }
            Return    : Tuple
                True,cmd
                False,error log
             
             Example    : 
                       kwargs   = {
                                    'mode'      : 'ladp'
                                    'policy'    : fallback-to-next
                                    'is_commit' : True
                        }                         
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        cmds = []

        if not 'mode' in kwargs:
            raise ValueError("mode is mandatory parameter!\n")        

        if not 'is_commit' in kwargs:
            is_commit = True
        else:
            is_commit = kwargs['is_commit']
        
        cmds.append("set system admin-auth remote {}".format(kwargs['mode']))
        
        if 'policy' in kwargs:
            policy = kwargs['policy']
            if type(policy) == str:
                policy = policy.split()
            if type(policy) == list:
                for policy_list in policy:
                    cmds.append("set system admin-auth policy {}" \
                    .format(policy_list))

        err_cmd,err_msg = self._access.va_config(cmds, commit=is_commit)
        
        if err_cmd != None or err_msg != None:
            logger.error("Fail to set admin-auth")
            return False,err_msg
        else:
            logger.info("Succeed to set admin-auth")
            return True,cmds        
