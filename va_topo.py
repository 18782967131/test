"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaTopo implements the class that abstracts the topology required to 
setup/cleanup testbed

.. moduleauthor::  xliu@sigma-rt.com
"""
import os, re, time, sys, pprint, ipaddress
import builtins

from vautils import logger
from vautils.dataparser.test import VaTestInfo
from vautils.dataparser.yaml import load_yaml
from feature.common.accesslib import VaAccess as Access

class VaTopo(object):
    """ 
    Class implements test bed set up and clean up
    """
    def __init__(self, test_param_yaml, topo_yaml, image=None,  **kwargs):
        """
        Initializes the device/pc object and data from topo and test_param yaml file

        Kwargs:
            test_param_yaml    : data of test parametes.
                                 onttrol information and  user_params
            topo_yaml          : data of topo,
                    for exampe: inventory file. devices information, connections information.
            image: string, url of image, for example: https://10.123.0.8/image.tar

        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.setup()
            vatpobj.cleanup()

        """
        #check if need to add varmour_no_cli user
        test_params = load_yaml(test_param_yaml)
        self.add_nocli_user = False
        if 'add_nocli_user' in test_params.get('control') and \
                        test_params.get('control').get('add_nocli_user').upper() == 'Y':
            self.add_nocli_user=True

        self.testdata = VaTestInfo(test_param_yaml, topo_yaml, add_nocli_user=self.add_nocli_user)
        self.link_info = self.testdata.va_get_links()
        self.ints_info = self.testdata.va_get_interfaces()
        self.route_info = self.testdata.va_get_routes()
        self.vmsobj = self.testdata.va_get_test_vms()
        self.swobjs = {}
        self.get_vsw_obj()  #get vswitch object
        self.control_data = self.testdata.va_get_control()
        self.image = image
        builtins.__dict__['testdata'] = self.testdata
        builtins.__dict__['dirs'] = []
        builtins.__dict__['cps'] = []
        builtins.__dict__['epis'] = []
        for dev_name in self.vmsobj.keys():
                dev_type =self.vmsobj.get(dev_name).get_nodetype()
                if (dev_type == 'esxi' ) :
                    continue

                dev_obj = self.testdata.va_get_by_uniq_id(dev_name)
                builtins.__dict__['%s' % dev_name] = dev_obj
                if (dev_type == 'dir'):
                    builtins.__dict__['dirs'].append(dev_obj)
                elif (dev_type == 'cp') :
                    builtins.__dict__['cps'].append(dev_obj)
                elif (dev_type == 'epi') :
                    builtins.__dict__['epis'].append(dev_obj)
                else :
                    pass

        for hv_id in self.swobjs.keys():
             hv_obj = self.swobjs.get(hv_id)
             builtins.__dict__['%s' % hv_id] = hv_obj

    def get_dir_object(self):
        '''
                get all director object according to topo file.

        Kwargs:
                None
        Return:
                tuple.
                Sucess: True,[dir1,dir2]
                Fail :False,[]
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.get_dir_object()
        '''
        for key,val in builtins.__dict__.items() :
            if key == 'dirs' :
                return True,val

        return False,[]

    def get_cp_object(self):
        '''
                get all cp object according to topo file.

        Kwargs:
                None
        Return:
                tuple.
                Sucess: True,[cp1,cp2]
                Fail :False,[]
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.get_cp_object()
        '''
        for key,val in builtins.__dict__.items() :
            if key == 'cps' :
                return True,val

        return False,[]

    def get_epi_object(self):
        '''
                get all epi object according to topo file.

        Kwargs:
                None
        Return:
                tuple.
                Sucess: True,[epi1,epi2]
                Fail :False,[]
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.get_epi_object()
        '''
        for key,val in builtins.__dict__.items() :
            if key == 'epis' :
                return True,val

        return False,[]

    def va_config_interfaces(self):
        """
        Config ip address for test interfaces according to topo file. both support vArmour device and linux pc.

        Kwargs:
                None
        Return:
                True   :   Succeed to config ip address for pc or vArmour devices according to topo file.
                False :    Failed to config ip address for pc or vArmour devices according to topo file.
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.va_config_interfaces()

        """
        logger.info("Start to config ip address")
        ints_info = self.ints_info

        for key in ints_info.keys() :
            devobj = self.testdata.va_get_by_uniq_id(key)
            node_type = self.testdata.va_get_by_uniq_id(key, False).get_nodetype() #linux or dir

            for int_info in ints_info[key] :
                if ( ( not 'auto_set' in  int_info) or (int_info['auto_set'] != 1) ) :
                    continue
                else :
                    #if auto_set =1 , it means to config ip address for defined interface
                    if node_type == 'linux' :
                        result = devobj.config_ip(int_info['ip'], int_info['phy_name'])
                        if not result :
                            logger.debug(devobj.show_interface(int_info['phy_name']))
                            return False
                    elif node_type == 'dir' :
                        result = devobj.va_set_ipv4(int_info['ip'], int_info['phy_name'],True)
                        if not result :
                            return False
                    else:
                        #not support to config inteface for other device now
                        continue

        logger.info("Finished to set interface")
        return True

    def va_unset_interfaces(self):
        """
        unset ip address for test interfaces according to topo file. both support vArmour device and linux pc.

        Kwargs:
                None
        Return:
                True   :   Succeed to unset ip address for pc or vArmour devices according to topo file.
                False :    Failed to unset ip address for pc or vArmour devices according to topo file.
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.va_unset_interfaces()

        """
        logger.info("Start to free address for device's interfaces")
        ints_info = self.ints_info

        for key in ints_info.keys() :
            devobj = self.testdata.va_get_by_uniq_id(key)
            node_type = self.testdata.va_get_by_uniq_id(key, False).get_nodetype() #linux or dir

            for int_info in ints_info[key] :
                if ( ( not 'auto_set' in  int_info) or (int_info['auto_set'] != 1) ) :
                    continue
                else :
                    #if auto_set =1 , it means to config ip address for defined interface
                    if node_type == 'linux' :
                        logger.info('Free address on {}:{}'.format(key,int_info['phy_name']))
                        result = devobj.unconfig_ip(int_info['ip'], int_info['phy_name'])
                        if not result :
                            logger.debug(devobj.show_interface(int_info['phy_name']))
                            return False
                    elif node_type == 'dir' :
                        logger.info('Free address on {}:{}'.format(key, int_info['phy_name']))
                        result = devobj.va_unset_ipv4(int_info['ip'], int_info['phy_name'],True)
                        if not result :
                            return False
                    else:
                        #not support to config inteface for other device now
                        continue

        logger.info("Completed to unset interface")
        return True

    def va_reset_director(self):
        """
        reset system configuration for each director

        Kwargs:
                None
        Return:
                True   :   Succeed to reset director according to topo file.
                False :    Failed to reset director according to topo file.
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.va_reset_director()

        """
        logger.info("Start to reset system configuration for directos")
        result,devobjs = self.get_dir_object()

        if result :
            for devobj in devobjs :
                logger.info('reset system configuration for director')
                if devobj._access._resource.get_user().get('name') == 'varmour_no_cli' :
                    continue
                devobj.va_cli('show system')
                result = devobj.va_reset_all()
                if self.add_nocli_user :
                    devobj.va_add_user(**{
                                   'name'    : 'varmour_no_cli',
                                   'password': devobj._access._resource.get_user().get('password'),
                                   'role'    : 'admin',
                                   'is_commit': True
                                  })

                if not result:
                    return False
        else :
            logger.error('Not found any director devices')
            return False

        logger.info("Completed to reset system configuration for director")
        return True

    def va_config_routes(self):
        """
         add route for vArmour device and linux pc according to topo file

         Kwargs:
                 None
         Return:
                 True   :   Succeed to add route for pc or vArmour devices according to topo file.
                 False :    Failed to add route for pc or vArmour devices according to topo file.
         Examples:
             vatpobj = VaTopo(test_param_file, topo_file)
             vatpobj.va_config_routes()

         """
        logger.debug("Start to config route")
        route_info = self.route_info

        for key in route_info.keys() :

            devobj = self.testdata.va_get_by_uniq_id(key,False)
            routes = route_info[key]
            node_type = devobj.get_nodetype()
            if (node_type == 'linux' or node_type == 'dir') :
                #only support linux pc and director now.
                devobj = self.testdata.va_get_by_uniq_id(key)
                for route in routes :
                    if (not 'auto_set' in route) or (route['auto_set'] != 1):
                        continue
                    else:
                        # if auto_set =1 , it means need to config route for defined pc
                        if node_type == 'linux':
                            result = devobj.config_route(route['dst'],route['netmask'],route['gateway'])

                        if node_type == 'dir':
                            #address netmask format.
                            if isinstance(route['netmask'],int) :
                                address = route['dst']+ '/' +route['netmask']
                            else :
                                address = route['dst'] + '/' + route['netmask']
                            result = devobj.va_set_route(ipaddress.IPv4Network(address), route['gateway'],True)

                        if not result :
                            logger.error('Failed to config route')
                            logger.debug(devobj.show_route())
                            logger.debug(devobj.show_interface())
                            return False

        logger.info("Completed to config route")
        return True

    def va_unset_routes(self):
        """
         delete route for vArmour device according to topo file

         Kwargs:
                 None
         Return:
                 True   :   Succeed to delete route for vArmour devices according to topo file.
                 False :    Failed to delete route for vArmour devices according to topo file.
         Examples:
             vatpobj = VaTopo(test_param_file, topo_file)
             vatpobj.va_unset_routes()
        """
        logger.debug("Start to unset route")
        route_info = self.route_info

        for key in route_info.keys() :
            devobj = self.testdata.va_get_by_uniq_id(key,False)
            routes = route_info[key]
            node_type = devobj.get_nodetype()
            if (node_type == 'linux' or node_type == 'dir') :
                #only support linux pc and director now.
                devobj = self.testdata.va_get_by_uniq_id(key)
                for route in routes :
                    if (not 'auto_set' in route) or (route['auto_set'] != 1):
                        continue
                    else:
                        # if auto_set =1 , it means need to config route for defined pc
                        if node_type == 'linux':
                            #the route will clear automatically after shutdwon the interface
                            continue

                        if node_type == 'dir':
                            #address netmask format.
                            if isinstance(route['netmask'],int) :
                                address = route['dst']+ '/' +route['netmask']
                            else :
                                address = route['dst'] + '/' + route['netmask']
                                address = ipaddress.IPv4Network(address)
                                result = devobj.va_unset_route(address,True)

                        if not result :
                            logger.error('Failed to unset route')
                            logger.debug(devobj.show_route())
                            logger.debug(devobj.show_interface())
                            return False

        logger.info("Completed to unset route")
        return True

    def va_get_reserved_vlan(self):
        """
         get reserved vlan

         Kwargs:
                 None
         Return:
                 List : all reserved vlan
         Examples:
             vatpobj = VaTopo(test_param_file, topo_file)
             vatpobj.va_get_reserved_vlan()

         """
        logger.debug("Start to get reserved vlan")
        return (self.testdata.va_get_network_config().get('vlan_range'))

    def config_links(self):
        """
         set link according to topo file

         Kwargs:
                 None
         Return:
                 True   :   Succeed to set link according to topo file.
                 False :    Failed to set link according to topo file.
         Examples:
             vatpobj = VaTopo(test_param_file, topo_file)
             vatpobj.config_links()
        """

        link_info = self.link_info
        reserved_vlan = self.va_get_reserved_vlan()
        reserved_vlans = []
        for vlan_range in reserved_vlan :
            vlan_start = int(vlan_range.split('-')[0])
            vlan_end = int(vlan_range.split('-')[1])
            vlans = range(vlan_start,vlan_end)
            reserved_vlans += vlans

        logger.info("Start to config link")

        index = 0
        for link_key in link_info.keys() :
            num = 1
            for pc_key in link_info[link_key] :
                if num == 1 :
                    src_port_sw = link_info[link_key][pc_key]['interface']['vswitch']
                    src_portgroup = link_info[link_key][pc_key]['interface']['port_group']
                    src_int = link_info[link_key][pc_key]['interface']['phy_name']
                    src_dev = pc_key

                if num == 2 :
                    dst_port_sw = link_info[link_key][pc_key]['interface']['vswitch']
                    dst_portgroup = link_info[link_key][pc_key]['interface']['port_group']
                    dst_int = link_info[link_key][pc_key]['interface']['phy_name']
                    dst_dev = pc_key

                if 'vlan' in link_info[link_key][pc_key] and \
                                link_info[link_key][pc_key]['vlan'] is not None:
                    vlan_val = link_info[link_key][pc_key]['vlan']
                else :
                    vlan_val = reserved_vlans[index]

                hv_uqid = link_info[link_key][pc_key]['hyp_visor']['uniq_id']
                num += 1

            index += 1
            if (len(link_info[link_key]) ==2) and (src_port_sw != dst_port_sw)  :
                logger.error('The link is not in the same switch')
                return False
            else :
                if len(link_info[link_key]) ==2 :
                    logger.info('Connection:{} Access vlan ({}),from {}:{}, to {}:{}, switch : {}'\
                                .format(link_key,vlan_val,src_dev,src_int,dst_dev,dst_int,src_port_sw))
                else :
                    logger.info('Connection:{} Access vlan ({}),{}:{}, switch : {}' \
                                .format(link_key, vlan_val, src_dev, src_int, src_port_sw))

                vswobj = self.swobjs[hv_uqid][src_port_sw]
                if not vswobj.update_vlan(src_portgroup,vlan_val) :
                    return  False

                #update portgroup for destination pc/device if need
                if len(link_info[link_key]) == 2 :
                    if not vswobj.update_vlan(dst_portgroup,vlan_val) :
                        return False

        vswobj.show_sw()

        logger.info("Completed to config link")
        return True

    def get_vsw_obj(self):
        """
         Instance all vswitch object

         Kwargs:
                  None
         Return:
                  vswitch object   :  dict
                 for example :
                {'hvisor_1':
                    {
                        'hvobj': <vautils.resource.Esxi object at 0x0000000003EA91D0>,
                        'vSwitch1': <vautils.resource.network.esxvswitch.EsxVswitch object at 0x000000000413E0B8>,
                        'vSwitch3': <vautils.resource.network.esxvswitch.EsxVswitch object at 0x000000000413E0F0>,
                        'vSwitch2': <vautils.resource.network.esxvswitch.EsxVswitch object at 0x000000000413E208>
                    }
                }

         Examples:
             vatpobj = VaTopo(test_param_file, topo_file)
             vatpobj.setup()
         """
        inventory_tb_data = load_yaml(self.testdata.inventory_file)
        self.swobjs = {}

        for dev_key in inventory_tb_data.keys() :
            if dev_key == 'network' :
                continue
            for dev in inventory_tb_data[dev_key]:
                if 'type' in dev and dev['type'] == 'esxi' :
                    continue

                hvid = dev['hvisor']['uniq_id']
                if not hvid in self.swobjs:
                    self.swobjs[hvid] = {}

                if not 'hvobj' in self.swobjs[hvid] :
                    self.swobjs[hvid]['hvobj'] = self.testdata.va_get_by_uniq_id(hvid, False)
                    self.swobjs[hvid]['hvobj'].setup_vswitch(self.swobjs[hvid]['hvobj'].get_shell())

                if 'interfaces' in dev:
                    for int in dev['interfaces']:
                        sw_name = int['vswitch']
                        if not sw_name in self.swobjs[hvid] :
                            self.swobjs[hvid][sw_name] = self.swobjs[hvid]['hvobj'].get_vswitch(sw_name)
        logger.info(self.swobjs)
        return self.swobjs

    def revert_links(self):
        """
         revert link according to inventory file

         Kwargs:
                 None
         Return:
                 True   :   Succeed to revert link according to inventory file.
                 False :    Failed to revert link according to inventory file.
         Examples:
             vatpobj = VaTopo(test_param_file, topo_file)
             vatpobj.revert_links()
        """
        inventory_tb_data = load_yaml(self.testdata.inventory_file)
        swobjs = {}

        for dev_key in inventory_tb_data.keys() :
            for dev in inventory_tb_data[dev_key]:
                if not 'interfaces' in dev or len(dev['interfaces']) == 0:
                     continue
                else :
                    vswitches = dev['hvisor']['vswitches']
                    vswitches_l = vswitches.split(' ')

                    for int in dev['interfaces'] :
                        logger.debug('Check switch {} if it is in hv {}'.format(int['vswitch'],
                                                                             dev['hvisor']['mgmt_ip']))
                        tag = 0
                        for vswname in vswitches_l:
                            if vswname == int['vswitch'] :
                                logger.debug('check vswitch on hv.done')
                                tag = 1
                                break

                        if tag == 0 :
                            logger.error('vswitch {} is not in hv {}' . format (int['vswitch'], \
                                                                                dev['hvisor']['mgmt_ip']))
                            return False

                        #update vlan for each interface
                        logger.info('Clean access vlan {} for {}:{}'\
                                    .format(int['vlan'],dev['uniq_id'],int['phy_name']))
                        hv_uqid = dev['hvisor']['uniq_id']
                        vswobj = self.swobjs[hv_uqid][int['vswitch']]
                        if not vswobj.update_vlan(int['port_group'], int['vlan']) :
                             return False

        logger.info("Completed to revert links")
        return True

    def setup(self, **kwargs):
        """
        Implementation of setup test bed

        Kwargs:
                 None
        Return:
                 True   :   Succeed to setup test bed
                 False :    Failed to setup testbed
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.setup()
        """
        setup_tb = self.control_data.get('setup_tb')
        cleanup_dut_cfg = self.control_data.get('cleanup_dut_cfg')
        upgrade_device = self.control_data.get('upgrade_device')

        logger.info("*********************************")
        logger.info("*                                ")
        logger.info("* Start to setup topology        ")
        logger.info("*                                ")
        logger.info("*********************************")

        if (setup_tb.upper() == 'Y') :
            #Config links
            if not self.config_links():
                logger.error('Failed to configure links')
                return False

            #Config interface
            if not self.va_config_interfaces():
                logger.error('Failed to configure ip address of interfaces')
                return False

            #Config interface
            if not self.va_config_routes():
                logger.error('Failed to configure routes')
                return False
        else :
            logger.info('Noe need to setup testbed')

        if (cleanup_dut_cfg.upper() == 'Y') :
            # Reset director
            if not self.va_reset_director():
                return False
        else :
            logger.info('Not need to cleanup director')

        #upgrade device if need.
        if (upgrade_device.upper() == 'Y' and self.image is not None) :
            if not self.va_update_firmware_for_directors(self.image):
                return False
        else:
            logger.info('Not need to upgrade device')

        #reconnect all cp/ep/epi


        logger.debug("*********************************")
        logger.debug("*                                ")
        logger.debug("* Finished to setup topology     ")
        logger.debug("*                                ")
        logger.debug("*********************************")
        return True

    def cleanup(self, **kwargs):
        """
        Implementation of cleanup test bed

        Kwargs:
                 None
        Return:
                 True   :   Succeed to cleanup test bed
                 False :    Failed to cleanup testbed
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.cleanup()
        """
        cleanup_tb = self.control_data.get('cleanup_tb')
        restore_dut_cfg = self.control_data.get('restore_dut_cfg')

        logger.info("*********************************")
        logger.info("*                                ")
        logger.info("* Start to clean topology        ")
        logger.info("*                                ")
        logger.info("*********************************")

        if (cleanup_tb.upper() == 'Y' ) :
            #Remove interface
            if not self.va_unset_interfaces():
                logger.error('Failed to remove ip address of interfaces')
                return False
            #Remove route
            if not self.va_unset_routes():
                logger.error('Failed to remove routes')
                return False

            #Remove link
            if not self.revert_links():
                logger.error('Failed to revert links')
                return False
        else :
            logger.info('Not need to cleanup testbed')

        if (restore_dut_cfg.upper() == 'Y') :
            # Reset director
            if not self.va_reset_director():
                return False
        else :
            logger.info('Not need to restore director')

        logger.info("*********************************")
        logger.info("*                                ")
        logger.info("* Finished to clean topology     ")
        logger.info("*                                ")
        logger.info("*********************************")
        return True

    def va_update_firmware_for_directors(self,image, **kwargs):
        """
        Implementation of upgrade devices for all directors

        Kwargs:
                 None
        Return:
                 True   :   Succeed to upgrade device
                 False :    Failed to upgrade device
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.va_update_firmware_for_directors()
        """
        #update firmware for director
        for dev_name in self.vmsobj.keys() :
            dev_type = self.vmsobj.get(dev_name).get_nodetype()
            user = self.vmsobj.get(dev_name).get_user().get('name')
            if dev_type == 'dir' and user == 'varmour':
                dev_obj = self.testdata.va_get_by_uniq_id(dev_name)
                if not dev_obj.va_update_firmware(image) :
                    return False

        #reconnect cp/ep/epi
        for dev_name in self.vmsobj.keys():
            dev_type = self.vmsobj.get(dev_name).get_nodetype()
            if dev_type == 'cp' or dev_type == 'ep' or dev_type == 'epi' or dev_type == 'dir':
                dev_obj = self.testdata.va_get_by_uniq_id(dev_name)
                dev_obj.va_disconnect()
                dev_obj.va_connect(60)

        return True

    def va_reconnect_cp_ep_epi(self):
        """
        reconnect all devices except director

        Kwargs:
                 None
        Return:
                 True   :   Succeed to reconnect all devices
                 False :    Failed to reconnect all devices
        Examples:
            vatpobj = VaTopo(test_param_file, topo_file)
            vatpobj.va_reconnect_cp_ep_epi()
        """
        ints_info = self.ints_info

        for key in ints_info.keys() :
            devobj = self.testdata.va_get_by_uniq_id(key)
            node_type = self.testdata.va_get_by_uniq_id(key, False).get_nodetype()

            for int_info in ints_info[key] :
                if node_type == 'dir' :
                    result = devobj.va_update_firmware(image)
                    if not result :
                        return False
                else:
                    #not support to update firmware now.
                    continue

        return True

    def __del__(self):
        """
        unlinking the reference to the inventory instance.
        """
        self._inventory = None
        self.testdata = None
        self.link_info = None
        self.ints_info = None
        self.route_info =  None
        self.vmsobj = None
        self.swobjs = None