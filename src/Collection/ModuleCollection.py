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
        
        self.labelfields_dialogs = {}
        self.computationfields_dialogs = {}

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        #splitter used to control panels that appear in this module
        
        #Each of the panels that could be used for this module:
        self.datasetretrieval_panel = SubModuleDatasets.DatasetRetrievalPanel(self)
        self.sizer.Add(self.datasetretrieval_panel)

        self.splitter = wx.SplitterWindow(self)
        self.datasetdetails_panel = SubModuleDatasets.DatasetDetailsPanel(self.splitter, self)
        self.datasetslist_panel = SubModuleDatasets.DatasetsListPanel(self.splitter, self)
        self.datasetslist_panel.datasets_ctrl.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnShowData)
        self.datasetslist_panel.Hide()
        self.datasetsdata_notebook = DatasetsGUIs.DataNotebook(self.splitter, self.GetSize())
        self.datasetsdata_notebook.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnChangeDatasetDataTab)
        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitHorizontally(self.datasetdetails_panel, self.datasetsdata_notebook)
        sash_height = int(self.datasetdetails_panel.GetBestSize().GetHeight()) + 5
        self.splitter.SetSashPosition(sash_height)
        self.splitter.Hide()
        
        #Module's notes
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.COLLECTION_LABEL)

        #Menu for Module
        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None

        #setup the default visable state
        self.Layout()
        logger.info("Finished")

    #functions called by GUI (menus, or ctrls)
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
        if not main_frame.options_dict['multipledatasets_mode']:
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
        main_frame = wx.GetApp().GetTopWindow()

        self.datasetslist_panel.DatasetsUpdated()
        self.datasetsdata_notebook.DatasetsUpdated()
        
        self.sizer.Clear()
        self.splitter.Hide()
        self.datasetretrieval_panel.Hide()
        if len(main_frame.datasets) == 0:
            self.datasetretrieval_panel.Show()
            self.sizer.Add(self.datasetretrieval_panel, proportion=1, flag=wx.EXPAND, border=5)
        else:
            self.splitter.Show()
            self.sizer.Add(self.splitter, proportion=1, flag=wx.EXPAND, border=5)
        
        for key in list(self.labelfields_dialogs.keys()):
            dataset = self.labelfields_dialogs[key].dataset
            if dataset.key not in main_frame.datasets:
                self.labelfields_dialogs[key].Destroy()
                del self.labelfields_dialogs[key]
            else:
                self.labelfields_dialogs[key].SetTitle(str(dataset.name)+" "+GUIText.CUSTOMIZE_LABEL_FIELDS)
                self.labelfields_dialogs[key].fields_panel.chosen_fields_model.Cleared()
        for key in list(self.computationfields_dialogs.keys()):
            dataset = self.computationfields_dialogs[key].dataset
            if dataset.key not in main_frame.datasets:
                self.computationfields_dialogs[key].Destroy()
                del self.computationfields_dialogs[key]
            else:
                self.computationfields_dialogs[key].SetTitle(str(dataset.name)+" "+GUIText.CUSTOMIZE_LABEL_FIELDS)
                self.computationfields_dialogs[key].fields_panel.chosen_fields_model.Cleared()
        self.OnChangeDatasetDataTab(None)
        self.Thaw()

        logger.info("Finished")

    def ModeChange(self):
        logger = logging.getLogger(__name__+".CollectionNotebook.OnToggleDatasets")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        self.sizer.Clear()
        self.splitter.Hide()
        self.datasetretrieval_panel.Hide()
        if len(main_frame.datasets) == 0:
            self.datasetretrieval_panel.Show()
            self.sizer.Add(self.datasetretrieval_panel, proportion=1, flag=wx.EXPAND, border=5)
        else:
            self.splitter.Show()
            self.sizer.Add(self.splitter, proportion=1, flag=wx.EXPAND, border=5)
        if not main_frame.options_dict['adjustable_label_fields_mode']:
            for key in list(self.labelfields_dialogs.keys()):
                self.labelfields_dialogs[key].Destroy()
                del self.labelfields_dialogs[key]
        if not main_frame.options_dict['adjustable_computation_fields_mode']:
            for key in list(self.computationfields_dialogs.keys()):
                self.computationfields_dialogs[key].Destroy()
                del self.computationfields_dialogs[key]
        self.datasetretrieval_panel.ChangeMode()
        index = self.datasetsdata_notebook.GetSelection()
        if index == -1:
            self.datasetdetails_panel.ChangeDataset(None)
            self.datasetslist_panel.DatasetsUpdated()
        else:
            selected_panel = self.datasetsdata_notebook.GetPage(index)
            self.datasetdetails_panel.ChangeDataset(selected_panel.dataset)
            self.datasetslist_panel.DatasetsUpdated()
        self.Thaw()
        
        #when done inside a freeze it leaves artifacts of previous panel
        old_window = self.splitter.GetWindow1()
        if main_frame.options_dict['multipledatasets_mode'] and old_window != self.datasetslist_panel:
            old_window.Hide()
            self.datasetslist_panel.Show()
            self.splitter.ReplaceWindow(old_window, self.datasetslist_panel)
            sash_height = int(self.GetSize().GetHeight()/6)
            self.splitter.SetSashPosition(sash_height)
        elif not main_frame.options_dict['multipledatasets_mode'] and old_window != self.datasetdetails_panel:
            old_window.Hide()
            self.datasetdetails_panel.Show()
            self.splitter.ReplaceWindow(old_window, self.datasetdetails_panel)
            sash_height = int(self.datasetdetails_panel.GetBestSize().GetHeight()) + 5
            self.splitter.SetSashPosition(sash_height)
        
        self.Fit()
        logger.info("Finished")

    def Load(self, saved_data):
        '''initalizes Collection Module with saved_data'''
        logger = logging.getLogger(__name__+".CollectionNotebook.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        
        self.sizer.Clear()
        self.splitter.Hide()
        self.datasetretrieval_panel.Hide()
        if len(main_frame.datasets) == 0:
            self.datasetretrieval_panel.Show()
            self.sizer.Add(self.datasetretrieval_panel, proportion=1, flag=wx.EXPAND, border=5)
        else:
            self.splitter.Show()
            self.sizer.Add(self.splitter, proportion=1, flag=wx.EXPAND, border=5)

        self.datasetslist_panel.DatasetsUpdated()
        self.datasetsdata_notebook.DatasetsUpdated()
        
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        self.Thaw()
        logger.info("Finished")

    def Save(self,):
        '''saves current Collection Module's data'''
        logger = logging.getLogger(__name__+".CollectionNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['notes'] = self.notes_panel.Save()
        #save configurations
        logger.info("Finished")
        return saved_data