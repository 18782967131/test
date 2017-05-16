"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaRestapi contains all va rest features

.. moduleauthor:: ckung@varmour.com
"""

from requests.auth import HTTPBasicAuth
from access import logger
from access.rest import Restutil
from feature.director.orchestration.microsegmentation.rel_3_1.rest_url_factory_rel_3_1 import VaResturlfactory


class VaRestapi:
    """
    VaRestapi has all va rest request
    All methods in this class involves rest call
    """

    def __init__(self, **kwargs):
        """
        constructor

        :param kwargs: | inv_object (inventory_object) - inventory object
                       | or
                       | ip (str) - director ip
                       | username (str) - director username
                       | password (str) - director password
                       | verbose (boolean) - enable/disable logger
                       | get_json_resp (boolean) - get json response
                       | format_json_log (boolean) - pretty print json format
        """
        dir_object = kwargs.get('inv_object', None)
        if dir_object:
            self.__username = dir_object.get_user().get('name')
            self.__password = dir_object.get_user().get('password')
            self.__url_factory = VaResturlfactory(dir_object.get_mgmt_ip())
            self.__rest_util = Restutil(verbose=dir_object.get_verbose(), get_json_resp=True, format_json_log=False)
        else:
            self.__username = kwargs.get('username', None)
            self.__password = kwargs.get('password', None)
            self.__url_factory = VaResturlfactory(kwargs.get('ip', None))
            self.__rest_util = Restutil(verbose=kwargs.get('verbose', False),
                                        get_json_resp=kwargs.get('getJsonObj', True),
                                        format_json_log=kwargs.get('formatJsonLog', False))

    @property
    def verbose(self):
        """
        verbose getter

        :return: True or False
        :type: bool
        """
        return self.__rest_util.verbose

    @verbose.setter
    def verbose(self, verbose):
        """
        verbose setter

        :param verbose: | if set True, print out all rest messages
                        | if set False, all rest messages will not be printed
        :type verbose: bool
        """
        if type(verbose) is bool:
            self.__rest_util.verbose = verbose

    @property
    def get_json_resp(self):
        """
        get_json_resp getter

        :return: True or False
        :type: bool
        """
        return self.__rest_util.get_json_resp

    @get_json_resp.setter
    def get_json_resp(self, get_json_resp):
        """
        get_json_resp setter

        :param get_json_resp: | if set True, return of rest request only returns message body of type str
                              | if set False, the return of rest request returns of type requests.models.Response
        :type get_json_resp: bool
        """
        if type(get_json_resp) is bool:
            self.__rest_util.get_json_resp = get_json_resp

    @property
    def format_json_log(self):
        """
        format_json_log getter

        :return: True or False
        :type: bool
        """
        return self.__rest_util.__format_json_log

    @format_json_log.setter
    def format_json_log(self, format_json_log):
        """
        format_json_log setter

        :param format_json: | if set True, logger will pretty print json strings
                            | if set False, logger will not pretty print json strings
        :type format_json_log: bool
        """
        if type(format_json_log) is bool:
            self.__rest_util.format_json_log = format_json_log

    def _va_rest_get_auth_key(self):
        """
        generates authentication key object

        :return: auth key object
        :type: HTTPBasicAuth
        """
        auth = HTTPBasicAuth(self.__username, self.__password)
        curr_verbose = self.verbose
        if curr_verbose:
            self.verbose = False
        status, response = self.__rest_util.request('post', self.__url_factory.va_get_url('auth'), auth=auth)
        if curr_verbose:
            self.verbose = curr_verbose
        if not status:
            error_message = 'getting auth key failed'
            return error_message

        auth_key = response['auth']

        return HTTPBasicAuth(self.__username, auth_key)

    def _va_rest_del_auth_key(self, auth):
        """
        removes authentication key object

        :param auth: auth object
        :type auth: HTTPBasicAuth
        :return: error message
        :type: str
        """
        curr_verbose = self.verbose
        if curr_verbose:
            self.verbose = False
        status, response = self.__rest_util.request('delete', self.__url_factory.va_get_url('auth'), auth=auth)
        if curr_verbose:
            self.verbose = curr_verbose
        if not status:
            error_message = 'delete auth key failed'
            return error_message

    def _va_error_message(self, method_name, reasons, show=False):
        """
        display error message

        :param method_name: method name
        :type method_name: str
        :param reasons: error message
        :type reasons: dict
        :return: error message
        :type: str
        """
        error_message = None
        if reasons and type(reasons) is str:
            error_message = 'method {} failed\nreasons {}'.format(method_name, reasons)
        elif reasons and 'response' in reasons.keys():
            error_message = 'method {} failed\nreasons {}'.format(method_name, reasons['response'])
        else:
            error_message = 'method {} failed'.format(method_name)
        if show:
            logger.error(error_message)
        return error_message

    def _va_rest_helper(self, method_name, verb, url, params, data, return_key, transaction=False):
        """
        rest helper method

        :param method_name: method name
        :type method_name: str
        :param verb: HTTP verb
        :type verb: str
        :param url: HTTP Url
        :type url: str
        :param params: HTTP Url pararmeters
        :type params: dict
        :param data: HTTP Request Body Message
        :type data: dict
        :return: HTTP response
        :type: str
        """
        auth = self._va_rest_get_auth_key()

        if type(auth) is str:
            return self._va_error_message(method_name, auth)

        status, response = self.__rest_util.request(verb, url, auth=auth, params=params, data=data)

        if transaction:
            if not status:
                self.va_rest_post_rollback(auth)
                self._va_rest_del_auth_key(auth)
                return self._va_error_message(method_name, response)

            self.va_rest_post_commit(auth)

        self._va_rest_del_auth_key(auth)

        if not status:
            return self._va_error_message(method_name, response)

        if return_key:
            if return_key in response.keys():
                return response[return_key]
            return self._va_error_message(method_name, 'key: {} does not exists in rest response'.format(return_key),
                                          True)

    def va_rest_post_commit(self, auth):
        """
        commit configuration

        :param auth: auth object
        :type auth: HTTPBasicAuth
        :return: error message
        :type: str
        """
        curr_verbose = self.verbose
        if curr_verbose:
            self.verbose = False
        status, response = self.__rest_util.request('post', self.__url_factory.va_get_url('commit'), auth=auth)
        if curr_verbose:
            self.verbose = curr_verbose
        if not status:
            error_message = 'commit failed'
            return error_message

    def va_rest_post_rollback(self, auth):
        """
        rollback configuration

        :param auth: auth object
        :type auth: HTTPBasicAuth
        :return: error message
        :type: str
        """
        curr_verbose = self.verbose
        if curr_verbose:
            self.verbose = False
        status, response = self.__rest_util.request('post', self.__url_factory.va_get_url('rollback'), auth=auth)
        if curr_verbose:
            self.verbose = curr_verbose
        if not status:
            error_message = 'rollback failed'
            return error_message

    def va_rest_get_hosts_inventory(self, params):
        """
        get all hosts information

        :param params: | {
                       |     'domain': 'datacenter name',
                       |     'instance' : 'instance name'
                       | }
        :type params: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_hosts_inventory'
        url = self.__url_factory.va_get_url('inventoryHost')
        return self._va_rest_helper(method_name, 'get', url, params, None, 'response')

    def va_rest_get_inventory(self, params):
        """
        get inventory information

        :param params: | {
                       |      'domain':'datacenter name'
                       |      'instance':'instance name'
                       | }
        :type params: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_inventory'
        url = self.__url_factory.va_get_url('inventory')
        return self._va_rest_helper(method_name, 'get', url, params, None, 'response')

    def va_rest_post_microsegmentation(self, data):
        """
        microsegmentation

        :param data: | {
                     |     'datacenter':'datacenter name',
                     |     'vlan':'vlan',
                     |     'portgroup':'portgroup',
                     |     'host':'host uuid',
                     |     'epi':'epi uuid'
                     | }
        :type data: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_post_microsegmentation'
        url = self.__url_factory.va_get_url('microsegmentation')
        return self._va_rest_helper(method_name, 'post', url, None, data, 'response')

    def va_rest_post_auto_microsegmentation(self, data):
        """
        enable auto microsegmentation

        :param data: | {
                     |     'instance': 'vcenter_1',
                     |     'scope': {
                     |              'domain': 'domain_A',
                     |              'zone': 'zone_K'
                     |              },
                     |     'filter_desc': [{
                     |                     'filter': {
                     |                               'type': 'endpoint_group',
                     |                               'value': {
                     |                                        'name': 'endpoint_group_W',
                     |                                        'vlan': 'vlan_101'
                     |                                        }
                     |                               },
                     |                               'associated_data': {}
                     |                      }, {
                     |                     'filter': {
                     |                               'type': 'endpoint_group',
                     |                               'value': {
                     |                                        'name': 'endpoint_group_X',
                     |                                        'vlan': 'vlan_201'
                     |                                        }
                     |                               },
                     |                               'associated_data': {}
                     |                          }]
                     | }
        :type data: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_post_auto_microsegmentation'
        url = self.__url_factory.va_get_url('enable_auto_microsegment')
        return self._va_rest_helper(method_name, 'post', url, None, data, None)

    def va_rest_post_disable_auto_microsegmentation(self, data):
        """
        disable auto microsegmentation

        :param data: | {
                     |     'instance': 'vcenter_1',
                     |     'scope': {
                     |              'domain': 'domain_A',
                     |              'zone': 'zone_K'
                     |              },
                     |     'filter_desc': [{
                     |                     'filter': {
                     |                               'type': 'endpoint_group',
                     |                               'value': {
                     |                                        'name': 'endpoint_group_W',
                     |                                        'vlan': 'vlan_101'
                     |                                        }
                     |                               },
                     |                               'associated_data': {}
                     |                      }, {
                     |                     'filter': {
                     |                               'type': 'endpoint_group',
                     |                               'value': {
                     |                                        'name': 'endpoint_group_X',
                     |                                        'vlan': 'vlan_201'
                     |                                        }
                     |                               },
                     |                               'associated_data': {}
                     |                          }]
                     | }
        :type data: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_delete_auto_microsegmentation'
        url = self.__url_factory.va_get_url('disable_auto_microsegment')
        return self._va_rest_helper(method_name, 'post', url, None, data, None)

    def va_rest_get_auto_microsegmentation(self, params):
        """
        get auto microsegmentation

        :param params:
        :type params: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_auto_microsegmentation'
        url = self.__url_factory.va_get_url('enable_auto_microsegment')
        return self._va_rest_helper(method_name, 'get', url, params, None, 'response')

    def va_rest_post_revert(self, data):
        """
        rollback from microsegmentation

        :param data: | {
                     |     'datacenter':'datacenter name',
                     |     'vlan':'vlan',
                     |     'portgroup':'portgroup',
                     |     'host':'host uuid',
                     |     'epi':'epi uuid'
                     | }
        :type data: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_post_revert'
        url = self.__url_factory.va_get_url('revert')
        return self._va_rest_helper(method_name, 'post', url, None, data, 'response')

    def va_rest_get_segmentation_stats(self):
        """
        get segmentation stats

        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_segmentation_stats'
        url = self.__url_factory.va_get_url('segmentationStats')
        return self._va_rest_helper(method_name, 'get', url, None, None, 'response')

    def va_rest_get_chassis_epi(self):
        """
        get chassis epi information

        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_chassis_epi'
        url = self.__url_factory.va_get_url('chassisEpi')
        return self._va_rest_helper(method_name, 'get', url, None, None, 'response')

    def va_rest_get_segmentation_info(self, params):
        """
        get segmentation information

        :param params: | {
                       |     'datacenter':'datacenter name',
                       |     'cluster':'cluster name',
                       |     'host': 'host uuid',
                       |     'portgroup':'portgroup',
                       |     'vlan':'vlan'
                       | }
        :type params: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_segmentation_info'
        url = self.__url_factory.va_get_url('segmentationInfo')
        return self._va_rest_helper(method_name, 'get', url, params, None, 'response')

    def va_rest_get_orchestration(self):
        """
        get orchestration status information

        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_orchestration'
        url = self.__url_factory.va_get_url('checkOrchestration')
        return self._va_rest_helper(method_name, 'get', url, None, None, 'response')

    # TODO working at this point
    def va_rest_post_config_orchestration(self, path, data):
        """
        configure orchestration connection

        :param path: | {
                     |     'name': 'server name'
                     | }
        :type path: dict
        :param data: | {
                     |     'address':'ip address',
                     |     'port':'port',
                     |     'passwd':'password',
                     |     'enable':'enable',
                     |     'type':'type',
                     |     'user':'user'
                     | }
        :type data: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_post_config_orchestration'
        url = self.__url_factory.va_get_url('configOrchestration').as_string() + '/\"name:' + path['name'] + '\"'
        return self._va_rest_helper(method_name, 'post', url, None, data, None, True)

    def va_rest_delete_config_orchestration(self, path):
        """
        delete orchestration connection

        :param path: | {
                     |     'name': 'server name'
                     | }
        :type path: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_delete_config_orchestration'
        url = self.__url_factory.va_get_url('configOrchestration').as_string() + '/\"name:' + path['name'] + '\"'
        return self._va_rest_helper(method_name, 'delete', url, None, None, None, True)

    def va_rest_get_micro_segmentation(self):
        """
        get vlan information

        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_get_micro_segmentation'
        url = self.__url_factory.va_get_url('micro_segmentation')
        return self._va_rest_helper(method_name, 'get', url, None, None, 'response')

    def va_rest_delete_micro_segmentation(self, path):
        """
        delete micro-vlan

        :param path: | {
                     |     'epiuuid':'epi uuid',
                     |     'segment':'segment',
                     |     'micro-vlan':'micro-vlan'
                     | }
        :type path: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_delete_micro_segmentation'
        url = self.__url_factory.va_get_url('configMicro_segmentation').as_string() + '/epi/name:' + path[
            'epiuuid'] + '/segment/name:' + path['segment'] + '/micro-vlan/name:' + path['micro-vlan']
        return self._va_rest_helper(method_name, 'delete', url, None, None, 'response')

    def va_rest_put_config_chassis_epi(self, data):
        """
        change epi mode

        :param data: | {
                     |     'operation-mode': 'inline, tap, or standby'
                     | }
        :type data: dict
        :return: rest response or error message
        :type: dict or str
        """
        method_name = 'va_rest_put_config_chassis_epi'
        url = self.__url_factory.va_get_url('configChassisEpi')
        return self._va_rest_helper(method_name, 'put', url, None, data, None, True)

    def va_get_inventory_updatestatus(self, params):
        """

        :param params:
        :return:
        """
        method_name = 'va_get_inventory_updatestatus'
        url = self.__url_factory.va_get_url('inventoryUpdatestatus')
        return self._va_rest_helper(method_name, 'get', url, params, None, 'response')

    def va_post_inventory_deployment(self, params, data):
        """

        :param params:
        :param data:
        :return:
        """
        method_name = 'va_post_inventory_deployment'
        url = self.__url_factory.va_get_url('operationDeployment')
        return self._va_rest_helper(method_name, 'post', url, params, data, 'response')

    def va_post_inventory_remove_deployment(self, params, data):
        """

        :param params:
        :param data:
        :return:
        """
        method_name = 'va_post_inventory_remove_deployment'
        url = self.__url_factory.va_get_url('operationRemoveDeployment')
        return self._va_rest_helper(method_name, 'post', url, params, data, 'response')

    def va_get_inventory_deployment(self, params):
        """

        :param params:
        :return:
        """
        method_name = 'va_get_inventory_deployment'
        url = self.__url_factory.va_get_url('operationDeploymentInfo')
        return self._va_rest_helper(method_name, 'get', url, params, None, 'response')
