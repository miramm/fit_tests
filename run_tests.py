#!/usr/bin/python

'''
Copyright 2016, EMC, Inc

Author(s):
George Paulos

This Script runs nose tests with command-line arguments.

usage: run_tests.py [-h] [-test TEST] [-group GROUP] [-stack STACK] [-ora ORA]
                    [-version VERSION] [-xunit] [-list] [-sku SKU]
                    [-source SOURCE] [-branch BRANCH]
                    [-obmmac OBMMAC | -nodeid NODEID] [-overlay OVERLAY]
                    [-v V]

Command Help

optional arguments:
  -h, --help        show this help message and exit
  -test TEST        test to execute, default: tests/
  -group GROUP      test group to execute: 'smoke', 'regression',
                    'extended', default: all
  -stack STACK      stack number, overrides -ip and -bmc
  -ora ORA          OnRack/RackHD appliance IP address or hostname
  -version VERSION  OnRack version, example:onrack-release-0.3.0, default:
                    onrack-devel
  -xunit            generates xUnit XML report files
  -list             generates test list only
  -sku SKU          node SKU, example:Phoenix, default=all
  -source SOURCE    RackHD source repo
  -obmmac OBMMAC    node OBM MAC address, example:00:1e:67:b1:d5:64,
                    default=all
  -nodeid NODEID    node identifier string of a discovered node, example:
                    56ddcf9a8eff16614e79ec74
  -overlay OVERLAY  set to overlay (delete/add) just after OnRack install
  -v V              Verbosity level of console output, default=0, Built Ins:
                    0: No debug, 2: User script output, 4: rest calls and
                    status info, 6: other common calls (ipmi, ssh), 9: all the
                    rest

To run the full test suite against a specified OnRack/RackHD appliance at IP 192.168.1.1:

./run_test.py -ora 192.168.1.1 -test tests/

'''

import os
import sys
import subprocess
import argparse
# set path to common libraries
sys.path.append(subprocess.check_output("git rev-parse --show-toplevel", shell=True).rstrip("\n") + "/common")
import fit_common


# command line argument parser returns CMD_ARGS dict
ARG_PARSER = argparse.ArgumentParser(description="Command Help")
ARG_PARSER.add_argument("-test", default="tests/",
                        help="test to execute, default: tests/")
ARG_PARSER.add_argument("-group", default="all",
                        help="test group to execute: 'smoke_test', 'regression', 'extended', default: 'all'")
ARG_PARSER.add_argument("-stack", default="None",
                        help="stack number, overrides -ip and -bmc")
ARG_PARSER.add_argument("-ora", default="localhost",
                        help="OnRack/RackHD appliance IP address or hostname, default: localhost")
ARG_PARSER.add_argument("-version", default="onrack-devel",
                        help="OnRack version, example:onrack-release-0.3.0, default: onrack-devel")
ARG_PARSER.add_argument("-xunit", default="False", action="store_true",
                        help="generates xUnit XML report files")
ARG_PARSER.add_argument("-list", default="False", action="store_true",
                        help="generates test list only")
ARG_PARSER.add_argument("-sku", default="all",
                        help="node SKU, example:Phoenix, default=all")
GROUP = ARG_PARSER.add_mutually_exclusive_group(required=False)
GROUP.add_argument("-obmmac", default="all",
                        help="node OBM MAC address, example:00:1e:67:b1:d5:64, default=all")
GROUP.add_argument("-nodeid", default="None",
                     help="node identifier string of a discovered node, example: 56ddcf9a8eff16614e79ec74")
ARG_PARSER.add_argument("-v", default=1, type=int,
                        help="Verbosity level of console output, default=0, Built Ins: " +
                             "0: No debug, " +
                             "2: User script output, " +
                             "4: rest calls and status info, " +
                             "6: other common calls (ipmi, ssh), " +
                             "9: all the rest ")

# parse arguments to CMD_ARGS dict
CMD_ARGS = vars(ARG_PARSER.parse_args())
# transfer argparse args to ARGS_LIST
for keys in CMD_ARGS:
    fit_common.ARGS_LIST[keys] = CMD_ARGS[keys]

# Run tests
EXITCODE = fit_common.run_nose(CMD_ARGS['test'])

exit(EXITCODE)

