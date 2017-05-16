"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Access abstracts the mechanism used by varmour product to execute the
cli commands remotely. It inherits from VaAccess, which is the common
access abstraction lib implemented for varmour product.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import time, os, platform, re

from feature.common.accesslib import VaAccess as Access
from access import logger


class VaAccess(Access):
    """
    Access implements methods that translate to executing cli commands
    to run specific actions remotely on the varmour product.
    """
    def va_reboot(self, cmd=None, timeout=60, persistent=False, reconnect_delay=100, typemode='cli'):
        """
        method to perform a system reboot on cli or shell mode on a varmour vm.

        Kwargs:
            :cmd (str): command to reboot
            :timeout (int): wait time for device to come back up.
            :persistent (bool): after reboot need access to device
            :reconnect_delay (int): timeout of reconnect
            :typemode (str) : cli or shell
        """
        cli = self.cli
        cli_prompt = cli.get_prompt()
        mgt_ip = self._resource.get_mgmt_ip()

        if typemode == 'cli' :
            self.va_cli()
        else :
            self.va_shell()

        self.va_log_command(cmd)

        if typemode == 'cli':
            i = 0
            while i < 5 :
                try :
                    cli.exec_command(
                        cmd,
                        timeout=timeout,
                        prompt=cli_prompt.sys_reboot()
                    )
                    break
                except Exception as err:
                    cli.va_exec_cli('\003')
                    logger.error(err)
                    i += 1
                    continue

            cli.exec_command(
                'Y',
                timeout=timeout,
                command_output=False,
                prompt=cli_prompt.sys_reboot_ack()
            )
        else :
            try:
                cli.exec_command(cmd)
            except Exception as err:
                logger.info(err)

        if persistent:
            logger.debug('disconnect device')
            self.va_disconnect()
            logger.debug('Sleep 30 seconds to wait device reboot')


            max = int(reconnect_delay/5) + 1
            time.sleep(30)

            logger.debug('Start to connect device after reboot')
            index = 1
            for i in range(1,max) :
                try:
                    if platform.system() == 'Windows':
                        ping_info = os.popen('ping {} -n 2'.format(mgt_ip))
                        match_reg = 'Packets: Sent = \d+, Received = \d+, Lost = (\d+) \(\d+% loss\)'
                    elif platform.system() == 'Darwin':
                        ping_info = os.popen('ping -c 2 {}'.format(mgt_ip))
                        match_reg = '\d+ packets transmitted, \d+ packets received, (\d+)\.\d+% packet loss'
                    else:
                        ping_info = os.popen('ping {} -c 2'.format(mgt_ip))
                        match_reg = '\d+ packets transmitted, \d+ received, (\d+)% packet loss'

                    ping_content = ping_info.readlines()
                    ping_content = ''.join(ping_content)
                    loss_match = re.search(r'%s' % match_reg, ping_content, re.I|re.M)

                    ping_info.close()
                    logger.debug('Check the status of mgt interface')
                    logger.debug(ping_content)
                    if loss_match is not None and int(loss_match.group(1)) == 0:
                        logger.debug('The management interface was UP')
                        logger.debug('Try to connect device on {} time'.format(index))
                        time.sleep(2)
                        self.va_init_cli(timeout=10,persistent=persistent)
                        return True
                    else :
                        log_info = 'The management interface was down. sleep 5 time,'
                        log_info += ' then try to check the interface again'
                        logger.debug(log_info)
                        time.sleep(5)
                        continue
                except Exception as err:
                    logger.error(err)
                    time.sleep(5)
                    continue

                index += 1

    def va_connect(self, timeout=60):
        """
        connect varmour device

        Kwargs:
            :timeout (int): wait time for device to come back up.
        """
        max = int(timeout / 10) + 1
        for i in range(1, max):
            try:
                self.va_init_cli(timeout=timeout, persistent=True)
                return True
            except:
                time.sleep(5)
                continue

    def va_disconnect(self):
        """
         disconnect varmour device

         Kwargs:
             : None
        """
        self.disconnect()