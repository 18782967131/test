""" coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

GenericNode abstracts the notion of a computing device that operates
in a computer network.

.. moduleauthor:: ppenumarthy@varmour.com
"""

from abc import ABCMeta, abstractmethod, abstractproperty
from vautils.resource.user import VaUser
from vautils.resource.network.esxvswitch import EsxVswitch
from access.shell import LinuxShell


class AbstractNode(metaclass=ABCMeta):
    """
    AbstractNode defines the properties of a generic node that can
    operate in a computer network.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractproperty
    def get_mgmt_ip(self):
        pass

    @abstractproperty
    def get_version(self):
        pass

    @abstractproperty
    def get_verbose(self):
        pass

    @abstractproperty
    def get_version_info(self):
        pass

    @abstractproperty
    def get_mgmt_interface(self):
        pass

    @abstractproperty
    def get_hostname(self):
        pass

    @abstractproperty
    def get_user(self):
        pass

    @abstractproperty
    def get_uniq_id(self):
        pass

    @abstractproperty
    def get_rack_id(self):
        pass

    @abstractproperty
    def get_interface(self):
        pass

    @abstractproperty
    def get_nodetype(self):
        pass

    @abstractproperty
    def get_terminal_session(self):
        pass

    @abstractproperty
    def get_rest_util(self):
        pass

    @abstractproperty
    def get_rest_need_auth(self):
        pass

    @abstractproperty
    def get_rest_format_console(self):
        pass


class GenericNode(AbstractNode):
    """
    Base class for all the nodes that are part of a vArmour test network.
    """
    def __init__(
            self,
            mgmt_ip=None,
            hostname=None,
            user=None,
            version=None,
            version_info=None,
            rackid=None,
            interfaces=None,
            type=None,
            mgmt_interface=None,
            uniq_id=None,
            verbose=None,
            rest_need_auth=None,
            rest_format_console=None,
            vmname=None
    ):
        """
        Initializes a specific device object.

        Kwargs:
            :hostname (str): hostname of the device
            :mgmt_ip (str): management ip address of the device
            :role (str): role of the device in the test setup
        """
        self.__mgmt_ip = mgmt_ip
        self.__hostname = hostname
        self.__nodetype = type
        self.__version = version
        self.__version_info = version_info
        self.__user = VaUser(**user)
        self.__rackid = rackid
        self.__interfaces = interfaces
        self.__mgmt_interface = mgmt_interface
        self.__uniq_id = uniq_id
        self.__verbose = verbose
        self.__rest_need_auth = rest_need_auth
        self.__rest_format_console = rest_format_console
        self.__rest_util = None
        self.__session = None
        self.__access = None
        self.__vmname = vmname

    def get_mgmt_ip(self):
        """
        get the mgmt ipv4 address of the node.
        """
        return self.__mgmt_ip

    def get_version(self):
        """
        get the version of the software running on the node.
        """
        return self.__version

    def get_version_info(self):
        """
        get info of the version of the software running on the node.
        """
        return self.__version_info

    def get_hostname(self):
        """
        get the hostname of the node.
        """
        return self.__hostname

    def get_user(self):
        """
        get the user account info.
        """
        return self.__user

    def get_uniq_id(self):
        """
        get the unique id of the device.
        """
        return self.__uniq_id

    def get_rack_id(self):
        """
        get the id of the vm.
        """
        return self.__rackid

    def get_interface(self, intf_name=None):
        """
        get the test interface configuration of the vm.
        """
        if intf_name:
            for interface in self.__interfaces:
                if intf_name == interface.get('name'):
                    return interface

        return self.__interfaces

    def get_mgmt_interface(self):
        """
        get the mgmt interface configuration of the vm.
        """
        return self.__mgmt_interface

    def get_nodetype(self):
        """
        get the vm node type.
        """
        return self.__nodetype

    def set_terminal_session(self, session=None):
        """
        set the terminal session for the vm node type.
        """
        self.__session = session

    def get_terminal_session(self):
        """
        get the terminal session object of the vm node.
        """
        return self.__session

    def set_access(self, access=None):
        """
        set the remote access for the vm node type.
        """
        self.__access = access

    def get_access(self):
        """
        get the remote access object of the vm node.
        """
        return self.__access

    def set_rest_util(self, rest_util=None):
        """
        set the rest util for the dir node type
        """
        self.__rest_util = rest_util

    def get_rest_util(self):
        """
        get the rest util object of the dir node
        """
        return self.__rest_util

    def get_verbose(self):
        """
        get the verbose
        """
        return self.__verbose

    def get_rest_need_auth(self):
        """
        get the rest need auth of the dir node 
        """
        return self.__rest_need_auth

    def get_rest_format_console(self):
        """
        get rest format console of the dir node 
        """
        return self.__rest_format_console

    def get_vmname(self):
        """
        get the vmname
        """
        return self.__vmname

    def __del__(self):
        try:
            self.__session = None
        except AttributeError:
            pass


class AciApic(GenericNode):
    """
    AciEpic class represents the Cisco Epic controller device and inherits
    from the generic node type.
    """
    pass


class Hypervisor(GenericNode):
    """
    Hypervisor class represents a general hypervisor or host node and
    inherits from the generic node type.
    """
    @abstractproperty
    def get_vswitch(self):
        pass


class Esxi(Hypervisor):
    def __init__(self, **kwargs):
        """
        Initialize the Hypervisor object
        """
        if kwargs.get('vswitches'):
            self.__vswitch = kwargs.get('vswitches').split()
            del kwargs['vswitches']

        super(Esxi, self).__init__(**kwargs)

    def get_shell(self):
        """
        get shell access to the hypervisor
        """
        user = self.get_user()
        shell = LinuxShell(
            host=self.get_mgmt_ip(),
            user=user.get('name'),
            pswd=user.get('password')
        )

        return shell

    def setup_vswitch(self, shell=None):
        """
        create vswitch instances if required by the test
        """
        vswitches = list()
        for vswitch in self.__vswitch:
            vswitches.append(EsxVswitch(
                name=vswitch,
                shell=shell
            ))
        self.__vswitch = vswitches

    def get_vswitch(self, name=None):
        """
        get the list of vswitches or the vswitch by name
        """
        for vswitch in self.__vswitch:
            if name == vswitch.get_name():
                return vswitch

        return self.__vswitch


class GenericVm(GenericNode):
    """
    GenericVm class represents a vm that is running on a host and has
    an associated hypervisor.
    """
    @abstractproperty
    def get_hypervisor(self):
        pass


class LinuxVm(GenericVm):
    """
    LinuxVm class represents the type for the linux vm.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object for LinuxVm.
        """
        self.__hypervisor = kwargs.get('hvisor')
        del kwargs['hvisor']

        super(LinuxVm, self).__init__(**kwargs)

    def get_hypervisor(self):
        """
        get the hypervisor node for the vm.
        """
        return self.__hypervisor


class VcenterVm(GenericVm):
    """
    VcneterVm class represents the type for the Vcenter
    Server Appliance.
    """

    def __init__(self, **kwargs):
        """
        Initialize the object for VcenterVm.
        """
        self.__hypervisor = kwargs.get('hvisor')
        del kwargs['hvisor']
        if kwargs.get('hosts'):
            self.__hosts = kwargs.get('hosts')
            del kwargs['hosts']

        super(VcenterVm, self).__init__(**kwargs)

    def get_hypervisor(self):
        """
        get the hypervisor node for the vm.
        """
        return self.__hypervisor


class VarmourVm(GenericVm):
    """
    VarmourVm class represents the type for the varmour vm.
    """

    def __init__(self, **kwargs):
        """
        Initialize the object for VarmourVm.
        """
        self.__hypervisor = kwargs.get('hvisor')
        self.__prompt_type = kwargs.get('prompt_type')
        del kwargs['hvisor']
        del kwargs['prompt_type']

        super(VarmourVm, self).__init__(**kwargs)

    def get_hypervisor(self):
        """
        get the hypervisor node for the vm.
        """
        return self.__hypervisor

    def get_prompt_type(self):
        """
        get the prompt type for the node.
        """
        if self.__prompt_type:
            return self.__prompt_type
        else:
            return self.get_nodetype()
