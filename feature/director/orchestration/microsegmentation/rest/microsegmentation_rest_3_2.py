"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaMicrosegmentation_3_1 provides va orchestration microsegmentation features

.. moduleauthor:: ckung@varmour.com
"""
import time
import datetime
from access import logger
from feature.director.orchestration.microsegmentation.rest.microsegmentation_rest_3_1 import VaMicrosegmentation


class VaMicrosegmentation(VaMicrosegmentation):
    def va_microsegment(self, **kwargs):
        """
        trigger microsegmentation

        :param kwargs: | network (str) - vss or vds
                       |
                       | if network is vss:
                       | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'vlanID': '',
                       |     'segment': '',
                       |     'hostUUID': '',
                       |     'epiUUID': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | vlanID (str) - vlan id
                       | segment (str) - segment
                       | hostUUID (str) - host uuid
                       | epiUUID (str) - epi uuid
                       | 
                       | if network is vds:
                       | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'domain': '',
                       |     'vlan_range': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | domain (str) - datacenter name
                       | vlan_range (str) - vlan range
                       
        :return: error message
        :type: str
        """
        method_name = 'va_microsegment'
        self._va_message_helper(method_name, 'start')
        postData = {}
        network = kwargs.get('network', 'vss')
        segmentData = kwargs.get('segmentData', None)
        if network == 'vss':
            if not segmentData:
                postData['instance'] = kwargs.get('instance', None)
                postData['vlan'] = kwargs.get('vlanID', None)
                postData['endpoint_group'] = kwargs.get('segment', None)
                postData['host'] = kwargs.get('hostUUID', None)
                postData['epi'] = kwargs.get('epiUUID', None)
            else:
                postData['instance'] = segmentData['instance']
                postData['vlan'] = segmentData['vlanID']
                postData['endpoint_group'] = segmentData['segment']
                postData['host'] = segmentData['hostUUID']
                postData['epi'] = segmentData['epiUUID']
        else:
            if not segmentData:
                postData['instance'] = kwargs.get('instance', None)
                postData['domain'] = kwargs.get('domain', None)
                postData['vlan_range'] = kwargs.get('vlan_range', None)
            else:
                postData['instance'] = segmentData['instance']
                postData['domain'] = segmentData['domain']
                postData['vlan_range'] = segmentData['vlan_range']


        check_input = self._va_check_input_data(method_name, postData)

        if check_input:
            return check_input

        response = self.va_rest_post_microsegmentation(postData)

        if self._check_failed_message(response, method_name):
            return response
        logger.info('... sleep for 30 secs ...')
        time.sleep(30)
        self._va_message_helper(method_name, 'end')


    def va_rollback(self, **kwargs):
        """
        roll back from microsegmentation

        :param kwargs: | network (str) - vss or vds
                       |
                       | if network is vss:
                       | segmentData (dict) -
                       | {
                       |     'instance': '',
                       |     'vlanID': '',
                       |     'segment': '',
                       |     'hostUUID': '',
                       |     'epiUUID': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | vlanID (str) - vlan id
                       | segment (str) - segment
                       | hostUUID (str) - host uuid
                       | epiUUID (str) - epi uuid
                       | 
                       | if network is vds:
                       | {
                       |     'instance': '',
                       |     'domain': '',
                       |     'endpoint_switch': '',
                       |     'endpoint_group': '',
                       |     'vlan': '',
                       | }
                       |
                       | or
                       |
                       | instance (str) - vcenter instance
                       | domain (str) - domain
                       | endpoint_switch (str) - endpoint switch name
                       | endpoint_group (str) - endpoint group name
                       | vlan (str) - vlan id
   
        :return: error message
        :type: str
        """
        method_name = 'va_rollback'
        self._va_message_helper(method_name, 'start')
        postData = {}
        network = kwargs.get('network', 'vss')
        segmentData = kwargs.get('segmentData', None)
        if network == 'vss':
            if not segmentData:
                postData['instance'] = kwargs.get('instance', None)
                postData['vlan'] = kwargs.get('vlanID', None)
                postData['endpoint_group'] = kwargs.get('segment', None)
                postData['host'] = kwargs.get('hostUUID', None)
                postData['epi'] = kwargs.get('epiUUID', None)
            else:
                postData['instance'] = segmentData['instance']
                postData['vlan'] = segmentData['vlanID']
                postData['endpoint_group'] = segmentData['segment']
                postData['host'] = segmentData['hostUUID']
                postData['epi'] = segmentData['epiUUID']
        else:
            if not segmentData:
                postData['instance'] = kwargs.get('instance', None)
                postData['domain'] = kwargs.get('domain', None)
                postData['endpoint_switch'] = kwargs.get('endpoint_switch', None)
                postData['endpoint_group'] = kwargs.get('endpoint_group', None)
                postData['vlan'] = kwargs.get('vlan', None)
            else:
                postData['instance'] = segmentData['instance']
                postData['domain'] = segmentData['domain']
                postData['endpoint_switch'] = segmentData['endpoint_switch']
                postData['endpoint_group'] = segmentData['endpoint_group']
                postData['vlan'] = segmentData['vlan']


        check_input = self._va_check_input_data(method_name, postData)
        if check_input:
            return check_input

        response = self.va_rest_post_revert(postData)

        if self._check_failed_message(response, method_name):
            return response

        logger.info('... sleep for 15 secs ...')
        time.sleep(15)

        self._va_message_helper(method_name, 'end')
