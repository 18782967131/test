"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Shell abstracts the actions executed on the devices supporting shell.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import paramiko
import select
import socket
import time


from access import logger
from access.ssh import Client
from access.exceptions import ShellCmdFail, VaAccessTimedout

TIMEOUT = 30
RECV_BYTES = 4096


class LinuxShell(object):
    """
    Class implements access to shell (bash).
    """
    def __init__(
        self,
        host=None,
        port=22,
        user=None,
        pswd=None,
        debug=None
    ):
        """
        Initializes the shell access object

        Kwargs:
            :version (str): version of BD product
            :controller_ip (IPv4Address): ip address of the controller
            :service_port (str): SSL service port
            :user (str): user name of a valid bd shell user
            :password (str): valid password of the BD user
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = pswd
        self._debug = debug
        self._log = logger

        self._client = Client(host, port, user, pswd, debug)

    def exec_command(
        self,
        command=None,
        timeout=60,
        output_exp=None,
        error_exp=True,
        exit_info=None,
        retry_count=3,
        retry_delay=5
    ):
        """
        Method to execute a shell command remotely - it connects the created
        client instance, and calls the helper _exec_shell_command.

        Kwargs
            :commmand (str): linux command as a string
            :timeout (int):
            :output_exp (str):
            :error_exp (str):
            :exit_info:
            :retry_count (int):
            :retry_delay (int):

        Returns:
            :command output as a list of lines
        """
        if not self._client.connected():
            self._client.connect()

        output, exit_status = self._exec_shell_command(
                                  command,
                                  timeout=timeout,
                                  retry_count=retry_count,
                                  retry_delay=retry_delay
                              )

        if isinstance(exit_info, dict):
            exit_info['status'] = exit_status

        if exit_status != 0:
            self._log.warn("command could not be executed as expected: {}"
                           .format(output))

        if not error_exp:
            raise ShellCmdFail(command)

        if (output_exp is not None) and (bool(output) != bool(output_exp)):
            # TODO: raise exception
            self._log.debug("Output error")

        return output, exit_status

    def _exec_shell_command(self, command, timeout, retry_count, retry_delay):
        """
        """
        try:
            channel = self._client._transport.open_session()
        except socket.error:
            if retry_count == 0:
                raise

            self._reconnect(retry_count, retry_delay)
            channel = self._client.transport.open_session()
        channel.set_combine_stderr(True)

        start_time = time.time()

        try:
            if self._debug:
                self._log.debug("Executing command: {}".format(command))
            channel.exec_command(command)
        except paramiko.SSHException:
            if not self._client.connected():
                raise
            else:
                self._log.debug("Ignored exception")

        channel_closed = False
        data_received = ''

        while not channel_closed:

            r, w, x = select.select([channel], [], [], 10)

            if timeout and (time.time() - start_time) > timeout:
                    raise VaAccessTimedout(data_received, timeout)

            if len(r) > 0:
                new_data = channel.recv(RECV_BYTES)
                if len(new_data) > 0:
                    decoded_data = new_data.decode('utf-8')
                    data_received += decoded_data
                else:
                    channel_closed = True
            elif channel.exit_status_ready():
                channel_closed = True

        while not channel.exit_status_ready():
            if timeout and (time.time() - start_time) > timeout:
                    raise VaAccessTimedout(data_received, timeout=timeout)
            else:
                time.sleep(0.5)

        exit_status = channel.recv_exit_status()
        channel.close()

        return data_received, exit_status

    def download(self, remote=None, local=None):
        """
        Method to download a remote file to the local path.

        Kwargs:
            :remote (str): absolute path of the remote file
            :local (str): absolute path of the local file
        """
        if not self._client.connected():
            self._client.connect()
        transport = self._client.get_transport()
        sftp = transport.open_sftp_client()
        sftp.get(remote, local)
        sftp.close()
        self._client.disconnect()

    def upload(self, remote=None, local=None):
        """
        Method to upload a local file to the remote path.

        Kwargs:
            :local (str): absolute path of the local file
            :remote (str): absolute path of the remote file
        """
        if not self._client.connected():
            self._client.connect()
        transport = self._client.get_transport()
        sftp = transport.open_sftp_client()
        sftp.put(local, remote)
        sftp.close()

    def _reconnect(self, retry_count, retry_delay):
        """
        """
        for count in range(retry_count):
            try:
                self._client.connect()
                return
            except paramiko.SSHException:
                time.sleep(retry_delay)

        #TODO: raise Exception

    def _parse_as_lines(self, output):
        lines = list()
        if output:
            for line in output.readlines():
                lines.append(line.rstrip())

        self.output = lines

    def __del__(self):
        """
        close the ssl connection before destroying the instance
        """
        self._client.disconnect()
