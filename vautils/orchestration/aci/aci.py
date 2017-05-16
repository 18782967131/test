"""
coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

vCenterVMs class is representing vim.VirtualMachine objects  and its methods.
class methods either return string or managed objects.

.. moduleauthor::ckung@varmour.com

"""
from vautils.orchestration.aci import aci_rest
from purl import URL
import sys

class Aci():
    def __init__(self, aci_object=None, **kwargs):
        self.user = kwargs.get('user', None)
        self.password = kwargs.get('password', None)
        self.ip = str(URL(scheme='https', host=kwargs.get('ip', None)))
        if aci_object:
            pass

        self.apic_session = aci_rest.Session(self.ip, self.user, self.password)

        resp = self.apic_session.login()
        if not resp.ok:
            sys.exit(0)

        self.cmd = aci_rest.Commands(self.apic_session)

    def test(self):
        # print(dir(self.cmd))
        tenants = self.cmd.get_tenants()
        import pdb;
        pdb.set_trace()
        # import pdb;pdb.set_trace()
        # epgs = self.cmd.get_epgs()
        # for epg in epgs:
        #     self.cmd.get_object_tags(epg)
        # epg_list = self._get_cmd().get_epgs
        # import pdb;pdb.set_trace()
        # self._get_cmd().get_object(epg_list[0])
        # print(dir(self._get_cmd()))

    def create_app_epg(self, tenant, app_profile=None, name=None, tags=None, bridge_domain=None, vm_domain=None):
        """

        need:
        tenant, app
        name, tags, bridge_domain, vm_domain
        """
        import pdb;pdb.set_trace()
        tenants = self.cmd.get_tenants()
        dn = None
        for tenant in tenants:
            if tenant['name'] == tenant:
                dn = tenant['dn']
                break
        epgs = self.cmd.get_epgs(tenant)


        pass