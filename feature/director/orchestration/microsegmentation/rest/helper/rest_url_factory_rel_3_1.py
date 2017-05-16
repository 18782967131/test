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
    enable_auto_microsegment = '/config/orchestration/vcenter/microsegmentation/auto-segment-enable'
    disable_auto_microsegment = '/config/orchestration/vcenter/microsegmentation/auto-segment-disable'
    configMicro_segmentation = '/config/micro-segmentation'
    configChassisEpi = '/config/chassis/epi'
    segmentationInfo = '/operation/orchestration/inventory/segmentation/info'
    revert = '/operation/orchestration/inventory/microsegmentation/revert'
    segmentationStats = '/operation/orchestration/inventory/segmentation/stats'
    inventory = '/operation/orchestration/inventory'
    inventory_updatestatus = '/operation/orchestration/inventory/updatestatus'
    inventoryHost = '/operation/orchestration/inventory/host'
    chassisEpi = '/operation/chassis/epi'
    configOrchestration = '/config/orchestration'
    checkOrchestration = '/operation/orchestration'
    operation_deployment_deploy = '/operation/orchestration/deployment/deploy'
    operation_deployment_remove = '/operation/orchestration/deployment/remove'
    operation_deployment_info = '/operation/orchestration/deployment/info'
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
        :param feature (str): va rest feature
        :return (URL): url object
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
            'enable_auto_microsegment': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.enable_auto_microsegment),
            'disable_auto_microsegment': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.disable_auto_microsegment),
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
            'inventoryUpdatestatus': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.inventory_updatestatus),
            'chassisEpi': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.chassisEpi),
            'configOrchestration': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.configOrchestration),
            'checkOrchestration': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.checkOrchestration),
            'operationDeployment': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.operation_deployment_deploy
            ),
            'operationRemoveDeployment': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.operation_deployment_remove
            ),
            'operationDeploymentInfo': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.operation_deployment_info
            ),
            'commit': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.commit),
            'rollback': self.__url.path(
                VaResturlfactory.api +
                VaResturlfactory.rollback)
        }[feature]
