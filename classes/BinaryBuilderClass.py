#KEECO HW Node - Binary and SPIFFS builder class
#Use the fullBuildProcess() function to build application and SPIFFS files

import json
from os.path import isfile, isdir, join, dirname, realpath, split
import shutil
import errno
from os import listdir, mkdir, system, name

class BinaryBuilder():
    def __init__(self):
        self.OS_type = ""
        self.required_libs = list()

        with open('settings.json') as json_file:
            self.settings_data = json.load(json_file)
        self.template_path, self.template_lastfolder = split(self.settings_data['templateFolderPath'])
        self.fullResultFolderPath = join(self.settings_data['resultFolderPath'],self.template_lastfolder)
        print("___BinaryBuilder working directories are set")

    def fullBuildProcess(self):
        self.buildBinary()
        self.buildSPIFFS()

    def buildBinary(self):
        system("cd " + self.fullResultFolderPath + "&" + "dir")
        cmd_string = "arduino-cli.exe compile --fqbn esp8266:esp8266:d1_mini " + self.fullResultFolderPath + " --build-path " + self.settings_data['buildFolderPath']
        print(cmd_string)
        res = system(cmd_string)
        if (res == 0):
            print("CODE BUILD SUCCESSFULLY FINISHED! You can deploy your binary now!")
        else:
            print("Code Build was not successful! Error code: " + str(res) + " For details see the console above...")

    def buildSPIFFS(self):
        fullDataFolderPath = join(self.settings_data['templateFolderPath'],"data")
        fullDataResultPath = join(self.settings_data['buildFolderPath'], "out.spiffs")
        cmd_string = "mkspiffs -c " + fullDataFolderPath + " -s 1048576 " + fullDataResultPath
        print(cmd_string)
        res = system(cmd_string)
        if (res == 0):
            print("2M SPIFFS BUILD SUCCESSFULLY FINISHED! You can deploy your binary now!")
        else:
            print("SPIFFS Build was not successful! Error code: " + str(res) + " For details see the console above...")

    def installDependencies(self):
        installed_libs = list()
        to_be_installed_libs = list()

        output = subprocess.check_output("arduino-cli.exe lib list --format json", shell=True).decode()
        obj = json.loads(output)

        with open('temp_plugins.json') as temp_plugin_file:
                PluginList = json.load(temp_plugin_file)

        for plugin in PluginList:
            for lib in plugin['Dependencies']:
                self.required_libs.append(lib)
        self.required_libs = list(dict.fromkeys(self.required_libs))

        for lib in obj['libraries']:
            installed_libs.append(lib['library']['RealName'])
            print (lib['library']['RealName'])
        installed_libs = list(dict.fromkeys(installed_libs))

        for req_lib in self.required_libs:
            if not (req_lib in installed_libs):
                to_be_installed_libs.append(req_lib)

        for lib in self.required_libs:
            print ("Installing:" + lib)
            system("arduino-cli.exe lib install \"" + lib + "\"")
