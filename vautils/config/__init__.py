import os

from imp import find_module, load_module

from vautils.config.linux import supported as linux_supported
from feature.exceptions import *  # NOQA
from vautils import logger


class Config(object):

    @classmethod
    def get_linux_config_util(cls, resource=None):
        """
        function to dynamically load the feature class based on the product and
        the version the resource or product is running.

        Kwargs:
            :resource: supported vm factory resource type

        Returns:
            :instance of the util class for the resource

        Raises:
            :InvalidResource - resource is not of a valid type
            :UnsupportedVersion - version is not supported by the product
            :FeatureNotFound - util class cannot be located
        """
        if not resource:
            raise InvalidResource(resource)

        product = resource.get_nodetype()
        version = resource.get_version()
        abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                product)
        found = False
        version = version.lower()
        if version not in linux_supported:
            raise UnsupportedVersion(product, version)

        #path = os.path.join(abs_path, version)
        #print("Path: ", path)
        try:
            modloc = find_module(version, [abs_path])
        except ImportError:
            raise
        else:
            load_mod = load_module(version, modloc[0], modloc[1], modloc[2])
            try:
                util = getattr(load_mod, version.title())
            except AttributeError:
                raise
            else:
                found = True
                return util(resource)
