import logging

import wx

from Common.GUIText import Reviewing as GUIText
import Common.Notes as Notes

class ReviewingPanel(wx.Panel):
    def __init__(self, *args, **kw):
        logger = logging.getLogger(__name__+".ReportingPanel.__init__")
        logger.info("Starting")
        super().__init__(*args, **kw)
        wx.StaticText(self, label="Not Yet Implimented")
        
        #Notes panel for module
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.REVIEWING_LABEL)

        #Menu for Module
        main_frame = wx.GetApp().GetTopWindow()
        self.view_menu = wx.Menu()
        self.view_menu_menuitem = None

        #actions that can be run against module or submodules
        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None

        #setup the default visable state
        
        logger.info("Finished")

    def CodesUpdated(self):
        #Triggered by any function from this module or sub modules.
        #updates the datasets to perform a global refresh
        logger = logging.getLogger(__name__+".ReviewingPanel.CodesUpdated")
        logger.info("Starting")
        logger.info("Finished")
    
    def ModeChange(self):
        logger = logging.getLogger(__name__+".ReportingPanel.CodesUpdated")
        logger.info("Starting")
        logger.info("Finished")

    def Load(self, saved_data):
        '''initalizes Reviewing Module with saved_data'''
        logger = logging.getLogger(__name__+".ReviewingPanel.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_BUSY_MSG_CONFIG)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        '''saves current Collection Module's data'''
        logger = logging.getLogger(__name__+".ReviewingPanel.Save")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
        saved_data = {}
        saved_data['notes'] = self.notes_panel.Save()
        logger.info("Finished")
        return saved_data
