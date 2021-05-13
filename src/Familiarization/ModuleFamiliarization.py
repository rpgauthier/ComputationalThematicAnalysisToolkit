'''Base Code for Familiatization Module'''
import logging

import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB

import Common.Constants as Constants
import Common.Notes as Notes
from Common.GUIText import Familiarization as GUIText
import Familiarization.SubModuleTokenFilters as SubModuleTokenFilters

class FamiliarizationNotebook(FNB.FlatNotebook):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)

        self.name = "familiarization_module"
        main_frame = wx.GetApp().GetTopWindow()
        self.sample_panels = {}

        #Submodules
        self.filters_submodule = SubModuleTokenFilters.TokenFiltersNotebook(self, size=size)
        self.filters_submodule.Hide()

        #Notes panel for module
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.FAMILIARIZATION_LABEL)

        #Menu for Module
        main_frame = wx.GetApp().GetTopWindow()
        self.view_menu = wx.Menu()
        self.toggle_filters_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                              GUIText.FILTERS_LABEL,
                                                              GUIText.SHOW_HIDE+GUIText.FILTERS_LABEL,
                                                              kind=wx.ITEM_CHECK)
        main_frame.Bind(wx.EVT_MENU, self.OnToggleTokenFilters, self.toggle_filters_menuitem)

        #actions that can be run against module or submodules
        #TODO need to put these somewhere or move to the GUI for the different modules
        self.menu = wx.Menu()
        
        #setup the default visable state
        self.toggle_filters_menuitem.Check(True)
        self.OnToggleTokenFilters(None)

        logger.info("Finished")

    def OnToggleTokenFilters(self, event):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.OnToggleTokenFilters")
        logger.info("Starting")
        if self.toggle_filters_menuitem.IsChecked():
            index = self.GetPageIndex(self.filters_submodule)
            if index is wx.NOT_FOUND:
                self.AddPage(self.filters_submodule, GUIText.FILTERS_LABEL)
                if self.filters_submodule.menu_menuitem is None:
                    self.filters_submodule.menu_menuitem = self.menu.AppendSubMenu(self.filters_submodule.menu, GUIText.FILTERS_LABEL)
                else:
                    self.menu.Append(self.filters_submodule.menu_menuitem)
        else:
            index = self.GetPageIndex(self.filters_submodule)
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
                self.filters_submodule.Hide()
                if self.filters_submodule.menu_menuitem is not None:
                    self.menu.Remove(self.filters_submodule.menu_menuitem)
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.DatasetsUpdated")
        logger.info("Starting")
        #trigger refresh of submodules that depend on dataset
        self.Freeze()
        self.filters_submodule.DatasetsUpdated()
        self.Thaw()
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_BUSY_MSG_CONFIG)

        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        
        if 'filters_submodule' in saved_data:
            self.filters_submodule.Load(saved_data['filters_submodule'])
        if 'filters_toggle_flag' in saved_data:
            self.toggle_filters_menuitem.Check(saved_data['filters_toggle_flag'])
            self.OnToggleTokenFilters(None)
        
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        #trigger save for submodules
        saved_data['filters_submodule'] = self.filters_submodule.Save()
        saved_data['notes'] = self.notes_panel.Save()
        #Save configurations
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
        saved_data['filters_toggle_flag'] = self.toggle_filters_menuitem.IsChecked()
        logger.info("Finished")
        return saved_data
