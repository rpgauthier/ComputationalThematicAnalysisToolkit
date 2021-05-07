'''Code for Collection Module Controls'''
import logging
import bz2
from shutil import copyfile
import os.path

import wx
import wx.adv
import _pickle as cPickle

import Common.Notes as Notes
from Common.GUIText import Collection as GUIText
import Collection.SubModuleDatasets as SubModuleDatasets

class CollectionPanel(wx.Panel):
    '''Manages the Collection Module'''
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CollectionNotebook.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        self.name = "collection_module"
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        

        #Each of the submodules
        #default only show dataset panel as other panels depend on having loaded datasets
        self.datasets_submodule = SubModuleDatasets.DatasetsPanel(self, size=size)
        sizer.Add(self.datasets_submodule, 1, wx.EXPAND|wx.ALL, border=5)
        self.SetSizer(sizer)

        #Module's notes
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        index = main_frame.notes_notebook.GetPageIndex(self.notes_panel)
        if index is wx.NOT_FOUND:
            main_frame.notes_notebook.AddPage(self.notes_panel,
                                              GUIText.COLLECTION_LABEL)

        #Menu for Module
        self.view_menu = wx.Menu()
        self.toggle_datasets_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                         GUIText.DATASETSLIST_LABEL,
                                                         GUIText.SHOW_HIDE+GUIText.DATASETSLIST_LABEL,
                                                         kind=wx.ITEM_CHECK)
        main_frame.Bind(wx.EVT_MENU, self.OnToggleDatasets, self.toggle_datasets_menuitem)
        self.toggle_datasetsdata_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                               GUIText.DATASETSDATA_LABEL,
                                                               GUIText.SHOW_HIDE+GUIText.DATASETSDATA_LABEL,
                                                               kind=wx.ITEM_CHECK)
        main_frame.Bind(wx.EVT_MENU, self.OnToggleDatasetsData, self.toggle_datasetsdata_menuitem)
        
        #setup the default visable state
        self.toggle_datasets_menuitem.Check(False)
        self.OnToggleDatasets(None)
        self.toggle_datasetsdata_menuitem.Check(True)
        self.OnToggleDatasetsData(None)
        logger.info("Finished")

    #functions called by GUI (menus, or ctrls)

    def OnToggleDatasets(self, event):
        logger = logging.getLogger(__name__+".CollectionNotebook.OnToggleDatasets")
        logger.info("Starting")
        old_window = self.datasets_submodule.splitter.GetWindow1()
        old_window.Hide()
        if self.toggle_datasets_menuitem.IsChecked():
            self.datasets_submodule.datasetslist_panel.Show()
            self.datasets_submodule.splitter.ReplaceWindow(old_window, self.datasets_submodule.datasetslist_panel)
        else:
            self.datasets_submodule.datasetdetails_panel.Show()
            self.datasets_submodule.splitter.ReplaceWindow(old_window, self.datasets_submodule.datasetdetails_panel)
        self.Layout()
        logger.info("Finished")
    
    def OnToggleDatasetsData(self, event):
        logger = logging.getLogger(__name__+".CollectionNotebook.OnToggleDatasetsData")
        logger.info("Starting")
        if self.toggle_datasetsdata_menuitem.IsChecked():
            self.datasets_submodule.datasetsdata_notebook.Show()
            self.datasets_submodule.splitter.SplitHorizontally(self.datasets_submodule.splitter.GetWindow1(), self.datasets_submodule.datasetsdata_notebook)
            self.datasets_submodule.splitter.SetSashPosition(int(self.GetSize().GetHeight()/4))
        else:
            self.datasets_submodule.datasetsdata_notebook.Hide()
            self.datasets_submodule.splitter.Unsplit(self.datasets_submodule.datasetsdata_notebook)
        self.Layout()
        logger.info("Finished")

    #functions called by other classes or internally

    def DatasetsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".CollectionNotebook.DatasetsUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.Freeze()
        self.datasets_submodule.DatasetsUpdated()
        self.Thaw()

        logger.info("Finished")

    def DocumentsUpdated(self):
        self.datasets_submodule.DocumentsUpdated()

    def Load(self, saved_data):
        '''initalizes DataFamiliarization Module with saved_data'''
        logger = logging.getLogger(__name__+".CollectionNotebook.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_BUSY_MSG_CONFIG)
        if 'datasets_toggle_flag' in saved_data:
            self.toggle_datasets_menuitem.Check(saved_data['datasets_toggle_flag'])
            self.OnToggleDatasets(None)
        if 'datasetsdata_toggle_flag' in saved_data:
            self.toggle_datasetsdata_menuitem.Check(saved_data['datasetsdata_toggle_flag'])
            self.OnToggleDatasetsData(None)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        #load the submodules
        if 'datasets_submodule' in saved_data:
            self.datasets_submodule.Load(saved_data['datasets_submodule'])
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        '''saves current Familiarization Module's data'''
        logger = logging.getLogger(__name__+".CollectionNotebook.Save")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
        saved_data = {}
        #trigger saves of submodules
        saved_data['datasets_submodule'] = self.datasets_submodule.Save()
        saved_data['notes'] = self.notes_panel.Save()
        #save configurations
        saved_data['datasets_toggle_flag'] = self.toggle_datasets_menuitem.IsChecked()
        saved_data['datasetsdata_toggle_flag'] = self.toggle_datasetsdata_menuitem.IsChecked()
        logger.info("Finished")
        return saved_data