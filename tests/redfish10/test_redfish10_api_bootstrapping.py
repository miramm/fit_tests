'''
Copyright 2016, EMC, Inc.
Author(s):
Marcos Mirambeaux
'''

import os
import sys
import subprocess
sys.path.append(subprocess.check_output("git rev-parse --show-toplevel", shell=True).rstrip("\n") + "/common")
import fit_common
import time
import random

class redfish10_api_bootstrapping(fit_common.unittest.TestCase):
    def setUp(self):
        print "Remote Bootstrap ESXi 6.0 test "  # test name here

    def tearDown(self):
        print "Test finished" # fit_common.testcase_complete(self)

    def download_image(self,reponame):
        status = {'exitcode', 1}
        if reponame == 'ESXi 6.0':
            status = fit_common.remote_shell(
                "cd /tmp;wget http://mirrors.hwimo.lab.emc.com/mirrors/esxi/6.0/esxi6.0.tgz;")
            fit_common.remote_shell("mkdir -p /var/mirrors;"
                                     "mkdir -p /var/mirrors/esxi6.0;"
                                     "cd /var/mirrors/esxi6.0;"
                                     "tar -zxvf /tmp/esxi6.0.tgz;rm /tmp/esxi6.0.tgz;"
                                     "ln -sf /var/mirrors/esxi6.0 /var/renasar/on-http/static/http;"
                                     "ln -sf /var/mirrors/esxi6.0 /var/renasar/on-tftp/static/tftp")
        if fit_common.VERBOSITY >= 2:
            print "Image Download status code:", status['exitcode']
        return status['exitcode']

    # this routine polls a task ID for completion
    def wait_for_task_complete(self,taskid, sysid, retries=30):
        for dummy in range(0, retries):
            result = fit_common.rackhdapi(taskid)
            if result['json']['TaskState'] == 'Running':
                fit_common.time.sleep(30)
            elif result['json']['TaskState'] == 'Completed':
                return True
            else:
                break
        # delete node active workflows if failed or timed out
                fit_common.rackhdapi('/api/current/nodes/' + sysid + '/workflows/active', action='delete')
        return False

    # ping test to check for node ping test
    def ping_test(self,addr):
        for dummy in range(0, 35):
            if fit_common.remote_shell('ping -c 1 -w 5 ' + addr)['exitcode'] == 0:
                return True
                time.sleep(30)
        return False


    # this is our main testing
    def test_redfish_v1_bootstrapping(self):
        # Creating local repo of ESXi 6.0
        # This node catalog section will be replaced with test_common.node_select() when it is checked in
        #NODECATALOG = fit_common.node_select()
        # Select one node at random
        #NODE = NODECATALOG[random.randint(0, len(NODECATALOG) - 1)]
        NODE= "57a042a91484c6e5098618bf"
        print 'Downloading OS image...'
        self.assertEqual(self.download_image('ESXi 6.0'), 0, 'Error in image download')
        print 'Running OS bootstrap...'
        nodehostname = 'Rinjin12'
        # create ssh key
        publickey = fit_common.remote_shell(
            "rm keyfile; ssh-keygen -t rsa -f keyfile -N \\\'\\\' -q ; cat keyfile.pub")['stdout']
        payload_data = {"version": "6.0",
                        "osName": "ESXi",
                        "repo": "http://172.31.128.1:9080/esxi6.0/esxi6",
                        "rootPassword": "1234567",
                        "rootSshKey": publickey,
                        "hostname": nodehostname,
                        "domain": "emc.com",
                        "dnsServers": ["10.253.130.61", "10.146.130.61"],
                        "users": [
                            {"name": "root", "password": "Onrack&1234", "uid": 1010, "sshKey": publickey}],
                        "networkDevices": [
                            {"device": "vmnic2",
                             "ipv4": {
                                 "ipAddr": "10.241.197.25",
                                 "gateway": "10.241.197.1",
                                 "netmask": "255.255.255.0"
                             }
                             }
                        ]
                        }

        '''if drive_Id != None:
            payload_data["installDisk"] = drive_Id'''

        result = fit_common.rackhdapi('/redfish/v1/Systems/'
                                            + NODE
                                            + '/Actions/RackHD.BootImage',
                                            action='post', payload=payload_data)
        print result
        self.assertEqual(result['status'], 201,
                         "Was expecting code 201. Got " + str(result['status'] )+ str(result['json']))

        self.assertEqual(self.wait_for_task_complete(result['json']['@odata.id'], NODE), True,
                         'TaskID' + result['json']['@odata.id'] + ' not successfully completed.')
        '''check = fit_common.remote_shell("cat /var/log/onrack-conductor-event.log "
                                         "| grep Graph.InstallEsx | grep CANCELLED "
                                         "| grep " + NODE)
        check = fit_common.remote_shell("cat /var/log/onrack-conductor-event.log "
                                        "| grep Graph.InstallEsx | grep FAILED "
                                        "| grep " + NODE)'''
        check = fit_common.remote_shell("cat /var/log/onrack-conductor-event.log "
                                        "| grep Graph.InstallEsx | grep SUCCEEDED "
                                        "| grep " + NODE)
        self.assertEqual(self.ping_test("10.241.197.25"), True, 'ESXi 6.0 ping test failed')
        self.assertEqual(check['exitcode'], 0, 'Error in Conductor log.')

