"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Traffic implements the abstraction needed to simulate or run a specific type of
traffic between a client and server.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import os
import time

from abc import ABCMeta, abstractmethod
from vautils import logger
from vautils.config import Config


class Traffic(metaclass=ABCMeta):
    """
    Traffic implements the class that can simulate or generate different types
    of traffic. It acts as a base class for the specific child traffic classes.
    """
    def __init__(self, client=None, server=None, dest_intf=None, duration=15):
        """
        Initializes the Traffic object - should be called by the
        child class.

        kwargs:
            :client (va_lab linux device object):
            :server (va_lab linux device object):
        """
        if not client and not server:
            pass
            # TODO: raise exception

        if 'Delegator' in client.__class__.__name__:
            client = client._resource
        if 'Delegator' in server.__class__.__name__:
            server = server._resource
        
        self._client = client
        self._server = server
        self._conf_client = Config.get_linux_config_util(client)
        self._conf_server = Config.get_linux_config_util(server)

        self._dest_ip = self._conf_server.get_ip(dest_intf)

        self._client_role = client.get_uniq_id()
        self._server_role = server.get_uniq_id()

        self._duration = duration
        self._log = logger
        self._started = False

    @abstractmethod
    def start(self):
        """
        should be implemented by the child class
        """
        pass

    @abstractmethod
    def stop(self):
        """
        should be implemented by the child class
        """
        pass

    @property
    def started(self):
        """
        method to get the traffic started boolean.
        """
        return self._started

    @started.setter
    def started(self, value):
        """
        method to set the traffic started boolean.
        """
        self._started = value

    def _local_file(self):
        """
        method to return the name of the file that is being copied
        """
        return os.path.basename(self._file_info[0])

    def _check_transfer(self, context=None, app=None):
        """
        helper method to check the transfer of a file from remote host
        """
        transfer = False
        if self._poll_file_transfer():
            transfer = True
            self._log.info("{} transfer successful".format(app))
        else:
            self._log.error("{} failed".format(app))

        return transfer

    def _poll_file_transfer(self, poll_period=3):
        """
        helper method to verify that the http transfer was successful.
        verification is based on the size & md5sum of the file downloaded
        as compared to the original file that resides on the remote vm.

        Kwargs:
            :poll_period (int): period of time to sleep before polling again

        Returns:
            :True|False (bool): True or False depending on the transfer
        """
        client_conf = self._conf_client
        home = client_conf.get_home_dir()

        remote_file, remote_file_size, remote_md5sum = self._file_info
        local_file = "{}/{}".format(home, self._local_file)

        start_time = time.time()
        timer = start_time + self._timeout
        timedout = False

        if remote_file and remote_file_size:
            download_file_size = 0
            while time.time() < timer and\
                    download_file_size != remote_file_size:
                download_file_stat = client_conf.get_file_stat(local_file)
                download_file_size = download_file_stat[4]
                time.sleep(int(poll_period))

            if download_file_size != remote_file_size:
                timedout = True
                self._log.error("file operation timed out")

            if not timedout:
                local_md5sum = client_conf.get_md5sum(local_file)
                if local_md5sum == remote_md5sum:
                    self._log.info("copied {} to {} on {}"
                                   .format(os.path.basename(local_file),
                                           os.path.dirname(local_file),
                                           self._client_role))
                    self._log.info("transferred {} bytes from {}"
                                   .format(download_file_size,
                                           self._server_role))
                    return True
                else:
                    self._log.error("md5sum verification failed")
                    return False

    def _transfer_cleanup_util(self, local=False, remote=False):
        """
        remove the remote and local files from the respective vm's.
        """
        cleanup_queue = list()
        if local:
            cleanup_queue.append((self._conf_client, self._local_file))
        if remote:
            cleanup_queue.append((self._conf_server, self._file_info[0]))

        for hostconf, to_be_removed in cleanup_queue: 
            hostconf.remove_file(to_be_removed)

    def __del__(self):
        """
        unlink the references to instances
        """
        self._client = None
        self._server = None
        self._conf_client = None
        self._conf_server = None
        self._log = None
