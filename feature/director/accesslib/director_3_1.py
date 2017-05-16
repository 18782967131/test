"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Access abstracts the mechanism used by director to execute the cli commands
remotely. It inherits from VaAccess, which is the common access abstraction
implemented for varmour product.

.. moduleauthor:: ppenumarthy@varmour.com
"""

from feature import logger
from feature.common.accesslib.varmour_3_1 import VaAccess as Access


class VaAccess(Access):
    """
    Access implements methods that translate to executing cli commands remotely
    on the director.
    """
    def va_config(self, cmd=None, timeout=60, commit=True, exit=True, **kwargs):
        """
        method calls the _va_exec_cli_cmd method of the access layer.

        kwargs:
            :cmd (str|list): a single string command or a list of string
                              commands
            :timeout (int): timeout for each command in the list
            :commit (bool-True): if the config requires a commit
            :exit (bool-True): exit config mode and go back to cli if True

        returns:
            :err_cmd, err_msg (tuple): None, None on success and errored cmd,
                                       error message on failure
        """
        cached_state = None
        if self.cli_state is self.SHELL:
            cached_state = self.SHELL
        if self.cli_state is not self.CONFIG:
            self._drive_cli_state(self.cli_state, self.CONFIG)

        err_cmd, status = None, True
        err_msg = None

        cmd_list = self._va_list_of_cmds(cmd)

        for each_cmd in cmd_list:
            output, status = self._va_exec_cli_cmd(each_cmd, timeout, **kwargs)

            if not self._va_sanitize_output(output):
                err_cmd, err_msg = each_cmd, output.splitlines()[1]
                break

        if not err_msg and status:
            if commit:
                status, mesg = self.va_commit()
                if not status:
                    messages = mesg.splitlines()
                    err_cmd = messages[0]
                    err_msg = ' '.join(messages[1:len(messages) - 1])
                    output, status = self._va_exec_cli_cmd('rollback', timeout)

        if exit:
            self.cli.va_exit_config_mode()

        if cached_state:
            if not exit and cached_state is not self.CONFIG:
                self._drive_cli_state(self.cli_state, cached_state)

        return err_cmd, err_msg

    def va_commit(self):
        """
        method to commit the configuration

        returns:
            :bool, err_msg (tuple): True, None on successful commit or False,
                                    error message on failure
        """
        output, match, mode = self.cli.va_config_commit()
        err_msg = None

        if 'Error' in output or 'Failed' in output:
            err_msg = output
            logger.error("config commit failed!")
            return False, err_msg
        else:
            logger.info("config commit succeeded")

        return True, err_msg

    def va_reset_all(self, reboot_delay=60, reset_type='all'):
        """
        method to perform a reset on a varmour vm.
        parameter:
            reboot_delay (int): max timeout of booting device. try to ping mgt, try to login mgt if interface is UP.
            reset_type (str) : 'all' or 'keepha' or 'keephaorch', default will reset system configuration. reset
            system configuration except move  ha configuration if reset_type is 'keepha'; reset system configuration
            except move ha and orch configuration if reset_type is 'keephaorch.
        """
        self.va_cli()
        cli_prompt = self.cli.get_prompt()
        if reset_type == 'keepha' :
            cmd = 'request system reset config keep-high-availability'
        elif reset_type == 'keephaorch' :
            cmd = ' request system reset config keep-high-availability-orch-setup'
        else :
            cmd = 'request system reset config all'

        self.va_log_command(cmd)
        self.cli.exec_command(
            cmd,
            prompt=cli_prompt.sys_reset_all()
        )
        output, match, mode = self.cli.exec_command(
                                  'Y',
                                  command_output=True,
                                  prompt=cli_prompt.normal()
                              )

        cmd = 'request system reboot'
        self.va_reboot(cmd, 90, True, reboot_delay)

        return output

    def va_disable_paging(self, cmd=None):
        """
        method to set the terminal length to 0 so that the output can be read
        from the remote device in one shot.

        kwargs:
            :cmd (str): cli command string
        """
        if not cmd:
            cmd = "request cli terminal-length 0"

        self.va_cli(cmd)

    def va_config_inactivity_timeout(self, timeout=250):
        """
        Configure the cli timeout on inactivity, default value is 250 minutes.
        kwargs:
            :timeout : int: Inactivity-timeout in minutes
        Return: Ture/False
        Examples: va_config_inactivity_timeout(10)
                  va_config_inactivity_timeout()
        """
        return_value, err_msg = \
            self.va_config('set system inactivity-timeout {}'.format(timeout))

        if return_value is not None:
            logger.error(err_msg)
            return False
