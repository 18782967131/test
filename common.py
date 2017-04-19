"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Common implements methods for linux configuration. It acts as a base class
and various distributions can be implemented as sub classes. They can inherit
common configuration mechanisms from this class and need to implement only
mechanisms that are specific to the distribution.

It inherits from the Feature class or the feature framework for the linux
product.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import ipaddress
import re
import os
import sys
import time

from vautils import logger
from ipaddress import AddressValueError, NetmaskValueError
from vautils.config.linux import ConfigUtil
from time import gmtime, strftime
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines

class Common(ConfigUtil):
    """
    Base class for the linux feature configuration on the remote
    vm's running linux.
    """
    def get_hostname(self):
        """
        method to get the hostname of the vm.

        Returns:
            :hostname (str): hostname of the vm
        """
        cmd = "hostname"
        result = self._access.exec_command(cmd)

        return result.rstrip()

    def show_interfaces_brief(self):
        """
        method to get brief info on the interfaces associated with
        a vm.
        """
        cmd = "ifconfig -a -s"
        output = self._access.exec_command(cmd)

        parsed = list()
        for line in output.splitlines()[1:]:
            line = line.strip()
            parsed.append(tuple(line.split()))

        return parsed

    def config_ip(self, address=None, interface=None):
        """
        method to configure an ip address for the specified
        interface on a linux device.

        Returns:
            :bool - True on success or False on failure:

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
            :ParamRequired: if interface is not provided
        """
        if not interface or interface == 'eth0':
            pass
            # TODO: raise ValueError

        try:
            configured = ipaddress.IPv4Interface(address)
        except (AddressValueError, NetmaskValueError):
            raise
        else:
            ip = str(configured.ip)
            mask = str(configured.netmask)
            cmd = self._config_ip_cmd(interface, ip, mask)
            self._access.exec_command(cmd)

        return self._verify_ip(interface, configured)

    def show_interface(self, interface=None):
        """
        method to get the interface configuration of a
        specified interface on a linux device. If interface
        is not specified return brief configuration of all
        interfaces.
        """
        if not interface:
            return self.show_interfaces_brief()

        cmd = "ifconfig {}".format(interface)
        output = self._access.exec_command(cmd)

        return self._parse_interface(output, interface)

    def unconfig_ip(self, address=None, interface=None):
        """
        method to unset the ip address for the specified
        interface.

        Returns:
            :bool - True on success or False on failure:

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
            :ParamRequired: if interface is not provided
        """
        if not interface or interface == 'eth0':
            pass
            # TODO: raise ParamRequired('address', 'interface')

        try:
            configured = ipaddress.IPv4Interface(address)
        except (AddressValueError, NetmaskValueError):
            raise
        else:
            ip = configured.with_prefixlen
            mask = str(configured.netmask)  # NOQA

            cmd = self._del_ip_cmd(interface, ip)
            self._access.exec_command(cmd)

        return (not self._verify_ip(interface))

    def _config_ip_cmd(self, interface=None, address=None, mask=None):
        """
        helper method to assemble an ifconfig method
        """
        cmd = "sudo ifconfig {} {} netmask {} up"\
              .format(interface, address, mask)

        return cmd

    def _del_ip_cmd(self, interface=None, address=None):
        """
        helper method to assemble an ip address delete command
        """
        cmd = "sudo ip addr del {} dev {}".format(address, interface)

        return cmd

    def _verify_ip(self, interface=None, config=None):
        """
        Helper method to compare ip address that is being
        configured and its actual set value.
        """
        output = self.show_interface(interface)
        logger.debug('Interface info: {}'.format(output))
        ip_addr = output[1][1].split(':')[1]

        if config and str(config.ip) == ip_addr:
            logger.info("ifconfig ip works")
            return True
        else:
            logger.info("ip address not configured")
            return False

    def get_ip(self, interface='eth1'):
        """
        Helper method to get ip address of interface.
        Returns:
            :str of an ip address on success or None on failure:
        """
        output = self.show_interface(interface)

        try:
            address = output[1][1].split(':')[1]
        except (IndexError) as e:
            return None

        try:
            configured = ipaddress.IPv4Interface(address)
        except (AddressValueError, NetmaskValueError) as e:  # NOQA
            logger.error("Not found ip address: {}".format(output))
            return None
        else:
            ip_addr = str(configured.ip)

        self._access.log_command("ipv4 address is {}".format(ip_addr))

        return ip_addr

    def get_ipv4_address(self, interface='eth1'):
        """
        Helper method to get ipv4 address of interface.
        Returns:
            :str of an ipv4 address on success or None on failure:
        """
        output = self.show_interface(interface)

        try:
            address = output[1][1].split(':')[1]
        except (IndexError) as e:
            return None

        try:
            configured = ipaddress.IPv4Interface(address)
        except (AddressValueError, NetmaskValueError) as e:  # NOQA
            logger.error("Not found ip address: {}".format(output))
            return None
        else:
            ip_addr = str(configured.with_prefixlen)

        self._access.log_command("ip address is {}".format(ip_addr))

        return ip_addr

    def get_mac_address(self, interface='eth1', style='linux'):
        """
        Helper method to get MAC address of interface.
        Returns:
            :str of an MAC address on success or None on failure
            :MAC address format is linux style by default like 00:00:0c:c0:ab:07
            :with varmour style which is like 0:0:c:c0:ab:7
        """
        output = self.show_interface(interface)

        try:
            mac_addr = output[0][3]
        except (IndexError) as e:
            return None

        self._access.log_command("MAC address is {}".format(mac_addr))

        if not style or style == 'linux':
            return mac_addr
        elif style == 'varmour':
            mac = mac_addr.split(':')
            new_mac = list()
            for i in mac:
                if i.startswith('0'):
                    i = i[1:]
                new_mac.append(i)
            new_mac = ':'.join(new_mac)
            return new_mac
        else:
            logger.error("Only 'linux' or 'varmour' style is supported for get_mac_address")
            return None

    def config_route(self, address=None, mask=None, gw=None):
        """
        method to configure an ip address for the specified
        interface.

        Returns:
            :bool - True on success or False on failure:

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
            :ParamRequired: if interface is not provided
        """
        if not address or not mask or not gw:
            pass
            # TODO: raise ParamRequired('address', 'interface')

        network_addr = "{}/{}".format(address, mask)

        try:
            configured = ipaddress.IPv4Network(network_addr)
            gw_addr = ipaddress.IPv4Address(gw)
        except (AddressValueError, NetmaskValueError):
            raise
        else:
            network = configured.network_address
            mask = configured.with_netmask.split('/')[1]

            cmd = self._route_cmd(network, mask, str(gw_addr))
            output = self._access.exec_command(cmd)  # NOQA

        return self._verify_route(configured, gw_addr)

    def _route_cmd(self, network=None, mask=None, gateway=None):
        """
        helper method to assemble an ip route add command
        """
        cmd = "sudo route add -net {} netmask {} gw {}"\
              .format(network, mask, gateway)

        return cmd

    def show_route(self):
        """
        method to parse the show route command on the device

        Returns:
            :list - parsed out as a list of route entries
        """
        cmd = "route"
        output = self._access.exec_command(cmd)

        return self._parse_route(output)

    def _parse_interface(self, output=None, interface=None):
        """
        helper method to parse the output of 'ifconfig eth'
        command.
        """
        lines = list()

        for line in output.splitlines():
            if line.startswith(interface):
                line = line[len(interface):]
            line = re.sub(':\s', ':', line)
            line = re.sub('\((\d+\.\d)+\s(\w+)\)', '\g<1>-\g<2>', line)
            props = line.split()
            lines.append(props)

        return lines

    def _verify_route(self, config=None, gateway=None):
        """
        Helper method to verify that a route exists on the
        device
        """
        routes = self.show_route()

        if not routes:
            return False

        for route in routes:
            if str(config.network_address) == route[0]\
                    and str(gateway) == route[1]:
                logger.info("route configured")
                return True
        logger.info("route does not exist")
        return False

    def _parse_route(self, output=None):
        """
        parse the output of 'route' command and each route
        entry is appended as a tuple to the list. The
        components that make up the entry are stored in the
        respective order within the tuple.

        Returns:
            :list of route entries

        ..note: can change to named tuple in future.
        """
        parsed = list()

        for line in output.splitlines():
            line = line.strip()
            if not line.startswith('Kernel') and\
               not line.startswith('Destination'):
                parsed.append(tuple(line.split()))

        return parsed

    def create_file(self, name='qatest.file', size=100, path=None,exec_type='sync'):
        """
        method to create a file using dd command on the host

        kwargs:
            :name (str): name of the file to be created
            :size (int): file size signifies multiple of a MB
            :path (str): path on the host where file is to be created
            :exec_type (str) :sync or async to create file

        returns:
            :3 element tuple of abs file path, file size, and md5sum
        """
        if not path:
            path = self.get_home_dir()
        if exec_type == 'async':
            exec_cmd = 'exec_background'
        else :
            exec_cmd = 'exec_command'

        path_info = self._access.exec_command("ls {}".format(path))
        if not path_info:
            self._access.exec_command('sudo mkdir -p {}'.format(path))

        rand_file = '{}/{}'.format(path,name)
        cmd = "sudo dd if=/dev/zero of={} bs=1048576 count={}"\
              .format(rand_file, size)

        if exec_type == 'async':
            pid, file = self.exec_background(cmd,redirect=True,search_full=True)
            return pid,file
        else :
            output = self._access.exec_command(cmd)
            if output:
                ls_cmd = "ls {}".format(rand_file)
                ls_output = self._access.exec_command(ls_cmd)
                if ls_output.splitlines()[0] == rand_file:
                    stat = self.get_file_stat(rand_file)
                    md5sum = self.get_md5sum(rand_file)

            return tuple((rand_file, stat[4], md5sum))

    def remove_file(self, file_res=None):
        """
        remove the file on the remote host

        kwargs:
            :file_res (str): abs path of the remote file
        """
        self._access.exec_command("sudo rm -f {}".format(file_res))

    def get_file_stat(self, file_res=None):
        """
        compute the file stat of the file on the device.

        kwargs:
            :file_res (str): abs path of the remote file

        returns:
            :tuple of the components that are output by an ls command:
        """
        stat = self._access.exec_command("ls -l {}".format(file_res))
        return tuple(stat.rstrip().split())

    def get_md5sum(self, file_res=None):
        """
        compute the md5sum of the file on the device.

        kwargs:
            :file_res (str): abs path of the remote file

        returns:
            :md5sum of the file
        """
        output = self._access.exec_command("md5sum {}".format(file_res))
        md5sum = tuple(output.rstrip().split())
        return md5sum[0]

    def get_home_dir(self):
        """
        method to get the home directory of the user on the host

        returns:
            :output of echo $HOME as string:
        """
        output = self._access.exec_command('echo $HOME')
        return output.splitlines()[0]

    def exec_background(
        self,
        cmd=None,
        outfile='temp',
        redirect=False,
        outdir=None,
        search_expr=None,
        search_full=False
    ):
        """
        method to run the command as part of the process in the background.

        kwargs:
            :cmd (str): linux command to be run in the background
            :outfile (str):
            :redirect (bool):
            :search_expr (str):
            :search_full (bool) : True/False .The pattern is normally only matched against the process name.
                                When the value is False, the full command line is used

        returns:
            :pid (int): pid of the remote process
        """
        pid = None
        remote_loc = None
        
        if not cmd:
            pass
            # TODO: raise exception or warning

        if not self.check_cmd_existence(cmd.split(' ')[0]) or \
            not self.check_writable():
            return pid, remote_loc

        if not search_expr:
            search_expr = cmd
        
        if not outdir:
            outdir = self.get_home_dir()

        if redirect:
            uid = strftime("%H:%M:%S", gmtime()).replace(':', '')
            file_name = '.'.join(('_'.join((outfile, uid)), 'txt'))
            remote_loc = '{}/{}'.format(outdir, file_name)
            bg_cmd = "nohup {} > {} 2>&1 &".format(cmd, remote_loc)
        else:
            bg_cmd = "nohup {} 2>&1 &".format(cmd)

        output = self._access.exec_command(bg_cmd)

        if output is False:
            logger.error("command: {} failed!".format(cmd))
        else:
            pass

        pid = self.get_pid(search_expr,search_full)
        if not pid:
            pass
            # TODO: raise or log warn

        return pid, remote_loc

    def get_pid(self, search_expr=None,search_full=False):
        """
        method to get the pid of the remote process running in the
        background.

        kwargs:
            :search_expr (str): search criteria for the process
            :search_full (bool): True/False, if the value is True, it will match full command of process else
             only matched against the process name
        Return :  int : pid

        Examples :
            get_pid(search_expr='tcpdump')
            get_pid(search_expr='/usr/bin/dbus-daemon',search_full=True)
        """
        if search_full :
            output = self._access.exec_command("ps ax | pgrep -f '{}'"
                                           .format(search_expr))
        else :
            output = self._access.exec_command("ps ax | pgrep '{}'"
                                           .format(search_expr))

        return output if output else False

    def get_remote_file(self, local=None, remote=None, rem_remote=True):
        """
        method to get the file where the remote process redirected
        it's output. It will copy to the local location under /tmp

        kwargs:
            :local (str): abs path name of file on client
            :remote (str): abs path name of file on server
            :rem_remote (bool): remove remote file on server
        """
        if not local:
            if os.path.exists(os.path.join(os.sep, 'tmp')):
                local = os.path.join(os.sep, 'tmp', os.path.basename(remote))

        self._access._shell.download(remote, local)

        if rem_remote:
            self.remove_file(remote)

    def load_file(self, process_output=None):
        """
        open the output file and assign it to the output attribute.

        returns:
            :process_output (str|io): redirected output of the
             process
        """
        if not process_output:
            process_output = self._remotefile

        output = open(process_output)

        return output

    def kill_background(self, pid=None, signal=2, **kwargs):
        """
        method to kill the process that is running remotely.

        kwargs:
            :pid (int): pid of the process to be killed
            :signal (int): signal type used by kill. Default - INT
        """
        if 'killall' in kwargs:
            kill_cmd = "killall {}".format(kwargs.get('killall'))
        else:
            kill_cmd = "kill -{} {}".format(signal, pid)
        output = self._access.exec_command(kill_cmd)

        return output

    def service_start(self, service=None):
        """
        start the service on the remote machine.

        kwargs:
            :service (str): name of the service daemon on the host
        """
        cmd = "sudo service {} start".format(service)

        out = self._access.exec_command(cmd)  # NOQA
        logger.debug('Service info: {}'.format(out))
        if not self.service_running(service):
            raise ValueError("{} not started!".format(service))   
        logger.info("successfully started")

    def service_stop(self, service=None):
        """
        stop the service on the remote machine.

        kwargs:
            :service (str): name of the service daemon on the host
        """
        cmd = "sudo service {} stop".format(service)

        out = self._access.exec_command(cmd)  # NOQA
        logger.debug('Service info: {}'.format(out))
        if self.service_running(service):
            raise ValueError("{} not stopped!".format(service))   
        logger.info("successfully stopped")

    def service_running(self, service=None):
        """
        check if the service is running on the remote machine.

        kwargs:
            :service (str): name of the service daemon on the host
        """
        executable_service = service
        if service == 'tftpd-hpa':
            service = 'tftpd'
            executable_service = 'in.{}'.format(service)
        elif service == 'bind9':
            service = 'named'
            executable_service = '{}'.format(service)

        executables = ['/usr/bin/{}'.format(executable_service),
                       '/usr/sbin/{}'.format(executable_service)]
        out_list = list()
        ps_cmd = "ps ax | grep {} |grep -v grep".format(service)
        if service == 'nfs-kernel-server' :
            executable_service = 'Started NFS server and services'
            ps_cmd = '/etc/init.d/{} status'.format(service)

        ps_output = self._access.exec_command(ps_cmd)
        logger.debug('Service info: {}'.format(ps_output))
        if not ps_output:
            logger.error('Service "{}" is not running!'.format(service))
            return False
        if  service == 'nfs-kernel-server' :
            if re.search(r'%s' % executable_service, ps_output.splitlines()[-1]) is not None :
                logger.info('Service is running: \n{}'.format(ps_output))
                return True
            else :
                logger.error('Service "{}" is not running!'.format(service))
                return False
        else :
            for line in ps_output.splitlines():
                line = line.rstrip()
                cmd_pos = line.find(ps_cmd)
                if cmd_pos >= 0:
                    ps_out = line[0:cmd_pos].split()
                    ps_out.append(line[cmd_pos:])
                else:
                    ps_out = line.split()
                out_list.append(tuple(ps_out))

            for output in out_list:
                for service in executables:
                    if service in output:
                        logger.info('Service is running: \n{}'.format(ps_output))
                        return True

    def start_tcpdump(self, intf='eth1', *args, **kwargs):
        """
        method used to start the tcpdump process in the background.
        param      : intf   : interface name
                   : kwargs : dict
        example    : start_tcpdump(eth1, **kwargs)
                     kwargs = {
                       'host' : host to match packets
                     }
        return: packets_file, pid and process_file on success, None,
            None and None on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if not self.check_writable():
            return None, None, None

        cmd = 'tcpdump -nev -i {}'.format(intf)
        uid = time.strftime("%H:%M:%S", time.gmtime()).replace(':', '')
        packets_file = '/tmp/tcpdump_packets_{}.txt'.format(uid)

        if 'host' in kwargs:
            host = kwargs.get('host')
            cmd = '{} host {}'.format(cmd, host)
        elif 'option' in kwargs:
            option = kwargs.get('option')
            cmd = '{} {}'.format(cmd, option)

        cmd = '{} -w {} -l -t'.format(cmd, packets_file)
        pid, process_file = self.exec_background(cmd, 'tcpdump', True, search_expr='tcpdump')
        logger.info("PID: {}".format(pid))

        if not pid:
            logger.error("Failed tcpdump.")
            self.remove_file(process_file)
            return None, None, None

        logger.info("Successfully started tcpdump")
        return packets_file, pid, process_file

    def stop_tcpdump(self, pid, process_file):
        """
        method used to stop the tcpdump process in the background.
        param      : pid   : process id
                   : process_file : process file
        example    : stop_tcpdump(pid, process_file)
        return: True on success, False on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        self.kill_background(pid)
        self.remove_file(process_file)
        search_expr = 'tcpdump | grep {}'.format(pid)
        if self.get_pid(search_expr):
            logger.error("Can not stop tcpdump.")
            return False

        logger.info("Successfully stopped tcpdump")
        return True

    def check_tcpdump(self, file, expr, *args, **kwargs):
        """
        method to check traffic packets via tcpdump
        param      : expr   : expression to match traffic packet
                   : file   : packets file
                   : kwargs : dict
        example    : check_tcpdump(file, expr, **kwargs)
                     kwargs = {
                      'exact' : 3, expect to receive packets number
                      'fuzzy' : 3-5, expect to receive packets number
                     }
        return: True on success or False on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd = "tcpdump -nev -r {}".format(file)
        shell = self._access.shell
        packets_info = shell(cmd)
        shell("sudo rm -f {}".format(file))
        if 'packets_info' not in dir():
            logger.error('Failed to query traffic packets')
            return False

        got_packet_count = 0
        logger.info('Packets info: {}'.format(packets_info))
        for info in packets_info[0].split('\n'):
            info = info.strip()
            if re.search(expr, info) is not None:
                got_packet_count += 1
        logger.info('Received packets number: {}'.format(got_packet_count))

        if got_packet_count == 0:
            logger.info('Expression: {}'.format(expr))
      
        if 'exact' in kwargs:
            packet_count = int(kwargs.get('exact'))
            if packet_count != got_packet_count:
                logger.error('Expected value: {}, actual value: {}'.format(
                    packet_count, got_packet_count))
                return False
        elif 'fuzzy' in kwargs:
            packet_count = kwargs.get('fuzzy')
            if '-' not in packet_count:
                logger.error('Invalid "fuzzy" parameter, expected value \
like this: 2-5')
                return False

            packet_count_min = int(packet_count.split('-')[0])
            packet_count_max = int(packet_count.split('-')[1])
            if packet_count_min > packet_count_max:
                logger.error('Invalid parameter: {}, the second parameter \
should be lager than first'.format(packet_count))
                return False

            if packet_count_min > got_packet_count or \
                            packet_count_max < got_packet_count:
                logger.error('Expected value: {}-{}, actual value: {}'.format(
                    packet_count_min, packet_count_max, got_packet_count))
                return False
        else:
            if got_packet_count == 0:
                logger.error('Expected to receive at least one traffic packet')
                return False

        logger.info('Succeed to check traffic packets')
        return True

    def check_cmd_existence(self, cmd):
        """
        method to check if command existence
        param      : cmd : command
        example    : check_cmd_existence('lftp')
        return: True on success or False on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        cmd_info = self._access.shell("whereis {}".format(cmd))
        cmd_info = cmd_info[0].strip('\n').split(':')
        if len(cmd_info[1]) == 0:
            logger.error('Not found command: {}'.format(cmd))
            return False

        return True

    def exec_command(self,cmd):
        output = self._access.exec_command(cmd)
        logger.info('CMD: {}'.format(cmd))
        logger.info('CMD OUTPUT: {}'.format(output))
        return output

    def check_writable(self, file=None):
        """
        method to check if file system writable
        param      : file : file to check
        example    : check_writable('/tmp/test.file')
        return: True on success or False on failure
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if file is None:
            file = '/tmp/test.file'
        cmd = 'sudo dd if=/dev/zero of={} bs=1048576 count=1'.format(file)
        output = self._access.shell(cmd)
        pattern = re.compile(r'cannot touch|Read-only|No space left on device')
        if pattern.search(output[0], re.I|re.M) is not None:
            logger.error('File system is not writable or No space left on device!')
            return False

        self.remove_file(file)
        return True

    def get_version(self):
        """
        method to get version of operation system
        example    : get_version()
        return: a tuple of version included os name and os version
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        version = None
        cmd = 'cat /etc/issue'
        output = self._access.shell(cmd)
        pattern = re.compile(r'(Ubuntu\s+\d+\.\d+)')
        match_result = pattern.search(output[0])
        if match_result is not None:
            version_info = match_result.group(1)
        version_info = version_info.split(' ')
        os_name = version_info[0]
        os_version = version_info[1]
        logger.info('OS: {}, version: {}'.format(os_name, os_version))
        return (os_name, os_version)

    def receive_multicast(self, *args, **kwargs):
        """
        method to recieve multicast traffic on server
        param      : kwargs     : dict
                     mulcast_ip : multicast ip address, '224.0.0.4' by default
                     interface  : route device, 'eth1' by default
                     interval   : seconds between periodic bandwidth reports, 1 by default
        return: pid and process_file on success, False and error message on failure
        example    : start_multicast()
                   : start_multicast(mulcast_ip='224.0.0.4', interface='eth1')
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        mulcast_ip = kwargs.get('mulcast_ip', '224.0.0.4')
        interface = kwargs.get('interface', 'eth1')
        interval = kwargs.get('interval', 1)

        cmd_route = "route add -net {} netmask 255.255.255.255 dev {}".format(mulcast_ip, \
            interface)
        output = self._access.shell(cmd_route)
        if re.search(r'Unknown host|No such device', output[0]) is not None:
            logger.error("Failed to add route")
            return(False, output[0])

        cmd_iperf = "iperf -s -u -B {} -i {}".format(mulcast_ip, interval)
        pid, process_file = self.exec_background(cmd_iperf, 'iperf_server', True, search_expr='iperf')
        logger.info("PID: {}".format(pid))

        if not pid:
            logger.error("Failed multicast!")
            self.remove_file(process_file)
            return(False, "Failed to call exec_background on server")

        cmd_cat = "cat {}".format(process_file)
        output = self._access.shell(cmd_cat)
        logger.debug('Multicast info: {}'.format(output[0]))
        reg_list = ['Server listening', 
            'Binding to local address\s+{}'.format(mulcast_ip), 
            'Joining multicast group\s+{}'.format(mulcast_ip), 
            'Receiving\s+(\d+)\s+byte\s+datagrams',
            'local\s+%s\s+port\s+(\d+)\s+connected\s+with\s+((\d+\.){3}\d+)\s+port\s+(\d+)' % (mulcast_ip)
        ]
        for reg in reg_list:
            if re.search(reg, output[0]) is None:
                logger.error('Failed to received multicast on server, \
expected expression: {}'.format(reg))
                return(False, output[0])

        logger.info("Successfully received multicast on server")
        return(pid, process_file)

    def stop_multicast(self, pid, process_file):
        """
        method used to stop the multicast process in the background.
        param      : pid   : process id
                   : process_file : process file
        return: a tuple of Ture and None on success, False and error message on failure
        example    : stop_multicast(pid, process_file)
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        output = self.kill_background(pid)
        if re.search(r'No such process', output) is not None:
            return(False, output)

        self.remove_file(process_file)
        cmd_route = "route del dvmrp.mcast.net"
        output = self._access.shell(cmd_route)
        if re.search(r'Unknown host', output[0]) is not None:
            logger.error("Failed to del route")
            return(False, output[0])
        search_expr = 'iperf | grep {}'.format(pid)
        output = self.get_pid(search_expr)
        if output:
            logger.error("Can not stop multicast")
            return(False, output)

        logger.info("Successfully stopped multicast")
        return(True, None)

    def tcpreplay(self, *args, **kwargs):
        """
        method used to tcpreplay
        param      : kwargs    : dict
                   : src_net   : source subnet, 
                   : src_intf  : source interface, 
                   : dest_obj  : destination object, 
                   : dest_intf : destination interface, 
                   : path      : file path of traffic packet file, 
                   : infile    : traffic packet file, 
                   : pps|mbps  : Replay packets at a given packets/sec|Mbps, 
                                 fast as possible by default
        returns:
            :tuple - True and output on success or False and error message on failure:
        example    : tcpreplay(**kwargs)
            kwargs = {
                'infile'    : 'google.pcap',
                'src_net'   : '15.15.15.0/24',
                'dest_obj'  : pc2,
                'mbps'      : 3,
            }
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        if 'dest_obj' not in kwargs:
            raise ValueError('"dest_obj" is a mandatory parameter!')
        dest_obj = kwargs.get('dest_obj')

        if 'src_net' not in kwargs:
            raise ValueError('"src_net" is a mandatory parameter!')
        src_net = kwargs.get('src_net')

        if 'infile' not in kwargs:
            raise ValueError('"infile" is a mandatory parameter!')
        infile  = kwargs.get('infile')
        outfile = "tcprewrite_outfile"
        if outfile in kwargs:
            outfile = kwargs.get('outfile')

        path = '/tmp'
        if 'path' in kwargs:
            path = kwargs.get('path')
        if '/' not in infile:
            infile  = "{}/{}".format(path, infile)
        if '/' not in outfile:
            outfile = "{}/{}".format(path, outfile)
        cachefile   = '{}/cachefile'.format(path)
            
        src_intf  = 'eth1'
        dest_intf = 'eth1'
        if 'src_intf' in kwargs:
            src_intf = kwargs.get('src_intf')
        if 'dest_intf' in kwargs:
            dest_intf = kwargs.get('dest_intf')

        src_mac  = self.get_mac(src_intf)
        dest_mac = dest_obj.get_mac(dest_intf)
        enet_smac = "{},{}".format(dest_mac, src_mac)
        enet_dmac = "{},{}".format(src_mac, dest_mac)

        if 'pps' in kwargs:
            opt_rate = "--pps={}".format(kwargs.get('pps'))
        elif 'mbps' in kwargs:
            opt_rate = "--mbps={}".format(kwargs.get('mbps'))
        else:
            opt_rate = "--topspeed"

        cmd_prep    = "tcpprep"
        cmd_rewrite = "tcprewrite"
        cmd_replay  = "tcpreplay"
        cmd_prep = "{} --cidr={} --pcap={} --cachefile={}".format(cmd_prep, src_net, \
            infile, cachefile)
        cmd_rewrite = "{} --enet-smac={} --enet-dmac={} --fixcsum --cachefile={} \
            --infile={} --outfile={}".format(cmd_rewrite, enet_smac, enet_dmac, cachefile, \
            infile, outfile)
        cmd_replay  = "{} --cachefile={} --intf1={} --intf2={} {} {}".format(cmd_replay, \
            cachefile, src_intf, dest_intf, opt_rate, outfile)

        pattern = re.compile(r'command not found|No such file or directory')
        for cmd in [cmd_prep, cmd_rewrite, cmd_replay]:
            output = self._access.shell(cmd)
            if pattern.search(output[0]) is not None:
                return(False, output[0])

        for f in [infile, outfile, cachefile]:
            self._access.shell("rm -f {}".format(f))
        logger.debug('Tcpreplay info: \n{}'.format(output[0]))

        pattern = re.compile(r'Actual: \d+ packets \(\d+ bytes\) sent')
        if pattern.search(output[0]) is None:
            logger.error('Failed to tcpreplay, expected expression: {}'.format(pattern))
            return(False, output[0])

        logger.info('Succeed to tcpreplay')
        return(True, output[0])

    def send_dns_query(self, name, server='localhost', *args, **kwargs):
        """
        method to send query to dns server
        return:  a tuple of name and ip address
        example: send_dns_query('varmour.com')
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        cmd = "dig @{} {}".format(server, name)
        output = self._access.shell(cmd)
        ip = None
        for line in va_parse_as_lines(output[0]):
            if name in line and re.search(r'((\d+\.){3}\d+)', line) is not None:
                try:
                    fqdn, ttl, xx, type, ip = line.split() 
                except ValueError:
                    pass

        logger.info('Answer from DNS: {}, {}'.format(name, ip)) 
        return(name, ip)

    def send_dhcp_request(self, interface='eth1', server=None, *args, **kwargs):
        """
        method to send request to dhcp server
        return: ip address or None
        example: send_dhcp_request()
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        output = self._access.shell("dhclient -r {}".format(interface))

        cmd = "dhclient {} -v".format(interface)
        if server is not None:
            cmd += " -s {}".format(server)

        output = self._access.shell(cmd)
        match_result = re.search(r'bound to\s+([\d.]+)', output[0])
        if match_result is None:
            return None

        ip = match_result.group(1)
        logger.info('Lease ip {} from DHCP server'.format(ip)) 
        return(ip)

    def config_dns(self, *args, **kwargs):
        """
        method to configure dns server
        param  : kwargs : dict
                 domain : domain name,
                 record : a record of dns like "pc IN A 6.6.6.6"
        Returns:
            :bool - True on success or False on failure:
        example: config_dns(domain='varmour.net', record=['pc IN A 6.6.6.6'])
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        domain = 'varmour.net'
        record = 'pc      IN      A       6.6.6.6;'
        if 'domain' in kwargs:
            domain = kwargs.get('domain')
        if 'record' in kwargs:
            record = kwargs.get('record')
        if not isinstance(record, list):
            record = [record]

        soa_info = \
        """
$TTL 86400
$ORIGIN {}.
@       IN      SOA     pc.{}. master.pc.{}. (
                        2008031101      ;Serial
                        86400           ;refresh
                        7200            ;retry
                        86400           ;expire
                        120             ;ttl
                        )
        """.format(domain, domain, domain)

        record_info = \
        """
@       IN      NS      pc.{}.
@       IN      MX      5       pc
test    IN      A       1.1.1.1;
        """.format(domain)
        for info in record:
            record_info = "{}\n{}".format(record_info, info)

        conf_info = \
        """
zone "." {
    type hint;
    file "/etc/bind/db.root";
};

zone "localhost" {
    type master;
    file "/etc/bind/db.local";
};

zone "127.in-addr.arpa" {
    type master;
    file "/etc/bind/db.127";
};

zone "0.in-addr.arpa" {
    type master;
    file "/etc/bind/db.0";
};

zone "255.in-addr.arpa" {
    type master;
    file "/etc/bind/db.255";
};
zone "%s" IN {
        type master;
        file "/etc/bind/%s";
};
        """ % (domain, domain)

        resolv_info = \
        """
        nameserver 127.0.0.1
        """

        service = "bind9"
        conf_path = '/etc/bind'
        conf_filename = "named.conf.default-zones"
        conf_file = '{}/{}'.format(conf_path, conf_filename)
        zone_info = soa_info + record_info
        zone_filename = domain
        zone_file = '{}/{}'.format(conf_path, zone_filename)
        resolv_file = '/etc/resolv.conf'

        for contents, f in zip([zone_info, conf_info, resolv_info], [zone_file, conf_file, resolv_file]):
            self._access.shell("mv {} {}.bak".format(f, f))
            self._access.shell("touch {}".format(f))
            for cont in va_parse_as_lines(contents):
                if len(cont) != 0:
                    output = self._access.shell("echo '{}' >> {}".format(cont, f))

        try:
            self.service_stop(service)
            self.service_start(service)
        except ValueError as e:
            logger.error(e)
            return False

        name, ip = self.send_dns_query(name='test.{}'.format(domain))
        if ip != "1.1.1.1":
            logger.error('Failed to setup DNS server!')
            return False

        logger.info('Succeed to setup DNS server')
        return True

    def config_dhcp(self, *args, **kwargs):
        """
        method to configure dhcp server
        param  : kwargs : dict
                 server : dhcp server ip address,
                 range  : dhcp range ip address for client,
                 gateway: gateway for client,
                 subnet : subnet for client,
        Returns:
            :bool - True on success or False on failure:
        example: config_dhcp(server='2.2.2.10', range='2.2.2.2-2.2.2.6', 
            gateway='2.2.2.1', subnet='2.2.2.0')
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)

        if 'range' not in kwargs:
            raise ValueError('The "range" is a mandatory parameter, should be split with "-"')
        range = kwargs.get('range')
        try:
            range = range.split('-')
        except:
            raise ValueError('The range value should be split with "-"!')
        range_start = range[0]
        range_end   = range[1]

        if 'subnet' not in kwargs:
            raise ValueError('The "subnet" is a mandatory parameter!')
        subnet = kwargs.get('subnet')
        
        if 'server' not in kwargs:
            raise ValueError('The "server" is a mandatory parameter!')
        server = kwargs.get('server')

        interface = "eth1"
        netmask = '255.255.255.0'
        gateway_info = ''
        if 'interface' in kwargs:
            interface = kwargs.get('interface')
        if 'subnet' in kwargs:
            subnet = kwargs.get('subnet')
        if 'netmask' in kwargs:
            netmask = kwargs.get('netmaks')
        if 'gateway' in kwargs:
            gateway = kwargs.get('gateway')
            gateway_info = \
            """
    option routers      {};
    option subnet-mask  {};
           """.format(gateway, netmask)

        conf_info = \
        """
ddns-update-style interim;
ignore client-updates;

subnet %s netmask %s {
    range dynamic-bootp %s %s;
    default-lease-time 300;
    max-lease-time 300;
    %s
}
        """ % (subnet, netmask, range_start, range_end, gateway_info)
   
        service = "isc-dhcp-server"
        service_path = '/etc/default'
        service_file = '{}/{}'.format(service_path, service)
        self._access.shell("sed -i -e 's/INTERFACES=.*/INTERFACES=\"{}\"/g' {}".format(\
            interface, service_file))

        self.config_ip("{}/{}".format(server, netmask), interface)

        conf_path = '/etc/dhcp'
        conf_filename = "dhcpd.conf"
        conf_file = '{}/{}'.format(conf_path, conf_filename)

        self._access.shell("mv {} {}.bak".format(conf_file, conf_file))
        self._access.shell("touch {}".format(conf_file))
        for contents in va_parse_as_lines(conf_info):
            if len(contents) != 0:
                output = self._access.shell("echo '{}' >> {}".format(contents, conf_file))

        try:
            self.service_stop(service)
            self.service_start(service)
        except ValueError as e:
            pass

        try:
            output = int(self._access.shell("netstat -uap |grep dhcpd -c")[0])
        except:
            output = 0
        if not output:
            logger.error('Failed to setup DHCP server')
            return(False)

        logger.info('Succeed to setup DHCP server')
        return True

    def send_multicast(self, *args, **kwargs):
        """
        method to send multicast traffic on client
        param      : kwargs     : dict
                     mulcast_ip : multicast ip address, '224.0.0.4' by default
                     interface  : route device, 'eth1' by default
                     interval   : seconds between periodic bandwidth reports, 1 by default
        return: pid and process_file on success, False and error message on failure
        example    : send_multicast()
                   : send_multicast(mulcast_ip='224.0.0.4', interface='eth1')
        """
        logger.info("\nIn subroutine: " + sys._getframe().f_code.co_name)
        
        mulcast_ip = kwargs.get('mulcast_ip', '224.0.0.4')
        interface = kwargs.get('interface', 'eth1')
        interval = kwargs.get('interval', 1)

        cmd_route = "route add -net {} netmask 255.255.255.255 dev {}".format(mulcast_ip, \
            interface)
        output = self._access.shell(cmd_route)
        if re.search(r'Unknown host|No such device', output[0]) is not None:
            logger.error("Failed to add route")
            return(False, output[0])

        cmd_iperf = "iperf -c {} -u -T 32 -t 3 -i {}".format(mulcast_ip, interval)
        pid, process_file = self.exec_background(cmd_iperf, 'iperf_client', True, search_expr='iperf')
        logger.info("PID: {}".format(pid))

        if not pid:
            logger.error("Failed multicast!")
            self.remove_file(process_file)
            return(False, "Failed to call exec_background on client")

        cmd_cat = "cat {}".format(process_file)
        output = self._access.shell(cmd_cat)
        logger.debug('Multicast info: {}'.format(output[0]))

        local_ip = self.get_ip(interface).split('/')[0]
        reg_list = ['Client connecting to\s+{}'.format(mulcast_ip), 
                    'Sending\s+(\d+)\s+byte datagrams', 
                    'local\s+{}\s+port\s+(\d+)\s+connected\s+with\s+{}\s+port\s+(\d+)'.format(
                        local_ip, mulcast_ip)]
        for reg in reg_list:
            if re.search(reg, output[0]) is None:
                logger.error('Failed to sent multicast on client, \
expected expression: {}'.format(reg))
                return(False, output[0])

        logger.info("Successfully sent multicast on client")
        return(pid, process_file)

    def get_mac(self, interface='eth1'):
        """
        Helper method to get mac address of interface.
        Returns:
            :str of an mac address on success or None on failure:
        """
        output = self.show_interface(interface)
        try:
            mac_addr = output[0][3]
        except (IndexError) as e:
            logger.error('Failed to get HWaddr: {}'.format(output))
            return None

        logger.info('HWaddr: {}'.format(mac_addr))
        return mac_addr
