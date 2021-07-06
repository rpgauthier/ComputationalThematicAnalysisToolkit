import logging

import wx
import wx.adv

from Common.GUIText import Coding as GUIText
import Common.Constants as Constants
import Common.Notes as Notes
import Common.Objects.DataViews.Codes as CodesDataViews

class CodeDialog(wx.Dialog):
    def __init__(self, parent, code, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CodeDialog["+str(code.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(code.key), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer()
        self.document_panel = CodePanel(self, code, size=self.GetSize())
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
        usefulness_label = wx.StaticText(edit_panel, label=GUIText.USEFULNESS_LABEL+":", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALL, 5)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=[GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl, 0, wx.ALL, 5)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.node.usefulness_flag is None:
            self.usefulness_ctrl.Select(0)
        elif self.node.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.node.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer)

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

class DocumentListPanel(wx.Panel):
    def __init__(self, parent, dataset_key):
        logger = logging.getLogger(__name__+".DocumentListPanel["+str(dataset_key)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)

        sizer = wx.BoxSizer(wx.VERTICAL)

        controls_sizer = wx.BoxSizer()
        actions_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.ACTIONS)
        actions_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        notsure_tool = actions_toolbar.AddTool(wx.ID_ANY, label=GUIText.NOT_SURE, bitmap=wx.Bitmap(1, 1),
                                      shortHelp=GUIText.NOT_SURE_HELP)
        actions_toolbar.Bind(wx.EVT_MENU, self.OnNotSure, notsure_tool)
        useful_tool = actions_toolbar.AddTool(wx.ID_ANY, label=GUIText.USEFUL, bitmap=wx.Bitmap(1, 1),
                                      shortHelp=GUIText.USEFUL_HELP)
        actions_toolbar.Bind(wx.EVT_MENU, self.OnUseful, useful_tool)
        notuseful_tool = actions_toolbar.AddTool(wx.ID_ANY, label=GUIText.NOT_USEFUL, bitmap=wx.Bitmap(1, 1),
                                         shortHelp=GUIText.NOT_USEFUL_HELP)
        actions_toolbar.Bind(wx.EVT_MENU, self.OnNotUseful, notuseful_tool)
        actions_toolbar.Realize()
        actions_sizer.Add(actions_toolbar)
        controls_sizer.Add(actions_sizer, 0, wx.ALL, 5)
        
        usefulness_menu = wx.Menu()
        self.notsure_toggle = usefulness_menu.Append(wx.ID_ANY, item=GUIText.NOT_SURE, kind=wx.ITEM_CHECK)
        self.notsure_toggle.Check()
        usefulness_menu.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.notsure_toggle)
        self.useful_toggle = usefulness_menu.Append(wx.ID_ANY, item=GUIText.USEFUL, kind=wx.ITEM_CHECK)
        self.useful_toggle.Check()
        usefulness_menu.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.useful_toggle)
        self.notuseful_toggle = usefulness_menu.Append(wx.ID_ANY, item=GUIText.NOT_USEFUL, kind=wx.ITEM_CHECK)
        self.notuseful_toggle.Check()
        usefulness_menu.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.notuseful_toggle)

        self.origins_menu = wx.Menu()
        self.origins_toggles = {}
        self.dataset_toggle = self.origins_menu.Append(wx.ID_ANY, item=GUIText.DATACOLLECTION_LIST, kind=wx.ITEM_CHECK)
        self.dataset_toggle.Check()
        self.origins_menu.Bind(wx.EVT_MENU, self.OnToggleSamples, self.dataset_toggle)
        
        view_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.VIEW)
        view_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        usefulness_tool = view_toolbar.AddTool(wx.ID_ANY, label=GUIText.SHOW_USEFULNESS, bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_DROPDOWN)
        usefulness_tool.SetDropdownMenu(usefulness_menu)
        origins_tool = view_toolbar.AddTool(wx.ID_ANY, label=GUIText.SHOW_DOCS_FROM, bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_DROPDOWN)
        origins_tool.SetDropdownMenu(self.origins_menu)
        self.search_ctrl = wx.SearchCtrl(view_toolbar)
        view_toolbar.AddControl(self.search_ctrl, GUIText.SEARCH)
        self.search_ctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.search_ctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.search_ctrl.SetDescriptiveText(GUIText.SEARCH)
        self.search_ctrl.ShowCancelButton(True)
        view_toolbar.Realize()
        view_sizer.Add(view_toolbar)
        controls_sizer.Add(view_sizer, 0, wx.ALL, 5)

        sizer.Add(controls_sizer, 0, wx.ALL, 5)
        
        #single dataset mode
        main_frame = wx.GetApp().GetTopWindow()
        self.documents_model = CodesDataViews.DocumentViewModel(main_frame.datasets[dataset_key], main_frame.samples)
        self.documents_model.samples_filter.append('dataset')
        self.documents_ctrl = CodesDataViews.DocumentViewCtrl(self, self.documents_model)
        sizer.Add(self.documents_ctrl, 1, wx.EXPAND)

        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)

        self.SetSizer(sizer)

        logger.info("Finished")    

    def OnNotSure(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotSure")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = None
                self.documents_model.ItemChanged(item)
        logger.info("Finished")

    def OnUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = True
                self.documents_model.ItemChanged(item)
        logger.info("Finished")

    def OnNotUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = False
                self.documents_model.ItemChanged(item)
        logger.info("Finished")
    
    def OnToggleShowUsefulness(self, event):
        notsure_toggled = self.notsure_toggle.IsChecked()
        if not notsure_toggled:
            if None in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(None)
        elif notsure_toggled:
            if None not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(None)
        
        useful_toggled = self.useful_toggle.IsChecked()
        if not useful_toggled:
            if True in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(True)
        elif useful_toggled:
            if True not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(True)
        
        notuseful_toggled = self.notuseful_toggle.IsChecked()
        if not notuseful_toggled:
            if False in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(False)
        elif notuseful_toggled:
            if False not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(False)
        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)

    def OnToggleSamples(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnToggleSamples")
        logger.info("Starting")
        origins = []

        if self.dataset_toggle.IsChecked():
            origins.append('dataset')
        for key in self.origins_toggles:
            if self.origins_toggles[key].IsChecked():
                origins.append(key)
        
        self.documents_model.samples_filter.clear()
        self.documents_model.samples_filter.extend(origins)

        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)
        logger.info("Finished")
    
    def OnSearch(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnSearch")
        logger.info("Starting")
        search_ctrl = event.GetEventObject()
        search_value = search_ctrl.GetValue()
        self.documents_model.search_filter = search_value
        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)
        logger.info("Finished")

    def OnSearchCancel(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnSearchCancel")
        logger.info("Starting")
        search_ctrl = event.GetEventObject()
        search_ctrl.SetValue("")
        self.OnSearch(event)
        logger.info("Finished")


    def DocumentsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".DocumentListPanel.DocumentsUpdated")
        logger.info("Starting")

        main_frame = wx.GetApp().GetTopWindow()
        for sample in list(self.origins_toggles.keys()):
            if sample not in main_frame.samples:
                self.origins_menu.Delete(self.origins_toggles[sample])
                del self.origins_toggles[sample]
        for sample in main_frame.samples:
            if sample not in self.origins_toggles:
                self.origins_toggles[sample] = self.origins_menu.Append(wx.ID_ANY, item=sample, kind=wx.ITEM_CHECK)
                self.origins_toggles[sample].Check()
                self.origins_menu.Bind(wx.EVT_MENU, self.OnToggleSamples, self.origins_toggles[sample])
                self.documents_model.samples_filter.append(sample)

        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)
        logger.info("Finished")

    #Module Control commands
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".DocumentListPanel.Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".DocumentListPanel.Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data

class DocumentDialog(wx.Dialog):
    def __init__(self, parent, document, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DocumentDialog["+str(document.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(document.key), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer()
        self.document_panel = DocumentPanel(self, document, size=self.GetSize())
        sizer.Add(self.document_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.info("Finished")

class DocumentPanel(wx.Panel):
    def __init__(self, parent, document, size):
        wx.Panel.__init__(self, parent, size=size)

        self.document = document

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(frame_sizer)

        frame_splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        frame_sizer.Add(frame_splitter, 1, wx.EXPAND)

        top_frame_splitter = wx.SplitterWindow(frame_splitter, style=wx.SP_BORDER)

        data_panel = wx.ScrolledWindow(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)
        data_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        url = wx.adv.HyperlinkCtrl(data_panel, url=document.url)
        data_panel_sizer.Add(url, 0, wx.ALL, 5)

        field_ctrl = wx.TextCtrl(data_panel, value="", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.BORDER_NONE)
        data_panel_sizer.Add(field_ctrl, 1, wx.EXPAND, 5)
        for field in document.data_dict:
            if isinstance(document.data_dict[field], list):
                for entry in document.data_dict[field]:
                    field_ctrl.AppendText(str(entry)+'\n------------\n')
            else:
                field_ctrl.AppendText(str(document.data_dict[field])+'\n------------\n')
        data_panel.SetSizer(data_panel_sizer)

        codes_panel = wx.Panel(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        codes_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        main_frame = wx.GetApp().GetTopWindow()
        self.codes_model = CodesDataViews.ObjectCodesViewModel(main_frame.codes, self.document)
        self.codes_ctrl = CodesDataViews.CodesViewCtrl(codes_panel, self.codes_model)
        codes_panel_sizer.Add(self.codes_ctrl, 1, wx.EXPAND, 5)
        codes_panel.SetSizer(codes_panel_sizer)

        edit_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        edit_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        usefulness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        usefulness_label = wx.StaticText(edit_panel, label=GUIText.USEFULNESS_LABEL+":", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALL, 5)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=[GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl, 0, wx.ALL, 5)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.document.usefulness_flag == None:
            self.usefulness_ctrl.Select(0)
        elif self.document.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.document.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer)

        self.notes_panel = Notes.NotesPanel(edit_panel)
        self.notes_panel.SetNote(document.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        edit_panel_sizer.Add(self.notes_panel, 1, wx.EXPAND, 5)
        
        edit_panel.SetSizer(edit_panel_sizer)

        top_frame_splitter.SetMinimumPaneSize(20)
        top_frame_splitter.SplitVertically(data_panel, codes_panel)
        top_frame_splitter.SetSashPosition(int(self.GetSize().GetWidth()/2))

        frame_splitter.SetMinimumPaneSize(20)
        frame_splitter.SplitHorizontally(top_frame_splitter, edit_panel)
        frame_splitter.SetSashPosition(int(self.GetSize().GetHeight()/2))

        #initialize scrolling
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        data_panel.SetScrollRate(fontsz.x, fontsz.y)
        data_panel.EnableScrolling(True, True)

        self.Layout()
    
    def OnUpdateUsefulness(self, event):
        choice = self.usefulness_ctrl.GetSelection()
        if choice == 0:
            self.document.usefulness_flag = None
        elif choice == 1:
            self.document.usefulness_flag = True
        elif choice == 2:
            self.document.usefulness_flag = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()

    def OnUpdateNotes(self, event):
        self.document.notes = self.notes_panel.GetNote()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()
    
    def DocumentUpdated(self):
        self.codes_model.Cleared()
        self.codes_ctrl.Expander(None)
        self.notes_panel.Unbind(wx.EVT_TEXT)
        self.notes_panel.SetNote(self.document.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)

class CreateQuotationDialog(wx.Dialog):
    def __init__(self, parent, code, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CreateQuotationDialog["+str(code.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(code.key), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer(wx.VERTICAL)

        instruction_label = wx.StaticText(self, label="Choose a document:")
        sizer.Add(instruction_label, 0, wx.ALL, 5)

        #single dataset mode
        main_frame = wx.GetApp().GetTopWindow()
        self.connections = code.GetConnections(main_frame.datasets, main_frame.samples)
        self.connections_model = CodesDataViews.DocumentConnectionsViewModel(self.connections)
        self.connections_ctrl = CodesDataViews.DocumentConnectionsViewCtrl(self, self.connections_model)
        self.connections_ctrl.ToggleWindowStyle(wx.dataview.DV_MULTIPLE)
        self.connections_ctrl.SetWindowStyle(wx.dataview.DV_SINGLE)
        sizer.Add(self.connections_ctrl, 1, wx.EXPAND, 5)

        self.connections_model.Cleared()

        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)
        sizer.Add(controls_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        logger.info("Finished")
    
    def OnOK(self, event):
        logger = logging.getLogger(__name__+".CreateQuotationDialog.OnOK")
        logger.info("Starting")
        #check that an object was selected
        if not self.connections_ctrl.HasSelection():
            wx.MessageBox("No item selected. Must select one item to create a quotation from.",
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('no item selected')
        else:
            self.EndModal(wx.ID_OK)
        logger.info("Finished")


