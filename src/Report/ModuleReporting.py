import logging

import wx

from Common.GUIText import Reporting as GUIText
import Common.Notes as Notes
import Common.Objects.DataViews.Codes as CodesDataViews


class ReportingPanel(wx.Panel):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".ReportingPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        sizer = wx.BoxSizer( wx.VERTICAL)

        main_frame = wx.GetApp().GetTopWindow()
        self.quotations_model = CodesDataViews.SelectedQuotationsViewModel(main_frame.codes)
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
        main_frame.PulseProgressDialog(GUIText.LOAD_BUSY_MSG_CONFIG)
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
