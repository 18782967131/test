"""coding: utf-8

Copyright 2017 vArmour Networks private.
All Rights reserved. Confidential

inheritance epi_3_1 feature
.. moduleauthor:: xliu@sigma-rt.com
"""
import sys,re, time
from collections import namedtuple
from feature import logger
from vautils.dataparser.string import va_parse_basic, va_parse_as_lines
from vautils.resource.delegator import Delegator
from feature.director.epi.epi_3_1 import VaEpi as VaEpi_3_1

class VaEpi(VaEpi_3_1):
    """
    Epi implements methods for 4.0 build
    """
    def _va_parse_chassis_epi(self, output=None):
        """
        helper method to parse 'show chassis epi uuid' or
        'show chassis epi hostname'

        returns (dict): look at the following output
        {
            "Active EPI":[
               Epi(uuid='420135BF-0069-120D-816E-29A058C829ED',
                   hostname='VA-31-EPi1',ep_id='2-6',mode='tap','fabric_ip'='100.0.92.84/24',
                   management_ip='10.150.92.84/16',connected_since='@Thu-Jul=28-09:13:56-2016',
                   connected_type=TLS'',licensed='yes'),
               Epi(uuid='420135BF-0069-120D-816E-29A058C829ED',
                   hostname='VA-31-EPi1',ep_id='2-7*',mode='tap','fabric_ip'='100.0.92.84/24',
                   management_ip='10.150.92.84/16',connected_since='@Thu-Jul=28-09:13:56-2016',
                   connected_type=TLS'',licensed='yes') 
            ],
            "Inactive EPI":[Epi(uuid='564DDF39-5C53-66E4-4F64-6CB7B2B8BC9B',hostname='-',last_connected_ep='3',mode='tap')]
            "Total inactive EPIs":"1",
            "Total active EPIs":" 1"
        }
        """
        print("==========================")
        print("4.04.0")
        parsed = dict()
        current_key = None
        active_tag = 0
        inactive_tag = 0
        parse_info = va_parse_as_lines(output)
        parse_info.pop(-1)
        for line in parse_info:
            line = line.lstrip()
            if line.startswith('Active'):
               active_tag = 1
               inactive_tag = 0
               current_key = line.rstrip(':')
               parsed[current_key] = list()
            elif line.startswith('Inactive'):
               active_tag = 0
               inactive_tag = 1
               current_key = line.rstrip(':')
               parsed[current_key] = list()
            elif not line.startswith('UUID')\
                    and not line.startswith('-')\
                    and not line.startswith('Total')\
                    and not line.startswith('*:'):
                if active_tag == 1:
                    Epi = namedtuple('Epi', ['uuid', 'hostname', 'ep_id', 'mode',
                                             'fabric_ip', 'management_ip', 'connected_since',
                                             'connected_type', 'licensed', 'type'])
                else:
                    Epi = namedtuple('Epi', ['uuid', 'hostname', 'last_connected_ep', 'mode'])
                values = line.split()
                parse_values = list()
                parse_tag = 0
                parse_element = ''
                for list_element in values:
                    if re.search('^@\w+$',list_element,re.I):
                        parse_tag = 1
                    if parse_tag:
                        if re.search('^\d{4}$',list_element):
                            parse_tag = 0
                            parse_element += '%s' % list_element
                            parse_values.append(parse_element)
                        else:
                            if re.search(r'INVALID$',list_element) :
                                parse_element += '%s' % list_element[0:4]
                                parse_values.append(parse_element)
                                parse_values.append('INVALID')
                                parse_tag = 0
                            else :
                                parse_element += '%s-' % list_element
                    else :
                        if re.search('^\*$',list_element):
                            parse_values[-1] += '*'
                        else:
                            parse_values.append(list_element)
                parsed[current_key].append(Epi(*parse_values))
            elif line.startswith('Total'):
                key, value = line.split(':')
                parsed[key] = value
            else:
                continue
        return parsed