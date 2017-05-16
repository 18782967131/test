"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

CLI asbtracts the characteristics of a generic Command Layer Interface.
Specific vendor CLI's like vArmour will be derived from this class.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import inspect
import re

from access import logger
from access.ssh import DataChannel

SSH_SERVICE_PORT = 22
CLEAR_LINE = b'\x15'
COMMAND_TERMINATE = '\n'


class ChannelRep(dict):
    """
    Convinient class to hold the arguments for instantiating the Data
    channel. Inheriting from dict allows to add attributes dynamically.
    """
    def __init__(self):
        self.host = None,
        self.user = None,
        self.password = None,
        self.terminal = None,
        self.port = None,
        self.prompt = None
        self.uniq_id = None
        self.debug = None


class Cli(object):
    """
    A generic Cli implementation for network devices - acts as a base
    class for the vArmour or other vendor specific Cli implementations.
    The Cli uses the DataChannel, to send cli commands over the network
    to the devices, and receive output if any. The regex strings for
    various cli prompts are modeled after vArmour cli prompts. Modeling
    Cli as a context manager gives the convinience of automating
    creation and termination of events that come with, when using a Cli.
    """
    def __init__(
        self,
        host=None,
        port=None,
        user='root',
        password=None,
        terminal='console',
        persistent=False,
        retry_timeout=60,
        term_log=False,
        prompt=None,
        uniq_id=None,
        channel_type=DataChannel,
        debug=None
    ):
        """
        Initializes a generic Cli object.

        Kwargs:
            :host (str): ip address of the network device
            :port (int): SSH service port
            :user (str): linux user initiating the SSH Cli session
            :password (str): login password for the user
            :terminal (str): remote termial type
            :prompt (regex str): login prompt to be expected
            :channel_type (class name): data channel that cli intends
                to use for transport of commands and their output
            :debug (bool): Enable debug in logging
        """
        self._channel_type = channel_type
        rep = ChannelRep()

        rep.host = host
        rep.port = SSH_SERVICE_PORT
        rep.user = user
        rep.password = password
        rep.terminal = terminal
        rep.uniq_id = uniq_id
        rep.term_log = term_log
        rep.debug = debug
        self.user = user

        self._channel = None
        self._channel_rep = rep
        self._uniq_id = uniq_id
        self._log = logger
        self._state = None
        self._persistent = persistent
        self._retry_timeout = retry_timeout
        self._debug = debug
        self._default_mode = None
        self._prompt = None
        self._shell_prompt = None
        self.user_nocli = 'varmour_no_cli'

        self.set_prompt(prompt)
        rep.prompt = self.get_prompt()

    def __enter__(self):
        """
        Implementation of __enter__ of the context manager protocol. It
        initiates the cli session by calling start. Return the cli object
        itself.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """
        Implementation of __exit__ of the context manager protocol. If no
        exception is raised delete the instance of the cli. Else raise an
        exception.

        Kwargs:
            :exc_type: exception type - set by sys.exc_info
            :exc_value: exception value - set by sys.exc_info
            :exc_tb: exception traceback - set by sys.exc_info
        """
        if exc_type is None:
            del(self)
        else:
            # TODO: implement an exception
            self._log.warn("oops!")
            pass

    def __del__(self):
        """
        Custom delete method for the cli instance. If channel was instantiated,
        stop it. Else set it to None
        """
        channel = self.get_channel()

        if channel:
            channel.stop()
            if channel._term_log:
                channel._log_buffer = None

        self._log = None
        self._channel = None

    def stop(self):
        """
        Custom delete method for the cli instance. If channel was instantiated,
        stop it. Else set it to None
        """
        channel = self.get_channel()

        if channel:
            channel.stop()
            if channel._term_log:
                channel._log_buffer = None

        self._log = None
        self._channel = None

    def setup_prompt(self):
        """
        Sets up the prompt object for the cli. This needs to be over ridden by
        the specific vendor cli implementation.
        """
        # TODO: Implement the prompt system for a generic cli
        pass

    def channel_args(self):
        """
        Instance method that converts the object representation of a channel to
        a dict whose keys correspond to the attributes of the object.

        Returns:
            dict of arguments and their values
        """
        if True:
            attributes = inspect.getmembers(
                self._channel_rep, lambda a: not(inspect.isroutine(a))
            )
            return dict([a for a in attributes if not(
                         a[0].startswith('__') and a[0].endswith('__'))])

    def start(self, login_prompt=None):
        """
        Grab the channel arguments and instantiate the data channel.

        Kwargs:
            :login_prompt (str): expected regex string of the prompt upon login
        """
        self.set_channel()
        channel = self.get_channel()

        if login_prompt is None:
            pass
            # TODO: exception? login_prompt should be set up by now

        output, match, mode = channel.start(
                                  login_prompt,
                                  self._persistent,
                                  self._retry_timeout
                              )
        return True


    def set_channel(self):
        """
        Set the data channel by creating an instance of the channel type class
        """
        self._channel = self._channel_type(**self.channel_args())

    def get_channel(self):
        """
        Get the data channel attribute of the Cli instance
        """
        return self._channel

    def get_term_log(self):
        """
        Get the data channel's Cli execution log with the terminal server
        """
        channel = self.get_channel()
        return channel.get_term_log()

    def _poll_on_send(
        self,
        command=None,
        expected_prompt=None,
        command_output=True,
        append_line=True,
        timeout=60,
        **kwargs
    ):
        """
        Transmit a command in the form of text to the device and poll through
        expect until the expected prompt in the form of rgex_str is seen in
        the output.

        Args:
            :text (str): command string to be issued on the device
            :rgex_str (regex string): regex string to be matched in the output
             of the command.

        Kwargs:
            :append_line (bool): If true command terminator will be appended to
             the command
            :timeout (int): time to wait till the output is received

        """
        if append_line:
            command += COMMAND_TERMINATE

        channel = self.get_channel()
        if channel:
            channel.empty_in_buffer()
            channel.send_data(command)
            if re.search(r'set system user.*password',command) is not None :
                expected_prompt = (re.compile('Input new password:'), 10)
            else :
                if 'handle_password' in kwargs and \
                                kwargs.get('handle_password') is not None:
                    expected_prompt = (re.compile('password:'), 8)

            return channel.expect(expected_prompt, timeout)

    def exec_command(self, cmd, timeout=60, command_output=True, prompt=None,**kwargs):
        """
        Instance method that will be used by the client to execute a command
        remotely on a network device and if the output is True, it will
        return it.

        Args:
            :cmd (str): command to be executed on the device

        Kwargs:
            :timeout (int): time to wait till the output is received
            :command_output (bool): does the command generate output
            :prompt (regex str): prompt that should appear after executing
             the command

        Raises:
            :CommandOutputException:

        Returns:
            :tuple of output, match, mode
        """
        if not cmd:
            command_output = False
        else:
            if self._debug:
                self._log.debug("Executing command: '{}'".format(cmd))

        if prompt is None:
            prompt = self.get_prompt()
            if self._state is prompt.NORMAL_MODE:
                prompt = prompt.normal()
            elif self._state is prompt.CONFIG_MODE:
                prompt = prompt.configure()

        output, match, mode = self._poll_on_send(
                                  cmd,
                                  prompt,
                                  command_output,
                                  timeout=timeout,
                                  **kwargs
                              )
        if re.search(r'set system .*password|secret',cmd) is not None or \
           re.search(r'set orchestration.*passphrase',cmd) is not None and \
           re.search('delete',cmd) is None:
            tmp_password = kwargs.get('handle_password')
            expected_prompt = (re.compile('Re-input new password:'), 10)

            output, match, mode = self._poll_on_send(
                tmp_password,
                expected_prompt,
                command_output,
                timeout=timeout
            )

            output, match, mode = self._poll_on_send(
                tmp_password,
                prompt,
                command_output,
                timeout=timeout
            )
        else :
            if 'handle_password' in kwargs and \
                            kwargs.get('handle_password') is not None:
                tmp_password = kwargs.get('handle_password')
                output, match, mode = self._poll_on_send(
                    tmp_password,
                    prompt,
                    command_output,
                    timeout=timeout
                )

        if command_output and not output:
            self._log.info("output error!")
            # TODO: CommandOutputException

        if match and mode:
            if self._debug:
                self._log.debug("Match: {} mode: {}".format(match, mode))
            return output, match, mode

        return None, None, None
