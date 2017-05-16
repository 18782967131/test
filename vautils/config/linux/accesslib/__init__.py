"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Model implements the base class for the linux product model framework
The models for the specific distributions must inherit from this class.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import os

from access.shell import LinuxShell
from imp import find_module, load_module
from vautils import logger


class Mode(object):
    """
    Model implements the base class for linux product models.
    """
    @classmethod
    def get(cls, resource=None):
        """
        class method to get the model associated with a specific linux
        distribution running on the resource vm.
        """
        access_class = resource.get_version().lower()
        abs_path = os.path.dirname(os.path.abspath(__file__))

        try:
            mod = find_module(access_class, [abs_path])
            load_mod = load_module(access_class, mod[0], mod[1], mod[2])
            mode = getattr(load_mod, 'Mode')
        except:
            raise
        else:
            return mode(resource)

    def __init__(self, resource=None):
        """
        Initialize the model object for the linux product.
        """
        user = resource.get_user()
        self._hostname = resource.get_hostname()
        session = resource.get_terminal_session()
        self._resource = resource
        
        if not session: 
            self._shell = LinuxShell(
                host=resource.get_mgmt_ip(),
                user=user.get('name'),
                pswd=user.get('password')
            )
            resource.set_terminal_session(self._shell)
        else:
            self._shell = session 

    def log_command(self, command=None):
        """
        Log the command and the role of the vm that executes the command.

        Kwargs:
            :command (str): cli command executed
        """
        logger.info("[{}] {}".format(self._hostname, command))

    def shell(self, cmd=None):
        """
        get the shell attribute of the model class.
        """
        self.log_command(cmd)
        return self._shell.exec_command(cmd)

    def __del__(self):
        """
        """
        self._resource.set_terminal_session(None)
        if self._shell._client.connected():
            self._shell._client.disconnect()
        self._shell = None
        self._resource = None
