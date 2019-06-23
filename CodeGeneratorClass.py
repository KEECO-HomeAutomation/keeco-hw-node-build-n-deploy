import json
from os.path import isfile, isdir, join, dirname, realpath, split
import shutil
import errno
from os import listdir, mkdir, system, name

class CodeGenerator():
    def __init__(self):

        self.manageIO_content = ""
        self.MQTT_content = ""
        self.PluginList = list()

        self.includes = []
        self.var_init = []
        self.mqtt_sub = []
        self.init = []
        self.publish = []
        self.readinput = []
        self.setoutput = []
        self.dependencies = []
        self.endpoints_list = []
        self.templates_list = []
        self.pluginAutonumbering = dict()

        self.descriptorFileContent = dict()

        with open('settings.json') as json_file:
            self.settings_data = json.load(json_file)
        self.template_path, self.template_lastfolder = split(self.settings_data['templateFolderPath'])
        self.fullResultFolderPath = join(self.settings_data['resultFolderPath'],self.template_lastfolder)
        if isdir(self.fullResultFolderPath):
            shutil.rmtree(self.fullResultFolderPath)
        else:
            mkdir(self.fullResultFolderPath)
        self.copy(self.settings_data['templateFolderPath'], self.fullResultFolderPath)
        self.manage_IO_Path = join(self.fullResultFolderPath, 'Manage_IO.ino')
        self.MQTT_Path = join(self.fullResultFolderPath, 'MQTT.ino')
        print("___CodeGen working directories are set")

    def fullCodeGenProcess(self, name):
        self.loadTemplates()
        self.loadTempPluginCollection()
        self.generateCode()
        self.writeCodeToFile()
        self.generateDescriptorFileContent(name)
        self.writeDescriptorContentToFile()

    def loadTemplates(self):
        with open(self.manage_IO_Path) as manageIO_file:
            self.manageIO_content = manageIO_file.read()
        with open(self.MQTT_Path) as MQTT_file:
            self.MQTT_content = MQTT_file.read()

    def loadTempPluginCollection(self):
        with open('temp_plugins.json') as temp_plugin_file:
            self.PluginList = json.load(temp_plugin_file)

    def generateCode(self):
        includelines = []
        for plugin in self.PluginList:
            if plugin['pluginPath'] in self.pluginAutonumbering:
                self.pluginAutonumbering[plugin['pluginPath']] += 1
            else:
                self.pluginAutonumbering[plugin['pluginPath']] = 0
            self.includes.append(plugin['Includes'])
            self.var_init.append(self.generateVarInitString(plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))
            self.mqtt_sub.append(self.changeNameToAlias(plugin['MQTT Subscriptions'],plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))
            self.init.append(self.changeNameToAlias(plugin['Init'],plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))
            self.publish.append(self.changeNameToAlias(plugin['Publish'],plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))
            self.readinput.append(self.changeNameToAlias(plugin['ReadInput'],plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))
            self.setoutput.append(self.changeNameToAlias(plugin['Setoutput'],plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))
            self.dependencies.append(plugin['Dependencies'])
            self.templates_list.append(self.changeNameToAliasInTemplates(plugin['templates'],plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))
            self.endpoints_list.append(self.changeNameToAliasInEndpoints(plugin['endpoints'],plugin['Variables'],self.pluginAutonumbering[plugin['pluginPath']]))

        for include in self.includes:
            lines = include.splitlines()
            for line in lines:
                includelines.append(line)
        includelines = list(dict.fromkeys(includelines))
        self.includes = includelines

        self.MQTT_content = self.replaceKeywordWithCodeMQTT(self.MQTT_content, "//@mqttSubTopics@", self.mqtt_sub)
        self.manageIO_content = self.replaceKeywordWithCode(self.manageIO_content, "//@includes@", self.includes)
        self.manageIO_content = self.replaceKeywordWithCode(self.manageIO_content, "//@globalvars@", self.var_init)
        self.manageIO_content = self.replaceKeywordWithCode(self.manageIO_content, "//@initIOcode@", self.init)
        self.manageIO_content = self.replaceKeywordWithCode(self.manageIO_content, "//@readIOcode@", self.readinput)
        self.manageIO_content = self.replaceKeywordWithCode(self.manageIO_content, "//@publishIOcode@", self.publish)
        self.manageIO_content = self.replaceKeywordWithCode(self.manageIO_content, "//@setOutputscode@", self.setoutput)
        print("___Code has been generated")

    def writeCodeToFile(self):
        with open(self.manage_IO_Path, "w") as f:
            f.write(self.manageIO_content)
        with open(self.MQTT_Path, "w") as f:
            f.write(self.MQTT_content)
        print("___Code has been written to file")

    def generateDescriptorFileContent(self, name):
        temp_templatelist = list()
        temp_endpointlist = list()
        self.descriptorFileContent['name'] = name
        self.descriptorFileContent['uuid'] = "UUID_PLACEHOLDER"
        for templates in self.templates_list:
            for template in templates:
                temp_templatelist.append(template)
        for endpoints in self.endpoints_list:
            for endpoint in endpoints:
                temp_endpointlist.append(endpoint)
        self.descriptorFileContent['endpoints'] = temp_endpointlist
        self.descriptorFileContent['templates'] = temp_templatelist
        print("___Descriptor file content has been created for KEECO HW Node: " + name)

    def writeDescriptorContentToFile(self):
        dataFolderPath = join(self.fullResultFolderPath, "data")
        dataFileName = join(dataFolderPath, "hwnode_info.txt")
        with open(dataFileName, "w") as f:
            json.dump(self.descriptorFileContent, f)
        print("___Descriptor file content has been written to file")

    def copy(self, src, dest):
        try:
            shutil.copytree(src, dest)
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                shutil.copy(src, dest)
            else:
                print('Directory not copied. Error: %s' % e)

    def changeNameToAlias(self, src, vars, number):
        result = src
        for var in vars:
            if (var['Name'] != ""):
                result = result.replace(var['Name'],var['Alias'])
        result = result.replace('@N@', str(number))
        return result

    def generateVarInitString(self, vars, number):
        result = ""
        for var in vars:
            if (var['Name'] != ""):
                result = result + var['Variable Initialisation'].replace(var['Name'],var['Alias']) + "\r"
            else:
                result = result + var['Variable Initialisation'] + "\r"

        result = self.changeNameToAlias(result, vars, number)
        result = result.replace("@N@", str(number))
        return result

    def replaceKeywordWithCodeMQTT(self, src, keyword, array):
        tempreplacement = ""
        for element in array[:-1]:
            tempreplacement = tempreplacement + element + ',' + "\r"
        tempreplacement = tempreplacement + array[-1] + "\r"
        num_of_MQTT_topics = tempreplacement.count(',')
        result = src.replace(keyword,tempreplacement)
        result = result.replace("int mqttSubTopicCount = 0;", "int mqttSubTopicCount = " + str(num_of_MQTT_topics+1) + ";")
        return result


    def replaceKeywordWithCode(self, src, keyword, array):
        tempreplacement = ""
        for element in array:
            tempreplacement = tempreplacement + element + "\r"
        result = src.replace(keyword,tempreplacement)
        return result

    def changeNameToAliasInTemplates(self, templatelist, vars, number):
        templates_out = list()
        for template in templatelist:
            mappings_out = list()
            template_out = dict()
            template_out['name'] = self.changeNameToAlias(template['name'], vars, number)
            for mapping in template['mappings']:
                mapping_out = dict()
                mapping_out['name'] = self.changeNameToAlias(mapping['name'],vars, number)
                mapping_out['endpoint'] = self.changeNameToAlias(mapping['endpoint'],vars, number)
                mappings_out.append(mapping_out)
            template_out['mappings'] = mappings_out
            templates_out.append(template_out)
        return templates_out

    def changeNameToAliasInEndpoints(self, endpointlist, vars, number):
        endpoints_out = list()
        for endpoint in endpointlist:
            endpoint_out = dict()
            endpoint_out['name'] = self.changeNameToAlias(endpoint['name'], vars, number)
            endpoint_out['output'] = self.changeNameToAlias(endpoint['output'], vars, number)
            endpoint_out['range'] = self.changeNameToAlias(endpoint['range'], vars, number)
            endpoints_out.append(endpoint_out)
        return endpoints_out
