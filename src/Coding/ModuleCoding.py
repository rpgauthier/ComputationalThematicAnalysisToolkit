import logging
import pickle
from threading import main_thread
from datetime import datetime

import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB
import wx.dataview as dv

import Common.Notes as Notes
import Common.Constants as Constants
from Common.GUIText import Coding as GUIText
import Common.Objects.Datasets as Datasets
import Common.Objects.DataViews.Codes as CodesDataViews
import Common.Objects.GUIs.Codes as CodesGUIs
import Common.Objects.Utilities.Codes as CodesUtilities

#TODO add ability to highlight what data was selected when checking a code. instructions on what was selected would need to be embeded in dataset>document

class CodingNotebook(FNB.FlatNotebook):
    '''Manages the Coding Module'''
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".CodingNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)

        self.name = "coding_module"

        self.coding_datasets_panels = {}

        self.codes_panel = wx.Panel(self)
        main_frame = wx.GetApp().GetTopWindow()
        default_sizer = wx.BoxSizer()
        self.codes_model = CodesDataViews.CodesViewModel(main_frame.codes)
        self.codes_ctrl = CodesDataViews.CodesViewCtrl(self.codes_panel, self.codes_model)
        default_sizer.Add(self.codes_ctrl, 1, wx.ALL|wx.EXPAND, 5)
        self.codes_panel.SetSizer(default_sizer)
        self.codes_panel.Show()
        self.AddPage(self.codes_panel, GUIText.CODES)

        #Module's notes
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.CODING_LABEL)
    
        #Menu for Module
        self.view_menu = wx.Menu()
        self.view_menu_menuitem = None
        #self.menu.AppendSeparator()
        #self.menu.AppendSubMenu(view_menu, GUIText.VIEW_MENU)

        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None
        importCodesItem = self.actions_menu.Append(wx.ID_ANY,
                                                   GUIText.CODES_IMPORT,
                                                   GUIText.CODES_IMPORT_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnImportCodes, importCodesItem)
        exportCodesItem = self.actions_menu.Append(wx.ID_ANY,
                                                   GUIText.CODES_EXPORT,
                                                   GUIText.CODES_EXPORT_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnExportCodes, exportCodesItem)
        
        logger.info("Finished")
 
    def OnImportCodes(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportRemovalSettings")
        logger.info("Starting")
        if wx.MessageBox(GUIText.CODES_IMPORT_CONFIRMATION_REQUEST,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
            # otherwise ask the user what new file to open
            with wx.FileDialog(self, GUIText.CODES_IMPORT, defaultDir='../Workspaces/',
                            wildcard="Code Pickle files (*.code_pk)|*.code_pk",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                # cancel if the user changed their mind
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                # Proceed loading the file chosen by the user
                pathname = file_dialog.GetPath()
                try:
                    main_frame = wx.GetApp().GetTopWindow()    
                    with open(pathname, 'rb') as file:
                        new_codes = pickle.load(file)
                        
                        def UpdateImportedCodes(code):
                            code.connections.clear()
                            for quotation in code.quotations:
                                quotation.DestroyObject()
                            code.quotations.clear()

                            for subcode_key in code.subcodes:
                                UpdateImportedCodes(code.subcodes[subcode_key])
                            
                            i = 1
                            new_code_key = code.key
                            tmp_new_code_key = code.key
                            while not CodesUtilities.CodeKeyUniqueCheck(tmp_new_code_key, main_frame.codes):
                                tmp_new_code_key = new_code_key+"_"+str(i)
                                i = i + 1
                            
                            if tmp_new_code_key != new_code_key:
                                code.key = tmp_new_code_key
                                if code.parent == None:
                                    new_codes[code.key] = code
                                    del new_codes[new_code_key]
                                else:
                                    code.parent.subcodes[code.key] = code
                                    del code.parent.subcodes[new_code_key]

                        for new_code_key in list(new_codes.keys()):
                            UpdateImportedCodes(new_codes[new_code_key])
                        
                        for new_code_key in new_codes:
                            main_frame.codes[new_code_key] = new_codes[new_code_key]
                            main_frame.codes[new_code_key].last_changed_dt = datetime.now()
                    
                    self.codes_model.Cleared()
                    for dataset_key in self.coding_datasets_panels:
                        self.coding_datasets_panels[dataset_key].DocumentsUpdated()
                        self.coding_datasets_panels[dataset_key].codes_model.Cleared()
                        for document_key in self.coding_datasets_panels[dataset_key].document_windows:
                            self.coding_datasets_panels[dataset_key].document_windows[document_key].codes_model.Cleared()
                    main_frame.CodesUpdated()
                except IOError:
                    wx.LogError("Cannot open file '%s'", self.saved_name)
                    logger.error("Failed to open file '%s'", self.saved_name)
        logger.info("Finished")

    def OnExportCodes(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnExportRemovalSettings")
        logger.info("Starting")
        with wx.FileDialog(self, GUIText.CODES_EXPORT, defaultDir='../Workspaces/',
                           wildcard="Code Pickle files (*.code_pk)|*.code_pk",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            # cancel if the user changed their mind
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            # save the current contents in the file
            pathname = file_dialog.GetPath()
            try:
                main_frame = wx.GetApp().GetTopWindow()
                with open(pathname, 'wb') as file:
                    pickle.dump(main_frame.codes, file)
            except IOError:
                wx.LogError("Cannot save current removal settings '%s'", self.saved_name)
                logger.error("Failed to save removal to file '%s'", self.saved_name)
        logger.info("Finished")
    
    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".CodingPanel.DatasetsUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.Freeze()
        
        main_frame = wx.GetApp().GetTopWindow()
        if len(main_frame.datasets) > 0:
            #hide default coding page
            idx = self.GetPageIndex(self.codes_panel)
            if idx >= 0:
                self.RemovePage(idx)
                self.codes_panel.Hide()
            
            #remove any datasets that are no longer present
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
        else:
            #remove any datasets that are no longer present
            for dataset_key in list(self.coding_datasets_panels.keys()):
                idx = self.GetPageIndex(self.coding_datasets_panels[dataset_key])
                self.DeletePage(idx)
                del self.coding_datasets_panels[dataset_key]
            #Show the coding panel
            idx = self.GetPageIndex(self.codes_panel)
            if idx == -1:
                self.codes_panel.Show()
                self.AddPage(self.codes_panel, GUIText.CODES)
                
        self.Thaw()
        logger.info("Finished")

    def DocumentsUpdated(self):
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
        #remove any datasets that were present
        for dataset_key in list(self.coding_datasets_panels.keys()):
            idx = self.GetPageIndex(self.coding_datasets_panels[dataset_key])
            self.DeletePage(idx)
            del self.coding_datasets_panels[dataset_key]
        if len(main_frame.datasets) > 0:
            #hide default coding page
            idx = self.GetPageIndex(self.codes_panel)
            if idx >= 0:
                self.RemovePage(idx)
                self.codes_panel.Hide()
            # add any datasets
            for dataset_key in main_frame.datasets:
                self.coding_datasets_panels[dataset_key] = CodingDatasetPanel(self, dataset_key, size=self.GetSize())
                self.AddPage(self.coding_datasets_panels[dataset_key], str(dataset_key))
        else:
            #Show the coding panel
            idx = self.GetPageIndex(self.codes_panel)
            if idx == -1:
                self.codes_panel.Show()
                self.AddPage(self.codes_panel, GUIText.CODES)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        
        self.DocumentsUpdated()
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

        self.documentlist_panel = CodesGUIs.DocumentListPanel(self.splitter, self.dataset_key)
        self.documentlist_panel.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelectDocument)

        self.default_document_panel = wx.Panel(self.splitter)
        main_frame = wx.GetApp().GetTopWindow()
        default_sizer = wx.BoxSizer()
        self.codes_model = CodesDataViews.CodesViewModel(main_frame.codes)
        self.codes_ctrl = CodesDataViews.CodesViewCtrl(self.default_document_panel, self.codes_model)
        default_sizer.Add(self.codes_ctrl, 1, wx.ALL|wx.EXPAND, 5)
        self.default_document_panel.SetSizer(default_sizer)

        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitHorizontally(self.documentlist_panel, self.default_document_panel)
        self.splitter.SetSashPosition(int(self.GetSize().GetHeight()/4))

        self.sizer.Add(self.splitter, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)

        self.SetSizer(self.sizer)
        logger.info("Finished")
    
    def OnSelectDocument(self, event):
        logger = logging.getLogger(__name__+".CodingDatasetPanel.OnSelectDocument")
        logger.info("Starting")
        selections = self.documentlist_panel.documents_ctrl.GetSelections()
        item = event.GetItem()
        if item.IsOk() and item in selections:
            node = self.documentlist_panel.documents_model.ItemToObject(item)
            if isinstance(node, Datasets.Document):
                self.Freeze()
                if node.key not in self.document_windows:
                    self.document_windows[node.key] = CodesGUIs.DocumentPanel(self.splitter, node, size=(self.GetSize().GetWidth(), int(self.GetSize().GetHeight()/4*3)))
                
                bottom_window = self.splitter.GetWindow2()
                bottom_window.Hide()
                self.splitter.ReplaceWindow(bottom_window, self.document_windows[node.key])
                self.document_windows[node.key].DocumentUpdated()
                self.document_windows[node.key].Show()
                
                self.splitter.Refresh()
                self.Thaw()
        else:
            self.Freeze()
            bottom_window = self.splitter.GetWindow2()
            bottom_window.Hide()
            self.splitter.ReplaceWindow(bottom_window, self.default_document_panel)
            self.codes_model.Cleared()
            self.default_document_panel.Show()
                
            self.splitter.Refresh()
            self.Thaw()
        logger.info("Finished")

    def DatasetsUpdated(self):
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
        #Triggered by any function from this module or sub modules.
        #updates the datasets to perform a global refresh
        logger = logging.getLogger(__name__+".CodingDatasetPanel.DatasetsUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.documentlist_panel.DocumentsUpdated()

        for node_key in self.document_windows:
            self.document_windows[node_key].DocumentUpdated()
        logger.info("Finished")