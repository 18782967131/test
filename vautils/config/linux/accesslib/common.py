"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Common implements model methods for executing linux feature configuration
commands (through feature configuration classes). The specific models for
the various distributions inherit from this class.

It inherits from the Model class or the model framework for the linux
product.

.. moduleauthor:: ppenumarthy@varmour.com
"""

from vautils.config.linux.accesslib import Mode
from access.exceptions import ShellCmdFail 


class Common(Mode):
    """
    Base class for executing the linux model methods on the remote vm
    running linux.
    """
    def exec_command(self, cmd=None):
        """
        model method to get the hostname of the remote vm.

        Kwargs:
            :cmd (str): linux command to be executed

        Returns:
            :output as string (str) of the command
        """
        output, exit_status = self._shell.exec_command(cmd)
        if int(exit_status) == 0:
            self.log_command(cmd)
            return output
        else:
            return False
