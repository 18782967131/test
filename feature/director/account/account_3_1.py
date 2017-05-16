"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Configure management user account related APIs.

.. moduleauthor:: xliu@sigma-rt.com
"""

import sys, re, time, copy
from collections import namedtuple
from feature.common import VaFeature
from feature import logger
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines


class VaAccount(VaFeature):
    """
    Configure management user account
    """

    def va_add_user(self, *args, **kwargs):

        """
           Add user
           param      : kwargs : dict
                       kwargs = {
                                   'name'    : 'account user name',
                                   'password': 'account user password',
                                   'role'    : 'account user role' [admin|operator|reader]
                                   'is_commit': True|False,  Optional parameters
                                  }
           return: Tuple
               True, cmd
               False, error log

            Example    : va_add_user(**kwargs)
                      kwargs = {
                       'name'    : 'varmour_no_cli',
                       'password': 'vArmour123',
                       'role'    : 'admin'
                       'is_commit': True
                      }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if not 'name' in kwargs:
            raise ValueError("name is mandatory parameter!\n")

        if not 'password' in kwargs:
            raise ValueError("password is mandatory parameter!\n")

        if not 'role' in kwargs:
            raise ValueError("role is mandatory parameter!\n")

        if not 'is_commit' in kwargs:
            is_commit = True
        else:
            is_commit = kwargs.get('is_commit')

        name = kwargs.get('name')
        password = kwargs.get('password')
        role = kwargs.get('role')
        cmd = 'set system user {} role {}'.format(name,role)
        cmd1 = 'set system user {} password'.format(name)
        err_cmd,err_msg = self._access.va_config(cmd, commit=False,exit=False)
        err_cmd1,err_msg1 = self._access.va_config(cmd1, **{'handle_password':password})

        if err_cmd is not None or err_msg is not None or\
            err_cmd1 is not None or err_msg1 is not None:
            logger.error('Failed to add user {}'.format(name))
            return False, err_msg

        logger.info('Succeed to add user {}'.format(name))
        return True,[cmd,cmd1]

    def va_check_user(self, *args, **kwargs):

        """
           check user is exist
           param      : kwargs : dict
                       kwargs = {
                                 'name'    : 'account user name'
                       }
           return: boolean
               True
               False

            Example    : va_check_user(**kwargs)
                       kwargs = {
                            'name'    : 'varmour_no_cli'
                       }
         """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if not 'name' in kwargs:
            raise ValueError("name is mandatory parameter!\n")

        name = kwargs.get('name')
        info = self.va_get_system_user_info()

        if name in info:
            logger.info("the user {} is exist".format(name))
            return True
        else:
            logger.error("the user {} is not exist".format(name))
            return False
    
    def _va_parse_user_info(self, output=None):

        """
            helper method to parse 'show system user name'
        
            param   : optput = show system user info

            varmour@vArmour#ROOT> show system user           
            ID                               ROLE       VSYS            
            --                               ----       ----            
            varmour                          admin      ROOT            
            varmour_no_cli                   admin      ROOT            
            mine                             operator   ROOT            
            min                              reader     ROOT            
            Total users: 4
             
            return (dict):look at the following output

            {
                'mine': {'ID': 'mine', 'ROLE': 'operator', 'VSYS': 'ROOT'}, 
                'min': {'ID': 'min', 'ROLE': 'reader', 'VSYS': 'ROOT'}, 
                'varmour_no_cli': {'ID': 'varmour_no_cli', 'ROLE': 'admin', 'VSYS': 'ROOT'}, 
                'varmour': {'ID': 'varmour', 'ROLE': 'admin', 'VSYS': 'ROOT'}
            }

            example     : _va_parse_user_info(output)                    
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        parsed = dict()

        for line in va_parse_as_lines(output):
            if not line.startswith('ID') and not line.startswith('-') and \
            'show system user' not in line and not line.startswith('Total users'):
                for key in line.split()[0:1]:
                    parsed[key] = dict()
                    parsed[key]['ID'] = line.split()[0:1]
                    parsed[key]['ROLE'] = line.split()[1:2]
                    parsed[key]['VAYS'] = line.split()[2:]
  
        logger.info(parsed)
        return parsed                  
  
    def va_get_system_user_info(self):

        """
           get the system user info 
           
           param    : None
           return: dict: dict of parsed information
           {
                'mine': {'ID': 'mine', 'ROLE': 'operator', 'VSYS': 'ROOT'}, 
                'min': {'ID': 'min', 'ROLE': 'reader', 'VSYS': 'ROOT'}, 
                'varmour_no_cli': {'ID': 'varmour_no_cli', 'ROLE': 'admin', 'VSYS': 'ROOT'}, 
                'varmour': {'ID': 'varmour', 'ROLE': 'admin', 'VSYS': 'ROOT'}
           }
         
            example    : dir_1.va_get_show_system_user_info(**kwargs)
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
           
        cmd = "show system user"            
        output = self._access.va_cli(cmd)

        return self._va_parse_user_info(output)

    def va_get_user_role(self, *args, **kwargs):

        """
           get the user role
           param      : kwargs : dict
                       kwargs = {
                                 'name'    : 'account user name'            
                       }
           return: tuple 
               True,user role
               False,error message

            Example    : va_get_user_role(**kwargs)
                       kwargs = {
                        'name'    : 'varmour_no_cli'                          
                       }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if not 'name' in kwargs:
            raise ValueError("name is mandatory parameter!\n")

        name = kwargs.get('name')
        info = self.va_get_system_user_info()

        if self.va_check_user(**kwargs) is not False :      
            if info is not None:
                userrole = info[name]['ROLE']
                logger.info('user {} role is  {}'.format(name,userrole))
                return True,userrole
            else :
                error = "user info is None,or user {} is not exist"
                logger.error(error)
                return False,error
        else:
            error = "User {} is not exist,get user role is fail".format(name)
            logger.error(error)
            return False,error

    def va_delete_user(self, *args, **kwargs):

        """
            delete system user
            param      : kwargs : dict
                       kwargs = {
                                 'name'    : 'account user name'
                                 'is_commit': True|False,  Optional parameters
                       }
            return: Tuple             
                True, cmd
                False,error log

             Example    : va_delete_user(**kwargs)
                        kwargs = {
                         'name'    : 'varmour_no_cli'
                         'is_commit': True
                        }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if not 'name' in kwargs:
            raise ValueError("name is mandatory parameter!\n")

        if not 'is_commit' in kwargs:
            is_commit = True
        else:
            is_commit = kwargs.get('is_commit')

        name = kwargs.get('name')
        cmd = 'unset system user {}'.format(name)

        if self.va_check_user(**kwargs) is not False :
            self._access.va_config(cmd,commit=is_commit)
            logger.info("Successful to delete user {}".format(name)) 
            return True,cmd   
        else:
            error = "User {} is not exist,delete user is fail".format(name)
            logger.error(error)
            return False,error

    def va_check_user_role(self, *args, **kwargs):

        """
            check user role is right
            param      : kwargs : dict
                       kwargs = {
                                 'name'    : 'account user name'
                                 'role'    : 'expect account user role' 
                       }
            return: boolean
                True
                False

             Example    : va_check_user_management_role(**kwargs)
                        kwargs = {
                         'name'    : 'varmour_no_cli
                         'role'    : 'admin'
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if not 'name' in kwargs:
            raise ValueError("name is mandatory parameter!\n")

        if not 'role' in kwargs:
            raise ValueError("role is mandatory parameter!\n")

        name = kwargs.get('name')
        expect_role = kwargs.get('role')
        boolean,real_role = self.va_get_user_role(**kwargs)
        
        if expect_role in real_role:
            logger.info("Verify role success")
            return True
        else :
            logger.error("Verify role fail,the real role is {},expect role is {}".format(real_role,expect_role))
            return False
    
