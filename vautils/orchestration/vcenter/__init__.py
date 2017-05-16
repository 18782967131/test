import os,glob

from imp import find_module, load_module

from vautils import logger
from vautils.orchestration.vcenter.vcenter_connector import VcenterConnector
from feature.exceptions import *

supported_mod = ['host','operation','network','vm','connector']
class VcenterConfig(object):

    @classmethod
    def get_vcenter_config_util(cls_name, resource=None):
        """
        function to dynamically load the all vcenter class
        Kwargs:
            :resource: supported vm factory resource type

        Returns:
            :instance of the self class for the resource

        """
        if not resource:
            raise InvalidResource(resource)

        product = resource.get_nodetype()
        abs_path = os.path.dirname(os.path.abspath(__file__))

        for smod in supported_mod:
            if smod == 'connector' :
                filenames = ['vcenter_connector.py']
                abs_path1 = abs_path
            else :
                abs_path1 = os.path.join(abs_path,smod)
                filename='{}_{}'.format(product,smod)
                filenames = glob.glob(os.path.join(abs_path1,'*.py'))

            for file_name in filenames :
                file_name = os.path.basename(file_name)

                if file_name == '__init__.py' or file_name == 'vm_verification.py' \
                        or file_name == 'vcenter_verification.py' or file_name == 'vnet_action.py' :
                    continue

                if len(filenames) == 2 :
                    filename = '{}_{}'.format(product, smod)
                else :
                    filename = file_name.split('.')[0]

                try:
                    modloc = find_module(filename, [abs_path1])
                except ImportError:
                    raise
                else:
                    load_mod = load_module(filename, modloc[0], modloc[1], modloc[2])
                    vcs = filename.split('_')
                    modulename = vcs[0].capitalize() + vcs[1].capitalize()
                    if modulename == 'VcenterVm' :
                        modulename = 'VcenterVMs'
                    try:
                        util = getattr(load_mod, modulename)
                        setattr(cls_name,modulename,util(resource))
                    except AttributeError:
                        raise
        return cls_name