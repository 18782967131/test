"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Exceptions abstracts the various errors that Va_lab package can
encounter at run time.

.. moduleauthor:: ppenumarthy@varmour.com
"""


class VaLabException(Exception):
    """
    LabSetupError is the base class for all run time errors
    encountered while the test bed is being initialized which
    includes device setup and network topology configuration.
    """
    pass


class UnknownDevice(VaLabException):
    """
    UnknownDevice is raised when the type of the given device is
    not identifiable and hence is not valid.
    """
    def __init__(self, device=None):
        msg = "Not a valid device: '{}'".format(device)

        super(UnknownDevice, self).__init__(msg)


class NoDeviceData(VaLabException):
    """
    NoDeviceData is raised by valid_device if the device data is
    not passed in as part of initialization.
    """
    def __init__(self, device_type=None):
        msg = "data needed for initialization of '{}'"\
              .format(device_type)

        super(NoDeviceData, self).__init__(msg)


class DeviceNotSetup(VaLabException):
    """
    DeviceNotSetup is raised when the device of a particular
    type is not initialized yet
    """
    def __init__(self, device=None):
        msg = "'{}' not initialized yet".format(device)

        super(DeviceNotSetup, self).__init__(msg)


class DevicePropertyError(VaLabException):
    """
    DeviceNotSetup is raised when the device of a particular
    type is not initialized yet
    """
    def __init__(self, device_type=None, prop=None):
        msg = "'{}' needed while making '{}'".format(prop, device_type)

        super(DevicePropertyError, self).__init__(msg)


class LabInfoError(VaLabException):
    """
    LabInfoError is raised when lab setup info is missing - in the yaml
    or any other supported form.
    """
    def __init__(self):
        msg = "lab setup info is missing" 

        super(LabInfoError, self).__init__(msg)


class TestInfoError(VaLabException):
    """
    TestInfoError is raised when test info is missing - in the yaml or
    any other supported form.
    """
    def __init__(self):
        msg = "test info is missing" 

        super(TestInfoError, self).__init__(msg)


class CapableDevNotfound(VaLabException):
    """
    CapableDevNotfound is raised when a capable device required by the
    test cannot be found in the lab.
    """
    def __init__(self, capability=None):
        msg = "capable device of type '{}' not found".format(capability) 

        super(CapableDevNotfound, self).__init__(msg)
