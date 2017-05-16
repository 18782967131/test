"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

Exceptions abstracts the various errors that Va_feature package can encounter
at run time.

.. moduleauthor:: ppenumarthy@varmour.com
"""


class VaFeatureException(Exception):
    """
    VaFeatureException is the base class for all run time errors encountered
    when a feature to configure a specific action on the product that is part
    of vArmour test infrastructure is being dynamically looked up and loaded.
    """
    pass


class InvalidResource(VaFeatureException):
    """
    InvalidResource is raised when a resource param is not paased in to
    get_feature.
    """

    def __init__(self, resource=None):
        msg = "valid resource needed to get feature. resource value passed" \
              " '{}'".format(resource)

        super(InvalidResource, self).__init__(msg)


class UnsupportedVersion(VaFeatureException):
    """
    UnsupportedVersion is raised when the version of software running on the
    product is not supported by VATF.
    """

    def __init__(self, product=None, version=None):
        msg = "version '{}' is not supported for product '{}'" \
            .format(version, product)

        super(UnsupportedVersion, self).__init__(msg)


class UnsupportedProduct(VaFeatureException):
    """
    UnsupportedProduct is raised when the product is not supported by VATF.
    """

    def __init__(self, product=None):
        msg = "product '{}' not supported".format(product)

        super(UnsupportedProduct, self).__init__(msg)


class FeatureNotFound(VaFeatureException):
    """
    UnsupportedProduct is raised when the product is not supported by VATF.
    """

    def __init__(self, feature=None):
        msg = "could not locate feature '{}'".format(feature)

        super(FeatureNotFound, self).__init__(msg)


class InvalidKey(VaFeatureException):
    """
    InvalidKey is raised when the key is not found in dictionary
    """

    def __init__(self, function):
        msg = "key can't be found when calling {} method".format(function)
        super(InvalidKey, self).__init__(msg)


class InvalidResponseFormat(VaFeatureException):
    """
    InvalidResponseFormat is raised when the va_feature gives
    the wrong response format
    """

    def __init__(self, function):
        msg = "response format is invalid when calling {} method".format(function)
        super(InvalidResponseFormat, self).__init__(msg)


class InvalidData(VaFeatureException):
    """
    InvalidData is raise when data is not in inventory
    """

    def __init__(self, function):
        msg = "data is invalid when calling {} method".format(function)
        super(InvalidData, self).__init__(msg)

class InvalidParameters(VaFeatureException):
    """
    InvalidData is raise when data is not in inventory
    """

    def __init__(self, function):
        msg = "parameters is invalid when calling {} method".format(function)
        super(InvalidParameters, self).__init__(msg)

class ResponseFailed(VaFeatureException):
    """
    ResponseFailed is raised when response shows failed keyword
    """

    def __init__(self, function):
        msg = "response failed when calling {} method".format(function)
        super(ResponseFailed, self).__init__(msg)