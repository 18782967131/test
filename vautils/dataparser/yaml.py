"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

fileutil implements utility functions for parsing and printing data
represented in yaml, json forms.

.. moduleauthor:: vArmour
"""

import yaml
import json

from vautils import logger


def load_yaml(yaml_file=None):
    """
    function to open a yaml file and return the python form.

    Args:
        :input_file (str): file name

    Returns:
        python form of the yaml data
    """
    with open(yaml_file, 'r') as yaml_form:
        return yaml.load(yaml_form)
