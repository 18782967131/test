"""
coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VMWare vCenter Connector Class that connect to vCenter Server and Gathering
Various vCenter Objects.

.. moduleauthor::jpatel@varmour.com

"""

import atexit
import ssl
from http.client import HTTPException
try :
    from pyVim.connect import SmartConnect, Disconnect
except ImportError :
    from pyvim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
from vautils import logger
from vautils.exceptions import VcenterObjectNotCreated

default_context = ssl._create_default_https_context


class VcenterConnector():
    """
        vCenter connector class that gives service instance after connected
        successfully.By default it uses https connections.
    """
    instance = []
    def __init__(self, vcenter_object=None, **kwargs):
        """
        Initiate vCenter connection object and service instance. service
        instance is a pointer of vcenter where User can iterate  various
        data objects and apply appropriate methods to those objects.

        Args:
            :vcenter_object (object): vcenter object from YAML.
             or
            :username (str): vcenter username
            :ip (str): vcenter ip
            :password (str): vcenter password
        raises:
            :method_fault (fault): pyvmomi method fault.

        """
        self.default_ssl_port = 443
        if not vcenter_object:
            self.user = kwargs.get('username', None)
            self.vcenter_ip = kwargs.get('ip', None)
            self.vcenter_password = kwargs.get('password', None)
        else:
            self.user_object = vcenter_object.get_user()
            self.user = self.user_object.get("name")
            self.vcenter_ip = vcenter_object.get_mgmt_ip()
            self.vcenter_password = self.user_object.get("password")
        self._get_connection()

    def _get_connection(self):
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            context.verify_mode = ssl.CERT_NONE
            self._serviceInstance = SmartConnect(host=self.vcenter_ip,
                                                user=self.user,
                                                pwd=self.vcenter_password,
                                                port=self.default_ssl_port,
                                                sslContext=context)
        except vmodl.MethodFault as error:
            logger.error("Exception Raise : {}".format(error.msg))
        try:
            atexit.register(Disconnect, self._serviceInstance)
        except AttributeError:
            raise VcenterObjectNotCreated
        finally:
            ssl._create_default_https_context = default_context

    def _wait_for_tasks(self, tasks, task_name=""):
        """
        This method is used by inherited objects from this class as well as
        class objects itself_wait_for_task is yield till any operational task
        is complete.It checks given task is completed successfully or failed.
        It dose not return any value.

        Args:
            :task      (list):list of tasks passed by inherited objects.
        Kwargs:
            :task_name (str):name of task passed by inherited objects.example,
                            "vm poweron",
                            "vm poweroff","vmotion vm"

        Raise:
             Task info error on task failure.
        """
        # tasks = tasks
        self._test_connection()
        collection = self._serviceInstance.content.propertyCollector
        task_list = [str(task) for task in tasks]
        object_specification = [vmodl.query.PropertyCollector.
                                ObjectSpec(obj=task) for task in tasks]
        task_pro_spec = vmodl.query.PropertyCollector.\
            PropertySpec(type=vim.Task, pathSet=[], all=True)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = object_specification
        filter_spec.propSet = [task_pro_spec]
        pcfilter = collection.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            while len(task_list):
                update = collection.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue

                            if not str(task) in task_list:
                                continue

                            if state == vim.TaskInfo.State.success:
                                logger.info(
                                    "{} task completed successfully".
                                    format(task_name))
                                task_list.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                logger.info(
                                    "{}  task was failed".format(task_name))
                                raise task.info.error
                version = update.version
        finally:
            if pcfilter:
                pcfilter.Destroy()

    def _get_content(self, type=None):
        """

        This method is used by inherited objects of this class to get various
        vcenter managed object/objects.It returns a list that has a container
        of object/objects. Most of them are iterative and user can get data
        and apply appropriate method written https://github.com/vmware/pyvmomi
        that mapped to vcenter API.

        Args:
            :type      (str): "host":   for getting esxi host (vim.HostSystem)
                                        managed object from vcenter level.
                              "vm"  :   for getting virtual machine
                                        (vim.VirtualMachine) managed object
                                        from vcenter level.
                              "network":for getting network (vim.Network)
                                        managed object from vcenter level.
                              "dvs" :   for getting DVS switch object.
                              "dvsportgroup": not implemented yet.
                              "datastore":for getting datastore(vim.Datastore)
                                        managed object from vcenter level.
                              "folder":    for getting folder level object.

        Return:
            :list      (list) : a list of objects represents managed objects by
                                vcenter.(based on passed type value).

        """
        self._test_connection()
        self.content = self._serviceInstance.RetrieveServiceContent()
        try:
            self.content.rootFolder.childEntity
        except vmodl.fault.MethodNotFound:
            self._get_connection()

        if type is not None:
            type = type.lower()

        if type == "host":
            self.host_view = self.content.viewManager. \
                CreateContainerView(self.content.rootFolder, [
                    vim.HostSystem], True)
            self.host_obj_list = [host for host in self.host_view.view]
            self.host_view.Destroy()
            return self.host_obj_list

        elif type == "vm":
            self.vm_view = self.content.viewManager. \
                CreateContainerView(self.content.rootFolder, [
                    vim.VirtualMachine], True)
            self.vm_obj_list = [vm for vm in self.vm_view.view]
            self.vm_view.Destroy()
            return self.vm_obj_list

        elif type == "network":
            self.network_view = self.content.viewManager. \
                CreateContainerView(self.content.rootFolder, [
                    vim.Network], True)
            self.net_obj_list = [net for net in self.network_view.view]
            self.network_view.Destroy()
            return self.net_obj_list

        elif type == "cluster":
            self.cluster_view = self.content.viewManager. \
                CreateContainerView(
                    self.content.rootFolder,[vim.ClusterComputeResource], True)
            self.cluster_obj = self.cluster_view.view
            self.cluster_view.Destroy()
            return self.cluster_obj

        elif type == "dvs":
            self.dvs_view = self.content.viewManager. \
                CreateContainerView(self.content.rootFolder, [
                    vim.dvs.DistributedVirtualPortgroup], True)
            self.dvs_obj_list = [dvs for dvs in self.dvs_view.view]
            self.dvs_view.Destroy()
            return self.dvs_obj_list

        elif type == "dvs_5":
            self.dvs_view = self.content.viewManager.\
                CreateContainerView(self.content.rootFolder, [
                    vim.dvs.VmwareDistributedVirtualSwitch], True)
            self.dvs_obj_list = [dvs for dvs in self.dvs_view.view]
            self.dvs_view.Destroy()
            return self.dvs_obj_list

        elif type == "dvsportgroup":
            self.dvs_portgroup_view = self.content.viewManager.\
                CreateContainerView(self.content.rootFolder, [
                    vim.dvs.DistributedVirtualPortgroup], True)
            self.dvs_portgroup_list = [dvs_portgroup for dvs_portgroup in self.dvs_portgroup_view.view]
            self.dvs_portgroup_view.Destroy()
            return self.dvs_portgroup_list

        elif type == "datastore":
            self.datastore_view = self.content.viewManager. \
                CreateContainerView(self.content.rootFolder, [
                    vim.Datastore], True)
            self.datastore_obj_list = [ds for ds in self.datastore_view]
            self.datastore_view.Destroy()
            return self.datastore_obj_list

        elif type == "folder":
            self.folder_view = self.content.viewManager. \
                CreateContainerView(
                    self.content.rootFolder, [vim.Folder], True)
            self.folder_obj = self.folder_view.view
            self.folder_view.Destroy()
            return self.folder_obj

        elif type == "content":
            return self.content

        else:
            self.all_mob_view = self.content.viewManager.CreateContainerView(
                self.content.rootFolder,
                [vim.Network, vim.HostSystem,
                 vim.VirtualMachine, vim.ResourcePool, vim.VirtualApp,
                 vim.DistributedVirtualSwitch,
                 vim.DistributedVirtualPortgroup,
                 vim.Datastore, vim.ComputeResource], True)
            self.all_obj_list = [x.name for x in self.all_mob_view.view]
            return self.all_obj_list

    def _test_connection(self):
        content = self._serviceInstance.RetrieveServiceContent()
        try:
            content.rootFolder.childEntity
        except (vmodl.fault.MethodNotFound, HTTPException):
            self._get_connection()
