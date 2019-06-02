# Multi-frame tkinter application v2.3
import tkinter as tk
from tkinter import ttk
import json
import errno
import shutil
from os import listdir, mkdir
from os.path import isfile, isdir, join, dirname, realpath, split
from tkinter import filedialog

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
        tk.Label(self, text="KEECO HW Node App Generator v0.1").pack(side="top", fill="x", pady=10)
        tk.Button(self, text="Select PlugIns", command=lambda: master.switch_frame(PlugInSelectPage)).pack()
        tk.Button(self, text="Build Application", command=lambda: master.switch_frame(BuildPage)).pack()
        tk.Button(self, text="Deploy Application", command=lambda: master.switch_frame(DeployPage)).pack()
        tk.Button(self, text="Configuration", command=lambda: master.switch_frame(ConfigPage)).pack()

class PlugInSelectPage(tk.Frame):
    def openPlugin(self, lb):
        DirPath = self.pluginDirPath
        CurrSel = lb.get(lb.curselection())
        selectedPlugIn = join(DirPath, CurrSel)
        text = tk.Text(self)
        text.insert('insert', selectedPlugIn)
        text.pack(side="bottom", pady=10)

    def __init__(self, master):
        if (isfile('settings.json')):
            with open('settings.json') as json_file:
                self.data = json.load(json_file)
            self.pluginDirPath = self.data['pluginFolderPath']
        else:
            self.pluginDirPath = dirname(realpath(__file__))
        tk.Frame.__init__(self, master)
        tk.Label(self, text="PlugIn Selector").pack(side="top", fill="x", pady=10)
        tk.Button(self, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).pack()
        lb = tk.Listbox(self)
        avalPlugins = [f for f in listdir(self.pluginDirPath) if isfile(join(self.pluginDirPath, f))]
        for plugin in avalPlugins:
            lb.insert(0, plugin)
        lb.pack()
        tk.Button(self, text="Use Selected PlugIn", command=lambda: self.openPluginWindow(lb)).pack()

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
            entry.pack(anchor='e')
            print(var['Name'])
            print(var['Description'])
            print(var['Variable Initialisation'])
        self.b = tk.Button(t, text="Apply parameters and Add plugin to poject", command=lambda: self.addPluginToList(dynamicEntries, pluginData, selectedPlugIn))
        self.b.pack()

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
    def replaceKeywordWithCode(self, keyword, array):
        tempstring = ""
        for element in array:
            

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

        print(manage_IO_Path)
        print(MQTT_Path)

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

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Builder").pack(side="top", fill="x", pady=10)
        tk.Button(self, text="Return to Main Page",
                  command=lambda: master.switch_frame(MainPage)).pack()
        if (isfile('temp_plugins.json')):
            with open('temp_plugins.json') as temp_plugin_file:
                self.tempPluginList = json.load(temp_plugin_file)
        self.tree = ttk.Treeview(self, height=20, selectmode='browse')
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.vsb.pack(side='right', fill='y')
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
        self.tree.pack(side=tk.TOP,fill=tk.X)
        tk.Button(self, text="Delete Selected Plugin", command=lambda: self.deletePlugin(self.tree)).pack()
        tk.Button(self, text="Generate Code", command=lambda: self.generateCode()).pack()


class DeployPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Deployment").pack(side="top", fill="x", pady=10)
        tk.Button(self, text="Return to Main Page", command=lambda: master.switch_frame(MainPage)).pack()

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

        self.pluginPath.grid(row=4, sticky="w")
        self.templateFolderPath.grid(row=5, sticky="w")
        self.resultFolderPath.grid(row=6, sticky="w")
        self.buildFolderPath.grid(row=7, sticky="w")

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

class EntryWithBrowse(tk.Frame):
    def __init__(self, parent, Name):
        tk.Frame.__init__(self, parent)
        self.name = Name
        self.var = tk.StringVar()
        self.w = tk.Label(self, text=self.name)
        self.e = tk.Entry(self, textvariable=self.var)
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

if __name__ == "__main__":
    pluginList = []
    app = SampleApp()
    app.mainloop()
