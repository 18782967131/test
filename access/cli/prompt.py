"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Prompt asbtracts the various components that make up the cli prompt
string. The resulting string is joined and compiled that could be used
for regex matching, when receiving output from the Terminal server.

Eventually this will be a generic implementation and various vendor
shell and cli command prompts will inherit from Command_prompt.

.. moduleauthor:: ppenumarthy@varmour.com 
"""

import re

from access import logger


class Command_prompt(object):
    """
    Implements a data type for the components of a generic command
    prompt string.

    The various components are defined as class level constants and are
    assigned to the regex strings that would match them. The order in
    which the components appear in the prompt, is the same as the order
    of elements in the COMPONENTS array
    """
    COMPONENTS = ['login_pre', 'user', 'ampersand', 'host', 'seperator',
                  'homedir', 'terminator']

    ANY_LOGIN_PREFIX_RE = '(^|\n|\r)'
    ANY_NORMAL_PREFIX_RE = ANY_LOGIN_PREFIX_RE
    ANY_USER_RE = '(?P<name>[\w\-\.]+)'
    ANY_AMPERSAND_RE = '@'
    ANY_HOST_RE = '(?P<host>[\w+/\-\d+\.]+)'
    ANY_SEP_RE = '(#|:)'
    ANY_HOMEDIR_RE = '(?P<homedir>[\w+/\-]+)'
    ANY_TERMINATOR_RE = '(#|\$|>)[ \t]*$'

    def __init__(
        self,
        login_pre=ANY_LOGIN_PREFIX_RE,
        normal_pre=ANY_NORMAL_PREFIX_RE,
        user=ANY_USER_RE,
        ampersand=ANY_AMPERSAND_RE,
        host=ANY_HOST_RE,
        seperator=ANY_SEP_RE,
        homedir=ANY_HOMEDIR_RE,
        terminator=ANY_TERMINATOR_RE
    ):
        """
        Initializes the Va_cli_prompt object

        Kwargs:
            :login_pre (str): regex for the prefix of a login prompt
            :normal_pre (str): regex for the prefix of a normal prompt
            :user (str): regex for the user trying to log in
            :user_at_host (str): regex for the str joining user and host
            :host (str): regex for the host name of the Terminal server
            :seperator (str): regex for the seperator string
            :terminator (str): regex for the str terminating the prompt
        """
        self.login_pre = login_pre
        self.normal_pre = normal_pre
        self.user = user
        self.ampersand = ampersand
        self.host = host
        self.seperator = seperator
        self.homedir = homedir
        self.terminator = terminator

        self._log = logger

    def _compile_regex(self, parts):
        """
        Concatenates the various components of a cli prompt and compiles it.

        Raises:
            :re.error:
        """
        regex_str = ''
        for part in parts:
            regex_str += getattr(self, part)

        try:
            return re.compile(regex_str)
        except re.error:
            # TODO: handler. for now just re raise
            raise


class Bash_prompt(Command_prompt):
    """
    It is almost a generic command prompt is'nt it.
    """
    pass


class Cli_prompt(Command_prompt):
    """
    Implements a data type for the components of a generic cli prompt
    string. It inherits from 'str' class so that string operations can
    be performed on the various components or the resulting string
    concatenated from the components.

    The various components are defined as class level constants and are
    assigned to the regex strings that would match them. The order in
    which the components appear is the same as the order of elements
    in the COMPONENTS array
    """
    ANY_CONFIG_RE = '\(config\)'

    NORMAL_MODE = 1
    CONFIG_MODE = 2
    SHELL_MODE = 3
    SHELL_VARMOURNOCLI_MODE = 9
    REBOOT_MODE = 6
    RESET_ALL_MODE = 7


class Va_shell_prompt(Bash_prompt):
    """
    Implements a data type for the components of the vArmour shell prompt
    string. It inherits from Bash_prompt class.

    Example:
        :normal mode: varmour@varmour-dir:/usr-varmour/home/varmour$
    """
    CLI_MODE = 1
    NORMAL_MODE = 3
    PASSWORD = 4
    TERM_TYPE = 5
    SHELL_VARMOURNOCLI_MODE = 9

    VA_SHELL_PASSWORD_RE = 'Input password:'
    VA_SHELL_TERM_TYPE_RE = 'Terminal type\?'
    VA_SUDO_SHELL_PASSWORD_RE = 'password for varmour(()|(\_no\_cli)):'
    VA_SHELL_VARMOURNOCLI_RE = '@vArmour:.*$'

    def __init__(self):
        """
        Initialize vArmour shell prompt. First initialize through the super
        class - then set the password and terminal type prompt attributes
        """
        super(Va_shell_prompt, self).__init__()

        self.password = self.VA_SHELL_PASSWORD_RE
        self.term_type = self.VA_SHELL_TERM_TYPE_RE
        self.sudo_password = self.VA_SUDO_SHELL_PASSWORD_RE
        self.shell_varmournocli = self.VA_SHELL_VARMOURNOCLI_RE
        
    def normal(self):
        """
        Constructs and compiles a regex that would match the shell prompt
        in normal mode or when switch happens from cli to shell.

        Returns:
            A tuple of compiled regex and the prompt mode
        """

        return self._compile_regex(self.COMPONENTS), self.NORMAL_MODE

    def password_prompt(self):
        """
        Constructs and compiles a regex that would match the shell prompt
        in normal mode or when switch happens from cli to shell.

        Returns:
            A tuple of compiled regex and the prompt mode
        """

        return self._compile_regex(['password']), self.PASSWORD

    def sudo_password_prompt(self):
        """
        Constructs and compiles a regex that would match the shell prompt
        in normal mode or when switch happens from cli to shell.

        Returns:
            A tuple of compiled regex and the prompt mode
        """
        return self._compile_regex(['sudo_password']), self.PASSWORD

    def varmournocli_prompt(self):
        """
        Constructs and compiles a regex that would match the shell prompt
        in normal mode or when switch happens from cli to shell.

        Returns:
            A tuple of compiled regex and the prompt mode
        """
        return self._compile_regex(['shell_varmournocli']), self.SHELL_VARMOURNOCLI_MODE

    def terminal_prompt(self):
        """
        Constructs and compiles a regex that would match the shell prompt
        in normal mode or when switch happens from cli to shell.

        Returns:
            A tuple of compiled regex and the prompt mode
        """

        return self._compile_regex(['term_type']), self.TERM_TYPE


class Va_cli_prompt(Cli_prompt):
    """
    Implements a data type for the components of the vArmour cli prompt
    string. It inherits from Cli_prompt class.

    Examples:
        :normal mode: varmour@varmour-dir#ROOT(M)>
        :config mode: varmour@varmour-dir#ROOT(config)(M)>
    """
    vARMOUR_USER_PERM_RE = '(?P<perm>\w+)'
    vARMOUR_ANY_ROLE_RE = '(\((?P<role>\w{1,2})\))?'
    vARMOUR_ANY_ROLE_RE1 = '(\(B\))'
    vARMOUR_LOGIN_PREFIX_RE = '(^|\n\n|\r)'
    vARMOUR_LOGIN_PREFIX_RE1 = '(..\n)'
    vARMOUR_CONFIG_RE = '\(config\)'
    vARMOUR_REBOOT_RE = \
        'You are about to reboot the device, are you sure\? \(Y/N\)\?'
    vARMOUR_REBOOT_ACK_RE = 'Y|y'
    vARMOUR_RESET_ALL_RE = \
        'You are about to reset the system configuration, are you sure\? \(Y/N\)\?'

    COMPONENTS = ['login_pre', 'normal_pre', 'user', 'ampersand',
                  'host', 'seperator', 'user_type', 'config', 'role',
                  'terminator']

    def __init__(self):
        """
        Initialize va cli prompt string. First initialize through super
        class and then set the vArmour specific attributes.

        
        Kwargs:
            :user_type (str): regex for the user type (as root|non-root)
            :config (str): regex for the config prompt if config mode
            :role (str): regex for the role of the host machine
        """
        super(Va_cli_prompt, self).__init__()

        self.login_pre = self.vARMOUR_LOGIN_PREFIX_RE
        self.user_type = self.vARMOUR_USER_PERM_RE
        self.role = self.vARMOUR_ANY_ROLE_RE
        self.config = self.vARMOUR_CONFIG_RE
        self.reboot = self.vARMOUR_REBOOT_RE
        self.reset_all = self.vARMOUR_RESET_ALL_RE
        self.reboot_ack = self.vARMOUR_REBOOT_ACK_RE

    def login(self):
        """
        Constructs and compiles a regex that would match the cli prompt
        on login.

        Returns:
            A tuple of compiled regex and the prompt mode
        """
        components = self.COMPONENTS[0:1] + self.COMPONENTS[2:7] +\
            self.COMPONENTS[8:]
        components1 = [self.vARMOUR_LOGIN_PREFIX_RE1] + self.COMPONENTS[2:7] +\
                      [self.vARMOUR_ANY_ROLE_RE1]
        compile_regex = [self._compile_regex(components)]
        self.login_pre = self.vARMOUR_LOGIN_PREFIX_RE1
        self.role = self.vARMOUR_ANY_ROLE_RE1
        components1 = self.COMPONENTS[0:1] + self.COMPONENTS[2:7] + \
                    self.COMPONENTS[8:]
        compile_regex.append(self._compile_regex(components1))
        self.login_pre = self.vARMOUR_LOGIN_PREFIX_RE
        self.role = self.vARMOUR_ANY_ROLE_RE
        return compile_regex, self.NORMAL_MODE

    def normal(self):
        """
        Constructs and compiles a regex that would match the cli prompt
        in normal mode or when commands are executed in normal mode.

        Returns:
            A tuple of compiled regex and the prompt mode
        """
        components = self.COMPONENTS[1:7] + self.COMPONENTS[8:]

        return self._compile_regex(components), self.NORMAL_MODE

    def configure(self):
        """
        Constructs and compiles a regex that would match the cli prompt
        in config mode or when commands are executed in config mode.

        Returns:
            A tuple of compiled regex and the prompt mode
        """
        components = self.COMPONENTS[1:]

        return self._compile_regex(components), self.CONFIG_MODE

    def sys_reboot(self):
        """
        Constructs and compiles a regex that would match the cli prompt
        when a reboot command is executed. 

        Returns:
            A tuple of compiled regex and the prompt mode
        """

        return self._compile_regex(['reboot']), self.REBOOT_MODE 

    def sys_reset_all(self):
        """
        Constructs and compiles a regex that would match the cli prompt
        when a reset all command is executed. 

        Returns:
            A tuple of compiled regex and the prompt mode
        """

        return self._compile_regex(['reset_all']), self.RESET_ALL_MODE 
    
    def sys_reboot_ack(self):
        """
        Constructs and compiles a regex that would match the cli prompt
        when a reboot command is executed. 

        Returns:
            A tuple of compiled regex and the prompt mode
        """

        return self._compile_regex(['reboot_ack']), self.REBOOT_MODE 
    
    def valid_modes(self):
        """
        Get the valid prompt modes for va_cli
        """
        return [1, 2, 3, 4, 5, 6, 7,9]


class Dir_prompt(Va_cli_prompt):
    """
    Implements a data type for the components of the vArmour director
    device cli prompt string. It inherits from Va_Cli_prompt class.
    This class is like a stub providing device type to prompt mapping.
    """
    pass


class Ep_prompt(Va_cli_prompt):
    """
    Implements a data type for the components of the vArmour ep device 
    cli prompt string. It inherits from Va_Cli_prompt class. This
    class is like a stub providing device type to prompt mapping.
    """
    vARMOUR_LOGIN_PREFIX_RE = '(|^|\n|\r)'


class Epi_prompt(Va_cli_prompt):
    """
    Implements a data type for the components of the vArmour epi device 
    cli prompt string. It inherits from Va_Cli_prompt class. This
    class is like a stub providing device type to prompt mapping.
    """
    vARMOUR_LOGIN_PREFIX_RE = '(|^|\n|\r)'
    ANY_TERMINATOR_RE = '[ \t]*$'


class Cp_prompt(Va_cli_prompt):
    """
    Implements a data type for the components of the vArmour cli prompt
    string. It inherits from Cli_prompt class.

    Examples:
        :normal mode: varmour@varmour-dir#ROOT(M)>
        :config mode: varmour@varmour-dir#ROOT(config)(M)>
    """
    vARMOUR_LOGIN_PREFIX_RE = '(|^|\n|\r)'
    SPACE_RE = '\s+'
    START_PARANTHESIS_RE = '('
    END_PARANTHESIS_RE = ')'
    END_QUANTIFIER_RE = '{2}'

    def __init__(self):
        """
        Initialize va cli prompt string. First initialize through super
        class and then set the vArmour specific attributes.

        
        Kwargs:
            :user_type (str): regex for the user type (as root|non-root)
            :config (str): regex for the config prompt if config mode
            :role (str): regex for the role of the host machine
        """
        super(Cp_prompt, self).__init__()

        self.space = self.SPACE_RE
        self.start_paran = self.START_PARANTHESIS_RE
        self.end_paran = self.END_PARANTHESIS_RE
        self.end_quantifier = self.END_QUANTIFIER_RE

    def login(self):
        """
        Constructs and compiles a regex that would match the cli prompt
        on login.

        Returns:
            A tuple of compiled regex and the prompt mode
        """
        components = self.COMPONENTS[0:7] + ['terminator']
        return self._compile_regex(components), self.NORMAL_MODE
