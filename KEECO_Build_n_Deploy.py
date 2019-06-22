# KEECO Build & Deploy tool based on the Multi-frame tkinter application v2.3 regarding the GUI
import tkinter as tk
from tkinter import ttk
import sys
import glob
import serial
import json
import errno
import tempfile
import shutil
import pprint
import subprocess
from os import listdir, mkdir, system, name
from os.path import isfile, isdir, join, dirname, realpath, split
from tkinter import filedialog
import tkinter.scrolledtext as tkst


class SampleApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(MainPage)

    def switch_frame(self, frame_class):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.grid()

class MainPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="KEECO HW Node App Generator v0.1").grid()
        tk.Button(self, text="Manage Plug-ins", width=60, command=lambda: master.switch_frame(PlugInManagerPage)).grid()
        tk.Button(self, text="Build Application", width=60, command=lambda: master.switch_frame(BuildPage)).grid()
        tk.Button(self, text="Deploy Application", width=60, command=lambda: master.switch_frame(DeployPage)).grid()
        tk.Button(self, text="Configuration", width=60, command=lambda: master.switch_frame(ConfigPage)).grid()
        tk.Label(self, text="Advanced Features").grid()
        tk.Button(self, text="Create Plug-Ins", width=60, command=lambda: master.switch_frame(PlugInCreatePage)).grid()

class PlugInManagerPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        if (isfile('settings.json')):
            with open('settings.json') as json_file:
                self.data = json.load(json_file)
            self.pluginDirPath = self.data['pluginFolderPath']
        else:
            self.pluginDirPath = dirname(realpath(__file__))

        self.varFrameObjs = list()
        tk.Label(self, text="Plug-in Selector").grid()
        tk.Button(self, text="Return to Main Page", width=80, command=lambda: master.switch_frame(MainPage)).grid()
        tk.Label(self, text="Plug-ins added to this project:").grid()
        self.variablesFrame = tk.Frame(self)
        self.variablesFrame.grid()
        tk.Button(self, text="Add Plugin", bg='green', width=80, command=lambda: self.addPlugin(self.variablesFrame)).grid()
        tk.Button(self, text="Save Project", width=80, command=lambda: self.saveProject(self.varFrameObjs)).grid()
        self.loadVarsAtStart(self.variablesFrame)

    def addPlugin(self, variablesframe):
        t = tk.Toplevel(self)
        t.title('Select Plugin to Add:')
        lb = tk.Listbox(t, width=100)
        avalPlugins = [f for f in listdir(self.pluginDirPath) if isfile(join(self.pluginDirPath, f))]
        for plugin in avalPlugins:
            lb.insert(0, plugin)
        lb.grid()
        tk.Button(t, text="Use Selected PlugIn", command=lambda: self.addtoVarSettingsFrame(variablesframe, lb)).grid()

    def addtoVarSettingsFrame(self, variablesframe, lb):
        DirPath = self.pluginDirPath
        CurrSel = lb.get(lb.curselection())
        selectedPlugIn = join(DirPath, CurrSel)

        varFrame = tk.Frame(variablesframe, bd = 3,  relief='groove')
        with open(selectedPlugIn) as plugin_file:
            pluginData = json.load(plugin_file)
        tk.Label(varFrame, text=CurrSel).grid()

        for var in pluginData['Variables']:
            entry = EntryWithLabel(varFrame, var['Description'])
            if (var['Name'] != ""):
                entry.grid(sticky = 'e')

        tk.Button(varFrame, text="Delete this Plug-in", bg='red', width=60, command= lambda:self.delete(varFrame, self.varFrameObjs)).grid()

        self.varFrameObjs.append(varFrame)
        varFrame.grid(sticky='e')

    def loadVarsAtStart(self, variablesframe):
        if (isfile('temp_plugins.json')):
            with open('temp_plugins.json') as temp_plugin_file:
                loadedPluginList = json.load(temp_plugin_file)
            for pluginData in loadedPluginList:
                varFrame = tk.Frame(variablesframe, bd=3, relief='groove')
                path, filename = split(pluginData['pluginPath'])
                tk.Label(varFrame, text=filename).grid()
                for var in pluginData['Variables']:
                    entry = EntryWithLabel(varFrame, var['Description'])
                    if (var['Name'] != ""):
                        entry.grid(sticky='e')
                        entry.setEntryValue(var['Alias'])
                tk.Button(varFrame, text="Delete this Plug-in", bg='red', width=60, command= lambda:self.delete(varFrame, self.varFrameObjs)).grid()
                self.varFrameObjs.append(varFrame)
                varFrame.grid(sticky='e')

    def delete(self, varframe, varframeobjs):
        to_be_deleted = varframeobjs.index(varframe)
        varframeobjs[to_be_deleted].grid_forget()
        del varframeobjs[to_be_deleted]

    def saveProject(self, varframeobjs):
        tempPluginList = list()
        directCopies = ['MQTT Subscriptions','Includes','Init','Publish','ReadInput','Setoutput','IO Type','Dependencies', 'templates', 'endpoints']
        for frame in varframeobjs:
            tempPlugin = dict()
            temp_varobjlist = list()
            widgetlist = frame.winfo_children()

            actualPlugin = join(self.pluginDirPath, widgetlist[0]['text'])

            with open(actualPlugin) as plugin_file:
                pluginData = json.load(plugin_file)
            for widget, var in zip(widgetlist[1:-1], pluginData['Variables']):
                temp_var = dict()
                temp_var['Alias'] = widget.getEntryValue()
                temp_var['Name'] = var['Name']
                temp_var['Description'] = var['Description']
                temp_var['Variable Initialisation'] = var['Variable Initialisation']
                temp_varobjlist.append(temp_var)
            tempPlugin['Variables'] = temp_varobjlist
            for key in directCopies:
                tempPlugin[key] = pluginData[key]
            tempPlugin['pluginPath'] = actualPlugin
            tempPluginList.append(tempPlugin)


        with open('temp_plugins.json', 'w') as temp_plugin_file:
            json.dump(tempPluginList, temp_plugin_file)


class BuildPage(tk.Frame):
    def deletePlugin(self, tree):
        selected_item = tree.selection()[0]
        if (tree.item(tree.parent(selected_item))['text']=="Plug-Ins"):
            selection_index = tree.index(selected_item)
            tree.delete(selected_item)
            del self.tempPluginList[selection_index]
            with open('temp_plugins.json', 'w') as temp_plugin_file:
                json.dump(self.tempPluginList, temp_plugin_file)
        else:
            print('Warning: Can only delete if Plug-In level is selected!')

    def copy(self, src, dest):
        try:
            shutil.copytree(src, dest)
        except OSError as e:
            # If the error was caused because the source wasn't a directory
            if e.errno == errno.ENOTDIR:
                shutil.copy(src, dest)
            else:
                print('Directory not copied. Error: %s' % e)

    def lastFolderInPath(self, path):           #currently unused
        folders = []
        while 1:
            path, folder = split(path)
            if folder != "":
                folders.append(folder)
            else:
                if path != "":
                    folders.append(path)
                break
        return folders[0]

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

    def generateCode(self):
        includes = []
        var_init = []
        mqtt_sub = []
        init = []
        publish = []
        readinput = []
        setoutput = []
        dependencies = []
        includelines = []
        endpoints_list = []
        templates_list = []
        pluginAutonumbering = dict()

        with open('settings.json') as json_file:
            self.settings_data = json.load(json_file)
        template_path, template_lastfolder = split(self.settings_data['templateFolderPath'])
        self.fullResultFolderPath = join(self.settings_data['resultFolderPath'],template_lastfolder)

        if isdir(self.fullResultFolderPath):
            shutil.rmtree(self.fullResultFolderPath)
        else:
            mkdir(self.fullResultFolderPath)
        self.copy(self.settings_data['templateFolderPath'], self.fullResultFolderPath)
        manage_IO_Path = join(self.fullResultFolderPath, 'Manage_IO.ino')
        MQTT_Path = join(self.fullResultFolderPath, 'MQTT.ino')

        with open(manage_IO_Path) as manageIO_file:
            manageIO_content = manageIO_file.read()

        with open(MQTT_Path) as MQTT_file:
            MQTT_content = MQTT_file.read()

        with open('temp_plugins.json') as temp_plugin_file:
            PluginList = json.load(temp_plugin_file)

        for plugin in PluginList:
            if plugin['pluginPath'] in pluginAutonumbering:
                pluginAutonumbering[plugin['pluginPath']] += 1
            else:
                pluginAutonumbering[plugin['pluginPath']] = 0

            includes.append(plugin['Includes'])
            var_init.append(self.generateVarInitString(plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))
            mqtt_sub.append(self.changeNameToAlias(plugin['MQTT Subscriptions'],plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))
            init.append(self.changeNameToAlias(plugin['Init'],plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))
            publish.append(self.changeNameToAlias(plugin['Publish'],plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))
            readinput.append(self.changeNameToAlias(plugin['ReadInput'],plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))
            setoutput.append(self.changeNameToAlias(plugin['Setoutput'],plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))
            dependencies.append(plugin['Dependencies'])
            templates_list.append(self.changeNameToAliasInTemplates(plugin['templates'],plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))
            endpoints_list.append(self.changeNameToAliasInEndpoints(plugin['endpoints'],plugin['Variables'],pluginAutonumbering[plugin['pluginPath']]))


        for include in includes:
            lines = include.splitlines()
            for line in lines:
                includelines.append(line)

        includelines = list(dict.fromkeys(includelines))
        includes = includelines

        MQTT_content = self.replaceKeywordWithCodeMQTT(MQTT_content, "//@mqttSubTopics@", mqtt_sub)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@includes@", includes)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@globalvars@", var_init)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@initIOcode@", init)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@readIOcode@", readinput)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@publishIOcode@", publish)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@setOutputscode@", setoutput)

        self.generateDescriptorFile(templates_list, endpoints_list, self.hwnode_name.get())

        with open(manage_IO_Path, "w") as f:
            f.write(manageIO_content)
        with open(MQTT_Path, "w") as f:
            f.write(MQTT_content)
        print(MQTT_content)
        print(manageIO_content)
        print("Code has been created successfully!")

    def generateDescriptorFile(self, templates_list, endpoints_list, name):
        result = dict()
        temp_templatelist = list()
        temp_endpointlist = list()
        result['name'] = name
        result['uuid'] = "UUID_PLACEHOLDER"
        for templates in templates_list:
            for template in templates:
                temp_templatelist.append(template)
        for endpoints in endpoints_list:
            for endpoint in endpoints:
                temp_endpointlist.append(endpoint)
        result['endpoints'] = temp_endpointlist
        result['templates'] = temp_templatelist

        dataFolderPath = join(self.fullResultFolderPath, "data")
        dataFileName = join(dataFolderPath, "hwnode_info.txt")

        with open(dataFileName, "w") as f:
            json.dump(result, f)


    def buildBinary(self):
        with open('settings.json') as json_file:
            self.settings_data = json.load(json_file)
        template_path, template_lastfolder = split(self.settings_data['templateFolderPath'])
        fullResultFolderPath = join(self.settings_data['resultFolderPath'],template_lastfolder)

        print("OS Type:" + name)
        system("cd " + fullResultFolderPath + "&" + "dir")

        print("arduino-cli.exe compile --fqbn esp8266:esp8266:d1_mini " + fullResultFolderPath + " --build-path " + self.settings_data['buildFolderPath'])
        res = system("arduino-cli.exe compile --fqbn esp8266:esp8266:d1_mini " + fullResultFolderPath + " --build-path " + self.settings_data['buildFolderPath'])
        if (res == 0):
            print("BUILD SUCCESSFULLY FINISHED! You can deploy your binary now!")
        else:
            print("Build was not successful! Error code: " + str(res) + " For details see the console above...")

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

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.required_libs = list()

        tk.Label(self, text="App Builder").grid()
        tk.Button(self, text="Return to Main Page", width=60,
                  command=lambda: master.switch_frame(MainPage)).grid()
        if (isfile('temp_plugins.json')):
            with open('temp_plugins.json') as temp_plugin_file:
                self.tempPluginList = json.load(temp_plugin_file)
        tk.Label(self, text="Give a name for your KEECO HW Node").grid()
        self.hwnode_name = tk.Entry(self, width=50)
        self.hwnode_name.grid()
        self.tree = ttk.Treeview(self, height=20, selectmode='browse')
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vsb.set)
        self.vsb.grid(column=1, sticky='e')

        self.tree["columns"]=("aliases","type","dependencies")
        self.tree.column("aliases", width=150, minwidth=150, stretch=tk.NO)
        self.tree.column("type", width=200, minwidth=200)
        self.tree.column("dependencies", width=400, minwidth=350, stretch=tk.NO)
        self.tree.heading("aliases", text="Aliases",anchor=tk.W)
        self.tree.heading("type", text="Type",anchor=tk.W)
        self.tree.heading("dependencies", text="Dependencies",anchor=tk.W)
        self.treeitems = []
        self.root_tree_node = self.tree.insert('', 'end', text='Plug-Ins', open=True)
        for idx, plugin in enumerate(self.tempPluginList):
            self.path, self.filename = split(plugin['pluginPath'])
            print(str(idx) + self.filename)
            self.treeitems.append(self.tree.insert(self.root_tree_node, idx, text=self.filename, values=("",plugin['IO Type'], plugin['Dependencies']), open='true'))
            for var in plugin["Variables"]:
                print(str(idx) + var['Name'] + var['Alias'])
                if (var['Name'] != ""):
                    self.tree.insert(self.treeitems[idx], "end", text=var['Name'], values=(var['Alias'],"",""))
        self.tree.grid()
        tk.Button(self, text="Delete Selected Plugin", width=60, command=lambda: self.deletePlugin(self.tree)).grid()
        tk.Button(self, text="Check Dependencies", width=60, command=lambda: self.installDependencies()).grid()
        tk.Button(self, text="Generate Code", width=60, command=lambda: self.generateCode()).grid()
        tk.Button(self, text="Build Wemos Binary", width=60, command=lambda: self.buildBinary()).grid()

class DeployPage(tk.Frame):
    def __init__(self, master):
        self.wemosSerialPort = ""
        self.portList = list()
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Deployment").grid()
        tk.Button(self, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).grid()
        tk.Button(self, text="Select Serial Port", command=lambda: self.openSerialSelectWindow()).grid()


    def list_serial_ports(self, lb):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        self.portList = result
        lb.delete(0,tk.END)
        for port in self.portList:
            lb.insert(0, port)

    def openSerialSelectWindow(self):
        t = tk.Toplevel(self)
        t.title('Select Serial port for Wemos')
        self.lb = tk.Listbox(t, width=20)
        self.b = tk.Button(t, text="Scan Serial Ports", command=lambda: self.list_serial_ports(self.lb))
        self.b.grid()
        self.list_serial_ports(self.lb)
        self.lb.grid()

class ConfigPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="Configuration").grid(row=0, column=0)
        tk.Button(self, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).grid(row=1, column=0)
        tk.Button(self, text="Save Settings", command=lambda: self.saveSettingsToFile()).grid(row=2, column=0)
        dir_path = dirname(realpath(__file__))
        if (isfile('settings.json')):
            with open('settings.json') as json_file:
                self.data = json.load(json_file)
        else:
            self.data =    {
              "pluginFolderPath": dir_path,
              "templateFolderPath": dir_path,
              "resultFolderPath": dir_path,
              "buildFolderPath": dir_path
            }
        self.pluginPath = EntryWithBrowse(self, "Plugin Path")
        self.templateFolderPath = EntryWithBrowse(self, "Template Path")
        self.resultFolderPath = EntryWithBrowse(self, "Result Path")
        self.buildFolderPath = EntryWithBrowse(self, "Build Path")

        self.pluginPath.grid(row=4, sticky="e")
        self.templateFolderPath.grid(row=5, sticky="e")
        self.resultFolderPath.grid(row=6, sticky="e")
        self.buildFolderPath.grid(row=7, sticky="e")

        self.pluginPath.setEntryValue(self.data['pluginFolderPath'])
        self.templateFolderPath.setEntryValue(self.data['templateFolderPath'])
        self.resultFolderPath.setEntryValue(self.data['resultFolderPath'])
        self.buildFolderPath.setEntryValue(self.data['buildFolderPath'])
    def saveSettingsToFile(obj):
        obj.data["pluginFolderPath"] = obj.pluginPath.getEntryValue()
        obj.data["templateFolderPath"] = obj.templateFolderPath.getEntryValue()
        obj.data["resultFolderPath"] = obj.resultFolderPath.getEntryValue()
        obj.data["buildFolderPath"] = obj.buildFolderPath.getEntryValue()
        with open('settings.json', 'w') as json_file:
            json.dump(obj.data, json_file)

class PlugInCreatePage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.variables = list()
        self.dependencies = list()
        self.iotype = tk.StringVar()

        self.canvas = tk.Canvas(self, bd=0, width=1024, height=768)
        self.frame_in_canvas = tk.Frame(self.canvas)
        self.variables_frame = tk.Frame(self.frame_in_canvas)
        self.dependencies_frame = tk.Frame(self.frame_in_canvas)
        self.templates_frame = tk.Frame(self.frame_in_canvas)
        self.endpointlist_frame = tk.Frame(self.frame_in_canvas)


        self.yscrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview )
        self.canvas.configure(yscrollcommand=self.yscrollbar.set)

        self.yscrollbar.grid(row=0, column=1, sticky='N'+'S')
        self.canvas.grid(row=0, column=0, sticky='N'+'S'+'E'+'W')
        self.canvas_window_id = self.canvas.create_window(0, 0, window=self.frame_in_canvas, anchor='nw')

        self.frame_in_canvas.bind("<Configure>", self.onFrameConfigure)

        tk.Label(self.frame_in_canvas, text="Create PlugIn").grid(row=0, column=0)
        tk.Button(self.frame_in_canvas, text="Return to Main Page", width = 70, command=lambda: master.switch_frame(MainPage)).grid()
        tk.Button(self.frame_in_canvas, text='Open Plugin', width = 70, command=lambda: self.openPlugin()).grid()
        tk.Button(self.frame_in_canvas, text='Save Plugin', width = 70, command=lambda: self.savePlugin()).grid()
        tk.Label(self.frame_in_canvas, text="Includes - Add complete include line, for example: #include <ESP8266WiFi.h> \r You can add multiple include lines as well.").grid()
        self.includesEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.includesEntry.grid()
        self.variables_frame.grid()
        tk.Button(self.frame_in_canvas, text="Add Variable", width = 70, command=lambda: self.addVariable(self.variables_frame)).grid()
        self.addVariable(self.variables_frame)
        tk.Label(self.frame_in_canvas, text="MQTT Subscriptions - Add your MQTT Subscription topics here. If multiple topics are to be included use a ,(comma) to seperate them and make sure not to put one after the last topic! \r Topics should be included in this format: \"node/UUID_PLACEHOLDER/@TOPIC@\" - where @TOPIC@ is your symbol for the actual topic in the variable definitions and \"node\" is fixed.\rMake sure to put quotations marks as well! \r The \" UUID_PLACEHOLDER \" will be replaced on the KEECO HW Node in run-time as the UUID is stored in the device's EEPROM").grid()
        self.mqttSubEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.mqttSubEntry.grid()
        tk.Label(self.frame_in_canvas, text="Initialisation - Place your code here that initialises your hardware add-ons / I/O on the Wemos. The code placed here will be called during Wemos's setup() function. \r Please note that the variable init should happen outside of this segment and be defined in the variables input field's Init box.").grid()
        self.initEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.initEntry.grid()
        tk.Label(self.frame_in_canvas, text="Publish - Place your code here that publishes information via the MQTT Client. You must use the client.publish(topic, data_char_arr, 1) function to publish data. \r Topic should be a symbol defined in the Variables field, \"1\" is the MQTT QoS. \r For your comfort we have created a \"char tempstr[128]\" that can be used with the itoa() function to do data type conversion for the publish() function. \r The tempstr[] variable is shared accross plugins but in this segment no other plugin can access it. \r This code is called every 5 seconds. Don't place code here that takes significant amount of time to execute. Publish values from variables stored in the Read I/O segment.").grid()
        self.publishEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.publishEntry.grid()
        tk.Label(self.frame_in_canvas, text="Read I/O - Place your code here to read inputs on your Wemos. This part can be used to store values to variables for the MQTT Publish() function, \r or you can explicitly call Publish() to publish changes.").grid()
        self.readIOEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.readIOEntry.grid()
        tk.Label(self.frame_in_canvas, text="Set Output - Place your code here to set outputs. Code here will be called in a function which is a callback \r function called when a new MQTT message is detected for any of the subscribed topics. \r The code below is placed in function whose signature is: \"setOutputs(char* topic, byte* payload, unsigned int length)\" \r We have created an \"int tempint\" variable in case you need a variable for conversion.").grid()
        self.setOutputEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.setOutputEntry.grid()
        tk.Label(self.frame_in_canvas, text="I/O Type - Define the Template Name how this I/O should appear in your KEECO System. See details on GitHub - keeco-hub!").grid()
        self.ioTypeEntry = tk.Entry(self.frame_in_canvas, textvariable=self.iotype, width=100)
        self.ioTypeEntry.grid()
        tk.Label(self.frame_in_canvas, text="Dependenices - Required dependencies for your plugin will be automatically installed. \r Use the name format of the requiered library how it appears with arduino-cli lib list - replace _(underscores) with space ").grid()
        self.dependencies_frame.grid()
        self.addDependency(self.dependencies_frame)
        tk.Button(self.frame_in_canvas, text="Add Dependency", width = 70, command=lambda: self.addDependency(self.dependencies_frame)).grid()
        tk.Label(self.frame_in_canvas, text="Templates").grid()
        self.templates_frame.grid()
        self.templatebox = TemplatesEntry(self.templates_frame)
        self.templatebox.grid()
        self.endpointlist_frame.grid()
        self.endpointbox = EndpointListEntry(self.endpointlist_frame)
        self.endpointbox.grid()


    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def addVariable(self, parent):
        self.variables.append(VariableTextboxes(parent, self.variables, bd =3, relief='groove'))
        self.variables[-1].grid()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def addDependency(self, parent):
        self.dependencies.append(DependencyEntry(parent, self.dependencies))
        self.dependencies[-1].grid()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def openPlugin(self):
        self.includesEntry.delete(1.0,'end')
        self.mqttSubEntry.delete(1.0,'end')
        self.initEntry.delete(1.0,'end')
        self.publishEntry.delete(1.0,'end')
        self.readIOEntry.delete(1.0,'end')
        self.setOutputEntry.delete(1.0,'end')
        self.ioTypeEntry.delete(0,'end')

        filename =  filedialog.askopenfilename(initialdir = "/",title = "Select Plug-in to Open",filetypes = (("plugin files","*.json"),("all files","*.*")))
        if (isfile(filename)):
            with open(filename) as plugin_file:
                plugin = json.load(plugin_file)
            self.includesEntry.insert(1.0, plugin['Includes'])
            for widget in self.variables:
                widget.grid_forget()
            del self.variables[:]
            for var in plugin['Variables']:
                self.variables.append(VariableTextboxes(self.variables_frame, self.variables))
                self.variables[-1].setEntryValue(var)
                self.variables[-1].grid()
            self.mqttSubEntry.insert(1.0, plugin['MQTT Subscriptions'])
            self.initEntry.insert(1.0, plugin['Init'])
            self.publishEntry.insert(1.0, plugin['Publish'])
            self.readIOEntry.insert(1.0, plugin['ReadInput'])
            self.setOutputEntry.insert(1.0, plugin['Setoutput'])
            self.ioTypeEntry.insert(0, plugin['IO Type'])
            for widget in self.dependencies:
                widget.grid_forget()
            del self.dependencies[:]
            for dep in plugin['Dependencies']:
                self.dependencies.append(DependencyEntry(self.dependencies_frame, self.dependencies))
                self.dependencies[-1].setEntryValue(dep)
                self.dependencies[-1].grid()
            self.templatebox.setEntryValue(plugin['templates'])
            self.endpointbox.setEntryValue(plugin['endpoints'])

    def savePlugin(self):
        filename =  filedialog.asksaveasfilename(initialdir = "/",title = "Select Plug-in to Save",filetypes = (("plugin files","*.json"),("all files","*.*")))
        varlist = list()
        deplist = list()
        pluginData = dict()

        for var in self.variables:
            varlist.append(var.getEntryValue())
        pluginData['Variables'] = varlist
        pluginData['MQTT Subscriptions'] = self.mqttSubEntry.get(1.0, 'end')
        pluginData['Includes'] = self.includesEntry.get(1.0, 'end')
        pluginData['Init'] = self.initEntry.get(1.0, 'end')
        pluginData['Publish'] = self.publishEntry.get(1.0, 'end')
        pluginData['ReadInput'] = self.readIOEntry.get(1.0, 'end')
        pluginData['Setoutput'] = self.setOutputEntry.get(1.0, 'end')
        pluginData['IO Type'] = self.ioTypeEntry.get()
        for dep in self.dependencies:
            deplist.append(dep.getEntryValue())
        pluginData['Dependencies'] = deplist
        pluginData['templates'] = self.templatebox.getEntryValue()
        pluginData['endpoints'] = self.endpointbox.getEntryValue()

        with open(filename, 'w') as plugin_file:
            json.dump(pluginData, plugin_file)

class EntryWithBrowse(tk.Frame):
    def __init__(self, parent, Name):
        tk.Frame.__init__(self, parent)
        self.name = Name
        self.var = tk.StringVar()
        self.w = tk.Label(self, text=self.name)
        self.e = tk.Entry(self, textvariable=self.var, width=100)
        self.b = tk.Button(self, text="Browse", command=lambda:self.var.set(filedialog.askdirectory()))
        self.w.grid(row=0, column=0, columnspan=3)
        self.e.grid(row=0, column=3, columnspan=5)
        self.b.grid(row=0, column=8, columnspan=1)
    def getEntryValue(self):
        print(str(self.var.get()))
        return str(self.var.get())
    def setEntryValue(self, value):
        self.var.set(value)

class EntryWithLabel(tk.Frame):
    def __init__(self, parent, Name):
        tk.Frame.__init__(self, parent)
        self.name = Name
        self.var = tk.StringVar()
        self.w = tk.Label(self, text=self.name)
        self.e = tk.Entry(self, textvariable=self.var, width=50)
        self.w.grid(row=0, column=0, columnspan=3)
        self.e.grid(row=0, column=3, columnspan=5)
    def getEntryValue(self):
        #print(str(self.var.get()))
        return str(self.var.get())
    def setEntryValue(self, value):
        self.var.set(value)

class VariableTextboxes(tk.Frame):
    def __init__(self, parent, varlist,  *args, **kwargs):
        tk.Frame.__init__(self, parent,  *args, **kwargs)
        self.l1 = tk.Label(self, text="Variable Name - Choose a unique symbol that will be replaced by User given alias, for example: @var@ \r Leave this field empty if you don't want to expose this variable to the user.")
        self.l2 = tk.Label(self, text="Variable Description - This text will be displayed when asking for user input for this variable")
        self.l3 = tk.Label(self, text="Variable Initialisation - Place variable initialisation code here if needed (a variable can be a user provided alias only in your code) \r Place the @N@ token in the name of your variable to make sure this plug-in can be added multiple times. \r @N@ token will be replaced by plug-in instance number automatically. This applies to all fields expect Include.")
        self.name = tk.StringVar()
        self.nameBox = tk.Entry(self, textvariable=self.name, width=100)
        self.description = tk.StringVar()
        self.descriptionBox = tk.Entry(self, textvariable=self.description, width=100)
        self.variableInitBox = tkst.ScrolledText(master = self, wrap   = 'word', width  = 100, height = 5)
        self.l1.grid()
        self.nameBox.grid()
        self.l2.grid()
        self.descriptionBox.grid()
        self.l3.grid()
        self.variableInitBox.grid()
        self.delButton = tk.Button(self, text="Delete this Variable", bg='red', command= lambda:self.delete(varlist))
        self.delButton.grid()

    def delete(self, varlist):
        self.grid_forget()
        to_be_deleted = varlist.index(self)
        print (to_be_deleted)
        del varlist[to_be_deleted]

    def getEntryValue(self):
        result = dict()
        result['Name'] = self.name.get()
        result['Description'] = self.description.get()
        result['Variable Initialisation'] = self.variableInitBox.get(1.0, tk.END)
        return result

    def setEntryValue(self, value):
        self.name.set(value['Name'])
        self.description.set(value['Description'])
        self.variableInitBox.insert(1.0, value['Variable Initialisation'])

class DependencyEntry(tk.Frame):
    def __init__(self, parent, varlist):
        #self.variablesList = varlist
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Dependency").grid()
        self.dependency = tk.StringVar()
        self.dependencyBox = tk.Entry(self, textvariable=self.dependency, width=100)
        self.dependencyBox.grid()

        self.delButton = tk.Button(self, text="Delete this Dependency", bg='red', command= lambda:self.delete(varlist))
        self.delButton.grid()

    def delete(self, varlist):
        self.grid_forget()
        to_be_deleted = varlist.index(self)
        print (to_be_deleted)
        del varlist[to_be_deleted]

    def getEntryValue(self):
        return self.dependency.get()

    def setEntryValue(self, value):
        self.dependency.set(value)

class TemplatesEntry(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        templateentry = TemplateEntry(parent)
        self.templateListFrame = tk.Frame(parent, bd=3, relief='groove')
        self.templateListFrame.grid()
        tk.Button(self, text="Add Template", bg='green', width=80, command=lambda: self.addTemplate()).grid()
        #self.addTemplate()

    def addTemplate(self):
        self.template = TemplateEntry(self.templateListFrame)
        self.template.grid()

    def setEntryValue(self, value):
        for template in value:
            self.template = TemplateEntry(self.templateListFrame)
            self.template.grid()
            self.template.setEntryValue(template)

    def getEntryValue(self):
        output = list()
        templateObjList = self.templateListFrame.winfo_children()
        for obj in templateObjList:
            template = dict()
            template = obj.getEntryValue()
            output.append(template)
        return output

class TemplateEntry(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.TemplateEntry = EntryWithLabel(self, "Template Name")
        self.TemplateEntry.grid()
        self.mappingsFrame = tk.Frame(self, bd=3, relief='groove')
        self.mappingsFrame.grid()
        tk.Button(self, text="Add Mapping", bg='green', width=40, command=lambda: self.addMappings()).grid()
        self.delButton = tk.Button(self, text="Delete this item template", width=80, bg='red', command= lambda:self.delete())
        self.delButton.grid()
        #self.addMappings()

    def delete(self):
        self.grid_forget()
        self.destroy()

    def getEntryValue(self):
        output = dict()
        mappinglist = list()
        output['name'] = self.TemplateEntry.getEntryValue()
        mappingsWidgetList = self.mappingsFrame.winfo_children()
        for widget in mappingsWidgetList:
            mapping = dict()
            mapping = widget.getEntryValue()
            mappinglist.append(mapping)
        output['mappings'] = mappinglist
        return output

    def setEntryValue(self, value):
        self.TemplateEntry.setEntryValue(value['name'])
        for mapping in value['mappings']:
            mappingBox = self.addMappings()
            mappingBox.setEntryValue(mapping)

    def addMappings(self):
        self.mappingsentry = MappingsEntry(self.mappingsFrame)
        self.mappingsentry.grid()
        return self.mappingsentry

class MappingsEntry(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        tk.Label(self, text="Mapping - Pin:").grid()
        self.mappingPinBox = EntryWithLabel(self, "Mapping - Pin")
        self.mappingEndpointBox = EntryWithLabel(self, "Mapping - Endpoint")
        self.mappingPinBox.grid(sticky='e')
        self.mappingEndpointBox.grid(sticky='e')

        self.delButton = tk.Button(self, text="Delete this mapping", bg='red', width=40, command= lambda:self.delete())
        self.delButton.grid()

    def delete(self):
        self.grid_forget()
        self.destroy()

    def getEntryValue(self):
        output = dict()
        output['name'] = self.mappingPinBox.getEntryValue()
        output['endpoint'] = self.mappingEndpointBox.getEntryValue()
        return output

    def setEntryValue(self, value):
        self.mappingPinBox.setEntryValue(value['name'])
        self.mappingEndpointBox.setEntryValue(value['endpoint'])

class EndpointEntry(tk.Frame):
    def __init__(self, parent,  *args, **kwargs):
        tk.Frame.__init__(self, parent,  *args, **kwargs)
        self.nameBox = EntryWithLabel(self, "Name")
        self.outputBox = EntryWithLabel(self, "Output")
        self.rangeBox = EntryWithLabel(self, "Range")
        self.nameBox.grid(sticky = 'e')
        self.outputBox.grid(sticky = 'e')
        self.rangeBox.grid(sticky = 'e')
        tk.Button(self, text="Delete this endpoint", bg='red', width=40, command= lambda:self.delete()).grid()

    def delete(self):
        self.grid_forget()
        self.destroy()

    def getEntryValue(self):
        output = dict()
        output['name'] = self.nameBox.getEntryValue()
        output['output'] = self.outputBox.getEntryValue()
        output['range'] = self.rangeBox.getEntryValue()
        return output

    def setEntryValue(self, value):
        print("endpoint entries were set")
        self.nameBox.setEntryValue(value['name'])
        self.outputBox.setEntryValue(value['output'])
        self.rangeBox.setEntryValue(value['range'])

class EndpointListEntry(tk.Frame):
    def __init__(self, parent):
         tk.Frame.__init__(self, parent)
         tk.Label(parent, text="Endpoints").grid()
         self.endpointlistframe = tk.Frame(parent, bd=3, relief='groove')
         self.endpointlistframe.grid()
         tk.Button(parent, text="Add new endpoint", bg='green', width=80, command= lambda:self.addEndpoint()).grid()
         #self.addEndpoint()

    def addEndpoint(self):
        endpointEntry = EndpointEntry(self.endpointlistframe, bd=3, relief='groove')
        endpointEntry.grid()

    def getEntryValue(self):
        output = list()
        ep_entries = self.endpointlistframe.winfo_children()
        for ep in ep_entries:
            data = dict()
            data = ep.getEntryValue()
            output.append(data)
        return output

    def setEntryValue(self, value):
        for entry in value:
            print(entry['name'])
            endpointEntry = EndpointEntry(self.endpointlistframe)
            endpointEntry.grid()
            endpointEntry.setEntryValue(entry)


if __name__ == "__main__":
    pluginList = []
    app = SampleApp()
    app.mainloop()
