import wx

class CheckListBoxComboPopup(wx.ComboPopup):
    def __init__(self, label):
        wx.ComboPopup.__init__(self)
        self.label = label
        self.checklistbox = None
        self.curitem = None
        self.options = {}

    def AddItem(self, text, key, check):
        self.checklistbox.Append(text)
        self.checklistbox.Check(len(self.options), check)
        self.options[key] = text
    
    def RemoveItem(self, key):
        key_positions = list(self.options.keys())
        key_position = key_positions.index(key)
        self.checklistbox.Delete(key_position)
        del self.options[key]
    
    def GetCheckedKeys(self):
        selected_positions = self.checklistbox.GetCheckedItems()
        key_positions = list(self.options.keys())
        selected_keys = []
        for selected_position in selected_positions:
            selected_keys.append(key_positions[selected_position])
        return selected_keys
    
    def GetKeys(self):
        return list(self.options.keys())

    def OnMotion(self, evt):
        item = self.checklistbox.HitTest(evt.GetPosition())
        if item >= 0:
            self.checklistbox.Select(item)
            self.curitem = item
        else:
            self.checklistbox.SetSelection(wx.NOT_FOUND)
            self.curitem = None

    def OnLeftDown(self, event):
        if self.curitem != None:
            if self.checklistbox.IsChecked(self.curitem):
                self.checklistbox.Check(self.curitem, False)
            else:
                self.checklistbox.Check(self.curitem, True)

    def Create(self, parent):
        self.checklistbox =wx.CheckListBox(parent, style=wx.CB_SIMPLE|wx.SIMPLE_BORDER)
        self.checklistbox.Bind(wx.EVT_MOTION, self.OnMotion)
        self.checklistbox.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        return True

    def GetControl(self):
        return self.checklistbox
    
    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        return wx.ComboPopup.GetAdjustedSize(self, minWidth, prefHeight, maxHeight)
    
    def GetStringValue(self):
        return self.label