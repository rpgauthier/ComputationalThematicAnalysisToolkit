import wx
import wx.lib.agw.flatnotebook as FNB

class TestFrame(wx.Frame):
    '''the Main GUI'''
    def __init__(self, parent, title,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, title=title, pos=pos, size=size, style=style)
        
        sizer = wx.BoxSizer()
        test_FNB = FNB.FlatNotebook(parent=self)

        test_panel1 = wx.Panel(self)
        test_FNB.AddPage(test_panel1, "test_1")
        test_panel2 = wx.Panel(self)
        test_FNB.AddPage(test_panel2, "test_2")

        sizer.Add(test_FNB, 1, wx.EXPAND)
        self.SetSizer(sizer)


app = wx.App()
top = TestFrame(None, title="FNB Crash Test", size=(300,200))
top.Show()
app.MainLoop()