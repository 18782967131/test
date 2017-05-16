"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Exceptions abstracts the various errors that Utils package can
encounter at run time.

.. moduleauthor:: ppenumarthy@varmour.com
"""


class VaLabException(Exception):
    """
    VaLabException is the base class for all run time errors
    encountered while the test lab is being initialized which
    includes device setup and network topology configuration.
    """
    pass


class InvalidUser(VaLabException):
    """
    InvalidUser is raised when the name or password properties
    of a va user are missing.
    """
    def __init__(self, prop=None, type=None):
        msg = "'{}' property missing for user of type: '{}'"\
              .format(prop, type)

        super(InvalidUser, self).__init__(msg)


class MgmtIpRequired(VaLabException):
    """
    MgmtIpRequired is raised when the ip address of the lab
    device is missing while racking it
    """
    def __init__(self, type=None):
        msg = "ip address required while racking {}"\
              .format(type)

        super(MgmtIpRequired, self).__init__(msg)


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

class VcenterException(Exception):
    """
    Vcenter Base Exception for handling majority of vcenter failure event
    Raise Exception when vcenter login failure or timeout issue.

    """
    pass


class VcenterObjectNotCreated(VcenterException):
    """
    Vcenter Exception for Invalid Username and Password
    Raise Exception when vcenter login failure.Since
    Vcenter Uses Hash for username and password string,
    Exception can not differentiate exact problem.
    """
    def __init__(self):
        msg = "VcenterException: Vcenter Service Instance Object is not \
        Created"
        super(VcenterObjectNotCreated, self).__init__(msg)


class VmNotFound(VcenterException):
    """
    Virtual Machine not found Exception.When user provides
    wrong or invalid name of VM.This Exception raised.
    """
    def __init__(self, vmname):
        msg = "VcenterException:VM {} is not found in vCenter.\
        Please make sure user provide correct VM name.".format(vmname)
        super(VmNotFound, self).__init__(msg)


class VmNicNotAvailable(VcenterException):
    """
    Virtual Machine has not NIC available for Operation.
    """
    def __init__(self, vmname, interface=None):
        msg = "VcenterException:VM {} has no interface {}\
         available.Please check nic settings in VM".format(vmname, interface)
        super(VmNicNotAvailable, self).__init__(msg)


class VmTagNotFound(VcenterException):
    """
    Exception raising upon missing vArmour vm-tag metadata in to vm
    """
    def __init__(self, vmname):
        msg = "VcenterException:VM {} has no tag inserted.\
        Please check VM tag setting".format(vmname)
        super(VmTagNotFound, self).__init__(msg)


class HostNotFound(VcenterException):
    """
    ESXi host not found Exception.When user provides
    wrong or invalid name of ESXi host.This Exception raised.
    """
    def __init__(self, hostname):
        msg = "VcenterException:Esxi Host {} is not found in vCenter.\
        Please make sure user provide correct host name.".format(hostname)
        super(HostNotFound, self).__init__(msg)


class NetworkNotFound(VcenterException):
    """
    Network not found Exception.When user provides
    wrong or invalid name of network.This Exception raised.
    """
    def __init__(self, net):
        msg = "VcenterException:Network {} is not found in vCenter.\
        Please make sure user provide correct network name.".format(net)
        super(NetworkNotFound, self).__init__(msg)

class ClusterNotFound(VcenterException):
    """
    Cluster not found Exception.When user provides
    wrong or invalid cluster name.This Exception raised.
    """
    def __init__(self, cluster):
        msg = "VcenterException:Cluster {} is not found in vCenter.\
        Please make sure user provide correct cluster name.".format(cluster)
        super(ClusterNotFound, self).__init__(msg)


