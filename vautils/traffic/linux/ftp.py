"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Ftp implements the abstraction needed to simulate or run ftp traffic across a
given client and server.

.. moduleauthor:: ppenumarthy@varmour.com
"""
import time
import os.path

from vautils import logger
from vautils.traffic.linux import Traffic

class Ftp(Traffic):
    """
    Ftp implements the Ftp traffic class.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the Ftp Traffic object. It calls the initializer of the
        parent first to set the common instance attributes

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
        super(Ftp, self).__init__(self._client, self._server, self._dest_intf)
        self._user  = self._server.get_user()

    def start(self, *args, **kwargs):
        """
        method used to start the Ftp traffic process in the background on the
        client. It does a clean up of file if existing locally.  It launches
        the lftp client tool in the background, and gets the corresponding pid.
        If it cannot retrieve the pid it means the transfer is already complete
        or the process launch failed. 

        kwargs:
            :file_size (str): size of the file to be put or get in terms of MB
            :mode (str): transfer mode, active or passive
            :rate (int): transfer rate (kb)
            :operation (str): put (upload) or get (download)
            :timeout (int): lftp timeout
        """
        self._cmd  = 'lftp'
        self._type = 'ftp'
        self._mode = 'passive'
        self._rate = 1024 * 128
        self._timeout = 90
        self._file_size = 100
        self._operation = 'get'
        self._stats = None
        self._outfile = None
        
        if 'mode' in kwargs:
            self._mode = kwargs.get('mode')
        if 'rate' in kwargs:
            self._rate = kwargs.get('rate')
            self._rate = int(self._rate) * 1024
        if 'operation' in kwargs:
            self._operation  = kwargs.get('operation')
        if 'file_size' in kwargs:
            self._file_size = kwargs.get('file_size')
        if 'timeout' in kwargs:
            self._timeout = kwargs.get('timeout')

        self.ctr_port = kwargs.get('port',21)

        try:
            self._setup_server_infra()
            self._build_ftp_cmd()
        except ValueError as e:
            raise e

        client = self._conf_client
        self._transfer_cleanup_util(True)
        pid, outfile = client.exec_background(self._cmd, redirect=True, 
            search_expr=self._cmd.split(' ')[0])
        logger.info('Ftp pid: {}'.format(pid))
        logger.info('Outfile: {}'.format(outfile))
        self._outfile = outfile
        if not pid or outfile is None:
            raise ValueError('Ftp traffic not started')

        times = 1
        sleeptime = 0.2
        self._stats = self.get_stats()
        while (self._stats == 'failed' or self._stats is None) and times <= 5:
            logger.debug('Sleeping {} seconds to start traffic'.format(sleeptime))
            time.sleep(sleeptime)
            self._stats = self.get_stats()
            times += 1

        if self._stats == 'failed' or self._stats is None:
            raise ValueError('Ftp traffic not started')
        
        logger.info('Ftp traffic started')

    def stop(self, *args, **kwargs):
        """
        method to stop the ftp traffic process spawned by the start method. It
        checks if the file transfer is complete. It then stops the vsftpd
        daemon, does a post transfer cleanup, and sets the traffic started
        boolean to false. It calls the del function to de-link references to
        the instances created by the traffic object, this also forces any
        open paramiko channels to the remote devices to be closed.
        """
        client = self._conf_client
        server = self._conf_server

        if self._stats == 'started':
            transfer_time = int(self._file_info[1]) / int(self._rate)
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
            logger.error('Ftp traffic not finished')
        else:
            logger.info('Ftp traffic finished')
       
        if self._outfile is not None:            
            self.get_stats()
            try:     
                client.exec_command('sudo rm -f {}'.format(self._outfile))
            except AttributeError as e:
                logger.warning(e)
        server.service_stop(self._service)
        self._transfer_cleanup_util(True, True)
        if self.ctr_port != 21 :
            server.exec_command("sed -i '/listen_port/d' /etc/vsftpd.conf")
            server.exec_command("sed -i '/isten=/a\listen_port=21' /etc/vsftpd.conf")
            output =server.exec_command('grep listen_port /etc/vsftpd.conf')
            server.service_stop(self._service)
            server.service_start(self._service)

        super(Ftp, self).__del__()
    
    def stop_by_force(self, *args, **kwargs):
        """
        method to stop the ftp traffic process spawned by force. It doesn't
        checks if the file transfer is complete. It will stops the vsftpd
        daemon by force, does a post transfer cleanup, and sets the traffic started
        boolean to false. It calls the del function to de-link references to
        the instances created by the traffic object, this also forces any
        open paramiko channels to the remote devices to be closed.
        """
        client = self._conf_client
        server = self._conf_server
        if self._outfile is not None:
            try:
                client.exec_command('sudo rm -f {}'.format(self._outfile))
            except AttributeError as e:
                logger.warning(e)
        server.service_stop(self._service)
        self._transfer_cleanup_util(True, True)
        super(Ftp, self).__del__()

    def _build_ftp_cmd(self):
        """
        helper method to build the lftp command to be run on the client.
        """
        if self._mode.upper() == 'PASSIVE':
            self._mode = 1
        elif self._mode.upper() == 'ACTIVE':
            self._mode = 0

        if self._dest_ip is None:
            raise ValueError('Invalid ip address: {}'.format(self._dest_ip))

        cmds = ''
        rate_arg = "set net:limit-rate {};".format(self._rate)
        mode_arg = "set ftp:passive-mode {};".format(self._mode)
        op_arg   = " {} {}; bye".format(self._operation, self._file_info[0])
        user_arg = " -u {},{}".format(self._user.get('name'), self._user.get('password'))
        timeout_arg = "set net:timeout {};".format(self._timeout)

        cmds += (rate_arg + mode_arg + timeout_arg + op_arg)
        self._cmd += " -e '{}' {} {}:{} -d".format(cmds, user_arg, self._dest_ip,self.ctr_port)
        logger.info('FTP CMD: {}'.format(self._cmd))

    def _setup_server_infra(self):
        """
        setup infra on the server for ftp service to enable a file download.
        """
        server = self._conf_server
        self._service = 'vsftpd'

        #configure ftp control port on ftp server
        if self.ctr_port != 21 :
            server.exec_command("sed -i '/listen_port/d' /etc/vsftpd.conf")
            server.exec_command("sed -i '/isten=/a\listen_port={}' /etc/vsftpd.conf".format(self.ctr_port))
            output =server.exec_command('grep listen_port /etc/vsftpd.conf')
            server.service_stop(self._service)
            server.service_start(self._service)

        self._file_info  = server.create_file(size=self._file_size)
        self._local_file = self._local_file()
        logger.info('Created file: {}'.format(self._file_info))

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
        helper method to get the lftp stats.
        """
        stats = None
        client = self._conf_client
        shell = client.exec_command
        cmd = 'grep'
        cmd_arg = '{} -c'.format(self._outfile)
        shell("cat {}".format(self._outfile))
        if  shell("{} 'Transfer complete' {}".format(cmd, cmd_arg)):
            if self._check_transfer('stop', self._type):
                stats = 'completed'
        elif  shell("{} 'Opening BINARY mode data connection' {}".format(cmd, cmd_arg)):
            stats = 'started'
        elif  shell("{} 'Connection refused' {}".format(cmd, cmd_arg)) or \
              shell("{} 'Access failed' {}".format(cmd, cmd_arg)):
            stats = 'failed'

        self._stats = stats
        logger.info('Ftp traffic stats: {}'.format(stats))
        return stats
