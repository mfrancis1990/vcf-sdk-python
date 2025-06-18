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
from vmware.vcf_installer.model_client import SddcDatastoreSpec

from utils.sddc_spec_util import WorkflowType, VERSION, \
    create_vcf_operations_spec, hostname_to_fqdn, \
    AUTO_GENERATED_PASSWORD, create_sddc_vcenter_spec, CLUSTER_NAME, \
    CLUSTER_DATACENTER_NAME, create_vsan_spec, get_hosts_to_thumbprint, \
    create_sddc_host_specs, get_default_network_profile, \
    create_sddc_network_specs, save_sddc_spec_to_file
from utils.client import create_vcf_installer_client
from utils.sddc_task_util import poll_sddc_validation_status, \
    poll_sddc_deployment_status
from utils.misc_util import parse_bool_or_str, \
    get_version_without_build_number

"""
Description:
Demonstrates how to deploy new VVF Instance.
Prerequisites for successful deployment:
    1. At least 4 prepared ESXi hosts
    2. All provided hostnames must be resolvable from the VCF Installer appliance
    3. The addresses of all components must be resolvable from the VCF Installer appliance (NTP, various VCF
        components, etc.)
    4. The Depot configuration must be complete
    5. The respective binary bundles need to be downloaded
Downloading respective bundles can be achieved by running the download_bundles_vvf_instance sample.
"""

parser = argparse.ArgumentParser()

parser.add_argument(
    '--vcf_installer_fqdn',
    required=True,
    help='VCF Installer Appliance name or FQDN.')

parser.add_argument(
    '--vcf_installer_admin_password',
    required=True,
    help='VCF Installer Appliance password for admin@local user')

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
    '--vcf_ops_fqdn',
    required=True,
    help='Hostname or FQDN of the VCF Operations that will be deployed. Example: vcfops1')

parser.add_argument(
    '--vcenter_fqdn',
    required=True,
    help='Hostname or FQDN of the vCenter that will be deployed. Example: vc1.vcf.local')

parser.add_argument(
    '--vcenter_sso_domain',
    default='vsphere.local',
    help='SSO domain for the vCenter deployment. Defaults to vsphere.local')

parser.add_argument(
    '--esxi_host_root_password',
    required=True,
    help='Password for the hosts used')

parser.add_argument(
    '--esx_hosts',
    required=True,
    help=""""String of a list of comma separated ESXi fqdns and (optional) SSL Certificate SHA256 thumbprints.
Example:
esx1.vcf.local,
esx2,
esx3=51:8D:84:62:AB:06:9E:BC:1D:2C:F5:72:FB:D2:C4:CA:D3:7D:BF:E1:19:98:D7:6D:A9:F4:9A:A4:03:E3:0B:38,
esx4.vcf.local=3F:AD:17:6C:80:29:10:B2:C6:BB:B9:41:18:CD:1C:3D:04:FF:F8:22:4E:58:F0:FD:D4:44:D2:B1:0A:9B:94:20""")

parser.add_argument(
    '--management_network_gateway',
    required=True,
    help='Gateway of the Management network. Example: 192.168.1.1')

parser.add_argument(
    '--management_network_subnet',
    required=True,
    help='Subnet of the Management network. Example: 192.168.1.0/24')

parser.add_argument(
    '--management_network_vlan_id',
    required=True,
    help='VLAN ID Of the management network. Example: 1',
    type=int)

parser.add_argument(
    '--vsan_network_gateway',
    required=True,
    help='Gateway of the vSAN network. Example: 192.168.2.1')

parser.add_argument(
    '--vsan_network_subnet',
    required=True,
    help='Subnet of the vSAN network. Example: 192.168.2.0/24')

parser.add_argument(
    '--vsan_network_vlan_id',
    required=True,
    help='VLAN ID Of the vSAN network. Example: 2',
    type=int)

parser.add_argument(
    '--vsan_network_ip_range_start',
    required=True,
    help='Start of the IP pool range of the vSAN network. Example: 192.168.2.2')

parser.add_argument(
    '--vsan_network_ip_range_end',
    required=True,
    help='End of the IP pool range of the vSAN network. Example: 192.168.2.200')

parser.add_argument(
    '--vmotion_network_gateway',
    required=True,
    help='Gateway of the vMotion network. Example: 192.168.3.1')

parser.add_argument(
    '--vmotion_network_subnet',
    required=True,
    help='Subnet of the vMotion network. Example: 192.168.3.0/24')

parser.add_argument(
    '--vmotion_network_vlan_id',
    required=True,
    help='VLAN ID Of the vMotion network. Example: 3',
    type=int)

parser.add_argument(
    '--vmotion_network_ip_range_start',
    required=True,
    help='Start of the IP pool range of the vMotion network. Example: 192.168.3.2')

parser.add_argument(
    '--vmotion_network_ip_range_end',
    required=True,
    help='End of the IP pool range of the vMotion network. Example: 192.168.3.200')

parser.add_argument(
    '--sddc_id',
    required=True,
    help='SDDC ID. Example: sddc-01')

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


def create_sddc_spec_for_new_vvf_instance(vcf_client, args):
    spec = model_client.SddcSpec()
    spec.workflow_type = WorkflowType.VVF.name
    spec.ceip_enabled = True
    spec.version = get_version_without_build_number(vcf_client) or VERSION
    spec.ntp_servers = args.ntp_servers.split(',')
    spec.dns_spec = model_client.DnsSpec(subdomain=args.dns_domain,
                                         nameservers=args.dns_nameserver.split(","))

    # Operations stack
    spec.vcf_operations_spec = create_vcf_operations_spec(
        hostname_to_fqdn(args.vcf_ops_fqdn, args.dns_domain),
        AUTO_GENERATED_PASSWORD,  # VCF Ops Admin Password
        False)  # Use Existing VCF Ops

    # vCenter
    spec.vcenter_spec = create_sddc_vcenter_spec(
        hostname_to_fqdn(args.vcenter_fqdn, args.dns_domain),
        None,  # vCenter SSL Thumbprint is required only for existing vCenter deployments
        AUTO_GENERATED_PASSWORD,  # vCenter Root Password
        args.vcenter_sso_domain,
        None,  # vCenter Admin User SSO Username
        AUTO_GENERATED_PASSWORD,  # vCenter Admin User SSO Password
        False)  # Use Existing vCenter

    spec.cluster_spec = model_client.SddcClusterSpec(CLUSTER_NAME.format(
        args.sddc_id), CLUSTER_DATACENTER_NAME.format(args.sddc_id))

    # Host Storage
    datastore_spec = SddcDatastoreSpec()
    datastore_spec.vsan_spec = create_vsan_spec()
    spec.datastore_spec = datastore_spec

    # Hosts
    hosts_dict = get_hosts_to_thumbprint(
        args.esx_hosts, args.dns_domain, args.ca_certs)
    host_specs = create_sddc_host_specs(args.esxi_host_root_password, hosts_dict)
    spec.host_specs = host_specs  # Host specs are required for greenfield deployments.

    # Networking
    default_network_profile = get_default_network_profile(vcf_client, args.dns_domain, host_specs)
    default_dvs_specs = default_network_profile.dvs_specs
    dvs_portgroups = default_network_profile.dvs_name_to_portgroup_specs[
        default_dvs_specs[0].dvs_name]
    spec.dvs_specs = default_dvs_specs
    spec.network_specs = create_sddc_network_specs(
        dvs_portgroups,
        args.management_network_gateway,
        args.management_network_subnet,
        args.management_network_vlan_id,
        args.vsan_network_gateway,
        args.vsan_network_subnet,
        args.vsan_network_vlan_id,
        args.vsan_network_ip_range_start,
        args.vsan_network_ip_range_end,
        args.vmotion_network_gateway,
        args.vmotion_network_subnet,
        args.vmotion_network_vlan_id,
        args.vmotion_network_ip_range_start,
        args.vmotion_network_ip_range_end)

    spec.sddc_id = args.sddc_id

    return spec


sddc_spec = create_sddc_spec_for_new_vvf_instance(client, args)
print("Crafted Deployment Spec is: " + sddc_spec.to_json())

validation = client.v1.sddcs.Validations.validate_sddc_spec(sddc_spec)
print("Started VVF Instance Deployment Spec validation task with id: {}".format(validation.id))
# poll the task status
poll_sddc_validation_status(client, validation.id, 3)
print("Finished VVF Instance Deployment Spec validation task with id: {}".format(validation.id))

if not args.validate_only:
    print("Starting VVF Instance deployment")
    sddc_task = client.v1.Sddcs.deploy_sddc(sddc_spec)
    print("Started VVF Instance deployment task with id: {}".format(sddc_task.id))
    # poll the task status
    poll_sddc_deployment_status(client, sddc_task.id, 7)
    print("Finished VVF Instance deployment task with id: {}".format(sddc_task.id))
    save_sddc_spec_to_file(client, sddc_task.id, args.deployment_spec_save_file_path)

print("Sample completed successfully")
