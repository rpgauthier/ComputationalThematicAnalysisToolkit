'''Base Code for Sampling Module'''
import logging

import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB

import Common.Notes as Notes
from Common.GUIText import Sampling as GUIText
import Common.Objects.GUIs.Samples as SamplesGUIs

class SamplingNotebook(FNB.FlatNotebook):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".SamplingNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=FNB.FNB_DEFAULT_STYLE|FNB.FNB_NO_X_BUTTON|FNB.FNB_FF2, size=size)
        self.name = "sampling_module"
        self.sample_panels = {}

        self.create_page = SamplesGUIs.SampleCreatePanel(self)
        self.AddPage(self.create_page, "+")

        self.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnDeleteSample)
        self.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CONTEXT_MENU, self.OnChangeSampleName)

        #Notes panel for module
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.SAMPLING_LABEL)

        #Menu for Module
        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None
        
        #setup the default visable state
        
        logger.info("Finished")

    def OnPageChanged(self, event):
        selection = event.GetSelection()
        page = self.GetPage(selection)
        if page == self.create_page:
            self.SetAGWWindowStyleFlag(FNB.FNB_DEFAULT_STYLE|FNB.FNB_NO_X_BUTTON)
        else:
            self.SetAGWWindowStyleFlag(FNB.FNB_DEFAULT_STYLE|FNB.FNB_NO_X_BUTTON|FNB.FNB_X_ON_TAB)

    def OnChangeSampleName(self, event):
        logger = logging.getLogger(__name__+".SamplingNotebook.OnChangeSampleName")
        logger.info("Starting")
        selection = event.GetSelection()
        page = self.GetPage(selection)

        if page != self.create_page:
            old_key = page.sample.key
            with wx.TextEntryDialog(self, GUIText.SAMPLE_NAME_LABEL, value=old_key) as dialog:
                ok_button = wx.FindWindowById(wx.ID_OK, dialog)
                ok_button.SetLabel(GUIText.SAMPLE_CHANGE_NAME_LABEL)
                if dialog.ShowModal() == wx.ID_OK:
                    new_name = dialog.GetValue().replace(" ", "_")
                    main_frame = wx.GetApp().GetTopWindow()
                    if new_name == "":
                        wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                                      GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                        logger.warning('name field is empty')
                    else:
                        sample = main_frame.samples.pop(old_key)
                        sample.name = new_name
                        self.SetPageText(selection, new_name)
                        main_frame.SamplesUpdated()
                        #hook this up to allow toggle of sample specific actions
                        #sample_panel.menu_menuitem.SetItemLabel(new_name)
        logger.info("Finished")

    #Hook this up so that users can toggle a specified sample vis the view menu
    def OnToggleSample(self, event):
        logger = logging.getLogger(__name__+".SamplingNotebook.OnToggleTokenFilters")
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
    
    def OnDeleteSample(self, event):
        logger = logging.getLogger(__name__+".SamplingNotebook.OnCreateSample")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.Freeze()
        selection = event.GetSelection()
        page = self.GetPage(selection)
        if page.sample.key in main_frame.samples:
            confirm_dialog = wx.MessageDialog(self, str(page.sample.name)+GUIText.DELETE_CONFIRMATION+GUIText.DELETE_SAMPLE_WARNING,
                                              GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
            confirm_dialog.SetOKCancelLabels(GUIText.DELETE_SAMPLE_LABEL, GUIText.SKIP)
            if confirm_dialog.ShowModal() == wx.ID_OK:
                main_frame.samples[page.sample.key].DestroyObject()
                del main_frame.samples[page.sample.key]
                del self.sample_panels[page.sample.key]
                main_frame.DocumentsUpdated(self)
            else:
                event.Veto()
        main_frame.Thaw()
        logger.info("Finished")

    def SamplesUpdated(self):
        logger = logging.getLogger(__name__+".SamplingNotebook.SamplesUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Unbind(FNB.EVT_FLATNOTEBOOK_PAGE_CLOSING)
        for key in list(self.sample_panels.keys()):
            if key not in main_frame.samples:
                #remove review_panel and menu
                sample_panel = self.sample_panels[key]
                del self.sample_panels[key]
                index = self.GetPageIndex(sample_panel)
                if sample_panel.menu_menuitem is not None:
                    self.actions_menu.Remove(sample_panel.menu_menuitem)
                if index is not wx.NOT_FOUND:
                    self.DeletePage(index)
        self.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnDeleteSample)
        for key in main_frame.samples:
            if key not in self.sample_panels:
                sample = main_frame.samples[key]
                new_sample_panel = None
                if sample.sample_type == "Random":
                    new_sample_panel = SamplesGUIs.RandomSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                elif sample.sample_type == "LDA":
                    new_sample_panel = SamplesGUIs.TopicSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                    new_sample_panel.Load({})
                elif sample.sample_type == "Biterm":
                    new_sample_panel = SamplesGUIs.TopicSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                    new_sample_panel.Load({})
                elif sample.sample_type == "NMF":
                    new_sample_panel = SamplesGUIs.TopicSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                    new_sample_panel.Load({})
                if new_sample_panel is not None:
                    self.InsertPage(len(self.sample_panels), new_sample_panel, str(sample.name), select=True)
                    self.sample_panels[sample.key] = new_sample_panel
                    #hook this up if need to allow sample specific actions 
                    #new_sample_panel.menu_menuitem = self.actions_menu.AppendSubMenu(new_sample_panel.menu, str(sample_key))

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".SamplingNotebook.DatasetsUpdated")
        logger.info("Starting")
        self.Freeze()
        for key in self.sample_panels:
            self.sample_panels[key].DatasetsUpdated()
        self.Thaw()
        logger.info("Finished")

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".SamplingNotebook.DatasetsUpdated")
        logger.info("Starting")
        self.Freeze()
        for key in self.sample_panels:
            self.sample_panels[key].DocumentsUpdated()
        self.Thaw()
        logger.info("Finished")
    
    def ModeChange(self):
        self.Unbind(FNB.EVT_FLATNOTEBOOK_PAGE_CLOSING)
        for key in list(self.sample_panels.keys()):
            #remove review_panel and menu
            sample_panel = self.sample_panels[key]
            del self.sample_panels[key]
            index = self.GetPageIndex(sample_panel)
            if sample_panel.menu_menuitem is not None:
                self.actions_menu.Remove(sample_panel.menu_menuitem)
            if index is not wx.NOT_FOUND:
                self.DeletePage(index)
        self.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnDeleteSample)
        self.SamplesUpdated()

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".SamplingNotebook.Load")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.SamplesUpdated()

        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".SamplingNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        #trigger save for submodules
        saved_data['notes'] = self.notes_panel.Save()
        #Save configurations
        logger.info("Finished")
        return saved_data
