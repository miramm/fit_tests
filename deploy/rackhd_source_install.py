'''
Copyright 2016, EMC, Inc.

Author(s):
George Paulos

This script installs RackHD from GitHub source onto blank OS.
'''

import os
import sys
import subprocess
# set path to common libraries
sys.path.append(subprocess.check_output("git rev-parse --show-toplevel", shell=True).rstrip("\n") + "/common")
import fit_common

# local methods
ENVVARS = ''
if 'proxy' in fit_common.GLOBAL_CONFIG['repos'] and fit_common.GLOBAL_CONFIG['repos']['proxy'] != '':
    ENVVARS = "export http_proxy=" + fit_common.GLOBAL_CONFIG['repos']['proxy'] + ";" + \
              "export https_proxy=" + fit_common.GLOBAL_CONFIG['repos']['proxy'] + ";"

class rackhd_source_install(fit_common.unittest.TestCase):
    def test01_install_rackhd_dependencies(self):
        print "**** Installing RackHD dependencies."
        # update sudoers to preserve proxy environment
        sudoersproxy = open("sudoersproxy", 'w')
        sudoersproxy.write('Defaults env_keep="HOME no_proxy http_proxy https_proxy"\n')
        sudoersproxy.close()
        fit_common.scp_file_to_ora("sudoersproxy")
        self.assertEqual(fit_common.remote_shell('cp sudoersproxy /etc/sudoers.d/'
                                                  )['exitcode'], 0, "sudoersproxy config failure.")
        os.remove('sudoersproxy')
        # install git
        self.assertEqual(fit_common.remote_shell("apt-get -y install git")['exitcode'], 0, "Git install failure.")
        self.assertEqual(fit_common.remote_shell("apt-get -y update")['exitcode'], 0, "update failure.")
        self.assertEqual(fit_common.remote_shell("apt-get -y dist-upgrade")['exitcode'], 0, "upgrade failure.")
        self.assertEqual(fit_common.remote_shell("git config --global http.proxy " + fit_common.GLOBAL_CONFIG['repos']['proxy']
                                                  )['exitcode'], 0, "Git proxy config failure.")
    def test02_install_network_config(self):
        print "**** Installing RackHD network config."
        # install network config
        self.assertEqual(fit_common.remote_shell("echo 'auto eth1' > /etc/network/interfaces.d/control.cfg;"
                                                  "echo 'iface eth1 inet static' >> /etc/network/interfaces.d/control.cfg;"
                                                  "echo 'address 172.31.128.1' >> /etc/network/interfaces.d/control.cfg;"
                                                  "echo 'netmask 255.255.252.0' >> /etc/network/interfaces.d/control.cfg"
                                                  )['exitcode'], 0, "Network config failure.")
        self.assertEqual(fit_common.remote_shell("echo 'auto eth2' > /etc/network/interfaces.d/pdudirect.cfg;"
                                                  "echo 'iface eth2 inet static' >> /etc/network/interfaces.d/pdudirect.cfg;"
                                                  "echo 'address 192.168.1.1' >> /etc/network/interfaces.d/pdudirect.cfg;"
                                                  "echo 'netmask 255.255.255.0' >> /etc/network/interfaces.d/pdudirect.cfg"
                                                  )['exitcode'], 0, "Network config failure.")

    def test03_install_node(self):
        print "**** Installing NodeJS 4"
        # install Node
        fit_common.remote_shell('apt-get -y remove nodejs nodejs-legacy')
        fit_common.remote_shell(ENVVARS +
                                'wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -;'
                                'echo "deb https://deb.nodesource.com/node_4.x trusty main" | tee /etc/apt/sources.list.d/nodesource.list;'
                                'echo "deb-src https://deb.nodesource.com/node_4.x trusty main" | tee -a /etc/apt/sources.list.d/nodesource.list;')
        fit_common.remote_shell('apt-get -y update;'
                                'apt-get -y install nodejs;'
                                )
        fit_common.remote_shell('apt-get -y install npm;npm config set https-proxy '
                                + fit_common.GLOBAL_CONFIG['repos']['proxy'])

    def test04_clone_rackhd_source(self):
        print "**** Cloning RackHD source."
        modules = [
            "on-core",
            "on-dhcp-proxy",
            "on-http",
            "on-statsd",
            "on-syslog",
            "on-taskgraph",
            "on-tasks",
            "on-tftp",
            "on-tools"
        ]
        # clone base repo
        fit_common.remote_shell('rm -rf ~/rackhd')
        self.assertEqual(fit_common.remote_shell(ENVVARS + "git clone "
                                                + fit_common.GLOBAL_CONFIG['repos']['install']['rackhd']
                                                + "/rackhd ~/rackhd"
                                                )['exitcode'], 0, "RackHD git clone failure.")
        # clone modules
        for repo in modules:
            self.assertEqual(fit_common.remote_shell(ENVVARS
                                                    + "rm -rf ~rackhd/" + repo + ";"
                                                    + "git clone "
                                                    + fit_common.GLOBAL_CONFIG['repos']['install']['rackhd']
                                                    + "/" + repo + " ~/rackhd/" + repo
                                                     )['exitcode'], 0, "RackHD git clone module failure:" + repo)

    def test05_run_ansible_installer(self):
        print "**** Run RackHD Ansible installer."
        # install Ansible
        self.assertEqual(fit_common.remote_shell(ENVVARS + "cd ~;apt-get -y install ansible")['exitcode'], 0, "Install failure.")
        # run Ansible RackHD installer
        self.assertEqual(fit_common.remote_shell(ENVVARS +
                                                 "cd ~/rackhd/packer/ansible/;"
                                                 "ansible-playbook -i 'local,' -c local rackhd_package.yml",
                                                 timeout=600,
                                                 )['exitcode'], 0, "Install failure.")

    def test06_install_rackhd_config_files(self):
        print "**** Installing RackHD config files."
        #create DHCP config
        dhcp_conf = open('dhcpd.conf', 'w')
        dhcp_conf.write(
                        'ddns-update-style none;\n'
                        'option domain-name "example.org";\n'
                        'option domain-name-servers ns1.example.org, ns2.example.org;\n'
                        'default-lease-time 600;\n'
                        'max-lease-time 7200;\n'
                        'log-facility local7;\n'
                        'deny duplicates;\n'
                        'ignore-client-uids true;\n'
                        'subnet 172.31.128.0 netmask 255.255.252.0 {\n'
                        '  range 172.31.128.2 172.31.131.254;\n'
                        '  option vendor-class-identifier "PXEClient";\n'
                        '}\n'
                         )
        dhcp_conf.close()
        # create RackHD config
        hdconfig = {
                    "CIDRNet": "172.31.128.0/22",
                    "amqp": "amqp://localhost",
                    "apiServerAddress": "172.31.128.1",
                    "apiServerPort": 9080,
                    "broadcastaddr": "172.31.131.255",
                    "dhcpGateway": "172.31.128.1",
                    "dhcpProxyBindAddress": "172.31.128.1",
                    "dhcpProxyBindPort": 4011,
                    "dhcpSubnetMask": "255.255.252.0",
                    "gatewayaddr": "172.31.128.1",
                    "httpEndpoints": [
                        {
                            "address": "0.0.0.0",
                            "port": fit_common.GLOBAL_CONFIG['ports']['http'],
                            "httpsEnabled": False,
                            "proxiesEnabled": True,
                            "authEnabled": False,
                            "routers": "northbound-api-router"
                        },
                        {
                            "address": "0.0.0.0",
                            "port": fit_common.GLOBAL_CONFIG['ports']['https'],
                            "httpsEnabled": True,
                            "proxiesEnabled": True,
                            "authEnabled": True,
                            "routers": "northbound-api-router"
                        },
                        {
                            "address": "172.31.128.1",
                            "port": 9080,
                            "httpsEnabled": False,
                            "proxiesEnabled": True,
                            "authEnabled": False,
                            "routers": "southbound-api-router"
                        }
                    ],
                    "httpDocsRoot": "./build/apidoc",
                    "httpFileServiceRoot": "./static/files",
                    "httpFileServiceType": "FileSystem",
                    "httpProxies": [{
                        "localPath": "/mirror",
                        "remotePath": "/",
                        "server": fit_common.GLOBAL_CONFIG['repos']['mirror']
                    }],
                    "httpStaticRoot": "/opt/monorail/static/http",
                    "minLogLevel": 3,
                    "authUsername": "admin",
                    "authPasswordHash": "KcBN9YobNV0wdux8h0fKNqi4uoKCgGl/j8c6YGlG7iA0PB3P9ojbmANGhDlcSBE0iOTIsYsGbtSsbqP4wvsVcw==",
                    "authPasswordSalt": "zlxkgxjvcFwm0M8sWaGojh25qNYO8tuNWUMN4xKPH93PidwkCAvaX2JItLA3p7BSCWIzkw4GwWuezoMvKf3UXg==",
                    "authTokenSecret": "RackHDRocks!",
                    "authTokenExpireIn": 86400,
                    "mongo": "mongodb://localhost/pxe",
                    "sharedKey": "qxfO2D3tIJsZACu7UA6Fbw0avowo8r79ALzn+WeuC8M=",
                    "statsd": "127.0.0.1:8125",
                    "subnetmask": "255.255.252.0",
                    "syslogBindAddress": "172.31.128.1",
                    "syslogBindPort": 514,
                    "tftpBindAddress": "172.31.128.1",
                    "tftpBindPort": 69,
                    "tftpRoot": "./static/tftp",
                }
        config_json = open('config.json', 'w')
        config_json.write(fit_common.json.dumps(hdconfig, sort_keys=True, indent=4))
        config_json.close()
        # AMQP config files
        rabbitmq_config = open('rabbitmq.config', 'w')
        rabbitmq_config.write('[{rabbit, [{tcp_listeners, [5672]}]}].' )
        rabbitmq_config.close()
        # copy files to ORA
        fit_common.scp_file_to_ora('config.json')
        fit_common.scp_file_to_ora('dhcpd.conf')
        fit_common.scp_file_to_ora('rabbitmq.config')
        self.assertEqual(fit_common.remote_shell('cp dhcpd.conf /etc/dhcp/')['exitcode'], 0, "DHCP Config failure.")
        self.assertEqual(fit_common.remote_shell('cp config.json /opt/monorail/')['exitcode'], 0, "RackHD Config file failure.")
        self.assertEqual(fit_common.remote_shell('cp rabbitmq.config /etc/rabbitmq/')['exitcode'], 0, "AMQP Config file failure.")
        os.remove('dhcpd.conf')
        os.remove('config.json')
        os.remove('rabbitmq.config')

    def test07_reboot_and_check(self):
        print "**** Reboot and check installation."
        # create startup files
        self.assertEqual(fit_common.remote_shell(
            "touch /etc/default/on-dhcp-proxy /etc/default/on-http /etc/default/on-tftp /etc/default/on-syslog /etc/default/on-taskgraph"
            )['exitcode'], 0, "Install failure.")
        # reboot
        self.assertEqual(fit_common.remote_shell("reboot")['exitcode'], 0, 'ORA reboot registered error')
        print "**** Rebooting appliance..."
        fit_common.countdown(30)
        print "**** Waiting for login..."
        shell_data = 0
        for dummy in range(0, 30):
            shell_data = fit_common.remote_shell("pwd")
            if shell_data['exitcode'] == 0:
                break
            else:
                fit_common.time.sleep(5)
        self.assertEqual(shell_data['exitcode'], 0, "Shell test failed after appliance reboot")
        fit_common.time.sleep(10)
        self.assertEqual(fit_common.rackhdapi("/api/2.0/config")['status'], 200, "Unable to contact RackHD.")

if __name__ == '__main__':
    fit_common.unittest.main()