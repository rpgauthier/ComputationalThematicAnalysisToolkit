import logging
import uuid
import xmlschema

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
        logger = logging.getLogger(__name__+".CodingNotebook["+str(self.name)+"].OnImportCodes")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if len(main_frame.codes) > 0:
            confirm_dialog = wx.MessageDialog(self, GUIText.CODES_IMPORT_CONFIRMATION_REQUEST,
                                            GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
            confirm_dialog.SetOKLabel(GUIText.CODES_IMPORT)
            confirm_flag = confirm_dialog.ShowModal()
        else:
            confirm_flag = wx.ID_OK
        if confirm_flag == wx.ID_OK:

            with wx.FileDialog(self, GUIText.CODES_IMPORT, defaultDir=Constants.SAVED_WORKSPACES_PATH,
                            wildcard="Codebook Exchange Format (*.qdc)|*.qdc",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                # cancel if the user changed their mind
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                # Proceed loading the file chosen by the user
                pathname = file_dialog.GetPath()
                try:
                    def IntegrateImportedCodes(new_codes):
                        for new_key in list(new_codes.keys()):
                            new_code = new_codes[new_key]
                            IntegrateImportedCodes(new_code.subcodes)

                            #Recurively find existing code if it exists
                            def FindCode(sought_code, codes):
                                if sought_code.key in codes:
                                    return codes[sought_code.key]
                                else:
                                    for key in codes:
                                        found_code = FindCode(sought_code, codes[key].subcodes)
                                        if found_code != None:
                                            return found_code
                                return None
                            found_code = FindCode(new_code, main_frame.codes)
                            if found_code != None:
                                #if it does exist ask user if they want to keep both, merge import into imported, merge existing into existing
                                action_dialog = wx.MessageDialog(self, "Code ["+found_code.name+"] already exists.\nWhat action would you like to take?",  GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
                                action_dialog.SetYesNoCancelLabels("Import as new Code", "Update Existing Code", "Skip")
                                action = action_dialog.ShowModal()

                                if action == wx.ID_YES:
                                    old_key = new_code.key
                                    new_code.key = str(uuid.uuid4())
                                    new_codes[new_code.key] = new_code
                                    del new_codes[old_key]
                                elif action == wx.ID_NO:
                                    for existing_subcode_key in list(found_code.subcodes.keys()):
                                        existing_subcode = found_code.subcodes[existing_subcode_key]
                                        if FindCode(existing_subcode, imported_codes) == None:
                                            existing_subcode.parent = new_code
                                            new_code.subcodes[existing_subcode.key] = existing_subcode
                                            del found_code.subcodes[existing_subcode_key]
                                    new_code.connections = found_code.connections
                                    found_code.connections = []
                                    new_code.doc_positions = found_code.doc_positions
                                    found_code.doc_positions = {}
                                    new_code.quotations = found_code.quotations
                                    for quotation in new_code.quotations:
                                        quotation.parent = new_code
                                    found_code.quotations = []
                                    found_code.DestroyObject()
                                elif action == wx.CANCEL:
                                    new_code.DestroyObject()


                    imported_codes = CodesUtilities.QDACodeImporter(pathname)
                    IntegrateImportedCodes(imported_codes)
                    for code_key in imported_codes:
                        main_frame.codes[code_key] = imported_codes[code_key]
                
                    self.codes_model.Cleared()
                    self.codes_ctrl.Expander(None)
                    for dataset_key in self.coding_datasets_panels:
                        self.coding_datasets_panels[dataset_key].DocumentsUpdated()
                        self.coding_datasets_panels[dataset_key].codes_model.Cleared()
                        self.coding_datasets_panels[dataset_key].codes_ctrl.Expander(None)
                        for document_key in self.coding_datasets_panels[dataset_key].document_windows:
                            self.coding_datasets_panels[dataset_key].document_windows[document_key].codes_model.Cleared()
                            self.coding_datasets_panels[dataset_key].document_windows[document_key].codes_ctrl.Expander(None)
                    main_frame.CodesUpdated()
                
                except xmlschema.XMLSchemaValidationError:
                    wx.LogError("Cannot Load file '%s' as it does not contain a valid REFI-QDA Codebook", pathname)
                    logger.error("Failed due to xml validation issue when loading file '%s'", pathname)
                except IOError:
                    wx.LogError("Cannot open file '%s'", pathname)
                    logger.error("Failed to open file '%s'", pathname)
        logger.info("Finished")

    def OnExportCodes(self, event):
        logger = logging.getLogger(__name__+".CodingNotebook["+str(self.name)+"].OnExportCodes")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if len(main_frame.codes) > 0:
            with wx.FileDialog(self, GUIText.CODES_EXPORT, defaultDir=Constants.SAVED_WORKSPACES_PATH,
                               wildcard="Codebook Exchange Format (*.qdc)|*.qdc",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
                # cancel if the user changed their mind
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                # save the current contents in the file
                pathname = file_dialog.GetPath()
                try:
                    main_frame = wx.GetApp().GetTopWindow()
                    CodesUtilities.QDACodeExporter(main_frame.codes, pathname)
                except xmlschema.XMLSchemaValidationError:
                    wx.LogError("XML Validation Error Occured when checking created file '%s'", pathname)
                    logger.error("XML Validation Failed for file '%s'", pathname)
                except IOError:
                    wx.LogError("Cannot save codebook to file '%s'", pathname)
                    logger.error("Failed to save removal to file '%s'", pathname)
        else:
            wx.MessageBox("No Codes available to export")
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

    def DocumentsUpdated(self, source):
        logger = logging.getLogger(__name__+".CodingPanel.DocumentsUpdated")
        logger.info("Starting")
        for dataset_key in self.coding_datasets_panels:
            self.coding_datasets_panels[dataset_key].DocumentsUpdated(source)
        logger.info("Finished")
    
    def CodesUpdated(self):
        logger = logging.getLogger(__name__+".CodingPanel.CodesUpdated")
        logger.info("Starting")
        for dataset_key in self.coding_datasets_panels:
            self.coding_datasets_panels[dataset_key].CodesUpdated()
        self.codes_model.Cleared()

        logger.info("Finished")

    def Load(self, saved_data):
        '''initalizes Coding Module with saved_data'''
        logger = logging.getLogger(__name__+".CodingPanel.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
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
        
        self.DocumentsUpdated(self)
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        '''saves current Coding Module's data'''
        logger = logging.getLogger(__name__+".CodingPanel.Save")
        logger.info("Starting")
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
                self.document_windows[node.key].RefreshDetails()
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

    def DocumentsUpdated(self, source):
        #Triggered by any function from this module or sub modules.
        #updates the datasets to perform a global refresh
        logger = logging.getLogger(__name__+".CodingDatasetPanel.DocumentsUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.documentlist_panel.DocumentsUpdated()

        for node_key in self.document_windows:
            if source != self.document_windows[node_key]:
                self.document_windows[node_key].RefreshDetails()
        logger.info("Finished")
    
    def CodesUpdated(self):
        #Triggered by any function from this module or sub modules.
        #updates the datasets to perform a global refresh
        logger = logging.getLogger(__name__+".CodingDatasetPanel.CodesUpdated")
        logger.info("Starting")
        #sets time that dataset was updated to flag for saving
        #trigger updates of any submodules that use the datasets for rendering
        self.documentlist_panel.DocumentsUpdated()

        for node_key in self.document_windows:
            self.document_windows[node_key].RefreshDetails()
        self.codes_model.Cleared()
        logger.info("Finished")