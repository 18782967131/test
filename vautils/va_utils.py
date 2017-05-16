"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

The libs will hold a banch of common functions

.. moduleauthor::  liliu@sigma-rt.com
"""
import os
import re
import sys
import time
import builtins

from vautils import logger
from vautils.traffic.linux.ftp import Ftp
from vautils.traffic.linux.tftp import Tftp
from vautils.traffic.linux.icmp import Icmp
from feature import Controller
from feature.common.accesslib import VaAccess

def va_setup_ha(*args, **kwargs):
    """
    API to setup HA environment.
    param   : kwargs : dict
    example : va_setup_ha(**kwargs)
        kwargs = {
                'master' : {dir1 : 
                               {'local_address'  : '8.8.8.1/24', 
                                'remote_address' : '8.8.8.2',
                                'priority'       : 8,
                                'preempt'        : enable,
                                'sw_obj'        : vswitch object,
                                'vlan'           : 3, used to update vlan of 
                                                   fabric into the same with 
                                                   pb
                               }
                           },
                'pb'     : {dir2 : 
                               {'local_address'  : '8.8.8.2/24', 
                                'remote_address' : '8.8.8.1'
                                'priority'       : 10,
                                'preempt'        : enable,
                                'sw_obj'         : vswitch object,
                                'vlan'           : 3, used to update vlan of 
                                                   fabric into the same with 
                                                   master
                               }
                           },
                'origin_vlan' : dict, included vlan_port, vlan_id and 
                                vswitch of HA, used to split vlan of fabric of
                                pb into different from master
                'timeout' : 60,
        }
    return:
        :bool - True on success or False on failure:
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    if 'master' not in kwargs or \
        'pb' not in kwargs:
        raise ValueError("master and pb are mandatory parameter!\n")
    master, master_kwargs = kwargs.get('master').popitem()
    pb, pb_kwargs = kwargs.get('pb').popitem()
    for kwgs in [master_kwargs, pb_kwargs]:
        if 'local_address' not in kwgs  or \
            'remote_address' not in kwgs or\
            'vlan' not in kwgs or\
            'sw_obj' not in kwgs:
            raise ValueError("'local_address', 'remote_address', \
                'vlan' and 'sw_obj' are mandatory parameters!\n")

    if 'origin_vlan' not in kwargs:
        raise ValueError("origin_vlan is  mandatory parameter!\n")
    origin_vlan = kwargs.pop('origin_vlan')

    if 'timeout' in kwargs:
        timeout = kwargs.get('timeout')
    else:
        timeout = 60 * 2
    
    master_uniq_id = master._resource.get_uniq_id()
    pb_uniq_id     = pb._resource.get_uniq_id()

    master_sw_obj = master_kwargs.get('sw_obj')
    pb_sw_obj     = pb_kwargs.get('sw_obj')

    vlan_data = origin_vlan.get(pb_uniq_id)
    vlan_data['sw_obj'] = pb_sw_obj
    if not va_update_ha_vlan(**vlan_data):
        return False

    times = 1
    sleeptime = 10
    status = master.va_check_chassis_status()
    while not status and times <= 6:
        logger.info('Sleeping {} seconds to wait'.format(sleeptime))
        time.sleep(sleeptime)
        status = master.va_check_chassis_status()
        times += 1

    if not status:
        return False

    if not master.va_config_ha(*args, **master_kwargs):
        return False

    times = 1
    sleeptime = 2
    ha_info = master.va_show_ha()
    ha_mode = ha_info.get('HA Mode')
    while ha_mode != 'ON' and times <= 6:
        logger.info('Sleeping {} seconds to wait'.format(sleeptime))
        time.sleep(sleeptime)
        ha_info = master.va_show_ha()
        ha_mode = ha_info.get('HA Mode')
        times += 1

    if ha_mode != 'ON':
        return False

    if not pb.va_delete_db():
        return False
    pb.va_reboot(reconnect_delay=timeout)

    if not pb.va_config_ha(*args, **pb_kwargs):
        return False
    pb.va_reboot(reconnect_delay=timeout)
    
    for uniq_id in [master_uniq_id, pb_uniq_id]:
        vlan_data = dict()
        if uniq_id == master_uniq_id:
            vlan_data = master_kwargs
        elif uniq_id == pb_uniq_id:
            vlan_data = pb_kwargs
        vlan_data['port_group'] = origin_vlan[uniq_id]['port_group']
        if not va_update_ha_vlan(**vlan_data):
            return False

    for dev_obj in [master, pb]:
        times = 1
        sleeptime = 10
        logger.debug('Waiting HA to normal')
        try:
            ha_info = dev_obj.va_show_ha()
            ha_mode = ha_info.get('HA Mode')
        except:
            pass
        while ha_mode != 'ON' and times <= 6:
            logger.info('Sleeping {} seconds to wait'.format(sleeptime))
            time.sleep(sleeptime)
            try:
                ha_info = dev_obj.va_show_ha()
                ha_mode = ha_info.get('HA Mode')
            except:
                pass
            times += 1
       
        times = 1
        sleeptime = 10
        is_ready = dev_obj.va_check_ha_ready()
        while not is_ready and times <= 30:
            logger.info('Sleeping {} seconds to wait'.format(sleeptime))
            time.sleep(sleeptime)
            is_ready = dev_obj.va_check_ha_ready()
            times += 1

        if not is_ready:
            logger.error('Unsuccessfully configured HA environment')
            return False

    logger.info('Successfully configured HA environment')
    return True

def va_get_ha_origin_vlan(*args, **kwargs):
    """
    API to get original vlan info of HA
    example : va_get_ha_origin_vlan()
    return:
        :dict : 
            {'dir_2': 
                {
                 'port_group': 'vlan-2', 
                 'vswitch': 'vSwitch3', 
                 'hyp_visor': 'hvisor_1', 
                 'name': 'intf1_0', 
                 'vlan': 22
                }, 
             'dir_1': 
                {
                 'port_group': 'vlan-1', 
                 'vswitch': 'vSwitch3', 
                 'hyp_visor': 'hvisor_1', 
                 'name': 'intf1_0', 
                 'vlan': 11
                }
            }
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    origin_vlan = dict()
    try:
        links = testdata.va_get_links()
    except:
        raise ValueError('The prameter testdata based on va_topo lib')

    for link_info in [links.get('HA_FABRIC_DIR1'), links.get('HA_FABRIC_DIR2')]:
        for dev_name, dev_info in link_info.items():
            tmp = dict()
            origin_vlan[dev_name] = dict()
            for name, info in dev_info.items():
                if name == 'interface':
                    for x in ['name', 'port_group', 'vlan', 'vswitch']:
                        tmp[x] = info[x]
                elif name == 'hyp_visor':
                    tmp[name] = info['uniq_id']
            origin_vlan[dev_name] = tmp

    for dev_name, vlan_info in origin_vlan.items():
        for name, info in vlan_info.items():
            if name == 'port_group':
                pg_name = info
                sw_name = vlan_info['vswitch']
                hv_name = vlan_info['hyp_visor']
                if hv_name in builtins.__dict__:
                    sw_obj = builtins.__dict__.get(hv_name).get(sw_name)
                else:
                    raise ValueError('Not found {} object'.format(sw_name))
                vlan_info['vlan'] = sw_obj.get_vlan(pg_name)
    logger.info('VLAN: {}'.format(origin_vlan))
    return origin_vlan

def va_update_ha_vlan(*args, **kwargs):
    """
    API to update HA vlan.
    param   : kwargs : dict
    example : va_update_ha_vlan(**kwargs)
        kwargs = {
                  'sw_obj'     : vswitch object,
                  'port_group' : vlan port group,
                  'vlan'       : vlan id,
                 }
    return:
        :bool - True on success or False on failure:

    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    if 'sw_obj' not in kwargs:
        raise ValueError("sw_obj is  mandatory parameter!\n")
    
    if 'port_group' not in kwargs:
        raise ValueError("port_group is  mandatory parameter!\n")
    
    if 'vlan' not in kwargs:
        raise ValueError("vlan is  mandatory parameter!\n")

    sw_obj    = kwargs.get('sw_obj')
    vlan_port = kwargs.get('port_group')
    vlan_id   = kwargs.get('vlan')

    if not sw_obj.update_vlan(vlan_port, vlan_id):
        return False

    return True

def va_clean_ha(*args, **kwargs):
    """
    API to clean HA environment.
    param   : kwargs : dict
    example : va_clean_ha(**kwargs)
        kwargs = {
                'master' : {dir1 : 
                               {'local_address'  : '8.8.8.1/24', 
                                'remote_address' : '8.8.8.2',
                                'priority'       : 8,
                                'preempt'        : enable,
                                'sw_obj'         : vswitch object,
                               }
                           },
                'pb'     : {dir2 : 
                               {'local_address'  : '8.8.8.2/24', 
                                'remote_address' : '8.8.8.1'
                                'priority'       : 10,
                                'preempt'        : enable,
                                'sw_obj'         : vswitch object,
                               }
                           },
                'origin_vlan' : dict, included vlan_port, vlan_id and 
                                vswitch of HA, used to split vlan of fabric of
                                pb into different from master,
                'timeout' : 60,
        }
    return:
        :bool - True on success or False on failure:
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    clean_status = True
    if 'master' not in kwargs or \
        'pb' not in kwargs:
        raise ValueError("master and pb are mandatory parameter!\n")
    master, master_kwargs = kwargs.get('master').popitem()
    pb, pb_kwargs = kwargs.get('pb').popitem()
    for kwgs in [master_kwargs, pb_kwargs]:
        if 'local_address' not in kwgs  or \
            'remote_address' not in kwgs or\
            'sw_obj' not in kwgs:
            raise ValueError("'local_address', 'remote_address', \
                'sw_obj' are mandatory parameters!\n")

    if 'origin_vlan' not in kwargs:
        raise ValueError("origin_vlan is  mandatory parameter!\n")
    origin_vlan = kwargs.pop('origin_vlan')

    if 'timeout' in kwargs:
        timeout = kwargs.get('timeout')
    else:
        timeout = 60 * 2
    
    pb_uniq_id = pb._resource.get_uniq_id()
    pb_sw_obj  = pb_kwargs.get('sw_obj')
    vlan_data = origin_vlan.get(pb_uniq_id)
    vlan_data['sw_obj'] = pb_sw_obj

    if not master.va_check_ha_is_master() and \
        pb.va_check_ha_is_master():
        if not pb.va_do_ha_failover():
            return False

        for dev_obj in [master, pb]:
            times = 1
            sleeptime = 10
            is_ready = dev_obj.va_check_ha_ready()
            while not is_ready and times <= 30:
                logger.info('Sleeping {} seconds to wait'.format(sleeptime))
                time.sleep(sleeptime)
                is_ready = dev_obj.va_check_ha_ready()
                times += 1

            if not is_ready:
                return False

    if not va_update_ha_vlan(**vlan_data):
        return False

    if pb.va_show_ha().get('HA Mode') == 'ON':
        if not pb.va_remove_ha(*args, **pb_kwargs):
            clean_status = False

        if not pb.va_delete_db():
            clean_status = False
    
        pb.va_reboot(reconnect_delay=timeout)

    if master.va_show_ha().get('HA Mode') == 'ON':
        if not master.va_remove_ha(*args, **master_kwargs):
            clean_status = False

    logger.info('Successfully cleaned HA environment')
    return clean_status

def va_get_micro_vlan(*args, **kwargs):
    """
    API to get micro vlan
    param   : kwargs : dict
    example : va_get_micro_vlan(**kwargs)
        kwargs = {
                  'sw_obj'  : vswitch object,
                  'dev_obj' : device object, such as traffic pc or director,
    return:
        :string : micro vlan id
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    if 'sw_obj' not in kwargs:
         raise ValueError("'sw_obj' is mandatory parameter!\n")
    
    if 'dev_obj' not in kwargs:
         raise ValueError("'dev_obj' is mandatory parameter!\n")
    
    sw_obj  = kwargs.get('sw_obj')
    dev_obj = kwargs.get('dev_obj')

    try:
        links = testdata.va_get_links()
    except:
        raise ValueError('The prameter testdata based on va_topo lib')

    micro_vlan = dict()
    for link_name, link_info in links.items():
        uniq_id = dev_obj._resource.get_uniq_id()
        for k, v in link_info.items():
            if k == uniq_id:
                vlan_port = v.get('interface').get('port_group')
                break 

    micro_vlan = sw_obj.get_vlan(vlan_port)

    logger.info('Micro vlan: {}'.format(micro_vlan))
    return micro_vlan

def va_send_and_verify_icmp(*args, **kwargs):
    """
    API to send traffic, capture packet and verify session related to ICMP
    param   : kwargs : dict
    example : va_send_and_verify_icmp(**kwargs)
        kwargs = {
                  'traffic_data' : {
                                    'client'    : pc1,
                                    'server'    : pc2,
                                    'src_intf'  : 'eth1',
                                    'dest_intf' : 'eth1',
                                    'size'      : 64,
                                    'count'     : 5,
                                    more parameters refer to Icmp,
                                   },
                  'tcpdump_data' : {
                                    'expr'      : expression to match packets,
                                    'host'      : 15.15.15.2,
                                    'intf'      : 'eth4',
                                    more parameters refer to start_tcpdump and 
                                    check_tcpdump,
                                   },
                  'session_data' : {
                                    'policy'    : 'test_pol',
                                    more parameters refer to va_verify_session,
                                   }
                     'dev_obj'   : dir_1,
    return:
        :bool - True on success or False on failure:
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    if 'traffic_data' not in kwargs or \
        'session_data' not in kwargs:
        raise ValueError('traffic_data and session_data are \
mandatory parameters!\n')

    traffic_data = kwargs.get('traffic_data')
    session_data = kwargs.get('session_data')

    if 'dev_obj' not in kwargs:
        raise ValueError('dev_obj is mandatory parameter!\n')
    dev_obj = kwargs.get('dev_obj')

    if 'client' not in traffic_data or    \
        'server' not in traffic_data or   \
        'src_intf' not in traffic_data or \
        'dest_intf' not in traffic_data:
        raise ValueError('client, server, src_intf and dest_intf are \
mandatory parameters!\n')

    client = traffic_data.get('client')
    server = traffic_data.get('server')
    src_intf  = traffic_data.get('src_intf')
    dest_intf = traffic_data.get('dest_intf')
    client_ip = client.get_ip(src_intf)
    server_ip = server.get_ip(dest_intf)
    
    tcpdump_data = None
    if 'tcpdump_data' in kwargs:
        tcpdump_data = kwargs.get('tcpdump_data')
        if 'intf' not in tcpdump_data:
            raise ValueError('intf is mandatory parameter!\n')
        intf = tcpdump_data.get('intf')

        if 'expr' in tcpdump_data:
            expr = tcpdump_data.get('expr')
        else:
            expr = '{}\s+>\s+{}:\s+ICMP echo request'.format(client_ip, server_ip)

    icmp_obj = Icmp(**traffic_data)
    if tcpdump_data is not None:
        packets_file, pid, process_file = server.start_tcpdump(intf=intf)

    if packets_file is None:
        return False

    dev_obj.va_clear_session()
    try:
        icmp_obj.start(**traffic_data)
    except ValueError as e:
        logger.error(e)
        logger.debug('Start to clean traffic since got exception')
        icmp_obj.stop()
        return False
        
    session = dev_obj.va_get_session()
    icmp_obj.stop()

    if tcpdump_data is not None:
        time.sleep(2)
        if not server.stop_tcpdump(pid, process_file):
            return False
        if not server.check_tcpdump(packets_file, expr, **tcpdump_data):
            return False

    session_data['proto'] = 'icmp'
    session_data['session'] = session
    if not dev_obj.va_verify_session(**session_data):
        return False

    del session_data['session']
    return True

def va_send_and_verify_ftp(*args, **kwargs):
    """
    API to send traffic and verify session related to FTP
    param   : kwargs : dict
    example : va_send_and_verify_ftp(**kwargs)
        kwargs = {
                  'traffic_data' : {
                                    'client'    : pc1,
                                    'server'    : pc2,
                                    'dest_intf' : 'eth1',
                                    more parameters refer to Icmp,
                                   },
                  'session_data' : {
                                    'policy'    : 'test_pol',
                                    more parameters refer to va_verify_session,
                                   }
                     'dev_obj'   : dir_1,
    return:
        :bool - True on success or False on failure:
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    if 'traffic_data' not in kwargs or \
        'session_data' not in kwargs:
        raise ValueError('traffic_data and session_data are \
mandatory parameters!\n')

    traffic_data = kwargs.get('traffic_data')
    session_data = kwargs.get('session_data')

    if 'dev_obj' not in kwargs:
        raise ValueError('dev_obj is mandatory parameter!\n')
    dev_obj = kwargs.get('dev_obj')

    dev_obj.va_clear_session()
    ftp_obj = Ftp(**traffic_data)
    try:
        ftp_obj.start(**traffic_data)
    except ValueError as e:
        logger.error(e)
        logger.debug('Start to clean traffic since got exception')
        ftp_obj.stop()
        return False

    session = dev_obj.va_get_session()

    times = 1
    session_data['proto']  = 'ftp'
    data_session_before = dev_obj.va_get_data_session(**session_data)
    time.sleep(1)
    data_session_after  = dev_obj.va_get_data_session(**session_data)
    is_increment = dev_obj.va_check_session_packets_increment(data_session_before, 
        data_session_after)
    while times <= 3 and not is_increment:
        logger.info('Retry {} times to check if session packet increment'.format(times))
        time.sleep(1)
        data_session_after  = dev_obj.va_get_data_session(**session_data)
        is_increment = dev_obj.va_check_session_packets_increment(data_session_before, 
            data_session_after)
        times +=1

    ftp_obj.stop()

    if not is_increment:
        return False

    session_data['session'] = session
    if not dev_obj.va_verify_session(**session_data):
        return False

    del session_data['session']
    return True

def va_send_and_verify_tftp(*args, **kwargs):
    """
    API to send traffic and verify session related to FTP
    param   : kwargs : dict
    example : va_send_and_verify_tftp(**kwargs)
        kwargs = {
                  'traffic_data' : {
                                    'client'    : pc1,
                                    'server'    : pc2,
                                    'dest_intf' : 'eth1',
                                    more parameters refer to Icmp,
                                   },
                  'session_data' : {
                                    'policy'    : 'test_pol',
                                    more parameters refer to va_verify_session,
                                   }
                     'dev_obj'   : dir_1,
    return:
        :bool - True on success or False on failure:
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    if 'traffic_data' not in kwargs or \
        'session_data' not in kwargs:
        raise ValueError('traffic_data and session_data are \
mandatory parameters!\n')

    traffic_data = kwargs.get('traffic_data')
    session_data = kwargs.get('session_data')

    if 'dev_obj' not in kwargs:
        raise ValueError('dev_obj is mandatory parameter!\n')
    dev_obj = kwargs.get('dev_obj')
    dev_obj.va_clear_session()
    tftp_obj = Tftp(**traffic_data)
    try:
        tftp_obj.start(**traffic_data)
    except ValueError as e:
        logger.error(e)
        logger.debug('Start to clean traffic since got exception')
        tftp_obj.stop()
        return False

    session = dev_obj.va_get_session()

    times = 1
    session_data['proto']  = 'tftp'
    data_session_before = dev_obj.va_get_data_session(**session_data)
    time.sleep(1)
    data_session_after  = dev_obj.va_get_data_session(**session_data)
    is_increment = dev_obj.va_check_session_packets_increment(data_session_before, 
        data_session_after)
    while times <= 6 and not is_increment:
        logger.info('Retry {} times to check if session packet increment'.format(times))
        time.sleep(1)
        data_session_after  = dev_obj.va_get_data_session(**session_data)
        is_increment = dev_obj.va_check_session_packets_increment(data_session_before, 
            data_session_after)
        times +=1

    tftp_obj.stop()

    if not is_increment:
        return False

    session_data['session'] = session
    if not dev_obj.va_verify_session(**session_data):
        return False

    del session_data['session']
    return True

def va_compare_config_sync_checksum(*args, **kwargs):
    """
    API to compare sync checksum of config of pb with master
    param   : kwargs : dict
              master : device obj, 
              pb     : device obj, support a list of device object 
    return:
        :bool - True on success or False on failure:
    example : va_compare_config_sync_checksum(master=dir_1, pb=[dir_2, dir_3])
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
    if 'master' not in kwargs or 'pb' not in kwargs:
        raise ValueError("master and pb are mandatory parameter!\n")
    master = kwargs.get('master')
    pb_list     = kwargs.get('pb')
    if not isinstance(pb_list, list):
        pb_list = [pb_list]

    succeed = True
    master_uniq_id  = master._resource.get_uniq_id()
    master_checksum = master.va_get_config_sync_checksum()
    for name, checksum in master_checksum.items():
        for pb in pb_list:
            pb_checksum = pb.va_get_config_sync_checksum()
            pb_uniq_id  = pb._resource.get_uniq_id()
            if pb_checksum.get(name) != checksum:
                logger.error('Mismatched checksum: {}: {}, {}: {}'.format(master_uniq_id, 
                    checksum, pb_uniq_id, pb_checksum.get(name)))
                succeed = False

    if not succeed:
        logger.error('Failed to compare checksum of config')
        return False

    logger.info('Succeed to compare checksum of config')
    return True

def va_get_traffic_interface_info(*args, **kwargs):
    """
    API to get interface info of traffic device
    return: a dict
    {'pc1': {'eth1': 
                    {
                     'name': 'eth1', 
                     'vlan': 3002, 
                     'vswitch': 'vSwitch2', 
                     'hyp_visor': 'hvisor_1', 
                     'port_group': 'vlan-3002'
                    }, 
             'eth2': 
                    {
                     'name': 'eth2', 
                     'vlan': 4000, 
                     'vswitch': 'vSwitch2', 
                     'hyp_visor': 'hvisor_1', 
                     'port_group': 'vlan-4000'
                    }
            },
     'pc2': {'eth1': 
                    {
                     'name': 'eth1', 
                     'vlan': 3003, 
                     'vswitch': 'vSwitch2', 
                     'hyp_visor': 'hvisor_1', 
                     'port_group': 'vlan-3003'
                    }, 
             'eth2': 
                    {
                     'name': 'eth2', 
                     'vlan': 4001, 
                     'vswitch': 'vSwitch2', 
                     'hyp_visor': 'hvisor_1', 
                     'port_group': 'vlan-4001'
                    }
            }
    }
    example : va_get_traffic_interface_info()
    """
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

    traffic_vlan = dict()
    try:
        links = testdata.va_get_links()
    except:
        raise ValueError('The prameter testdata based on va_topo lib')

    for link_name, link_info in links.items():
        if 'HA' in link_name:
            continue
        for dev_name, dev_info in link_info.items():
            if dev_name.split('_')[0] in ['dir', 'ep', 'cp', 'epi']:
                continue
            tmp = dict()
            if dev_name not in traffic_vlan:
                traffic_vlan[dev_name] = dict()
            for name, info in dev_info.items():
                if name == 'interface':
                    intf_name = info['name']
                    for x in ['name', 'port_group', 'vlan', 'vswitch']:
                        tmp[x] = info[x]
                elif name == 'hyp_visor':
                    tmp[name] = info['uniq_id']
            traffic_vlan[dev_name][intf_name] = tmp

    for dev_name, vlan_info in traffic_vlan.items():
        for intf_name, intf_info in vlan_info.items():
            for name, info in intf_info.items():
                if name == 'port_group':
                    pg_name = info
                    sw_name = intf_info['vswitch']
                    hv_name = intf_info['hyp_visor']
                    if hv_name in builtins.__dict__:
                        sw_obj = builtins.__dict__.get(hv_name).get(sw_name)
                    else:
                        raise ValueError('Not found {} object'.format(sw_name))
                    intf_info['vlan'] = sw_obj.get_vlan(pg_name)

    logger.info('Traffic interface info: {}'.format(traffic_vlan))
    return(traffic_vlan)

def va_login_with_specific_user(**kwargs) :
    '''
    login device with the other user then invokes all feature methods dynamically,
    return value is new device object and access object, user can call va_disconnect
    to stop the session.
    Args:
        **kwargs (dict) :
        'user' : {
            'name' : user name (str)
            'password' : password (str)
            }
        }
    Returns: Tuple, ndevobj,devaccobj

    Examples: ndevobj,devaccobj = \
              va_login_with_specific_user(**{'user':{'name':'xiaoping','password':'vArmour123'}})
              ndevobj.va_disable_paging()
              devaccobj.disconnect()
    '''
    logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
    devobj = kwargs.get('devojb',dir_1)
    ip = devobj._resource.get_mgmt_ip()
    logger.info('Login device {} with accout {}'.format(ip,\
                            kwargs.get('user').get('name')))
    devobj._resource.set_terminal_session(None)
    devaccobj = VaAccess(devobj._resource,**kwargs)
    devaccobj._resource.set_access(None)
    ndevobj = Controller(devaccobj._resource)
    ndevobj.va_disable_paging()
    return ndevobj,devaccobj