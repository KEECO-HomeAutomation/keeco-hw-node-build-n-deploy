import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import tkinter.scrolledtext as tkst


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
