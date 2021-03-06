#!/usr/bin/python

import json
import os
import subprocess
import sys
import urllib


url_base = "http://admin.ci.centos.org:8080"
api_key = open("/home/atomic-sig/duffy.key").read().strip()
count = os.environ['MACHINE_COUNT']
ver = "7"
arch = "x86_64"
req_url = "%s/Node/get?key=%s&ver=%s&arch=%s&count=%s" \
    % (url_base, api_key, ver, arch, count)

ansible_repo_url = os.environ['ANSIBLE_REPO_URL']

test_cmd = "export ghprbActualCommit=%s && " % os.environ["ghprbActualCommit"]
test_cmd += "export ghprbPullId=%s && " % os.environ["ghprbPullId"]
test_cmd += os.environ['TEST_CMD']

try:
    jsondata = urllib.urlopen(req_url).read()
except Exception as e:
    print e.message()
    sys.exit(1)

data = json.loads(jsondata)

for host in data['hosts']:
    host = data['hosts'][0]

    ssh_cmd = ("ssh -t -t "
               "-o UserKnownHostsFile=/dev/null "
               "-o StrictHostKeyChecking=no "
               "root@%s " % (host))

    remote_cmd = ("yum -y -q install git && "
                  "git clone %s && "
                  "cd adb-ci-ansible && ./install-ansible.sh && "
                  "ansible-playbook install-adb.yml --extra-vars "
                  "'adb_tests=true clone_adb_repo=true'") % \
        ansible_repo_url

    # This `cmd` does all the installation and setup
    cmd = '%s "%s"' % (ssh_cmd, remote_cmd)

    print("Running cmd: {}".format(cmd))
    exit_code = subprocess.call(cmd, shell=True)

    # This `cmd` does all the tests
    cmd = '%s "%s"' % (ssh_cmd, test_cmd)

    print("Running cmd: {}".format(cmd))
    exit_code = subprocess.call(cmd, shell=True)

    done_nodes_url = "%s/Node/done?key=%s&ssid=%s" % (url_base, api_key,
                                                      data['ssid'])
    print urllib.urlopen(done_nodes_url).read()
sys.exit(exit_code)
