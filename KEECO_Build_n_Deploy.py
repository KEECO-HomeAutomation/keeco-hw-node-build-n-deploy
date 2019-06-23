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
import classes.CodeGeneratorClass as cgc
import classes.BinaryBuilderClass as bbc
import classes.CustomWidgetClasses as cwc


class MainApp(tk.Tk):
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
        print("___Main page has been loaded successfully")

class PlugInManagerPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.varFrameObjs = list()
        self.variablesFrame = tk.Frame(self)

        if (isfile('settings.json')):
            with open('settings.json') as json_file:
                self.data = json.load(json_file)
            self.pluginDirPath = self.data['pluginFolderPath']
        else:
            self.pluginDirPath = dirname(realpath(__file__))

        tk.Label(self, text="Plug-in Selector").grid()
        tk.Button(self, text="Return to Main Page", width=80, command=lambda: master.switch_frame(MainPage)).grid()
        tk.Label(self, text="Plug-ins added to this project:").grid()
        self.variablesFrame.grid()
        tk.Button(self, text="Add Plugin", bg='green', width=80, command=lambda: self.addPlugin(self.variablesFrame)).grid()
        tk.Button(self, text="Save Project", width=80, command=lambda: self.saveProject(self.varFrameObjs)).grid()
        self.loadVarsAtStart(self.variablesFrame)
        print("____Plug-in manager page has been loaded successfully")

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
            entry = cwc.EntryWithLabel(varFrame, var['Description'])
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
                    entry = cwc.EntryWithLabel(varFrame, var['Description'])
                    if (var['Name'] != ""):
                        entry.grid(sticky='e')
                        entry.setEntryValue(var['Alias'])
                tk.Button(varFrame, text="Delete this Plug-in", bg='red', width=60, command= lambda:self.delete(varFrame, self.varFrameObjs)).grid()
                self.varFrameObjs.append(varFrame)
                varFrame.grid(sticky='e')
        print("____Plug-ins have been loaded from temp plugin file")

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
        print("____Plugins are saved to temp plugin file")

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

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.required_libs = list()
        self.cg = cgc.CodeGenerator()
        self.bb = bbc.BinaryBuilder()

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
            #print(str(idx) + self.filename)
            self.treeitems.append(self.tree.insert(self.root_tree_node, idx, text=self.filename, values=("",plugin['IO Type'], plugin['Dependencies']), open='true'))
            for var in plugin["Variables"]:
                #print(str(idx) + var['Name'] + var['Alias'])
                if (var['Name'] != ""):
                    self.tree.insert(self.treeitems[idx], "end", text=var['Name'], values=(var['Alias'],"",""))
        self.tree.grid()
        tk.Button(self, text="Delete Selected Plugin", width=60, command=lambda: self.deletePlugin(self.tree)).grid()
        tk.Button(self, text="Check Dependencies", width=60, command=lambda: self.bb.installDependencies()).grid()
        tk.Button(self, text="Generate Code", width=60, command=lambda: self.cg.fullCodeGenProcess(self.hwnode_name.get())).grid()
        tk.Button(self, text="Build Wemos Binary", width=60, command=lambda: self.bb.fullBuildProcess()).grid()
        print("____Build page has been loaded successfully")

class DeployPage(tk.Frame):
    def __init__(self, master):
        self.wemosSerialPort = ""
        self.portList = list()
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Deployment").grid()
        tk.Button(self, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).grid()
        tk.Button(self, text="Select Serial Port", command=lambda: self.openSerialSelectWindow()).grid()
        tk.Button(self, text="Upload binary and SPIFFS file", command=lambda: self.uploadProgram()).grid()
        print("____Deploy page has been loaded successfully")


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
        self.selButton = tk.Button(t, text="Select Serial Port", command=lambda: self.setSerialPort(self.lb))
        self.selButton.grid()

    def setSerialPort(self, lb):
        self.wemosSerialPort = lb.get(lb.curselection())

    def uploadProgram(self):
        with open('settings.json') as json_file:
            settings_data = json.load(json_file)

        print ("esptool.exe --port " + self.wemosSerialPort + " --baud 921600 write_flash 0x200000 " +  join(settings_data['buildFolderPath'],"out.spiffs"))
        res = system("esptool.exe --port " + self.wemosSerialPort + " --baud 921600 write_flash 0x200000 " +  join(settings_data['buildFolderPath'],"out.spiffs"))

        print ("esptool.exe --port " + self.wemosSerialPort + " --baud 921600 write_flash 0x000000 " +  join(settings_data['buildFolderPath'],"KEECO_hwNode_ESP8266.ino.bin"))
        res = system("esptool.exe --port " + self.wemosSerialPort + " --baud 921600 write_flash 0x000000 " +  join(settings_data['buildFolderPath'],"KEECO_hwNode_ESP8266.ino.bin"))

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
        self.pluginPath = cwc.EntryWithBrowse(self, "Plugin Path")
        self.templateFolderPath = cwc.EntryWithBrowse(self, "Template Path")
        self.resultFolderPath = cwc.EntryWithBrowse(self, "Result Path")
        self.buildFolderPath = cwc.EntryWithBrowse(self, "Build Path")

        self.pluginPath.grid(row=4, sticky="e")
        self.templateFolderPath.grid(row=5, sticky="e")
        self.resultFolderPath.grid(row=6, sticky="e")
        self.buildFolderPath.grid(row=7, sticky="e")

        self.pluginPath.setEntryValue(self.data['pluginFolderPath'])
        self.templateFolderPath.setEntryValue(self.data['templateFolderPath'])
        self.resultFolderPath.setEntryValue(self.data['resultFolderPath'])
        self.buildFolderPath.setEntryValue(self.data['buildFolderPath'])
        print("____Configuration page has been loaded successfully")

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
        self.templatebox = cwc.TemplatesEntry(self.templates_frame)
        self.templatebox.grid()
        self.endpointlist_frame.grid()
        self.endpointbox = cwc.EndpointListEntry(self.endpointlist_frame)
        self.endpointbox.grid()
        print("____Plug-in configurator page has been loaded successfully")


    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def addVariable(self, parent):
        self.variables.append(cwc.VariableTextboxes(parent, self.variables, bd =3, relief='groove'))
        self.variables[-1].grid()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def addDependency(self, parent):
        self.dependencies.append(cwc.DependencyEntry(parent, self.dependencies))
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
                self.variables.append(cwc.VariableTextboxes(self.variables_frame, self.variables))
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
                self.dependencies.append(cwc.DependencyEntry(self.dependencies_frame, self.dependencies))
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


if __name__ == "__main__":
    pluginList = []
    app = MainApp()
    app.mainloop()
