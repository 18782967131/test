"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Access implements the base class for the linux product access framework
The accesslibs for specific versions must inherit from this class.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import os
import time
import re

from access.cli.va_os import VaCli
from access.rest.rest_util import Restutil
from feature import logger
from imp import find_module, load_module
from feature.common import supported, version_map
from access.exceptions import VaAccessTimedout
from feature.exceptions import UnsupportedVersion

CLEAR_CMD = '\003'


class VaAccess(object):
    """
    Access implements the base class for linux product access modes.
    """
    NORMAL = 1
    CONFIG = 2
    SHELL = 3

    @classmethod
    def get(cls, resource=None):
        """
        class method to get the accesslib associated with a specific varmour
        version running on the resource vm.

        kwargs:
            :resource (object): varmour resource object

        returns:
            accesslib class associated with the product's version

        raises:
            :ImportError, UnsupportedVersion:
        """
        found = False
        abs_path = os.path.dirname(os.path.abspath(__file__))

        product = resource.get_nodetype()
        if product == 'dir':
            product = 'director'
            varmour_path = os.path.abspath(os.path.join(abs_path, '..', '..'))
            accesslib = os.path.join(varmour_path, product, 'accesslib')
        elif product in ['ep', 'epi', 'cp']:
            accesslib = abs_path
            product = 'varmour'

        version = resource.get_version().split('.')[:2]
        version = '.'.join(version)

        if version not in supported:
            raise UnsupportedVersion(product, version)

        for ver in supported[supported.index(version):]:
            fwk_version = version_map.get(ver)
            access_file = '_'.join((product, fwk_version))

            try:
                mod = find_module(access_file, [accesslib])
            except ImportError:
                continue
            else:
                load_mod = load_module(access_file, mod[0], mod[1], mod[2])
                try:
                    access = getattr(load_mod, 'VaAccess')
                except AttributeError:
                    pass
                else:
                    found = True                     
                    return access

        if not found:
            raise ImportError("accesslib import error for {} with {}"
                              .format(product, version))

    def __init__(self, resource=None,**kwargs):
        """
        Initialize the access object for the varmour product.

        kwargs:
            :resource (object): varmour resource object
        """

        self._hostname = resource.get_hostname()
        self._resource = resource
        self._cli = None
        self._rest_util = None
        if 'add_nocli_user' in dir(resource) :
            self.add_nocli_user= resource.add_nocli_user
        else :
            self.add_nocli_user = False

        cli_session = resource.get_terminal_session()
        if not cli_session:
            self.va_init_cli(**kwargs)
        else:
            self._cli = cli_session

        rest_util = resource.get_rest_util()
        if not rest_util:
            self.va_init_rest_util(**kwargs)
        else:
            self._rest_util = rest_util


    @property
    def cli(self):
        """
        getter for cli property
        """
        return self._cli

    @property
    def cli_state(self):
        """
        getter for cli state property
        """
        return self.cli._state

    @property
    def rest_util(self):
        """
        getter for rest property
        :return: 
        """
        return self._rest_util

    def va_cli(self, cmd=None, timeout=60, **kwargs):
        """
        method to execute a single or a list of cli commands in normal
        mode

        kwargs:
            :cmd (str|list): a single string command or a list of string
                              commands
            :timeout (int): timeout for each command in the list
            :kwargs (dict): {'handle_password':'sigma-rt'}. handle input password command.
                            the value of handle_password is inputting password.
        """
        current_state = self.cli_state
        if current_state is not self.NORMAL:
            self._drive_cli_state(current_state, self.NORMAL)

        if cmd is not None :
            cmd_list = self._va_list_of_cmds(cmd)
            output = self._va_exec_command_list(cmd_list, timeout,**kwargs)

            if current_state is not self.NORMAL:
                self._drive_cli_state(self.NORMAL, current_state)
        else :
            output = ''

        return output

    def va_shell(self, cmd=None, timeout=60, sudo=True, exit=False, **kwargs):
        """
        method to execute a single or a list of shell commands with or without
        sudo access

        kwargs:
            :cmds (str|list): a single string command or a list of string
                              commands
            :timeout (int): timeout for each command in the list
            :sudo (bool-True): True if as sudo else False
            :exit (bool-True): exit shell mode and go back to cli if True
            :kwargs (dict): {'handle_password':'sigma-rt'}. handle input password command.
                            the value of handle_password is inputting password.

        returns:
            :output (str): output of a command or aggregated output of list
                           of commands

        example :
            dut.va_shell('sudo scp /tmp/xx root@10.11.120.141:/tmp/',\
                            **{'handle_password':'sigma-rt'})
        """
        cached_state = None
        if self.cli_state is self.CONFIG:
            cached_state = self.CONFIG
        if self.cli_state is not self.SHELL:
            self._drive_cli_state(self.cli_state, self.SHELL)

        if cmd is not None:
            cmd_list = self._va_list_of_cmds(cmd)
            output = self._va_exec_command_list(cmd_list, timeout, **kwargs)

            if exit:
                self.cli.va_enter_cli_from_shell(sudo)

            if cached_state:
                if not exit and cached_state is not self.SHELL:
                    self._drive_cli_state(self.cli_state, cached_state)
        else :
            output = ''
        return output

    def va_log_command(self, command=None):
        """
        log the command and the vm that executes the command

        kwargs:
            :command (str): cli command executed
        """
        logger.info("{}".format(command))

    def _va_list_of_cmds(self, cmds=None):
        """
        helper method to check the type of cmds and convert it to a list if
        needed

        kwargs:
            :cmds (str|list): a single string command or a list of string
                              commands
        """
        if type(cmds) is not list:
            cmd_list = list()
            cmd_list.append(cmds)
        else:
            cmd_list = cmds

        return cmd_list

    def _va_exec_command_list(self, command_list=None, timeout=None, **kwargs):
        """
        helper method to execute the list of cli or shell commands

        kwargs:
            :command_list (list): list of cli (string) commands
            :timeout (int): timeout for each command in the list
        """
        output = str()

        for each_cmd in command_list:
            cmd_out, status = self._va_exec_cli_cmd(
                                  each_cmd, timeout, **kwargs
                              )
            output += cmd_out

            if not status:
                cmd_index = command_list.index(each_cmd) + 1
                logger.info("command failed: {}".format(each_cmd))
                logger.info("command index: {}".format(cmd_index))
                logger.error("command error: {}".format(cmd_out))

        return output

    def _va_exec_cli_cmd(self, cmd=None, timeout=60, **kwargs):
        """
        helper method to execute a single cli command

        kwargs:
            :cmd (str): cli command
            :timeout (int): timeout for the command
        """
        status = True

        try:
            self.va_log_command(cmd)
            output, match, mode = self.cli.va_exec_cli(
                                      cmd, timeout=timeout, **kwargs
                                  )

            #not need to check error message on shell mode
            if mode != 3 and mode != 9:
                if not self._va_sanitize_output(output):
                    status = False
                    err_msg = output.splitlines()[1]
                    output, match, mode = self.cli.va_exec_cli(CLEAR_CMD)
                    output = err_msg
        except VaAccessTimedout as err_msg:
            status = False
            output, match, mode = self.cli.va_exec_cli(CLEAR_CMD)

            if re.search(r'Error\:',str(err_msg),re.I|re.M|re.S) is not None :
                output = str(err_msg)

        return output, status

    def _va_sanitize_output(self, output=None):
        """
        helper method to check for errors in output
        """
        if 'Error' in output:
            return False
        else:
            return True

    def _drive_cli_state(self, current=None, expected=None):
        """
        helper method to change the cli state from current state to
        an expected state

        kwargs:
            :current (int): current state - NORMAL|CONFIG|SHELL
            :expected (int): expected state - NORMAL|CONFIG|SHELL
        """
        if current == self.NORMAL and expected == self.CONFIG:
            self.cli.va_enter_config_mode()
        elif current == self.NORMAL and expected == self.SHELL:
            self.cli.va_enter_sudo_shell_from_cli()
        elif current == self.CONFIG and expected == self.NORMAL:
            self.cli.va_exit_config_mode()
        elif current == self.CONFIG and expected == self.SHELL:
            self.cli.va_exit_config_mode()
            self.cli.va_enter_sudo_shell_from_cli()
        elif current == self.SHELL and expected == self.NORMAL:
            self.cli.va_enter_cli_from_shell()
        elif current == self.SHELL and expected == self.CONFIG:
            self.cli.va_enter_cli_from_shell()
            self.cli.va_enter_config_mode()
        else:
            pass

    def va_init_cli(self, timeout=10, persistent=False,**kwargs):
        """
        re-instantiate the cli if required by the feature (reboot).
        or re-instantiate the cli of specific user.
        """
        resource = self._resource
        resource.__session = None
        resource_uniq_id = resource.get_uniq_id()

        try:
            del self._cli
        except AttributeError:
            pass

        user = resource.get_user()
        if 'user' in kwargs :
            user = kwargs.get('user')

        instance = VaCli(
            host=resource.get_mgmt_ip(),
            user=user.get('name'),
            password=user.get('password'),
            persistent=persistent,
            retry_timeout=timeout,
            prompt=resource.get_prompt_type(),
            uniq_id=resource_uniq_id
        )

        with instance as product_cli:
            self._cli = product_cli
            resource.set_terminal_session(product_cli)
            if self._cli:
                self.va_log_command('cli initiated')
                if resource.get_nodetype() == 'dir' and user.get('name') == 'varmour':
                    if self.add_nocli_user :
                        self.va_add_varmour_no_cli()
                    self.va_disable_paging()
                    self.va_config_inactivity_timeout()

                if user.get('name') == 'varmour_no_cli' :
                    self.cli.va_enter_sudo_shell_from_shell()
                    get_version = self.va_shell('cat /version')
                    match_reg = re.search(r'([\d\.]+)-', get_version, re.I | re.M)
                else :
                    get_version = self.va_cli('show system | grep version')
                    match_reg = re.search(r'software version:\s+([\d\.]+)-', get_version, re.I | re.M)

                if match_reg is not None:
                    version = match_reg.group(1)
                else:
                    version = resource.get_version()
                resource.current_version=version

    def va_add_varmour_no_cli(self):
        # add varmour_no_cli user to check core file
        name = self.cli.user_nocli
        user = self._resource.get_user()
        output = self.va_shell("sudo grep -A3 '%s' /etc/bash.bashrc" % name, exit=False)
        match_nocliuser = re.search(r'\$user\s*==\s*"%s"' % name, output, re.I|re.M)
        if match_nocliuser is None:
            self.va_shell("cp /etc/bash.bashrc /etc/bash.bashrc_bak", exit=False)
            output = self.va_shell("grep '$USER ==' /etc/bash.bashrc", exit=False)
            match_if_condition = re.search(r'if\s*\[(.*?)\]\s*;', output, re.I|re.M)
            if match_if_condition is not None:
                org_if_condition = match_if_condition.group(1).strip()
            else:
                org_if_condition = '$USER == "root"'

            self.va_shell("sed -i 's/%s/$USER == \"%s\" -o %s/g' /etc/bash.bashrc" % \
                          (org_if_condition, name, org_if_condition))
            output = self.va_shell("grep -A3 '%s' /etc/bash.bashrc" % name)
            if re.search(r'\$user\s*==\s*"%s"' % name, output, re.I|re.M) is None :
                logger.error('Failed to add varmour_no_cli to /etc/bash.bashrc file')
            else :
                logger.info('Succeed to add varmour_no_cli to /etc/bash.bashrc file')

        cmd = 'set system user {} role admin'.format(name)
        cmd1 = 'set system user {} password'.format(name)
        self.va_cli()
        err_cmd, err_msg = self.va_config(cmd, commit=False, exit=False)
        err_cmd1, err_msg1 = self.va_config(cmd1, **{'handle_password': user.get('password')})

        if err_cmd is not None or err_msg is not None or \
                        err_cmd1 is not None or err_msg1 is not None:
            logger.error('Failed to add user {}'.format(name))
            return False

        logger.info('Succeed to add user {}'.format(name))
        return True

    def va_init_rest_util(self, **kwargs):
        """
        re-instantiate the cli if required by the feature (reboot).
        or re-instantiate the cli of specific user.
        """
        resource = self._resource
        resource.__rest_util = None
        resource_uniq_id = resource.get_uniq_id()

        try:
            del self._rest_util
        except AttributeError:
            pass
        kwargs['resource'] = resource
        rest_util_instance = Restutil(
            **kwargs
        )
        resource.set_rest_util(rest_util_instance)
        self._rest_util = rest_util_instance
        self.va_log_command('rest util initiated')


    def disconnect(self):
        self._cli = self.cli.stop()

    def __del__(self):
        """
        unlink the cli instance
        """
        try:
            self._cli = None
        except AttributeError:
            pass
