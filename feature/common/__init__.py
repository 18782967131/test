
"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Feature implements the base class for the linux product feature framework
The features for the specific distributions must inherit from this class.

.. moduleauthor:: ppenumarthy@varmour.com
"""

supported = ('4.0', '3.1', '3.2')
version_map = {
    '3.1': '3_1',
    '3.2': '3.2',
    '4.0': '4_0'
}

from feature.common.accesslib import VaAccess  # NOQA


class VaFeature(object):
    """
    Feature implements the base class for director product features.
    """
    def __init__(self, resource=None):
        """
        Initialize the feature object for director product.

        Kwargs:
            :resource (VarmourVm Lab object)
        """
        self._resource = resource

        if not resource.get_access():
            access = VaAccess.get(resource)
            self._access = access(resource)
            resource.set_access(self._access)
        else:
            self._access = resource.get_access()

    def __getattr__(self, method):
        """
        intercept the calls to common system and route it to the
        instance

        args:
            method - method name to be looked up in the parent and
            dispatched
        """
        def route_call_to_common(*args, **kwargs):
            routed = False
            if method in dir(self._parent):
                call = getattr(self._parent, method)
                routed = True
                return call(*args, **kwargs)

            if not routed:
                raise AttributeError(method)

        return route_call_to_common

    @property
    def controller(self):
        """
        get method or the API name
        """
        return self._controller

    @controller.setter
    def controller(self, inst):
        """
        set the instance of Controller for the conroller attribute
        """
        self._controller = inst

    def __del__(self):
        """
        Custom delete to unlink the references to access and resource
        objects.
        """
        self._access = None
        self._resource = None
