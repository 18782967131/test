"""coding: utf-8

Copyright 2016 vArmour image function.
All Rights reserved. Confidential

Image related features. A superset of features apply
to the product 'dir', 'cp', 'ep', 'epi,
.. moduleauthor:: xliu@varmour.com
"""

import re
import time
from feature.director.system.chassis.chassis_3_1 import VaChassis as Chassis
from feature import logger
from feature.common import VaFeature
from feature import Controller

class VaImage(VaFeature):
    """
    Image implements methods to download or install image related
    features.
    """

    def __init__(self, resource=None):
        """
        instantiate the feature object by calling parent's init. then
        setup controller to create feature objects for other features
        to be used within this feature. Also set the common system
        instance to the parent attribute - instead of inheriting it
        and complicating the dependency we are holding a link to the
        common system feature and routing calls to it through getattr.

        kwargs:
            resource - VaResource object
        """
        super(VaImage, self).__init__(resource)
        self._parent = None

        other_features = ['chassis','system','system-common']
        self.controller = Controller(resource, other_features)

        common = '_'.join(('', 'system-common'))
        if common in self.controller.__dict__.keys():
            self._parent = self.controller.__dict__.get(common)

    def va_download_image(self, image, download_delay=300, **kwargs):
        """
        Download image from image server

        Arguments:
            :image (str): Software image location. for example:
                HTTP path(http://192.168.1.1/image-file.tar)
            :download_delay (int) : time of download image of each device.
            :kwargs (dict) : support in the further. for example. scp.

        returns:
            :Talse: Failed to download image.
            :Ture: Succeed to download image.

        Examples:
            va_download_image('http://192.168.1.1/image-file.tar')
        """
        self._access.va_cli("request system delete device all image all")
        rt = self._access.va_cli("request download software {}".format(image), download_delay)

        if re.search(r'file already exist', rt, re.I | re.M) is not None:
            loginfo = 'Not need to download software since '
            loginfo += 'the image have exists on the device'
            logger.info(loginfo)
            return True
        elif re.search(r'(download failed)|(download file is empty)', rt, re.I | re.M) \
                is not None:
            logger.error("Failed to download image.")
            return False

        time.sleep(30)

        if not self.va_check_download_status_for_ep_or_cp():
            return False

        if not self.va_check_download_status_for_epi():
            return False

        logger.info('***********************************************************')
        logger.info("*******************download completed to all***************")
        logger.info('***********************************************************')
        return True

    def va_check_download_status_for_ep_or_cp(self, **kwargs):
        """
        Check the status of download image for EP or CP. it will return false if
        download image does not finish in (number of activate device *  1 minutes + 1minutes).

        Arguments:
            None

        returns:
            :False: Failed to download image.
            :True: Succeed to download image.

        Examples:
            va_check_download_status_for_ep_or_cp()
        """

        if not 'num_activate_devs' in dir(self):
            self.num_activate_devs = self.controller.va_get_active_device()

        num_activate_dev = int(self.num_activate_devs['active_devices'])
        max = num_activate_dev * 15 + 4
        result = False
        exp = 'system software download status: [\d+] completed'
        exp +=', 0 in-progress, 0 failed, 0 not run'

        logger.info('Check the status of download image for EP or CP')
        output = self._access.va_cli("show download all")
        for i in range(1, max):
            if re.search(exp, output, re.I | re.M) is not None:
                result = True
                break
            else:
                output = self._access.va_cli("show download all")
                result = False
                time.sleep(20)

        if not result:
            logger.error('Failed to check the status of download image')
            self._access.va_cli("show chassis database device all")
            return False

        logger.info('Check the status of download image. Done')
        return result

    def va_check_download_status_for_epi(self,**kwargs):
        """
              Check the status of download image for EPi. it will return false if
              download image does not finish in (number of activate device *  1 minutes + 0.5 minutes).

              Arguments:
                  None

              returns:
                  :False: Failed to download image.
                  :True: Succeed to download image.

              Examples:
                  va_check_download_status_for_epi()
        """
        if not 'num_activate_devs' in dir(self):
            self.num_activate_devs = self.controller.va_get_active_device()

        num_activate_dev = int(self.num_activate_devs['active_epis'])
        max = num_activate_dev * 15 + 5
        result = False
        exp = 'system software download status: [\d+] completed'
        exp += ', 0 in-progress, 0 failed, 0 not run'

        logger.info('Check the status of download image for EPI')
        output = self._access.va_cli("show download epi")
        for i in range(1, max):
            if re.search(exp, output, re.I | re.M) is not None:
                result = True
                break
            else:
                output = self._access.va_cli("show download epi")
                result = False
                time.sleep(20)

        if not result :
            logger.error('Failed to check the status of download image for EPI')
            self._access.va_cli("show chassis database device all")
            return False

        logger.info('Check the status of download image for EPI. Done')
        return result

    def va_check_install_status_for_ep_or_cp(self,**kwargs):
        """
        Check the status of install image for EP or CP. it will return false if
        install image does not finish in (number of activate device *  2 minutes + 1minutes).

        Arguments:
            None

        returns:
            :False: Failed to install image.
            :True: Succeed to install image.

        Examples:
            va_check_install_status_for_ep_or_cp()
        """

        if not 'num_activate_devs' in dir(self) :
            self.num_activate_devs = self.controller.va_get_active_device()

        num_activate_dev = int(self.num_activate_devs['active_devices'])
        max = num_activate_dev * 15 + 4
        result = False
        exp = 'system software install status: [\d+] completed'
        exp += ', 0 in-progress, 0 failed, 0 not run'

        logger.info('Check the status of install image for EP or CP')
        output = self._access.va_cli("show install all")
        for i in range(1, max):
            if re.search(exp, output, re.I | re.M) is not None:
                result = True
                break
            else:
                output = self._access.va_cli("show install all")
                result = False
                time.sleep(20)

        if not result:
            logger.error('Failed to check the status of install image')
            self._access.va_cli("show chassis database device all")
            return False

        logger.info('Check the status of install image. Done')
        return result

    def va_check_install_status_for_epi(self,**kwargs):
        """
              Check the status of install image for EPi. it will return false if
              install image does not finish in (number of activate device *  2 minutes + 0.5 minutes).

              Arguments:
                  None

              returns:
                  :False: Failed to download image.
                  :True: Succeed to download image.

              Examples:
                  va_check_download_status_for_epi()
        """
        if not 'num_activate_devs' in dir(self):
            self.num_activate_devs = self.controller.va_get_active_device()

        num_activate_dev = self.num_activate_devs['active_epis']
        max = int(num_activate_dev) * 15 + 2
        result = False
        exp = 'system software install status: [\d+] completed'
        exp += ', 0 in-progress, 0 failed, 0 not run'

        logger.info('Check the status of install image for EPI')
        output = self._access.va_cli("show install epi")
        for i in range(1, max):
            if re.search(exp, output, re.I | re.M) is not None:
                result = True
                break
            else:
                output = self._access.va_cli("show install epi")
                result = False
                time.sleep(20)

        if not result :
            logger.error('Failed to check the status of install image for EPI')
            self._access.va_cli("show chassis database device all")
            return False

        logger.info('Check the status of install image for EPI. Done')

        return result

    def va_install_image(self, image, **kwargs ):
        """
        Install image

        Arguments:
            :image (str): Software image name
            :kwargs (dict) :
                'install_os'    :  primary/secondary
                'install_delay' : time of install image
        returns:
            :False: Failed to install image.
            :True: Succeed to install image.

        Examples:
            va_install_image('image-file.tar')
            va_install_image('image-file.tar',\
                {'install_os':'primary','install_delay':200})
        """
        if not 'install_os' in kwargs:
            install_os = 'primary'
        else :
            install_os = kwargs['install_os']

        if not 'install_delay' in kwargs:
            install_delay = 300
        else :
            install_delay = kwargs['install_delay']

        if not 'reboot_delay' in kwargs:
            reboot_delay = 120
        else:
            reboot_delay = kwargs['reboot_delay']

        logger.info('install delay is {}'.format(install_delay))
        self._access.va_cli("request install software {} {}"\
                            .format(image, install_os),install_delay)

        #check the status of install firmeare
        if not self.va_check_install_status_for_ep_or_cp():
            return False

        if not self.va_check_install_status_for_epi() :
            return False

        logger.debug("Change boot-sector to %s" % install_os)
        self._access.va_cli("request system boot-sector {}" .format(install_os))
        time.sleep(30)

        logger.info("**************Completed install image to all devices************")
        return True

    def va_update_firmware(self, image, **kwargs ):
        """
        Update firmware

        Arguments:
            :image (str): Software image name
            :kwargs (dict) :
                'install_os'    :  primary/secondary
                'install_delay' : time of install image
                :download_delay (int) : time of download image of each device.
                'reboot_delay'   : time of reboot devices
        returns:
            :False: Failed to install image.
            :True: Succeed to install image.

        Examples:
            va_update_firmware('http://10.11.120.141/image-file.tar')
        """
        if not 'install_os' in kwargs:
            install_os = 'primary'
        else :
            install_os = kwargs['install_os']

        image_info = image.split('/')
        image_list_len = len(image_info)
        image_name = image_info[image_list_len - 1]
        image_name = image_name.strip()
        curr_version = self.va_get_version()
        image_v_info = re.search(r'image-(.*).rel.tar', image_name ,re.I|re.M)
        if image_v_info is not None :
            name = image_v_info.group(1)

        #check device version if it is same as the image
        if (name == curr_version) :
            logger.info("Not need to update firmware. device version is %s" % curr_version)
            boot_directory = self.va_show_system().get('boot directory')
            if boot_directory == 0 or boot_directory != install_os :
                self._access.va_cli("request system boot-sector %s" % install_os)

            return True
        else :
            self._va_clear_epi_config()

            dev_nums1 = self.controller.va_get_active_device()
            dev_num1 = int(dev_nums1['active_devices'])
            epi_num1 = int(dev_nums1['active_epis'])

            if not self.va_download_image(image) :
                return False

            if not self.va_install_image(image_name,**{'install_os':install_os}) :
                return False

            self.va_reboot(persistent=True, reconnect_delay=600)

            # check all device status
            curr_mode = self.va_get_mode()
            time_out = (int(dev_num1) + int(epi_num1)) * 16
            if (curr_mode == "B") or (curr_mode == "PB"):
                logger.info('PB does not support using "show chassis" command')
            else:
                for i in range(1, time_out):
                    ret = self.controller.va_check_chassis_status("is_ha")
                    if ret:
                        break

                    time.sleep(20)

                if not ret:
                    logger.error("The status of device is inactive after waiting {} seconds"\
                                 .format(int(time_out) * 20))
                    self.va_show_chassis()
                    return False

            logger.info('Check devices connections after reboot device.')
            dev_nums2 = self.controller.va_get_active_device()
            dev_num2 = int(dev_nums2['active_devices'])
            epi_num2 = int(dev_nums2['active_epis'])

            check_dev_rt = 0
            for i in range(1, time_out):
                if (dev_num1 != dev_num2) or (epi_num1 != epi_num2):
                    dev_nums2 = self.controller.va_get_active_device()
                    dev_num2 = int(dev_nums2['active_devices'])
                    epi_num2 = int(dev_nums2['active_epis'])
                    time.sleep(20)
                    continue
                else:
                    check_dev_rt = 1
                    break

            if check_dev_rt :
                logger.info("The status of devices are correct")
            else :
                logger.error('The status of devices are incorrect after upgrading')
                return False

            logger.info('Check new version after install')
            curr_version  = self.va_get_version()
            #remove -ep from image name so that the cmp will work
            image_name = re.sub(r'-ep','',image_name)
            if re.search(curr_version ,image_name,re.I) is not None :
                logger.info("Succeed to update firmware to {}".format(curr_version))
            else :
                logger.error("Failed to update firmware to {} (image:{})".\
                             format(curr_version ,image_name))
                return False

        logger.info("**************Completed install image to all devices************")
        return True

    def _va_clear_epi_config(self) :
        """
        clear epi config according to show running-config since command of epi have independence

        Arguments:
            None
        returns:
            :False: Failed to clear epi configuration
            :True: Succeed to clear epi configuration

        Examples:
            _va_clear_epi_config()
        """
        logger.info('Clear epi related command to work around the status of \
                        EPI is incorrect issue.')
        running_infos = self.controller.va_show_running_config()
        running_info = '\n'.join(running_infos)
        reg_epi = re.compile(r'set chassis epi\s+.*\s+inline')

        match_epi_result = reg_epi.search(running_info)
        if match_epi_result is not None:
            cmdList_epi = re.findall(r'set micro-segmentation epi\s+.*', running_info, re.M)
            cmdList_epi.append('commit')
            cmdList_epi.extend(reg_epi.findall(running_info))
            cmdList_epi.append('commit')
            unset_cmdList = list()
            for cmd in cmdList_epi:
                unset_cmd = re.sub(r'^set ', 'unset ', cmd.strip())
                unset_cmdList.append(unset_cmd)
            try:
                self.config(unset_cmdList)
            except Exception as msg:
                self._access.va_config('rollback')
                self._access.va_config(unset_cmdList)

            running_infos = self.controller.va_show_running_config()
            running_info = '\n'.join(running_infos)
            if reg_epi.search(running_info) is not None:
                self._access.va_config('rollback')
                logger.error("lFailed to remove configuration of EPI")
                return False
            logger.info("Succeed to remove configuration of EPI")

        return True
