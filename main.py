import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, Tk
import io
import os
import glob
import sys
import re
import pyang
from pyang import plugin
from pyang import error
from pyang import util
from pyang import hello
from pyang import context
from pyang import repository
from pyang import statements
from pyang import syntax

class YangExplorer(tk.Frame):
    def __init__(self, root):
        self.yangModule=None
        self.yangModuleList = None
        self.filePath=''
        self.folderPath=''
        self.initial_dir='.'
        self.root = root
        self.initUI()

    def initUI(self):
        # Configure the root object for the YangExplorer
        self.root.geometry("1024x500")
        self.root.title("YangExplorer")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Menubar
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", accelerator='Ctrl+O', command=self.selectYangFileCmd)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(background="white", menu=menubar)

        # 2nd frame
        self.secondFrame = tk.Frame(self.root, width=200, heigh=10)
        self.secondFrame.grid(column=0, row=1, sticky='nsew')
        self.secondFrame.config(background="white")

        # Define the different GUI widgets
        self.pathLabel = tk.Label(self.secondFrame, text="", width=100, fg='blue')
        self.pathLabel.grid(row=0, column=0, sticky='nsew')
        self.buttonOpenFile = tk.Button(self.secondFrame, text="Open File", command=self.selectYangFileCmd)
        self.buttonOpenFile.grid(row=0, column=1, sticky='nsew')
        self.buttonReload = tk.Button(self.secondFrame, text="File Reload", command=self.ReloadYangFileCmd)
        self.buttonReload.grid(row=0, column=2, sticky='nsew')
        self.folderLabel = tk.Label(self.secondFrame, text="", width=100, fg='blue')
        self.folderLabel.grid(row=1, column=0, sticky='nsew')
        self.buttonOpenFolder = tk.Button(self.secondFrame, text="Open Folder", command=self.selectFolderCmd)
        self.buttonOpenFolder.grid(row=1, column=1, sticky='nsew')
        self.buttonFolderReload = tk.Button(self.secondFrame, text="Folder Reload", command=self.ReloadFolderCmd)
        self.buttonFolderReload.grid(row=1, column=2, sticky='nsew')

        # Set the treeview
        self.tree = ttk.Treeview(self.root, columns=('Element', 'Schema', 'DataType'))

        ysb = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=ysb.set)
        ysb.grid(row=0, column=12, sticky='ns')

        self.tree.grid(row=0, column=0, sticky='nswe')
        self.tree.heading('#0', text='Element')
        self.tree.heading('#1', text='Schema')
        self.tree.heading('#2', text='DataType')
        self.tree.heading('#3', text='Path')

    def loadYangFile(self):
        filename = self.filePath
        path = '.'
        repos = repository.FileRepository(path)
        ctx = context.Context(repos)
        fd = io.open(filename, "r", encoding="utf-8")
        text = fd.read()
        m = syntax.re_filename.search(filename)
        if m is not None:
            name, rev, in_format = m.groups()
            name = os.path.basename(name)
            module = ctx.add_module(filename, text, in_format, name, rev, expect_failure_error=False)
        else:
            module = ctx.add_module(filename, text)
        ctx.validate()
        return module

    def loadYangFolder(self):
        modules = []
        path = '.'
        repos = repository.FileRepository(path)
        ctx = context.Context(repos)
        for filename in glob.glob(self.folderPath + '/*.yang'):
            filename = os.path.abspath(filename)
            fd = io.open(filename, "r", encoding="utf-8")
            text = fd.read()
            m = syntax.re_filename.search(filename)
            module = None
            if m is not None:
                name, rev, in_format = m.groups()
                name = os.path.basename(name)
                module = ctx.add_module(filename, text, in_format, name, rev, expect_failure_error=False)
            else:
                module = ctx.add_module(filename, text)
            if module is not None:
                modules.append(module)
        ctx.validate()
        return modules

    def loadYangToTree(self):
        if self.filePath == '':
            return None
        self.yangModule = self.loadYangFile()
        if self.yangModule == None:
            return 0
        self.tree.delete(*self.tree.get_children())
        self.buildTreeChild('', self.yangModule)
        self.expandAll()

    def loadYangFolderToTree(self):
        if self.folderPath == '':
            return None
        self.yangModuleList = self.loadYangFolder()
        if self.yangModuleList == None:
            return 0
        self.tree.delete(*self.tree.get_children())
        for yangmod in self.yangModuleList:
            self.buildTreeChild('', yangmod)
        self.expandAll()

    def getAllChildren(self, tree, item=""):
        children = tree.get_children(item)
        for child in children:
            children += self.getAllChildren(tree, child)
        return children

    def expandAll(self):
        for item in self.getAllChildren(self.tree):
            self.tree.item(item, open=True)

    def buildTreeChild(self, id1, item1):
        t = item1.search_one('type')
        if t is None:
            t = ''
        id2 = self.tree.insert(id1, 'end', iid=None, text=item1.arg, values=(item1.keyword, t))
        if hasattr(item1, 'i_children'):
            chs = [ch for ch in item1.i_children if ch.keyword in statements.data_definition_keywords]
            for item2 in chs:
                self.buildTreeChild(id2, item2)

    def selectYangFileCmd(self):
        self.filePath = filedialog.askopenfilename(initialdir=self.initial_dir, filetypes=[("Yang files", "*.yang")])
        self.pathLabel['text'] = self.filePath
        self.initial_dir = os.path.dirname(os.path.abspath(self.filePath))
        self.loadYangToTree()

    def selectFolderCmd(self):
        self.folderPath = filedialog.askdirectory(initialdir=self.initial_dir, title='Please select a folder')
        self.folderLabel['text'] = self.folderPath
        self.initial_dir = os.path.dirname(os.path.abspath(self.folderPath))
        self.loadYangFolderToTree()

    def ReloadYangFileCmd(self):
        self.loadYangToTree()

    def ReloadFolderCmd(self):
        self.loadYangFolderToTree()

app = YangExplorer(tk.Tk())
app.root.mainloop()

