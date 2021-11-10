import functools
import logging
import webbrowser
from datetime import datetime

import wx
import wx.adv
import wx.richtext
import wx.dataview as dv

from Common.GUIText import Coding as GUIText
import Common.Constants as Constants
import Common.Notes as Notes
import Common.Objects.DataViews.Codes as CodesDataViews

class CodeConnectionsDialog(wx.Dialog):
    def __init__(self, parent, code, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CodeConnectionsDialog["+str(code.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(code.name), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.code = code

        self.sizer = wx.BoxSizer()
        self.codeconnections_panel = CodeConnectionsPanel(self, self.code, size=self.GetSize())
        self.sizer.Add(self.codeconnections_panel, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        logger.info("Finished")
    
    def RefreshDetails(self):
        self.codeconnections_panel.RefreshDetails()

class CodeConnectionsPanel(wx.Panel):
    def __init__(self, parent, code, size):
        wx.Panel.__init__(self, parent, size=size)

        self.code = code

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(frame_sizer)

        frame_splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        frame_sizer.Add(frame_splitter, 1, wx.EXPAND)

        objects_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        objects_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        main_frame = wx.GetApp().GetTopWindow()
        self.objects_model = CodesDataViews.CodeConnectionsViewModel(code, main_frame.datasets, main_frame.samples)
        self.objects_ctrl = CodesDataViews.CodeConnectionsViewCtrl(objects_panel, self.objects_model)
        objects_panel_sizer.Add(self.objects_ctrl, 1, wx.EXPAND, 5)
        objects_panel.SetSizer(objects_panel_sizer)

        edit_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        edit_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        usefulness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        usefulness_label = wx.StaticText(edit_panel, label=GUIText.USEFULNESS_LABEL+" ", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=[GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.code.usefulness_flag is None:
            self.usefulness_ctrl.Select(0)
        elif self.code.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.code.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer, 0, wx.ALL, 5)

        self.notes_panel = Notes.NotesPanel(edit_panel)
        self.notes_panel.SetNote(code.notes)
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
            self.code.usefulness_flag = None
        elif choice == 1:
            self.code.usefulness_flag = True
        elif choice == 2:
            self.code.usefulness_flag = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated(self)

    def OnUpdateNotes(self, event):
        self.code.notes = self.notes_panel.GetNote()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated(self)
    
    def RefreshDetails(self):
        self.objects_model.Cleared()
        self.objects_ctrl.Expander(None)
        if self.code.usefulness_flag is None:
            self.usefulness_ctrl.Select(0)
        elif self.code.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.code.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        self.notes_panel.Unbind(wx.EVT_TEXT)
        self.notes_panel.SetNote(self.code.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)

class DocumentListPanel(wx.Panel):
    def __init__(self, parent, dataset_key):
        logger = logging.getLogger(__name__+".DocumentListPanel["+str(dataset_key)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)

        self.dataset_key = dataset_key

        main_frame = wx.GetApp().GetTopWindow()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        controls_sizer = wx.BoxSizer()
        actions_box = wx.StaticBox(self, label=GUIText.ACTIONS)
        actions_box.SetFont(main_frame.DETAILS_LABEL_FONT)
        actions_sizer = wx.StaticBoxSizer(actions_box, wx.HORIZONTAL)
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
        
        view_box = wx.StaticBox(self, label=GUIText.VIEW)
        view_box.SetFont(main_frame.DETAILS_LABEL_FONT)
        view_sizer = wx.StaticBoxSizer(view_box, wx.HORIZONTAL)
        view_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        usefulness_tool = view_toolbar.AddTool(wx.ID_ANY, label=GUIText.SHOW_USEFULNESS, bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_DROPDOWN)
        usefulness_tool.SetDropdownMenu(usefulness_menu)
        origins_tool = view_toolbar.AddTool(wx.ID_ANY, label=GUIText.SHOW_DOCS_FROM, bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_DROPDOWN)
        origins_tool.SetDropdownMenu(self.origins_menu)
        view_toolbar.Realize()
        view_sizer.Add(view_toolbar)
        controls_sizer.Add(view_sizer, 0, wx.ALL, 5)

        self.search_ctrl = wx.SearchCtrl(self)
        self.search_ctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.search_ctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.search_ctrl.SetDescriptiveText(GUIText.SEARCH)
        self.search_ctrl.ShowCancelButton(True)
        #TODO check this on OSX
        extent = self.search_ctrl.GetTextExtent(GUIText.SEARCH)
        size = self.search_ctrl.GetSizeFromTextSize(extent.GetWidth()*4, -1)
        self.search_ctrl.SetMinSize(size)
        controls_sizer.Add(self.search_ctrl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)

        self.sizer.Add(controls_sizer, 0, wx.ALL, 5)
        
        #single dataset mode
        main_frame = wx.GetApp().GetTopWindow()
        self.documents_model = CodesDataViews.DocumentViewModel(main_frame.datasets[self.dataset_key], main_frame.samples)
        self.documents_model.samples_filter.append('dataset')
        self.documents_ctrl = CodesDataViews.DocumentViewCtrl(self, self.documents_model)
        self.sizer.Add(self.documents_ctrl, 1, wx.EXPAND)

        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)

        self.SetSizer(self.sizer)

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

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".DocumentListPanel.DatasetsUpdated")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        new_documents_model = CodesDataViews.DocumentViewModel(main_frame.datasets[self.dataset_key], main_frame.samples)
        new_documents_model.samples_filter.extend(self.documents_model.samples_filter)
        new_documents_ctrl = CodesDataViews.DocumentViewCtrl(self, new_documents_model)
        self.sizer.Replace(self.documents_ctrl, new_documents_ctrl)
        self.documents_ctrl.Destroy()
        self.documents_model = new_documents_model
        self.documents_ctrl = new_documents_ctrl
        self.Layout()
        self.Thaw()
        self.DocumentsUpdated()
        logger.info("Finished")

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".DocumentListPanel.DocumentsUpdated")
        logger.info("Starting")

        main_frame = wx.GetApp().GetTopWindow()
        for key in list(self.origins_toggles.keys()):
            if key not in main_frame.samples:
                self.origins_menu.Delete(self.origins_toggles[key])
                del self.origins_toggles[key]
        for key in main_frame.samples:
            if key not in self.origins_toggles:
                self.origins_toggles[key] = self.origins_menu.Append(wx.ID_ANY, item=main_frame.samples[key].name, kind=wx.ITEM_CHECK)
                self.origins_toggles[key].Check()
                self.origins_menu.Bind(wx.EVT_MENU, self.OnToggleSamples, self.origins_toggles[key])
                self.documents_model.samples_filter.append(key)

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
    def __init__(self, parent, document, size=wx.Size((600,600))):
        logger = logging.getLogger(__name__+".DocumentDialog["+str(document.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(document.doc_id), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.document = document

        self.sizer = wx.BoxSizer()
        self.document_panel = DocumentPanel(self, document, size=self.GetSize())
        self.sizer.Add(self.document_panel, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        logger.info("Finished")
    
    def RefreshDetails(self):
        self.document_panel.RefreshDetails()

class DocumentPanel(wx.Panel):
    def __init__(self, parent, document, size):
        wx.Panel.__init__(self, parent, size=size)
        self.document = document
        self.cur_position = None
        self.field_positions = {}

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(frame_sizer)

        frame_splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        frame_sizer.Add(frame_splitter, 1, wx.EXPAND)

        top_frame_splitter = wx.SplitterWindow(frame_splitter, style=wx.SP_BORDER)

        data_panel = wx.ScrolledWindow(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)
        data_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        self.field_ctrl = wx.richtext.RichTextCtrl(data_panel, value="", style=wx.richtext.RE_READONLY)
        data_panel_sizer.Add(self.field_ctrl, 1, wx.EXPAND|wx.ALL, 5)
        self.PopulateFieldCtrl()
        data_panel.SetSizer(data_panel_sizer)
        self.field_ctrl.Bind(wx.EVT_TEXT_URL, self.OnURL)
        self.field_ctrl.Bind(wx.richtext.EVT_RICHTEXT_RIGHT_CLICK, self.OnShowPopup)

        codes_panel = wx.Panel(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        codes_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        main_frame = wx.GetApp().GetTopWindow()
        self.codes_model = CodesDataViews.ObjectCodesViewModel(main_frame.codes, self.document)
        self.codes_ctrl = CodesDataViews.ObjectCodesViewCtrl(codes_panel, self.codes_model)
        codes_panel_sizer.Add(self.codes_ctrl, 1, wx.ALL|wx.EXPAND, 5)
        codes_panel.SetSizer(codes_panel_sizer)

        self.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.OnShowCode, self.codes_ctrl)

        edit_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        edit_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        usefulness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        usefulness_label = wx.StaticText(edit_panel, label=GUIText.USEFULNESS_LABEL+" ", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=[GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.document.usefulness_flag == None:
            self.usefulness_ctrl.Select(0)
        elif self.document.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.document.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer, 0, wx.ALL, 5)

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
        self.OnShowCode(None)
    
    def OnURL(self, event):
        logger = logging.getLogger(__name__+".DocumentPanel["+str(self.document.key)+"].OnURL")
        logger.info("Call to access url[%s]", event.GetString())
        webbrowser.open_new_tab(event.GetString())

    def OnUpdateUsefulness(self, event):
        choice = self.usefulness_ctrl.GetSelection()
        if choice == 0:
            self.document.usefulness_flag = None
        elif choice == 1:
            self.document.usefulness_flag = True
        elif choice == 2:
            self.document.usefulness_flag = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated(self)

    def OnUpdateNotes(self, event):
        self.document.notes = self.notes_panel.GetNote()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated(self)
    
    def OnShowCode(self, event):
        base_attr = wx.TextAttr()
        base_attr.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
        base_attr.SetTextColour(wx.Colour(0, 0, 0))
        self.field_ctrl.SelectAll()
        self.field_ctrl.SetStyle(self.field_ctrl.GetSelectionRange(), base_attr)
        self.field_ctrl.SelectNone()

        codes = []
        code_connections = self.document.GetCodeConnections(self.codes_model.codes)
        count = 0
        for item in self.codes_ctrl.GetSelections():
            code = self.codes_model.ItemToObject(item)
            if code in code_connections:
                codes.append(code)
            count = count + 1
        if count == 0:
            codes = code_connections
        
        for code in codes:
            if (self.document.parent.key, self.document.key) in code.doc_positions:
                new_attr = wx.TextAttr()
                new_attr.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
                new_attr.SetTextColour(wx.Colour(code.colour_rgb[0], code.colour_rgb[1], code.colour_rgb[2]))
                for position in code.doc_positions[(self.document.parent.key, self.document.key)]:
                    if position[0] in self.field_positions:
                        start = position[1] + self.field_positions[position[0]][0]
                        end = position[2] + self.field_positions[position[0]][0]
                        self.field_ctrl.SetStyle(start, end, new_attr)

    def ForwardEvent(self, evt):
        # The RichTextCtrl can handle menu and update events for undo,
        # redo, cut, copy, paste, delete, and select all, so just
        # forward the event to it.
        self.field_ctrl.ProcessEvent(evt)

    def OnShowPopup(self, event):
        self.cur_position = event.GetPosition()
        
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY, GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.ForwardEvent, copy_menuitem)
        menu.AppendSeparator()
        
        cur_selection = self.field_ctrl.GetSelectionRange()
        if cur_selection.Contains(self.cur_position):
            for code in self.document.GetCodeConnections(self.codes_model.codes):
                select_menuitem = menu.Append(wx.ID_ANY, GUIText.SELECT + " " + code.name)
                self.Bind(wx.EVT_MENU, functools.partial(self.OnSelect, code), select_menuitem)

        relative_field = None
        relative_position = None
        for field_key, field_position in self.field_positions.items():
            if field_position[0] <= self.cur_position <= field_position[1]:
                relative_field = field_key
                relative_position = self.cur_position - field_position[0]
                break
        for code in self.document.GetCodeConnections(self.codes_model.codes):
            if (self.document.parent.key, self.document.key) in code.doc_positions:
                for position in code.doc_positions[(self.document.parent.key, self.document.key)]:
                    if position[0] == relative_field and position[1] <= relative_position <= position[2]:
                        remove_menuitem = menu.Append(wx.ID_ANY, GUIText.REMOVE + " " + code.name)
                        self.Bind(wx.EVT_MENU, functools.partial(self.OnRemove, code), remove_menuitem)
                        break

        self.PopupMenu(menu)

    def OnSelect(self, code, event):
        r = self.field_ctrl.GetSelectionRange()
        cur_selection = (r.GetStart(), r.GetEnd(),)
        for field_key, field_position in self.field_positions.items():
            include = False
            if field_position[0] <= cur_selection[0] <= field_position[1]:
                start = cur_selection[0] - field_position[0]
                include = True
            else:
                start = 0
            if cur_selection[0] <= field_position[1] <= cur_selection[1]:
                end = field_position[1] - field_position[0]
                include = True
            else:
                end = cur_selection[1] - field_position[0]
            if include:
                if (self.document.parent.key, self.document.key) not in code.doc_positions:
                    code.doc_positions[(self.document.parent.key, self.document.key)] = []
                code.doc_positions[(self.document.parent.key, self.document.key)].append((field_key, start, end,))
        self.field_ctrl.SelectNone()
        self.OnShowCode(None)
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CodesUpdated()

    def OnRemove(self, code, event):
        if (self.document.parent.key, self.document.key) in code.doc_positions:
            relative_field = None
            relative_position = None
            for field_key, field_position in self.field_positions.items():
                if field_position[0] <= self.cur_position <= field_position[1]:
                    relative_field = field_key
                    relative_position = self.cur_position - field_position[0]
                    break
            for position in reversed(code.doc_positions[(self.document.parent.key, self.document.key)]):
                if position[0] == relative_field and position[1] <= relative_position <= position[2]:
                    code.doc_positions[(self.document.parent.key, self.document.key)].remove(position)
                    if len(code.doc_positions[(self.document.parent.key, self.document.key)]) == 0:
                        del code.doc_positions[(self.document.parent.key, self.document.key)]
        self.field_ctrl.SelectNone()
        self.OnShowCode(None)
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CodesUpdated()

    def PopulateFieldCtrl(self):
        if self.field_ctrl:
            self.field_ctrl.Clear()
            urlStyle = wx.richtext.RichTextAttr()
            urlStyle.SetFontUnderlined(True)
            self.field_ctrl.BeginSuppressUndo()
            cur_pos = 0
            if self.document.parent != None:
                for key in self.document.parent.label_fields:
                    field = self.document.parent.label_fields[key]
                    if field.name in self.document.parent.data[self.document.doc_id]:
                        field_data = self.document.parent.data[self.document.doc_id][field.name]
                        self.field_ctrl.WriteText('------'+str(field.name)+'------\n')
                        if isinstance(field_data, list):
                            for entry in field_data:
                                if field.fieldtype == 'url':
                                    self.field_ctrl.BeginStyle(urlStyle)
                                    self.field_ctrl.BeginURL(entry)
                                    self.field_ctrl.WriteText(entry)
                                    self.field_ctrl.EndURL()
                                    self.field_ctrl.EndStyle()
                                    self.field_ctrl.WriteText('\n------------\n')
                                elif field.fieldtype == 'UTC-timestamp':
                                    value_str = datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT)
                                    self.field_ctrl.WriteText(value_str+' UTC\n------------\n')
                                else:
                                    self.field_ctrl.WriteText(str(entry)+'\n------------\n')
                        else:
                            if field.fieldtype == 'url':
                                self.field_ctrl.BeginStyle(urlStyle)
                                self.field_ctrl.BeginURL(field_data)
                                self.field_ctrl.WriteText(field_data)
                                self.field_ctrl.EndURL()
                                self.field_ctrl.EndStyle()
                                self.field_ctrl.WriteText('\n------------\n')
                            elif field.fieldtype == 'UTC-timestamp':
                                value_str = datetime.utcfromtimestamp(field_data).strftime(Constants.DATETIME_FORMAT)
                                self.field_ctrl.WriteText(value_str+' UTC\n------------\n')
                            else:
                                self.field_ctrl.WriteText(str(field_data)+'\n------------\n')
                    self.field_positions[field.key] = (cur_pos, self.field_ctrl.GetInsertionPoint()-1)
                    cur_pos = self.field_ctrl.GetInsertionPoint()
                for key in self.document.parent.computational_fields:
                    field = self.document.parent.computational_fields[key]
                    if key not in self.document.parent.label_fields and field.name in self.document.parent.data[self.document.doc_id]:
                        field_data = self.document.parent.data[self.document.doc_id][field.name]
                        self.field_ctrl.WriteText('------'+str(field.name)+'------\n')
                        if isinstance(field_data, list):
                            for entry in field_data:
                                if field.fieldtype == 'url':
                                    self.field_ctrl.BeginStyle(urlStyle)
                                    self.field_ctrl.BeginURL(entry)
                                    self.field_ctrl.WriteText(entry)
                                    self.field_ctrl.EndURL()
                                    self.field_ctrl.EndStyle()
                                    self.field_ctrl.WriteText('\n------------\n')
                                elif field.fieldtype == 'UTC-timestamp':
                                    value_str = datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT)
                                    self.field_ctrl.WriteText(value_str+' UTC\n------------\n')
                                else:
                                    self.field_ctrl.WriteText(str(entry)+'\n------------\n')
                        else:
                            if field.fieldtype == 'url':
                                self.field_ctrl.BeginStyle(urlStyle)
                                self.field_ctrl.BeginURL(field_data)
                                self.field_ctrl.WriteText(field_data)
                                self.field_ctrl.EndURL()
                                self.field_ctrl.EndStyle()
                                self.field_ctrl.WriteText('\n------------\n')
                            elif field.fieldtype == 'UTC-timestamp':
                                value_str = datetime.utcfromtimestamp(field_data).strftime(Constants.DATETIME_FORMAT)
                                self.field_ctrl.WriteText(value_str+' UTC\n------------\n')
                            else:
                                self.field_ctrl.WriteText(str(field_data)+'\n------------\n')
                        self.field_positions[field.key] = (cur_pos, self.field_ctrl.GetInsertionPoint()-1)
                        cur_pos = self.field_ctrl.GetInsertionPoint()
    
    def RefreshDetails(self):
        self.PopulateFieldCtrl()
        self.codes_model.Cleared()
        self.OnShowCode(None)
        self.codes_ctrl.Expander(None)
        if self.document.usefulness_flag == None:
            self.usefulness_ctrl.Select(0)
        elif self.document.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.document.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        self.notes_panel.Unbind(wx.EVT_TEXT)
        self.notes_panel.SetNote(self.document.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)


class CreateQuotationDialog(wx.Dialog):
    def __init__(self, parent, code, datasets, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CreateQuotationDialog["+str(code.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(code.name), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.code = code
        self.datasets = datasets

        instruction_label = wx.StaticText(self, label="Choose a document:")
        sizer.Add(instruction_label, 0, wx.ALL, 5)

        #single dataset mode
        main_frame = wx.GetApp().GetTopWindow()
        self.positions_model = CodesDataViews.DocumentPositionsViewModel(self.code, self.datasets)
        self.positions_ctrl = CodesDataViews.DocumentPositionsViewCtrl(self, self.positions_model)
        self.positions_ctrl.ToggleWindowStyle(wx.dataview.DV_MULTIPLE)
        self.positions_ctrl.SetWindowStyle(wx.dataview.DV_SINGLE)
        sizer.Add(self.positions_ctrl, 1, wx.EXPAND, 5)

        self.positions_model.Cleared()

        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.SetLabel(GUIText.CREATE_QUOTATION)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)
        sizer.Add(controls_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.SetSizer(sizer)
        logger.info("Finished")
    
    def OnOK(self, event):
        logger = logging.getLogger(__name__+".CreateQuotationDialog.OnOK")
        logger.info("Starting")
        #check that an object was selected
        if not self.positions_ctrl.HasSelection():
            wx.MessageBox("No item selected. Must select atleast one document or quotation.",
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('no item selected')
        else:
            self.EndModal(wx.ID_OK)
        logger.info("Finished")


