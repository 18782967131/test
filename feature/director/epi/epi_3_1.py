"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Epi abstracts epi related features. A superset of features apply
to the product 'dir', while a subset of features apply to other products
- cp, ep, epi. It inherits from class VaSystem, where all the common
features are implemented.

.. moduleauthor:: ppenumarthy@varmour.com, mzhao@varmour.com
"""
import sys
import re
import time
from collections import namedtuple

from feature.common import VaFeature
from feature import logger
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines
from vautils.resource.delegator import Delegator

class VaEpi(VaFeature):
    """
    Epi implements methods to configure or view the EPI related
    features.
    """
    def va_show_chassis_epi(self, host_id=None):
        """
        method to get chassis epi information.

        kwargs:
            :host_id (str): uuid of the epi or the hostname

        returns:
            :dict: dict of parsed information
        """
        cmd = "show chassis epi"
        parser = self._va_parse_chassis_epi
        if host_id:
            cmd = "show chassis epi {}".format(host_id)
            parser = va_parse_basic

        output = self._access.va_cli(cmd)
        return parser(output)

    def _va_parse_chassis_epi(self, output=None):
        """
        helper method to parse 'show chassis epi uuid' or
        'show chassis epi hostname'

        returns (dict): look at the following output
        {
            "Active EPI":[
               Epi(uuid='420135BF-0069-120D-816E-29A058C829ED',
                   hostname='VA-31-EPi1',ep_id='2-6',mode='tap','fabric_ip'='100.0.92.84/24',
                   management_ip='10.150.92.84/16',connected_since='@Thu-Jul=28-09:13:56-2016',
                   connected_type=TLS'',licensed='yes'),
               Epi(uuid='420135BF-0069-120D-816E-29A058C829ED',
                   hostname='VA-31-EPi1',ep_id='2-7*',mode='tap','fabric_ip'='100.0.92.84/24',
                   management_ip='10.150.92.84/16',connected_since='@Thu-Jul=28-09:13:56-2016',
                   connected_type=TLS'',licensed='yes') 
            ],
            "Inactive EPI":[Epi(uuid='564DDF39-5C53-66E4-4F64-6CB7B2B8BC9B',hostname='-',last_connected_ep='3',mode='tap')]
            "Total inactive EPIs":"1",
            "Total active EPIs":" 1"
        }
        """
        parsed = dict()
        current_key = None
        active_tag = 0
        inactive_tag = 0
        parse_info = va_parse_as_lines(output)
        parse_info.pop(-1)
        for line in parse_info:
            line = line.lstrip()
            if line.startswith('Active'):
               active_tag = 1
               inactive_tag = 0
               current_key = line.rstrip(':')
               parsed[current_key] = list()
            elif line.startswith('Inactive'):
               active_tag = 0
               inactive_tag = 1
               current_key = line.rstrip(':')
               parsed[current_key] = list()
            elif not line.startswith('UUID')\
                    and not line.startswith('-')\
                    and not line.startswith('Total')\
                    and not line.startswith('*:'):
                if active_tag == 1:
                    Epi = namedtuple('Epi', ['uuid', 'hostname', 'ep_id', 'mode',
                                             'fabric_ip', 'management_ip', 'connected_since',
                                             'connected_type', 'licensed'])
                else:
                    Epi = namedtuple('Epi', ['uuid', 'hostname', 'last_connected_ep', 'mode'])
                values = line.split()
                parse_values = list()
                parse_tag = 0
                parse_element = ''
                for list_element in values:
                    if re.search('^@\w+$',list_element,re.I):
                        parse_tag = 1
                    if parse_tag:
                        if re.search('^\d{4}$',list_element):
                            parse_tag = 0
                            parse_element += '%s' % list_element
                            parse_values.append(parse_element)
                        else:
                            if re.search(r'INVALID$',list_element) :
                                parse_element += '%s' % list_element[0:4]
                                parse_values.append(parse_element)
                                parse_values.append('INVALID')
                                parse_tag = 0
                            else :
                                parse_element += '%s-' % list_element
                    else :
                        if re.search('^\*$',list_element):
                            parse_values[-1] += '*'
                        else:
                            parse_values.append(list_element)
                parsed[current_key].append(Epi(*parse_values))
            elif line.startswith('Total'):
                key, value = line.split(':')
                parsed[key] = value
            else:
                continue
        return parsed

    def va_get_epi_uuid (self, *args, **kwargs):

        """
        method to get epi uuid by epi mgt ip
        param      : kwargs : dict
        example    : va_get_epi_uuid(**kwargs)
                   kwargs = {
                    'epi_obj': EPI1
                   }
        return: uuid if given epi_object, a list of uuid if not specify, None
            on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   

        epi_uuid = list() 

        epi_info = self.va_show_chassis_epi()
        active_epi_info = epi_info.get('Active EPI')
        if len(active_epi_info) == 0 :
            logger.error("Not found any Active EPI")
            return None

        #for info in uuid_info:
        for info in active_epi_info:
            if 'epi_obj' in kwargs:
                epi_uuid = ''
                epi_obj = kwargs.get('epi_obj')
                epi_mgt_ip = epi_obj._resource.get_mgmt_ip()
                if epi_mgt_ip in info.management_ip:
                    epi_uuid = info.uuid
                    break
            else:
                epi_uuid.append(info.uuid)

        if len(epi_uuid) == 0:
            logger.error("Failed to get uuid of EPI")
            return None

        logger.info("UUID: {}".format(epi_uuid))
        return epi_uuid

    def va_get_epi_status(self, *args, **kwargs):
        """
        method to get epi status 
        param      : kwargs : dict
        example    : va_get_epi_status(kwargs)
                   kwargs = {
                    'uuid': 'xxx'
                   }
        return: 'active' or 'inactive' or None (if epi not found)
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
   
        if not 'uuid' in kwargs :
            raise ValueError(" uuid is mandatory parameter!\n") 

        uuid = kwargs['uuid']
        epi_info = self.va_show_chassis_epi()
        
        for active_info in epi_info.get('Active EPI'):
            if uuid == active_info.uuid:
                status = 'active'
                logger.info('Status of EPI: {}'.format(status))
                return status
        
        for inactive_info in epi_info.get('Inactive EPI'):
            if uuid == inactive_info.uuid:
                status = 'inactive'
                logger.info('Status of EPI: {}'.format(status))
                return status
        
        logger.error("Not found EPI: {}".format(uuid))
        return None

    def va_get_epi_mode(self, *args, **kwargs):
        """
        method to get epi mode 
        param      : kwargs : dict
        example    : va_get_epi_status(kwargs)
                   kwargs = {
                    'uuid': 'xxx'
                   }
        return: 'tap' or 'inline' or 'standy' or None (if epi not found)
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
   
        if not 'uuid' in kwargs :
            raise ValueError(" uuid is mandatory parameter!\n") 

        uuid = kwargs['uuid']
        active_info = self.va_show_chassis_epi().get('Active EPI')
        
        for info in active_info:
            if info.uuid == uuid:
                logger.info('Mode of EPI: {}'.format(info.mode))
                return info.mode
        
        logger.error('Not found EPI {} in Activate EPI'.format(uuid))
        return None

    def va_config_epi_operation_mode(self, *args, **kwargs):

        """
        method to config epi operation mode 
        param      : kwargs : dict
        example    : va_config_epi_operation_mode(**kwargs)
                   kwargs = {
                    'uuid': '564DB44A-B3F3-5D0B-0C33-77CD43987BFC'
                    'mode': 'inline'|'tap'|'pvlan'
                    'is_commit': True|False, True by default
                   }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   
        
        if not 'mode' in kwargs or \
            not 'uuid' in kwargs:
            raise ValueError(" 'mode' and 'uuid' are mandatory parameters!\n") 
        
        is_commit = True
        uuid = kwargs.get('uuid')
        mode = kwargs.get('mode')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')

        cmd = 'set chassis epi {} operation-mode {}'.format(uuid, mode)
        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            return False, err_msg

        logger.info('Succeed to configure operation mode of EPI')
        return True, cmd 
        
    def va_config_micro_segmentation(self, *args, **kwargs):
        """
        API to config micro segmentation of EPI
        param      : kwargs : dict
                       'uuid'      : uuid of epi,
                       'segment_id': segment id of epi,
                       'micro_vlan': micro-vlan primary value of epi,
                       'pvlan'     : micro-vlan secondary value of epi,
                       'is_commit' : commit commands, True or False, True by default
        example    : va_config_micro_segmentation(**kwargs)
                     kwargs = {
                       'uuid': '564DB44A-B3F3-5D0B-0C33-77CD43987BFC'
                       'segment_id': 3000
                       'micro_vlan': 100
                       'pvlan'     : 200
                      }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   
        
        if not 'uuid' in kwargs or \
            not 'segment_id' in kwargs or \
            not 'micro_vlan' in kwargs:
            raise ValueError(" 'uuid', 'segment_id' and 'micro_vlan' \
are mandatory parameters!\n") 

        is_commit = True
        uuid = kwargs.get('uuid')
        segment_id = kwargs.get('segment_id')
        micro_vlan = kwargs.get('micro_vlan')
        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')

        cmd = 'set micro-segmentation epi {} segment {} micro-vlan {}'.format(
            uuid, segment_id, micro_vlan)
        if 'pvlan' in kwargs:
            pvlan = kwargs.get('pvlan')
            cmd += ' micro-vlan-2nd {}'.format(pvlan)

        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            return False, err_msg

        logger.info('Succeed to configure micro segmentation of EPI')
        return True, cmd 
    
    def va_check_chassis_epi_status(self):

        """
        API to check chassis status of EPI.
        return:
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        chassis_info = self.va_show_chassis_epi()
        inactive_count = int(chassis_info.get('Total inactive EPIs'))
        if inactive_count != 0:
            logger.error('Found inactive EPis: {}'.format(inactive_count))
            return False

        logger.info('All EPis are connected')
        return True

    def va_get_epi_connecting_mode(self, *args, **kwargs):
        """
        API to get connecting mode of EPI.
        param   : kwargs : dict
        example : va_get_epi_connecting_mode(**kwargs)
            kwargs = {
                    'epi_obj' : a object of EPI,
            }
        return: 
            :string - None or connecting mode(primary/backup)
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        epi_mode = None

        if not 'epi_obj' in kwargs :
           raise ValueError("epi_obj is mandatory parameter!\n") 
        epi_obj = kwargs['epi_obj']
        epi_mgt_ip = epi_obj._resource.get_mgmt_ip()
        if 'epi_mgt_ip' not in dir():
            logger.error("Failed to get management ip of EPI")
            return epi_mode

        epi_info = self.va_show_chassis_epi()
        epi_info = epi_info.get('Active EPI')
        if len(epi_info) == 0:
            logger.warning('Active EPI is None')
            return epi_mode
        
        for info in epi_info:
            if epi_mgt_ip in info.management_ip:
                if '*' in info.ep_id:
                    epi_mode = 'backup'
                else:
                    epi_mode = 'primary'
                break

        logger.info("EPI is connecting to its '{}' EP/CP".format(epi_mode))
        return epi_mode

    def va_reconnect_epi(self, *args, **kwargs):
        """
        API to reconnect epi
        param   : kwargs : dict
        example : va_reconnect_epi(**kwargs)
            kwargs = {
                    'epi' : uuid|hostname,
                    'dev_id' : device id,
            }
        return: 
            :bool - True on success or False on failure:
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = 'request system reconnect'
        if 'epi' in kwargs:
            epi = kwargs.get('epi')
            cmd = '{} epi {}'.format(cmd, epi)
            if 'dev_id' in kwargs:
                dev_id = kwargs.get('dev_id')
                cmd = '{} device {}'.format(cmd, dev_id)
            else:
                cmd = '{} primary'.format(cmd)

        output = self._access.va_cli(cmd)
        return True

    def va_get_epi_forwarding_table(self, *args, **kwargs):
        """
        get epi forwarding table according to uuid or hostname of epi
        param   : kwargs : dict
            kwargs = {
                    'epi' : uuid or hostname of the epi. eg: 2-6 or epi6
            }
        return: tuple
            Success: True,
                : {'0:50:56:8e:ed:8': {
                            'EPI-MAC': 'local',
                            'EPI-IP': 'local',
                            'SEG-ID': '3000',
                            'MICRO-VLAN': '2003',
                            'VM-MAC': '0:50:56:8e:ed:8',
                            'FLAG': '110'},
                   'Total remote entries': '0',
                   'Total local entries': '2',
                   '0:c:29:51:77:f8': {
                         'EPI-MAC': 'local',
                         'EPI-IP': 'local',
                         'SEG-ID': '3000',
                         'MICRO-VLAN': '2002',
                         'VM-MAC': '0:c:29:51:77:f8',
                         'FLAG': '110'
                         }
                   }
            Failure: False,{}
        example : va_get_epi_forwarding_table(**kwargs)

        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        return_data = {}
        if not 'epi' in kwargs :
            raise ValueError("uuid of hostname of epi is mandatory parameter!\n")

        cmd = 'show chassis epi {} forwarding'.format(kwargs.get('epi'))
        output = self._access.va_cli(cmd)
        if re.search(r'Fail to find EPI',output, re.M|re.I) is not None :
            logger.error('Failed to find EPI {}'.format(kwargs.get('epi')))
            return False,return_data

        output = output.split('\n')
        output.pop(0)
        last_index = len(output) - 1
        output.pop(int(last_index))
        output.pop(1)

        #address the number of tatal local/remove entries
        for i in range (1,3) :
            total_line = output.pop(-1).split(':')
            return_data[total_line[0].strip()] = total_line[1].strip()

        #get key name
        key_name = output.pop(0)
        key_name = key_name.split()

        #get forwarding information for each vm-mac
        for fw_in in output :
            fw_in_l = fw_in.split()
            num = len(fw_in_l)
            vm_mac = fw_in_l[0]
            return_data[vm_mac] = {}
            for i in range(0,num) :
                fw_in_e_v = fw_in_l[i].strip()
                fw_in_e_k = key_name[i].strip()
                return_data[vm_mac][fw_in_e_k] = fw_in_e_v
        logger.debug('forwaing table of {} epi is {}\n'.format(kwargs.get('epi'),return_data))
        return True,return_data

    def va_check_epi_forwarding_table(self, *args, **kwargs):
        """
        check epi forwarding table if it is correct according to the value of epi,vm-mac, micro-vlan and seg-id
         or option parameter (epi-mac, epi-ip and flag)
        param   : kwargs : dict
            kwargs = {
                    'epi' : uuid or hostname of the epi. eg: 2-6 or epi6
                    'fw_data' :[
                       {
                            'EPI-MAC': the value of epi-mac[option],
                            'EPI-IP': the value of epi ip[Option]
                            'SEG-ID': 'the value of seg id
                            'MICRO-VLAN': the value of micor vlan
                            'VM-MAC': the value of vm mac
                            'FLAG': the value of flag[option]}
                        }
                    ],
                    'Total remote entries' : option,
                    'Total local entries': option
            }
        return: bool
            Success: return True
            Failure: return False
        example :
             va_check_epi_forwarding_table(**kwargs)
             kwargs = {
                'epi': '2-6',
                'fw_data': [
                    {
                        'EPI-MAC': 'local',
                        'EPI-IP': 'local',
                        'SEG-ID': '3000',
                        'MICRO-VLAN': '2002',
                        'VM-MAC': '0:c:29:51:77:f8',
                        'FLAG': '111'
                     },
                     {'SEG-ID': '3000', 'MICRO-VLAN': '2003', 'VM-MAC': '0:50:56:8e:ed:8'}],
                     'Total local entries' : 2,
                     'Total remote entries': 0

            }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if not 'epi' in kwargs :
            raise ValueError("uuid of hostname of epi is mandatory parameter!\n")

        if not 'fw_data' in kwargs :
            raise ValueError("fw_table is mandatory parameter!\n")

        result,forwarding_info = self.va_get_epi_forwarding_table(**{'epi': kwargs.get('epi')})

        if result == False :
            return False

        expect_fw_data = kwargs.get('fw_data')

        if 'Total remote entries' in kwargs :
            expect_val = int(kwargs.get('Total remote entries'))
            actual_val = int(forwarding_info.get('Total remote entries'))
            if actual_val != expect_val :
                logger.error('The value of total remove entries is incorrect')
                logger.debug('Expect value of total remove entries is {}'.format(expect_val))
                logger.debug('Actual value of total remove entries is {}'.format(actual_val))
                return False

        if 'Total local entries' in kwargs:
            expect_val = int(kwargs.get('Total local entries'))
            actual_val = int(forwarding_info.get('Total local entries'))
            if actual_val != expect_val:
                logger.error('The value of Total local entries is incorrect')
                logger.debug('Expect value of Total local entries is {}'.format(expect_val))
                logger.debug('Actual value of Total local entries is {}'.format(actual_val))
                return False

        for each_fw_info in expect_fw_data:
            vm_mac = each_fw_info.get('VM-MAC')
            micro_vlan = each_fw_info.get('MICRO-VLAN')
            seg_id = each_fw_info.get('SEG-ID')
            if not vm_mac.strip() in forwarding_info:
                logger.error('Not found vm_mac {} in forwarding table'.format(vm_mac))
                return False

            actual_fw =  forwarding_info.get(vm_mac.strip())
            if vm_mac.strip() != actual_fw.get('VM-MAC') or \
                micro_vlan.strip() != actual_fw.get('MICRO-VLAN') or \
                seg_id.strip() != actual_fw.get('SEG-ID') :
                logger.error('Verification failure!!!')
                logger.debug('Expect value are:vm_mac:{},micro_vlan:{},\
                seg_id:{}'.format(vm_mac,micro_vlan,seg_id))
                logger.debug('Acutal values are:vm_mac:{},micro_vlan:{},\
                seg_id:{}'.format(actual_fw.get('VM-MAC'),actual_fw.get('MICRO-VLAN'),actual_fw.get('SEG-ID')))
                return False

            if 'EPI-MAC' in each_fw_info :
                epi_mac = each_fw_info.get('EPI-MAC')
                if epi_mac != actual_fw.get('EPI-MAC') :
                    logger.error('Verification failure for EPI-MAC. expect value:{}, \
                    actual value:{}'.format(actual_fw.get('EPI-MAC'),epi_mac))
                    return False

            if 'EPI-IP' in each_fw_info :
                epi_ip =each_fw_info.get('EPI-IP')
                if epi_ip != actual_fw.get('EPI-IP'):
                    logger.error('Verification failure for EPI-IP. expect value:{}, \
                                actual value:{}'.format(actual_fw.get('EPI-IP'), epi_ip))
                    return False

            if 'FLAG' in each_fw_info:
                flag = each_fw_info.get('FLAG')
                if flag != actual_fw.get('FLAG'):
                    logger.error('Verification failure for FLAG. expect value:{}, \
                                actual value:{}'.format(actual_fw.get('FLAG'), flag))
                    return False
            logger.info('Succeed to check forwaring for vm_mac {}'.format(vm_mac))

        logger.info('Succeed to check forwarding for epi {}'.format(kwargs.get('epi')))
        return True

    def va_get_epi_interface(self, *args, **kwargs):
        """
        Method to get interface of epi
        param      : kwargs : dict
                     epi : object | uuid | hostname of epi
        return (List): a list like this
        [
            Intf(NAME='fabric-intf', IP='10.0.0.96', MAC='0:c:29:d9:5:eb', ID='0x600', STATE='Up/Up'), 
            Intf(NAME='south-intf', IP='0.0.0.0', MAC='0:c:29:d9:5:9', ID='0x603', STATE='Up/Up')
        ]
        example    : intf_info = va_get_epi_interface(epi='2-6')
                   : intf_info = va_get_epi_interface(epi=epi_1)
                     for intf in intf_info:
                        name = intf.NAME ##: -- Get detailed info, such as name, ip if you need
                        ip   = intf.IP
                        ...
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'epi' not in kwargs:
            raise ValueError(" epi is mandatory parameter!\n") 
        epi = kwargs.get('epi')
        if isinstance(epi, Delegator):
            if epi._resource.get_nodetype() == 'epi':
                epi_obj = epi
                epi = self.va_get_epi_uuid(epi_obj=epi_obj)

        cmd = 'show chassis epi {} interface'.format(epi)
        output = self._access.va_cli(cmd)

        return(self._va_parse_epi_interface(output))

    def _va_parse_epi_interface(self, output=None):
        """
        Helpter method to parse interface of epi
        show chassis epi 2-6 interface
         NAME           IP               MAC                ID     STATE(ADMIN/LINK)
        -----------------------------------------------------------------------------
         fabric-intf    10.0.0.96        0:c:29:d9:5:eb     0x600  Up/Up 
         mgt-intf       10.11.120.96     0:c:29:d9:5:f5     0x601  Up/Up 
         north-intf     0.0.0.0          0:c:29:d9:5:ff     0x602  Up/Up 
         south-intf     0.0.0.0          0:c:29:d9:5:9      0x603  Up/Up 
        ##: disabled due to user request. Use command "request chassis epi ..." to bring the interface up.

        return (List): a list like this
        [
            Intf(NAME='fabric-intf', IP='10.0.0.96', MAC='0:c:29:d9:5:eb', ID='0x600', STATE='Up/Up'), 
            Intf(NAME='mgt-intf', IP='10.11.120.96', MAC='0:c:29:d9:5:f5', ID='0x601', STATE='Up/Up'), 
            Intf(NAME='north-intf', IP='0.0.0.0', MAC='0:c:29:d9:5:ff', ID='0x602', STATE='Up/Up'), 
            Intf(NAME='south-intf', IP='0.0.0.0', MAC='0:c:29:d9:5:9', ID='0x603', STATE='Up/Up')
        ]
        """
        parsed = list()
        Intf = namedtuple('Intf', ['NAME', 'IP', 'MAC', 'ID',
                                       'STATE'])

        for line in va_parse_as_lines(output):
            line = line.lstrip()
            if not line.startswith('NAME')\
                and not line.startswith('-')\
                and not line.startswith('##')\
                and not line.startswith('varmour'):
                    values = line.split()
                    print(values)
                    parsed.append(Intf(*values))

        return parsed

    def va_unset_epi_microsegmentation(self, *args, **kwargs):

        """
        Method to unset epi micro-segmentation 
        Param      : kwargs : dict
                     uuid    : epi uuid
                     segment_id(optional) : Segment information
                     micro_vlan(optional)     : Local VLAN ID  micro-vlan value
                     is_commit : True|False, True by default
        example    : va_unset_epi_microsegmentation(**kwargs)
                   kwargs = {
                    'uuid': '564DB44A-B3F3-5D0B-0C33-77CD43987BFC',
                    'segment': '1000',
                    'micro-vlan' : '2000'
                   }
        return: a tuple of True and cmd on success, False and err_msg on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   
        if not 'uuid' in kwargs:
            raise ValueError(" 'uuid' is mandatory parameters!\n") 
        
        is_commit = True
        uuid = kwargs.get('uuid')
        cmd = 'unset micro-segmentation epi {}'.format(uuid)
        
        if 'segment_id' in kwargs:
            cmd += ' segment {}'.format(kwargs.get('segment_id'))
        
        if 'micro_vlan' in kwargs:
            cmd += ' micro-vlan {}'.format(kwargs.get('micro_vlan'))

        if 'is_commit' in kwargs:
            is_commit = kwargs.get('is_commit')

        ret_val, err_msg = self._access.va_config(cmd, commit=is_commit)
        if ret_val is not None:
            return False, err_msg

        cmd = cmd.replace('unset','set')
        logger.info('Succeed to unset micro-segmentation of EPI')
        return True, cmd
    
    
    def va_show_microsegment_epi(self, epi_dev=None):
        """
        method to get epi microsegment info.

        kwargs:
            :epi_dev : epi obj

        returns:
            :dict: dict of parsed information
        
        Example    : va_show_microsegment_epi()
                     va_show_microsegment_epi(epi_1)
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if epi_dev:
            cmd = "show micro-segmentation epi {}".format(self.va_get_epi_uuid(epi_obj=epi_dev))
        else:
            cmd = "show micro-segmentation epi"
        parser = self._va_parse_microsegment_epi
        output = self._access.va_cli(cmd)
        return parser(output)

    def _va_parse_microsegment_epi(self, output=None):
        """
        helper method to parse 'show microsegment epi' or
        'show micro-segmentation epi uuid'

        returns (list): look at the following output
        [Micro_Epi(EPI='564DDF39-5C53-66E4-4F64-6CB7B2B8BC9B', EPI_hostname='-', segment='100', micro_vlan='1'), 
         Micro_Epi(EPI='564DDF39-5C53-66E4-4F64-6CB7B2B8BC9B', EPI_hostname='-', segment='100', micro_vlan='2'), 
         Micro_Epi(EPI='564DDF39-5C53-66E4-4F64-6CB7B2B8BC9B', EPI_hostname='-', segment='200', micro_vlan='3'), 
         Micro_Epi(EPI='564DDF39-5C53-66E4-4F64-6CB7B2B8BC9B', EPI_hostname='-', segment='200', micro_vlan='4'), 
         Micro_Epi(EPI='564D6404-88C7-0A2C-04D2-3CD6F05E3C6D', EPI_hostname='-', segment='100', micro_vlan='1')]
        """
        parsed = list()

        parse_info = va_parse_as_lines(output)
        parse_info.pop(-1)
        micro_epi = namedtuple('Micro_Epi',['EPI','EPI_hostname','segment','micro_vlan'])
        for line in parse_info:
            line = line.strip()
            if line.startswith('EPI') or line.startswith('---') or 'show micro-segmentation' in line:
                continue
            else:
                parse_values = list()
                values = line.split('|')
                for list_element in values:
                    parse_values.append(list_element.strip())
                parsed.append(micro_epi(*parse_values))
        return parsed
