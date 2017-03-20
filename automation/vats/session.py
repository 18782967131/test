"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Client asbtracts the client side functionality of a paramiko SSH session

.. moduleauthor:: ppenumarthy@varmour.com
"""

import paramiko
import socket
import time

from access import logger
from access.exceptions import ConnectFail, ChannelFail, AuthFail


class Client(object):
    """
    Client implements the client side functionality of an SSH session
    """
    def __init__(
        self,
        host=None,
        port=22,
        user='varmour',
        password='vArmour123',
        debug=None
    ):
        """
        Initiates the SSH Client object

        Kwargs:
            :host (str): ip address of the host (SSH server)
            :port (int): SSH service port
            :user (str): linux user initiating the SSH session
            :password (str): login password for the user
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._debug = debug

        self._transport = None
        self._log = logger

    def connect(self, persistent=False, retry_timeout=60):
        """
        Creates a paramiko transport object, negotiates an SSH2 session as
        a client, and authenticates the user with the credentials passed
        in to the Client object

        Raises:
            :SSHException: On connection failure, or an SSH negotiation\
                failure. This exception is re raised through ConnectFail\
                exception.
        """
        retry = True
        end_time = time.time() + retry_timeout
        while retry:
            if time.time() < end_time:
                try:
                    transport = paramiko.Transport((self._host, self._port))
                    self.set_transport(transport)
                    transport.start_client()
                    authd = self._authenticate()
                except (paramiko.ssh_exception.SSHException,
                        socket.timeout) as e:
                    self.disconnect()
                    if persistent:
                        if self._debug:
                            self._log.info("retrying connect..")
                    else:
                        retry = False
                        raise ConnectFail(e)
                else:
                    retry = False
                    if authd and self._debug:
                        self._log.debug(
                            "user '{}' successfully initiated an SSH session to {}"
                            .format(self._user, self._host)
                        )
            else:
                retry = False
                self._log.error("connect timed out!")

    def disconnect(self):
        """
        Closes the current SSH2 session and any open channels associated
        with it.
        """
        transport = self.get_transport()
        if transport:
            if self._debug:
                self._log.debug(
                    "closing SSH session and open transport channels to {}"
                    .format(self._host)
                )
            transport.close()

    def connected(self):
        """
        Checks whether the SSH2 session that was started is active

        Returns:
            :True|False (bool): True if session is active (if not False)
        """
        transport = self.get_transport()
        if transport:
            return transport.is_active()
        else:
            if self._debug:
                self._log.debug("Transport disconnected!")
            return False

    def open_channel(self, term='console', height=24, width=80):
        """
        Request the server to open a channel - if successful, a pseudo
        terminal with a specified height, and width is requested - if
        successfull an interactive shell is requested. The stderr and
        stdout streams will be combined, so that errors will appear in
        stdout and thus in recv calls (otherwise errors have to be
        explicitly received through recv_stderr and recv_stderr_ready)

        Kwargs:
            :term (str): terminal type
            :height (int): height of the terminal (default 24 characters)
            :width (int): width of the terminal (default 80 characters)

        Returns:
            :channel: a new channel will be connected to the stdin and
                stdout of the pty

        Raises:
            :SShException: if any of the requests are rejected or the
                session ends prematurely. This exception is re raised
                through ChannelFail exception.
        """
        if self.connected():
            try:
                channel = self._transport.open_session()
                channel.get_pty(term, width, height)
                channel.invoke_shell()
                channel.set_combine_stderr(True)
            except paramiko.ssh_exception.SSHException as e:
                self.disconnect()
                raise ChannelFail(e)
            else:
                if self._debug:
                    self._log.debug(
                        "Transport channel created to {}".format(self._host)
                    )
                return channel

    def get_transport(self):
        """
        Get the transport attribute of the session
        """
        return self._transport

    def set_transport(self, transport):
        """
        Set the transport attribute to the instantiated paramiko transport
        object

        Args:
            :transport (paramiko.Transport): Instance of the paramiko
                Transport object
        """
        self._transport = transport

    def _authenticate(self):
        """
        Helper method to authenticate a user - calls the auth_password
        instance method of the paramiko.Transport object.

        Raises:
            :AuthenticationException: On invalid user name and password
            :BadAuthenticationType: If the authentication scheme is not
            supported by the server.
            One of the above exceptions is re raised through the AuthFail
            exception.
        """
        try:
            transport = self.get_transport()
            transport.auth_password(
                    self._user, self._password, fallback=True
            )
        except (paramiko.ssh_exception.AuthenticationException,
                paramiko.ssh_exception.BadAuthenticationType) as e:
            self.disconnect()
            raise AuthFail(e, user=self._user, password=self._password)
        else:
            return True
