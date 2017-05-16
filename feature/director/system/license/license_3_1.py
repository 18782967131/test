"""coding: utf-8

Copyright 2016 vArmour license function.
All Rights reserved. Confidential

license related features. A superset of features apply
to the product 'dir'
.. moduleauthor:: xliu@varmour.com
"""

import re
import time
from feature import logger
from feature.common import VaFeature

class VaLicense(VaFeature):
    """
    Image implements methods to license related
    features.
    """
    def va_download_license(self,**kwargs):
        """
        Download license via scp or http

        kwargs: dict
            :license (string) :
                HTTP path(http://192.168.1.1/license-file)
                scp path(e.g. scp://john@192.168.1.1:/home/john/license-file)
            :password : input password if type is scp

        returns:
            :False : Failed to download license.
            :Ture: Succeed to download license.

        Examples:
            dir1.va_download_license(**{'license':'scp://varmour@10.11.120.254:/fileserver1/img/va_license.bin',\
                                        'password':'varmour'})
            dir1.va_download_license(**{'license':'http://10.11.120.254/va_license.bin'})
        """
        license = kwargs.get('license')
        type = license.split(':')[0]

        if type == 'scp' and not 'password'in kwargs:
            logger.error('Lack of passowrd while download license via scp')
            return False

        if type == 'scp' :
            output = self._access.va_cli("request download license {}".format(license),\
                                         **{'handle_password':kwargs.get('password')})
            expect_msg = 'File copy done!'
        else :
            output = self._access.va_cli("request download license {}".format(license))
            expect_msg = '200 OK'

        if re.search(r'%s' % expect_msg, output, re.I | re.M) is not None:
            logger.info('Succeed to download license')
        else :
            logger.error("Failed to download image.")
            return False

        return True