"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Address abstracts address and address-group related features.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import copy
import sys
import re
from feature.common import VaFeature
from feature import logger  # NOQA
from vautils.dataparser.string import va_parse_as_lines


class VaAddress(VaFeature):
    """
    Address implements methods to configure or view the address related
    features.
    """
    def va_unset_address(self, name=None):
        """
        method to unset an ipv4 address

        Kwargs:
            :name (str): name of the address configuration

        Returns:
            :bool - True on success and False on failure
        """
        if not name:
            raise ValueError

        cmd = "unset address {}".format(name)
        self._access.va_config(cmd, True)

    def va_unset_address_group(self, name=None, member_list=None):
        """
        method to configure a hostname address for a security policy.

        Kwargs:
            :name (str): address group name
            :member_list (list): list of member addresses configured

        Returns:
            :bool - True on success and False on failure

        Raises:
            :ValueError: if name or member are not provided
        """
        return self._do_op('unset', name, member_list)

    def _do_op(self, op=None, name=None, member_list=None):
        """
        helper method to carry out set or unset operation on address
        group.

        Kwargs:
            :op (str): set or unset operation
        """
        if not name:
            raise ValueError

        if member_list:
            for member in member_list:
                cmd = "{} address-group {} member {}"\
                      .format(op, name, member)
                self._access.va_config(cmd)
        else:
            cmd = "{} address-group {}".format(op, name)
            self._access.va_config(cmd)

        return self._access.va_commit()

    def va_show_address(self, name=None):
        """
        method to get address information - output of 'show address'

        kwargs:
            :name - (str): name of the address

        returns:
            :list: list of namedtuple please see the parser method for more
                   info
        """
        cmd = "show address"
        output = self._access.va_cli(cmd)

        return self._va_parse_address(output)

    def va_show_address_group(self):
        """
        method to get address information - output of 'show address-group'
    
        Params : None        

        returns:
            :list: list of namedtuple please see the parser method for more
                   info
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = "show address-group"
        output = self._access.va_cli(cmd)

        return self._va_parse_address_group(output)

    def _va_parse_address(self, output=None):
        """
        helper method to parse 'show address'

        kwargs:
            :output (str): unicode str output of the cli command

        returns (list): sample output below
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        parsed = list()

        for line in va_parse_as_lines(output):
            line = line.lstrip()
            if not line.startswith('Name'):
                parsed.append(line.split())

        return parsed

    def _va_parse_address_group(self, output=None):
        """
        helper method to parse 'show address-group'

        kwargs:
            :output (str): unicode str output of the cli command

        returns (list): sample output below
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        parsed = list()

        for line in va_parse_as_lines(output):
            line = line.lstrip()
            if not line.startswith('ID') and re.search(r'\w+\@\w+\#\w+',line) is None:
                parsed.append(line.split())

        return parsed

    def va_config_address(self, dataDict, *args, **kwargs):
        """"
        API to config address

        param     : data: dict
            data = {
                 name      : address name 
                 type      : mac-address|ipv4|hostname|segment-id
                 address  : the value of ipv4|mac|hostname|segment-id
                 is_commit : commit, ON/OFF
            }
    
        example  :
            data = {
                 'name'     : 'addr1',
                 'type'     : 'ipv4',
                 'address'  : '1.1.1.1/24',
                 'is_commit' : 'ON',
            }
            va_config_address(data)
        return: True/False
        """

        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   
        data = copy.deepcopy(dataDict) 

        set_cmd = ""
        cmds = []
        cmdprefix = 'set address'
        retcmds = []
    
        if (not 'name' in data) or (not 'type' in data) or (not 'address' in data):
            raise ValueError(" Please input parameter 'name', 'type' and 'address'\n") 
           
        name = data['name'].strip()
        type = data['type'].strip()
        address = data['address'].strip()

        # handle dynamic address
        set_cmd = '%s %s %s %s' % (cmdprefix, name, type, address)
        if 'life_time' in data and 'idle_time' in data:
            life_time = data['life_time']
            idle_time = data['idle_time']
            set_cmd += " type dynamic life-time %s idle-time %s" % (life_time, idle_time)
        elif 'life_time' in data :
            life_time = data['life_time']
            set_cmd += " type dynamic life-time %s" % (life_time)
        elif 'idle_time' in data :
            idle_time = data['idle_time']
            set_cmd += " type dynamic idle-time %s" % (idle_time)
        cmds.append(set_cmd)
        retcmds = copy.deepcopy(cmds)
        self._access.va_config(cmds)
        
        if not 'is_commit' in data :
            is_commit = 'ON'
        else :
            is_commit = data['is_commit']
            
        if is_commit.upper() == "ON" :
            if self._access.va_commit() is False:
                return False
        return True

    def va_config_address_group (self, dataDict, *args, **kwargs):
        """
            Config adddress group
            param     : data: dict
                data = {
                    name     : address group name 
                    member     : [], Any | address name
                    is_commit : commit, ON/OFF
                }
     
            example  :
                data = {
                    'name'       : 'addr-group',
                    'member'   : [],
                    'is_commit': 'ON',
                }
                va_config_address_group(data)
            return: True/False
       """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   
        data = copy.deepcopy(dataDict)

        cmds = []
        cmdprefix = 'set address-group'
        retcmds = []
        
        if not 'name' in data:
            raise ValueError(" Please input parameter 'name'\n") 
           
        name = data['name'].strip()

        if 'member' in data:
            member = data['member']
            if not isinstance(member, list):
                member_list = [member]
            else:
                member_list = member
            for member in member_list:
                cmds.append('%s %s member %s' % (cmdprefix, name, member))
        else:
            cmds.append('%s %s' % (cmdprefix, name))
        retcmds = copy.deepcopy(cmds)
        
        if not 'is_commit' in data :
            is_commit = 'ON'
        else :
            is_commit = data['is_commit']
  
        self._access.va_config(cmds)
        
        if is_commit.upper() == "ON" :
            if self._access.va_commit() is False:
                return False
        return True 

    def va_show_flow_address_group(self,name):
        """
        API for show address-group member list,and return the member list
        
        Param : name : address-group name

        Return : Tuple
            True,list
            False,err_msg

        Returns the result as follows:
            True,['saddr', 'daddr']
            False,'Fail to show address group member,address group test_group is not exist'

        Example : dir_1.va_show_flow_address_group()
                  dir_1.va_show_flow_address_group(name = 'test_group')
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = 'show address-group {}'.format(name)
        output = self._access.va_cli(cmd)
        if re.search('cannot find address group',output) != None:
            error = 'Fail to show address group member,address group {} is not exist'.format(name)
            logger.error(error)
            return False,error
        else:
            result = self._va_parse_address_group_member(output)
            if len(result)<1 :
                logger.info("address-group {} don't have any memeber".format(name))
                return True,result
            else:
                return True,result

    def _va_parse_address_group_member(self,output):
        """
        Helper method to parse address-group member list

        Params: output : unicode str output of the cli command
        
        Return : list : list of parsed information
            ['saddr', 'daddr']
                                    
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        parsed = list()

        for line in va_parse_as_lines(output):
            line = line.lstrip()
            if not line.startswith('Address Group') and re.search(r'\w+\@\w+\#\w+',line) is None:
                parsed.append(line)
        
        return parsed
