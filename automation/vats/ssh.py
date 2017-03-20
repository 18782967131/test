"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Ssh implements the abstraction needed to simulate or run ftp traffic across a
given client and server.

    Ssh :: will create a object to initiate ssh session
    start() : method to create sessions
             It will create one ssh session each time
        Args: IP address of the system, where ssh session initiated
            destination IP, to create ssh session from above system
            user ID : optional argument, by default 'varmour'
            password : optional argument, by default 'varmour'
            commands : to execute on ssh session, default [ls, pwd, uname]
            timeout : by default it keep it for 180 sec
    stop(): method to delete the sessions.
            It will delete all existing session which are
            create by start method


.. moduleauthor:: kbullappa@varmour.com
"""

import time
import os
import sys

from vautils.traffic.linux.process import LinuxProcess
from vautils.traffic.linux.service import LinuxService
from vautils.traffic.linux import Traffic
from vautils.config import Config
from access.shell import LinuxShell
from vautils import logger


class Ssh(Traffic):
    """
    Ssh implements the Ssh traffic class.
    """
    def __init__(
        self,
        client=None,
        destination=None,
        userid='varmour',
        passwd='varmour',
        rcmd=['ls', 'pwd', 'uname'],
        timeout=None,
        debug=False,
        logfile='sshlogs.logs'
    ):
        """
        Initializes the Ssh Traffic object.

        kwargs:
            :client (va_lab linux device object):
                Client where SSH session initiated
            :destination (str): destination ip address, which is
                destination IP address for SSH session
            :timeout (int): ssh timeout, by default it is tcp timeout 180
            :debug (bool): enable debug logging
        """

        self._type = 'ssh'
        self._client = client
        self._ssh_timeout = timeout
        self._debug = debug
        self._cmd = 'ssh'
        self._destination = destination
        self._ssh_userid = userid
        self._ssh_passwd = passwd
        self._remote_cmd = rcmd
        self._logfile = logfile
        self._ssh_timeout = timeout

        self._build_ssh_cmd()

    def start(self):
        """
        method used to start the Ssh traffic process in the background on the
        client. It does a clean up of file if existing locally.  It launches
        the lssh client tool in the background, and gets the corresponding pid.
        If it cannot retrieve the pid it means the transfer is already complete
        or the process launch failed.
        """
        cmd = self._ssh_cmd
        if not cmd:
            logger.info('Command is not passed ')
            pass
            # TODO: raise exception or warning

        logger.info('Client' + str(self._client))

        shell = LinuxShell(
            host=self._client,
            user=self._ssh_userid,
            pswd=self._ssh_passwd
        )
        output = shell.exec_command(cmd)
        logger.info('Command execution Output :\n' + str(output))
        # TODO
        output = shell.exec_command('ps -ef | grep sshpass')
        logger.info('check the process is running or not in below \
            output :\n' + str(output))
        if self._ssh_userid in str(output):
            logger.info('SSH session started sucessfully \
                output : \n' + str(output))
            return True, output
        else:
            logger.error("SSH session  NOT started sucessfully")
            return False, None

    def stop(self):
        """
        method to stop the icmp traffic process spawned by the start method.
        """

        shell = LinuxShell(
            host=self._client,
            user=self._ssh_userid,
            pswd=self._ssh_passwd
        )
        output = shell.exec_command("killall sshpass")
        logger.info('Output :' + str(output))
        if self._ssh_userid not in str(output):
            logger.info('SSH closed successfully')
            return True, None
        else:
            logger.error('SSH NOT closed successfully' + str(output))
            return False, output

    def _build_ssh_cmd(self):
        """
        helper method to build the ssh command to be run on the client.
        Here is the example
         sshpass -p varmour ssh -o StrictHostKeyChecking=no -t -t  \
                varmour@10.150.93.132 "ls;sleep 300" | tee  logs &
        """
        cmds = ''
        rcmdlist = '"'
        for icmd in self._remote_cmd:
            rcmdlist = rcmdlist + " {}; sleep 60;".format(icmd)

        if self._ssh_timeout:
            logger.info('User looking for long lived session, \
                        adding additional wait time')
            for i in range(int(self._ssh_timeout/30)):
                rcmdlist = rcmdlist + " pwd; sleep 30;"
        else:
            logger.info('SSH session is with default has default wait time')
        rcmdlist = rcmdlist + '"'
        cmds = "sshpass -p {} ssh -o StrictHostKeyChecking=no -t -t  {}@{} {} | tee  {} & \
               ".format(self._ssh_passwd, self._ssh_userid,
                        self._destination, rcmdlist, self._logfile)
        logger.info('The ssh command :' + str(cmds))
        self._ssh_cmd = cmds
