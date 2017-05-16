"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

parser implements generic functions for parsing string output

.. moduleauthor:: ppenumarthy@varmour.com
"""

import re


def va_parse_basic(output=None):
    """
    parses a string output into a tablular form of data which consists of keys
    and values.

    args:
        :output (str): output of the command

    returns:
        :parsed (dict): properties as keys and their values
    """
    parsed_dict = dict()

    if output:
        for line in output.splitlines():
            if not line == '\r' and re.match(r'.*:.*', line):
                line = line.rstrip()
                prop, value = line.split(':', 1)
                parsed_dict[prop.strip()] = value.strip()

        return parsed_dict


def va_parse_as_lines(output=None, ignore_line=0):
    """
    parses a string output into a list of lines split at line break

    args:
        :output (str): output of the command
        :ignore_line (int): all lines until the ignore_line will be ignored
                            in the output

    returns:
        :parsed (list): list of line strings
    """
    list_of_lines = output.splitlines()
    return list_of_lines[ignore_line + 1:]
