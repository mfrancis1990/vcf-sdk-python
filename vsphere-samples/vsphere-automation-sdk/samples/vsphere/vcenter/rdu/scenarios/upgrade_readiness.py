#!/usr/bin/env python
"""
* *******************************************************
* Copyright (c) Broadcom, Inc. 2025. All Rights Reserved.
* SPDX-License-Identifier: MIT
* *******************************************************
*
* DISCLAIMER. THIS PROGRAM IS PROVIDED TO YOU "AS IS" WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, WHETHER ORAL OR WRITTEN,
* EXPRESS OR IMPLIED. THE AUTHOR SPECIFICALLY DISCLAIMS ANY IMPLIED
* WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY,
* NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE.
"""

__author__ = 'Broadcom, Inc.'
__vcenter_version__ = '9.0.0'

import logging
import sys

from samples.vsphere.common import sample_util
from samples.vsphere.vcenter.rdu.update_plugin_util.update_vcenter_lifecycle_manager import UpdateLifecyclePlugin
from samples.vsphere.vcenter.rdu.rdu_runner.rdu_steps import RDU
from samples.vsphere.vcenter.rdu.rdu_runner.init_spec import InitSpec
from samples.vsphere.vcenter.rdu.utils import get_rdu_arg_parser
from samples.vsphere.vcenter.rdu.rdu_runner.status import notifications_to_str


logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

parser = get_rdu_arg_parser()
args = sample_util.process_cli_args(parser.parse_args())


def main():
    """
    This scenario demonstrates how to check if the environment is ready for upgrade
    without actually triggering the upgrade.

    It includes the following steps:

    1. Update the lifecycle plugin. If the plugin has already been upgraded this script won't fail
    and will continue with the upgrade.
    2. Create an init spec. This example create an init spec with only the mandatory fields.
       All other fields will be autopopulated by the framework.
    3. Run the precheck API with the init spec.
    :return:
    """
    logger.info("Step 1: Update lifecycle manager plug-in")

    plugin_update = UpdateLifecyclePlugin(args.server, args.username, args.password, args.skipverification, args.target_upgrade_repo)
    plugin_update.run()

    logger.info("Step 2: Create init spec for the upgrade.")
    init_spec = InitSpec(root_password=args.target_temp_password,
                         target_version=args.target_version,
                         target_ova=args.target_ova,
                         target_upgrade_repo=args.target_upgrade_repo).get_init_spec()
    logger.info("Init spec can be further customized than what is show in this sample. "
                "For details check the API documentation.")

    logger.info("Step 3: Run prechecks against the created init spec")
    rdu_upgrade = RDU(username=args.username, password=args.password,
                      server=args.server, skipverification=args.skipverification)

    precheck_result = rdu_upgrade.precheck(init_spec=init_spec)
    if precheck_result.notifications.errors:
        logger.error("Provided init spec didn't pass the prechecks. "
                     "Check the prechecks result for problems and try again:\n %s",
                     notifications_to_str(precheck_result.notifications))
        return


if __name__ == "__main__":
    main()
