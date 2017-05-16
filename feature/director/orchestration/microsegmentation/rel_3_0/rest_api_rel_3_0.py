"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaRestapi contains all va rest features

.. moduleauthor:: ckung@varmour.com
"""

from feature.director.orchestration.microsegmentation.rel_3_0. \
    rest_url_factory_rel_3_0 import VaResturlfactory
from access.rest import Restutil
from requests.auth import HTTPBasicAuth
from feature.exceptions import *


class VaRestapi:
    """
    VaRestapi has all va rest request
    All methods in this class involves rest call
    """

    def __init__(self, **kwargs):
        """
        constructor has restUtil objects
        Args:
            **kwargs:
                :inv_object (inventory_object): inventory object
                or
                :ip (str): director ip
                :username (str): director username
                :password (str): director password
                :verbose (boolean): enable/disable logger
        """
        if kwargs.get('inv_object', None):
            dir_object = kwargs.get('inv_object', None)
            self.username = dir_object.get_user().get('name')
            self.password = dir_object.get_user().get('password')
            self.url_factory = VaResturlfactory(dir_object.get_mgmt_ip())
            self.verbose = dir_object.get_verbose()
        else:
            self.username = kwargs.get('username', None)
            self.password = kwargs.get('password', None)
            self.url_factory = VaResturlfactory(kwargs.get('ip', None))
            self.verbose = kwargs.get('verbose', None)

        self.restUtil = Restutil(
            logoutUrl=self.url_factory.va_get_url('auth'),
            logoutMethod='delete')
        self.restUtil.verbose = self.verbose

    def _va_rest_get_auth_key(self):
        """
        generates authentication key object
        Returns: :(HTTPBasicAuth): HTTPBasicAuth object

        """
        response = self.restUtil.post_request(
            self.url_factory.va_get_url('auth'),
            auth=HTTPBasicAuth(self.username, self.password))
        auth_key = response['auth']
        return HTTPBasicAuth(self.username, auth_key)

    def _va_rest_del_auth_key(self, auth):
        """
        removes authentication key
        Args:
            :auth (HTTPBasicAuth): authentication key object

        """
        self.restUtil.delete_request(
            self.url_factory.va_get_url('auth'), auth=auth)

    def va_rest_get_hosts_inventory(self, params):
        """
        get all hosts information
        Args:
            :params (dict): {'datacenter': 'datacenter name'}
        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        host_inventory = self.restUtil.get_request(
            self.url_factory.va_get_url('inventoryHost'),
            params=params,
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return host_inventory

    def va_rest_get_inventory(self, params):
        """
        get inventory information
        Args:
            :params (dict): {'datacenter':'datacenter name'
                            'host':'host name'}

        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        inventory = self.restUtil.get_request(
            self.url_factory.va_get_url('inventory'),
            params=params,
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return inventory

    def va_rest_post_microsegmentation(self, data):
        """
        execute microsegmentation
        Args:
            :data (dict): {'datacenter':'datacenter name',
                          'vlan':'vlan',
                          'portgroup':'portgroup',
                          'host':'host uuid',
                          'epi':'epi uuid'}

        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        microsegmentation = self.restUtil.post_request(
            self.url_factory.va_get_url('microsegmentation'),
            data=data,
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return microsegmentation

    def va_rest_post_revert(self, data):
        """
        execute rollback
        Args:
            :data: {'datacenter':'datacenter name',
                   'vlan':'vlan',
                   'portgroup':'portgroup',
                   'host':'host uuid',
                   'epi':'epi uuid'}


        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        revert = self.restUtil.post_request(
            self.url_factory.va_get_url('revert'),
            data=data,
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return revert

    def va_rest_get_segmentation_stats(self):
        """
        get segmentation stats
        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.get_request(
            self.url_factory.va_get_url('segmentationStats'),
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return response

    def va_rest_get_chassis_epi(self):
        """
        get chassis epi information
        Returns (dict): rest response

        """
        """

        :return: response of epi rest request
        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.get_request(
            self.url_factory.va_get_url('chassisEpi'),
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return response

    def va_rest_get_segmentation_info(self, params):
        """
        get segmentation information
        Args:
            :params (dict): {'datacenter':'datacenter name',
                            'cluster':'cluster name',
                            'host': 'host uuid',
                            'portgroup':'portgroup',
                            'vlan':'vlan'}

        Returns (dict): response of segment info rest request

        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.get_request(
            self.url_factory.va_get_url('segmentationInfo'),
            params=params,
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return response

    def va_rest_get_orchestration(self):
        """
        get orchestration connection
        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.get_request(
            self.url_factory.va_get_url('checkOrchestration'),
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return response

    def va_rest_post_config_orchestration(self, path, data):
        """
        configure orchestration connection
        Args:
            :path (dict): {'name': 'server name'}
            :data (dict): {'address':'ip address',
                          'port':'port',
                          'passwd':'password',
                          'enable':'enable',
                          'type':'type',
                          'user':'user'}

        Returns (dict): rest response

        """

        auth = self._va_rest_get_auth_key()
        response = self.restUtil.post_request(
            self.url_factory.va_get_url('configOrchestration').as_string()
            + '/\"name:' + path['name'] + '\"',
            data=data,
            auth=auth)
        try:
            if response['status'] == 'ok':
                self.va_rest_post_commit(auth=auth)
                self._va_rest_del_auth_key(auth)
            else:
                raise ResponseFailed('va_rest_post_config_orchestration')
        except (KeyError, ResponseFailed) as e:
            self.va_rest_post_rollback(auth=auth)
            self._va_rest_del_auth_key(auth)
            raise e
        return response

    def va_rest_delete_config_orchestration(self, path):
        """
        delete orchestration connection
        Args:
            :path (dict): {'name': 'server name'}

        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.delete_request(
            self.url_factory.va_get_url('configOrchestration').as_string()
            + '/\"name:' + path['name'] + '\"',
            auth=auth)
        if response['status'] == 'ok':
            self.va_rest_post_commit(auth=auth)
            self._va_rest_del_auth_key(auth)
        else:
            self.va_rest_post_rollback(auth=auth)
            self._va_rest_del_auth_key(auth)

        return response

    def va_rest_post_commit(self, auth):
        """
        commit configuration
        Args:
           :auth (HTTPBasicAuth): authentication key object

        """
        self.restUtil.post_request(
            self.url_factory.va_get_url('commit'),
            auth=auth)

    def va_rest_post_rollback(self, auth):
        """
        rollback configuration
        Args:
           :auth (HTTPBasicAuth): authentication key object

        """
        self.restUtil.post_request(
            self.url_factory.va_get_url('rollback'),
            auth=auth)

    def va_rest_get_micro_segmentation(self):
        """
        get vlan information
        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.get_request(
            self.url_factory.va_get_url('micro_segmentation'),
            auth=auth)
        self._va_rest_del_auth_key(auth)
        return response

    def va_rest_delete_micro_segmentation(self, path):
        """
        delete micro-vlan
        Args:
            :path (dict): {'epiuuid':'epi uuid',
                           'segment':'segment',
                           'micro-vlan':'micro-vlan'}
        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.delete_request(
            self.url_factory.va_get_url('configMicro_segmentation').as_string()
            + '/epi/name:' + path['epiuuid'] + '/segment/name:' +
            path['segment'] + '/micro-vlan/name:' + path['micro-vlan']
            ,
            auth=auth
        )

        if response['status'] == 'ok':
            self.va_rest_post_commit(auth=auth)
        else:
            self.va_rest_post_rollback(auth=auth)
        self._va_rest_del_auth_key(auth)
        return response

    def va_rest_put_config_chassis_epi(self, path, data):
        """
        change epi mode
        Args:
            :path (dict): {'epiuuid':'epi uuid'}
            :data (dict): {'operation-mode': 'inline, tap, or standby'}

        Returns (dict): rest response

        """
        auth = self._va_rest_get_auth_key()
        response = self.restUtil.put_request(
            self.url_factory.va_get_url('configChassisEpi').as_string()
            + '/name:' + path['epiuuid'],
            data=data,
            auth=auth)
        if response['status'] == 'ok':
            self.va_rest_post_commit(auth=auth)
        else:
            self.va_rest_post_rollback(auth=auth)
        self._va_rest_del_auth_key(auth)
        return response
