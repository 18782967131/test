"""coding: utf-8

Copyright 2017 vArmour Networks private.
All Rights reserved. Confidential

Arping implements the abstraction needed to simulate or run ping traffic from a
client to a given destination.


.. moduleauthor:: ppenumarthy@varmour.com
"""

import time
import os
import sys

from vautils.traffic.linux import Traffic
from vautils import logger
from pprint import pprint


class Arping(Traffic):
    """
    Arping implements the Arping traffic class.
    """
    def __init__(self, *args, **kwargs):
        """
        Initializes the Arping Traffic object.

        kwargs:
            :client (linux resource object): Client initiating arping
            :server (linux resource object): destination for arping
            :src_intf (str): source interface of arping
            :destination (str): destination ip address
        """
        client, server = None, None
        src_intf, destination = None, None

        if 'src_intf' in kwargs:
            src_intf = kwargs.get('src_intf')
        if 'destination' in kwargs:
            destination = kwargs.get('destination')

        if not src_intf or not destination:
            raise ValueError('src_intf and destination params missing') 
       
        if 'client' in kwargs:
            client = kwargs.get('client')
        if 'server' in kwargs:
            server = kwargs.get('server')

        self._cmd = 'arping'
        super(Arping, self).__init__(client, server)

        self._destination = destination
        self._src_intf = src_intf
        self._opt_count = None
        self._opt_dod = None

    def start(self, *args, **kwargs):
        """
        method used to start the arping process in the background on the client.
        It launches the arping client tool in the background, and gets the
        corresponding pid. It redirects the output to a file. 
        
        kwargs:
            :opt_count (int): number of packets to be transmitted
            :opt_dod (str): option to set duplicate address detection
        """
        if 'opt_count' in kwargs:
            self._opt_count = int(kwargs.get('opt_count'))
        if 'opt_dod' in kwargs:
            self._opt_dod = True 
        
        self._build_arping_cmd()
        
        cmd = self._cmd + " {}".format(self._destination)
        if not cmd:
            logger.info('Command is not passed ')

        client = self._conf_client

        pid, outfile = client.exec_background(cmd, redirect=True,
            search_expr=self._cmd.split(' ')[0])

        self._pid = pid
        self._outfile = outfile

        logger.info('arping pid: {}'.format(pid))
        logger.info('outfile: {}'.format(outfile))

        if not pid:
            raise ValueError('arping traffic not started') 

    def stop(self):
        """
        method to stop the icmp traffic process spawned by the start method.
        """
        self._local = os.path.join(os.sep, 'tmp', os.path.basename(self._outfile))

        self._conf_client.get_remote_file(self._local, self._outfile)
        self._arp_table = self._parse_arp_table()

        self._conf_client.kill_background(self._pid)

        super(Arping, self).__del__()

    def get_stats(self):
        """
        method to summarize the statistics from the output of the arping command.
        """
        with open(self._local, 'r') as outfile:
            output = list()
            for line in outfile:
                output.append(line.strip())

        return output

    def get_arp_table(self):
        """
        method to return the arp table attribute
        """
        return self._arp_table

    def find_arp_entry(self, entry=None):
        """
        method to look up the arp table for an entry, which could be an
        ip address or a mac address

        kwargs:
            :entry (str): ip address or mac address

        return:
            :tuple of bool and output entry in /proc/net/arp
        """
        result = False, None
        table = self.get_arp_table() 

        if not entry or not table:
            return result

        for each_entry in table:
            if entry in each_entry:
                return True, each_entry 
        
        return result
 
    def _parse_arp_table(self):
        """
        method to parse the output of the /proc/net/arp file 
        """
        arp_file = 'arp'
        remote = os.path.join(os.sep, 'proc', 'net', arp_file)
        local = os.path.join(os.sep, 'tmp', arp_file)
        self._conf_client.get_remote_file(local, remote, False)

        with open(local, 'r') as outfile:
            output = list()
            for line in outfile:
                output.append(tuple(line.strip().split()))

        return output[1:]

    def _build_arping_cmd(self):
        """
        helper method to build the arping command to be run on the client.
        Here is the example

            arping -I eth0 -c 2 192.168.100.18
            arping -D -q -I eth0 -c 2 192.168.99.35
        """

        if self._opt_dod:
            self._cmd =  ' '.join((self._cmd, '-D')) 

        self._cmd = ' '.join((self._cmd, "-I {}".format(self._src_intf)))

        if self._opt_count:
            self._cmd = ' '.join((self._cmd, "-c {}".format(self._opt_count))) 

        logger.info('arping command: {}'.format(self._cmd))
