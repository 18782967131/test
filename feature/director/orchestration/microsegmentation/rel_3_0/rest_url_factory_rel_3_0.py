"""coding: utf-8

Copyright 2016 vArmour Networks private.
All Rights reserved. Confidential

VaResturlfactory has all va rest feature urls

.. moduleauthor:: ckung@varmour.com
"""
from purl import URL


class VaResturlfactory:
    """
    VaResturlfactory generates url cooresponding to va rest request
    """
    api = '/api/v1.0'
    auth = '/auth'
    micro_segmentation = '/operation/micro-segmentation'
    microsegmentation = '/operation/orchestration/inventory/microsegmentation'
    configMicro_segmentation = '/config/micro-segmentation'
    configChassisEpi = '/config/chassis/epi'
    segmentationInfo = '/operation/orchestration/inventory/segmentation/info'
    revert = '/operation/orchestration/inventory/microsegmentation/revert'
    segmentationStats = '/operation/orchestration/inventory/segmentation/stats'
    inventory = '/operation/orchestration/inventory'
    inventoryHost = '/operation/orchestration/inventory/host'
    chassisEpi = '/operation/chassis/epi'
    configOrchestration = '/config/orchestration'
    checkOrchestration = '/operation/orchestration'
    commit = '/commit'
    rollback = '/rollback'

    def __init__(self, ip):
        """
        constructor generates URL object
        Args:
            ip: director ip
        """
        self.__url = URL(scheme='https', host=ip)

    def va_get_url(self, feature=None):
        """
        get_url returns url objects based on feature input
        :param feature: (str): va rest feature
        :return: (URL) object
        """
        return {
            'auth': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.auth),
            'microsegmentation': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.microsegmentation),
            'micro_segmentation': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.micro_segmentation),
            'configMicro_segmentation': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.configMicro_segmentation),
            'configChassisEpi': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.configChassisEpi),
            'revert': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.revert),
            'segmentationInfo': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.segmentationInfo),
            'segmentationStats': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.segmentationStats),
            'inventory': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.inventory),
            'inventoryHost': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.inventoryHost),
            'chassisEpi': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.chassisEpi),
            'configOrchestration': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.configOrchestration),
            'checkOrchestration': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.checkOrchestration),
            'commit': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.commit),
            'rollback': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.rollback)
        }[feature]
