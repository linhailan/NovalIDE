import wx
from noval.tool.consts import SPACE,HALF_SPACE,_ 

class PromptMessageDialog(wx.Dialog):
    
    DEFAULT_PROMPT_MESSAGE_ID = wx.ID_YES
    def __init__(self,parent,dlg_id,title,msg):
        wx.Dialog.__init__(self,parent,dlg_id,title)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        #-- icon and message --#
        msgSizer = wx.BoxSizer(wx.HORIZONTAL)
        # icon #
        artID = wx.ART_QUESTION

        bmp = wx.ArtProvider_GetBitmap(artID, wx.ART_MESSAGE_BOX, (48, 48))
        bmpIcon = wx.StaticBitmap(self, -1, bmp)
        msgSizer.Add(bmpIcon, 0, wx.ALIGN_CENTRE | wx.ALL, HALF_SPACE)
        # msg #
        txtMsg = wx.StaticText(self, -1, msg, style=wx.ALIGN_CENTRE)
        msgSizer.Add(txtMsg, 0, wx.ALIGN_CENTRE | wx.ALL, HALF_SPACE)
        sizer.Add(msgSizer, 0, wx.ALIGN_CENTRE, HALF_SPACE)
        line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALL, HALF_SPACE)
        #-- buttons --#
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        btnYes = wx.Button(self, wx.ID_YES, _('Yes'))
        btnSizer.Add(btnYes, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_YES, self.OnBtnClick)
        
        btnNo = wx.Button(self, wx.ID_NO, _('No'))
        btnSizer.Add(btnNo, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
                    
        wx.EVT_BUTTON(self, wx.ID_YESTOALL, self.OnBtnClick)
                           
        btnYesAll = wx.Button(self, wx.ID_YESTOALL, _('YestoAll'))
        btnSizer.Add(btnYesAll, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_NO, self.OnBtnClick)
        btnNoAll = wx.Button(self, wx.ID_NOTOALL, _('NotoAll'))
        btnSizer.Add(btnNoAll, 0,
                           wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, SPACE)
        wx.EVT_BUTTON(self, wx.ID_NOTOALL, self.OnBtnClick)


        sizer.Add(btnSizer, 0, wx.ALIGN_CENTRE | wx.TOP|wx.BOTTOM, SPACE)
        #--
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.Fit()

    def OnBtnClick(self,event):
        self.EndModal(event.GetId())
        

class FileFilterDialog(wx.Dialog):
    def __init__(self,parent,dlg_id,title):
        wx.Dialog.__init__(self,parent,dlg_id,title)