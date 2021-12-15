import logging

import wx

from Common.GUIText import Reporting as GUIText
import Common.Constants as Constants
import Common.Notes as Notes
import Common.Objects.DataViews.Codes as CodesDataViews
import Common.Objects.GUIs.Generic as GenericGUIs


class ReportingPanel(wx.Panel):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".ReportingPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        main_frame = wx.GetApp().GetTopWindow()

        sizer = wx.BoxSizer( wx.VERTICAL)

        controls_sizer = wx.BoxSizer()
        sizer.Add(controls_sizer, 0, wx.ALL, 5)
        
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

        theme_filter_combo_ctrl = wx.ComboCtrl(self, value=GUIText.THEME_FILTERS, style=wx.TE_READONLY)
        self.theme_filter_popup_ctrl = GenericGUIs.CheckListBoxComboPopup(GUIText.CODE_FILTERS)
        theme_filter_combo_ctrl.SetPopupControl(self.theme_filter_popup_ctrl)
        view_sizer.Add(theme_filter_combo_ctrl, 1)
        theme_filter_combo_ctrl.Bind(wx.EVT_COMBOBOX_CLOSEUP, self.OnFilterThemes)
        self.theme_filter_popup_ctrl.AddItem(GUIText.NOT_SURE, Constants.NOT_SURE, True)
        self.theme_filter_popup_ctrl.AddItem(GUIText.USEFUL, Constants.USEFUL, True)
        self.theme_filter_popup_ctrl.AddItem(GUIText.NOT_USEFUL, Constants.NOT_USEFUL, True)
        longest_string = max([GUIText.CODE_FILTERS, GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], key=len)
        size = theme_filter_combo_ctrl.GetSizeFromText(longest_string)
        theme_filter_combo_ctrl.SetMinSize(size)

        code_filter_combo_ctrl = wx.ComboCtrl(self, value=GUIText.CODE_FILTERS, style=wx.TE_READONLY)
        self.code_filter_popup_ctrl = GenericGUIs.CheckListBoxComboPopup(GUIText.CODE_FILTERS)
        code_filter_combo_ctrl.SetPopupControl(self.code_filter_popup_ctrl)
        view_sizer.Add(code_filter_combo_ctrl, 1)
        code_filter_combo_ctrl.Bind(wx.EVT_COMBOBOX_CLOSEUP, self.OnFilterCodes)
        self.code_filter_popup_ctrl.AddItem(GUIText.NOT_SURE, Constants.NOT_SURE, True)
        self.code_filter_popup_ctrl.AddItem(GUIText.USEFUL, Constants.USEFUL, True)
        self.code_filter_popup_ctrl.AddItem(GUIText.NOT_USEFUL, Constants.NOT_USEFUL, True)
        longest_string = max([GUIText.CODE_FILTERS, GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], key=len)
        size = code_filter_combo_ctrl.GetSizeFromText(longest_string)
        code_filter_combo_ctrl.SetMinSize(size)

        quote_filter_combo_ctrl = wx.ComboCtrl(self, value=GUIText.QUOTE_FILTERS, style=wx.TE_READONLY)
        self.quote_filter_popup_ctrl = GenericGUIs.CheckListBoxComboPopup(GUIText.QUOTE_FILTERS)
        quote_filter_combo_ctrl.SetPopupControl(self.quote_filter_popup_ctrl)
        view_sizer.Add(quote_filter_combo_ctrl, 1)
        quote_filter_combo_ctrl.Bind(wx.EVT_COMBOBOX_CLOSEUP, self.OnFilterQuotes)
        self.quote_filter_popup_ctrl.AddItem(GUIText.NOT_SURE, Constants.NOT_SURE, True)
        self.quote_filter_popup_ctrl.AddItem(GUIText.USEFUL, Constants.USEFUL, True)
        self.quote_filter_popup_ctrl.AddItem(GUIText.NOT_USEFUL, Constants.NOT_USEFUL, True)
        longest_string = max([GUIText.QUOTE_FILTERS, GUIText.NOT_SURE, GUIText.USEFUL, GUIText.NOT_USEFUL], key=len)
        size = quote_filter_combo_ctrl.GetSizeFromText(longest_string)
        quote_filter_combo_ctrl.SetMinSize(size)

        main_frame = wx.GetApp().GetTopWindow()
        self.quotations_model = CodesDataViews.SelectedQuotationsViewModel()
        self.quotations_model.theme_usefulness_filter.append(None)
        self.quotations_model.theme_usefulness_filter.append(True)
        self.quotations_model.theme_usefulness_filter.append(False)
        self.quotations_model.code_usefulness_filter.append(None)
        self.quotations_model.code_usefulness_filter.append(True)
        self.quotations_model.code_usefulness_filter.append(False)
        self.quotations_model.quote_usefulness_filter.append(None)
        self.quotations_model.quote_usefulness_filter.append(True)
        self.quotations_model.quote_usefulness_filter.append(False)
        self.quotations_ctrl = CodesDataViews.SelectedQuotationsViewCtrl(self, self.quotations_model)
        sizer.Add(self.quotations_ctrl, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        
        #Notes panel for module
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.REPORTING_LABEL)

        #Menu for Module
        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None
        
        #setup the default visable state
        
        logger.info("Finished")

    def OnNotSure(self, event):
        logger = logging.getLogger(__name__+".ReportingPanel.OnNotSure")
        logger.info("Starting")
        for item in self.quotations_ctrl.GetSelections():
            node = self.quotations_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = None
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")

    def OnUseful(self, event):
        logger = logging.getLogger(__name__+".ReportingPanel.OnUseful")
        logger.info("Starting")
        for item in self.quotations_ctrl.GetSelections():
            node = self.quotations_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = True
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")

    def OnNotUseful(self, event):
        logger = logging.getLogger(__name__+".ReportingPanel.OnNotUseful")
        logger.info("Starting")
        for item in self.quotations_ctrl.GetSelections():
            node = self.quotations_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = False
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")
    
    def OnFilterThemes(self, event):
        logger = logging.getLogger(__name__+".ReportingPanel.OnFilterCodes")
        logger.info("Starting")
        self.quotations_model.theme_usefulness_filter.clear()
        checked_keys = self.theme_filter_popup_ctrl.GetCheckedKeys()
        if Constants.NOT_SURE in checked_keys:
            self.quotations_model.theme_usefulness_filter.append(None)
        if Constants.USEFUL in checked_keys:
            self.quotations_model.theme_usefulness_filter.append(True)
        if Constants.NOT_USEFUL in checked_keys:
            self.quotations_model.theme_usefulness_filter.append(False)
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")

    def OnFilterCodes(self, event):
        logger = logging.getLogger(__name__+".ReportingPanel.OnFilterCodes")
        logger.info("Starting")
        self.quotations_model.code_usefulness_filter.clear()
        checked_keys = self.code_filter_popup_ctrl.GetCheckedKeys()
        if Constants.NOT_SURE in checked_keys:
            self.quotations_model.code_usefulness_filter.append(None)
        if Constants.USEFUL in checked_keys:
            self.quotations_model.code_usefulness_filter.append(True)
        if Constants.NOT_USEFUL in checked_keys:
            self.quotations_model.code_usefulness_filter.append(False)
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")

    def OnFilterQuotes(self, event):
        logger = logging.getLogger(__name__+".ReportingPanel.OnFilterQuotes")
        logger.info("Starting")
        self.quotations_model.quote_usefulness_filter.clear()
        checked_keys = self.quote_filter_popup_ctrl.GetCheckedKeys()
        if Constants.NOT_SURE in checked_keys:
            self.quotations_model.quote_usefulness_filter.append(None)
        if Constants.USEFUL in checked_keys:
            self.quotations_model.quote_usefulness_filter.append(True)
        if Constants.NOT_USEFUL in checked_keys:
            self.quotations_model.quote_usefulness_filter.append(False)
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")


    def CodesUpdated(self):
        #Triggered by any function from this module or sub modules.
        #updates the datasets to perform a global refresh
        logger = logging.getLogger(__name__+".ReportingPanel.CodesUpdated")
        logger.info("Starting")
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")
    
    def ModeChange(self):
        logger = logging.getLogger(__name__+".ReportingPanel.CodesUpdated")
        logger.info("Starting")
        self.quotations_ctrl.UpdateColumns()
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        logger.info("Finished")

    def Load(self, saved_data):
        '''initalizes Reporting Module with saved_data'''
        logger = logging.getLogger(__name__+".ReportingPanel.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.StepProgressDialog(GUIText.LOAD_BUSY_CONFIG_STEP)
        self.quotations_model.Cleared()
        self.quotations_ctrl.Expander(None)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        '''saves current Reporting Module's data'''
        logger = logging.getLogger(__name__+".ReportingPanel.Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['notes'] = self.notes_panel.Save()
        logger.info("Finished")
        return saved_data
