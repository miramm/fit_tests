## Test config files:

    All test config files must reside in the config directory.
    There are two required files global_config.json and stack_config.json.

## Global config file:

    The global config file specifies operating parameters and test environment.
    '''
    {
      "credentials": { # section for all usernames and passwords
        "hyper": [ # appliance hypervisor credentials, may be multiple, first is default
          {
            "username": "root",
            "password": "1234567"
          }
        ],
        "ora": [ # appliance admin credentials, may be multiple, first is default
          {
            "username": "onrack",
            "password": "onrack"
          }
        ],
        "bmc": [ # node or appliance bmc credentials, may be multiple, first is default
          {
            "username": "admin",
            "password": "admin"
          },
          {
            "username": "root",
            "password": "1234567"
          }
        ],
        "node": [ # node OS login credentials, may be multiple, first is default
          {
            "username": "root",
            "password": "1234567"
          },
          {
            "username": "onrack",
            "password": "onrack"
          }
        ],
        "switch": [ # switch login credentials, may be multiple, first is default
          {
            "username": "admin",
            "password": "1234567"
          }
        ],
        "pdu": [ # PDU login credentials, may be multiple, first is default
          {
            "username": "admn",
            "password": "admn"
          }
        ]
      },
    "snmp":{ # SNMP config data
        "community": "onrack"
    },
      "repos": { # list of all OS and package repositories
        "_comment": "This is the list of repositories for each category",
        "proxy": "http://web.hwimo.lab.emc.com:3128",
        "mirror": "http://mirrors.hwimo.lab.emc.com/mirrors",
        "os": { # all OS install repos
          "esxi55": "http://mirrors.hwimo.lab.emc.com/mirrors/esxi/5.5/",
          "esxi60": "http://mirrors.hwimo.lab.emc.com/mirrors/esxi/6.0/",
          "centos60": "http://mirrors.hwimo.lab.emc.com/mirrors/centos/6.5/",
          "centos70": "http://mirrors.hwimo.lab.emc.com/mirrors/centos/7/",
          "rhel70": "http://mirrors.hwimo.lab.emc.com/mirrors/rhel/7.0/"
        },
        "install": { # RackHD and OnRack installation repos
          "template": "http://mirrors.hwimo.lab.emc.com/mirrors/ova/ubunutu16.ova", # OVA template
          "onrackova": "http://mirrors.hwimo.lab.emc.com/mirrors/ova/onrack.ova", # OnRack OVA install
          "onrack": "http://onrack.hwimo.lab.emc.com/get/", # OnRack package install mirror
          "rackhd": "https://github.com/rackhd/" # RackHD Git repo
          },
        "skupack": [ # SKU pack repositories, may be multiple
          "https://github.com/RackHD/on-skupack"
          ],
        "firmware": { # all firmware repos
          "quanta-t41": {
            "bios": "",
            "bmc": "",
            "raid": "",
            "config": ""
          },
          "quanta-d51": {
            "bios": "",
            "bmc": "",
            "raid": "",
            "config": ""
          }
        }
      },
      "ports": { # default access ports
        "_comment": "These are the northbound rest API port assignments",
        "http": 8080,
        "https": 8443
      }
    }
    '''
## Stack config:

    The stack config file specifies addresses and environment for the specific hardware under test.
    A stack config file is required for running deployment scripts.
    The stack config file is organized by stack label, which can be any alphanumeric key value.
    The stack key is used to identify the hardware to be used with test scripts using the '-stack' argument.

    Sample stack configuration file:
    '''
    {
    "stack1":{                           #stack label, can be any number of stacks defined
        "bmc": "stack1.bmc.lab",         #appliance bmc address (required)
        "control": "stack1.control.lab", #control switch admin address (optional)
        "data": "stack1.data.lab",       #data switch admin address (optional)
        "hyper": "stack1.esxi.lab",      #esxi hypervisor admin address (required only for esxi)
        "ora": "stack1.host.lab",        #appliance OVA admin address (required)
        "ovamac": "00:50:56:00:11:00",   #appliance OVA MAC address (required only for esxi)
        "pdu": "192.168.1.5",            #PDU admin address (optional)
        "type": "esxi"                   #deployment type: esxi, docker, linux (required)
    }
    '''

# Stack config override files:

    Any stack config can be modified via a 'detail' file by loading it into the config dir.
    A detail file can have any name but must have a .json extension.
    The detail file will look like the sample above but may have additional elements.
    Only the stack data in the specified keys will be overwritten.
    The detail file must have all of the required fields because it will overwrite all initial values.
