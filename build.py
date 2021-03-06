'''
Boxee App Builder
A Python script that builds an application from source and packages it for distribution on any Boxee repo.

written by /rob, 29 March 2011

Requres:
Python 2.4 (executed as python2.4)
python-lxml


Usage:
This script builds your Boxee skin app and packages it appropriately for submission to the Boxee App Library.  You have the option of compiling your Python
modules for distribution in binary form.  

Example:

Build your app!
python build.py -i [yourapp]

Build your app with compiled Python!
python build.py -i [yourapp] -c

Get some usage help!
python build.py --help

Get debug output!
python build.py -i [yourapp] --debug

'''

import sys
import os
import zipfile
import lxml.etree as ET
import logging
import subprocess
import shutil
import getopt

'''
Logging Configuration
'''
logging_level = logging.INFO
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel(logging_level) 
log_formatter = logging.Formatter('%(asctime)s::%(name)s::%(levelname)s::%(message)s')
log_handler.setFormatter(log_formatter)

'''
Info
'''
VERSION = 1.0
__cwd__ = os.getcwd().replace(";","")
class BuildApp:
    def __init__(self, path, compile=False):
        self.path = path
        self.compile = compile
        self.zip_path = "buildapp.zip"
        self.build_dir = os.path.join(__cwd__, "build")
        self.app_dir = os.path.basename(self.path)
        self.log = logging.getLogger("BuildApp")
        self.log.setLevel(logging_level)
        self.log.addHandler(log_handler)
        self.log.debug("Initialized BuildApp.")
        
    def main(self):
        if self.isApp():
            app = self.getApp()
            appid, version = self.prepareDescriptor(app)
            package = self.packageApp(app, appid, version, self.compile)
            shutil.rmtree(app)
            self.log.info("Build located here: %s" % (package))
    
    def isApp(self):
        for root, dirs, files in os.walk(self.path):
            if "descriptor.xml" in files:
                return True
        raise BuildAppException("Could not find descriptor.xml in path: %s" % (self.path), "BuildError")
    
    def getApp(self):
        self.log.info("Copying source to builddir: %s" % self.build_dir)
        tmpdir = os.path.join(self.build_dir, self.path)
        if os.path.exists(tmpdir): shutil.rmtree(tmpdir)
        shutil.copytree(self.path, tmpdir)
        return os.path.join(self.build_dir, os.path.basename(self.path))
    
    def prepareDescriptor(self, path, output = None):
        self.log.info("Preparing descriptor.xml at: %s" % path)
        try:
            doc = ET.parse(os.path.join(path, "descriptor.xml"))
        except Exception, e:
            raise BuildAppException("Could not parse descriptor.xml in %s" % path, e)
        modified = False
        if doc.getroot().findall(".//test-app"):
            for node in doc.getroot().findall(".//test-app"):
                doc.getroot().remove(node)
                modified = True
        appid = doc.getroot().find(".//id").text
        version = doc.getroot().find(".//version").text
        if modified:
            if output:
                self.log.debug("Writing new descriptor at: %s" % output)
                try:
                    doc.write(os.path.join(output, "descriptor.xml"))
                except Exception, e:
                    raise BuildAppException("Could not write to descriptor.xml at: %s" % output, e)
            else:
                self.log.debug("Writing new descriptor at: %s" % path)
                try:
                    doc.write(os.path.join(path, "descriptor.xml"))
                except Exception, e:
                    raise BuildAppException("Could not write to descriptor.xml at: %s" % path, e)
        return appid, version
    
    def packageApp(self, path, appid, version, compile=False):
        self.log.info("Packaging app: %s-%s" % (appid, version))
        self.log.info("Packaging app: %s" % (path))
        if compile:
            self.log.info("Compiling Python modules...")
            compile = subprocess.Popen(["C:\Program Files (x86)\python2.4\python", "-O", "-m", "compileall", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            compile.wait()
        if os.path.exists(os.path.join(self.build_dir, appid)):
            self.log.debug("Temporary build directory matching appid exists: %s, deleting." % (os.path.join(self.build_dir, appid)))
            shutil.rmtree(os.path.join(self.build_dir, appid))
        shutil.copytree(path, os.path.join(self.build_dir, appid))
        zip = zipfile.ZipFile(self.build_dir + "/" + appid + "-" + version + ".zip", "w", zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(self.build_dir + "/" + appid):
            if "git" not in root and "svn" not in root and "CVS" not in root and "tests" not in root:
                for file in files:
                    if "py" in file and "pyo" not in file and compile:
                        pass
                    else:
                        split = root.split(appid)
                        zip.write(os.path.join(root,file), os.path.join(appid, split[1][1:], file))
        zip.close()
        shutil.rmtree(os.path.join(self.build_dir, appid))
        return os.path.join(self.build_dir, appid + "-" + version + ".zip") 

class BuildAppException(Exception):
    def __init__(self, message, e):
        Exception.__init__(self, message)
        self.log = logging.getLogger("Exception")
        self.log.addHandler(log_handler)
        self.logError(message, e)
    
    def logError(self, e, message):
        return self.log.critical("%s! %s" % (str(e), message)) 

def usage():
    print "Boxee App Builder - " + str(VERSION)
    print "Usage: ",sys.argv[0]," [-i /path/to/app] [-c] [-h] [-d]"
    print "-i (--input): Required.  Path to the Boxee app you wish to build."
    print "-c (--compile): Optional. Compiles all Python modules into .pyo files."
    print "-d (--debug): Optional. Turns on debug output."
    print "-h (--help): Optional.  Displays this message."

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:cd", ["help", "input=", "compile", "debug"] )
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    input = None
    compile = False
        
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-d", "--debug"):
            logging.DEBUG
        elif opt in ("-i", "--input"):
            input = arg
        elif opt in ("-c", "--compile"):
            compile = True
        else:
            assert False, "Unrecognized command line flag."
    
    if input:
        if os.path.exists(input):
            if input[-1] == "/" or input[-1] == "/":
                input = input[:-1]
            build = BuildApp(input, compile)
            build.main()
        else:
            assert False, "Input directory %s does not exist!" % (input)
    else:
        assert False, "Did not provide input directory."