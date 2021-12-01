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
import Common.Objects.Codes as Codes
import Common.Objects.DataViews.Codes as CodesDataViews
import Common.Objects.GUIs.Generic as GenericGUIs
import Common.Objects.Utilities.Generic as GenericUtilities

class CodeDialog(wx.Dialog):
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
        self.objects_model = CodesDataViews.CodeConnectionsViewModel(code)
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
        self.objects_ctrl.Expander(None)
    
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
        self.code.notes, self.code.notes_string = self.notes_panel.GetNote()
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

class ThemeDialog(wx.Dialog):
    def __init__(self, parent, theme, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".ThemesDialog["+str(theme.name)+"]["+str(theme.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(theme.name), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.theme = theme

        self.sizer = wx.BoxSizer()
        self.theme_panel = ThemePanel(self, self.theme, size=self.GetSize())
        self.sizer.Add(self.theme_panel, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        logger.info("Finished")
    
    def RefreshDetails(self):
        self.theme_panel.RefreshDetails()

class ThemePanel(wx.Panel):
    def __init__(self, parent, theme, size):
        wx.Panel.__init__(self, parent, size=size)

        self.theme = theme

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(frame_sizer)

        frame_splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        frame_sizer.Add(frame_splitter, 1, wx.EXPAND)

        objects_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        objects_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        main_frame = wx.GetApp().GetTopWindow()
        self.themes_model = CodesDataViews.ThemesViewModel(theme)
        self.themes_ctrl = CodesDataViews.ThemesViewCtrl(objects_panel, self.themes_model, theme=theme)
        objects_panel_sizer.Add(self.themes_ctrl, 1, wx.EXPAND, 5)
        objects_panel.SetSizer(objects_panel_sizer)

        edit_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        edit_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        usefulness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        usefulness_label = wx.StaticText(edit_panel, label=GUIText.USEFULNESS_LABEL+" ", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=[GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.theme.usefulness_flag is None:
            self.usefulness_ctrl.Select(0)
        elif self.theme.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.theme.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer, 0, wx.ALL, 5)

        self.notes_panel = Notes.NotesPanel(edit_panel)
        self.notes_panel.SetNote(theme.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        edit_panel_sizer.Add(self.notes_panel, 1, wx.EXPAND, 5)
        
        edit_panel.SetSizer(edit_panel_sizer)

        frame_splitter.SetMinimumPaneSize(20)
        frame_splitter.SplitHorizontally(objects_panel, edit_panel)
        frame_splitter.SetSashPosition(int(self.GetSize().GetHeight()/2))

        self.Layout()
        self.themes_ctrl.Expander(None)
    
    def OnUpdateUsefulness(self, event):
        choice = self.usefulness_ctrl.GetSelection()
        if choice == 0:
            self.theme.usefulness_flag = None
        elif choice == 1:
            self.theme.usefulness_flag = True
        elif choice == 2:
            self.theme.usefulness_flag = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated(self)

    def OnUpdateNotes(self, event):
        self.theme.notes, self.theme.notes_string = self.notes_panel.GetNote()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated(self)
    
    def RefreshDetails(self):
        self.themes_model.Cleared()
        self.themes_ctrl.Expander(None)
        if self.theme.usefulness_flag is None:
            self.usefulness_ctrl.Select(0)
        elif self.theme.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.theme.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        self.notes_panel.Unbind(wx.EVT_TEXT)
        self.notes_panel.SetNote(self.theme.notes)
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
        self.sizer.Add(controls_sizer, 0, wx.ALL, 5)

        actions_box = wx.StaticBox(self, label=GUIText.ACTIONS)
        actions_box.SetFont(main_frame.DETAILS_LABEL_FONT)
        actions_sizer = wx.StaticBoxSizer(actions_box, wx.HORIZONTAL)
        controls_sizer.Add(actions_sizer)

        notsure_btn = wx.Button(self, label=GUIText.NOT_SURE)
        notsure_btn.SetToolTip(GUIText.NOT_SURE_HELP)
        notsure_btn.Bind(wx.EVT_BUTTON, self.OnNotSure)
        actions_sizer.Add(notsure_btn)
        useful_btn = wx.Button(self, label=GUIText.USEFUL)
        useful_btn.SetToolTip(GUIText.USEFUL_HELP)
        useful_btn.Bind(wx.EVT_BUTTON, self.OnUseful)
        actions_sizer.Add(useful_btn)
        notuseful_btn = wx.Button(self, label=GUIText.NOT_USEFUL)
        notuseful_btn.SetToolTip(GUIText.NOT_USEFUL_HELP)
        notuseful_btn.Bind(wx.EVT_BUTTON, self.OnNotUseful)
        actions_sizer.Add(notuseful_btn)
        
        view_box = wx.StaticBox(self, label=GUIText.VIEW)
        view_box.SetFont(main_frame.DETAILS_LABEL_FONT)
        view_sizer = wx.StaticBoxSizer(view_box, wx.HORIZONTAL)
        controls_sizer.Add(view_sizer)

        usefulness_combo_ctrl = wx.ComboCtrl(self, value=GUIText.SHOW_USEFULNESS, style=wx.TE_READONLY)
        self.usefulness_popup_ctrl = GenericGUIs.CheckListBoxComboPopup(GUIText.SHOW_USEFULNESS)
        usefulness_combo_ctrl.SetPopupControl(self.usefulness_popup_ctrl)
        view_sizer.Add(usefulness_combo_ctrl, 1)
        usefulness_combo_ctrl.Bind(wx.EVT_COMBOBOX_CLOSEUP, self.OnToggleShowUsefulness)
        self.usefulness_popup_ctrl.AddItem(GUIText.NOT_SURE, Constants.NOT_SURE, True)
        self.usefulness_popup_ctrl.AddItem(GUIText.USEFUL, Constants.USEFUL, True)
        self.usefulness_popup_ctrl.AddItem(GUIText.NOT_USEFUL, Constants.NOT_USEFUL, True)
        longest_string = max([GUIText.SHOW_USEFULNESS, GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], key=len)
        size = usefulness_combo_ctrl.GetSizeFromText(longest_string)
        usefulness_combo_ctrl.SetMinSize(size)
        
        origins_combo_ctrl = wx.ComboCtrl(self, value=GUIText.SHOW_DOCS_FROM, style=wx.TE_READONLY)
        self.origins_popup_ctrl = GenericGUIs.CheckListBoxComboPopup(GUIText.SHOW_DOCS_FROM)
        origins_combo_ctrl.SetPopupControl(self.origins_popup_ctrl)
        view_sizer.Add(origins_combo_ctrl, 1)
        origins_combo_ctrl.Bind(wx.EVT_COMBOBOX_CLOSEUP, self.OnToggleSamples)
        size = origins_combo_ctrl.GetSizeFromText(GUIText.SHOW_DOCS_FROM)
        origins_combo_ctrl.SetMinSize(size)

        self.search_ctrl = wx.SearchCtrl(self)
        self.search_ctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.search_ctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.search_ctrl.SetDescriptiveText(GUIText.SEARCH)
        self.search_ctrl.ShowCancelButton(True)
        extent = self.search_ctrl.GetTextExtent(GUIText.SEARCH)
        size = self.search_ctrl.GetSizeFromTextSize(extent.GetWidth()*4, -1)
        self.search_ctrl.SetMinSize(size)
        controls_sizer.Add(self.search_ctrl, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        
        main_frame = wx.GetApp().GetTopWindow()
        self.documents_model = CodesDataViews.DocumentViewModel(main_frame.datasets[self.dataset_key])
        self.documents_ctrl = CodesDataViews.DocumentViewCtrl(self, self.documents_model)
        self.sizer.Add(self.documents_ctrl, 1, wx.ALL|wx.EXPAND, 5)

        #single dataset mode
        self.origins_popup_ctrl.AddItem(GUIText.DATACOLLECTION_LIST, 'dataset', True)
        self.documents_model.samples_filter.append('dataset')

        self.SetSizerAndFit(self.sizer)
        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)

        logger.info("Finished")    

    def OnNotSure(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotSure")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = None
        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)
        logger.info("Finished")

    def OnUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = True
        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)
        logger.info("Finished")

    def OnNotUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = False
        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)
        logger.info("Finished")
    
    def OnToggleShowUsefulness(self, event):
        self.documents_model.usefulness_filter.clear()
        
        checked_keys = self.usefulness_popup_ctrl.GetCheckedKeys()

        if Constants.NOT_SURE in checked_keys:
            self.documents_model.usefulness_filter.append(None)
        if Constants.USEFUL in checked_keys:
            self.documents_model.usefulness_filter.append(True)
        if Constants.NOT_USEFUL in checked_keys:
            self.documents_model.usefulness_filter.append(False)

        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)

    def OnToggleSamples(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnToggleSamples")
        logger.info("Starting")
        
        origins = self.origins_popup_ctrl.GetCheckedKeys()
        
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
        new_documents_model = CodesDataViews.DocumentViewModel(main_frame.datasets[self.dataset_key])
        new_documents_model.samples_filter.extend(self.documents_model.samples_filter)
        new_documents_ctrl = CodesDataViews.DocumentViewCtrl(self, new_documents_model)
        self.sizer.Replace(self.documents_ctrl, new_documents_ctrl)
        self.documents_ctrl.Destroy()
        self.documents_model = new_documents_model
        self.documents_ctrl = new_documents_ctrl
        self.Layout()
        self.documents_model.Cleared()
        self.documents_ctrl.Expander(None)
        self.Thaw()
        self.DocumentsUpdated()
        logger.info("Finished")

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".DocumentListPanel.DocumentsUpdated")
        logger.info("Starting")

        main_frame = wx.GetApp().GetTopWindow()
        for key in self.origins_popup_ctrl.GetKeys():
            if key not in main_frame.samples and key != 'dataset':
                self.origins_popup_ctrl.RemoveItem(key)
                if key in self.documents_model.samples_filter:
                    self.documents_model.samples_filter.remove(key)
        cur_keys = self.origins_popup_ctrl.GetKeys()
        for key in main_frame.samples:
            if key not in cur_keys:
                self.origins_popup_ctrl.AddItem(main_frame.samples[key].name, key, True)
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
        self.codes_model = CodesDataViews.ObjectCodesViewModel(self.document)
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
        self.codes_ctrl.Expander(None)
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
        self.document.notes, self.document.notes_string = self.notes_panel.GetNote()
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
                bg_colour, fg_colour = GenericUtilities.BackgroundAndForegroundColour(code.colour_rgb)
                new_attr = wx.TextAttr()
                new_attr.SetFlags(wx.TEXT_ATTR_TEXT_COLOUR)
                new_attr.SetBackgroundColour(bg_colour)    
                new_attr.SetTextColour(fg_colour)
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
    def __init__(self, parent, node, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CreateQuotationDialog["+str(node.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(node.name), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.node = node

        instruction_label = wx.StaticText(self, label="Choose a document:")
        sizer.Add(instruction_label, 0, wx.ALL, 5)

        #single dataset mode
        self.positions_model = CodesDataViews.DocumentPositionsViewModel(self.node)
        self.positions_ctrl = CodesDataViews.DocumentPositionsViewCtrl(self, self.positions_model)
        self.positions_model.Cleared()
        self.positions_ctrl.Expander(None)
        self.positions_ctrl.ToggleWindowStyle(wx.dataview.DV_MULTIPLE)
        self.positions_ctrl.SetWindowStyle(wx.dataview.DV_SINGLE)
        sizer.Add(self.positions_ctrl, 1, wx.EXPAND, 5)

        
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

class IncludeCodesDialog(wx.Dialog):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".IncludeCodesDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.INCLUDE_CODES, size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.included_code_keys = []

        main_frame = wx.GetApp().GetTopWindow()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.error_label = wx.StaticText(self, label="")
        self.error_label.SetForegroundColour(wx.Colour(255, 0, 0))
        self.sizer.Add(self.error_label, 0, wx.ALL, 5)
        self.error_label.Hide()

        
        
        self.codes_model = CodesDataViews.CodesViewModel()
        self.codes_ctrl = CodesDataViews.CodesViewCtrl(self, self.codes_model)
        self.sizer.Add(self.codes_ctrl, 1, wx.EXPAND|wx.ALL, 5)

        #Retriever button to collect the requested data
        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.SetLabel(GUIText.INCLUDE_CODES)
        self.sizer.Add(controls_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        self.Layout()

        ok_button.Bind(wx.EVT_BUTTON, self.OnSelect)
        logger.info("Finished")
    
    def OnSelect(self, event):
        for item in self.codes_ctrl.GetSelections():
            node = self.codes_model.ItemToObject(item)
            if isinstance(node, Codes.Code):
                self.included_code_keys.append(node.key)
        
        if len(self.included_code_keys) == 0:
            self.error_label.SetLabel("To be able to include codes at least one code must be selected")
            self.error_label.Show()
        else:
            self.EndModal(wx.ID_OK)
