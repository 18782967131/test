"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Telnet implements the abstraction needed to simulate or run telnet traffic
across a given client and server.

.. moduleauthor:: kbullappa@varmour.com
"""

import os, sys, time

from vautils import logger
from vautils.traffic.linux import Traffic

class Telnet(Traffic):
    """
    Telnet implements the Telnet traffic class.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the Telnet Traffic object.

        kwargs:
            :client (LinuxVm): linux vm object type
            :server (LinuxVm): linux vm object type
            :dest_intf (str): destination interface that receives the request
        """

        if 'client' not in kwargs or \
            'server' not in kwargs or \
            'dest_intf' not in kwargs:
            raise ValueError("'client', 'server' and 'dest_intf' are \
mandatory parameters!")

        self._client = kwargs.get('client')
        self._server = kwargs.get('server')
        self._dest_intf = kwargs.get('dest_intf')
        super(Telnet, self).__init__(self._client, self._server, self._dest_intf)
        self._user  = self._server.get_user()

        prog_name = 'va_telnet'
        client = self._conf_client
        local_path = os.path.split(os.path.realpath(__file__))[0]
        local_file = "{}/{}".format(local_path, prog_name)
        remote_path = '/bin'
        remote_file = "{}/{}".format(remote_path, prog_name)
        client._access._shell.upload(remote_file, local_file)
        client.exec_command('chmod 755 {}'.format(remote_file))

    def start(self, *args, **kwargs):
        """
        method used to start the telnet traffic process in the background on
        the client. It does a clean up of file if existing locally.  It
        launches the telnet client tool in the background, and gets the
        corresponding pid. If it cannot retrieve the pid it means the transfer
         is already complete or the process launch failed.
        kwargs:
            :timeout (int): telnet timeout
            :rcmd (str): cmds to execute on server
            :dest_ip (str): destination ip address, such as ip, hostname
        """
        self._type  = 'telnet'
        self._cmd   = 'va_telnet'
        self._timeout = 180
        self._userid  = self._user.get('name')
        self._passwd  = self._user.get('password')
        self._rcmd    = ['pwd']

        if 'timeout' in kwargs:
            self._timeout = kwargs.get('timeout')
        if 'rcmd' in kwargs:
            self._rcmd.append(kwargs.get('rcmd'))
        if 'dest_ip' in kwargs:
            self._dest_ip = kwargs.get('dest_ip')

        try:
            self._build_telnet_cmd()
        except ValueError as e:
            raise e

        client = self._conf_client
        pid, outfile = client.exec_background(self._cmd, redirect=True, 
            search_expr=self._cmd.split(' ')[0], search_full=True)
        logger.info('Telnet pid: {}'.format(pid))
        logger.info('Outfile: {}'.format(outfile))
        self._outfile = outfile
        if not pid or outfile is None:
            raise ValueError('Telnet traffic not started')

        times = 1
        sleeptime = 0.2
        self._stats = self.get_stats()
        while (self._stats == 'failed' or self._stats is None) and times <= 5:
            logger.debug('Sleeping {} seconds to start traffic'.format(sleeptime))
            time.sleep(sleeptime)
            self._stats = self.get_stats()
            times += 1

        if self._stats == 'failed' or self._stats is None:
            raise ValueError('Telnet traffic not started')
        
        logger.info('Telnet traffic started')

    def stop(self):
        """
        method to stop the telnet traffic process spawned by the start method.
        """
        client = self._conf_client
        if self._stats == 'started':
            transfer_time = int(self._timeout)
            logger.info('Time to transfer: {} seconds'.format(transfer_time))
            sleeptime = 10
            elapsedtime = 0
            while self._stats != 'completed' and elapsedtime <= transfer_time:
                if int(transfer_time / 60) != 0:
                    sleeptime = sleeptime * int(transfer_time / 60)
                time.sleep(sleeptime)
                self.get_stats()
                elapsedtime += sleeptime
                sleeptime += 10

        if self._stats != 'completed':
            logger.error('Telnet traffic not finished')
        else:
            logger.info('Telnet traffic finished')
       
        if self._outfile is not None:            
            self.get_stats()
            try:     
                client.exec_command('sudo rm -f {}'.format(self._outfile))
            except AttributeError as e:
                logger.warning(e)

        super(Telnet, self).__del__()

    def _build_telnet_cmd(self):
        """
        helper method to build the telnet command to be run on the client.
        """
        if self._dest_ip is None:
            raise ValueError('Invalid ip address: {}'.format(self._dest_ip))

        cmds = ''
        user_arg = '-u {}'.format(self._userid)
        passwd_arg = '-p {}'.format(self._passwd)

        rcmd_arg = ''
        for rcmd in self._rcmd:
            rcmd_arg += ' {}'.format(rcmd)
        rcmd_arg = '-c {}'.format(rcmd_arg)

        timeout_arg = ' -t {}'.format(self._timeout)
        self._cmd = "{} {} {} {} {} {}".format(self._cmd, self._dest_ip, user_arg, passwd_arg, timeout_arg, rcmd_arg)
        logger.info('The TELNET command :' + str(self._cmd))

    def _setup_server_infra(self):
        """
        setup infra on the server for telnet service to enable a file download.
        """
        self._service = 'xinetd'
        conf_file = "/etc/xinetd.d/telnet"
        server = self._conf_server
        shell = server.exec_command
        conf_info = \
'''service telnet
{
       flags          = REUSE
       socket_type    = stream
       wait           = no
       user           = root
       server         = /usr/sbin/in.telnetd
       log_on_failure += USERID
       disable        = no
}'''
        cmd_create = 'sudo echo  \"' + conf_info + '\" > {}'.format(conf_file)

        logger.info('check if the telnet service is already running')
        cmd_cat = 'cat {}'.format(conf_file)
        output = shell(cmd_cat)
        logger.debug('server output : {}'.format(output))
        if 'service telnet' in str(output):
            logger.info('telnet file already exists')
        else:
            output = server.exec_command(telnet_file_create_cmd)
            logger.debug('telnet server details ', cmd_create)

        cmd_chmod = ' sudo chmod -R 777 /etc/xinetd.d/telnet; \
            sudo chown -R 777 /etc/xinetd.d/telnet'
        output = shell(cmd_chmod)

        times = 0
        sleeptime = 0.5
        service_status = server.service_running(self._service)
        while not service_status and times <= 3:
            try:
                server.service_start(self._service)
            except ValueError as e:
                service_status = False
            else:
                service_status = True
                break
            time.sleep(sleeptime)
            times += 1

        if not service_status:
            raise ValueError(e)

        logger.info('Service {} is running'.format(self._service))

    def get_stats(self):
        """
        helper method to get the telnet stats.
        """
        stats = None
        client = self._conf_client
        shell = client.exec_command
        cmd = 'grep'
        cmd_arg = '{} -c'.format(self._outfile)
        shell("cat {}".format(self._outfile))
        if  shell("{} '/{}' {}".format(cmd, self._userid, cmd_arg)) and \
             shell("{} 'logout' {}".format(cmd, cmd_arg)):
            stats = 'completed'
        elif  shell("{} 'login:' {}".format(cmd, cmd_arg)):
            stats = 'started'
        elif  shell("{} 'Permission denied' {}".format(cmd, cmd_arg)) or \
              shell("{} 'No route to host' {}".format(cmd, cmd_arg)):
            stats = 'failed'

        self._stats = stats
        logger.info('Telnet traffic stats: {}'.format(stats))
        return stats
