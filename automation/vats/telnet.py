"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Telnet implements the abstraction needed to simulate or run ftp traffic
across a given client and server.

    Telnet :: will create a object to initiate telnet session
    start() : method to create sessions
             It will create one telnet session each time
        Args:         server=None,
        server - where telnetd is running
        server_uid - username for server
                default is 'varmour'
        server_pw - password for server
                default is 'varmour'
        client - where telnet traffic is initiated
        client_uid - management user id
               default is 'varmour'
        client_pw - password
               default is 'varmour'
        telnet_destination - IP address to initiate telnet from client
        telnet_uid - userid for telnet service
                default is 'varmour'
        telnet_pw - password
                default is 'varmour'

        rcmd - list of commands to execute on telnet session
               default ['ls', 'pwd', 'uname']
               These are just to keep telnet session alive
        timeout - how long you want to keep telnet
               default is 180
    stop(): method to delete the sessions.
            It will delete all existing session which are
            create by start method


.. moduleauthor:: kbullappa@varmour.com
"""

import time
import os
import sys


from vautils.traffic.linux import Traffic
from vautils.config import Config
from access.shell import LinuxShell
from vautils import logger


class Telnet(Traffic):
    """
    Telnet implements the Telnet traffic class.
    """
    def __init__(
        self,
        server=None,
        server_uid='varmour',
        server_pw='varmour',
        client=None,
        client_uid='varmour',
        client_pw='varmour',
        telnet_destination=None,
        telnet_uid='varmour',
        telnet_pw='varmour',
        rcmd=['ls', 'pwd', 'uname'],
        timeout=None,
        debug=False,
        logfile='telnetlogs.logs'
    ):
        """
        Initializes the Telnet Traffic object.

        kwargs:
            :server (va_lab linux device object):
                Client where telnet session initiated
            :destination (str): destination ip address, which is
                destination IP address for telnet session
            :timeout (int): telnet timeout,
                    by default it is tcp timeout 180
            :debug (bool): enable debug logging
        """

        self._type = 'telnet'
        self._server = server
        self._server_uid = server_uid
        self._server_pw = server_pw
        self._client = client
        self._client_uid = client_uid
        self._client_pw = client_pw
        self._telnet_timeout = timeout
        self._debug = debug
        self._cmd = 'telnet'
        self._telnet_destination = telnet_destination
        self._telnet_userid = telnet_uid
        self._telnet_passwd = telnet_pw
        self._remote_cmd = rcmd
        self._logfile = logfile

        self._build_telnet_cmd()

    def start(self):
        """
        method used to start the telnet traffic process in the background on
        the client. It does a clean up of file if existing locally.  It
        launches the telnet client tool in the background, and gets the
        corresponding pid. If it cannot retrieve the pid it means the transfer
         is already complete or the process launch failed.
        """
        cmd = self._telnet_cmd
        if not cmd:
            logger.info('Command is not passed ')
            pass
            # TODO: raise exception or warning

        logger.info('Server' + str(self._server))

        servershell = LinuxShell(
            host=self._server,
            user=self._server_uid,
            pswd=self._server_pw
        )
        output, status = servershell.exec_command(' ls')
        print('server output : {} , Status : ', output, status)
        logger.info('Adding telnet details and restart xientd')
        xinetd_cmd = 'sudo apt-get install xinetd'
        telnet_server_details = '''service telnet
{
       flags          = REUSE
       socket_type    = stream
       wait           = no
       user           = root
       server         = /usr/sbin/in.telnetd
       log_on_failure += USERID
       disable        = no
}'''
        print(telnet_server_details)
        telnet_file_create_cmd = 'sudo echo  \"' + telnet_server_details + \
                                 '\" > /etc/xinetd.d/telnet'
        logger.info('check if the telnet service is already running')
        telnet_service_cmd = 'cat /etc/xinetd.d/telnet'
        output, status = servershell.exec_command(telnet_service_cmd)
        print('server output : {} , Status : ', output, status)
        if 'service telnet' in str(output):
            logger.info('telnet file already exists')
        else:
            print('telnet server details ', telnet_file_cmd)
            output, status = servershell.exec_command(telnet_file_create_cmd)
            print('server output : {} , Status : ', output, status)
        logger.info('restarting xinetd')
        xinetd_cmd = ' sudo chmod -R 777 /etc/xinetd.d/telnet; \
         sudo chown -R 777 /etc/xinetd.d/telnet '
        output, status = servershell.exec_command(xinetd_cmd)
        print('server output : {} , Status : ', output, status)
        xinetd_cmd = ' sudo /etc/init.d/xinetd restart '
        output, status = servershell.exec_command(xinetd_cmd)
        print('server output : {} , Status : ', output, status)
        print('CLIENT execution starts here...............',self._client)
        clientshell = LinuxShell(
            host=self._client,
            user=self._client_uid,
            pswd=self._client_pw
        )
        print(cmd)
        output, status = clientshell.exec_command(cmd)
        logger.info('Telnet Command execution Output :\n' + str(output))
        time.sleep(2)
        output = ''
        output, status = clientshell.exec_command('ps -ef | grep telnet')
        logger.info('......check the process is running or not in below \
            output :....\n' + str(output))
        #if 'sleep' + self._telnet_destination in str(output):
        if 'sleep' in str(output):
            logger.info('TELNET session started sucessfully \
                output : \n' + str(output))
            return True, output
        else:
            logger.error(".....TELNET session  NOT started sucessfully")
            logger.error('this system might not have telnetd.\
             Pleae install using the command : \
             sudo apt-get install xinetd telnetd')
            return False, None

    def stop(self):
        """
        method to stop the telnet traffic process spawned by the start method.
        """

        shell = LinuxShell(
            host=self._client,
            user=self._client_uid,
            pswd=self._client_pw
        )
        stop_cmd = 'pkill -f \'telnet ' + self._telnet_destination + '\''
        #stop_cmd = '\'killall \'telnet ' + self._telnet_destination + '\'\''
        print(stop_cmd)
        output = shell.exec_command(stop_cmd)
        logger.info('Output :' + str(output))
        if 'telnet' not in str(output):
            logger.info('TELNET closed successfully')
            return True, None
        else:
            logger.error('TELNET NOT closed successfully' + str(output))
            return False, output

    def _build_telnet_cmd(self):
        """
        helper method to build the telnet command to be run on the client.
        """
        cmds = ''
        rcmdlist = '('
        rcmdlist = rcmdlist + 'sleep 2; echo {}; sleep 5; echo {}; sleep 3; \
        echo ls; '.format(self._telnet_userid, self._telnet_passwd)
        for icmd in self._remote_cmd:
            rcmdlist = rcmdlist + " sleep 2; echo {}; ".format(icmd)

        if self._telnet_timeout:
            logger.info('User looking for long lived session, \
                        adding additional wait time')
            for i in range(int(self._telnet_timeout/30)):
                rcmdlist = rcmdlist + " pwd; sleep 30;"
        else:
            logger.info('TELNET session is with default has default wait time')
            rcmdlist = rcmdlist + " pwd; sleep 180;"
        cmds = rcmdlist + ') | telnet {} &'.format(self._telnet_destination)
        logger.info('The TELNET command :' + str(cmds))
        self._telnet_cmd = cmds


