"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Exceptions abstracts the various errors that Access package can encounter at
run time. These can be categorized into three types - exceptions raised by
paramiko, exceptions that are raised while executing commands in Cli
environment, and exceptions raised while executing commands in linux bash
environment.  

.. moduleauthor:: ppenumarthy@varmour.com
"""


class ConnectionError(Exception):
    """
    ConnectionError is the base class for all paramiko run time errors
    encountered while the connection is being set up, or other errors that
    cause the connection to close down. The exceptions could happen while an
    SSH session is negotiated, or user is being authenticated (clear text user
    name and password), or when an interactive channel is requested. Here the
    class is empty and an exception raised is propagated to Exception class
    (which is the super class)
    """
    pass


class AccessError(Exception):
    """
    AccessError is the base class for all paramiko run time errors encountered
    while a command is executed remotely.
    """
    pass

class RestError(Exception):
    """
    RestError is the base class for all rest response errors.
    """
    pass


class ConnectFail(ConnectionError):
    """
    ConnectFail is raised when a paramiko Transport initialization fails, or
    an SSH client could not be started, or the user authentication fails and
    cannot be raised by AuthFail.
    """
    def __init__(self, inst):
        msg = 'connect failed during Transport Initialization'

        super(ConnectFail, self).__init__(msg)


class ChannelFail(ConnectionError):
    """
    ChannelFail is raised when a paramiko Transport fails to request an
    interactive shell from the Terminal server.
    """
    def __init__(self, inst):
        msg = 'creating an interactive channel failed'

        super(ChannelFail, self).__init__(msg)


class AuthFail(ConnectionError):
    """
    AuthFail is raised when a paramiko Transport initialization succeeds, but
    the user authentication fails.
    """
    def __init__(self, inst, user=None, password=None, host=None):
        msg = "Auth fail: credentials - user: {}, password: {}, host: {}"\
              .format(user, password, host)
        super(AuthFail, self).__init__(msg)


class ChannelError(ConnectionError):
    """
    ChannelError is raised when a paramiko Transport fails to send or receive
    data on the channel, or the channel closes prematurely.
    """
    def __init__(self, output=None, context=None):
        msg = ''
        if output:
            msg += output
        if context:
            msg += context
        super(ChannelError, self).__init__(msg)


class VaAccessTimedout(AccessError):
    """
    VaAccessTimedout is raised when the given regex pattern cannot be found in
    the output received on executing a command.
    """
    def __init__(self, output=None, timeout=None, exp_match=None):
        msg = "Timed out while trying to receive data"

        if output is not None:
            msg += '\nreceive data is {}\n'.format(output)

        if exp_match:
            msg += "Regex being matched: {}".format(exp_match)

        self.errmsg=msg
        super(VaAccessTimedout, self).__init__(msg)


class VaUnknownCliMode(AccessError):
    """
    UnknownCliMode is raised when the mode of the given prompt is not
    identified and hence is not valid.
    """
    def __init__(self, mode=None):
        msg = "Not a valid cli mode: {}".format(mode)

        super(VaUnknownCliMode, self).__init__(msg)


class VaCliModeError(AccessError):
    """
    CliModeSwitchError is raised when the cli cannot transition successfully
    from a given mode to an expected mode. This covers the scenario of
    switching from cli to shell also.
    """
    def __init__(self, cur_mode=None, exp_mode=None):
        msg = "Error occurred while switching from {} to {}"\
              .format(cur_mode, exp_mode)

        super(VaCliModeError, self).__init__(msg)


class ShellCmdFail(AccessError):
    """
    ShellCmdFail is raised when the shell command failed on the remote vm and
    the shell returns a failed exit status of 1 (instead of 0).
    """
    def __init__(self, cmd=None):
        msg = "Error occurred while executing shell command: {}".format(cmd)

        super(ShellCmdFail, self).__init__(msg)

class RestResponseFail(RestError):
    """
    RestResponseFail is raised when rest returns http error
    """
    def __init__(self):
        msg = "Error occured while executing rest call"

        super(RestResponseFail, self).__init__(msg)
