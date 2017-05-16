"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Tftp implements the abstraction needed to simulate or run tftp traffic across a
given client and server.

.. moduleauthor:: ppenumarthy@varmour.com
"""
import time
import os.path

from vautils import logger
from vautils.traffic.linux import Traffic

class Tftp(Traffic):
    """
    Tftp implements the Tftp traffic class.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the Tftp Traffic object. It calls the initializer of the
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
        super(Tftp, self).__init__(self._client, self._server, self._dest_intf)
        self._user  = self._server.get_user()

    def start(self, *args, **kwargs):
        """
        method used to start the Tftp traffic process in the background on the
        client. It does a clean up of file if existing locally.  It launches
        the tftp client tool in the background, and gets the corresponding pid.
        If it cannot retrieve the pid it means the transfer is already complete
        or the process launch failed. 

        kwargs:
            :file_size (str): size of the file to be get in terms of MB
            :rate (int): transfer rate (kb)
            :operation (str): -g, get remote file
            :timeout (int): tftp timeout
        """
        self._cmd  = 'curl'
        self._type = 'tftp'
        self._rate = 128
        self._timeout = 90
        self._file_size = 100
        self._operation = '-g'
        self._stats = None
        self._outfile = None
        
        if 'rate' in kwargs:
            self._rate = kwargs.get('rate')
        if 'operation' in kwargs:
            self._operation  = kwargs.get('operation')
        if 'file_size' in kwargs:
            self._file_size = kwargs.get('file_size')
        if 'timeout' in kwargs:
            self._timeout = kwargs.get('timeout')

        try:
            self._setup_server_infra()
            self._build_tftp_cmd()
        except ValueError as e:
            raise e

        client = self._conf_client
        self._transfer_cleanup_util(True)
        logger.info('######################################################')
        logger.info('#                                                    #')
        logger.info("# Warning, TFTP can't control transfer rate so far!!!#")
        logger.info('#                                                    #')
        logger.info('######################################################')
        pid, outfile = client.exec_background(self._cmd, redirect=True, 
            search_expr=self._cmd.split(' ')[0])
        logger.info('Tftp pid: {}'.format(pid))
        logger.info('Outfile: {}'.format(outfile))
        self._outfile = outfile
        if not pid or outfile is None:
            raise ValueError('Tftp traffic not started')

        times = 1
        sleeptime = 0.2
        self._stats = self.get_stats()
        while (self._stats == 'failed' or self._stats is None) and times <= 5:
            logger.debug('Sleeping {} seconds to start traffic'.format(sleeptime))
            time.sleep(sleeptime)
            self._stats = self.get_stats()
            times += 1

        if self._stats == 'failed' or self._stats is None:
            raise ValueError('Tftp traffic not started')

        logger.info('Tftp traffic started')

    def stop(self, *args, **kwargs):
        """
        method to stop the tftp traffic process spawned by the start method. It
        checks if the file transfer is complete. It then stops the xinetd
        daemon, does a post transfer cleanup, and sets the traffic started
        boolean to false. It calls the del function to de-link references to
        the instances created by the traffic object, this also forces any
        open paramiko channels to the remote devices to be closed.
        """
        client = self._conf_client
        server = self._conf_server
        if self._stats == 'started':
            transfer_time = int(self._file_info[1]) / int(self._rate * 1024)
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
            logger.error('Tftp traffic not finished')
        else:
            logger.info('Tftp traffic finished')
            
        if self._outfile is not None:            
            self.get_stats()
            try:     
                client.exec_command('sudo rm -f {}'.format(self._outfile))
            except AttributeError as e:
                logger.warning(e)
        server.service_stop(self._service)
        self._transfer_cleanup_util(True, True)
        super(Tftp, self).__del__()

    def _build_tftp_cmd(self):
        """
        helper method to build the tftp command to be run on the client.
        """
        if self._dest_ip is None:
            raise ValueError('Invalid ip address: {}'.format(self._dest_ip))

        remote_filename  = self._file_info[0].split('/')[-1]
        if self._user.get('name') == 'root' :
            file_path = ''
        else :
            file_path = '/home'
        local_file = '{}/{}/{}'.format(file_path, self._user.get('name'), remote_filename)
        timeout_arg = " --connect-timeout {}".format(self._timeout)
        op_arg = " {} tftp://{}/{} -o {}".format(self._operation, self._dest_ip, \
            remote_filename, local_file)
        rate_arg = " --limit-rate {}K".format(self._rate)
        self._cmd += " {} {} {} -v -#".format(op_arg, timeout_arg, rate_arg)
        logger.info('FTP CMD: {}'.format(self._cmd))

    def _setup_server_infra(self):
        """
        setup infra on the server for tftp service to enable a file download.
        """
        server = self._conf_server
        os, version = server.get_version()
        if os.lower() == 'ubuntu' and version == '16.04':
            self._service = 'tftpd-hpa'
        else:
            self._service = 'xinetd'

        self._file_info  = server.create_file(size=self._file_size, path='/tftpboot')
        self._local_file = self._local_file()
        logger.info('Created file: {}'.format(self._file_info))

        times = 0
        sleeptime = 1
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
        helper method to get the tftp stats.
        """
        stats = None
        client = self._conf_client
        shell = client.exec_command
        cmd = 'grep'
        cmd_arg = '{} -c'.format(self._outfile)
        shell("cat {}".format(self._outfile))
        if  shell("{} '100.0%\* Closing connection' {}".format(cmd, cmd_arg)):
            if self._check_transfer('stop', self._type):
                stats = 'completed'
        elif  shell("{} 'Connected for receive' {}".format(cmd, cmd_arg)):
            stats = 'started'
        elif  shell("{} 'File Not Found' {}".format(cmd, cmd_arg)):
            stats = 'failed'

        self._stats = stats
        logger.info('Tftp traffic stats: {}'.format(stats))
        return stats
