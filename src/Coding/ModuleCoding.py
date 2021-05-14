import logging

import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB
import wx.dataview as dv

from Common import Constants
from Common import Notes
from Common.GUIText import Coding as GUIText
import Common.Objects.Datasets as Datasets
import Common.Objects.GUIs.Datasets as DatasetGUIs

class CodingNotebook(FNB.FlatNotebook):
    '''Manages the Coding Module'''
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CodingNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)

        self.name = "coding_module"
        self.coding_datasets_panels = {}

        #Module's notes
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.CODING_LABEL)
    
        #Menu for Module
        self.view_menu = wx.Menu()
        
        #self.menu.AppendSeparator()
        #view_menu = wx.Menu()
        #self.menu.AppendSubMenu(view_menu, GUIText.VIEW_MENU)

        logger.info("Finished")
    
    def DatasetsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".CodingPanel.DatasetsUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.Freeze()

        #remove any datasets that are no longer present
        main_frame = wx.GetApp().GetTopWindow()
        for dataset_key in list(self.coding_datasets_panels.keys()):
            if dataset_key not in main_frame.datasets:
                idx = self.GetPageIndex(self.coding_datasets_panels[dataset_key])
                self.DeletePage(idx)
                del self.coding_datasets_panels[dataset_key]

        # add any new datasets and update any existing datasets
        for dataset_key in main_frame.datasets:
            if dataset_key in self.coding_datasets_panels:
                self.coding_datasets_panels[dataset_key].DatasetsUpdated()
            else:
                self.coding_datasets_panels[dataset_key] = CodingDatasetPanel(self, dataset_key, size=self.GetSize())
                self.AddPage(self.coding_datasets_panels[dataset_key], str(dataset_key))
                
        self.Thaw()
        logger.info("Finished")

    def DocumentsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".CodingPanel.DocumentsUpdated")
        logger.info("Starting")
        for dataset_key in self.coding_datasets_panels:
            self.coding_datasets_panels[dataset_key].DocumentsUpdated()
        logger.info("Finished")

    def Load(self, saved_data):
        '''initalizes Coding Module with saved_data'''
        logger = logging.getLogger(__name__+".CodingPanel.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_BUSY_MSG_CONFIG)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        '''saves current Coding Module's data'''
        logger = logging.getLogger(__name__+".CodingPanel.Save")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
        saved_data = {}
        #trigger saves of submodules
        saved_data['notes'] = self.notes_panel.Save()
        #save configurations
        logger.info("Finished")
        return saved_data

class CodingDatasetPanel(wx.Panel):
    def __init__(self, parent, dataset_key, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CodingDatasetPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        self.document_windows = {}

        self.dataset_key = dataset_key
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.splitter = wx.SplitterWindow(self)

        self.documentlist_panel = DatasetGUIs.DocumentListPanel(self.splitter, self.dataset_key)
        self.documentlist_panel.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelectDocument)

        self.default_document_panel = wx.Panel(self.splitter)

        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitHorizontally(self.documentlist_panel, self.default_document_panel)
        self.splitter.SetSashPosition(int(self.GetSize().GetHeight()/4))

        self.sizer.Add(self.splitter, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

        self.SetSizer(self.sizer)
        logger.info("Finished")
    
    def OnSelectDocument(self, event):
        logger = logging.getLogger(__name__+".CodingDatasetPanel.OnSelectDocument")
        logger.info("Starting")
        item = event.GetItem()
        if item.IsOk():
            node = self.documentlist_panel.documents_model.ItemToObject(item)
            if isinstance(node, Datasets.Document):
                self.Freeze()
                if node.key not in self.document_windows:
                    self.document_windows[node.key] = DatasetGUIs.DocumentPanel(self.splitter, node, size=(self.GetSize().GetWidth(), int(self.GetSize().GetHeight()/4*3)))
                
                bottom_window = self.splitter.GetWindow2()
                bottom_window.Hide()
                self.splitter.ReplaceWindow(bottom_window, self.document_windows[node.key])
                self.document_windows[node.key].DocumentUpdated()
                self.document_windows[node.key].Show()
                
                self.splitter.Refresh()
                self.Thaw()
        logger.info("Finished")

    def DatasetsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".CodingDatasetPanel.DatasetsUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.Freeze()
        self.documentlist_panel.DatasetsUpdated()
        bottom_window = self.splitter.GetWindow2()
        if bottom_window is not self.default_document_panel:
            self.default_document_panel.Show()
            self.splitter.ReplaceWindow(bottom_window, self.default_document_panel)
            self.document_windows.clear()
        self.Thaw()
        logger.info("Finished")

    def DocumentsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".CodingDatasetPanel.DatasetsUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.documentlist_panel.DocumentsUpdated()

        for node_key in self.document_windows:
            self.document_windows[node_key].DocumentUpdated()
        logger.info("Finished")