# VMware vSphere Automation SDK for Python  

## Table of Contents
- [Abstract](#abstract)
- [Supported vCenter Releases](#supported-onprem-vcenter-releases)
- [Quick Start Guide](#quick-start-guide)
- [Run SDK Samples](#run-sdk-samples)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Support](#support)
- [Repository Administrator Resources](#repository-administrator-resources)
- [VMware Resources](#vmware-resources)

## Abstract
This document describes the vSphere Automation Python SDK samples that use the vSphere Automation
python client library. Additionally, some of the samples demonstrate the combined use of the
vSphere Automation and vSphere APIs. To support this combined use, the vSphere Automation Python SDK
samples require the vSphere Management SDK packages (pyVmomi) to be installed on the client.
The samples have been developed to work with python 3.9+

## Supported OnPrem vCenter Releases
vCenter 7.0, 7.0U1, 7.0U2, 7.0U3 , 8.0, 8.0U1, 8.0U2, 8.0U3, 9.0.0.0
Please refer to the notes in each sample for detailed compatibility information.

## Quick Start Guide

### Prepare a Python Development Environment

We recommend you to install latest [Python](http://docs.python-guide.org/en/latest/starting/installation/) and [pip](https://pypi.python.org/pypi/pip/) on your system.

A Python virtual environment is also highly recommended.
* [Install a virtual env for Python 3](https://docs.python.org/3/tutorial/venv.html)

### Installing Required Python Packages
SDK package installation commands may differ depending on the environment where it is being installed. The three installation options provided below are for different environments.
*pip* and *setuptools* are common requirements for these installation types, upgrade to the latest *pip* and *setuptools*.

**NOTE:** The SDK also requires OpenSSL 1.0.1+ in order to support TLS1.1 & 1.2

##### 1. Typical Installation
This is the recommended way to install the SDK. The installation is done from [PyPI](https://pypi.org/) and [Automation SDK Python Github](https://github.com/vmware/vsphere-automation-sdk-python) repositories.

Install/Update latest pip from PyPI.
```cmd
pip install --upgrade pip
```
Install/Update setuptools
```cmd
pip install --upgrade setuptools
```
Install SDK packages from GitHub.
```cmd
pip install --upgrade git+https://github.com/vmware/vsphere-automation-sdk-python.git
```

### Connect to a vCenter Server

```python
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client
session = requests.session()

# Disable cert verification for demo purpose. 
# This is not recommended in a production environment.
session.verify = False

# Disable the secure connection warning for demo purpose.
# This is not recommended in a production environment.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Connect to a vCenter Server using username and password
vsphere_client = create_vsphere_client(server='<vc_ip>', username='<vc_username>', password='<vc_password>', session=session)

# List all VMs inside the vCenter Server
vsphere_client.vcenter.VM.list()
```

Output in a Python Interpreter:

```shell
(venv) het-m03:vsphere-automation-sdk-python het$ python
Python 3.9.8 (main, Nov 10 2021, 06:03:50)
[GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import requests
>>> import urllib3
>>> from vmware.vapi.vsphere.client import create_vsphere_client
>>> session = requests.session()
>>> session.verify = False
>>> urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 
>>> vsphere_client = create_vsphere_client(server='<vc_ip>', username='<vc_username>', password='<vc_password>', session=session)
>>> vsphere_client.vcenter.VM.list()
[Summary(vm='vm-58', name='standalone-20e4bd3af-esx.0-vm.0', power_state=State(string='POWERED_OFF'), cpu_count=1, memory_size_mib=256), 
...]
```

**NOTE:** If you are using Bash, be sure to use single quote for username and password to preserve the values. If you use double quote, you will have to escape special characters, such as "$". See [Bash manual](http://www.gnu.org/software/bash/manual/html_node/Double-Quotes.html) 

## Run SDK Samples

In this section, we will walk you through the steps to run the sample code for vSphere.

### First, set PYTHONPATH to use SDK helper methods  

* Linux/Mac:

    export PYTHONPATH=\$\{PWD\}:\$PYTHONPATH

* Windows:

    set PYTHONPATH=%cd%;%PYTHONPATH%

### Run vSphere Samples

A vSphere test environment is required with the following configuration:
* 1 vCenter Server
* 2 ESX hosts
* 1 NFS Datastore with at least 3GB of free capacity

**Note** Please have the details of these available but do not have any configuration pre-created on vCenter server or ESXi Hosts, for example there should be no existing datacenters, clusters or attached hosts on the vCenter server.

#### Running the SDK Sample Setup Script

Before executing the samples we'll need to setup the vSphere test environment using one of the sample scripts (samples/vsphere/vcenter/setup/main.py). The script will perform the following:

* Create 2 test Datacenters 
* Create a test Cluster
* Create Test Folders for VM Storage
* Attach the hosts
* Create a Distributed Switch
* Create a Distributed Portgroup
* Attach the NFS datastore (if Selected) to the hosts
* Copy the [Photon OS](https://vmware.github.io/photon/) ISO image downloaded from [VMware's bintray server](https://github.com/vmware/photon/wiki/Downloading-Photon-OS#downloading-photon-os-50-ga) to the datastore
* Create directories to add sample ports

First, edit settings in samples/vsphere/vcenter/setup/testbed.py and replace everything in < > brackets with your environment information. Leave the rest of the settings in this file at their default values.

```python
config["SERVER"]    = "<vcenter_hostname_or_ip>"
config["USERNAME"]  = "<vsphere_username>"
config["PASSWORD"]  = "<vsphere_password>"

config["ESX_HOST1"] = "<ESX_host1_ipaddress>"
config["ESX_HOST2"] = "<ESX_host2_ipaddress>"
config["ESX_USER"]  = "<esx_username>"
config["ESX_PASS"]  = "<esx_password>"

config["USE_NFS"]   = True
config["NFS_HOST"]  = "<nfs_ipaddress>"
config["NFS_REMOTE_PATH"] = "/store1"
```

At this point, we're ready to run the setup script: 

```cmd
$ python samples/vsphere/vcenter/setup/main.py -sv
```

After completion you will see from the output and also the vSphere Client that the environment has now been fully setup and is ready to easily run further samples.

To view other available command-line options:

```cmd
$ python samples/vsphere/vcenter/setup/main.py -h
```

#### Run the vAPI vCenter sample suite:

```cmd
$ python samples/vsphere/vcenter/setup/main.py -riv
```

#### Run a specific sample in a standalone mode:

```cmd
$ python samples/vsphere/vcenter/vm/list_vms.py -v
```

## Troubleshooting

Common issues you may run into while installing the sdk and running samples are listed [here](https://github.com/vmware/vsphere-automation-sdk-python/wiki/Troubleshooting)

## Support

Support details can be referenced under the **SDK and API Support for Commercial and Enterprise Organizations** section at [Broadcom Developer Portal](https://developer.broadcom.com/support).

For community support, please open a [Github issue](https://github.com/vmware/vsphere-automation-sdk-python/issues) or start a [Discussion](https://github.com/vmware/vsphere-automation-sdk-python/discussions).

## Repository Administrator Resources

### Board Members

Board members are volunteers from the SDK community and VMware staff members, board members are not held responsible for any issues which may occur from running of samples from this repository.

Members:
* Ankit Agrawal (VMware)
* Jobin George (VMware)
* Martin Tsvetanov (VMware)
* Shweta Purohit (VMware)
* Kunal Singh (VMware)

## VMware Resources
* VMware vSphere [REST API Reference documentation](https://developer.broadcom.com/xapis/vsphere-automation-api/latest/).
