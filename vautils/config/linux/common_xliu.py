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

    def create_file(self, name='qatest.file', size=100, path=None):
        """
        method to create a file using dd command on the host

        kwargs:
            :name (str): name of the file to be created
            :size (int): file size signifies multiple of a MB
            :path (str): path on the host where file is to be created

        returns:
            :3 element tuple of abs file path, file size, and md5sum
        """
        if not path:
            path = self.get_home_dir()
        path_info = self._access.exec_command("ls {}".format(path))
        if not path_info:
            self._access.exec_command('sudo mkdir -p {}'.format(path))

        rand_file = '{}/{}'.format(path,name)
        cmd = "sudo dd if=/dev/zero of={} bs=1048576 count={}"\
              .format(rand_file, size)
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
        search_expr=None
    ):
        """
        method to run the command as part of the process in the background.

        kwargs:
            :cmd (str): linux command to be run in the background
            :outfile (str):
            :redirect (bool):
            :search_expr (str):

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

        pid = self.get_pid(search_expr)
        if not pid:
            pass
            # TODO: raise or log warn

        return pid, remote_loc

    def get_pid(self, search_expr=None):
        """
        method to get the pid of the remote process running in the
        background.

        kwargs:
            :search_expr (str): search criteria for the process
        """
        output = self._access.exec_command("ps ax | pgrep '{}'"
                                           .format(search_expr))

        # ps_output = [tuple(line.split()) for line in output.splitlines()]
        # running = [line for line in ps_output if 'grep' not in line]
        #
        # if running:
        #     pid = ps_output[0][0]
        #     return pid

        return output if output else False

    def get_remote_file(self, local=None, remote=None):
        """
        method to get the file where the remote process redirected
        it's output. It will copy to the local location under /tmp

        kwargs:
            :local (str): abs path name of file on client
            :remote (str): abs path name of file on server
        """
        if not local:
            if os.path.exists(os.path.join(os.sep, 'tmp')):
                local = os.path.join(os.sep, 'tmp')

        self._access._shell.download(remote, local)

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

    def kill_background(self, pid=None, signal=2):
        """
        method to kill the process that is running remotely.

        kwargs:
            :pid (int): pid of the process to be killed
            :signal (int): signal type used by kill. Default - INT
        """
        kill_cmd = "kill -{} {}".format(signal, pid)
        self._access.exec_command(kill_cmd)

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
            print('#############################')
            print(ps_output.splitlines()[-1])
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
