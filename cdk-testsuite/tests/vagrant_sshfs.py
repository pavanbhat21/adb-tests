#!/usr/bin/python

from avocado import Test
#from avocado import main
from avocado.utils import process
import os, re, vagrant

class VagrantSshfs(Test):
    def setUp(self):
        self.vagrant_VAGRANTFILE_DIR = self.params.get('vagrant_VAGRANTFILE_DIR')
        self.vagrant_PROVIDER = self.params.get('vagrant_PROVIDER', default='')
        self.vagrant_RHN_USERNAME = self.params.get('vagrant_RHN_USERNAME')
        self.vagrant_RHN_PASSWORD = self.params.get('vagrant_RHN_PASSWORD')
        self.v = vagrant.Vagrant(self.vagrant_VAGRANTFILE_DIR)
	#self.platform = os.system("uname | grep -i cygwin >/dev/null 2>&1")
        #if not self.platform:
	if os.name == "nt":
	    self.mountpoint = os.getenv("USERPROFILE")
	    self.mountpoint_vm = '/' + self.mountpoint[:1].lower() + self.mountpoint[2:].replace("\\", "/")
	    self.mountpoint_host = "/cygdrive" + self.mountpoint_vm
        elif os.name == "posix":
            self.mountpoint = self.mountpoint_host = self.mountpoint_vm = os.getenv("HOME")
	self.dummy_file1_vm = os.path.join(self.mountpoint_vm, "dummy_file1.txt")
	self.dummy_file2_vm = os.path.join(self.mountpoint_vm, "dummy_file2.txt")
	self.dummy_file3_vm = os.path.join(self.mountpoint_vm, "dummy_file3.txt")
	self.dummy_file1_host = os.path.join(self.mountpoint_host, "dummy_file1.txt")
	self.dummy_file2_host = os.path.join(self.mountpoint_host, "dummy_file2.txt")
	self.dummy_file3_host = os.path.join(self.mountpoint_host, "dummy_file3.txt")
	self.dummy_contents1 = "Dumping dummy contents into file"
	self.dummy_contents2 = "This is a dummy file"	
        self.v = vagrant.Vagrant(self.vagrant_VAGRANTFILE_DIR)
	os.chdir(self.vagrant_VAGRANTFILE_DIR)

    
    def vagrant_up_with_subscription(self):
	self.log.info("Bringing up the vagrant box...")
        self.v.destroy()
        os.environ["SUB_USERNAME"] = self.vagrant_RHN_USERNAME
        os.environ["SUB_PASSWORD"] = self.vagrant_RHN_PASSWORD
        self.log.info("Brining up the vagrant box and registering to RHN...")
        self.v.up()
	out = self.v.status()
        state = re.search(r"state='(.*)',", str(out) ).group(1)
        self.assertEqual("running", state, "The vagrant box is not up")

    def remove_vm(self):
	self.log.info("Destroying the vagrant box...")
	os.chdir(self.vagrant_VAGRANTFILE_DIR)
        self.v.destroy()


    def test_check_mount(self):
	#self.vagrant_up_with_subscription()
	self.log.info("Checking if the user home dir is mounted fine inside the VM...")
	self.log.info("Checking the user home dir...")
	self.assertTrue(os.path.isdir(self.mountpoint_host))
	self.log.info("Checking the mount point in the CDK box...")	
	cmd = "vagrant ssh -c 'ls -d %s'" %(self.mountpoint_vm)
	out = process.run(cmd, shell=True)
        self.assertEqual(self.mountpoint_vm, out.stdout.strip("\r\n"), "User home dir is not mounted inside the VM")


    def test_create_file(self):
	self.log.info("Creating a file under user home dir...")
	try:
            open(self.dummy_file1_host, 'a').write(self.dummy_contents1)
        except Exception as e:
            self.log.error("Error while creating file")
            raise e
        cmd = "vagrant ssh -c 'cat %s'" %(self.dummy_file1_vm)
        out = process.run(cmd, shell=True)
	self.assertEqual(self.dummy_contents1, out.stdout.strip("\r\n"), "File contents do not match")

    def test_create_file_inside_vm(self):	
	self.log.info("Creating a file under mount point inside the VM...")
	try:
    	    cmd = "vagrant ssh -c 'touch %s'" %(self.dummy_file2_vm)
	    out = process.run(cmd, shell=True)
	    cmd = "vagrant ssh -c 'echo \"%s\" > %s'" %(self.dummy_contents2, self.dummy_file3_vm)
	    out = process.run(cmd, shell=True)
	    with open(self.dummy_file3_host, 'r') as myfile:
	        data = myfile.read()
	    self.assertEqual(data.strip("\n"), self.dummy_contents2, "File contents do not match")	
	except Exception as e:
	    self.log.error("Error creating files")
	    raise e
    
    def test_modify_files(self):
	self.log.info("Editing the created files...")
	try:
            open(self.dummy_file3_host, 'a').write(self.dummy_contents1)
	    cmd = "vagrant ssh -c 'echo \"%s\" >> %s'" %(self.dummy_contents2, self.dummy_file1_vm)
            out = process.run(cmd, shell=True)
 	    with open(self.dummy_file1_host, 'r') as myfile:
                data = myfile.read()
            self.assertEqual(data.strip("\n"), self.dummy_contents1 + self.dummy_contents2, "File contents do not match")
            with open(self.dummy_file3_host, 'r') as myfile:
                data = myfile.read()
            self.assertEqual(data.strip("\n"), self.dummy_contents2 + '\n' + self.dummy_contents1, "File contents do not match")
        except Exception as e:
            self.log.error("Error while modifying files")
            raise e

	

    def test_delete_files(self):
	self.log.info("Deleting the files already created...")
	try:
	    cmd = "vagrant ssh -c 'rm -f %s %s'" %(self.dummy_file1_vm, self.dummy_file2_vm)
	    out = process.run(cmd, shell=True)
	    os.remove(self.dummy_file3_host)
	except Exception as e:
	    self.log.error("Error while removing file...")
	    raise e
	#self.remove_vm()
	
    def tearDown(self):
	print "End of test.........."

