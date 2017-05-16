"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

vswitch of esxi implements feature configuration utility functions.

.. moduleauthor:: autotest@sigma-rt.com
"""

import re
from vautils import logger


class EsxVswitch(object):
    """
    EsxVswitch implements methods to configure vswitch features
    """ 
    def __init__(self, name=None, shell=None):
        """
        initialize the vswitch object.

        Kwargs:
            :name (str): unique name of the vswitch
            :shell (obj): LinuxShell object type
        """
        self._name = name
        self._shell = shell
        self.list_vswitch_cmd = "esxcfg-vswitch -l"

    def get_name(self):
        """
        get the name of the vswitch
        """
        return self._name

    def set_vlan(self, pg_name, vlan_id):
        """
        Update portgroup to the value

        Kwargs:
            :pg_name (str): valid portgroup name of the vSwitch
            :vlan_id (str): valid vlan id of the vSwitch
        Returns:
            0: failed
            1: succeed 
        """
        switch_name = self._name
        #self.log_command(self.list_vswitch_cmd)
        results = self._shell.exec_command(self.list_vswitch_cmd)
        result = results[0]
        logger.debug(result)
        buffer = re.sub("\r\n", "\n", result)
        linelist = re.split("\n", buffer)
        for line in linelist:
            learned_mac = re.findall('\s+'+str(pg_name) +\
                '\s+[\d]+\s+[\d]+\s+[^\s]'+'|\s+'+str(pg_name)+\
                '\s+[\d]+\s+[\d]+',line)
            if(len(learned_mac) > 0):
                int_info = learned_mac[0].split(" ")
                for val in int_info :
                    if val != "" :
                        int_name = val
                        break
                cmd = "esxcfg-vswitch -p {} -v {} {}".format(pg_name, \
                    vlan_id, switch_name)
                self.log_command(cmd)
                self._shell.exec_command(cmd)

                if self.check_vlan(pg_name=pg_name, vlan_id=vlan_id):
                    logger.info("Succeed to set portgroup () to vlan {}" . format(pg_name,vlan_id))
                    return True
        logger.error("Failed to set portgroup () to vlan {}" . format(pg_name,vlan_id))
        return False

    def clean_vlan(self, pg_name, vlan = 0):
        """
        Update porgroup to default value. for example.
        if the portgroup name is vlan-20. it will update hte portgroup to vlan 20

        Kwargs:
            :pg_name (str): valid portgroup name of the vSwitch
            :vlan_id (str): valid vlan id of the vSwitch
        Returns:
            0: failed
            1: succeed
        """
        switch_name = self._name
        #self.log_command(self.list_vswitch_cmd)
        results = self._shell.exec_command(self.list_vswitch_cmd)
        result = results[0]
        logger.debug(result)
        buffer = re.sub("\r\n", "\n", result)
        linelist = re.split("\n", buffer)
        for line in linelist:
            learned_mac = re.findall('\s+'+str(pg_name) +\
               '\s+[\d]+\s+[\d]+\s+[^\s]'+'|\s+'+str(pg_name)+\
               '\s+[\d]+\s+[\d]+', line)
            if(len(learned_mac) > 0):
                int_info = learned_mac[0].split(" ")
                for val in int_info :
                    if val != "" :
                        int_name = val
                        vlanid = int_name.split("-")
                        vlan = vlanid[1]
                        break
                cmd = "esxcfg-vswitch -p {} -v {} {}".format(int_name, \
                    vlan, switch_name)
                self.log_command(cmd)
                self._shell.exec_command(cmd)
                logger.info("Succeed to clean vlan")
                return True
        logger.error("Failed to clean vlan")
        return False

    def set_trunk(self, pg_name):
        """
        Update portgroup to value 4095

        Kwargs:
            :pg_name (str): valid portgroup name of the vSwitch
            :vlan_id (str): valid vlan id of the vSwitch
        Returns:
            0: failed
            1: succeed
        """
        return(self.set_vlan(pg_name,4095))

    def clean_trunk(self, pg_name, vlan=0):
        """
        Update porgroup to default value. for example.
        if the portgroup name is vlan-20. it will update hte portgroup to vlan 20

        Kwargs:
            :pg_name (str): valid portgroup name of the vSwitch
            :vlan_id (str): valid vlan id of the vSwitch
        Returns:
            0: failed
            1: succeed
        """
        return(self.clean_vlan(pg_name,vlan=0))

    def set_name(self, switch_name):
        """
        Implementation of set_name of the esxswitch.

        Kwargs:
            :name (str): valid name of the vSwitch
        Returns:
            1: succeed 
        """
        self._name = switch_name
        logger.info("Succeed to set vswitch name")
        return True
    
    def get_sw_name(self):
        """
        Get all switch's information

        Kwargs: none
        Returns:
            a list of vswitch name
        """
        #self.log_command(self.list_vswitch_cmd)
        results = self._shell.exec_command(self.list_vswitch_cmd)
        result = results[0]
        logger.debug(result)
        buffer = re.sub("\r\n", "\n", result)
        linelist = re.split("\n", buffer)
        i = 0
        switch_name = []
        for line in linelist:
            pattern = re.compile(r'Switch Name\s+Num Ports\s+Used Ports\s+Configured Ports\s+MTU\s+Uplinks')
            info = pattern.search(line)
            i = i + 1
            if info:
                nextline = linelist[i]
                swinfo = re.match(r'(\w+)\s+',nextline)
                if swinfo is not None:
                    name = swinfo.group(1)
                    switch_name.append(name)
        if len(switch_name) == 0:
            logger.error("Failed to get vswitch name")
            return False
        logger.info("Succeed to get vswitch name")
        return(switch_name)
    
    def get_vlan(self, pg_name):
        """
        Get the value of vlan of the portgroup

        Kwargs:
            :pg_name (str): valid portgroup name of the vSwitch
        Returns:
            0: failed
            1: succeed 
        """
        vlan_id = 0
        switch_name = self._name
        #self.log_command(self.list_vswitch_cmd)
        results = self._shell.exec_command(self.list_vswitch_cmd)
        result = results[0]
        buffer = re.sub("\r\n", "\n", result)
        linelist = re.split("\n", buffer)
        for line in linelist:
            matchinfo = re.match(r'\s+([^\s]+)\s+([^\s]+)',line)
            if matchinfo :
                portgroup_name = matchinfo.group(1)
                if (portgroup_name == pg_name) :
                    vlan_id = int(matchinfo.group(2))
                    break
        if vlan_id == 0:
            pass
        logger.info("Succeed to get vlan. vlan id is {}".format(vlan_id))
        return(vlan_id)
    
    def update_vlan(self, pg_name, vlan_id):
        """
        Implementation of upate_porgroup to the define value

        Kwargs:
            :pg_name (str): valid portgroup name of the vSwitch
            :vlan_id (str): valid vlan id of the vSwitch

        Returns:
            0: failed
            1: succeed 
        """
        switch_name = self._name
        #self.log_command(self.list_vswitch_cmd)
        results = self._shell.exec_command(self.list_vswitch_cmd)
        result = results[0]
        reg = r'switch\s+name\s+num\s+ports\s+used\s+ports\s+configured\s+\
            ports\s+mtu\s+uplinks'
        for idx in range (0,len(result.split('\n'))) :
            if re.search(reg,result.split('\n')[idx].strip(),re.I) is not None :
                break
            elif idx == len(result.split('\n'))-1 :
                #self.log_command(self.list_vswitch_cmd)
                results = self._shell.exec_command(self.list_vswitch_cmd)
                result = results[0]
                break
        chk_info = re.findall(switch_name,result)
        if (len(chk_info) == 0) :
            return False

        buffer = re.sub("\r\n", "\n", result)
        linelist = re.split("\n", buffer)
        for line in linelist:
            learned_mac = re.findall('\s+'+str(pg_name) +\
               '\s+[\d]+\s+[\d]+\s+[^\s]'+'|\s+'+str(pg_name)+\
               '\s+[\d]+\s+[\d]+', line)
            if(len(learned_mac) > 0):
                int_info = learned_mac[0].split(" ")
                for val in int_info :
                    if val != "" :
                        int_name = val
                        break
                cmd = "esxcfg-vswitch -p {} -v {} {}".format(int_name, \
                    vlan_id, switch_name)
                self.log_command(cmd)
                self._shell.exec_command(cmd)
                if self.check_vlan(pg_name=pg_name, vlan_id=vlan_id):
                    logger.info("Succeed to update portgroup {} to vlan {}".format(pg_name,vlan_id))
                    return True
        logger.error("Failed to update portgroup {} to vlan {}".format(pg_name,vlan_id))
        return False

    def check_vlan(self, pg_name, vlan_id):
        """
        Check vlan if it is same as expect value

        Kwargs:
            :pg_name (str): valid portgroup name of the vSwitch
            :vlan_id (str): valid vlan id of the vSwitch

        Returns:
            0: failed
            1: succeed
        """
        get_vlan_id = self.get_vlan(pg_name=pg_name)
        if get_vlan_id == int(vlan_id):
            return True

        logger.error("Expected vlan id: {}, actual vlan id: {}".format(\
            vlan_id, get_vlan_id))
        return False

    def show_sw(self):
        """
        Show switch's information

        Kwargs:
            :command (str): cli command executed

        Returns: switch's information
        """

        result = ''
        self.log_command(self.list_vswitch_cmd)
        results = self._shell.exec_command(self.list_vswitch_cmd)
        result = results[0]
        logger.info("\n{}".format(result))
        return result

    def log_command(self, command=None):
        """
        Log the command and the device which executes the
        command
        
        Kwargs:
            :command (str): cli command executed
        """
        role = self.get_name()
        logger.debug("[{}]: {}".format(role, command))

    def __del__(self):
        """
        Breaking the references to cli and resource objects.
        """
        self._shell = None
        self._resource = None
