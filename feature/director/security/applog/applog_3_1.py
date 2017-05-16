import unittest
from feature.common import VaFeature
from feature import logger
import sys
import jtextfsm


class VaApplog(VaFeature):
    """
    Here we implement the Applog related feature methods
    """

    def va_set_applog_profile(self, app_log_name=None, app_log_rule=None,
                           app_log_application=None, app_log_context=None,
                           app_log_filter=None, app_log_modifier=None,
                           app_log_commit=None):
        """
        :param app_log_name: Profile name
        :param app_log_rule: Matching rule name
        :param app_log_application: Supported Application name
        :param app_log_context: Attribute for provided application
        :param app_log_filter: String to match the context
        :param app_log_modifier: Modifier string (Optional)
        :param app_log_commit: string, will configure on DUT if it is passed

        :return:  complete command if commit is not passed
                  Else : True  on success of configuration on DUT

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
            :ParamRequired: if interface is not provided
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)

        mandatory = [app_log_name, app_log_rule, app_log_application,
                     app_log_context, app_log_filter]

        for param in mandatory:
            if not param:
                pass
                # TODO: raise ValueError
                raise ValueError(" The app profile parameter is not provided, \
                    This is mandetory Argument\n")
        cmd = []
        if app_log_modifier:
            cmd.append('set profile app-log {} rule {} application {} context {}  '
                       'filter {} modifier {}'.format(app_log_name, app_log_rule,
                                                 app_log_application,
                                                 app_log_context,
                                                 app_log_filter,
                                                 app_log_modifier))
            logger.debug('APPLOG command :' + str(cmd))
        else:
            cmd.append('set profile app-log {} rule {} application {} context {} '
                       'filter {} '.format(app_log_name, app_log_rule, app_log_application,
                               app_log_context, app_log_filter))
            logger.debug('APPLOG command :' + str(cmd))

        if app_log_commit:
            cmd.append('commit')

        config_status, output = self._access.va_config(cmd)
        logger.debug('commit status' + str(config_status) + str(output))
        gcmd = 'show running | grep \"set profile app-log\" '
        logger.info("Executing show command : " + str(gcmd))
        routput = self._access.va_cli(gcmd)
        logger.info("the execution status : " + str(routput))
        for i in cmd:
            if i not in routput:
                logger.error('The command is not in running configs: ' + i)
                return False, routput
        logger.debug('The command is available in running configs :' + i)
        return config_status, output


    def va_unset_applog_profile(self, app_log_name=None,
                           app_log_commit=None):
        '''

        :param app_log_name:
        :param app_log_commit:
        :return:
                   complete command if commit is not passed
            Else : True  on success of configuration on DUT

        Raises:
            :AddressValueError: if invalid address is provided
            :NetmaskValueError: if invalid mask is provided
            :ParamRequired: if interface is not provided
        '''

        logger.info("We are in ::" + sys._getframe().f_code.co_name)

        mandatory = [app_log_name]

        for param in mandatory:
            if not param:
                pass
                # TODO: raise ValueError
                raise ValueError(" The app profile parameter is not provided, \
                    This is mandetory Argument\n")
        cmd = []
        cmd.append('unset profile app-log {} '.format(app_log_name))
        logger.debug('APPLOG command :' + str(cmd))

        if app_log_commit:
            cmd.append('commit')

        config_status, output = self._access.va_config(cmd)
        logger.debug('commit status' + str(config_status) + str(output))
        return config_status, output

    def va_verify_app_log(self, policy_name=None, app_log_profile_name=None,
                       policy_template=None):
        """

        :param policy_name:
        :param app_log_profile_name:
        :param policy_template:

        :return: True if app-log profile is associated with policy else False
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)

        mandatory = [app_log_profile_name]

        if not policy_template:
            policy_template = "policy_template"

        for param in mandatory:
            if not param:
                # TODO: raise ValueError
                raise ValueError(" The app profile parameter is not provided, \
                 This is mandetory Argument\n")

        if policy_name:
            cmd = "show policy name {}".format(policy_name)
        else:
            cmd = "show policy"

        output = self._access.exec_command(cmd)

        logger.info("TextFSM parsing POC")
        policy_template = open(policy_template)
        policy_table = jtextfsm.TextFSM(policy_template)

        logger.debug("CLI OUTPUT :\n" + output + "\n\n\n\n")
        policy_fsm_results = policy_table.ParseText(output)

        # Results will be writen to output file
        outputfile_name = open("show_policy_output.csv", "w+")
        outfile = outputfile_name

        for s in policy_table.header:
            outfile.write("%s;" % s)
        outfile.write("\n")

        # Iterate for all the rows
        logger.info(" Here is the result parsed using TextFSM:")
        counter = 0
        for row in policy_fsm_results:
            logger.info(" Row :" + str(counter) + " columns :" + str(row))
            for s in row:
                outfile.write("%s;" % s)
            outfile.write("\n")
            counter += 1
        logger.info(" Number of records:" + str(counter))
        exit()

        # below code will do regular pattern matching
        parsed = self._va_parse_app_profile(output)
        logger.debug(parsed)
        for line in parsed:
            app_log_profile_name = app_log_profile_name
            if line[1] == policy_name and app_log_profile_name in line[8]:
                logger.info(" The profile is associated with policy")
                return True
            else:
                logger.error(" The app profile is not \
                associated with policy")
                return False

    def _va_parse_app_profile(self, output=None):
        """
        Parse the Output of show policy and check the given app profile
        is associated with policy

        :param output:

        :return:
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not output:
            logger.error(" The output is empty string and \
            nothing to verify")
            return False
        logger.debug(" The output :")
        parsed = list()

        for line in output.splitlines()[1:]:
            line = line.strip()
            if not line.startswith('index') and \
                    not line.startswith('=') and \
                    not line.startswith('Total'):
                parsed.append(line.split())
        logger.info(parsed)
        return parsed

    # Might need to move this function to common location
    def va_verify_show_session(self, globaloption=False, id=None, match=None,
                            rate=None, matchstring=None, matchcriteria=None):
        """
        Execute the "show session" command if none of the options are present

        TODO : Need to implement remaining options

        Args:
            globaloption:
            id:
            match:
            rate:
            matchstring:
            matchcriteria:

        Returns:

        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if globaloption:
            cmd = "show session global"
        elif matchstring:
            if matchcriteria:
                cmd = "show session match {} {}".format(matchstring,matchcriteria)
            else:
                cmd = "show session match {} any".format(matchstring)
        else:
            cmd = "show session"
        output = self._access.va_cli(cmd)
        logger.info(" The show session output:\n " + output)
        parsed = matchcriteria in output
        if not parsed:
            logger.error("There NO matching sessions exists")
            return False
        else:
            logger.info(" This has ACTIVE sessions in system:")
            return True

    def _va_parse_show_session(self, output=None):
        """
        Parse the Output of show policy and check the given
        app profile is associated with policy

        :param output:

        :return:
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not output:
            logger.error(" The output is empty string and \
            nothing to verify")
            return False
        logger.debug(" The \"show session\" output :")

    def va_config_global_applog(self, application=None, port=None, commit=None):
        '''
        API to configure global applog

        :param application:
        :param port:
        :param commit:
        :return:
        '''
        logger.info('We are in ::' + sys._getframe().f_code.co_name)
        if not application:
            return False, 'Application name is mandotory'
        cmd = []
        cmd.append('set system app-log %s port %s' %(application, port))
        if commit :
            cmd.append('commit')
        config_status, output = self._access.va_config(cmd)
        print('Configuration of Global APPLOG : ', config_status, output)

        if config_status is False:
            logger.error('Global APPLOG Configuration/commit FAILED')
            return False, output
        else:
            logger.info('Global APPLOG Configuration/commit is successful')
            print('Configuration of GLOBAL APPLOG: ', config_status, output)
            rstatus, output = self.va_globalapplog_conf_in_running(cmd)
            return True, output

    def va_globalapplog_conf_in_running(self, config=None):
        """

        :param config:
        :return:   True if it is enabled
                   False if not
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not config:
            raise ValueError(" Policy name is mandatory for setting policy")
        cmd = 'show running | grep \"set system app-log\" '
        logger.info("Executing show command : " + str(cmd))
        routput = self._access.va_cli(cmd)
        logger.info("the execution status : " + str(routput))
        for i in config:
            if i not in routput:
                logger.error('The command is not in running configs: ' + i)
                return False, routput
        logger.debug('The command is available in running configs :' + i)
        return True, routput

    def va_unconfig_global_applog(self, application=None, port=None,
                               commit=None):
        '''
        API to configure global applog

        :param application:
        :param port:
        :param commit:
        :return:
        '''
        logger.info('We are in ::' + sys._getframe().f_code.co_name)
        if not application:
            return False, 'Application name is mandotory'
        if port:
            cmd = 'unset system app-log %s port %s' %(application, port)
        else:
            cmd = 'unset system app-log %s' %(application)
        if commit :
            cmd.append('commit')
        config_status, output = self._access.va_config(cmd)
        logger.debug('UnConfiguration of Global APPLOG : ' + str(config_status) + str(output))

        if config_status is False:
            logger.error('Global APPLOG Configuration/commit FAILED')
            return False, output
        else:
            logger.info('Global APPLOG Configuration/commit is successful')
            print('Configuration of GLOBAL APPLOG: ', config_status, output)
            return True, output

if __name__ == '__main__':
    unittest.main()
