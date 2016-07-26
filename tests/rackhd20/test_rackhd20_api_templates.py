'''
Copyright 2016, EMC, Inc.

Author(s):
George Paulos

'''

import os
import sys
import subprocess
sys.path.append(subprocess.check_output("git rev-parse --show-toplevel", shell=True).rstrip("\n") + "/common")
import fit_common

# Select test group here using @attr
from nose.plugins.attrib import attr
@attr(all=True, regression=True, smoke=True)
class rackhd20_api_templates(fit_common.unittest.TestCase):
    def test_api_20_templates_library(self):
        api_data = fit_common.rackhdapi("/api/2.0/templates/library")
        self.assertEqual(api_data['status'], 200, "Was expecting code 200. Got " + str(api_data['status']))
        for item in api_data['json']:
            # check required fields
            for subitem in ['contents', 'createdAt', 'id', 'name', 'updatedAt']:
                if fit_common.VERBOSITY >= 2:
                    print "Checking:", item['name'], subitem
                self.assertGreater(len(item[subitem]), 0, subitem + ' field error')

    def test_api_20_templates_library_ID(self):
        api_data = fit_common.rackhdapi("/api/2.0/templates/library")
        self.assertEqual(api_data['status'], 200, "Was expecting code 200. Got " + str(api_data['status']))
        for item in api_data['json']:
            lib_data = fit_common.rackhdapi("/api/2.0/templates/library/" + item['name'])
            self.assertEqual(lib_data['status'], 200, "Was expecting code 200. Got " + str(lib_data['status']))
            # check required fields
            for subitem in ['contents', 'createdAt', 'id', 'name', 'updatedAt']:
                if fit_common.VERBOSITY >= 2:
                    print "Checking:", item['name'], subitem
                self.assertGreater(len(item[subitem]), 0, subitem + ' field error')

if __name__ == '__main__':
    fit_common.unittest.main()
