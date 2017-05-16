"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

System abstracts system related features. A superset of features apply
to the product 'dir', while a subset of features apply to other products
- cp, ep, epi. It inherits from class VaSystem, where all the common
features are implemented.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import sys
import re
import copy
import time

from feature.common import VaFeature
from feature import logger

proto_map = {
    'icmp'    : 1,
    'ftp'     : 6,
    'ftp-data': 6,
    'http'    : 6,
    'ssh'     : 6,
    'telnet'  : 6,
    'dhcp'    : 17,
    'tftp'    : 17,
}

port_map = {
    'ftp'      : 21,
    'ftp-data' : 20,
    'http'     : 80,
    'ssh'      : 22,
    'telnet'   : 23,
    'dhcp'     : 67,
    'tftp'     : 69,
}

class VaFlow(VaFeature):
    """
    System implements methods to configure or view the flow related
    features.
    """
    def va_get_session(self, *args, **kwargs):
        """
        API to get flow sessions
        param     : kwargs : dict
            kwargs = {
                    'dev_id'    : device id,
                    'proto'     : protocol
                    'dst_ip'    : destination IPv4 address,
                    'app_id'    : matching application id,
                    'intf'      : matching interface,
                    'policy_id' : matching policy index,
                    'segment_id': matching segment id,
                    'gt_pkt'    : matching pkt cnt greater than value
                    'lt_pkt'    : matching pkt cnt less than value,
                }    
        example :
                    va_get_session_id(**kwargs)
                    va_get_session(dev_id=1)
                    va_get_session(proto='any')
                    va_get_session(dst_ip='15.15.15.1')
                    va_get_session(app_id='--')
                    va_get_session(policy_id='1')
                    va_get_session(segment_id='3000')
                    va_get_session(gt_pkt='0')
                    va_get_session(lt_pkt='5')
                    va_get_session(epi='2-6')
        return: session or None
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        times = 1
        session = ""
        sleeptime = 0.5
        max_times = 3
        if 'is_fail' in args:
            max_times = 1

        cmd = 'show session '
        if 'dev_id' in kwargs:
            dev_id = kwargs.get('dev_id')
            cmd = 'show device {} session '.format(dev_id)

        if 'proto' in kwargs:
            proto = kwargs.get('proto')
            cmd += 'match protocol {}'.format(proto)
        elif 'dst_ip' in kwargs:
            dst_ip = kwargs.get('dst_ip')
            cmd += 'match dst-ip {}'.format(dst_ip)
        elif 'app_id' in kwargs:
            app_id = kwargs.get('app_id')
            cmd += 'match app-id {}'.format(app_id)
        elif 'intf' in kwargs:
            intf = kwargs.get('intf')
            cmd += 'match interface {}'.format(intf)
        elif 'policy_id' in kwargs:
            policy_id = kwargs.get('policy_id')
            cmd += 'match policy {}'.format(policy_id)
        elif 'segment_id' in kwargs:
            segment_id = kwargs.get('segment_id')
            cmd += 'match segment-id {}'.format(segment_id)
        elif 'gt_pkt' in kwargs:
            gt_pkt = kwargs.get('gt_pkt')
            cmd += 'match pkt-cnt gt {}'.format(gt_pkt)
        elif 'lt_pkt' in kwargs:
            lt_pkt = kwargs.get('lt_pkt')
            cmd += 'match pkt-cnt lt {}'.format(lt_pkt)
        elif 'epi' in kwargs:
            epi = kwargs.get('epi')
            cmd += 'match epi {}'.format(epi)

        if cmd.strip().endswith('session'):
            cmd += 'match protocol any'

        session = self._access.va_cli(cmd)
        pattern = re.compile(r'(\d+\.){3}\d+')
        ses_match = pattern.search(session)
        while times <= max_times and ses_match is None:
            logger.info("\nRetry to get session for the %d time\n "%times)
            session = self._access.va_cli(cmd)
            ses_match = pattern.search(session)
            time.sleep(sleeptime)
            times += 1
        if ses_match is not None:
            logger.info("Succeeded to get sessions\n")
        return session

    def va_check_session(self, data=None, *args):
        """
        method to match a bunch of keyswords related to session output. The
        session output is part of the data. Look at the following data dict
        for the valid keywords. data should have a mandatory key - session,
        which is the session output. other keywords are optional.

        {
            'app': '--',
            'flag': '0x00c00004',
            'id': '0x5000100000008',
            'in_dst_ip': '152.32.13.174',
            'in_dst_port': '10001',
            'in_intf': 'reth0',
            'in_micro_vlan': '1',
            'in_packets': '213',
            'in_phy_intf': '(xe-2/0/2)',
            'in_src_ip': '152.16.13.174',
            'in_src_port': '1087',
            'out_dst_ip': '152.16.13.174',
            'out_dst_port': '1087',
            'out_intf': 'reth1',
            'out_micro_vlan': '1',
            'out_packets': '0',
            'out_phy_intf': '(xe-2/0/3)',
            'out_src_ip': '152.32.13.174',
            'out_src_port': '10001',
            'policy': 'Any',
            'proto': '17',
            'state': '-1--1',
            'time': '1769',
            'vsys_id': '1'
        }

        raises:
            :ValueError: if data does not have session defined

        returns:
            :True|False (bool): True if match succeeds else False
        """
        found_match = False
        match_counter = 0
        most_match_session = dict()
        failed_in_most_match = None

        output = data.get('session')
        if not output:
            raise ValueError

        data.pop('session')

        session_stats = self._va_parse_session(output)

        if 'data_session' in args:
            in_ip = data.pop('in_dst_ip')
            out_ip = data.pop('out_dst_ip')
            data['in_dst_ip'] = data.pop('in_src_ip')
            data['in_src_ip'] = in_ip
            data['out_dst_ip'] = data.pop('out_src_ip')
            data['out_src_ip'] = out_ip

        for device in session_stats:
            if found_match:
                break
            for active_sessions in session_stats.get(device):
                if found_match:
                    break
                for session in active_sessions.get('sessions'):
                    match, no_matches, failed = self._va_check_single_session(
                                            data, session
                                        )

                    if no_matches > match_counter:
                        match_counter = no_matches
                        most_match_session = session
                        failed_in_most_match = failed

                    if match:
                        found_match = True
                        break
                    else:
                        continue

        if not found_match:
            logger.debug('Expected match session info:\n%s' % data)
            logger.debug("failed keywords: {}".format(failed_in_most_match))
            logger.debug("session with most matches: {}"
                        .format(most_match_session))
            logger.error("session match failed!")

        logger.info("session match succeed!")
        return found_match

    def _va_check_single_session(self, data, session):
        """
        helper method to match the keyword based values in data to that of
        session

        args:
            :data (dict): dict of valid keywords aand their values
            :session (dict): parsed single session from the session output

        returns:
            :True|False, no_of_matches, failed matches (tup): tuple of True
             or False and no of matches
        """
        match = True
        no_matches = 0
        failed = list()

        for keyword in data:
            if str(data.get(keyword)) == session.get(keyword):
                no_matches += 1
            else:
                match = False
                failed.append(keyword)

        return match, no_matches, failed

    def _va_parse_session(self, output=None):
        """
        helper method to parse the session output and return the python form
        which will be convenient to use.

        sample cli output: (show session match protocol any)

        <Dev ID: 1>
        Active Sessions (DEV: 1) : 0 (0)
        -----------------------------------------------------------
        -----------------------------------------------------------
        <Dev ID: 2>
        Active Sessions (DEV: 423801C4-CA6D-BAE4-89EA-1F15FEAC92DD) : 1 (1)
        -----------------------------------------------------------
        id 0x6020000000007c0, vsys id 1, policy p1, flag 0x21c004a4
          proto 1   time    1  App: --   State: -1--1  segment: 20
          i: 603.1 5.5.5.2, 61 -> 5.5.5.3, 17436  pkts: 1
          o: 603.2 5.5.5.2, 61 <- 5.5.5.3, 17436  pkts: 1
        -----------------------------------------------------------

        parsed output:

        {'1': [{'Active_Sessions': '0 (0)', 'DEV': '1', 'sessions': []}],
         '2': [{'Active_Sessions': '14 (14)',
                'DEV': '423801C4-CA6D-BAE4-89EA-1F15FEAC92DD',
                'sessions': [{'app': '--',
                              'in_dst_ip': '5.5.5.3',
                              'out_dst_ip': '5.5.5.3',
                              'in_dst_port': '17436',
                              'out_dst_port': '17436',
                              'flag': '0x21c004a4',
                              'id': '0x6020000000007c0',
                              'in_intf': '603',
                              'out_intf': '603',
                              'in_micro_vlan': '1',
                              'out_micro_vlan': '2',
                              'in_packets': '1',
                              'out_packets': '1',
                              'policy': 'p1',
                              'proto': '1',
                              'segment': '20',
                              'in_src_ip': '5.5.5.2',
                              'out_src_ip': '5.5.5.2',
                              'in_src_port': '61',
                              'out_src_port': '61',
                              'state': '-1--1',
                              'time': '1',
                              'vsys_id': '1'}]}]}

        kwargs:
            :output (str): session output

        returns:
            :parsed output (dict): please see above
        """
        stats = dict()

        devid = None
        session = None
        session_dict = None

        for line in output.splitlines():
            line = line.strip()

            if 'Dev ID' in line:
                devid = re.findall('\d+', line)[0]
                stats[devid] = list()
            elif line.startswith('Active Sessions'):
                prop = line.rpartition(':')
                no_sessions = prop[-1].strip()
                prop = [s.strip().replace(' ', '_', 1) for s in prop[:-1]]
                sessions_key, dev_id = prop[0].split(' ', 1)
                dev_id = re.sub('\(|\)', '', dev_id)
                dev_id_key, value = dev_id.split()

                session_dict = dict()
                session_dict[sessions_key] = no_sessions
                session_dict[dev_id_key.rstrip(':')] = value
                session_dict['sessions'] = list()
                session = dict()

                stats[devid].append(session_dict)

            elif line.startswith('id'):
                props = [prop.strip().rpartition(' ') for prop in
                         line.split(',')]
                for prop, sep, value in props:
                    session[prop.replace(' ', '_', 1)] = value
            elif line.startswith('proto'):
                props = line.split()
                for prop, value in zip(props[::2], props[1::2]):
                    session[prop.rstrip(':').lower()] = value

            elif line.startswith('i'):
                flow_spec = ['in', 'intf', 'micro_vlan', 'phy_intf', 'src_ip',
                             'src_port', 'dst_ip', 'dst_port', 'packets']

                self._va_extract_flow_props(line, flow_spec, session)

            elif line.startswith('o'):
                flow_spec = ['out', 'intf', 'micro_vlan', 'phy_intf',
                             'dst_ip', 'dst_port', 'src_ip', 'src_port',
                             'packets']

                self._va_extract_flow_props(line, flow_spec, session)

                session_dict['sessions'].append(session)
                session = {}

        return stats

    def _va_extract_flow_props(self, flow=None, spec=None, session=None):
        """
        helper method to parse, extract the flow properties for a session

        kwargs:
            :flow (str): cli output of the flow section
            :spec (list): properties of a flow
            :session (dict): session dict that is containing the keywords
        """
        props = [prop.rstrip(':,') for prop in flow.split()]
        props = [prop for prop in props if prop != '->' and
                 prop != '<-' and prop != 'pkts']

        props = props[1:]
        intf, vlan = props[0].split('.')
        props[0] = intf
        props.insert(1, vlan)

        tag = spec.pop(0)

        if len(props) < len(spec):
            spec.pop(2)

        for index, prop in enumerate(props):
            keytag = '_'.join((tag, spec[index]))
            session[keytag] = prop

    def va_verify_session(self, *args, **kwargs):
        """
        API to check flow session 
    
        param     : kwargs : dict
            kwargs = {
                    'session' : session_val,
                    'proto'   : 'icmp' | 'ftp',
                    'policy'  : 'test_pol',
                    more parameters refer to va_check_session,
                }    
        example :
                    va_check_session(**kwargs)

        return: True/False
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)   
        check_data = copy.copy(kwargs)

        if not 'session' in kwargs:
            session = self.va_get_session()
        else:
            session = kwargs.pop('session')
        check_data['session'] = session

        if not 'policy' in kwargs:
            check_data['policy'] = "test_pol"

        if 'proto' in kwargs:
            proto = kwargs.pop('proto')
            check_data['proto'] = proto_map.get(proto)

            if proto.upper() != 'ICMP':
                if proto.upper() == 'FTP-DATA':
                    check_data['in_src_port'] = port_map.get(proto)
                    check_data['out_dst_port'] = port_map.get(proto)
                else :
                    check_data['in_dst_port']  = port_map.get(proto)
                    check_data['out_src_port'] = port_map.get(proto)

        if 'is_fail' in args:
            if 'data_session' in args:
                return self.va_check_session(check_data,'is_fail','data_session')
            else:
                return self.va_check_session(check_data,'is_fail')
        if 'data_session' in args:
            return self.va_check_session(check_data,'data_session')
        else:
            return self.va_check_session(check_data)

    def va_check_session_packets_increment(self, session_before, session_after, 
        *args, **kwargs):
        """
        API to check if packets counter of data session increase
        param     : 'session_before', should be single data session before increment
                    'session_after', should be single data session after increment
                }    
        example :
                    va_check_session_packets_increment(session_before, session_after)
        returns:
            :True|False (bool): True on success, False on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        in_packets_before  = int(session_before.get('in_packets'))
        in_packets_after   = int(session_after.get('in_packets'))
        out_packets_before = int(session_before.get('out_packets'))
        out_packets_after  = int(session_after.get('out_packets'))
        if in_packets_before > in_packets_after or \
            out_packets_before > out_packets_after:
            logger.debug('In_packets:  {}, {}'.format(in_packets_before, in_packets_after))
            logger.debug('Out_packets: {}, {}'.format(out_packets_before, out_packets_after))
            logger.error('Packet counter of data session is not increasing!')
            return False

        logger.info('Packet counter of data session is increasing.')
        return True

    def va_get_data_session(self, *args, **kwargs):
        """
        API to get data session, not support multiple session at same time
    
        param     : kwargs : dict
            kwargs = {
                    'session' : session_val,
                    'proto'   : 'icmp' | 'ftp',
                    'policy'  : 'pol_test',
                    more parameters refer to _va_check_single_session,
                }    
        example :
                    va_get_session_id(**kwargs)
        return: a dict of session like this
        {'app': '--',
         'in_dst_ip': '5.5.5.3',
         'out_dst_ip': '5.5.5.3',
         'in_dst_port': '17436',
         'out_dst_port': '17436',
         'flag': '0x21c004a4',
         'id': '0x6020000000007c0',
         'in_intf': '603',
         'out_intf': '603',
         'in_micro_vlan': '1',
         'out_micro_vlan': '2',
         'in_packets': '1',
         'out_packets': '1',
         'policy': 'p1',
         'proto': '1',
         'segment': '20',
         'in_src_ip': '5.5.5.2',
         'out_src_ip': '5.5.5.2',
         'in_src_port': '61',
         'out_src_port': '61',
         'state': '-1--1',
         'time': '1',
         'vsys_id': '1',
        }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if not 'session' in kwargs:
            session = self.va_get_session()
        else:
            session = kwargs.pop('session')

        if not 'proto' in kwargs:
            proto_name = 'ftp'
        else:
            proto_name = kwargs.pop('proto').split('-')[0]

        if proto_name in ['ftp', 'tftp']:
            f = lambda x,y:x!=y
        else:
            f = lambda x,y:x==y

        if not 'policy' in kwargs:
            kwargs['policy'] = "pol_test"

        port  = port_map.get(proto_name)
        kwargs['proto'] = proto_map.get(proto_name)
        session_stats = self._va_parse_session(session)

        data_session = dict()
        for device in session_stats:
            for active_sessions in session_stats.get(device):
                for session in active_sessions.get('sessions'):
                    match, no_matches, failed = self._va_check_single_session(kwargs, session)
                    in_dst_port = int(session.get('in_dst_port'))
                    logger.debug('Session    : \n{}'.format(session))
                    logger.debug('Matched    : {}'.format(match))
                    logger.debug('Not Matched: {}'.format(no_matches))
                    logger.debug('Failed     : {}'.format(failed))
                    if len(failed) != 0:
                        match = True
                        for name in failed:
                            failed_name  = str(kwargs.get(name))
                            session_name = session.values()
                            if failed_name not in session_name:
                                match = False
                        if not match:
                            logger.error('Not matched: {}, {}'.format(failed_name, session_name))
                    if match:
                        if f(in_dst_port, port):
                            data_session = session
                            break
                    else:
                        continue
        
        logger.info('Data session: {}'.format(data_session))
        return data_session

    def va_clear_session(self):
        """
        API to clear session
        param      : None
        example    : va_clear_session()
        returns:
            :True|False (bool): True if success else False
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        times = 1
        sleeptime = 2
        self._access.va_cli('clear session')
        session = self.va_get_session('is_fail')
        pattern = re.compile(r'((\d+\.){3}\d+)')
        while pattern.search(session) is not None and times <= 6:
            time.sleep(sleeptime)
            logger.debug('Retry {} times to clear session'.format(times))
            self._access.va_cli('clear session')
            session = self.va_get_session('is_fail')
            times += 1

        if pattern.search(session) is not None:
            logger.error("Session can't be cleared")
            return False

        logger.info('Session are cleared')
        return True

