"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Delegator intercepts method calls that can be executed on a resource VM and
delegates it to the appropriate class. It supports access level, feature
level and resource level delegation.

.. moduleauthor:: ppenumarthy@varmour.com
"""

from access.cli.va_os import VaCli
from feature.common.accesslib import VaAccess
from vautils.config.linux.accesslib import Mode
from feature import Controller
from vautils.config import Config
from vautils import logger


class Delegator(object):
    """
    Delegator class caches the Access and Feature instances, intercepts the
    corresponding method call, and dynamically dispatches it to the correct
    feature, access, or resource class and invokes it. Feature for linux
    resource corresponds to Config utility. For access it checks if the
    access instance already exists, if not creates an instance
    """
    def __init__(self, resource=None):
        """
        Initializes the delegator object.

        Kwargs:
            resource (object): VarmourVm resource type
        """
        self._resource = resource
        self._method = None
        self._feature = None
        print('###################################')
        print('###################################')
        print('###################################')
        self.load_features()

    def __getattr__(self, method):
        """
        custom getattr to intercept the method call and dispatch the API to
        the correct class
        """
        def dispatcher(*args, **kwargs):
            self.method = method
            if method in ['va_cli', 'va_config', 'va_commit',
                          'va_shell', 'shell','va_reset_all']:
                return self._invoke_access_method(*args, **kwargs)
            else:
                if self._resource.get_nodetype() == 'linux':
                    return self._invoke_linux_config(*args, **kwargs)
                else:
                    return self._invoke_feature_method(*args, **kwargs)
        return dispatcher

    @property
    def method(self):
        """
        get method or the API name
        """
        return self._method

    @method.setter
    def method(self, name):
        """
        set the method or the API name
        """
        self._method = name

    def load_features(self):
        """
        method to set the feature objects of the respective features for
        the resource
        """
        resource = self._resource
        nodetype = resource.get_nodetype()

        if nodetype in ['dir', 'cp', 'epi', 'ep']:

            if not resource.get_access():
                access_class = VaAccess.get(resource)
                self._access = access_class(resource)
                resource.set_access(self._access)
            else:
                self._access = resource.get_access() 

            self._feature = Controller(resource)

        elif nodetype in ['linux']:
            self._access = Mode.get(resource)
            self._feature = Config.get_linux_config_util(resource)

    def get_property(self, property_name=None, property_id=None):
        """
        build the property callable for the resource and invoke it

        kwargs:
            :property_name (str): valid property name of the resource
            :property_id (str): valid id to identify the specific prop

        returns:
            :list of values for the property or a string value
        """
        method = '_'.join(('get', property_name))
        method_callable = getattr(self._resource, method)

        if property_id:
            return method_callable(property_id)
        else:
            return method_callable()

    def va_check_login(self, user=None, pswd=None):
        """
        method to verify login to the resource with user name and passowrd.
        if no exception is raised login attempt is successful.

        kwargs:
            :user (str): name of the user account
            :pswd (str): password of the user account
        """
        resource = self._resource
        login = False
        cmd = 'show system'

        try:
            instance = VaCli(
                host=resource.get_mgmt_ip(),
                user=user,
                password=pswd,
                prompt=resource.get_prompt_type(),
                uniq_id=resource.get_uniq_id()
            )
            with instance as cli:
                output, match, mode  = cli.va_exec_cli(cmd)
        except Exception as e:
            instance = None
            logger.info(e)
        else:
            login = True

        return login

    def reset_terminal_session(self):
        """
        """
        self._access._cli = self._resource.get_terminal_session() 

    def _invoke_access_method(self, *args, **kwargs):
        """
        invoke the access level API
        """
        method_callable = getattr(self._access, self.method)
        return method_callable(*args, **kwargs)

    def _invoke_linux_config(self, *args, **kwargs):
        """
        invoke the linux config level API
        """
        method_callable = getattr(self._feature, self.method)
        return method_callable(*args, **kwargs)

    def _invoke_feature_method(self, *args, **kwargs):
        """
        invoke the feature level API
        """
        return self._feature.__getattr__(self.method)(*args, **kwargs)

    def __del__(self):
        """
        custom delete to unlink the feature, access, and resource
        instances
        """
        self._resource = None
        self._access = None
        self._feature = None
