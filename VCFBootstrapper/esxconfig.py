#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for
import json
import ssl
import atexit
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import os

app = Flask(__name__)
CONFIG_FILE = 'esxi_hosts_config.json'
CONFIGURED_FILE = 'configured_hosts.json'

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(CONFIGURED_FILE):
    with open(CONFIGURED_FILE, 'w') as f:
        json.dump([], f)

def update_host_config(host_config):
    context = ssl._create_unverified_context()
    try:
        si = SmartConnect(
            host=host_config["host"],
            user=host_config["username"],
            pwd=host_config["password"],
            sslContext=context
        )
        atexit.register(Disconnect, si)

        content = si.RetrieveContent()
        host_obj = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem], True).view[0]
        config_mgr = host_obj.configManager

        dns_config = vim.host.DnsConfig(
            hostName=host_config["hostname"],
            domainName=host_config["domain"],
            address=host_config["dns"]
        )
        config_mgr.networkSystem.UpdateDnsConfig(dns_config)

        nic = config_mgr.networkSystem.networkInfo.vnic[0].spec
        nic.ip = vim.host.IpConfig(
            dhcp=False,
            ipAddress=host_config["ip"],
            subnetMask=host_config["netmask"]
        )
        config_mgr.networkSystem.UpdateVirtualNic("vmk0", nic)

        route_config = vim.host.IpRouteConfig(
            defaultGateway=host_config["gateway"]
        )
        config_mgr.networkSystem.UpdateIpRouteConfig(route_config)

        try:
            current_ntp = config_mgr.dateTimeSystem.dateTimeInfo.ntpConfig.server
            if host_config["ntp"] not in current_ntp:
                ntp_config = vim.host.NtpConfig(server=[host_config["ntp"]])
                config_mgr.dateTimeSystem.UpdateDateTimeConfig(
                    vim.host.DateTimeConfig(ntpConfig=ntp_config))
            config_mgr.dateTimeSystem.EnableNtp()
        except Exception as e:
            print(f"⚠️ NTP config skipped or failed: {e}")

        if host_config.get("wipe_disks"):
            storage_mgr = config_mgr.storageSystem
            storage_mgr.RescanAllHba()
            storage_mgr.RescanVmfs()
            storage_mgr.RescanAll()

            boot_disk = host_obj.config.bootOptions.bootableDisk[0].devicePath if host_obj.config.bootOptions.bootableDisk else None
            for disk in storage_mgr.storageDeviceInfo.scsiLun:
                if isinstance(disk, vim.HostScsiDisk) and disk.devicePath != boot_disk:
                    try:
                        print(f"Wiping partitions on {disk.devicePath}...")
                        storage_mgr.UpdateDiskPartitions(disk.devicePath, spec=vim.HostDiskPartitionSpec())
                    except Exception as e:
                        print(f"⚠️ Failed to wipe {disk.devicePath}: {e}")

        return "success"
    except Exception as e:
        return f"[{host_config['host']}] ❌ Failed: {str(e)}"

@app.route('/')
def index():
    with open(CONFIG_FILE) as f:
        hosts = json.load(f)
    with open(CONFIGURED_FILE) as f:
        configured = json.load(f)
    return render_template('form.html', hosts=hosts, configured=configured)

@app.route('/add-host', methods=['POST'])
def add_host():
    dns_list = [d.strip() for d in request.form['dns'].split(',') if d.strip()]

    host_config = {
        "host": request.form['host'],
        "username": request.form['username'],
        "password": request.form['password'],
        "hostname": request.form['hostname'],
        "ip": request.form['ip'],
        "netmask": request.form['netmask'],
        "gateway": request.form['gateway'],
        "dns": dns_list,
        "domain": request.form['domain'],
        "ntp": request.form['ntp'],
        "wipe_disks": request.form.get('wipe_disks') == 'on'
    }

    with open(CONFIG_FILE, 'r') as f:
        existing = json.load(f)
    existing.append(host_config)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(existing, f, indent=2)

    return redirect(url_for('index'))

@app.route('/remove-host/<int:index>', methods=['POST'])
def remove_host(index):
    with open(CONFIG_FILE, 'r') as f:
        hosts = json.load(f)
    if 0 <= index < len(hosts):
        del hosts[index]
        with open(CONFIG_FILE, 'w') as f:
            json.dump(hosts, f, indent=2)
    return redirect(url_for('index'))

@app.route('/apply-all', methods=['POST'])
def apply_all():
    with open(CONFIG_FILE) as f:
        hosts = json.load(f)
    successful = []
    failed = []
    results = []
    for host in hosts:
        result = update_host_config(host)
        if result == "success":
            successful.append(host)
            results.append(f"[{host['host']}] ✅ Configuration applied successfully.")
        else:
            failed.append(host)
            results.append(result)

    with open(CONFIGURED_FILE, 'r') as f:
        previously_configured = json.load(f)
    previously_configured.extend(successful)
    with open(CONFIGURED_FILE, 'w') as f:
        json.dump(previously_configured, f, indent=2)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(failed, f, indent=2)

    return render_template('result.html', result="\n".join(results))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)




