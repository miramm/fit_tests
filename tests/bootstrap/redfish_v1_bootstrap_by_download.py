# Copyright 2016, EMC, Inc.

'''
This script is only for use in Plymouth MN Lab, contains direct links to Lab repositories
This script tests base case of the OnRack BootImage API and OS bootstrap workflows
The test will select a single eligible node to run all currently supported bootstrap workflows
This is a LONG-RUNNING script which will typically take 1-2 hours to execute
'''

import os
import sys
import subprocess
import random

# set path to common libraries
sys.path.append(subprocess.check_output("git rev-parse --show-toplevel", shell=True).rstrip("\n") + "/common")
import fit_common

# This node catalog section will be replaced with fit_common.node_select() when it is checked in
NODECATALOG = fit_common.node_select()

# Select one node at random
NODE = NODECATALOG[random.randint(0, len(NODECATALOG)-1)]

# This routine will download a specific image from mirrors.hwimo.lab.emc.com to appliance
def download_image(reponame):
    status = {'exitcode', 1}
    if reponame == 'ESXi 5.5':
        status = fit_common.remote_shell("cd /tmp;wget " + "http://mirrors.hwimo.lab.emc.com/mirrors/esxi/5.5/" + "esxi5.5.tgz;")
        fit_common.remote_shell("mkdir -p /var/mirrors;"
                                 "mkdir -p /var/mirrors/esxi5.5;"
                                 "cd /var/mirrors/esxi5.5;"
                                 "tar -zxvf /tmp/esxi5.5.tgz;rm /tmp/esxi5.5.tgz;"
                                 "ln -sf /var/mirrors/esxi5.5 /var/renasar/on-http/static/http;"
                                 "ln -sf /var/mirrors/esxi5.5 /var/renasar/on-tftp/static/tftp")
    elif reponame == 'ESXi 6.0':
        status = fit_common.remote_shell("cd /tmp;wget " + "http://mirrors.hwimo.lab.emc.com/mirrors/esxi/6.0/" + "esxi6.0.tgz;")
        fit_common.remote_shell("mkdir -p /var/mirrors;"
                                 "mkdir -p /var/mirrors/esxi6.0;"
                                 "cd /var/mirrors/esxi6.0;"
                                 "tar -zxvf /tmp/esxi6.0.tgz;rm /tmp/esxi6.0.tgz;"
                                 "ln -sf /var/mirrors/esxi6.0 /var/renasar/on-http/static/http;"
                                 "ln -sf /var/mirrors/esxi6.0 /var/renasar/on-tftp/static/tftp")
    elif reponame == 'CentOS 6.5':
        status = fit_common.remote_shell("cd /tmp;wget " + "http://mirrors.hwimo.lab.emc.com/mirrors/centos/6.5/" + "centos65.tgz;")
        fit_common.remote_shell("mkdir -p /var/mirrors;"
                                 "mkdir -p /var/mirrors/centos65;"
                                 "cd /var/mirrors/centos65;"
                                 "tar -zxvf /tmp/centos65.tgz;rm /tmp/centos65.tgz;"
                                 "ln -sf /var/mirrors/centos65 /var/renasar/on-http/static/http;"
                                 "ln -sf /var/mirrors/centos65 /var/renasar/on-tftp/static/tftp")
    elif reponame == 'CentOS 7':
        status = fit_common.remote_shell("cd /tmp;wget " + "http://mirrors.hwimo.lab.emc.com/mirrors/centos/7/" + "centos70.tgz;")
        fit_common.remote_shell("mkdir -p /var/mirrors;"
                                 "mkdir -p /var/mirrors/centos70;"
                                 "cd /var/mirrors/centos70;"
                                 "tar -zxvf /tmp/centos70.tgz;rm /tmp/centos70.tgz;"
                                 "ln -sf /var/mirrors/centos70 /var/renasar/on-http/static/http;"
                                 "ln -sf /var/mirrors/centos70 /var/renasar/on-tftp/static/tftp")
    elif reponame == 'RHEL 7':
        status = fit_common.remote_shell("cd /tmp;wget " + "http://mirrors.hwimo.lab.emc.com/mirrors/rhel/7.0/" + "rhel70.tgz;")
        fit_common.remote_shell("mkdir -p /var/mirrors;"
                                 "mkdir -p /var/mirrors/rhel70;"
                                 "cd /var/mirrors/rhel70;"
                                 "tar -zxvf /tmp/rhel70.tgz;rm /tmp/rhel70.tgz;"
                                 "ln -sf /var/mirrors/rhel70 /var/renasar/on-http/static/http;"
                                 "ln -sf /var/mirrors/rhel70 /var/renasar/on-tftp/static/tftp")
    if fit_common.VERBOSITY >= 2:
        print "Image Download status code:", status['exitcode']
    return status['exitcode']

# this routine polls a task ID for completion
def wait_for_task_complete(taskid, sysid, retries=60):
    for dummy in range(0, retries):
        result = fit_common.rackhdapi(taskid)
        if result['json']['TaskState'] == 'Running' or result['json']['TaskState'] == 'Pending':
            if fit_common.VERBOSITY >= 2:
                print "OS Install workflow state: {}".format(result['json']['TaskState'])
            fit_common.time.sleep(30)
        elif result['json']['TaskState'] == 'Completed':
            if fit_common.VERBOSITY >= 2:
                print "OS Install workflow state: {}".format(result['json']['TaskState'])
            return True
        else:
            break
    print "Task failed with the following state: " + result['json']['TaskState']
    return False


# Get node SKU name
NODENAME = fit_common.rackhdapi('/redfish/v1/Systems/' + NODE)['json']['Name']

# ------------------------ Tests -------------------------------------
from nose.plugins.attrib import attr
@attr(all=False)
class bootstrap_os(fit_common.unittest.TestCase):
    def setUp(self):
        #delete active workflows for specified node
        fit_common.rackhdapi('/api/1.1/nodes/' + NODE + '/workflows/active', action='delete')
    def test_bootstrap_esxi5(self):
        # Creating local repo of ESXi 5.5
        print 'Downloading OS image...'
        self.assertEqual(download_image('ESXi 5.5'), 0, 'Error in image download')
        print 'Running ESXI 5.5 bootstrap...'
        nodehostname = 'esxi55'
        payload_data = {"osName":"ESXi",
                        "version":"5.5",
                        "repo":"http://172.31.128.1:8080/esxi5.5/esxi",
                        "rootPassword": "1234567",
                        "hostname": nodehostname,
                        "domain": "hwimo.lab.emc.com",
                        "dnsServers": ["172.31.128.1"],
                        "users": [{
                                    "name": "onrack",
                                    "password": "Onr@ck1!",
                                    "uid": 1010,
                                }]
                       }
        result = fit_common.rackhdapi('/redfish/v1/Systems/'
                                            + NODE
                                            + '/Actions/RackHD.BootImage',
                                            action='post', payload=payload_data)
        self.assertEqual(result['status'], 201,
                         'Was expecting code 201. Got ' + str(result['status']))
        self.assertEqual(wait_for_task_complete(result['json']['@odata.id'], NODE, retries=80), True,
                         'TaskID ' + result['json']['@odata.id'] + ' not successfully completed.')

    def test_bootstrap_esxi6(self):
        # Creating local repo of ESXi 6.0
        print 'Downloading OS image...'
        self.assertEqual(download_image('ESXi 6.0'), 0, 'Error in image download')
        print 'Running ESXI 6.0 bootstrap...'
        nodehostname = 'esxi60'
        payload_data = {"osName":"ESXi",
                        "version":"6.0",
                        "repo":"http://172.31.128.1:8080/esxi6.0/esxi6",
                        "rootPassword": "1234567",
                        "hostname": nodehostname,
                        "domain": "hwimo.lab.emc.com",
                        "dnsServers": ["172.31.128.1"],
                        "users": [{
                                    "name": "onrack",
                                    "password": "Onr@ck1!",
                                    "uid": 1010,
                                }]
                       }
        result = fit_common.rackhdapi('/redfish/v1/Systems/'
                                            + NODE
                                            + '/Actions/RackHD.BootImage',
                                            action='post', payload=payload_data)
        self.assertEqual(result['status'], 201,
                         'Was expecting code 201. Got ' + str(result['status']))
        self.assertEqual(wait_for_task_complete(result['json']['@odata.id'], NODE, retries=80), True,
                         'TaskID ' + result['json']['@odata.id'] + ' not successfully completed.')

    def test_bootstrap_centos65(self):
        # Creating local repo of CentOS
        print 'Downloading OS image...'
        self.assertEqual(download_image('CentOS 6.5'), 0, 'Error in image download')
        print 'Running CentOS 6.5 bootstrap...'
        nodehostname = 'centos65'
        payload_data = {"osName":"CentOS",
                        "version":"6.5",
                        "repo":"http://172.31.128.1:8080/centos65/os/x86_64",
                        "rootPassword": "1234567",
                        "hostname": nodehostname,
                        "domain": "hwimo.lab.emc.com",
                        "dnsServers": ["172.31.128.1"],
                        "users": [{
                                    "name": "onrack",
                                    "password": "onrack",
                                    "uid": 1010,
                                }]
                       }
        result = fit_common.rackhdapi('/redfish/v1/Systems/'
                                            + NODE
                                            + '/Actions/RackHD.BootImage',
                                            action='post', payload=payload_data)
        self.assertEqual(result['status'], 201,
                         'Was expecting code 201. Got ' + str(result['status']))
        self.assertEqual(wait_for_task_complete(result['json']['@odata.id'], NODE), True,
                         'TaskID ' + result['json']['@odata.id'] + ' not successfully completed.')

    def test_bootstrap_centos7(self):
        # Creating local repo of CentOS
        print 'Downloading OS image...'
        self.assertEqual(download_image('CentOS 7'), 0, 'Error in image download')
        print 'Running CentOS 7 bootstrap...'
        nodehostname = 'centos70'
        payload_data = {"osName":"CentOS",
                        "version":"7",
                        "repo":"http://172.31.128.1:8080/centos70/os/x86_64",
                        "rootPassword": "1234567",
                        "hostname": nodehostname,
                        "domain": "hwimo.lab.emc.com",
                        "dnsServers": ["172.31.128.1"],
                        "users": [{
                                    "name": "onrack",
                                    "password": "onrack",
                                    "uid": 1010,
                                }],

                       }
        result = fit_common.rackhdapi('/redfish/v1/Systems/'
                                            + NODE
                                            + '/Actions/RackHD.BootImage',
                                            action='post', payload=payload_data)
        self.assertEqual(result['status'], 201,
                         'Was expecting code 201. Got ' + str(result['status']))
        self.assertEqual(wait_for_task_complete(result['json']['@odata.id'], NODE), True,
                         'TaskID ' + result['json']['@odata.id'] + ' not successfully completed.')

    def test_bootstrap_centos65_kvm(self):
        # Creating local repo of CentOS
        print 'Downloading OS image...'
        self.assertEqual(download_image('CentOS 6.5'), 0, 'Error in image download')
        print 'Running CentOS 7 KVM bootstrap...'
        nodehostname = 'centos65'
        payload_data = {"osName":"CentOS+KVM",
                        "version":"6.5",
                        "repo":"http://172.31.128.1:8080/centos65/os/x86_64",
                        "rootPassword": "1234567",
                        "hostname": nodehostname,
                        "domain": "hwimo.lab.emc.com",
                        "dnsServers": ["172.31.128.1"],
                        "users": [{
                                    "name": "onrack",
                                    "password": "onrack",
                                    "uid": 1010,
                                }]
                       }
        result = fit_common.rackhdapi('/redfish/v1/Systems/'
                                            + NODE
                                            + '/Actions/RackHD.BootImage',
                                            action='post', payload=payload_data)
        self.assertEqual(result['status'], 201,
                         'Was expecting code 201. Got ' + str(result['status']))
        self.assertEqual(wait_for_task_complete(result['json']['@odata.id'], NODE), True,
                         'TaskID ' + result['json']['@odata.id'] + ' not successfully completed.')

    def test_bootstrap_rhel7_kvm(self):
        # Creating local repo of RHEL
        print 'Downloading OS image...'
        self.assertEqual(download_image('RHEL 7'), 0, 'Error in image download')
        print 'Running RHEL 7 KVM bootstrap...'
        nodehostname = 'rhel70'
        payload_data = {"osName":"RHEL+KVM",
                        "version":"7",
                        "repo":"http://172.31.128.1:8080/rhel70/os/x86_64",
                        "rootPassword": "1234567",
                        "hostname": nodehostname,
                        "domain": "hwimo.lab.emc.com",
                        "dnsServers": ["172.31.128.1"],
                        "users": [{
                                    "name": "onrack",
                                    "password": "onrack",
                                    "uid": 1010,
                                }],

                       }
        result = fit_common.rackhdapi('/redfish/v1/Systems/'
                                            + NODE
                                            + '/Actions/RackHD.BootImage',
                                            action='post', payload=payload_data)
        self.assertEqual(result['status'], 201,
                         'Was expecting code 201. Got ' + str(result['status']))
        self.assertEqual(wait_for_task_complete(result['json']['@odata.id'], NODE), True,
                         'TaskID ' + result['json']['@odata.id'] + ' not successfully completed.')
