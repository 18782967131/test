import unittest
import sys
import copy

from feature.common import VaFeature
from feature import logger


class VaDeception(VaFeature):
    """
    VaDeception  implements methods that configure deception of the
    varmour director product. This also includes the hidden commands
    like deception server user credential like user name and passphrase
    """

    def va_config_deceptionserver(self, data, *args, **kwargs):
        """
            API to config deception server policy
            Here user credential are optional, it will be configure
            if user provide the details
            param    :
                data = {
                     'server'       : 'Deception server name'
                     'endpoint-ip'   : 'Server end point IP'
                           - Note that DNS name is not supported
                     'username'   : 'UserID to connect server'
                     'passphrase'  : 'password'
                     'encrypted'  : True/False, by default it is False
                            provided password is encrypted?
                     'is_commit"  : Commit pending configuration
            example  : va_config_deception_server(data)
            return   : tuple with True/False and log output
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)

        data1 = copy.deepcopy(data)

        if 'server' not in data1:
            logger.error('Missing the mandotory argument: Server')
            raise ValueError('Missing the mandotory argument: Server')
        if 'endpoint-ip' not in data1:
            logger.error('Missing the mandotory argument: {}'.format(data1['server']))
            raise ValueError('Missing the mandotory argument: \
            {}'.format(data1['server']))
        if 'iscommit' not in data1:
            data1['iscommit'] = 'ON'
        if 'username' in data1:
            if 'passphrase' not in data:
                logger.error('passphrase required for user {}'.format(data['username']))
                raise ValueError('passphrase required for \
                user {}'.format(data['username']))
        if 'encrypted' not in data1:
            data1['encrypted'] = False

        logger.debug('data1........ in darknet,' + str(data1))
        cmds = []

        cmds.append('set deception server %s endpoint-ip %s' % (data1['server'], data1['endpoint-ip']))
        if 'username' in data1:
            cmds.append('set deception server %s username %s' % (data1['server'], data1['username']))
            if data1['encrypted'] is True:
                cmds.append('set deception server %s passphrase encrypted-password %s' % (data1['server'], data1['passphrase']))
                logger.info('Deception Server command :' + str(cmds))
                config_status, output = self._access.va_config(cmds)
                logger.info('Configuration of DECEPTION: {} : {} '.format(config_status, output))
            else:
                #TODO NEED TO CHECK HOW INTERACTIVE COMMAND EXECUTED IN CLI
                # replace below code with commented one
                logger.info('Deception Server command :' + str(cmds))
                config_status, output = self._access.va_config(cmds)
                logger.info('Configuration of DECEPTION: {} : {} '.format(config_status, output))
                '''
                cmds.append('set deception server %s passphrase ' % (data1['server']))
                config_status, output = self._access.va_config(cmds)
                logger.info('Configuration of DECEPTION: {} : {} '.format(config_status, output))
                #cmds.append( data1['passphrase'])
                #cmds.append( data1['passphrase'])
                config_status, output = self._access.va_cli(data1['passphrase'])
                config_status, output = self._access.va_cli(data1['passphrase'])
                '''
        else:
            logger.info('Deception Server command :' + str(cmds))
            config_status, output = self._access.va_config(cmds)
            logger.info('Configuration of DECEPTION: {} : {} '.format(config_status, output))

        '''logger.info('Deception Server command :' + str(cmds))

        config_status, output = self._access.va_config(cmds)
        print('Configuration of DARKNET: ', config_status, output)
        '''
        if config_status is False:
            logger.error('Configuration/commit FAILED')
            return False, output
        else:
            if 'username' in data1:
                logger.info('Configuration and commit is successful')
                print('Configuration of DECEPTION: ', config_status, output)
                if data1['encrypted'] is True:
                    cmds.pop()
                else:
                    #TODO THESE required when interactive cli is available
                    #cmds.pop()
                    cmds.pop()
            rstatus, output = self.va_deceptionserver_in_running(cmds)
            return True, output

    def va_unconfig_deceptionserver(self, server=None, commit=None):
        """
            API to unconfig  darknet policy
            param    :
                pname : darknet policy name
                pcommit : commit flag set
            example  : va_unconfig_darknet('darknet1')
            return   : True/False
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not server:
            raise ValueError(" Policy name is mandatory for setting policy")
        cmd = []
        cmd.append('unset deception server %s' % (server))
        logger.info('Unconfiguring the darknet policy' + str(cmd))
        if commit:
            cmd.append('commit')
        logger.info("Now commiting the configs")

        logger.info('Unconfiguring the deception server' + str(cmd))
        config_status, output = self._access.va_config(cmd)
        logger.info("the commit status :" + str(config_status) + str(output))
        cmd = 'show running | grep \"deception server\"'
        logger.info("Executing show command" + str(cmd))
        cmdkey = 'set deception server ' + str(server)
        routput = self._access.va_cli(cmd)
        logger.info("the execution status :" + str(routput))
        logger.debug('Command key to check in running config' + cmdkey)
        if str(cmdkey) in routput:
            logger.error('The config not removed from running configs' +
                         str(cmd))
            return False, routput
        logger.debug('The given deception server is removed from running configs')
        return config_status, output



    def va_disable_deceptionserver(self, server=None, commit=None):
        '''
        API to disable the deception server
        In this case the policy will not be deleted, just disabled state
        :param data:
        :param args:
        :param kwargs:
        :return:
        '''
        logger.info("We are in ::" + sys._getframe().f_code.co_name)

        if not server:
            raise ValueError(" Policy name is mandatory for setting policy")

        logger.debug('data1........ in darknet,' + str(data1))
        cmds = []

        cmds.append('set deception server %s disable' % data1['name'])
        if commit:
            cmds.append('commit')
        logger.info('Darknet command :' + str(cmds))

        config_status, output = self._access.va_config(cmds)
        logger.debug('Configuration of Deception disable: {} :: \
                {} '.format(config_status, output))

        if config_status is False:
            logger.error('Configuration/commit FAILED')
            return False, output
        else:
            logger.info('Configuration and commit is successful')
            logger.debug('Configuration of DARKNET: {} \
            :: {} '.format(config_status, output))
            return True, output

    def va_deceptionserver_in_running(self, config=None):
        """
            API to check given darknet policy available in running configs
            param    :
                pname : darknet policy name
                Check given policy is available in running conf or not.
            example  : va_darknetconf_in_running('darknet1')
            return   : True if it is enabled
                       False if not
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not config:
            raise ValueError(" Policy name is mandatory for setting policy")
        cmd = 'show running | grep deception server'
        logger.info("Executing show command" + str(cmd))
        output = self._access.va_cli(cmd)
        logger.info("the execution status :" + str(output))
        for i in config:
            if i not in output:
                logger.error('The command is not in running configs' + i)
                return False, output
        logger.debug('The given policy is available in running configs')
        return True, output


    def va_deceptionserver_enabled(self, server=None):
        """
            API to check given Deception server enabled?

        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not server:
            raise ValueError(" Deception server name is\
             mandatory for setting policy")
        cmd = "show deception server {}".format(server)
        logger.info("Executing show command ->" + str(cmd))
        cstatus = self._access.va_cli(cmd)
        logger.info("the execution status :" + str(cstatus))
        if 'enable' in str(cstatus):
            logger.debug('The given Deception Server is enabled')
            return True, cstatus
        else:
            logger.error('Given Deception Server  is NOT enabled')
            return False, cstatus

    def va_get_ppp_number(self, server=None):
        '''
        API to get PPP ID for given Deception server
        :param server:
        :return:
        '''
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        pppid = -1
        if not server:
            raise ValueError(" Deception server name is\
             mandatory for setting policy")
        cmd = 'show konfd deception'
        logger.info("Executing show command...." + str(cmd))
        status = self._access.va_cli('show konfd deception')
        logger.info("the execution status :::" + str(status))
        serverstatus = status.split('deception_server')[1].split('\n')
        for i in serverstatus:
            if server in i:
                myserver = i
                pppid = myserver.split()[1]
                break
        if 'disable' in myserver:
            logger.error('The server is in disable state : {}'.format(status))
            return False, status
        logger.info('PPP tunnel {} established in Deception server {}'.format('ppp' + myserver.split()[1], server))

        #cmd = 'ifconfig'
        #logger.info(self._access.va_cli('show version'))
        #ifstatus = i.access.va_shell(cmd)

        '''if 'ppp' + myserver.split()[1] in ifstatus:
            logger.info('PPP tunnel {} established in Deception server {}'.format('ppp' + myserver.split()[1], server))
        else:
            logger.error('PPP tunnel {} NOT established in EPI {}'.format('ppp' + myserver.split()[1], server))
            return False, cstatus
        '''
        logger.info('PPP tunnel {} established in EPI {}'.format('ppp' + pppid, server))
        return pppid, status


    def va_deception_pptp_status_in_epi(self, pppid=None):
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not pppid:
            raise ValueError('PPP ID is mandotary')
        cmd = 'ifconfig'
        ifstatus = self._access.va_shell(cmd)

        if 'ppp' + pppid in ifstatus:
            logger.info('PPP tunnel {} established in EPI {}'.format('ppp' + pppid))
            return True, status
        else:
            logger.error('PPP tunnel {} NOT established in EPI {}'.format('ppp' + pppid))
            return False, cstatus


    def va_deceptionserver_pptp_up(self, server=None):
        '''
            API to check the server server pptp tunnel is up or not

        :param server:
        :param epilist:
        :return:

        Steps: get the server name from user
               find the associated ppp interface number
               check if that ppp interface up on all EPI
        '''
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not server:
            raise ValueError(" Deception server name is\
             mandatory for setting policy")
        cmd = 'show konfd deception'
        logger.info("Executing show command...." + str(cmd))
        status = self._access.va_cli('show konfd deception')
        logger.info("the execution status :::" + str(status))
        serverstatus = status.split('deception_server')[1].split('\n')
        for i in serverstatus:
            if server in i:
                myserver = i
                break
        if 'disable' in myserver:
            logger.error('The server is in disable state : {}'.format(status))
            return False, status
        cmd = 'ifconfig'
        logger.info(self._access.va_cli('show version'))
        ifstatus = i.access.va_shell(cmd)
        if 'ppp' + myserver.split()[1] in ifstatus:
            logger.info('PPP tunnel {} established in EPI {}'.format('ppp' + myserver.split()[1], i))
        else:
            logger.error('PPP tunnel {} NOT established in EPI {}'.format('ppp' + myserver.split()[1], i))
            return False, cstatus
        logger.error('PPP tunnel {} established in EPI {}'.format('ppp' + myserver.split()[1], i))
        return True, status
        '''
        #pppnum = myserver.split()[1]
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        if not epilist:
            raise ValueError("EPI is mandatory for checking the status on shell")
        else:
            if type(epilist) is not list:
                logger.info('Single EPI is passed, making this as part of list')
                epilist = list(epilist)
            #if epilist:
            print('##########################################################')
            for i in epilist:
                cmd = 'ifconfig'
                print(self._access.va_cli('show version'))
                ifstatus = i.access.va_shell(cmd)
                if 'ppp'+myserver.split()[1] in ifstatus:
                    logger.info('PPP tunnel {} established in EPI {}'.format('ppp'+myserver.split()[1], i))
                else:
                    logger.error('PPP tunnel {} NOT established in EPI {}'.format('ppp'+myserver.split()[1], i))
                    return False, cstatus
        '''
        logger.error('PPP tunnel {} established in EPI {}'.format('ppp' + myserver.split()[1], i))
        return True, status


    def va_deceptionserver_status_on_epi(self, epiuuid=None, dpname=None):
        """
            API to check the server server pptp tunnel is up or not
        :param epiuuid:
        :param dpname:
        :return:

                Steps: get the server status on given EPI

        Example: status, cmdoutput = dir1.va_deceptionserver_status_on_epi(UUID, dpname)
        """

        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not epiuuid:
            raise ValueError(" UUID is mandotory argument")
        cmd = 'show device '+ epiuuid.strip() + ' deception server'
        logger.info("Executing show command...." + str(cmd))
        status = self._access.va_cli(cmd)
        logger.info("the execution status :::" + str(status))
        if dpname is not None:
            logger.info('DP NAME is provided, verifying the status of DP : {}'.format(dpname))
            for i in status.split('\n'):
                if dpname in i:
                    if i.split()[3] == 'disconnected':
                        logger.info('DP is in NOT CONNECTED STATE for given EPI')
                        return False, status
                    else:
                        logger.info('DP is in  CONNECTED STATE for given EPI')
                        return True, status
        elif 'disconnected' in status:
            logger.info('All servers are NOT CONNECTED STATE for given EPI')
            return False, status
        logger.info('All servers are in CONNECTED STATE for given EPI')
        return True, status





if __name__ == '__main__':
    unittest.main()
