"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

va_get_feature implements the function that looks up the feature framework for
the valid feature requested based on the product.

Controller consolidates the features that can be executed on one resource,
instead of calling va_get_feature multiple times for different features.

.. moduleauthor:: ppenumarthy@varmour.com
"""

import os
import configparser

from vautils.log import va_fwk_log
try:
    logger = va_fwk_log(__name__, True, log_file)
except:
    logger = va_fwk_log(__name__)
from feature.common import supported, version_map
from feature.exceptions import *  # NOQA
from imp import find_module, load_module


def va_get_feature(resource=None, feature=None, rest=False, product=None):
    """
    Function to dynamically load the feature class based on the product and
    the version the resource or product is running.

    Kwargs:
        :resource: supported Va_lab vm resource type
        :feature (str): supported feature that can be configured on a resource

    Returns:
        :instance of the feature class for the resource

    Raises:
        :InvalidResource - if the resource is not set for a valid type
        :UnsupportedVersion - when a version is not supported by the product
        :UnsupportedProduct - when a product is not supported by VATF
        :FeatureNotFound - when a feature class cannot be located
    """
    if not resource:
        raise InvalidResource(resource)

    if not product:
        product = resource.get_nodetype()

    sub_product = None
    version = resource.get_version()
    abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    found = False
    version_supported = False

    for info in supported:
        if info in version:
            version_supported = True

    if not version_supported:
        raise UnsupportedVersion(product, version)

    version = version[0:3]

    if product == 'dir':
        sub_product = 'director'
        path = os.path.join(abs_path, sub_product)
    elif product in ['ep', 'epi', 'cp', 'common']:
        path = os.path.join(abs_path, 'common')
    else:
        raise UnsupportedProduct(product)

    for ver in supported[supported.index(version):]:
        software_version = version_map.get(ver)
        feature_source = '_'.join((feature, software_version))

        if rest:
            feature_source = '_'.join((feature, 'rest', software_version))

        for module in os.walk(path):
            try:
                modloc = find_module(feature_source, [module[0]])
            except ImportError:
                continue
            else:
                load_mod = load_module(
                               feature_source, modloc[0], modloc[1], modloc[2]
                           )

                try:
                    feature_class = getattr(load_mod, 'Va' + feature.title())
                except AttributeError:
                    pass
                else:
                    found = True
                    return feature_class(resource)

    if not found:
        raise FeatureNotFound(feature)


class Controller(object):
    """
    Controller class caches the feature instances and intercepts the feature
    method call and dynamically dispatches it to the correct feature and
    invokes it.
    """
    def __init__(self, resource=None, features=None):
        """
        Initializes the controller object.

        Kwargs:
            resource (object): VarmourVm resource type
            features (list): features to be cached. Default is all features
                             specified in features.ini
        """
        abs_path = os.path.dirname(os.path.abspath(__file__))
        config = configparser.ConfigParser()
        config.read(os.path.join(abs_path, 'features.ini'))

        if resource.get_nodetype() == 'dir':
            product = 'director'
        else:
            product = 'common'

        self._feature_list = features
        if not features:
            features = list(config[product].keys())
            self._feature_list = features
        for feature in features:
            attr = ''.join(('_', feature))
            if '-' in feature:
                feat, comp = feature.split('-')
                inst = va_get_feature(resource, feat, product=comp)
                setattr(self, attr, inst)
            else:
                inst = va_get_feature(resource, feature)
                setattr(self, attr, inst)

    def __getattr__(self, method):
        """
        custom getattr to intercept the method call
        """
        def dispatcher(*args, **kwargs):
            found = False
            for feature in self._feature_list:
                attr = getattr(self, ''.join(('_', feature)))
                name_space = dir(attr)
                if method in name_space:
                    call = getattr(attr, method)
                    return call(*args, **kwargs)
                else:
                    if '_parent' in name_space:
                        if method in dir(attr._parent):
                            call = getattr(attr._parent, method)
                            return call(*args, **kwargs)

            if not found:
                raise AttributeError(method)

        return dispatcher

    def __del__(self):
        """
        custom delete to unlink the feature instances
        """
        for feature in self._feature_list:
            attr = ''.join(('_', feature))
            setattr(self, attr, None)
