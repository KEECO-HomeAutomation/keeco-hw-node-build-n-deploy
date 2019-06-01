# Multi-frame tkinter application v2.3
import tkinter as tk
import json
from os import listdir
from os.path import isfile, join, dirname, realpath
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
        tk.Button(self, text="Select PlugIns",
                  command=lambda: master.switch_frame(PlugInSelectPage)).pack()
        tk.Button(self, text="Build Application",
                  command=lambda: master.switch_frame(BuildPage)).pack()
        tk.Button(self, text="Deploy Application",
                  command=lambda: master.switch_frame(DeployPage)).pack()
        tk.Button(self, text="Configuration",
                  command=lambda: master.switch_frame(ConfigPage)).pack()

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
        tk.Button(self, text="Return to Main Page",
                  command=lambda: master.switch_frame(MainPage)).pack()
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
        self.pluginData = {'username': 'sammy-shark', 'followers': 987, 'online': True}
        with open(selectedPlugIn) as plugin_file:
            self.pluginData = json.load(plugin_file)
        t = tk.Toplevel(self)
        t.title('Enter parameters for selected PlugIn')
        self.dynamicEntries = []
        for var in self.pluginData['Variables']:
            entry = EntryWithLabel(t, var['Description'])
            self.dynamicEntries.append(entry)
            entry.pack(anchor='e')
            print(var['Name'])
            print(var['Description'])
            print(var['Variable Initialisation'])

class BuildPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Builder").pack(side="top", fill="x", pady=10)
        tk.Button(self, text="Return to Main Page",
                  command=lambda: master.switch_frame(MainPage)).pack()

class DeployPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="App Deployment").pack(side="top", fill="x", pady=10)
        tk.Button(self, text="Return to Main Page",
                  command=lambda: master.switch_frame(MainPage)).pack()

class ConfigPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="Configuration").grid(row=0, column=0)
        tk.Button(self, text="Return to Main Page",
                  command=lambda: master.switch_frame(MainPage)).grid(row=1, column=0)
        tk.Button(self, text="Save Settings",
                  command=lambda: self.saveSettingsToFile()).grid(row=2, column=0)
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
        self.b = tk.Button(self, text="Browse",
                               command=lambda:self.var.set(filedialog.askdirectory()))
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
    app = SampleApp()
    app.mainloop()
