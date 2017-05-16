"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Feature implements the base class for the linux product feature framework
The features for the specific distributions must inherit from this class.

.. moduleauthor:: ppenumarthy@varmour.com
"""

supported = ('centos', 'ubuntu')


from vautils.config.linux.accesslib import Mode 


class ConfigUtil(object):
    """
    Feature implements the base class for linux product features.
    """
    def __init__(self, resource=None):
        """
        Initialize the feature object for linux product.

        Kwargs:
            :resource (VaLinux Lab object)
        """
        self._resource = resource
        mode = Mode.get(resource)
        self._access = mode

    def __del__(self):
        """
        Custom delete to unlink the references to model and resource
        objects.
        """
        self._resource = None
        self._access = None
