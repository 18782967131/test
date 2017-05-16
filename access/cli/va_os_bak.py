"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaCli asbtracts the characteristics of the vArmour CLI. It inherits
from the Cli class. At a later point - with a different approach and
some refactoring the generic parent Cli, and vendor cli's like varmour
can be completely seperated. They kind of co exist now - this approach
will allow us to open source the cli and shell frameworks modeled around
paramiko

.. moduleauthor:: ppenumarthy@varmour.com
"""
import time,re
from access.cli import Cli
from access.cli.prompt import *  # NOQA
from access.exceptions import VaUnknownCliMode, VaCliModeError


class VaCli(Cli):
    """
    Implements remote command execution capability for the vArmour Cli.
    Inherits from generic Cli.
    """

    def set_prompt(self, prompt):
        """
        Sets the prompt attribute by calling the Va_cli_prompt class. The
        resulting object's attributes correspond to the various components
        that make up the vArmour cli prompt string. Please read the
        documentation of Va_cli_prompt class for more information.

        .. note:
           This method will be called by the parent class Cli, so cannot
           prefix the name by va at this point.
        """
        prompt_class = '_'.join((prompt.title(), 'prompt'))
        self._prompt_class = prompt_class
        self.dev_type = self._prompt_class.split('_')[0]
        self._prompt = globals().get(prompt_class)()

    def get_prompt(self):
        """
        Get cli prompt

        .. note:
           This method will be called by the parent class Cli, so cannot
           prefix the name by va at this point.
        """
        return self._prompt

    def get_shell_prompt(self):
        """
        Gets shell prompt

        .. note:
           This method will be called by the parent class Cli, so cannot
           prefix the name by va at this point.
        """
        return self._shell_prompt

    def start(self):
        """
        Initialize the SSH data channel through start of the super class

        .. note:
           This method will be called by the parent class Cli, so cannot
           prefix the name by va at this point.
       """

        if self.user == self.user_nocli :
            login_prompt = Va_shell_prompt().varmournocli_prompt()
        elif self.dev_type == 'Dm' or self.dev_type == 'Dp':
            login_prompt = Va_shell_prompt().dpdm_prompt()
        else :
            login_prompt = self.get_prompt().login()

        i = 0
        while i < 7 :
            i+=1
            try :
                super(VaCli, self).start(login_prompt)
                break
            except Exception as err:
                self._log.error('login device failure on {} time since encounter device issue'.format(i))
                self._log.error(err.errmsg)
                check_msg = 'Management server is disconnected,type word'
                if re.search(r'%s' % check_msg,err.errmsg,re.I|re.M) is not None :
                    self._log.debug("Waiting 30s to login device again")
                    time.sleep(30)
                    continue
                else :
                    break

        self.va_set_prompt_state(self.va_prompt_mode())

    def va_prompt_mode(self):
        """
        Get the current cli mode. Execute a new line on the command prompt
        and try to match all the recognizable prompts in the received
        output. If an instance of shell prompt was created, then add the
        normal shell prompt to the list.

        Raises:
            :VaUnknownCliMode:
        """
        prompt = self.get_prompt()
        if  self.dev_type == 'Dm' or self.dev_type == 'Dp' :
            all_prompts=[]
        else :
            all_prompts = [prompt.normal(), prompt.configure()]

        if self.user == self.user_nocli :
            all_prompts.append(Va_shell_prompt().varmournocli_prompt())

        if self._shell_prompt:
            all_prompts.append(self._shell_prompt.normal())

        if self.dev_type == 'Dm' or self.dev_type == 'Dp':
            all_prompts.append(Va_shell_prompt().dpdm_prompt())
            return Va_shell_prompt().SHELL_DPDM_MODE
        else :
            output, match, mode = self.exec_command('', prompt=all_prompts)
            print('node::::{}'.format(mode))
            print(prompt.valid_modes())
            if mode not in prompt.valid_modes():
                raise VaUnknownCliMode(mode)

            return mode

    def va_set_prompt_state(self, state=None):
        """
        Sets the cli state - config | normal. Helpful when executing a
        command. This will be set when a session logs in and sees the
        prompt or cli switches between normal and config.
        """
        if state:
            self._state = state

    def va_enter_config_mode(self):
        """
        Enter the configure mode of the device cli from normal mode.

        Raises:
            :VaCliModeError:

        .. note:
           entry from other modes will be explored and implemented
        """
        prompt = self.get_prompt()

        if self.va_prompt_mode() is prompt.NORMAL_MODE:
            output, match, mode = self.exec_command(
                                      'configure',
                                      prompt=prompt.configure()
                                  )

            if mode is prompt.CONFIG_MODE:
                self.va_set_prompt_state(mode)
                if self._debug:
                    self._log.debug("entered configure mode")
            else:
                raise VaCliModeError('normal', 'config')

    def va_exit_config_mode(self):
        """
        Exit the configure mode of the device cli, and go to the normal mode.

        Raises:
            :VaCliModeError:
        """
        prompt = self.get_prompt()

        if self.va_prompt_mode() is prompt.CONFIG_MODE:
            output, match, mode = self.exec_command(
                                      'exit',
                                      prompt=prompt.normal()
                                  )

            if mode is prompt.NORMAL_MODE:
                self.va_set_prompt_state(mode)
                if self._debug:
                    self._log.debug("exited configure mode")
            else:
                raise VaCliModeError('config', 'normal')

    def va_exec_cli(self, command=None, timeout=60, output_exp=True,**kwargs):
        """
        Method to run cli commands on the va device in normal mode.

        Kwargs:
            :command (str): command string to be run
            :timeout (int): time to wait for the command to execute remotely
            :output_exp (bool): output expected when the command is run

        Returns:
            :output as str generated by the command

        Raises:
            :CliCommandRequired: if command string is not provided
        """
        prompt = self.get_prompt()
        if self._state is prompt.NORMAL_MODE:
            expected_prompt = prompt.normal()
        elif self._state is prompt.CONFIG_MODE:
            expected_prompt = prompt.configure()
        elif self._state is prompt.SHELL_MODE:
            if self.user == self.user_nocli:
                expected_prompt = Va_shell_prompt().varmournocli_prompt()
            elif self.dev_type == 'Dm' or self.dev_type == 'Dp':
                expected_prompt = Va_shell_prompt().dpdm_prompt()
            else :
                expected_prompt = self._shell_prompt.normal()
        elif self._state == Va_shell_prompt().SHELL_VARMOURNOCLI_MODE :
            expected_prompt = Va_shell_prompt().varmournocli_prompt()
        elif self._state == Va_shell_prompt().VA_SHELL_DPDM_RE :
            expected_prompt = Va_shell_prompt().dpdm_prompt()
        else:
            self._log.warn("unknown cli state")

        if not command:
            self._log.info("no cli command!")
            return
        output, match, mode = self.exec_command(
                                  command,
                                  timeout,
                                  output_exp,
                                  expected_prompt,
                                  **kwargs)

        if output_exp:
            return output, match, mode

    def va_config_commit(self):
        """
        method to commit the configuration.
        """
        prompt = self.get_prompt()

        switch_mode = False
        if self.va_prompt_mode() is not prompt.CONFIG_MODE:
            self.va_enter_config_mode()
            switch_mode = True

        output, match, mode = self.va_exec_cli('commit')

        if switch_mode:
            self.va_exit_config_mode()

        return output, match, mode 
    
    def va_enter_cli_from_shell(self, sudo=True):
        """
        Enter the normal mode of cli from shell

        Kwargs:
            :sudo (bool): defining the param for future

        Raises:
            :VaCliModeError:
        """
        shell_prompt =  Va_shell_prompt()
        prompt = self.get_prompt()


        if self.user == self.user_nocli:
            output, match, mode = self.exec_command(
                'cli',
                prompt=[Va_cli_prompt().login(),prompt.login()]
            )
        else :
            prompt_exit_1, prompt_exit_2 = shell_prompt.normal(),\
                                           prompt.login()

            if not sudo:
                prompt_exit_1 = prompt.login()

            if self.va_prompt_mode() is shell_prompt.NORMAL_MODE:
                output, match, mode = self.exec_command(
                                          'exit',
                                          prompt=prompt_exit_1
                                      )

            if sudo:
                if self.va_prompt_mode() is shell_prompt.NORMAL_MODE:
                    output, match, mode = self.exec_command(
                                              'exit',
                                              prompt=prompt_exit_2
                                          )

        if mode is prompt.NORMAL_MODE:
            self.va_set_prompt_state(mode)

            if 'dir' in self._prompt.__class__.__name__.lower():
                self._reset_cli_page_length()

            if self._debug:
                self._log.debug("exited shell mode")
        else:
            raise VaCliModeError('shell', 'cli-normal')

    def va_enter_shell_from_cli(self):
        """
        Enter the shell from normal or configure mode of cli, ti will try to login device 3 times if failure
        """
        prompt = Va_shell_prompt()
        self._shell_prompt = prompt

        states = {
            'enter_shell': ('debug shell', prompt.password_prompt()),
            'enter_paswd': ('vMour!@#)0Ar', prompt.terminal_prompt()),
            'enter_term': ('linux', prompt.normal())
        }

        i = 0
        while i < 3 :
            timeout = 60+i*5
            try :
                if self.va_prompt_mode() is prompt.CLI_MODE:
                    for state in ['enter_shell', 'enter_paswd', 'enter_term']:
                        command, expected_prompt = states.get(state)
                        output, match, mode = self._va_exec_shell_state(
                            state, command, expected_prompt,time_out=timeout
                        )
                    self.va_set_prompt_state(mode)
                    break
            except Exception as err:
                self._log.error(err)
                time.sleep(5)
                i+=1
                continue


    def va_enter_sudo_shell_from_cli(self):
        """
        Enter the sudo shell from normal or configure mode of cli
        """
        self.va_enter_shell_from_cli()
        prompt = self._shell_prompt

        states = {
            'enter_sudo': ('sudo -s', [prompt.sudo_password_prompt(),
                                       prompt.normal()]),
            'enter_sudo_paswd': ('vArmour123', prompt.normal())
        }

        if self.va_prompt_mode() is prompt.NORMAL_MODE:
            for state in ['enter_sudo', 'enter_sudo_paswd']:
                command, expected_prompt = states.get(state)
                output, match, mode = self._va_exec_shell_state(
                    state, command, expected_prompt
                )
                
                if mode is prompt.NORMAL_MODE:
                    break
 
            self.va_set_prompt_state(mode)

    def va_enter_sudo_shell_from_shell(self):
        """
        Enter the sudo shell from normal or configure mode of cli
        """
        prompt = Va_shell_prompt()

        states = {
            'enter_sudo': ('sudo -s', [prompt.sudo_password_prompt(),
                                       prompt.normal()]),
            'enter_sudo_paswd': ('vArmour123', prompt.normal())
        }

        if self.va_prompt_mode() is prompt.SHELL_VARMOURNOCLI_MODE:
            for state in ['enter_sudo', 'enter_sudo_paswd']:
                command, expected_prompt = states.get(state)
                output, match, mode = self._va_exec_shell_state(
                    state, command, expected_prompt
                )

                if mode is prompt.NORMAL_MODE:
                    break

            self.va_set_prompt_state(mode)

    def _va_exec_shell_state(self, state, command, exp_prompt,time_out=60):
        """
        Helper method to drive the shell from one state to the next, when
        entering from cli. When entering from cli the system goes through
        three states - debug shell, shell password, terminal type.

        Args:
            :state (str): the state to transition to
            :command (str): command to execute to transition to next state
            :exp_prompt (tuple): Tuple of compiled regex of the expected
                 prompt of the next state, and prompt mode
            : time_out : time out of get return value after exec command, default is 60 seconds

        Raises:
            :VaCliModeError:
        """
        mode_index = 1
        if type(exp_prompt) is list:
            exp_modes = [prompt[mode_index] for prompt in exp_prompt]
        else:
            exp_modes = [exp_prompt[mode_index]]

        output, match, mode = self.exec_command(
                                  command,
                                  prompt=exp_prompt,
                                  timeout=time_out
                              )

        if mode in exp_modes:
            if self._debug:
                self._log.debug("shell state - {}".format(state))
            return output, match, mode
        else:
            raise VaCliModeError('cli', state)

    def _reset_cli_page_length(self):
        """
        helper method to set cli page length to 0
        """
        prompt = self.get_prompt()

        cmd = 'request cli terminal-length 0'
        output, match, mode = self.exec_command(cmd, prompt=prompt.normal())
        output, match, mode = self.exec_command(
                                  'show cli page', prompt=prompt.normal()
                              )

        cmd_output = output.splitlines()[1]

        if int(cmd_output.split(':')[1].strip()) == 0:
            self._log.info("cli page length set to 0")
