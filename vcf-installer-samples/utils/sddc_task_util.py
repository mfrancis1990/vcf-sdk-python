"""
* *******************************************************
* Copyright (c) 2025 Broadcom. All rights reserved.
* The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
* *******************************************************
*
* DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
* EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
* WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
* NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.
"""

from utils.misc_util import poll

_VALIDATION_STATUS_COMPLETED = "COMPLETED"
_VALIDATION_STATUS_IN_PROGRESS = "IN_PROGRESS"
_DEPLOYMENT_STATUS_COMPLETED_WITH_SUCCESS = "COMPLETED_WITH_SUCCESS"
_DEPLOYMENT_STATUS_COMPLETED_WITH_FAILURE = "COMPLETED_WITH_FAILURE"

_DEFAULT_POLL_INTERVAL = 60


def poll_sddc_validation_status(client, validation_id, timeout):
    """
    Poll the validation status.

    :type: client: :class:`utils.client.VcfInstallerClient`
    :param client: VCF Installer Client
    :param validation_id: id of validation
    :param timeout: time to poll before giving up (in hours)
    :return: retrieved validation if it is successful or `None` if still in progress
    :rtype: :class:`vmware.vcf_installer.model_client.Validation`
    :raises AssertionError: If validation fails or a timeout is hit.
    """
    def poller():
        validation = client.v1.sddcs.Validations.get_sddc_spec_validation(validation_id)
        if not validation:
            raise AssertionError("Unable to poll validation")
        elif validation.execution_status == _VALIDATION_STATUS_COMPLETED:
            return validation
        elif validation.execution_status != _VALIDATION_STATUS_IN_PROGRESS:
            raise AssertionError("Failed to perform validation with id ",
                                 validation_id, validation.execution_status)
        else:
            return None

    return poll(poller, timeout, _DEFAULT_POLL_INTERVAL)


def poll_sddc_deployment_status(client, sddc_task_id, timeout):
    """
    Poll the SDDC deployment task status.

    :type: client: :class:`utils.client.VcfInstallerClient`
    :param client: VCF Installer Client
    :param sddc_task_id: id of sddc deployment task
    :param timeout: time to poll before giving up (in hours)
    :return: the retrieved task if it is successful or `None` if still in progress
    :rtype: :class:`vmware.vcf_installer.model_client.SddcTask`
    :raises AssertionError: If validation fails or a timeout is hit.
    """
    def poller():
        task = client.v1.Sddcs.get_sddc_task_by_id(sddc_task_id)
        if not task:
            raise AssertionError("Unable to poll sddc deployment task")
        elif task.status == _DEPLOYMENT_STATUS_COMPLETED_WITH_SUCCESS:
            return task
        elif task.status == _DEPLOYMENT_STATUS_COMPLETED_WITH_FAILURE:
            raise AssertionError("Failed deployment with id {}".format(sddc_task_id))
        else:
            return None

    return poll(poller, timeout, _DEFAULT_POLL_INTERVAL)
