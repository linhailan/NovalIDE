#----------------------------------------------------------------------------
# Name:         ExtensionService.py
# Purpose:      Extension Service for IDE
#
# Author:       Peter Yared
#
# Created:      5/23/05
# CVS-ID:       $ID:$
# Copyright:    (c) 2005-2006 ActiveGrid, Inc.
# License:      wxWindows License
#----------------------------------------------------------------------------

import wx
import wx.lib.pydocview
import MessageService
import ProjectEditor
import os
import os.path
import noval.util.xmlutils as xmlutils
import subprocess
import sys
import UnitTestDialog
import noval.util.sysutils as sysutilslib
import noval.util.fileutils as fileutils
import Service
from noval.dummy.userdb import UserDataDb
import GeneralOption
import noval.util.appdirs as appdirs
import noval.parser.utils as parserutils
import requests
from download import FileDownloader
import noval.tool.interpreter.Interpreter as Interpreter
import getpass
import noval.util.fileutils as fileutils
import which as whichpath
_ = wx.GetTranslation


#----------------------------------------------------------------------------
# Constants
#----------------------------------------------------------------------------
SPACE = 10
HALF_SPACE = 5


#----------------------------------------------------------------------------
# Classes
#----------------------------------------------------------------------------

class Extension:


    def __init__(self, menuItemName=None):
        self.menuItemName = menuItemName
        self.id = 0
        self.menuItemDesc = ''
        self.command = ''
        self.commandPreArgs = ''
        self.commandPostArgs = ''
        self.fileExt = None
        self.opOnSelectedFile = True


class ExtensionService(Service.BaseService):

    EXTENSIONS_KEY = "/AG_Extensions"

    def __init__(self):
        self.LoadExtensions()


    def __getExtensionKeyName(extensionName):
        return "%s/%s" % (ExtensionService.EXTENSIONS_KEY, extensionName)


    __getExtensionKeyName = staticmethod(__getExtensionKeyName)


    def LoadExtensions(self):
        self._extensions = []

        extensionNames = []
        config = wx.ConfigBase_Get()
        path = config.GetPath()
        try:
            config.SetPath(ExtensionService.EXTENSIONS_KEY)
            cont, value, index = config.GetFirstEntry()
            while cont:
                extensionNames.append(value)
                cont, value, index = config.GetNextEntry(index)
        finally:
            config.SetPath(path)

        for extensionName in extensionNames:
            extensionData = config.Read(self.__getExtensionKeyName(extensionName))
            if extensionData:
                extension = xmlutils.unmarshal(extensionData.encode('utf-8'))
                self._extensions.append(extension)


    def SaveExtensions(self):
        config = wx.ConfigBase_Get()
        config.DeleteGroup(ExtensionService.EXTENSIONS_KEY)
        for extension in self._extensions:
            config.Write(self.__getExtensionKeyName(extension.menuItemName), xmlutils.marshal(extension))


    def GetExtensions(self):
        return self._extensions


    def SetExtensions(self, extensions):
        self._extensions = extensions


    def CheckSumExtensions(self):
        return xmlutils.marshal(self._extensions)


    def InstallControls(self, frame, menuBar = None, toolBar = None, statusBar = None, document = None):
        toolsMenuIndex = menuBar.FindMenu(_("&Tools"))
        if toolsMenuIndex > -1:
            toolsMenu = menuBar.GetMenu(toolsMenuIndex)
        else:
            toolsMenu = wx.Menu()

        if toolsMenuIndex == -1:
            index = menuBar.FindMenu(_("&Run"))
            if index == -1:
                index = menuBar.FindMenu(_("&Project"))
            if index == -1:
                index = menuBar.FindMenu(_("&Format"))
            if index == -1:
                index = menuBar.FindMenu(_("&View"))
            menuBar.Insert(index + 1, toolsMenu, _("&Tools"))
            id = wx.NewId()
            toolsMenu.Append(id,_("&Terminator"))
            wx.EVT_MENU(frame, id, self.OpenTerminator)  

            id = wx.NewId()
            toolsMenu.Append(id,_("&UnitTest"))
            wx.EVT_MENU(frame, id, self.RunUnitTest)

            id = wx.NewId()
            toolsMenu.Append(id,_("&Interpreter"))
            wx.EVT_MENU(frame, id, self.OpenInterpreter)
        
        helpMenuIndex = menuBar.FindMenu(_("&Help"))
        helpMenu = menuBar.GetMenu(helpMenuIndex)
        start_index = 0
        if sysutilslib.isWindows():
            id = wx.NewId()
            helpMenu.Insert(0,id,_("&Python Help Document"))
            wx.EVT_MENU(frame, id, self.OpenPythonHelpDocument)
            start_index += 1

        id = wx.NewId()
        helpMenu.Insert(start_index,id,_("&Tips of Day"))
        wx.EVT_MENU(frame, id, self.ShowTipsOfDay)
        start_index += 1
        
        id = wx.NewId()
        helpMenu.Insert(start_index,id,_("&Visit Website"))
        wx.EVT_MENU(frame, id, self.GotoWebsite)
        
        id = wx.NewId()
        helpMenu.Insert(start_index,id,_("&Check for Updates"))
        wx.EVT_MENU(frame, id, self.CheckforUpdate)
        start_index += 1

        if self._extensions:
            if toolsMenu.GetMenuItems():
                toolsMenu.AppendSeparator()
            for ext in self._extensions:
                # Append a tool menu item for each extension
                ext.id = wx.NewId()
                toolsMenu.Append(ext.id, ext.menuItemName)
                wx.EVT_MENU(frame, ext.id, frame.ProcessEvent)
                wx.EVT_UPDATE_UI(frame, ext.id, frame.ProcessUpdateUIEvent)

    def ShowTipsOfDay(self,event):
        wx.GetApp().ShowTipfOfDay(True)
        
    def GotoWebsite(self,event):
        fileutils.start_file(UserDataDb.HOST_SERVER_ADDR)
        
    def CheckforUpdate(self,event):
        self.CheckAppUpdate()
        
    def CheckAppUpdate(self,ignore_error = False):
        api_addr = '%s/member/get_update' % (UserDataDb.HOST_SERVER_ADDR)
        config = wx.ConfigBase_Get()
        langId = GeneralOption.GetLangId(config.Read("Language",""))
        lang = wx.Locale.GetLanguageInfo(langId).CanonicalName
        app_version = sysutilslib.GetAppVersion()
        data = UserDataDb.get_db().RequestData(api_addr,arg = {'app_version':app_version,'lang':lang})
        if data is None:
            if not ignore_error:
                wx.MessageBox(_("could not connect to version server"),style=wx.OK|wx.ICON_ERROR)
            return
        #no update
        if data['code'] == 0:
            if not ignore_error:
                wx.MessageBox(data['message'])
        #have update
        elif data['code'] == 1:
            ret = wx.MessageBox(data['message'],_("Update Available"),wx.YES_NO |wx.ICON_QUESTION)
            if ret == wx.YES:
                new_version = data['new_version']
                download_url = '%s/member/download_app' % (UserDataDb.HOST_SERVER_ADDR)
                payload = dict(new_version = new_version,lang = lang,os_name=sys.platform)
                user_id = UserDataDb.get_db().GetUserId()
                if user_id:
                    payload.update({'member_id':user_id})
                req = requests.get(download_url,params=payload, stream=True)
                #print req.headers,"------------"
                #print req.url
                if 'Content-Length' not in req.headers:
                    data = req.json()
                    if data['code'] != 0:
                        wx.MessageBox(data['message'],style=wx.OK|wx.ICON_ERROR)
                else:
                    file_length = req.headers['Content-Length']
                    content_disposition = req.headers['Content-Disposition']
                    file_name = content_disposition[content_disposition.find(";") + 1:].replace("filename=","").replace("\"","")
                    file_downloader = FileDownloader(file_length,file_name,req,self.Install)
                    file_downloader.StartDownload()
        #other error
        else:
            if not ignore_error:
                wx.MessageBox(data['message'],style=wx.OK|wx.ICON_ERROR)
            
    def Install(self,app_path):
        if sysutilslib.isWindows():
            os.startfile(app_path)
        else:
            path = os.path.dirname(sys.executable)
            pip_path = os.path.join(path,"pip")
            cmd = "%s  -c \"from distutils.sysconfig import get_python_lib; print get_python_lib()\"" % (sys.executable,)
            python_lib_path = Interpreter.GetCommandOutput(cmd).strip()
            user = getpass.getuser()
            should_root = not fileutils.is_writable(python_lib_path,user)
            if should_root:
                cmd = "pkexec " + "%s install %s" % (pip_path,app_path)
            else:
                cmd = "%s install %s" % (pip_path,app_path)
            subprocess.call(cmd,shell=True)
            app_startup_path = whichpath.GuessPath("NovalIDE")
            #wait a moment to avoid single instance limit
            subprocess.Popen("/bin/sleep 2;%s" % app_startup_path,shell=True)
        wx.GetApp().MainFrame.OnExit(None)

    def OpenPythonHelpDocument(self,event):
        interpreter = wx.GetApp().GetCurrentInterpreter()
        if interpreter is None:
            return
        if interpreter.HelpPath == "":
            return
        os.startfile(interpreter.HelpPath)

    def OpenTerminator(self, event):
        if sysutilslib.isWindows():
            subprocess.Popen('start cmd.exe',shell=True)
        else:
            subprocess.Popen('gnome-terminal',shell=True)

    def RunUnitTest(self,event):
        cur_view = self.GetActiveView()
        if cur_view is None or not cur_view.IsUnitTestEnable():
            return
        dlg = UnitTestDialog.UnitTestDialog(wx.GetApp().GetTopWindow(),-1,_("UnitTest"),cur_view)
        if dlg.CreateUnitTestFrame():
            dlg.ShowModal()
        dlg.Destroy()

    def OpenInterpreter(self,event):
        interpreter = wx.GetApp().GetCurrentInterpreter()
        if interpreter is None:
            return
        try:
            if sysutilslib.isWindows():
                fileutils.start_file(interpreter.Path)
            else:
                cmd_list = ['gnome-terminal','-x','bash','-c',interpreter.Path]
                subprocess.Popen(cmd_list,shell = False)
        except Exception as e:
            wx.MessageBox(_("%s") % str(e),_("Open Error"),wx.OK|wx.ICON_ERROR,wx.GetApp().GetTopWindow())
        
    def ProcessEvent(self, event):
        id = event.GetId()
        for extension in self._extensions:
            if id == extension.id:
                self.OnExecuteExtension(extension)
                return True
        return False


    def ProcessUpdateUIEvent(self, event):
        id = event.GetId()
        for extension in self._extensions:
            if id == extension.id:
                if extension.fileExt:
                    doc = wx.GetApp().GetDocumentManager().GetCurrentDocument()
                    if doc and '*' in extension.fileExt:
                        event.Enable(True)
                        return True
                    if doc:
                        for fileExt in extension.fileExt:
                            if fileExt in doc.GetDocumentTemplate().GetFileFilter():
                                event.Enable(True)
                                return True
                        if extension.opOnSelectedFile and isinstance(doc, ProjectEditor.ProjectDocument):
                            filename = doc.GetFirstView().GetSelectedFile()
                            if filename:
                                template = wx.GetApp().GetDocumentManager().FindTemplateForPath(filename)
                                for fileExt in extension.fileExt:
                                    if fileExt in template.GetFileFilter():
                                        event.Enable(True)
                                        return True
                    event.Enable(False)
                    return False
        return False


    def OnExecuteExtension(self, extension):
        if extension.fileExt:
            doc = wx.GetApp().GetDocumentManager().GetCurrentDocument()
            if not doc:
                return
            if extension.opOnSelectedFile and isinstance(doc, ProjectEditor.ProjectDocument):
                filename = doc.GetFirstView().GetSelectedFile()
                if not filename:
                    filename = doc.GetFilename()
            else:
                filename = doc.GetFilename()
            ext = os.path.splitext(filename)[1]
            if not '*' in extension.fileExt:
                if not ext or ext[1:] not in extension.fileExt:
                    return
            cmds = [extension.command]
            if extension.commandPreArgs:
                cmds.append(extension.commandPreArgs)
            cmds.append(filename)
            if extension.commandPostArgs:
                cmds.append(extension.commandPostArgs)
            os.spawnv(os.P_NOWAIT, extension.command, cmds)

        else:
            cmd = extension.command
            if extension.commandPreArgs:
                cmd = cmd + ' ' + extension.commandPreArgs
            if extension.commandPostArgs:
                cmd = cmd + ' ' + extension.commandPostArgs
            f = os.popen(cmd)
            messageService = wx.GetApp().GetService(MessageService.MessageService)
            messageService.ShowWindow()
            view = messageService.GetView()
            for line in f.readlines():
                view.AddLines(line)
            view.GetControl().EnsureCaretVisible()
            f.close()


class ExtensionOptionsPanel(wx.Panel):


    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)

        extOptionsPanelBorderSizer = wx.BoxSizer(wx.VERTICAL)

        extOptionsPanelSizer = wx.BoxSizer(wx.HORIZONTAL)

        extCtrlSizer = wx.BoxSizer(wx.VERTICAL)
        extCtrlSizer.Add(wx.StaticText(self, -1, _("External Tools:")), 0, wx.BOTTOM, HALF_SPACE)
        self._extListBox = wx.ListBox(self, -1, style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.OnListBoxSelect, self._extListBox)
        extCtrlSizer.Add(self._extListBox, 1, wx.BOTTOM | wx.EXPAND, SPACE)
        buttonSizer = wx.GridSizer(cols=2, vgap=HALF_SPACE, hgap=HALF_SPACE)
        self._moveUpButton = wx.Button(self, -1, _("Move Up"))
        self.Bind(wx.EVT_BUTTON, self.OnMoveUp, self._moveUpButton)
        buttonSizer.Add(self._moveUpButton, 1, wx.EXPAND)
        self._moveDownButton = wx.Button(self, -1, _("Move Down"))
        self.Bind(wx.EVT_BUTTON, self.OnMoveDown, self._moveDownButton)
        buttonSizer.Add(self._moveDownButton, 1, wx.EXPAND)
        self._addButton = wx.Button(self, wx.ID_ADD)
        self.Bind(wx.EVT_BUTTON, self.OnAdd, self._addButton)
        buttonSizer.Add(self._addButton, 1, wx.EXPAND)
        self._deleteButton = wx.Button(self, wx.ID_DELETE, label=_("Delete")) # get rid of accelerator for letter d in "&Delete"
        self.Bind(wx.EVT_BUTTON, self.OnDelete, self._deleteButton)
        buttonSizer.Add(self._deleteButton, 1, wx.EXPAND)
        extCtrlSizer.Add(buttonSizer, 0, wx.ALIGN_CENTER)
        extOptionsPanelSizer.Add(extCtrlSizer, 0, wx.EXPAND)

        self._extDetailPanel = wx.Panel(self)
        staticBox = wx.StaticBox(self, label=_("Selected External Tool"))
        staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)

        extDetailSizer = wx.FlexGridSizer(cols=2, vgap=5, hgap=5)
        extDetailSizer.AddGrowableCol(1,1)

        extDetailSizer.Add(wx.StaticText(self._extDetailPanel, -1, _("Menu Item Name:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self._menuItemNameTextCtrl = wx.TextCtrl(self._extDetailPanel, -1, size = (-1, -1))
        extDetailSizer.Add(self._menuItemNameTextCtrl, 0, wx.EXPAND)
        self.Bind(wx.EVT_TEXT, self.SaveCurrentItem, self._menuItemNameTextCtrl)

        extDetailSizer.Add(wx.StaticText(self._extDetailPanel, -1, _("Menu Item Description:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self._menuItemDescTextCtrl = wx.TextCtrl(self._extDetailPanel, -1, size = (-1, -1))
        extDetailSizer.Add(self._menuItemDescTextCtrl, 0, wx.EXPAND)

        extDetailSizer.Add(wx.StaticText(self._extDetailPanel, -1, _("Command Path:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self._commandTextCtrl = wx.TextCtrl(self._extDetailPanel, -1, size = (-1, -1))
        findFileButton = wx.Button(self._extDetailPanel, -1, _("Browse..."))
        def OnBrowseButton(event):
            fileDlg = wx.FileDialog(self, _("Choose an Executable:"), style=wx.OPEN|wx.FILE_MUST_EXIST|wx.CHANGE_DIR)
            path = self._commandTextCtrl.GetValue()
            if path:
                fileDlg.SetPath(path)
            # fileDlg.CenterOnParent()  # wxBug: caused crash with wx.FileDialog
            if fileDlg.ShowModal() == wx.ID_OK:
                self._commandTextCtrl.SetValue(fileDlg.GetPath())
                self._commandTextCtrl.SetInsertionPointEnd()
                self._commandTextCtrl.SetToolTipString(fileDlg.GetPath())
            fileDlg.Destroy()
        wx.EVT_BUTTON(findFileButton, -1, OnBrowseButton)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(self._commandTextCtrl, 1, wx.EXPAND)
        hsizer.Add(findFileButton, 0, wx.LEFT, HALF_SPACE)
        extDetailSizer.Add(hsizer, 0, wx.EXPAND)

        extDetailSizer.Add(wx.StaticText(self._extDetailPanel, -1, _("Command Pre Args:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self._commandPreArgsTextCtrl = wx.TextCtrl(self._extDetailPanel, -1, size = (-1, -1))
        extDetailSizer.Add(self._commandPreArgsTextCtrl, 0, wx.EXPAND)

        extDetailSizer.Add(wx.StaticText(self._extDetailPanel, -1, _("Command Post Args:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self._commandPostArgsTextCtrl = wx.TextCtrl(self._extDetailPanel, -1, size = (-1, -1))
        extDetailSizer.Add(self._commandPostArgsTextCtrl, 0, wx.EXPAND)

        extDetailSizer.Add(wx.StaticText(self._extDetailPanel, -1, _("File Extensions:")), flag=wx.ALIGN_CENTER_VERTICAL)
        self._fileExtTextCtrl = wx.TextCtrl(self._extDetailPanel, -1, size = (-1, -1))
        self._fileExtTextCtrl.SetToolTipString(_("""For example: "txt, text" (comma separated) or "*" for all files"""))
        extDetailSizer.Add(self._fileExtTextCtrl, 0, wx.EXPAND)

        self._selFileCtrl = wx.CheckBox(self._extDetailPanel, -1, _("Operate on Selected File"))
        extDetailSizer.Add(self._selFileCtrl, 0, wx.ALIGN_CENTER_VERTICAL|wx.TOP, SPACE)
        self._selFileCtrl.SetToolTipString(_("If focus is in the project, instead of operating on the project file, operate on the selected file."))

        self._extDetailPanel.SetSizer(extDetailSizer)
        staticBoxSizer.Add(self._extDetailPanel, 1, wx.ALL|wx.EXPAND, SPACE)

        extOptionsPanelSizer.Add(staticBoxSizer, 1, wx.LEFT|wx.EXPAND, SPACE)

        extOptionsPanelBorderSizer.Add(extOptionsPanelSizer, 1, wx.ALL|wx.EXPAND, SPACE)
        self.SetSizer(extOptionsPanelBorderSizer)

        if self.PopulateItems():
            self._extListBox.SetSelection(0)
        self.OnListBoxSelect()

        self.Layout()

        parent.AddPage(self, _("External Tools"))


    def OnOK(self, optionsDialog):
        self.SaveCurrentItem()
        extensionsService = wx.GetApp().GetService(ExtensionService)
        extensionsService.SetExtensions(self._extensions)
        extensionsService.SaveExtensions()
        if extensionsService.CheckSumExtensions() != self._oldExtensions:  # see PopulateItems() note about self._oldExtensions
            msgTitle = wx.GetApp().GetAppName()
            if not msgTitle:
                msgTitle = _("Document Options")
            wx.MessageBox(_("Extension changes will not appear until the application is restarted."),
                          msgTitle,
                          wx.OK | wx.ICON_INFORMATION,
                          self.GetParent())


    def PopulateItems(self):
        extensionsService = wx.GetApp().GetService(ExtensionService)
        import copy
        self._extensions = copy.deepcopy(extensionsService.GetExtensions())
        self._oldExtensions = extensionsService.CheckSumExtensions()  # wxBug:  need to make a copy now since the deepcopy reorders fields, so we must compare the prestine copy with the modified copy
        for extension in self._extensions:
            self._extListBox.Append(extension.menuItemName, extension)
        self._currentItem = None
        self._currentItemIndex = -1
        return len(self._extensions)


    def OnListBoxSelect(self, event=None):
        self.SaveCurrentItem()
        if self._extListBox.GetSelection() == wx.NOT_FOUND:
            self._currentItemIndex = -1
            self._currentItem = None
            self._deleteButton.Enable(False)
            self._moveUpButton.Enable(False)
            self._moveDownButton.Enable(False)
        else:
            self._currentItemIndex = self._extListBox.GetSelection()
            self._currentItem = self._extListBox.GetClientData(self._currentItemIndex)
            self._deleteButton.Enable()
            self._moveUpButton.Enable(self._extListBox.GetCount() > 1 and self._currentItemIndex > 0)
            self._moveDownButton.Enable(self._extListBox.GetCount() > 1 and self._currentItemIndex < self._extListBox.GetCount() - 1)
        self.LoadItem(self._currentItem)


    def SaveCurrentItem(self, event=None):
        extension = self._currentItem
        if extension:
            if extension.menuItemName != self._menuItemNameTextCtrl.GetValue():
                extension.menuItemName = self._menuItemNameTextCtrl.GetValue()
                self._extListBox.SetString(self._currentItemIndex, extension.menuItemName)
            extension.menuItemDesc = self._menuItemDescTextCtrl.GetValue()
            extension.command = self._commandTextCtrl.GetValue()
            extension.commandPreArgs = self._commandPreArgsTextCtrl.GetValue()
            extension.commandPostArgs = self._commandPostArgsTextCtrl.GetValue()
            fileExt = self._fileExtTextCtrl.GetValue().replace(' ','')
            if not fileExt:
                extension.fileExt = None
            else:
                extension.fileExt = fileExt.split(',')
            extension.opOnSelectedFile = self._selFileCtrl.GetValue()


    def LoadItem(self, extension):
        if extension:
            self._menuItemDescTextCtrl.SetValue(extension.menuItemDesc or '')
            self._commandTextCtrl.SetValue(extension.command or '')
            self._commandTextCtrl.SetToolTipString(extension.command or '')
            self._commandPreArgsTextCtrl.SetValue(extension.commandPreArgs or '')
            self._commandPostArgsTextCtrl.SetValue(extension.commandPostArgs or '')
            if extension.fileExt:
                list = ""
                for ext in extension.fileExt:
                    if list:
                        list = list + ", "
                    list = list + ext
                self._fileExtTextCtrl.SetValue(list)
            else:
                self._fileExtTextCtrl.SetValue('')
            self._selFileCtrl.SetValue(extension.opOnSelectedFile)
            self._menuItemNameTextCtrl.SetValue(extension.menuItemName or '')  # Do the name last since it triggers the write event that updates the entire item
            self._extDetailPanel.Enable()
        else:
            self._menuItemNameTextCtrl.SetValue('')
            self._menuItemDescTextCtrl.SetValue('')
            self._commandTextCtrl.SetValue('')
            self._commandTextCtrl.SetToolTipString(_("Path to executable"))
            self._commandPreArgsTextCtrl.SetValue('')
            self._commandPostArgsTextCtrl.SetValue('')
            self._fileExtTextCtrl.SetValue('')
            self._selFileCtrl.SetValue(True)
            self._extDetailPanel.Enable(False)


    def OnAdd(self, event):
        self.SaveCurrentItem()
        name = _("Untitled")
        count = 1
        while self._extListBox.FindString(name) != wx.NOT_FOUND:
            count = count + 1
            name = _("Untitled%s") % count
        extension = Extension(name)
        self._extensions.append(extension)
        self._extListBox.Append(extension.menuItemName, extension)
        self._extListBox.SetStringSelection(extension.menuItemName)
        self.OnListBoxSelect()
        self._menuItemNameTextCtrl.SetFocus()
        self._menuItemNameTextCtrl.SetSelection(-1, -1)


    def OnDelete(self, event):
        self._extListBox.Delete(self._currentItemIndex)
        self._extensions.remove(self._currentItem)
        self._currentItemIndex = min(self._currentItemIndex, self._extListBox.GetCount() - 1)
        if self._currentItemIndex > -1:
            self._extListBox.SetSelection(self._currentItemIndex)
        self._currentItem = None  # Don't update it since it no longer exists
        self.OnListBoxSelect()


    def OnMoveUp(self, event):
        itemAboveString = self._extListBox.GetString(self._currentItemIndex - 1)
        itemAboveData = self._extListBox.GetClientData(self._currentItemIndex - 1)
        self._extListBox.Delete(self._currentItemIndex - 1)
        self._extListBox.Insert(itemAboveString, self._currentItemIndex)
        self._extListBox.SetClientData(self._currentItemIndex, itemAboveData)
        self._currentItemIndex = self._currentItemIndex - 1
        self.OnListBoxSelect() # Reset buttons


    def OnMoveDown(self, event):
        itemBelowString = self._extListBox.GetString(self._currentItemIndex + 1)
        itemBelowData = self._extListBox.GetClientData(self._currentItemIndex + 1)
        self._extListBox.Delete(self._currentItemIndex + 1)
        self._extListBox.Insert(itemBelowString, self._currentItemIndex)
        self._extListBox.SetClientData(self._currentItemIndex, itemBelowData)
        self._currentItemIndex = self._currentItemIndex + 1
        self.OnListBoxSelect() # Reset buttons
