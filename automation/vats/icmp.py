"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Icmp implements the abstraction needed to run icmp traffic between client and
and server pair.

.. moduleauthor:: ppenumarthy@varmour.com
"""
import os
import time

from vautils import logger
from vautils.traffic.linux import Traffic

class Icmp(Traffic):

    def __init__(self, *args, **kwargs):
        """
        Initializes the Icmp Traffic object. It calls the initializer of the
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
        super(Icmp, self).__init__(self._client, self._server, self._dest_intf)
        self._user  = self._server.get_user()

    def start(self, *args, **kwargs):
        """
        method used to start the Icmp traffic process in the background on the
        client. It does a clean up of file if existing locally.  It launches
        the ping client tool in the background, and gets the corresponding pid.
        If it cannot retrieve the pid it means the transfer is already complete
        or the process launch failed. 
        kwargs:
            :src_intf (str): source interface name
            :count (int): number of ICMP pings
            :size (int): size of the ping packet
            :timeout (int): ping timeout
        """
        self._cmd  = 'ping'
        self._type = 'ping'
        self._count = 5
        self._size  = 56
        self._timeout  = int(self._count) + 3
        self._interval = 1.0
        self._src_intf = None
        self._stats = None
        self._outfile = None
        
        if 'src_intf' in kwargs:
            self._src_intf = kwargs.get('src_intf')
        if 'count' in kwargs:
            self._count = kwargs.get('count')
        if 'size' in kwargs:
            self._size  = kwargs.get('size')
        if 'timeout' in kwargs:
            self._timeout = kwargs.get('timeout')
        if 'interval' in kwargs:
            self._interval = kwargs.get('interval')

        try:
            self._build_ping_cmd()
        except ValueError as e:
            raise e

        client = self._conf_client
        pid, outfile = client.exec_background(self._cmd, redirect=True, 
            search_expr=self._cmd.split(' ')[0])
        logger.info('Icmp pid: {}'.format(pid))
        logger.info('Outfile: {}'.format(outfile))
        self._outfile = outfile
        if not pid or outfile is None:
            raise ValueError('Icmp traffic not started!')

        times = 1
        sleeptime = 0.1
        self._stats = self.get_stats()
        while (self._stats == 'failed' or self._stats is None) and times <= 5:
            logger.debug('Sleeping {} seconds to start traffic'.format(sleeptime))
            time.sleep(sleeptime)
            self._stats = self.get_stats()
            times += 1

        if self._stats == 'failed' or self._stats is None:
            raise ValueError('Icmp traffic not started!')
        
        logger.info('Icmp traffic started')

    def stop(self, *args, **kwargs):
        """
        method to stop the icmp traffic process spawned by the start method. It
        checks if the ping is complete. It does a post transfer cleanup, and 
        sets the traffic started boolean to false. It calls the del function 
        to de-link references to the instances created by the traffic object, 
        this also forces any open paramiko channels to the remote devices to 
        be closed.
        """
        client = self._conf_client
        if self._stats == 'started':
            logger.info('Time to ping: {} seconds'.format(self._timeout))
            sleeptime = 1
            elapsedtime = 0
            while self._stats != 'completed' and elapsedtime <= self._timeout:
                time.sleep(sleeptime)
                self.get_stats()
                elapsedtime += sleeptime

        if self._stats != 'completed':
            logger.error('Icmp traffic not finished')
        else:
            logger.info('Icmp traffic finished')

        if self._outfile is not None:            
            self.get_stats()
            try:     
                client.exec_command('sudo rm -f {}'.format(self._outfile))
            except AttributeError as e:
                logger.warning(e)
        super(Icmp, self).__del__()

    def _build_ping_cmd(self):
        """
        helper method to build the ping command to be run on the client.
        """
        if self._dest_ip is None:
            raise ValueError('Invalid ip address: {}'.format(self._dest_ip))

        if 'src_intf' is not None:
            intf_arg  = " -I {}".format(self._src_intf)
        count_arg = " -c {}".format(self._count)
        size_arg  = " -s {}".format(self._size)
        timeout_arg = "-w {}".format(self._timeout)
        interval_arg = "-i {}".format(self._interval)
        self._cmd += "{} {} {} {} {} {}".format(intf_arg, count_arg, size_arg,
            self._dest_ip, timeout_arg, interval_arg)
        logger.info('ICMP CMD: {}'.format(self._cmd))

    def get_stats(self):
        """
        helper method to get the ping stats.
        """
        stats = None
        client = self._conf_client
        shell = client.exec_command
        cmd = 'grep'
        cmd_arg = '{} -c'.format(self._outfile)
        shell("cat {}".format(self._outfile))
        if  shell("{} 'ping statistics' {}".format(cmd, cmd_arg)):
            stats = 'completed'
        elif  shell("{} 'bytes from' {}".format(cmd, cmd_arg)):
            stats = 'started'
        elif  shell("{} 'Host Unreachable' {}".format(cmd, cmd_arg)):
            stats = 'failed'

        self._stats = stats
        logger.info('Icmp traffic stats: {}'.format(stats))
        return stats
