'''Code for Collection Module Controls'''
import logging

import wx
import wx.adv
import wx.dataview as dv
import External.wxPython.flatnotebook_fix as FNB

from Common.GUIText import Collection as GUIText
import Common.Notes as Notes
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Collection.SubModuleDatasets as SubModuleDatasets

class CollectionPanel(wx.Panel):
    '''Manages the Collection Module'''
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CollectionNotebook.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        self.name = "collection_module"
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        #splitter used to control panels that appear in this module
        self.splitter = wx.SplitterWindow(self)

        #Each of the panels that could be used for this module:
        self.datasetdetails_panel = SubModuleDatasets.DatasetDetailsPanel(self.splitter)

        self.datasetslist_panel = SubModuleDatasets.DatasetsListPanel(self.splitter)
        self.datasetslist_panel.datasets_ctrl.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnShowData)
        self.datasetslist_panel.Hide()
        
        self.datasetsdata_notebook = DatasetsGUIs.DataNotebook(self.splitter)
        self.datasetsdata_notebook.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnChangeDatasetDataTab)

        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitHorizontally(self.datasetdetails_panel, self.datasetsdata_notebook)
        sash_height = int(self.datasetdetails_panel.GetBestSize().GetHeight()) + 5
        self.splitter.SetSashPosition(sash_height)
        
        sizer.Add(self.splitter, proportion=1, flag=wx.EXPAND, border=5)
        self.SetSizer(sizer)

        #Module's notes
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.COLLECTION_LABEL)

        #Menu for Module
        self.view_menu = wx.Menu()
        self.view_menu_menuitem = None
        self.toggle_datasetsdata_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                               GUIText.DATASETSDATA_LABEL,
                                                               GUIText.SHOW_HIDE+GUIText.DATASETSDATA_LABEL,
                                                               kind=wx.ITEM_CHECK)
        main_frame.Bind(wx.EVT_MENU, self.OnToggleDatasetsData, self.toggle_datasetsdata_menuitem)
        
        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None

        #setup the default visable state
        self.toggle_datasetsdata_menuitem.Check(True)
        self.OnToggleDatasetsData(None)
        logger.info("Finished")

    #functions called by GUI (menus, or ctrls)
    def OnToggleDatasetsData(self, event):
        logger = logging.getLogger(__name__+".CollectionNotebook.OnToggleDatasetsData")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if self.toggle_datasetsdata_menuitem.IsChecked():
            self.datasetsdata_notebook.Show()
            self.splitter.SplitHorizontally(self.splitter.GetWindow1(), self.datasetsdata_notebook)
            
            if main_frame.multipledatasets_mode:
                sash_height = int(self.GetSize().GetHeight()/6)
            else:
                sash_height = int(self.datasetdetails_panel.GetBestSize().GetHeight()) + 5
            self.splitter.SetSashPosition(sash_height)
        else:
            self.datasetsdata_notebook.Hide()
            self.splitter.Unsplit(self.datasetsdata_notebook)
        self.Layout()
        logger.info("Finished")

    def OnShowData(self, event):
        logger = logging.getLogger(__name__+".CollectionNotebook.OnShowData")
        logger.info("Starting")
        node = self.datasetslist_panel.datasets_model.ItemToObject(event.GetItem())
        self.datasetsdata_notebook.ShowData(node)
        self.Refresh()
        logger.info("Finished")

    def OnChangeDatasetDataTab(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnChangeDatasetDataTab")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        index = self.datasetsdata_notebook.GetSelection()
        if index == -1:
            self.datasetdetails_panel.ChangeDataset(None)
        else:
            selected_panel = self.datasetsdata_notebook.GetPage(index)
            self.datasetdetails_panel.ChangeDataset(selected_panel.dataset)
        if main_frame.multipledatasets_mode == False:
            sash_height = int(self.datasetdetails_panel.GetBestSize().GetHeight()) + 5
            self.splitter.SetSashPosition(sash_height)
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
        self.datasetslist_panel.DatasetsUpdated()
        self.datasetsdata_notebook.DatasetsUpdated()
        self.OnChangeDatasetDataTab(None)
        self.Thaw()

        logger.info("Finished")

    def ModeChange(self):
        logger = logging.getLogger(__name__+".CollectionNotebook.OnToggleDatasets")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        old_window = self.splitter.GetWindow1()
        if main_frame.multipledatasets_mode and old_window != self.datasetslist_panel:
            old_window.Hide()
            self.datasetslist_panel.Show()
            self.splitter.ReplaceWindow(old_window, self.datasetslist_panel)
            sash_height = int(self.GetSize().GetHeight()/6)
            self.splitter.SetSashPosition(sash_height)
        elif old_window != self.datasetdetails_panel:
            old_window.Hide()
            self.datasetdetails_panel.Show()
            self.splitter.ReplaceWindow(old_window, self.datasetdetails_panel)
            sash_height = int(self.datasetdetails_panel.GetBestSize().GetHeight()) + 5
            self.splitter.SetSashPosition(sash_height)
        self.Layout()
        logger.info("Finished")

    def Load(self, saved_data):
        '''initalizes Collection Module with saved_data'''
        logger = logging.getLogger(__name__+".CollectionNotebook.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_BUSY_MSG_CONFIG)
        if 'datasetsdata_toggle_flag' in saved_data:
            self.toggle_datasetsdata_menuitem.Check(saved_data['datasetsdata_toggle_flag'])
            self.OnToggleDatasetsData(None)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        '''saves current Collection Module's data'''
        logger = logging.getLogger(__name__+".CollectionNotebook.Save")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
        saved_data = {}
        saved_data['notes'] = self.notes_panel.Save()
        #save configurations
        saved_data['datasetsdata_toggle_flag'] = self.toggle_datasetsdata_menuitem.IsChecked()
        logger.info("Finished")
        return saved_data