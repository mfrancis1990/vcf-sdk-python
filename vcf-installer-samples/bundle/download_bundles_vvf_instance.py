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

import argparse

import utils.download_bundles_util
import utils.misc_util

from utils import download_bundles_util
from utils.client import create_vcf_installer_client
from utils.misc_util import parse_bool_or_str

"""
Demonstrates how to configure online depot and download bundles necessary for deploying VVF.
This includes the following components: vCenter, VCF Operations.
"""

parser = argparse.ArgumentParser()

parser.add_argument(
    '--vcf_installer_host_address',
    required=True,
    help='VCF Installer Appliance address')

parser.add_argument(
    '--vcf_installer_admin_password',
    required=True,
    help='VCF Installer Appliance password for admin@local user')

parser.add_argument(
    '--depot_account_username',
    required=True,
    help='Depot username for access.')

parser.add_argument(
    '--depot_account_password',
    required=True,
    help='Depot password for access.')

parser.add_argument(
    '--ca_certs',
    default=True,
    type=parse_bool_or_str,
    help="""By default uses built-in CA.
    To pass custom CA provide absolute path to the folder containing CA certs to use for SSL verifications.
    Pass False to disable SSL verifications 
    (do not leave it empty on production environments).""")

parser.add_argument(
    '--time_to_wait_for_depot_sync_in_minutes',
    required=False,
    default=download_bundles_util.DEFAULT_DEPOT_SYNC_TIMEOUT_MINS,
    help='The maximum time that the depot sync status should be polled until it has completed, measured in minutes.')

parser.add_argument(
    '--time_to_wait_in_between_polls_for_depot_sync_in_seconds',
    required=False,
    default=download_bundles_util.DEFAULT_WAIT_BETWEEN_POLLS_DEPOT_SYNC_SEC,
    help='The time to sleep in between each poll when polling the depot sync status, measured in seconds.')

parser.add_argument(
    '--max_time_to_poll_download_status_in_hours',
    required=False,
    default=download_bundles_util.DEFAULT_POLL_DOWNLOAD_STATUS_TIMEOUT_HOURS,
    help='The maximum time that the download status should be polled until all bundles have been successfully downloaded, measured in hours.')

parser.add_argument(
    '--time_to_sleep_in_between_polls_for_download_status_in_seconds',
    required=False,
    default=download_bundles_util.DEFAULT_WAIT_BETWEEN_POLLS_DOWNLOAD_STATUS_SEC,
    help='The time to sleep in between each poll when polling the download status of the bundles, measured in seconds.')

args = parser.parse_args()
server = args.vcf_installer_host_address
password = args.vcf_installer_admin_password
client = create_vcf_installer_client(server=server,
                                     password=password,
                                     ca_certs=args.ca_certs)

download_bundles_util.configure_online_depot(client,
                                             args.depot_account_username,
                                             args.depot_account_password)
print("Configured online depot")

download_bundles_util.force_sync_depot(client,
                                       args.time_to_wait_for_depot_sync_in_minutes,
                                       args.max_time_to_poll_download_status_in_hours)
print("Synced online depot")

version_without_build_number = utils.misc_util.get_version_without_build_number(client)

latest_product_release_components = download_bundles_util.get_latest_product_release_components(
    client=client,
    sku="VVF",
    release_version=version_without_build_number,
    product_release_components_names_to_include={"VCENTER",
                                                 "VROPS"  # VCF Operations
                                                 })
print("Retrieved product release components")

bundle_ids_being_downloaded = download_bundles_util.start_bundles_download(
    client, latest_product_release_components)
print("Started downloading all necessary bundles".format(bundle_ids_being_downloaded))

utils.download_bundles_util.poll_bundles_downloaded(
    client,
    bundle_ids_being_downloaded,
    version_without_build_number,
    args.time_to_wait_for_depot_sync_in_minutes,
    args.max_time_to_poll_download_status_in_hours)
print("Downloaded all necessary bundles")

print("Sample completed successfully")
