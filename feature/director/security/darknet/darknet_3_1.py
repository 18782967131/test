import unittest
import sys
import copy

from feature.common import VaFeature
from feature import logger


class VaDarknet(VaFeature):
    """
    VaDarknet  implements methods that configure darknet of the
    varmour director product.
    """
    def va_unconfig_darknet(self, pname=None, pcommit=None):
        """
            API to unconfig  darknet policy
            param    :
                pname : darknet policy name
                pcommit : commit flag set
            example  : va_unconfig_darknet('darknet1')
            return   : True/False
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not pname:
            raise ValueError(" Policy name is mandatory for setting policy")
        cmd = []
        cmd.append('unset deception dark-net %s' % (pname))
        logger.info('Unconfiguring the darknet policy' + str(cmd))
        if pcommit:
            cmd.append('commit')
        logger.info("Now commiting the configs")

        logger.info('Unconfiguring the darknet policy' + str(cmd))
        config_status, output = self._access.va_config(cmd)
        logger.info("the commit status :" + str(config_status) + str(output))
        cmd = 'show running | grep \"deception dark-net\"'
        logger.info("Executing show command" + str(cmd))
        cmdkey = 'set deception dark-net ' + str(pname)
        routput = self._access.va_cli(cmd)
        logger.info("the execution status :" + str(routput))
        logger.debug('Command key to check in running config' + cmdkey)
        if str(cmdkey) in routput:
            logger.error('The config not removed from running configs' +
                         str(cmd))
            return False, routput
        logger.debug('The given policy is removed in running configs')
        return config_status, output


    def va_config_darknet(self, data, *args, **kwargs):
        """
            API to config darknet policy
            param    :
                data1 = {
                     'name'       : 'Darknet policy name'
                     'epi'        : 'EPI UUID' or by default it is all
                     'segment'    : 'segment ID' or by default it is all
                     'from2address': pair address from and to
                     'isenable'   : 'enable' or by default yes
                     'is_commit"  : Commit pending configuration
            example  : va_config_darknet(data1)
            return   : True/False
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)

        data1 = copy.deepcopy(data)

        if 'name' not in data1:
            data1['name'] = 'darknet_new1'
        if 'iscommit' not in data1:
            data1['iscommit'] = 'ON'
        if 'isenable' not in data1:
            data1['isenable'] = 'enable'
        if 'epi' not in data1:
            data1['epi'] = 'all'
        if 'segment' not in data1:
            data1['segment'] = 'all'

        logger.debug('data1........ in darknet,' + str(data1))
        cmds = []

        cmds.append('set deception dark-net %s epi %s segment %s' %
                    (data1['name'], data1['epi'], data1['segment']))

        darknetaddresses = data1['from2address']
        print('Length of from2address list :', len(data1['from2address']),
              darknetaddresses, darknetaddresses[0])
        if type(darknetaddresses) == str:
            cmds.append('set deception dark-net %s address %s to %s' %
                        (data1['name'], darknetaddresses, darknetaddresses))
        elif len(darknetaddresses) == 2 and type(darknetaddresses[0]) == str:
            cmds.append('set deception dark-net %s address %s to %s' %
                    (data1['name'], darknetaddresses[0], darknetaddresses[1]))
        else:
            logger.debug('THIS IS FOR MORE THAN ONE LIST')
            for e in darknetaddresses:
                print(' each element in darknet', e)
                if len(e) == 1:
                    cmds.append('set deception dark-net %s address %s to %s'
                                % (data1['name'], e[0], e[0]))
                else:
                    cmds.append('set deception dark-net %s address %s to %s'
                                % (data1['name'], e[0], e[1]))

        cmds.append('set deception dark-net %s %s' % (data1['name'],
                                                      data1['isenable']))
        logger.info('Darknet command :' + str(cmds))

        config_status, output = self._access.va_config(cmds)
        print('Configuration of DARKNET: ', config_status, output)

        if config_status is False:
            logger.error('Configuration/commit FAILED')
            return False, output
        else:
            logger.info('Configuration and commit is successful')
            print('Configuration of DARKNET: ', config_status, output)
            rstatus, output = self.va_darknetconf_in_running(cmds)
            return True, output

    def va_disable_darknet(self, data, *args, **kwargs):
        '''
        API to disable the darknet policy
        In this case the policy will not be deleted, just disabled state
        :param data:
         Where Data is the dictionary with darknet policy details as 
         shown below:
           data = {
                 'name': 'darknet policy name',
                  'iscommit': ' commit it or not'
           }
        :param args:
        :param kwargs:
        :return:
        '''
        logger.info("We are in ::" + sys._getframe().f_code.co_name)

        data1 = copy.deepcopy(data)

        if 'name' not in data1:
            data1['name'] = 'darknet_new1'
        if 'iscommit' not in data1:
            data1['iscommit'] = 'ON'

        logger.debug('data1........ in darknet,' + str(data1))
        cmds = []

        cmds.append('unset deception dark-net %s enable' % data1['name'])
        if data1['iscommit'] == 'ON':
            cmds.append('commit')
        logger.info('Darknet command :' + str(cmds))

        config_status, output = self._access.va_config(cmds)
        logger.debug('Configuration of DARKNET: {} :: {} '.format(config_status, output))

        if config_status is False:
            logger.error('Configuration/commit FAILED')
            return False, output
        else:
            logger.info('Configuration and commit is successful')
            logger.debug('Configuration of DARKNET: {} :: {} '.format(config_status, output))
            return True, output

    def va_darknetconf_in_running(self, config=None):
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
        cmd = 'show running | grep deception'
        logger.info("Executing show command" + str(cmd))
        output = self._access.va_cli(cmd)
        logger.info("the execution status :" + str(output))
        for i in config:
            if i not in output:
                logger.error('The command is not in running configs' + i)
                return False, output
        logger.debug('The given policy is available in running configs')
        return True, output


    def va_darknet_enabled(self, pname=None):
        """
            API to check given darknet policy enabled?
            param    :
                pname : darknet policy name
                Check given policy is enabled or not.
            example  : va_darknet_enabled('darknet1')
            return   : True if it is enabled
                       False if not
        """
        logger.info("We are in ::" + sys._getframe().f_code.co_name)
        if not pname:
            raise ValueError(" Policy name is mandatory for setting policy")
        cmd = "show deception dark-net {}".format(pname)
        logger.info("Executing show command" + str(cmd))
        cstatus = self._access.va_cli(cmd)
        logger.info("the execution status :" + str(cstatus))
        if 'enable' in str(cstatus):
            logger.debug('The given DARKNET policy is enabled')
            return True, cstatus
        else:
            logger.error('Given DARKNET policy is NOT enabled')
            return False, cstatus

if __name__ == '__main__':
    unittest.main()
