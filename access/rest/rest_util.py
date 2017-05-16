"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Restutil is a tool for calling rest requests via http methods

.. moduleauthor:: ckung@varmour.com
"""
import json
import pprint
import atexit
from access.rest.rest_session import *
from access import logger

SUPPORTED_VERB = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']


class Restutil():
    """
    Restutil class
    """

    def __init__(self, host=None, user=None, password=None, verbose=False, format_console=False, need_auth=True, resource=None):
        """
        constructor

        :param verbose: | True - print out all rest messages
                        | False - all rest messages will not be printed
        :type verbose: bool
        :param get_json_resp: | True - return of rest request only returns message body of type str
                              | False - the return of rest request returns of type requests.models.Response
        :type get_json_resp: bool
        :param format_json_log: | True - logger will pretty print json strings
                                | False - logger will not pretty print json strings
        :type format_json_log: bool
        """
        self.__host = host
        self.__user = user
        self.__password = password
        self.__verbose = verbose
        self.__format_console = format_console
        self.__need_auth = need_auth

        if resource:
            self.__host = resource.get_mgmt_ip()
            self.__user = resource.get_user().get('name')
            self.__password = resource.get_user().get('password')
            self.__verbose = resource.get_verbose()
            self.__format_console = resource.get_rest_format_console()
            self.__need_auth = resource.get_rest_need_auth()

        self.__session = RestSession(host=self.__host, user=self.__user, password=self.__password, need_auth=self.__need_auth, parent=self)
        atexit.register(self.__session.del_auth)

    @property
    def verbose(self):
        """
        verbose getter

        :return: True or False
        :type: bool
        """
        return self.__verbose

    @verbose.setter
    def verbose(self, verbose):
        """
        verbose setter

        :param verbose: | True - print out all rest messages
                        | False - all rest messages will not be printed
        :type verbose: bool
        """
        if type(verbose) is bool:
            self.__verbose = verbose

    @property
    def format_console(self):
        """
        format_json_log getter

        :return: True or False
        :type: bool
        """
        return self.__format_console

    @format_console.setter
    def format_console(self, format_console):
        """
        format_json_log setter

        :param format_json: | True - logger will pretty print json strings
                            | False - logger will not pretty print json strings
        :type format_json_log: bool
        """
        if type(format_console) is bool:
            self.__format_console = format_console

    def request(self, verb, url, **kwargs):
        """
        rest request

        :param verb: get, post, put, delete
        :type verb: str
        :param url: url
        :type url: str
        :param kwargs: | header (dict) - HTTP header
                       | auth (HTTPBasicAuth) - HTTPBasicAuth obj if any
                       | params (str) - URL parameters
                       | data (dict) - Rest body content
                       | transaction (boolean) - if URL contains config
        :return:
        """

        headers = kwargs.get('headers', DEFAULT_HEADER)
        dynamic_params = kwargs.get('dynamic_params', None)
        params = kwargs.get('params', None)
        auth = kwargs.get('auth', None)
        data = kwargs.get('data', None)
        verb = verb.upper()
        transaction = kwargs.get('transaction', False)

        if dynamic_params:
            for key, value in dynamic_params.items():
                temp_key = '{' + key + '}'
                if temp_key not in url:
                    raise URLRequired

            for key, value in dynamic_params.items():
                dynamic_url = ''
                for k, v in value.items():
                    dynamic_url += str(k) + ':' + str(v)
                temp_key = "{" + key + "}"
                dynamic_url = key + '/' + dynamic_url
                url = url.replace(temp_key, dynamic_url)

        if self.__verbose:
            logger.debug('----------begin {} request----------'.format(verb))
            logger.debug('url: {}'.format(url))
            logger.debug('params: {}'.format(params))
            logger.debug('data: {}'.format(data))
            logger.debug('......{} response result......'.format(verb))

        if data:
            data = json.dumps(data, ensure_ascii=False)

        try:
            if verb.upper() not in SUPPORTED_VERB:
                raise Exception('Http Request Verb')
            if not auth:
                auth = self.__session.get_auth()

            response_obj = requests.request(verb.upper(), url, params=params, data=data, headers=headers, auth=auth,
                                            verify=False)

            if self.__verbose:
                logger.debug('{} response status {}'.format(verb, response_obj.status_code))

            try:
                response_json = response_obj.json()
            except Exception as e:
                pass
            else:
                if response_json and 'status' in response_json.keys() and not ('ok' in response_json['status'] or '200' in response_json['status']):
                    raise RequestException
                else:
                    response_status = str(response_obj.status_code)
                    if response_status[0] != '2':
                        raise RequestException

            if transaction:
                self.__session.commit()
        except URLRequired:
            self.__show_error_log(verb, url, 'URL Error', response_obj)
            return self.__return_obj(False, response_obj, True)
        except HTTPError:
            self.__show_error_log(verb, url, 'HTTP', response_obj)
            return self.__return_obj(False, response_obj, True)
        except RequestException:
            self.__show_error_log(verb, url, 'Request Exception', response_obj)
            return self.__return_obj(False, response_obj, True)
        except Timeout:
            self.__show_error_log(verb, url, 'Timeout', response_obj)
            return self.__return_obj(False, response_obj, True)
        except ConnectionError:
            self.__show_error_log(verb, url, 'Connection', response_obj)
            return self.__return_obj(False, response_obj, True)
        except TooManyRedirects:
            self.__show_error_log(verb, url, 'Too Many Redirects', response_obj)
            return self.__return_obj(False, response_obj, True)
        except Exception as e:
            self.__show_error_log(verb, url, 'Exception', e)
            return self.__return_obj(False, response_obj, True)
        else:
            resp_msg = None
            try:
                resp_msg = response_obj.json()
            except Exception as e:
                pass
            if self.__verbose:
                if self.__format_console:
                    logger.debug('{} response message:\n{}'.format(verb, pprint.pformat(resp_msg)))
                else:
                    logger.debug('{} response message:\n{}'.format(verb, resp_msg))
                logger.debug('----------end {} request----------\n'.format(verb))
            return self.__return_obj(True, response_obj)

    def __show_error_log(self, verb, url, reason, response_message):
        """

        :param verb:
        :param url:
        :param reason:
        :param response_message:
        :return:
        """
        logger.error('error sending {} to url {}'.format(verb, url))
        logger.error('reason: {}'.format(reason))
        resp_msg = None
        try:
            resp_msg = response_message.json()
        except Exception as e:
            pass

        if self.__format_console and type(response_message) is requests.models.Response:
            logger.error('message:\n{}'.format(pprint.pformat(resp_msg)))
        elif not self.__format_console and type(response_message) is requests.models.Response:
            logger.error('message:\n{}'.format(resp_msg))
        else:
            logger.error('message:\n{}'.format(response_message))
        logger.debug('----------end {} request----------\n'.format(verb))

    def __return_obj(self, status_bool, response_obj, transaction_fail=False):
        """

        :param status_bool:
        :param response_obj:
        :return:
        """
        if transaction_fail:
            self.__session.rollback()

        response = {'status': None, 'body': None}
        try:
            response_body = response_obj.json()
        except Exception as e:
            response['status'] = str(response_obj.status_code)
        else:

            if not 'status' in response_body.keys():
                if not response['status']:
                    response['status'] = str(response_obj.status_code)
            else:
                response['status'] = str(response_body['status'])
            response['body'] = response_body

        return status_bool, response



