"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

DataChannel asbtracts the synchronous data transfer between the client
and the remote SSH server

.. moduleauthor:: ppenumarthy@varmour.com
"""

import select
import paramiko
import time
import re
import logging

from access.ssh import Client
from access import logger
from access.exceptions import ChannelError, VaAccessTimedout

TERM_WIDTH = 24
TERM_HEIGHT = 80
POLL_INTERVAL = 10
RECV_TIMEOUT = 60
RECV_BYTES = 4096


class DataChannel(object):
    """
    Implements the abstraction for send/receive data on an SSH session
    """
    def __init__(
        self,
        host=None,
        user=None,
        password=None,
        port=22,
        terminal='console',
        prompt=None,
        uniq_id=None,
        width=TERM_WIDTH,
        height=TERM_HEIGHT,
        term_log=False,
        debug=None
    ):
        """
        Initiates the Data Channel object

        Kwargs:
            :host (str): ip address of the network device
            :user (str): linux user initiating the SSH session
            :password (str): login password for the user
            :port (int): SSH service port
            :terminal (str): remote termial type
            :width (int): terminal width (default 24 characters)
            :height (int): terminal height (default 80 characters)
        """
        self.client = Client(host, port, user, password, debug)

        self._host = host
        self._term = terminal
        self._term_width = width
        self._term_height = height
        self._term_log = None 
        self._user = user
        self._password = password
        self._uniq_id = uniq_id

        self._log = logger
        self._debug = debug
        self.channel = None

    def start(self, expect_prompt=None, persistent=False, retry_timeout=3):
        """
        Starts an interactive channel with the host.

        raises:
            :VaAccessTimedout or ChannelError:
        """
        if not self.client.connected():
            self.client.connect(persistent, retry_timeout)

        self.channel = self.client.open_channel(
                           self._term, self._term_width, self._term_height
                       )

        try:
            output, match, mode = self.expect(expect_prompt)
        except (VaAccessTimedout, ChannelError):
            raise
        else:
            if self._debug:
                self._log.debug("Interactive channel successfully opened.")
            return output, match, mode

    def stop(self):
        """
        Disconnects the interactive channel if it was open
        """
        if self.client.connected():
            self.client.disconnect()
            if self._debug:
                self._log.debug("Interactive channel to '{}' stopped"
                               .format(self._host))

    def connected(self):
        """
        Checks if the channel is open and the transport object of the sshclient
        is still connected
        """
        # TODO: some form of exception if required
        if self.channel and self.client.connected():
            return True
        return False

    def send_data(self, data_to_send):
        """
        Send data to the host on the channel.

        Args:
            :data_to_send (str): data to be transmitted
        """
        if self.connected():
            bytes_sent = 0
            while bytes_sent < len(data_to_send):
                bytes_sending = self.channel.send(data_to_send[bytes_sent:])
                
                if bytes_sending == 0:
                    raise ChannelError(context='data send failure')
                
                bytes_sent += bytes_sending

    def empty_in_buffer(self):
        """
        Empty the incoming channel buffer into data. Send window update when
        received data exceeds threshold

        Returns:
            :data (str): data in the form of str
        """
        if self.connected():
            data = self.channel.in_buffer.empty()

            win_update = self.channel._check_add_window(len(data))
            if win_update > 0:
                msg = paramiko.Message()
                msg.add_byte(paramiko.channel.cMSG_CHANNEL_WINDOW_ADJUST)
                msg.add_int(self.channel.remote_chanid)
                msg.add_int(win_update)
                self.channel.transport._send_user_message(msg)

            return data

    def expect(self, regex_pattern, timeout=RECV_TIMEOUT):
        """
        Receives data until it matches the regex string to match the
        rgex_str. Safe to empty the receive buffer, before calling send and
        expect from the client application - this way we make sure that we
        expect the data corresponding to the send that was issued.

        Args:
            :rgex_str (REGEX str): regex str to be matched in the received
             data

        Kwargs:
            :timeout (int): time to wait for received data before giving up

        Returns:
            :str, <class: re.MatchObject>, int: tuple consisting of output
                excluding the match, match object, and prompt mode

        Raises:
            :VaAccessTimedout: timeout waiting for a match
            :ChannelError: data receive error or channel closed prematurely
        """
        data_received = ''
        start_time = time.time()
        keep_receiving = True

        while keep_receiving:
            try:
                r, w, x = select.select([self.channel], [], [], POLL_INTERVAL)
                if timeout and (time.time() - start_time) > timeout:
                    raise VaAccessTimedout(
                              data_received, timeout, regex_pattern
                          )

                new_data = None

                if len(r) > 0:
                    new_data = self.channel.recv(RECV_BYTES)
                    if len(new_data) == 0:
                        raise ChannelError(
                                  output=data_received,
                                  context='Data receive error on channel'
                              )

                    decoded_data = new_data.decode('utf-8')
                    normalized_data = self.norm_line_feeds(decoded_data)
                    data_received += normalized_data 
                    output, match, mode = self._match_regex(
                                              data_received, regex_pattern
                                          )

                    if (output, match, mode) != (None, None, None):
                        keep_receiving = False

                elif self.channel.exit_status_ready():
                    raise ChannelError(
                              output=data_received,
                              context='Channel closed prematurely'
                          )
            except (VaAccessTimedout, ChannelError):
                keep_receiving = False
                raise
            finally:
                pass

        self._append_log(output)

        return output, match, mode

    def _init_term_log(self):
        """
        terminal logging helper for future 
        """
        logfile = logger.handlers[1].baseFilename
        term_logger = logging.getLogger('term')
        term_logger.setLevel(logging.DEBUG)
        term_logger.addHandler(logging.FileHandler(filename=logfile))

        self._term_log = term_logger

    def _append_log(self, content=None):
        """
        append the command execution log to the logger
        """
        for line in content.splitlines():
            uniq_id = "[{}]".format(self._uniq_id)
            self._log.info(' '.join((uniq_id, line)))

    def _match_regex(self, data_received, regex):
        """
        Try to match the expected regex str in the data accumulated thus
        far.

        Args:
            :data_received (str): normalized accumulated data so far
            :regex_str (regex str): regex string expected to be matched

        Raises:
            :re.error:
        """
        # TODO: need more robust checking
        if type(regex) != list:
            regex = [regex, ]

        for pattern, mode in regex:
            try:
                match = pattern.search(data_received)
                if match:
                    output = data_received
                    return output, match, mode
            except re.error:
                raise
        return None, None, None

    def norm_line_feeds(self, data):
        """
        Normalizes the line feeds and newlines in the received data to
        a convenient form. A general attempt is implemented here to
        address the different ways a carriage return and a new line can
        be sent by the CLI.

        Args:
            :data (str): newly received data

        Raises:
            :re.error:
        """
        try:
            fixed_data = re.sub('\r+', '\r', data)
            fixed_data = re.sub('\r\n', '\n', fixed_data)
            # Convert \n\r to \n, unless the \r is the end of the line
            # (a\\r\\n\\rb) -> (a\\n\\rb) -> (a\\nb)
            fixed_data = re.sub('\n\r(?!$|\r|\n)', '\n', fixed_data)
        except re.error:
            raise
        else:
            return fixed_data
