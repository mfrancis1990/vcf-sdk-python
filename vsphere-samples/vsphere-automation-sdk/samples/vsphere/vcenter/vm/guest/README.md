This directory contains below samples for inventory APIs:

1. Bulk Transition

   | Sample                     | Description                                                                 |
   |----------------------------|-----------------------------------------------------------------------------|
   | customize_live_vm.py       | Demonstrates customizing a running virtual machine and start the network service in the guest.                   |


### Running the samples:

    #For example, you can use the following command to customize the running VM
    python vsphere-samples/vsphere-automation-sdk/samples/vsphere/vcenter/vm/guest/customize_live_vm.py -s "<vcenter_ip>" -u "<vcenter_user>" -p "<vcenter_password>" -n "<vm_name>" -v -vu "<vm_username>" -vp "<vm_password>" -c
### Testbed Requirement:

    - vCenter Server >= 9.0.0+
