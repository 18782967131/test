"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Ssh implements the abstraction needed to simulate or run ssh traffic across a
given client and server.

.. moduleauthor:: kbullappa@varmour.com
"""

import os, sys, time

from vautils import logger
from vautils.traffic.linux import Traffic

class Ssh(Traffic):
    """
    Ssh implements the Ssh traffic class.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the Ssh Traffic object.

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
        super(Ssh, self).__init__(self._client, self._server, self._dest_intf)
        self._user  = self._server.get_user()

    def start(self, *args, **kwargs):
        """
        method used to start the Ssh traffic process in the background on the
        client. It does a clean up of file if existing locally.  It launches
        the lssh client tool in the background, and gets the corresponding pid.
        If it cannot retrieve the pid it means the transfer is already complete
        or the process launch failed.
        kwargs:
            :timeout (int): ssh timeout
            :rcmd (str): cmds to execute on server
            :dest_ip (str): destination ip address, such as ip, hostname
        """
        self._type  = 'ssh'
        self._cmd   = 'sshpass'
        self._timeout = 300
        self._userid  = self._user.get('name')
        self._passwd  = self._user.get('password')
        self._rcmd    = ['uname', 'pwd']

        if 'timeout' in kwargs:
            self._timeout = kwargs.get('timeout')
        if 'rcmd' in kwargs:
            self._rcmd.append(kwargs.get('rcmd'))
        if 'dest_ip' in kwargs:
            self._dest_ip = kwargs.get('dest_ip')

        try:
            self._build_ssh_cmd()
        except ValueError as e:
            raise e

        client = self._conf_client
        pid, outfile = client.exec_background(self._cmd, redirect=True, 
            search_expr=self._cmd.split(' ')[0])
        logger.info('Ssh pid: {}'.format(pid))
        logger.info('Outfile: {}'.format(outfile))
        self._outfile = outfile
        if not pid or outfile is None:
            raise ValueError('Ssh traffic not started')

        times = 1
        sleeptime = 0.2
        self._stats = self.get_stats()
        while (self._stats == 'failed' or self._stats is None) and times <= 5:
            logger.debug('Sleeping {} seconds to start traffic'.format(sleeptime))
            time.sleep(sleeptime)
            self._stats = self.get_stats()
            times += 1

        if self._stats == 'failed' or self._stats is None:
            raise ValueError('Ssh traffic not started')
        
        logger.info('Ssh traffic started')

    def stop(self):
        """
        method to stop the ssh traffic process spawned by the stop method.
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
            logger.error('Ssh traffic not finished')
        else:
            logger.info('Ssh traffic finished')
       
        if self._outfile is not None:            
            self.get_stats()
            try:     
                client.exec_command('sudo rm -f {}'.format(self._outfile))
            except AttributeError as e:
                logger.warning(e)

        super(Ssh, self).__del__()

    def _build_ssh_cmd(self):
        """
        helper method to build the ssh command to be run on the client.
        Here is the example
         sshpass -p varmour ssh -o StrictHostKeyChecking=no -t -t  \
                varmour@10.150.93.132 "ls;sleep 300" | tee  logs &
        """
        if self._dest_ip is None:
            raise ValueError('Invalid ip address: {}'.format(self._dest_ip))

        cmds = ''
        rcmdlist = '"'
        for icmd in self._rcmd:
            rcmdlist = rcmdlist + " {}; sleep 10;".format(icmd)

        if self._timeout:
            logger.info('User looking for long lived session, \
                        adding additional wait time')
            for i in range(int(self._timeout/30)):
                rcmdlist = rcmdlist + " pwd; sleep 10;"
        else:
            logger.info('SSH session is with default has default wait time')

        rcmdlist = rcmdlist + '"'
        cmds = "{} -p {} ssh -o StrictHostKeyChecking=no -t -t  {}@{} {} \
               ".format(self._cmd, self._passwd, self._userid, self._dest_ip, rcmdlist)
        logger.info('The ssh command:' + str(cmds))
        self._cmd = cmds

    def get_stats(self):
        """
        helper method to get the sshpass stats.
        """
        stats = None
        client = self._conf_client
        shell = client.exec_command
        cmd = 'grep'
        cmd_arg = '{} -c'.format(self._outfile)
        shell("cat {}".format(self._outfile))
        if  shell("{} '/{}' {}".format(cmd, self._userid, cmd_arg)) and \
             shell("{} 'Linux' {}".format(cmd, cmd_arg)):
            stats = 'completed'
        elif  shell("{} 'Linux' {}".format(cmd, cmd_arg)) or \
              shell("{} '/{}' {}".format(cmd, self._userid, cmd_arg)):
            stats = 'started'
        elif  shell("{} 'Permission denied' {}".format(cmd, cmd_arg)) or \
              shell("{} 'No route to host' {}".format(cmd, cmd_arg)):
            stats = 'failed'

        self._stats = stats
        logger.info('Ssh traffic stats: {}'.format(stats))
        return stats
