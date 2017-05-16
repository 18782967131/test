"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Client asbtracts the client side functionality of a rest session

.. moduleauthor:: ckung@varmour.com
"""
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.exceptions import *
import requests
import weakref
from requests.auth import HTTPBasicAuth
from purl import URL

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DEFAULT_HEADER = {'content-type': 'application/json'}


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class RestSessionContainer(metaclass=Singleton):
    def __init__(self):
        self._session = {}

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        self._session = session


class RestSession():

    def __init__(self, host, user, password, need_auth, parent):
        self.parent = weakref.ref(parent)
        self._host = host
        self._user = user
        self._password = password
        self._need_auth = need_auth
        self._rest_session_container = RestSessionContainer()
        self._url = URL(scheme='https', host=host)
        self._auth_url = self._url.path('/api/v1.0/auth')
        self._commit_url = self._url.path('/api/v1.0/commit')
        self._rollback_url = self._url.path('/api/v1.0/rollback')
        self._check_auth_url = self._url.path('/api/v1.0/operation/chassis/epi')
        if self._need_auth:
            self._login()

    def _check_auth(self):
        if self._host not in self._rest_session_container.session.keys():
            return False
        response_obj = requests.request('GET', self._check_auth_url, headers=DEFAULT_HEADER, auth=self._rest_session_container.session[self._host], verify=False)
        response_json = response_obj.json()
        if 'response' in response_json.keys() and isinstance(response_json['response'], str) and 'Authentication failed' in response_json['response']:
            return False
        return True

    def _login(self):
        if not self._check_auth():
            auth = HTTPBasicAuth(self._user, self._password)
            response_obj = requests.request('POST', self._auth_url, headers=DEFAULT_HEADER, auth=auth, verify=False)
            response_json = response_obj.json()

            if 'auth' in response_json.keys() and 'status' in response_json['auth']:
                raise RequestException

            auth_key = response_json['auth']
            self._rest_session_container.session[self._host] = HTTPBasicAuth(self._user, auth_key)

    def get_auth(self):
        if not self._need_auth:
            return HTTPBasicAuth(self._user, self._password)
        if not self._check_auth():
            self._login()
        return self._rest_session_container.session[self._host]

    def del_auth(self):
        if self._need_auth and self._check_auth():
            response_obj = requests.request('DELETE', self._auth_url, headers=DEFAULT_HEADER, auth=self._rest_session_container.session[self._host], verify=False)
        # response_json = response_obj.json()
        # if 'auth' in response_json.keys() and 'status' in response_json['auth']:
        #     raise RequestException

    def commit(self):
        if not self._check_auth():
            raise RequestException
        response_obj = requests.request('POST', self._commit_url, headers=DEFAULT_HEADER, auth=self._rest_session_container.session[self._host], verify=False)
        response_json = response_obj.json()
        if 'status' in response_json.keys() and not (
                'ok' in response_json['status'] or '200' in response_json['status']):
            raise RequestException

    def rollback(self):
        if not self._check_auth():
            raise RequestException
        requests.request('POST', self._rollback_url, headers=DEFAULT_HEADER, auth=self._rest_session_container.session[self._host], verify=False)

