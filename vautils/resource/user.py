""" coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaUser implements the class that abstracts the data type for a user that can
access a remote test gear.

.. moduleauthor:: ppenumarthy@varmour.com
"""

from vautils.exceptions import InvalidUser


class VaUser(dict):
    """
    VaUser implements a valid va user. It inherits from the built-in data type
    dict.
    """
    def __init__(
        self,
        name=None,
        password=None,
        role=None,
        type=None,
        shell_password=None
    ):
        """
        Initializes the va user object.

        Kwargs:
            :name (str): name of the user
            :password (str): password for the user
            :role (str): role of the user
            :type (str): type of the user
            :shell_password (str): required for varmour devices - dir, ep, epi
        """
        if not name:
            raise InvalidUser('name', type)
        if not password:
            raise InvalidUser('password', type)

        self.update({
            'name': name,
            'password': password,
            'role': role,
            'type': type,
            'shell_password': shell_password
        })
