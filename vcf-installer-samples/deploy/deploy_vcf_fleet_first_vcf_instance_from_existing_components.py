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

from vmware.vcf_installer import model_client

from utils.ssl_helper import get_ssl_cert_thumbprint
from utils.sddc_spec_util import WorkflowType, VERSION, \
    create_vcf_operations_management_spec, \
    hostname_to_fqdn, AUTO_GENERATED_PASSWORD, create_vcf_operations_spec, \
    create_vcf_operations_collector_spec, \
    create_sddc_vcenter_spec, create_sddc_nsxt_spec, create_sddc_manager_spec, \
    create_vcf_automation_spec, save_sddc_spec_to_file
from utils.client import create_vcf_installer_client
from utils.sddc_task_util import poll_sddc_validation_status, \
    poll_sddc_deployment_status
from utils.misc_util import parse_bool_or_str, \
    get_version_without_build_number

"""
Description:
Demonstrates how to deploy new VCF Fleet with first VCF Instance in it, reusing existing Vcenter and NSX-T.
Prerequisites for successful deployment:
    1. Existing components need to be configured and reachable by the VCF Installer appliance
    2. All provided hostnames must be resolvable from the VCF Installer appliance
    3. The addresses of all components must be resolvable from the VCF Installer appliance (NTP, various VCF
       components, etc.)
    4. The Depot configuration must be complete
    5. The respective binary bundles need to be downloaded

Downloading respective bundles can be achieved by running the
download_bundles_vcf_fleet_first_vcf_instance_from_existing_components sample.
"""

parser = argparse.ArgumentParser()

parser.add_argument(
    '--vcf_installer_fqdn',
    required=True,
    help='VCF Installer Appliance hostname or FQDN.')

parser.add_argument(
    '--vcf_installer_admin_password',
    required=True,
    help='VCF Installer Appliance password for admin@local user.')

parser.add_argument(
    '--dns_domain',
    required=True,
    help='Domain of existing and to-be-deployed appliances. Example: vcf.local')

parser.add_argument(
    '--dns_nameserver',
    required=True,
    help='Nameserver containing the domain\'s DNS records. Example: 192.168.0.1')

parser.add_argument(
    '--ntp_servers',
    required=True,
    help='Comma separated list of NTP servers used when deploying SDDC Manager appliance.')

parser.add_argument(
    '--vcf_ops_fleet_management_fqdn',
    required=True,
    help='Hostname or FQDN of the VCF Operations Fleet Management that will be deployed. Example: vcfops')

parser.add_argument(
    '--vcf_ops_fqdn',
    required=True,
    help='Hostname or FQDN of the VCF Operations that will be deployed. Example: vcfops1')

parser.add_argument(
    '--vcf_automation_fqdn',
    help='Hostname or FQDN of the VCF Automation that will be deployed. If left None along with'
         '--vcf_automation_pool_ip_range_start and --vcf_automation_pool_ip_range_end - VCF '
         'Automation deployment is skipped.')

parser.add_argument(
    '--vcf_automation_pool_ip_range_start',
    help='Start of the IP pool range of the VCF Automation. If left None along with'
         '--vcf_automation_fqdn and --vcf_automation_pool_ip_range_end - VCF '
         'Automation deployment is skipped.')

parser.add_argument(
    '--vcf_automation_pool_ip_range_end',
    help='End of the IP pool range of the VCF Automation. If left None along with'
         '--vcf_automation_fqdn and --vcf_automation_pool_ip_range_start - VCF '
         'Automation deployment is skipped.')

parser.add_argument(
    '--vcf_ops_collector_fqdn',
    required=True,
    help='Hostname or FQDN of the VCF Operations Collector that will be deployed')

parser.add_argument(
    '--vcenter_fqdn',
    required=True,
    help='Hostname or FQDN of the existing vCenter deployment. Example: vc1.vcf.local')

parser.add_argument(
    '--vcenter_thumbprint',
    help='SSL Certificate SHA256 Thumbprint of the vCenter deployment.')

parser.add_argument(
    '--vcenter_root_password',
    required=True,
    help='Password for the root user of the existing vCenter deployment.')

parser.add_argument(
    '--vcenter_admin_sso_username',
    required=True,
    help='Admin SSO Username for the existing vCenter deployment. Example: Administrator@VSPHERE.LOCAL')

parser.add_argument(
    '--vcenter_admin_sso_password',
    required=True,
    help='Admin SSO Password for the existing vCenter deployment')

parser.add_argument(
    '--nsx_fqdn',
    required=True,
    help='Hostname or FQDN of the existing NSX-T deployment. Example: nsx1.vcf.local')

parser.add_argument(
    '--nsx_vip_fqdn',
    required=True,
    help='Hostname or FQDN of the cluster for the existing NSX-T deployment. Example: nsx.vcf.local')

parser.add_argument(
    '--nsx_thumbprint',
    help='SSL Certificate SHA256 Thumbprint of the NSX-T deployment.')

parser.add_argument(
    '--nsx_root_password',
    required=True,
    help='Password for the root user of the existing NSX-T deployment.')

parser.add_argument(
    '--nsx_admin_password',
    required=True,
    help='Password for the admin user of the existing NSX-T deployment.')

parser.add_argument(
    '--nsx_audit_password',
    required=True,
    help='Password for the audit user of the existing NSX-T deployment.')

parser.add_argument(
    '--sddc_id',
    required=True,
    help='SDDC ID. Example: sddc-01')

parser.add_argument(
    '--sddc_manager_fqdn',
    required=True,
    help='Hostname or FQDN of the SDDC Manager that will be deployed. Example: sm.vcf.local')

parser.add_argument(
    "--validate_only",
    default=False,
    action=argparse.BooleanOptionalAction,
    help="Whether to only run the validations and skip deployment. Default: False")

parser.add_argument(
    '--ca_certs',
    default=True,
    type=parse_bool_or_str,
    help="""By default uses built-in CA.
    To pass custom CA provide absolute path to the folder containing CA certs to use for SSL verifications.
    Pass False to disable SSL verifications
    (do not leave it empty on production environments).""")

parser.add_argument(
    '--deployment_spec_save_file_path',
    help="""
    Path to file or directory where to save the actual deployment specification in JSON format used by the
    VCF Installer during deployment.
    """)

args = parser.parse_args()
server = args.vcf_installer_fqdn
password = args.vcf_installer_admin_password
client = create_vcf_installer_client(server=server,
                                     password=password,
                                     ca_certs=args.ca_certs)


def create_sddc_spec_for_new_vcf_fleet_with_existing_vcenter_nsx(vcf_client, args):
    spec = model_client.SddcSpec()
    spec.workflow_type = WorkflowType.VCF.name
    spec.ceip_enabled = True
    spec.version = get_version_without_build_number(vcf_client) or VERSION
    spec.ntp_servers = args.ntp_servers.split(',')
    spec.dns_spec = model_client.DnsSpec(subdomain=args.dns_domain,
                                         nameservers=args.dns_nameserver.split(","))
    # Skipping ESXi Thumbprint validation for deployments with existing vCenter.
    spec.skip_esx_thumbprint_validation = True

    # Operations stack
    spec.vcf_operations_fleet_management_spec = create_vcf_operations_management_spec(
        hostname_to_fqdn(args.vcf_ops_fleet_management_fqdn, args.dns_domain),
        AUTO_GENERATED_PASSWORD,  # VCF Ops Fleet Management Admin Password
        None,
        None,  # Deploy new VCF Ops Fleet Management
        args.ca_certs)
    spec.vcf_operations_spec = create_vcf_operations_spec(
        hostname_to_fqdn(args.vcf_ops_fqdn, args.dns_domain),
        AUTO_GENERATED_PASSWORD)  # VCF Ops Admin Password

    spec.vcf_operations_collector_spec = create_vcf_operations_collector_spec(
        hostname_to_fqdn(args.vcf_ops_collector_fqdn, args.dns_domain), False)

    # VCF Automation
    skip_vcf_automation = not (
        args.vcf_automation_fqdn or
        args.vcf_automation_pool_ip_range_start or
        args.vcf_automation_pool_ip_range_end)

    if not skip_vcf_automation:
        if not (  # not all required settings are set
                args.vcf_automation_fqdn and
                args.vcf_automation_pool_ip_range_start and
                args.vcf_automation_pool_ip_range_end):
            raise AssertionError("Missing VCF Automation settings")

        spec.vcf_automation_spec = create_vcf_automation_spec(
            hostname_to_fqdn(args.vcf_automation_fqdn, args.dns_domain),
            AUTO_GENERATED_PASSWORD,  # VCF Automation Admin Password
            None,
            args.vcf_automation_pool_ip_range_start,
            args.vcf_automation_pool_ip_range_end)

    # vCenter
    vcenter_fqdn = hostname_to_fqdn(args.vcenter_fqdn, args.dns_domain)
    vcenter_thumbprint = args.vcenter_thumbprint or get_ssl_cert_thumbprint(vcenter_fqdn)
    spec.vcenter_spec = create_sddc_vcenter_spec(
        hostname_to_fqdn(args.vcenter_fqdn, args.dns_domain),
        vcenter_thumbprint,
        args.vcenter_root_password,
        None,
        args.vcenter_admin_sso_username,  # vCenter Admin User SSO Username
        args.vcenter_admin_sso_password,  # vCenter Admin User SSO Password
        True)  # Use Existing vCenter

    # NSX-T
    nsxt_fqdn = hostname_to_fqdn(args.nsx_fqdn, args.dns_domain)
    nsxt_thumbprint = args.nsx_thumbprint or get_ssl_cert_thumbprint(nsxt_fqdn)
    spec.nsxt_spec = create_sddc_nsxt_spec(
        nsxt_fqdn,
        hostname_to_fqdn(args.nsx_vip_fqdn, args.dns_domain),
        nsxt_thumbprint,
        args.nsx_root_password,  # NSX-T Root Password
        args.nsx_admin_password,  # NSX-T Admin Password
        args.nsx_audit_password,  # NSX-T Audit Password
        None,
        None,
        True)  # Use Existing NSX-T

    # SDDC Manager
    spec.sddc_id = args.sddc_id
    spec.sddc_manager_spec = create_sddc_manager_spec(
        hostname_to_fqdn(args.sddc_manager_fqdn, args.dns_domain),
        AUTO_GENERATED_PASSWORD,  # SDDC Manager Root Password
        AUTO_GENERATED_PASSWORD,  # SDDC Manager Local User Password
        AUTO_GENERATED_PASSWORD,  # SDDC Manager VCF User Password
        False)  # Use Existing SDDC Manager

    return spec


sddc_spec = create_sddc_spec_for_new_vcf_fleet_with_existing_vcenter_nsx(client, args)
print("Crafted Deployment Spec is: " + sddc_spec.to_json())

validation = client.v1.sddcs.Validations.validate_sddc_spec(sddc_spec)
print("Started Sddc Spec validation task with id: {}".format(validation.id))
# poll the task status
poll_sddc_validation_status(client, validation.id, 3)
print("Finished Sddc Spec validation task with id: {}".format(validation.id))

if not args.validate_only:
    print("Starting VCF Fleet deployment")
    sddc_task = client.v1.Sddcs.deploy_sddc(sddc_spec)
    print("Started VCF Fleet deployment task with id: {}".format(sddc_task.id))
    # poll the task status
    poll_sddc_deployment_status(client, sddc_task.id, 7)
    print("Finished VCF Fleet deployment task with id: {}".format(sddc_task.id))
    save_sddc_spec_to_file(client, sddc_task.id, args.deployment_spec_save_file_path)

print("Sample completed successfully")
