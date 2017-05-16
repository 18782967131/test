"""coding: utf-8

Copyright 2016 vArmour Chassis private.
All Rights reserved. Confidential

Chassis related features. A superset of features apply
to the product 'dir'.
.. moduleauthor:: xliu@varmour.com
"""
import re, sys
from collections import namedtuple
from feature import logger
from feature.common import VaFeature
from feature import Controller
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines


class VaChassis(VaFeature):
    """
    Chassis realted API.
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
        super(VaChassis, self).__init__(resource)
        self._parent = None

        other_features = ['system', 'system-common']
        self.controller = Controller(resource, other_features)

        common = '_'.join(('', 'system-common'))
        if common in self.controller.__dict__.keys():
            self._parent = self.controller.__dict__.get(common)

    def va_get_active_device(self):
        """
        get the number of active devices of director and CP/EP

        kwargs: None

        returns:
            dict : {'active_devices': The number of active devices except EPI,
                    'active_epis': The number of active EPIs
                    }
        Examples:
            va_get_active_device()
        """
        count_dev = 0
        count_epis = 0
        return_value = {}

        chassis_info = self.controller.va_show_chassis()
        dev_status = chassis_info.get('devices status')
        total_dev_counts = dev_status.get('total devices connected')
        inactive_devs = dev_status.get('inactive devices')

        match_tol_act_devs = re.search(r'^(\d+)\s+\(',total_dev_counts, re.I | re.M)
        if match_tol_act_devs is not None:
            total_dev_count = match_tol_act_devs.group(1)
            if int(total_dev_count) != 0:
                logger.debug("The number of devices are %s" % total_dev_count)
            else:
                logger.warn("The number of total connected devices is incorrect")
        else:
            logger.error("Failed to get 'total devices connected' \
        information via 'show chassis'")

        match_rt = re.search(r'(\d+)\s+\(', inactive_devs, re.I|re.M)
        if match_rt is not None:
            inactive_dev_count = match_rt.group(1)
            if int(inactive_dev_count) == 0:
                logger.debug("No inactivate devices")
            else:
                logger.warn("The number of inactive device are %s" % inactive_dev_count)
        else:
            logger.error("Failed to get information of inactive device")

        #number of activate devices except EPI.
        count_dev = int(total_dev_count) - int(inactive_dev_count)
        return_value['active_devices'] = count_dev

        #get number of activate EPIs
        rt = self._access.va_cli('show chassis epi')
        match_rt = re.search(r'Total active EPIs:\s+(\d+)', rt, re.I | re.M)
        if match_rt is not None:
            count_epis = match_rt.group(1)
            if count_epis != 0:
                logger.debug("The number of EPIs are %s" % count_epis)
            else:
                logger.debug("No activate EPIs")
        else:
            logger.error("Failed to get information of EPIs")
        return_value['active_epis'] = count_epis

        return return_value

    def va_get_chassis_database(self, *args, **kwargs):
        """
        API to get 'show chassis database'
        param   : kwargs : dict
                : dev_id : device id, 'all' by default
        return  : a dict like this
            {
                'Chassis db device info 1': {
                    'DEVICE': 'vArmour',
                    'DEVICE ID': '1',
                    'DEVICE TYPE': 'controller',
                    'LAST UP TIME': 'Tue Mar  7 19:40:07 2017',
                    'UUID': '564D6062-7AAA-D604-17FE-79163FFCE9B5',
                    'Licensed': 'No',
                    'UP COUNT': '1',
                    'CONF VERSION': '0xf',
                    'Chassis db slot info': '',
                    'MANAGEMENT GATEWAY': '10.11.120.1',
                    'CONF PUSH STATUS': 'done',
                    'ENABLED MGT SERVICE': 'https ssh',
                    'SLOT COUNT': '1',
                    'CONNECTION TYPE': 'LOCAL',
                    'Chassis db slot info 1': {
                        'SLOT ID': '0',
                        'Containing node info 1': {
                            'LAST UP TIME': 'Tue Mar  7 19:40:09 2017',
                            'TYPE': 'Control Node',
                            'CONF PUSH STATUS': 'done',
                            'NODE ID': '1',
                            'UP COUNT': '1',
                            'intf': [
                                intf(name='local', node='1/173', flag='00400100', address='84:49:15:ff:0:1', state='up', note=''),
                        },
                        'Containing node info 2': {
                            'NODE ID': '2',
                            'LAST UP TIME': 'Tue Mar  7 19:40:10 2017',
                            'TYPE': 'Routing Engine Node',
                            'UP COUNT': '1',
                            'CONF PUSH STATUS': 'done'
                        },
                        'Containing node info 3': {
                            'LAST UP TIME': 'Tue Mar  7 19:40:12 2017',
                            'TYPE': 'Service Node',
                            'SESSION THRESHOLD': '0',
                            'CONF PUSH STATUS': 'done',
                            'NODE ID': '3',
                            'EXCLUDE FROM RR': 'No',
                            'UP COUNT': '1'
                        },
                        'Containing node info 4': {
                            'LAST UP TIME': 'Tue Mar  7 19:40:14 2017',
                            'TYPE': 'Switch Node',
                            'CONF PUSH STATUS': 'done',
                            'NODE ID': '4',
                            'UP COUNT': '1',
                            'intf': [
                                intf(name='xe-1/0/3', node='4/007', flag='00000000', address='0:50:56:99:2b:e3', state='up', note=''),
            
                                intf(name='xe-1/0/3.1', node='0x00403001', flag='00000000', address='0.0.0.0/00', state='up', note='')
                            ]
                        }
                    }
                }
            }
        example  : output = va_get_chassis_database(dev_id=1)
                   output = va_get_chassis_database()
                   for k, v in output.items(): get device info
                       for x, y in v.items(): # get slot info
                           try:
                               for key, val in y.items(): # get node info
                                   if 'intf' in val:
                                       for intf_info in val.get('intf'): # get intf info from a list of intf
                                           intf_name = intf_info.name # get interface name, such as name='xe-1/0/3'
                                           intf_node = intf_info.node # get interface node, such as node='4/007'
                           except AttributeError:
                               pass
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   
        if 'dev_id' in kwargs:
            dev_id = kwargs.get('dev_id')
        else:
            dev_id = "all"
        cmd = "show chassis database device {}".format(dev_id)
        output = self._access.va_cli(cmd)

        #Split output with 'DEVICE ID'
        lines = va_parse_as_lines(output)
        info_index_list = list()
        for line in lines:
            line = line.strip()
            try:
                name, value = line.split(':')
                name = name.strip()
            except:
                name = None
            if name == 'DEVICE ID':
                info_index = lines.index(line)
                info_index_list.append((info_index - 1))

        dev_id = 1
        parsed = dict()
        for i in range(len(info_index_list)):
            try:
               s, e = info_index_list[i], info_index_list[i +1]
            except IndexError:
               s, e = info_index_list[i], -1
            new_output = lines[s:e]
            parsed.update(self._va_parse_chassis_database(new_output, dev_id))
            dev_id += 1
        return(parsed)

    def _va_parse_chassis_database(self, output=None, dev_id=1):
        """
        helper method to parse 'show chassis database'
        return (dict): look at the following output
        """
        parsed = dict()
        parsed_intf = list()
        intf_name_list = ['name', 'node', 'flag', 'address', 'state', 'note']
        named_intf = namedtuple('intf', intf_name_list)

        slot_id = 1
        node_id = 1
        dev_info  = 'Chassis db device info'
        slot_info = 'Chassis db slot info'
        node_info = 'Containing node info'
        for line in output:
            line = line.strip()

            #Get info related to 'Chassis db device info'
            if line.startswith('DEVICE') and ('DEVICE ID' not in line and \
                'DEVICE TYPE' not in line):
                outter_key = "{} {}".format(dev_info, dev_id)
                dev_key = outter_key
                dev_id += 1
                tmpDict = dict()
            elif line.startswith('[Containing slot info'):
                outter_key = "{} {}".format(slot_info, slot_id)
                slot_key = outter_key
                slot_id += 1
                tmpDict = dict()
            elif line.startswith('[Containing node info'):
                outter_key = "{} {}".format(node_info, node_id)
                node_key = outter_key
                node_id += 1
                tmpDict = dict()

            if outter_key not in tmpDict:
                tmpDict[outter_key] = dict()

            if '/' in line and not line.startswith('name'):
                values = line.split()
                if len(values) != len(intf_name_list):
                    values.append("")
                try:
                    parsed_intf.append(named_intf(*values))
                except TypeError:
                    pass
                if outter_key.startswith(node_info):
                    tmpDict[outter_key]['intf'] = parsed_intf
            elif ':' in line:
                inner_key, value = line.split(':', 1)

                # Here need to handle special string 'CONNECTION TYPE : : LOCAL'
                if ":" in value:
                    value = value.split(':')[1]
                tmpDict[outter_key][inner_key.strip()] = value.strip()

            if outter_key.startswith(slot_info):
                parsed[dev_key].update(tmpDict)
            elif outter_key.startswith(node_info):
                parsed[dev_key][slot_key].update(tmpDict)
            elif outter_key.startswith(dev_info):
                parsed.update(tmpDict)
        return(parsed)

    def va_get_chassis_fabric_vxlan_info(self):
        """
            get chassis fabric vxlan info 
            param   : None
 
            return (list) : look at the following output
            varmour@vArmour#ROOT> show chassis fabric
            Global VXLAN Tunnel ID: 10
            DEV-ID   | HOSTNAME             | STATE      | MGT-IP               | FABRIC-IP            | FABRIC-GW            | MODE 
            -------------------------------------------------------------------------------------------------------------------------
            1        | vArmour              | Active     | 10.11.120.41/24      | 10.0.0.41/24         | --                   | DIR   
            2        | vArmour              | In-Active  | --                   | 10.0.0.43/24         | --                   |       
            3        | vArmour              | Active     | 10.11.120.46/24      | 10.0.0.46/24         | --                   | CP    
            4        | vArmour              | Active     | 10.11.120.43/24      | 10.0.0.43/24         | --                   | CP   

            return (list) :                                                                                                                                                  
       
            [  
                'Global VXLAN Tunnel ID: 10', 
                fabric(DEVID='1', HOSTNAME='vArmour', STATE='Active', MGT_IP=' 10.11.120.41/24', FABRIC_IP=' 10.0.0.41/24', FABRIC_GW='--', MODE='DIR'), 
                fabric(DEVID='2', HOSTNAME=' vArmour', STATE=' In-Active', MGT_IP='--', FABRIC_IP=' 10.0.0.43/24', FABRIC_GW='--', MODE='   '), 
                fabric(DEVID='3', HOSTNAME=' vArmour', STATE=' Active', MGT_IP=' 10.11.120.46/24', FABRIC_IP=' 10.0.0.46/24', FABRIC_GW='--', MODE='CP'), 
                fabric(DEVID='4', HOSTNAME=' vArmour', STATE=' Active', MGT_IP=' 10.11.120.43/24', FABRIC_IP=' 10.0.0.43/24 ', FABRIC_GW='--', MODE=' CP')
            ]
            
            example     : dir_1.va_get_chassis_fabric_vxlan_info()
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        parsed = list()
        Usert = namedtuple('fabric',['DEVID','HOSTNAME','STATE','MGT_IP','FABRIC_IP','FABRIC_GW','MODE'])
        rt = self._access.va_cli("show chassis fabric")

        for line in va_parse_as_lines(rt):
            line = line.replace(' ','')
            if line.startswith('Global VXLAN Tunnel ID') and not line.startswith('DEV-ID') \
            and 'show chassis fabric' not in line and not line.startswith('-'):
                parsed.append(line)                
            elif not line.startswith('Global VXLAN Tunnel ID') and not line.startswith('DEV-ID') \
            and not line.startswith('-') and 'show chassis fabric' not in line:
                values = line.split("|")
                if '-' in values:
                    values = "_"
                try:
                    parsed.append(Usert(*values))
                except TypeError:
                    pass
        
        logger.info(parsed)
        return parsed

    def va_show_chassis_database_option(self,*args, **kwargs):

        """
            method to show chassis database info
            param    : kwargs : dict
                     kwargs = {                       
                                   fir_option : database option 'saved|device|slot|node|interface|logical-interface|next-hop|address'
                                   sec_option : database saved option  'device|interface|node|logical-interface'
                                   device_id : device id or all
                     }


            return (str) : the chassis database option info 
            example    : dir_1.va_show_chassis_database_option(**kwargs)
                          kwargs = {
                           'fir_option'    : 'saved'
                           'sec_option'    : 'node'
                           'device_id'       : 4
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        pre_cmd = "show chassis database"

        if 'fir_option' in kwargs :
            pre_cmd+=' %s' % kwargs['fir_option']
        else:
            raise ValueError("fir_option is mandatory parameter!\n")

        if 'sec_option' not in kwargs:
            if kwargs['fir_option'] == 'saved':
                raise ValueError("sec_option is mandatory parameter!\n")
        else:
            pre_cmd+=' %s' % kwargs['sec_option']            
        
        if 'device_id' not in kwargs :
            if kwargs['fir_option'] != 'address' or kwargs['fir_option'] != 'next-hop':
                raise ValueError("device_id is mandatory parameter!\n")                
        else :
            if kwargs['fir_option'] == 'address' or kwargs['fir_option'] == 'next-hop':
                raise ValueError("address or next-hop don't need device_id parameter!\n")
            else:
                pre_cmd+=' %s' % kwargs['device_id']
   
        return(self._access.va_cli(pre_cmd))

    def va_set_chassis_fabric(self, *args, **kwargs):

        """
            method set fabric tunnel/secret/heartbeat-interval 
            param      : kwargs : dict
                       kwargs = {
                                 'vxlan'    : 'vxlan identifier'
                                 'secret'   : 'fabric secret key'
                                 'heartbeat_interval'   : ' Heartbeat interval in seconds'
                                 'is_commit': 'commit' True|False
                       }
            return     : Tuple
                True,cmd
                False,err log

            Example    : va_set_chassis_fabric(**kwargs)
                        kwargs = {
                         'vxlan'    : 10,
                         'secret'   : 'varmour',
                         'heartbeat_interval'    : 3,
                         'is_commit'    : True
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmds = []

        if 'vxlan' in kwargs:
            cmds.append('set chassis fabric tunnel vxlan %s' % (kwargs['vxlan']))

        if 'heartbeat_interval' in kwargs:
            cmds.append('set chassis fabric heartbeat_interval %s' % (kwargs['heartbeat_interval']))

        if 'secret' in kwargs:
            cmds.append('set chassis fabric secret %s' % (kwargs['secret']))

        if not 'is_commit' in kwargs :
            is_commit = True
        else :
            is_commit = kwargs['is_commit']
    
        err_cmd,err_msg = self._access.va_config(cmds,commit=is_commit)

        if err_cmd is None or err_msg is None:
            logger.info("Succeed to set chassis fabric")
            return True,cmds
        else:
            error = "Failed to set chassis fabric"
            logger.error(error)
            return False,err_msg
    
    def va_conf_chassis_debug(self,*args, **kwargs):

        """
            API config chassi debug service/control/io/agent/routing-engine/konfd/chassis-d/orchestration/telemetry
            Param      : kwargs : 
                         debug_name(list) : Enabled debug name (default: ['service','io','agent','control','routing-engine',
                                                                         'konfd','chassis-d','telemetry','orchestration'])
                         enable_device    : Device ID or all devices (default: all)
                         orchestration_debug(list) : Orchestration debug flag (default: all)
                         is_commit        : commit True|False(default:True)
            Return     : Tuple
                         True,cmd
                         False,err log

            Example    : 
                       va_conf_chassis_debug(orchestration_debug=['orch-event','orch-deploy',\
                                                                  'vcenter-plugin-event'])
                       va_conf_chassis_debug(debug_name='orchestration')
                        
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        name_list = ['service','io','agent','control','routing-engine',\
                     'konfd','chassis-d','telemetry','orchestration']
        cmds = []
        pre_cmd = 'set chassis process '
        is_commit = kwargs.get('is_commit',True)
        debug_name = kwargs.get('debug_name',['service','io','agent','control','routing-engine',\
                                              'konfd','chassis-d','telemetry','orchestration'])
        if isinstance(debug_name,str):
            debug_name = debug_name.split(',')
        
        for enable_debug_name in debug_name:
            if enable_debug_name in ['service','io','agent']:
                enable_dev = kwargs.get('enable_device','all')
                cmds.append(pre_cmd + '{} {} debug all'.format(enable_debug_name,enable_dev))
            elif enable_debug_name == 'orchestration':
                orch_debugs = kwargs.get('orchestration_debug','all')
                if isinstance(orch_debugs,str):
                    orch_debugs = orch_debugs.split(',')
                for flag in orch_debugs:
                    cmds.append(pre_cmd + 'orchestration debug {}'.format(flag))
            else:
                if enable_debug_name not in name_list:
                    logger.error('Process name "{}" invalid'.format(enable_debug_name))
                    raise ValueError('Incorrect param "{}"'.format(enable_debug_name))
                cmds.append(pre_cmd + '{} debug all'.format(enable_debug_name))

        ret_val, err_msg = self._access.va_config(cmds, commit=is_commit)
        if ret_val is not None:
            logger.error('Fail to set chassis debug')
            return False, err_msg
        logger.info('Succeed to set chassis debug')
        return True, cmds 

    def va_unset_chassis_debug(self,*args, **kwargs):

        """
            API unset chassi debug service/control/io/agent/routing-engine/konfd/chassis-d/orchestration/telemetry
            Param      : kwargs : 
                         debug_name(list) : Enabled debug name (default: all of debug process list)
                         enable_device    : Device ID or all devices (default: all)
                         orchestration_debug(list) : Orchestration debug flag (default: all)
                         is_commit        : commit True|False(default:True)
            Return     : Tuple
                         True,cmd
                         False,err log

            Example    : 
                       va_unset_chassis_debug(orchestration_debug=['orch-event','orch-deploy',\
                                                                  'vcenter-plugin-event'])
                       va_unset_chassis_debug(debug_name='orchestration'),
                       va_unset_chassis_debug()
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        debug_name = ['service','io','agent','control','routing-engine','konfd','chassis-d',\
                      'telemetry','orchestration']

        cmds = []
        pre_cmd = 'unset chassis process '
        is_commit = kwargs.get('is_commit',True)

        debug_name = kwargs.get('debug_name',['service','io','agent','control','routing-engine',\
                                              'konfd','chassis-d','telemetry','orchestration'])
        if isinstance(debug_name,str):
            debug_name = debug_name.split(',')
        
        for enable_debug_name in debug_name:
            if enable_debug_name in ['service','io','agent']:
                enable_dev = kwargs.get('enable_device','all')
                cmds.append(pre_cmd + '{} {} debug all'.format(enable_debug_name,enable_dev))
            elif enable_debug_name == 'orchestration':
                orch_debugs = kwargs.get('orchestration_debug','all')
                if isinstance(orch_debugs,str):
                    orch_debugs = orch_debugs.split(',')
                for flag in orch_debugs:
                    cmds.append(pre_cmd + 'orchestration debug {}'.format(flag))
            else:
                cmds.append(pre_cmd + '{} debug all'.format(enable_debug_name))

        ret_val, err_msg = self._access.va_config(cmds, commit=is_commit)
        if ret_val is not None:
            logger.error('Fail to unset chassis debug')
            return False, err_msg
        cmd_str = ','.join(cmds)
        cmd_list = (cmd_str.replace('unset','set')).split(',')
        logger.info('Succeed to unset chassis debug')
        return True, cmds 
