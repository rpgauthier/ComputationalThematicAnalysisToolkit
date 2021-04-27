import logging

import wx

from Common.GUIText import Coding as GUIText
import Common.Notes as Notes
import Common.Objects.Codes as Codes
import Common.Objects.DataViews.Codes as CodesDataViews

class AddCodesDialog(wx.Dialog):
    def __init__(self, parent, obj, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".AddCodesDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.ADD_CODES_DIALOG_LABEL+str(obj.name),
                           size=size,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.obj = obj

        sizer = wx.BoxSizer(wx.VERTICAL)

        #add an existing code
        existing_label = wx.StaticText(self, label=GUIText.EXISTING_CODES+":")
        main_frame = wx.GetApp().GetTopWindow()
        self.existing_model = CodesDataViews.AllCodesViewModel(main_frame.codes)
        self.existing_ctrl = CodesDataViews.CodesViewCtrl(self, self.existing_model)
        sizer.Add(existing_label)
        sizer.Add(self.existing_ctrl, 1, wx.EXPAND)

        #add a new code
        new_sizer = wx.BoxSizer(wx.HORIZONTAL)
        new_label = wx.StaticText(self, label=GUIText.NEW_CODE+":")
        self.new_ctrl = wx.TextCtrl(self)
        self.new_ctrl.SetToolTip(GUIText.NEW_CODE_TOOLTIP)
        new_sizer.Add(new_label)
        new_sizer.Add(self.new_ctrl)
        sizer.Add(new_sizer)

        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK, )
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label=GUIText.CANCEL)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.Add(ok_button)
        controls_sizer.Add(cancel_button)
        sizer.Add(controls_sizer)
        self.SetSizer(sizer)
        logger.info("Finished")

    def OnOK(self, event):
        logger = logging.getLogger(__name__+".AddCodesDialog.OnOK")
        logger.info("Starting")

        codes_to_add = []
        status_flag = True

        main_frame = wx.GetApp().GetTopWindow()

        new_code = self.new_ctrl.GetValue()
        if new_code != "":
            if new_code in main_frame.codes:
                wx.MessageBox(GUIText.NEW_CODE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('name[%s] is not unique', new_code)
                status_flag = False
            else:
                main_frame.codes[new_code] = Codes.Code(new_code)
                codes_to_add.append(main_frame.codes[new_code])
        if status_flag:
            #include any selected existing codes
            for item in self.existing_ctrl.GetSelections():
                node = self.existing_model.ItemToObject(item)
                codes_to_add.append(node)
            #add codes to the obj
            for code in codes_to_add:
                if code.key not in self.obj.codes:
                    self.obj.AppendCode(code.key)
                    code.AddConnection(self.obj)

        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)

class CodeDialog(wx.Dialog):
    def __init__(self, parent, node, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CodeDialog["+str(node.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(node.key), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer()
        self.document_panel = CodePanel(self, node, size=self.GetSize())
        sizer.Add(self.document_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.info("Finished")

class CodePanel(wx.Panel):
    def __init__(self, parent, node, size):
        wx.Panel.__init__(self, parent, size=size)

        self.node = node

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(frame_sizer)

        frame_splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        frame_sizer.Add(frame_splitter, 1, wx.EXPAND)

        objects_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        objects_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        main_frame = wx.GetApp().GetTopWindow()
        objects = node.GetConnections(main_frame.datasets, main_frame.samples)
        self.objects_model = CodesDataViews.CodeConnectionsViewModel(objects)
        self.objects_ctrl = CodesDataViews.CodeConnectionsViewCtrl(objects_panel, self.objects_model)
        objects_panel_sizer.Add(self.objects_ctrl, 1, wx.EXPAND, 5)
        objects_panel.SetSizer(objects_panel_sizer)

        edit_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        edit_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        usefulness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        usefulness_label = wx.StaticText(edit_panel, label="Usefullness: ", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALL, 5)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=["Unsure", "Useful", "Not Useful"], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl, 0, wx.ALL, 5)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.node.usefulness_flag is None:
            self.usefulness_ctrl.Select(0)
        elif self.node.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.node.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer)
        
        #notes_label = wx.StaticText(edit_panel, label="Notes", style=wx.ALIGN_LEFT)
        #notes_label.SetFont(label_font)
        #edit_panel_sizer.Add(notes_label, 0, wx.ALL, 5)
        #self.notes_ctrl = wx.TextCtrl(edit_panel, value=node.notes, style=wx.TE_LEFT|wx.TE_MULTILINE)
        #self.notes_ctrl.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        #edit_panel_sizer.Add(self.notes_ctrl, 1, wx.EXPAND, 5)
        self.notes_panel = Notes.NotesPanel(edit_panel)
        self.notes_panel.SetNote(node.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        edit_panel_sizer.Add(self.notes_panel, 1, wx.EXPAND, 5)
        
        edit_panel.SetSizer(edit_panel_sizer)

        frame_splitter.SetMinimumPaneSize(20)
        frame_splitter.SplitHorizontally(objects_panel, edit_panel)
        frame_splitter.SetSashPosition(int(self.GetSize().GetHeight()/2))

        self.Layout()
    
    def OnUpdateUsefulness(self, event):
        choice = self.usefulness_ctrl.GetSelection()
        if choice == 0:
            self.node.usefulness_flag = None
        elif choice == 1:
            self.node.usefulness_flag = True
        elif choice == 2:
            self.node.usefulness_flag = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()

    def OnUpdateNotes(self, event):
        self.node.notes = self.notes_panel.GetNote()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()