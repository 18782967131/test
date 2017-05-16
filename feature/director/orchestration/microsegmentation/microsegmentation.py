"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaMicrosegmentationFactory provides corresponding VaMicrosegmentation_3_1 object

.. moduleauthor:: ckung@varmour.com
"""

from feature.director.orchestration.microsegmentation.rel_3_0. \
    microsegmentation_rel_3_0 import VaMicrosegmentation_3_0
from feature.director.orchestration.microsegmentation.rel_3_1. \
    microsegmentation_rel_3_1 import VaMicrosegmentation_3_1
from feature.exceptions import *


class VaMicrosegmentationFactory:
    """
    | MicrosegmentationFactory generates
    | microsegmentation obj according to version input
    |
    | Use this class to get corresponding microsegmentation object
    | Example:
    |     inventory_obj = ...
    |     mseg_obj = VaMicrosegmentationFactory.getFeature(inventory_obj)
    |
    """

    @staticmethod
    def getFeature(dir):
        """
        get microsegmentation object

        :param dir: inventory
        :type dir: inventory object
        :return: microsegmentation object
        :type: microsegmentation object
        """
        if '3.0' in dir.get_version():
            return VaMicrosegmentation_3_0(inv_object=dir)
        elif '3.1' in dir.get_version():
            return VaMicrosegmentation_3_1(inv_object=dir)
        else:
            raise UnsupportedVersion(dir.get_nodetype(), dir.get_version())
