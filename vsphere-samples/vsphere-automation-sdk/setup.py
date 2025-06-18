#!/usr/bin/env python

import os

from setuptools import setup

setup(name='vsphere-automation-sdk',
      version='9.0.0.0',
      description='VMware vSphere Automation SDK for Python',
      url='https://github.com/vmware/vsphere-automation-sdk-python',
      author='Broadcom, Inc.',
      license='MIT',
      packages=[],
      install_requires=[
            'lxml >= 4.3.0',
            'six >= 1.12',
            'pyVmomi == 9.0.0.0',
            'vmware-vapi-common-client == 2.61.2',
            'vmware-vapi-runtime == 2.61.2',
            'vmware-vcenter == 9.0.0.0',
            'vmware-vsan-data-protection==9.0.0.0',
      ]
      )
