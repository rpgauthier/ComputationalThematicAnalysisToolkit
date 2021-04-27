import images
import wx

########################################################################
class TabPanel(wx.Panel):
    """
    This will be the first notebook tab
    """
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """"""
        
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        txtOne = wx.TextCtrl(self, wx.ID_ANY, "")
        txtTwo = wx.TextCtrl(self, wx.ID_ANY, "")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(txtOne, 0, wx.ALL, 5)
        sizer.Add(txtTwo, 0, wx.ALL, 5)
        
        self.SetSizer(sizer)
 
########################################################################
class TreebookDemo(wx.Treebook):
    """
    Treebook class
    """
 
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Treebook.__init__(self, parent, wx.ID_ANY, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                            )
 
        pages = [(TabPanel(self), "Panel One"),
                 (TabPanel(self), "Panel Two"),
                 (TabPanel(self), "Panel Three")]
        for page, label in pages:
            self.AddPage(page, label)

        for i in range(2):
            self.InsertSubPage(i, page, "sub-"+label)
 
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGING, self.OnPageChanging)
 
        # This is a workaround for a sizing bug on Mac...
        wx.FutureCall(100, self.AdjustSize)
 
    #----------------------------------------------------------------------
    def AdjustSize(self):
        #print self.GetTreeCtrl().GetBestSize()
        self.GetTreeCtrl().InvalidateBestSize()
        self.SendSizeEvent()
 
    #----------------------------------------------------------------------
    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        print ('OnPageChanged,  old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()
 
    #----------------------------------------------------------------------
    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        print ('OnPageChanging, old:%d, new:%d, sel:%d\n' % (old, new, sel))
        event.Skip()
 
########################################################################
class DemoFrame(wx.Frame):
    """
    Frame that holds all other widgets
    """
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "Treebook Tutorial",
                          size=(700,400)
                          )
        panel = wx.Panel(self)
 
        notebook = TreebookDemo(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        self.Layout()
 
        self.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = DemoFrame()
    app.MainLoop()