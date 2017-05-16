"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

System abstracts system related features. A superset of features apply
to the product 'dir', while a subset of features apply to other products
- cp, ep, epi. It inherits from class VaSystem, where all the common
features are implemented.

.. moduleauthor:: ppenumarthy@varmour.com, mzhao@varmour.com
"""

import sys
import re
import time
import copy
from collections import namedtuple

from feature import Controller
from feature.common import VaFeature
from feature import logger
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines


class VaSystem(VaFeature):
    """
    System implements methods to configure or view the system related
    features.
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
        super(VaSystem, self).__init__(resource)
        self._parent = None
        
        other_features = ['network', 'epi', 'system-common']
        self.controller = Controller(resource, other_features)

        common = '_'.join(('', 'system-common'))
        if common in self.controller.__dict__.keys():
            self._parent = self.controller.__dict__.get(common)

    def va_disable_paging(self):
        """
        method to set the terminal page length to 0. This will cause the
        entire output to be read once - instead of one page at a time.
        """
        self._access.va_disable_paging()
        result = self._access.va_cli('show cli page')

        parsed = va_parse_basic(result)
        if int(parsed.get('Terminal length')) == 0:
            logger.info("successfully disabled paging!")
            return True

    def va_show_chassis(self):
        """
        method to get chassis information.
        """
        cmd = "show chassis"
        output = self._access.va_cli(cmd)

        return self._va_parse_chassis(output)

    def va_show_running_config(self):
        """
        method to get running configuration on the varmour vm.
        """
        cmd = "show running-config"
        output = self._access.va_cli(cmd)

        return va_parse_as_lines(output)

    def va_show_config_status(self):
        """
        method to get configuration status.

        returns:
            :list: list of namedtuple please see the parser method for more
                   info
        """
        cmd = "show config status"
        output = self._access.va_cli(cmd)
    
        return self._va_parse_config_status(output)

    def _va_parse_chassis(self, output=None):
        """
        helper method to parse 'show chassis'

        returns (dict):

        {
            "virtual chassis setup":{
                "virtual-mac":"disabled",
                "session distribution method":"ingress-first",
                "image-operation delay":"60 seconds",
                "fabric default gateway":"0.0.0.0",
                "control fabric ip":"100.0.92.81/24",
                "management default gateway":"10.150.0.1",
                "control fabric interface":"xe-1/0/0",
                "datapath id":"00:00:00:50:56:81:c4:33",
                "management ip":"10.150.92.81",
                "configuration version":"0x33",
                "virtual-mac identifier":"127",
                "chassis identifier":"vArmour",
                "control protocol/port":"tcp/6634"
            },
            "EPI controller recovery":{
                "commit time":"10 minutes",
                "status":"enabled"
            },
            "openflow controller":{
                "controller ip":"0.0.0.0",
                "connected since":"not connected",
                "controller protocol/port":"NA/0"
            },
            "interfaces registered":{
                "logical":"19",
                "physical":"16"
            },
            "devices status":{
                "total devices connected":"5 (0 ASG devices, 5 vm instances)",
                "last device joined":"device 2 @ Thu Jul 28 09:10:42 2016",
                "total inactive EPIs ":"0",
                "inactive devices":"2 (device id: 4,5)",
                "total EPIs connected":"2"
            }
        }
        """
        parsed = dict()

        outer_key = None
        for line in va_parse_as_lines(output):
            if ':' not in line and not line.startswith('-'):
                if line.strip():
                    outer_key = line
                    parsed[outer_key] = dict()
            else:
                if not line.startswith('-'):
                    inner_key, value = line.split(':', 1)
                    parsed[outer_key][inner_key] = value.strip()

        return parsed

    def _va_parse_config_status(self, output=None):
        """
        helper method to parse config status

        [
            [
                "1",
                "10.150.92.101/16",
                "DIR",
                "0x1c",
                "2016-07-30_20:56:27_UTC",
                "InSync"
            ]
        ]
        """
        parsed = list()
        Config = namedtuple('Config', ['dev', 'mgmt_ip', 'mode', 'version',
                                       'commit_timestamp', 'status'])

        for line in va_parse_as_lines(output):
            line = line.lstrip()
            if not line.startswith('DEV')\
                    and not line.startswith('-')\
                    and not line.startswith('Director'):
                values = line.split()
                try:
                    parsed.append(Config(*values))
                except TypeError:
                   pass

        return parsed

    def va_check_chassis_status(self, *args, **kwargs):
        """
        API to check status of chassis
        param   : kwargs : dict
                : va_check_chassis_status(**kwargs)
            kwargs = {
                    'dev_obj' : device object,
                    'dev_ids' : device id,
            }
        example : va_check_chassis_status(dev_obj=cp_1, dev_ids=2)
                : va_check_chassis_status(dev_obj=[cp_1, cp_2], dev_ids=[2, 3])
        return:
            :bool - True on success or False on failure:
 
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        chassis_info = self.va_show_chassis()
        inactive_info = chassis_info.get('devices status').get(
            'inactive devices')
        pat = re.compile(r'(\d+)\s+')
        match_result = pat.search(inactive_info)
        inactive_count = int(match_result.group(1))

        if 'is_ha' in args:
            total_info = chassis_info.get('devices status').get(
                'total devices connected')
            match_result = pat.search(total_info)
            total_count = int(match_result.group(1))
            active_count = total_count - inactive_count
            if active_count != 1 and int(inactive_count) != 0:
                logger.error('Found inactive device: {}'.format(inactive_count))
                return False
        else:
            if inactive_count != 0:
                logger.error('Found inactive device: {}'.format(inactive_count))
                return False
            if not self.controller.va_check_chassis_epi_status():
                return False

        if 'dev_obj' in kwargs and 'dev_ids' in kwargs:
            if not self.controller.va_check_interfaces_order(**kwargs):
               return False

        logger.info('All devices are connected')
        return True

    def va_check_configured_cmds(self, *args, **kwargs):
        """
        API to check if commands are configured 
        param   : kwargs : dict
        example : va_check_configured_cmds(**kwargs)
            kwargs = {
                    'cmdList' : a list of checking commands,
                    'type'    : 'regexp',
            }
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'cmdList' in kwargs :
            cmdList = kwargs.get('cmdList')
        else:
            raise ValueError("cmdList is mandatory parameter!\n") 
        logger.info("Check CMD: {}".format(cmdList))

        if not 'type' in kwargs :
            type = 'regexp'
        else :
            type = kwargs.get('type')
        
        infoList = self.va_show_running_config()

        for cmd in ['exit', 'configure', 'commit', '']:
            if cmdList.count(cmd) > 0:
                cmdList.remove(cmd)
            if infoList.count(cmd) > 0:
                infoList.remove(cmd)
        
        results = True
        for get_setted_cmd in cmdList:
            get_setted_cmd = get_setted_cmd.strip()
            get_setted_cmd = re.sub(r'^unset ', 'set ', get_setted_cmd)
            for get_cmd in infoList:
                if re.search(r'^set', get_cmd) is not None:
                    if (type == 'regexp') :
                        intf_pat = "(set interface .* unit)"
                        unit_pat = "(\d+)-(\d+)"
                        if re.search(r"{}\s+(.*)".format(intf_pat), get_setted_cmd):
                            interface_pre = re.search(r"{}".format(intf_pat),\
                                            get_setted_cmd).group(0)
                            interface_unit = re.search(r"{}\s+(.*)".format(intf_pat),\
                                             get_setted_cmd).group(1)
                            if re.search(interface_pre,get_cmd) :
                                pat = re.compile(r"{}".format(unit_pat))
                                interface_unit_active = re.search(r"unit\s+(.*)", 
                                    get_cmd).group(1)
                                interface_unit_list = interface_unit_active.split(',')
                                src_unit = interface_unit.split(',')
                                dst_unit = interface_unit_active.split(',')
                                src_unit_list = []
                                dst_unit_list = []
                                for unit_id in src_unit :
                                    if pat.search(unit_id):
                                        temp_re = pat.search(unit_id)
                                        start_id = temp_re.group(1)
                                        end_id = temp_re.group(2)
                                        for temp_id in range(int(start_id),int(end_id)+1):
                                            src_unit_list.append(str(temp_id))
                                    else :
                                        src_unit_list.append(str(unit_id))
                                for unit_id in dst_unit :
                                    if pat.search(unit_id):
                                        temp_re = pat.search(unit_id)
                                        start_id = temp_re.group(1)
                                        end_id = temp_re.group(2)
                                        for temp_id in range(int(start_id),int(end_id)+1):
                                            dst_unit_list.append(str(temp_id))
                                    else :
                                        dst_unit_list.append(str(unit_id))
                                union_list = set(src_unit_list + dst_unit_list)
                                if len(union_list) == len(dst_unit_list):
                                    result = True
                                    break
                                else :
                                    result = False
                                    break
                            else :
                                result = False
                            continue
                        if re.search(get_setted_cmd, get_cmd, re.I) is not None:
                            result = True
                            break
                        else:
                            result = False
                    else :
                        if (get_cmd == get_setted_cmd):
                            result = True
                            break
                        else:
                            result = False
            results = results & result
            if result:
                infoList.remove(get_cmd)
                logger.info("Matched: {}".format(get_setted_cmd))
            else:
                logger.error("Not matched: {}, {}".format(get_setted_cmd, 
                    get_cmd))

        if not results:
            logger.error('Some commands are not in running configurations')
            return False

        logger.info('Succeed to check all configured commands')
        return True

    def va_check_config_status(self):

        """
        API to check status of configuration.
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        status_info = self.va_show_config_status()
        for info in status_info:
            if info.status == 'mismatch':
                logger.error('Found "mismatch" in status of configuration: \
{}'.format(status_info))
                return False

        logger.info('Succeed to check status of configuration')
        return True

    def va_check_system_timestamp(self, *args, **kwargs):

        """
        API to check timestamp of system.
        param   : kwargs : dict
        example : va_check_system_timestamp(**kwargs)
            kwargs = {
                    'epi_obj' : a object of EPI,
            }
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        if 'epi_obj' in kwargs:
            epi_obj = kwargs.get('epi_obj')
            epi_mgt_ip = epi_obj._resource.get_mgmt_ip()
            if 'epi_mgt_ip' not in dir():
                logger.error('Failed to get mangement ip of EPI')
                return False

            epi_mgt_ip = {'mgt_ip' : epi_mgt_ip}
            epi_uuid = self.controller.va_get_epi_uuid(**epi_mgt_ip)
        else:
            epi_uuid = self.controller.va_get_epi_uuid()

        if 'epi_uuid' not in dir() or epi_uuid is None:
            return False

        system_info = self.va_show_system()
        global_timestamp = system_info.get('global commit timestamp')
        for uuid in epi_uuid:
            epi_info = self.controller.va_show_chassis_epi(uuid)
            epi_timestamp = epi_info.get('Commit timestamp')
            if global_timestamp != epi_timestamp:
                logger.error('The timestamp {} is different from EPi {}'.format(
                    global_timestamp, epi_timestamp))
                return False

        logger.info('Succeed to check timestatmp')
        return True

    def va_show_session(self, *args, **kwargs):
        """
        API to get session.
        param   : kwargs : dict
        example : va_show_session(**kwargs)
            kwargs = {
                    'dst_ip'    : '2.2.2.2',
                    'app_id'    : 'icmp',
                    'interface' : 'xe-2/0/0.1',
                    'policy'    : '1', Policy Index,
                    'epi'       : '2-7', UUID | hostname
            }
        return: session or None
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'dst_ip' in kwargs:
            filter = 'match dst-ip {}'.format(kwargs.get('dst_ip'))
        elif 'app_id' in kwargs:
            filter = 'match app-id {}'.format(kwargs.get('app_id'))
        elif 'interface' in kwargs:
            filter = 'match interface {}'.format(kwargs.get('interface'))
        elif 'policy' in kwargs:
            filter = 'match policy {}'.format(kwargs('policy'))
        elif 'epi' in kwargs:
            filter = 'match epi {}'.format(kwargs('epi'))
        else:
            filter = ""

        cmd = "show session {}".format(filter)
        session = self._access.va_cli(cmd)
        if 'session' not in dir():
            logger.error("Failed to get session")
            return None

        return session

    def va_show_counters (self, *args, **kwargs) :
        """
        API to show counters.
        param   : kwargs : dict
        example : va_show_counters(**kwargs)
            kwargs = {
                    'epi'     : uuid|hostname,
                    'counter' : a string of counter name,
            }
        return: 
            :string - counter info or None
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = 'show counters'
        if 'epi' in kwargs:
            epi = kwargs.get('epi')
            cmd += ' epi {}'.format(epi)

        if 'counter' in kwargs:
            counter = kwargs.get('counter')
            cmd += ' |grep {}'.format(counter)

        counter_info = self._access.va_cli(cmd)
        if 'counter_info' not in dir():
            logger.error("Failed to get counters")
            return None

        return counter_info

    def va_check_counters(self, *args, **kwargs):

        """
        API to check counters.
        param   : kwargs : dict
        example : va_show_chassis_epi(**kwargs)
            kwargs = {
                    'epi'     : uuid|hostname,
                    'counter' : a string of counter name,
                    'counter_value' : a value of counter,
            }
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'epi' not in kwargs:
            raise ValueError("epi is mandatory parameter!\n") 
        epi = kwargs.get('epi')
        
        if 'counter' in kwargs:
            counter = kwargs.get('counter')
        else:
            counter = 'Turbo from'

        if 'counter_value' in kwargs:
            counter_value = int(kwargs.get('counter_value'))
        else:
            counter_value = 0

        data = {"epi" : epi, "counter" : counter}
        counter_info = self.va_show_counters(**data)
        if 'counter_info' not in dir():
            logger.error('Failed to get counters')
            return False

        pat = re.compile(r'{}:\s+(\d+)'.format(counter))
        match_result = pat.search(counter_info)
        if match_result is None:
            logger.error('Failed to get info related to "{}" counter'.format(
                counter))
            return False

        got_counter_value = int(match_result.group(1))
        if counter_value != got_counter_value:
            logger.error('Expected value: {}, actual value: {}'.format(
                counter_value, got_counter_value))
            return False

        logger.info('Succeed to check counters')
        return True

    def va_is_3_0(self, *args, **kwargs):
        """
        API to check if version of system is 3.0
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        version_info = self.va_get_version()
        if version_info is None:
            return False
        if re.search(r'^3\.0\.', version_info) is None:
            logger.error('Current version is not 3.0')
            return False

        logger.info('Current version is 3.0')
        return True

    def va_is_3_1(self, *args, **kwargs):
        """
        API to check if version of system is 3.1
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        version_info = self.va_get_version()
        if version_info is None:
            return False
        if re.search(r'^3\.1\.', version_info) is None:
            logger.error('Current version is not 3.1')
            return False

        logger.info('Current version is 3.1')
        return True

    def va_delete_db(self, *args, **kwargs):
        """
        API to delete DB files
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        db_path = '/opt/varmour/db/'
        shell = self._access.va_shell
        shell("rm -f {}chasd_*.db".format(db_path))
        shell("sync")
        time.sleep(0.1)
        db_info = shell("ls -al {} | grep chasd |grep -v chasd_stat -c".format(db_path))
        db_count = int(db_info.split('\n')[-2])
        if db_count != 0:
            logger.error("DB files can't be deleted!")
            return False

        logger.info("DB files are deleted")
        return True
    
    def va_check_home_directory(self,*args,**kwargs):
        """
            Check home directory
            
            Param   : None
            
            Reruen  : boolean
                True
                False
             
            Example    : va_check_home_directory()
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        directory_info = ''
        directory_name = '/usr-varmour/home/varmour'

        try:
            directory_info = self._access.va_shell("sudo ls -ld {}" .format(directory_name))
        except:
            logger.error("Fail to get home directory {}" .format(directory_name))
            return False

        if len(directory_info) == 0:
            logger.error("Invalid direcotry info {}".format(directory_info))
            return False
        
        if re.search(r'drwxr.*{}'.format(directory_name),directory_info,re.I|re.M) is None:
            logger.error("Fail to found home directory {}" .format(directory_name))
            return False
    
        logger.info("Succeed to Found home directory {}".format(directory_name))
        return True

    def va_config_ldap_client(self, *args, **kwargs):
        """
        API to configure ldap client
        param   : kwargs : dict
            'server'    : server address,
            'base_dn'   : ldap server base,
            'account_dn': ldap server root bind dn,
            'password'  : password,
            'encoded_password' : Encrypted passwd,
            'is_commit': True|False, True by default
        return: a tuple of True and cmdList on success, False and err_msg on failure
        example : va_config_ldap_client(**{
            'server' : '10.123.52.250',
            'base_dn' : 'dc=varmour,dc=com',
            'account_dn' : 'cn=admin,dc=varmour,dc=com',
            'encoded_password' : '=$->gAfeIXtI2m4=',
            })
        example : va_config_ldap_client(**{
            'server' : '10.123.52.250',
            'base_dn' : 'dc=varmour,dc=com',
            'account_dn' : 'cn=admin,dc=varmour,dc=com',
            'password' : 'vArmour123',
            })
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = 'set system ldap-client'
        if not 'server' in kwargs or \
            not 'base_dn' in kwargs or \
            not 'account_dn' in kwargs:
            raise ValueError('server, base_dn, and account are mandatory parameters!\n')

        is_encoded = False
        if 'encoded_password' in kwargs:
            is_encoded = True
            password = kwargs.get('encoded_password')
            kw_args = dict()
        elif 'password' in kwargs:
            password = kwargs.get('password')
            kw_args = {'handle_password' : password}
        else:
            raise ValueError('passowrd or encoded_password is mandatory parameters!\n')
        
        is_commit = True
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')

        server  = kwargs.get('server')
        base_dn = kwargs.get('base_dn')
        account_dn = kwargs.get('account_dn')

        cmdList = list()
        cmdList.append('{} server-address {}'.format(cmd, server))
        cmdList.append('{} base-dn {}'.format(cmd, base_dn))
        self._access.va_config(cmdList, commit=False, exit=False)
        if is_encoded:
            cmdList.append('{} account-dn {} password {}'.format(cmd, account_dn, password))
        else:
            cmdList.append('{} account-dn {} password'.format(cmd, account_dn))
        ret_val, err_msg = self._access.va_config(cmdList[-1], commit=is_commit, **kw_args)
        if ret_val is not None:
            return False, err_msg

        logger.info('Succeed to configure ldap client')
        return True, cmdList 

    def va_config_radius(self, *args, **kwargs):
        """
        API to configure radius
        param   : kwargs : dict
            'ip'       : ip address,
            'secret'   : secret,
            'encoded_secret' : Encrypted secret,
            'is_commit': True|False, True by default
        return: a tuple of True and cmdList on success, False and err_msg on failure
        example : va_config_radius(**{
            'ip' : '10.123.52.250',
            'secret' : 'varmour',
            })
        example : va_config_radius(**{
            'ip' : '10.123.52.250',
            'encoded_secret' : '=$->Ba5qYWhzBnQTrG+1tfVRng==',
            })
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = 'set system radius'
        if not 'ip' in kwargs:
            raise ValueError('ip is mandatory parameters!\n')
        ip  = kwargs.get('ip')

        is_encoded = False
        if 'encoded_secret' in kwargs:
            is_encoded = True
            secret = kwargs.get('encoded_secret')
            kw_args = dict()
        elif 'secret' in kwargs:
            secret = kwargs.get('secret')
            kw_args = {'handle_password' : secret}
        else:
            raise ValueError('secret or encoded_secret is mandatory parameters!\n')
        
        is_commit = True
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')

        cmdList = list()
        cmdList.append('{} ip {}'.format(cmd, ip))

        if 'port' in kwargs:
            port = kwargs.get('port')
            cmdList.append('{} port {}'.format(cmd, port))
        if 'timeout' in kwargs:
            timeout = kwargs.get('timeout')
            cmdList.append('{} timeout {}'.format(cmd, timeout))

        self._access.va_config(cmdList, commit=False, exit=False)
        if is_encoded:
            cmdList.append('{} secret {}'.format(cmd,secret))
        else:
            cmdList.append('{} secret'.format(cmd))
        ret_val, err_msg = self._access.va_config(cmdList[-1], commit=is_commit, **kw_args)
        if ret_val is not None:
            return False, err_msg

        logger.info('Succeed to configure radius')
        return True, cmdList 

    def va_config_dns(self, *args, **kwargs):
        """
        API to configure dns
        param   : kwargs : dict
            'primary'  : primary ip address,
            'secondary': secondary ip address,
            'timeout'  : DNS retry timeout,
            'is_commit': True|False, True by default
        return: a tuple of True and cmdList on success, False and err_msg on failure
        example : va_config_dns(**{
            'primary'  : '10.123.52.250',
            'secondary': '10.123.52.222',
            'timeout'  : '40', lager than 30
            })
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'primary' in kwargs and \
            not 'secondary' in kwargs:
            raise ValueError('primary or secondary is mandatory parameter!\n')

        cmdList = list()
        cmd = 'set system service domain-name-service'
        if 'primary' in kwargs:
            primary = kwargs.get('primary')
            cmdList.append('{} primary {}'.format(cmd, primary))
        if 'secondary' in kwargs:
            secondary = kwargs.get('secondary')
            cmdList.append('{} secondary {}'.format(cmd, secondary))
        if 'timeout' in kwargs:
            timeout = kwargs.get('timeout')
            cmdList.append('{}  retry-timeout {}'.format(cmd, timeout))

        is_commit = True
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')

        ret_val, err_msg = self._access.va_config(cmdList, commit=is_commit)
        if ret_val is not None:
            return False, err_msg

        logger.info('Succeed to configure dns')
        return True, cmdList

    def va_get_config_sync_checksum(self, *args, **kwargs):
        """
        API to get checksum of configuration
        return (Dict): 
        {
            '/tmp/varmour_conf_sync.tmp': '0xd338c7a5', 
            '/tmp/va_default_sync.tmp': '0x9387a55b'
        }
        example : va_get_config_sync_checksum()
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        cmd = 'show konfd cli syncable-checksum'
        output = self._access.va_cli(cmd)

        parsed = dict()
        for line in va_parse_as_lines(output):
            line = line.strip()
            if not line.startswith('crc32'):
                try:
                    key, value = line.split(':')
                    parsed[key.strip()] = value.strip()
                except ValueError as e:
                    pass

        return(parsed)

    def _va_save_config(self,choose_type,filename):
        """
        Save current config

        Param :
                choose_type(str)   : 'type of system config 'save'
                filename(str)      : 'save config file name' (Default 'varmour.conf')
        
        Return   : Tuple             
                True, cmd
                False,error log

        
        Example  : self._save_config(choose_type,filename)
                    kwargs = {
                                'choose_type'      : 'save',
                                'filename'         : 'varmour.conf'
                            }        
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        file_name = filename.split(".")[0]
        check_cmd = 'ls -ld /config-varmour/configuration/varmour_conf/ext/{}'
        cmd = "request system config {} {}".format(choose_type,file_name)
        rt = self._access.va_cli(cmd)
        find = self._access.va_shell(check_cmd.format(filename))

        if re.search("{}: No such file or directory".format(filename),find,re.I|re.M) is None:
            logger.info("succeed to request system config: {}".format(choose_type))
            return True,cmd
        else:
            error = "Fail to request system config: {}".format(choose_type)
            logger.error(error)
            return False,error

    def _va_delete_config(self,choose_type,filename):
        """
        Delete the config file

        Param :
                choose_type(str)   : 'type of system config 'delete'
                filename(str)      : 'delete config file name or all' (Default 'varmour.conf') 
        
        Return   : Tuple             
                True, cmd
                False,error log

        
        Example  : self._va_delete_config(choose_type,filename)
                    kwargs = {
                                'choose_type'      : 'delete',
                                'filename'         : 'varmour.conf'
                            }        
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = "request system {} config {}".format(choose_type,filename)
        check_cmd = 'ls -ld /config-varmour/configuration/varmour_conf/ext/{}'
        check_all = 'ls -ld /config-varmour/configuration/varmour_conf/ext/*.conf' 
        rt = self._access.va_cli(cmd)

        if re.search('Can not find file to delete',rt) is None:
            if filename == 'all':
                find = self._access.va_shell(check_all)
            else:
                find = self._access.va_shell(check_cmd.format(filename))
            if re.search("No such file or directory",find,re.I|re.M) is not None:
                logger.info("succeed to request system config: {}".format(choose_type))
                return True,cmd
            else:
                error = "Fail to request system config: {}".format(choose_type)
                logger.error(error)
                return False,error
        else:
            error = "Fail to {} config,{} is not exist".format(choose_type,filename)
            logger.error(error)
            return False,error

    def _va_load_config(self,choose_type,filename,is_reboot):
        """
        Load config

        Param :
                choose_type(str)   : 'type of system config 'load',
                filename(str)      : 'load file name' (Default 'varmour.conf'),
                is_reboot(str)     : 'whether reboot after load config' Y|N 
        
        Return   : Tuple             
                True, cmd
                False,error log

        
        Example  : self._va_load_config(choose_type,filename,is_reboot)
                    kwargs = {
                                'choose_type'      : 'load',
                                'filename'         : 'varmour.conf',
                                'is_reboot'        : 'Y'
                            }        
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        self._access.va_cli()
        cmd = 'request system config {} {} next-reboot'.format(choose_type,filename)
        self._access._cli.exec_command(cmd,prompt=(re.compile\
        ('Any changes to the current configuration will not be retained after reboot'),100))
        rt = self._access._cli.exec_command('Y')

        if re.search('Wrong file name found', str(rt)) is not None:
            error = 'Fail to load config,{} is not exist'.format(filename)
            logger.error(error)
            return False,error
        else:
            if is_reboot == 'Y':
                cmd = 'request system reboot'
                if self._access.va_reboot(cmd,persistent=True, reconnect_delay=120) is True:
                    logger.info("succeed to reboot system")
                    logger.info("succeed to request system config: {}".format(choose_type))
                    return True,cmd
                else:
                    error = "Fail to reboot system after load config"
                    logger.error(error)
                    return False,error
            else:
                logger.info("succeed to request system config: {}".format(choose_type))
                return True,cmd

    def _va_export_config(self,dst_pc,path,choose_type,filename,save_path,passwd):
        """
        Save config file out of the system

        Param :
                choose_type(str)   : 'type of system config 'export',
                dst_pc             : 'destination pc object',
                path(str)          : 'export config path'
                filename(str)      : 'export config file name' (Default 'varmour.conf'),
                save_path(str)     : 'export ip and file path',
                passwd(str)        : 'receiver password'
        
        Return   : Tuple             
                True, cmd
                False,error log
        
        Example  : self._va_export_config(dst_pc,path,choose_type,filename,save_path,passwd)
                    kwargs = {
                                'choose_type'      : 'export',
                                'dst_pc'           : pc1
                                'path'             : '/tmp'
                                'filename'         : 'varmour.conf'
                                'save_path'        : 'varmour@10.11.120.142:/tmp'
                                'passwd'           : 'varmour'
                            }        
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = "request system {} config {} to {}".format(choose_type,filename,save_path)
        rt = self._access.va_cli(cmd,**{'handle_password':passwd})

        if re.search('File copy failed!',str(rt)) is not None :
            error = "Fail to request system config: {}".format(choose_type)
            logger.error(error)
            return False,error
        else:
            self_ip = self._access._resource.get_mgmt_ip()
            find = str(dst_pc.shell(r'ls -ld {}/{}*{}'.format(path,self_ip,filename)))
            if re.search("No such file or directory",find,re.I|re.M) is None:
                logger.info("succeed to request system config: {}".format(choose_type))
                return True,cmd
            else:
                error = "Fail to request system config: {}".format(choose_type)
                logger.error(error)
                return False,error

    def _va_import_config(self,choose_type,filename,save_path,save_filename,passwd):
        """
        Save config file to system

        Param :
                choose_type(str)   : 'type of system config 'import',
                filename(str)      : 'import config file name,
                save_path(str)     : 'import ip and file path',
                save_filename(str) : 'save name for import'
                passwd(str)        : 'sender password'
        
        Return   : Tuple             
                True, cmd
                False,error log
        
        Example  : self._va_export_config(path,choose_type,filename,save_path,save_filename,passwd)
                    kwargs = {
                                'choose_type'      : 'import',
                                'cmd'              : 'request system',
                                'filename'         : 'varmour.conf',
                                'save_path'        : 'varmour@10.11.120.142:/tmp',                            
                                'save_filename'    : 'varmour.conf',
                                'passwd'           : 'varmour'
                            }        
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = 'request system {} config {}/{} {}'.format(choose_type,save_path,filename,save_filename)
        check_cmd = 'ls -ld /config-varmour/configuration/varmour_conf/ext/{}'
        rt = self._access.va_cli(cmd,**{'handle_password':passwd})

        if re.search('File copy failed!',str(rt)) is not None :
            error = "Fail to  request system config: {}".format(choose_type)
            logger.error(error)
            return False,error
        else:
            find = self._access.va_shell(check_cmd.format(save_filename))
            if re.search("No such file or directory",find,re.I|re.M) is None:
                logger.info("succeed to request system config: {}".format(choose_type))
                return True,cmd
            else:
                error = "Fail to request system config: {}".format(choose_type)
                logger.error(error)
                return False,error

    def va_request_system_config(self, *args, **kwargs):
        """
        Save config file in/out of system,the API support following: 
        export,import,delete,save,load

        Param   : kwargs : dict
                 kwargs = {
                            choose_type(str)   : 'type of system config 'export|import|delete|save|load'
                            path(str)          : 'import or export config path' (Default '/tmp')
                            filename(str)      : 'export|import|delete|save|load config file name' (Default 'varmour.conf')
                            save_filename(str) : 'save name for import' (Default 'varmour.conf')
                            dst_pc             : 'destination pc object' (Default pc1)
                            is_reboot(str)     : 'whether reboot after load config' Y|N (Default 'Y')
                        }

        Return   : Tuple             
                True, cmd
                False,error log

        Example  : va_request_system_config(**kwargs)
                    kwargs = {
                                'choose_type'   : 'export',
                                'save_filename' : 'varmour.conf',
                                'dst_pc'        : pc1,
                                'path'          : '/tmp',
                                'filename'      : 'varmour.conf',
                                'is_reboot'        : 'Y'
                            }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        type_list = ['import', 'export', 'load', 'save', 'delete']
        
        if 'choose_type' not in kwargs:
            raise ValueError("choose_type is mandatory parameter!\n")
        
        choose_type = kwargs['choose_type'].strip().lower()
        
        #Loading filename and save_filename        
        if 'filename' not in kwargs:
            filename = 'varmour.conf'
        else:
            filename = kwargs['filename']

        if 'save_filename' not in kwargs:
            save_filename = 'varmour.conf'
        else:
            save_filename = kwargs['save_filename']
        
        #Request save config or delete config
    
        if choose_type == type_list[3]: 
            return self._va_save_config(choose_type,filename)

        elif choose_type == type_list[4] :
            return self._va_delete_config(choose_type,filename)

        #Request load config
        elif choose_type == type_list[2]:
            if 'is_reboot' not in kwargs:
                is_reboot = 'Y'
            else:
                is_reboot = kwargs['is_reboot']

            return self._va_load_config(choose_type,filename,is_reboot)

        #Request export config or import config
        elif choose_type in type_list[0:2]:
            
            if 'dst_pc' not in kwargs:
                dst_pc = pc1
            else:
                dst_pc = kwargs.get('dst_pc')
            
            dst_resource = dst_pc._access._resource
            dst_ip = dst_resource.get_mgmt_ip()
            user = dst_resource.get_user().get('name')
            passwd = dst_resource.get_user().get('password')
            
            if 'path' not in kwargs:
                path = '/tmp'
            else:
                path = kwargs['path']
            
            save_path = "{}@{}:{}".format(user,dst_ip,path)

            if choose_type == type_list[1]:            
                return self._va_export_config(dst_pc,path,choose_type,filename,save_path,passwd)
    
            elif choose_type == type_list[0]:
                return self._va_import_config(choose_type,filename,save_path,save_filename,passwd)

    def va_delete_system_info(self, *args, **kwargs):
        """
        API to delete system info
        Param: kwargs     : dict
               delete_flag(list): Deleted system option (default: all of option)
               image      : Deleted image (default: all)
               license    : Deleted license (default: all)
               device_id  : Deleted device id (default: all)
               device      : Delete device system option
        Return: True/False
        Example: va_delete_system_info(delete_flag='device',device=['log','debug'])
                 va_delete_system_info()
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        cmds = list()
        device = None
        is_negative = kwargs.get('is_negative',False)
        delete_flag = kwargs.get('delete_flag',['config','core','cn-secret','log',\
                                                'image','license','debug','device'])
        if isinstance(delete_flag,str):
            delete_flag = delete_flag.split(',')
        
        pre_cmd = 'request system delete '
        
        for flag in delete_flag:
            if flag == 'device':
                device = True
                continue
            elif flag in ['core','cn-secret','log']:
                cmds.append(pre_cmd + flag)
            elif flag == 'config':
                cmds.append(pre_cmd + 'config all')
            else:
                if flag == 'debug':
                    flag_content = kwargs.get(flag,['file','archive'])
                    if isinstance(flag_content,str):
                        flag_content = flag_content.split(',')
                    for debug_flag in flag_content:
                        cmds.append(pre_cmd + 'debug {}'.format(debug_flag))
                else:
                    flag_content = kwargs.get(flag,'all')
                    cmds.append(pre_cmd + '{} {}'.format(flag,flag_content))
        
        if device:
            dev_id = kwargs.get('device_id','all')
            pre_cmd += 'device {} '.format(dev_id)
            dev_flag = kwargs.get('device')
            if isinstance(dev_flag,str):
                dev_flag = dev_flag.split(',')
            
            for device_flag in dev_flag:
                if device_flag == 'debug':
                    cmds.append(pre_cmd + 'debug file')
                elif device_flag == 'image':
                    img = kwargs.get(device_flag,'all')
                    cmds.append(pre_cmd + 'image {}'.format(img))
                else:
                    cmds.append(pre_cmd + device_flag)
        for cmd in cmds:
            output = self._access.va_cli(cmd)
            if re.search('(unnecessary user import|can not find file to delete|file not found)',\
                          output,re.I|re.M) is not None and not is_negative:
                logger.error('Fail to delete system info\nfailed command:{}'.format(cmd))
                return False
        return True

    def va_reset_config(self,is_reverse = False):
        """
        Unset system configuration according the show running config information

        Param : 'is_reverse'(boolean) : 'Whether to reverse' (True|False,Default False)
        
        Return: tuple
            True,msg
            False,err_msg

        Example    : va_reset_config()
                     va_reset_config(is_reverse = True)
                        
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        unset_cmds = []
        unset_cmds_new = []
    
        self._access.va_config('rollback')
        get_cmds_list = self.va_show_running_config()        
        del get_cmds_list[0:4]
        del get_cmds_list[-1]
        del get_cmds_list[-1]

        if get_cmds_list != None:
            #Reverse to reset configuration
            if is_reverse:
                get_cmds_list.reverse()
            for cmd in get_cmds_list:
                cmd = cmd.strip()

                if  re.search(r'set system user ([\d\w_-]+) password', cmd, re.M|re.I) is not None\
                    or re.search(r'set system inactivity-timeout 250',cmd, re.M|re.I) is not None\
                    or re.search(r'set chassis process.*debug',cmd, re.M|re.I) is not None\
                    or re.search(r'set vsys-profile default',cmd, re.M|re.I) is not None\
                    or re.search(r'set system debug-shell password',cmd, re.M|re.I) is not None\
                    or re.search(r'set system user (varmour|varmour_no_cli) role admin',cmd,re.M|re.I) is not None :

                    continue
                
                #handle service
                info = re.search(r'set service ([\d\w_-]+)',cmd,re.I)               
                if info != None:
                    cmd = info.group(0)    
                    
                #handle orchestration
                info = re.search(r'set orchestration ([\d\w_-]+)',cmd,re.I)                       
                if info != None :
                    cmd = info.group(0)

                #handle system user
                info = re.search(r'set system user ([\d\w_-]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle policy
                info = re.search(r'set policy name ([\d\w_-]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle nat rule/pool
                info = re.search(r'set nat (rule|pool) ([\d\w_-]+)',cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle syslog
                info = re.search(r'set system service syslog (ep-id|epid) ([\d\w_-]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)  
 
                #handle syslog tag/syslog tag group
                info = re.search(r'set system service ((syslog-tag)|(syslog-tag-group)) ([\d\w_-]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle syslog service
                info = re.search(r'set system service syslog-service policy ([\d\w_-]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle interface member
                info = re.search(r'set interface ([\d\w\-\/\.]+) member ([\d\w\-\/\.]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle track ip
                info = re.search(r'set interface ([\d\w\-\/\.]+) track-ip ([\d\/\.]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle multi path
                info = re.search(r'set interface ([\d\w\-\/\.]+) multi-path priority ([\d]+)', cmd,re.I)
                if info != None :
                    int_name = info.group(1)
                    cmd = "set interface {} multi-path".format(int_name)

                #handle dhcp relay
                info = re.search(r'set interface ([\d\w\-\/\.]+) dhcp-relay .*', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle ntp-service
                info = re.search(r'set system service ntp-service ([\d\w\-\/\.]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle routing instance
                info = re.search(r'set routing-instance ([\d\w\-\/\.]+) route static [\d\.\/]+', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle VR
                info = re.search(r'(set vrouter [\d\w\-\/\.]+ route static [\d\.\/]+) next-hop [\d\.\/]+', cmd,re.I)
                info1 = re.search(r'set vrouter [\d\w\-\/\.]+ route static [\d\.\/]+', cmd,re.I)
                if info != None :
                    cmd = info.group(1)
                elif info1 != None :
                    cmd = info1.group(0)
                
                #handle IDS 
                info = re.search(r'set profile stateful-inspection ([\d\w_-]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)
                
                #hanlde custom app
                info = re.search(r'set profile custom-app ([\d\w_-]+)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)
                
                #handle static route
                info = re.search(r'set route static [\d\.\/]+', cmd,re.I)
                if info != None :
                    cmd = info.group(0)
                
                #handle zone
                info = re.search(r'set zone ([\d\w\-\/\.]+) type L2 routing-interface ([\d\w\.\/\-]+)', cmd,re.I)
                info1 = re.search(r'set zone ([\d\w\-\/\.]+) type', cmd,re.I)
                if info != None :
                    cmd = info.group(0)
                elif info1 != None :
                    zone = info1.group(1)
                    cmd = "set zone %s" % zone

                #handle subinterface
                info = re.search(r'set interface ([\w\w\.\/\-]+) unit (\d+)', cmd,re.I)
                if info != None :
                    cmd = "set interface {}.{}".format(info.group(1),info.group(2))

                #handle dhcp service
                info = re.search(r'set system service dhcp-service subnet address [\d\.\/]+', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle address-binding for dhcp server
                info = re.search(r'set system service dhcp-service address-binding \S+', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle AD/RADIUS/LDAP
                info = re.search(r'set system (active-directory|radius|ldap-client)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                info = re.search(r'set system admin-auth (remote|policy)', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle dhcp relay
                info = re.search(r'set profile dhcp-relay ([\d\w\-\/\.]+) server [\d\.]+', cmd,re.I)
                if info != None :
                    cmd = "set profile dhcp-relay %s" % info.group(1)

                #handle snmp
                info = re.search(r'set system snmp', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle address
                info = re.search(r'set address (([\d\w\-\/\.]+))', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle arp
                info = re.search(r'set arp [\d\.]+ [\d\w\:]+\s+', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle mailopt
                info = re.search(r'set system mailopt', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle app-control
                info = re.search(r'set profile app-control (([\d\w\-\/\.]+))', cmd,re.I)
                if info != None :
                    cmd = info.group(0)

                #handle vwire
                info = re.search(r'set vwire-group ([\d\w_-]+) interface-pair (\d+)', cmd,re.I)
                info1 = re.search(r'set vwire-group [\d\w_-]+', cmd,re.I)
                if info != None :
                    cmd = info.group(0)
                elif info1 != None :
                    cmd = info1.group(0)

                #handle image-operation
                info = re.search(r'(set chassis image-operation) delay-interval \d+', cmd,re.I)
                if info != None :
                    cmd = info.group(1)

                #handle operation mode of EPI to match behavior change
                info = re.search(r'set chassis epi\s+.*\s+inline', cmd, re.I)
                if info != None :
                    unset_cmds_new.append('un{}'.format(info.group(0)))
                    continue

                cmd_un='un{}'.format(cmd)

                #handle duplicate commands
                try :
                    unset_cmds.index(cmd_un)
                except :
                    unset_cmds.append(cmd_un)

            err_cmd,err_msg = self._access.va_config(unset_cmds)

            if len(unset_cmds_new) != 0:
                err_cmd,err_msg = self._access.va_config(unset_cmds_new)

            if err_cmd is not None or err_msg is not None:
                logger.error('Failed to {}'.format(err_cmd))
                return False, err_msg
            else:
                info = 'Succeed to unset system configuration'
                logger.info(info)
                return True,info
        else :
            error = "Fail to get running-config info"
            logger.error(error)
            return False,error

