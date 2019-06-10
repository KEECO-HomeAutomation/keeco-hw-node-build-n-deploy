# Multi-frame tkinter application v2.3
import tkinter as tk
from tkinter import ttk
import json
import errno
import shutil
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
        tk.Button(self, text="Select Plug-Ins", width=60, command=lambda: master.switch_frame(PlugInSelectPage)).grid()
        tk.Button(self, text="Build Application", width=60, command=lambda: master.switch_frame(BuildPage)).grid()
        tk.Button(self, text="Deploy Application", width=60, command=lambda: master.switch_frame(DeployPage)).grid()
        tk.Button(self, text="Configuration", width=60, command=lambda: master.switch_frame(ConfigPage)).grid()
        tk.Label(self, text="Advanced Features").grid()
        tk.Button(self, text="Create Plug-Ins", width=60, command=lambda: master.switch_frame(PlugInCreatePage)).grid()

class PlugInSelectPage(tk.Frame):
    def openPlugin(self, lb):
        DirPath = self.pluginDirPath
        CurrSel = lb.get(lb.curselection())
        selectedPlugIn = join(DirPath, CurrSel)
        text = tk.Text(self)
        text.insert('insert', selectedPlugIn)
        text.grid(side="bottom", pady=10)

    def __init__(self, master):
        if (isfile('settings.json')):
            with open('settings.json') as json_file:
                self.data = json.load(json_file)
            self.pluginDirPath = self.data['pluginFolderPath']
        else:
            self.pluginDirPath = dirname(realpath(__file__))
        tk.Frame.__init__(self, master)
        tk.Label(self, text="PlugIn Selector").grid()
        tk.Button(self, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).grid()
        lb = tk.Listbox(self, width=100)
        avalPlugins = [f for f in listdir(self.pluginDirPath) if isfile(join(self.pluginDirPath, f))]
        for plugin in avalPlugins:
            lb.insert(0, plugin)
        lb.grid()
        tk.Button(self, text="Use Selected PlugIn", command=lambda: self.openPluginWindow(lb)).grid()


    def openPluginWindow(self, lb):
        DirPath = self.pluginDirPath
        CurrSel = lb.get(lb.curselection())
        selectedPlugIn = join(DirPath, CurrSel)
        pluginData = dict()
        with open(selectedPlugIn) as plugin_file:
            pluginData = json.load(plugin_file)
        t = tk.Toplevel(self)
        t.title('Enter parameters for selected PlugIn')
        dynamicEntries = []
        for var in pluginData['Variables']:
            entry = EntryWithLabel(t, var['Description'])
            dynamicEntries.append(entry)
            entry.grid()
            print(var['Name'])
            print(var['Description'])
            print(var['Variable Initialisation'])
        self.b = tk.Button(t, text="Apply parameters and Add plugin to project", command=lambda: self.addPluginToList(dynamicEntries, pluginData, selectedPlugIn))
        self.b.grid()

    def addPluginToList(self, entries, plugindata, path):
        tempPluginDataWithVars = dict()
        tempPluginDataWithVars['pluginPath'] = path
        Vars = []
        tempPluginList = []
        for e, p in zip(entries, plugindata['Variables']):
            var = dict()
            var['Alias'] = e.getEntryValue()
            var['Name'] = p['Name']
            var['Description'] = p['Description']
            var['Variable Initialisation'] = p['Variable Initialisation']
            Vars.append(var)
        tempPluginDataWithVars['Variables'] = Vars
        tempPluginDataWithVars['MQTT Subscriptions'] = plugindata['MQTT Subscriptions']
        tempPluginDataWithVars['Includes'] = plugindata['Includes']
        tempPluginDataWithVars['Init'] = plugindata['Init']
        tempPluginDataWithVars['Publish'] = plugindata['Publish']
        tempPluginDataWithVars['ReadInput'] = plugindata['ReadInput']
        tempPluginDataWithVars['Setoutput'] = plugindata['Setoutput']
        tempPluginDataWithVars['IO Type'] = plugindata['IO Type']
        tempPluginDataWithVars['Dependencies'] = plugindata['Dependencies']

        if (isfile('temp_plugins.json')):
            with open('temp_plugins.json') as temp_plugin_file:
                tempPluginList = json.load(temp_plugin_file)
        tempPluginList.append(tempPluginDataWithVars)
        with open('temp_plugins.json', 'w') as temp_plugin_file:
            json.dump(tempPluginList, temp_plugin_file)


class BuildPage(tk.Frame):
    def deletePlugin(self, tree):
        selected_item = tree.selection()[0]
        print(tree.item(selected_item))
        print(tree.index(selected_item))
        print(tree.item(tree.parent(selected_item)))

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

    def changeNameToAlias(self, src, vars):
        result = src
        for var in vars:
            result = result.replace(var['Name'],var['Alias'])
        return result

    def generateVarInitString(self, vars):
        result = ""
        for var in vars:
            result = result + var['Variable Initialisation'].replace(var['Name'],var['Alias']) + "\r\n"
        return result

    def replaceKeywordWithCodeMQTT(self, src, keyword, array):
        tempreplacement = ""
        for element in array[:-1]:
            tempreplacement = tempreplacement + element + ',' + "\r\n"
        tempreplacement = tempreplacement + array[-1] + "\r\n"
        num_of_MQTT_topics = tempreplacement.count(',')
        result = src.replace(keyword,tempreplacement)
        result = result.replace("int mqttSubTopicCount = 0;", "int mqttSubTopicCount = " + str(num_of_MQTT_topics+1) + ";")
        return result


    def replaceKeywordWithCode(self, src, keyword, array):
        tempreplacement = ""
        for element in array:
            tempreplacement = tempreplacement + element + "\r\n"
        result = src.replace(keyword,tempreplacement)
        return result

    def generateCode(self):
        includes = []
        var_init = []
        mqtt_sub = []
        init = []
        publish = []
        readinput = []
        setoutput = []
        dependencies = []

        with open('settings.json') as json_file:
            self.settings_data = json.load(json_file)
        template_path, template_lastfolder = split(self.settings_data['templateFolderPath'])
        fullResultFolderPath = join(self.settings_data['resultFolderPath'],template_lastfolder)

        if isdir(fullResultFolderPath):
            shutil.rmtree(fullResultFolderPath)
        else:
            mkdir(fullResultFolderPath)
        self.copy(self.settings_data['templateFolderPath'], fullResultFolderPath)
        manage_IO_Path = join(fullResultFolderPath, 'Manage_IO.ino')
        MQTT_Path = join(fullResultFolderPath, 'MQTT.ino')

        with open(manage_IO_Path) as manageIO_file:
            manageIO_content = manageIO_file.read()

        with open(MQTT_Path) as MQTT_file:
            MQTT_content = MQTT_file.read()

        with open('temp_plugins.json') as temp_plugin_file:
            PluginList = json.load(temp_plugin_file)

        for plugin in PluginList:
            includes.append(plugin['Includes'])
            var_init.append(self.generateVarInitString(plugin['Variables']))
            mqtt_sub.append(self.changeNameToAlias(plugin['MQTT Subscriptions'],plugin['Variables']))
            init.append(self.changeNameToAlias(plugin['Init'],plugin['Variables']))
            publish.append(self.changeNameToAlias(plugin['Publish'],plugin['Variables']))
            readinput.append(self.changeNameToAlias(plugin['ReadInput'],plugin['Variables']))
            setoutput.append(self.changeNameToAlias(plugin['Setoutput'],plugin['Variables']))
            dependencies.append(plugin['Dependencies'])

        MQTT_content = self.replaceKeywordWithCodeMQTT(MQTT_content, "//@mqttSubTopics@", mqtt_sub)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@includes@", includes)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@globalvars@", var_init)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@initIOcode@", init)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@readIOcode@", readinput)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@publishIOcode@", publish)
        manageIO_content = self.replaceKeywordWithCode(manageIO_content, "//@setOutputscode@", setoutput)

        with open(manage_IO_Path, "w") as f:
            f.write(manageIO_content)
        with open(MQTT_Path, "w") as f:
            f.write(MQTT_content)
        print(MQTT_content)
        print(manageIO_content)
        print("Code has been created successfully!")

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

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Builder").grid()
        tk.Button(self, text="Return to Main Page", width=60,
                  command=lambda: master.switch_frame(MainPage)).grid()
        if (isfile('temp_plugins.json')):
            with open('temp_plugins.json') as temp_plugin_file:
                self.tempPluginList = json.load(temp_plugin_file)
        self.tree = ttk.Treeview(self, height=20, selectmode='browse')
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.vsb.grid()
        self.tree.configure(yscrollcommand=self.vsb.set)

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
                self.tree.insert(self.treeitems[idx], "end", text=var['Name'], values=(var['Alias'],"",""))
        self.tree.grid()
        tk.Button(self, text="Delete Selected Plugin", width=60, command=lambda: self.deletePlugin(self.tree)).grid()
        tk.Button(self, text="Generate Code", width=60, command=lambda: self.generateCode()).grid()
        tk.Button(self, text="Build Wemos Binary", width=60, command=lambda: self.buildBinary()).grid()


class DeployPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Deployment").grid()
        tk.Button(self, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).grid()

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

        self.canvas = tk.Canvas(self, bd=0, width=1024, height=768)
        self.frame_in_canvas = tk.Frame(self.canvas)
        self.variables_frame = tk.Frame(self.frame_in_canvas)
        self.dependencies_frame = tk.Frame(self.frame_in_canvas)

        self.yscrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview )
        self.canvas.configure(yscrollcommand=self.yscrollbar.set)

        self.yscrollbar.grid(row=0, column=1, sticky='N'+'S')
        self.canvas.grid(row=0, column=0, sticky='N'+'S'+'E'+'W')
        self.canvas_window_id = self.canvas.create_window(0, 0, window=self.frame_in_canvas, anchor='nw')

        self.frame_in_canvas.bind("<Configure>", self.onFrameConfigure)

        tk.Label(self.frame_in_canvas, text="Create PlugIn").grid(row=0, column=0)
        tk.Button(self.frame_in_canvas, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).grid(row=1, column=0)
        tk.Button(self.frame_in_canvas, text="Add Variable", command=lambda: self.addVariable(self.variables_frame)).grid(row=2, column=0)
        tk.Label(self.frame_in_canvas, text="Includes - Add complete include line, for example: #include <ESP8266WiFi.h> \r You can add multiple include lines as well.").grid()
        self.includesEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.includesEntry.grid()
        self.variables_frame.grid()
        self.addVariable(self.variables_frame)
        tk.Label(self.frame_in_canvas, text="MQTT Subscriptions - Add your MQTT Subscription topics here. If multiple topics are to be included use a ,(comma) to seperate them and make sure not to put a \",\" after the last one! \r Topics should be included in this format: \" node/UUID_PLACEHOLDER/@TOPIC@ \" - where \"@TOPIC@\" is your symbol for the actual topic in the variable definitions. \r The \" UUID_PLACEHOLDER \" will be replaced on the KEECO HW Node in run-time as the UUID is stored in the device's EEPROM").grid()
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
        tk.Label(self.frame_in_canvas, text="Set Output - Place your code here to set outputs. Code here will be called in a function which is a callback \r function called when a new MQTT message is detected for any of the subscribed topics. \r The code below is placed in function whose signature is: \"setOutputs(char* topic, byte* payload, unsigned int length\")").grid()
        self.setOutputEntry = tkst.ScrolledText(self.frame_in_canvas, width=100, height=5)
        self.setOutputEntry.grid()
        tk.Label(self.frame_in_canvas, text="I/O Type - Define the Template Name how this I/O should appear in your KEECO System. See details on GitHub - keeco-hub!").grid()
        self.ioType = tk.StringVar()
        self.ioTypeEntry = tk.Entry(self.frame_in_canvas, textvariable=self.ioType, width=100 )
        self.ioTypeEntry.grid()
        tk.Label(self.frame_in_canvas, text="Dependenices - Required dependencies for your plugin will be automatically installed. \r Use the name format of the requiered library how it appears with arduino-cli lib list - replace _(underscores) with space ").grid()
        self.dependencies_frame.grid()
        self.addDependency(self.dependencies_frame)
        tk.Button(self.frame_in_canvas, text="Add Dependency", command=lambda: self.addDependency(self.dependencies_frame)).grid()

    def onFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def addVariable(self, parent):
        self.variables.append(VariableTextboxes(parent, self.variables))
        self.variables[-1].grid()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def addDependency(self, parent):
        self.dependencies.append(DependencyEntry(parent, self.dependencies))
        self.dependencies[-1].grid()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


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
        print(str(self.var.get()))
        return str(self.var.get())
    def setEntryValue(self, value):
        self.var.set(value)

class VariableTextboxes(tk.Frame):
    def __init__(self, parent, varlist):
        tk.Frame.__init__(self, parent)
        self.l1 = tk.Label(self, text="Variable Name - Choose a unique symbol that will be replaced by User given alias, for example: @var@ ")
        self.l2 = tk.Label(self, text="Variable Description - This text will be displayed when asking for user input for this variable")
        self.l3 = tk.Label(self, text="Variable Initialisation - Place variable initialisation code here if needed (a variable can be a user provided alias only in your code)")
        self.name = tk.StringVar()
        self.nameBox = tk.Entry(self, textvariable=self.name, width=100)
        self.description = tk.StringVar()
        self.descriptionBox = tk.Entry(self, textvariable=self.description, width=100)
        self.variableInitBox = tkst.ScrolledText(master = self, wrap   = 'word', width  = 100, height = 10)
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
        self.result['Name'] = self.name.get()
        self.result['Description'] = self.description.get()
        self.result['Variable Initialisation'] = self.variableInitBox.get(1.0, tk.END)
        return self.result

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
        self.name.set(value)

if __name__ == "__main__":
    pluginList = []
    app = SampleApp()
    app.mainloop()
