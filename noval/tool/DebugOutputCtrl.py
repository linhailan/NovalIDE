import STCTextEditor
import wx
_ = wx.GetTranslation

class DebugOutputCtrl(STCTextEditor.TextCtrl):
    
    ItemIDs = [wx.ID_UNDO, wx.ID_REDO,wx.ID_CUT, wx.ID_COPY, wx.ID_PASTE, wx.ID_CLEAR, wx.ID_SELECTALL,STCTextEditor.WORD_WRAP_ID]
    
    def __init__(self, parent, id=-1, style = wx.NO_FULL_REPAINT_ON_RESIZE, clearTab=True):
        STCTextEditor.TextCtrl.__init__(self, parent, id, style)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        accelTbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('A'), wx.ID_SELECTALL),(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY),(wx.ACCEL_CTRL, ord('V'), wx.ID_PASTE)])  
        self.SetAcceleratorTable(accelTbl)
        
    def OnRightUp(self, event):
        self.PopupMenu(self.CreatePopupMenu(), event.GetPosition())
        
    def CreatePopupMenu(self):
        menu = wx.Menu()   
        menu.Append(wx.ID_UNDO, "Undo")
        menu.Append(wx.ID_REDO, "Redo")
        menu.AppendSeparator()       
        menu.Append(wx.ID_CUT, "Cut")
        menu.Append(wx.ID_COPY, "Copy\tCtrl+C")
        menu.Append(wx.ID_PASTE, "Paste\tCtrl+V")
        menu.Append(wx.ID_CLEAR, "Clear")
        menu.AppendSeparator()
        menu.Append(wx.ID_SELECTALL, "Select All\tCtrl+A")
                    
        menu.AppendCheckItem(STCTextEditor.WORD_WRAP_ID, _("Word Wrap"))
        wx.EVT_MENU(self, wx.ID_UNDO, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, wx.ID_UNDO, self.DSProcessUpdateUIEvent)
        wx.EVT_MENU(self, wx.ID_REDO, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, wx.ID_REDO, self.DSProcessUpdateUIEvent)
        wx.EVT_MENU(self, wx.ID_CUT, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, wx.ID_CUT, self.DSProcessUpdateUIEvent)
        wx.EVT_MENU(self, wx.ID_COPY, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, wx.ID_COPY, self.DSProcessUpdateUIEvent)
        wx.EVT_MENU(self, wx.ID_PASTE, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, wx.ID_PASTE, self.DSProcessUpdateUIEvent)
        wx.EVT_MENU(self, wx.ID_CLEAR, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, wx.ID_CLEAR, self.DSProcessUpdateUIEvent)
        wx.EVT_MENU(self, wx.ID_SELECTALL, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, wx.ID_SELECTALL, self.DSProcessUpdateUIEvent)
        wx.EVT_MENU(self, STCTextEditor.WORD_WRAP_ID, self.DSProcessEvent) 
        wx.EVT_UPDATE_UI(self, STCTextEditor.WORD_WRAP_ID, self.DSProcessUpdateUIEvent)
        return menu
        
    def DSProcessEvent(self, event):
        id = event.GetId()
        if id == wx.ID_UNDO:
            self.Undo()
            return True
        elif id == wx.ID_REDO:
            self.Redo()
            return True
        elif id == wx.ID_CUT:
            self.Cut()
            return True
        elif id == wx.ID_COPY:
            self.Copy()
            return True
        elif id == wx.ID_PASTE:
            self.OnPaste()
            return True
        elif id == wx.ID_CLEAR:
            self.OnClear()
            return True
        elif id == wx.ID_SELECTALL:
            self.SelectAll()
            return True
        elif id == STCTextEditor.WORD_WRAP_ID:
            self.SetWordWrap(not self.GetWordWrap())
            return True
        else:
            return True
            
    def DSProcessUpdateUIEvent(self, event):
        id = event.GetId()
        if id == wx.ID_UNDO:
            event.Enable(self.CanUndo())
            return True
        elif id == wx.ID_REDO:
            event.Enable(self.CanRedo())
            return True
        elif (id == wx.ID_CUT
        or id == wx.ID_COPY
        or id == wx.ID_CLEAR):
            hasSelection = self.GetSelectionStart() != self.GetSelectionEnd()
            event.Enable(hasSelection)
            return True
        elif id == wx.ID_PASTE:
            event.Enable(self.CanPaste())
            return True
        elif id == wx.ID_SELECTALL:
            hasText = self.GetTextLength() > 0
            event.Enable(hasText)
            return True
        elif id == STCTextEditor.WORD_WRAP_ID:
            event.Enable(self.CanWordWrap())
            event.Check(self.CanWordWrap() and self.GetWordWrap())
            return True
        else:
            return True        