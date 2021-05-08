'''Base Code for Familiatization Module'''
import logging
import bz2
from shutil import copyfile
import os.path

import _pickle as cPickle
import wx
import wx.aui
import wx.dataview as dv

import Common.Constants as Constants
import Common.Notes as Notes
import Common.Objects.Datasets as Datasets
from Common.GUIText import Familiarization as GUIText
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Common.Objects.GUIs.Samples as SamplesGUIs
import Familiarization.SubModuleTokenFilters as SubModuleTokenFilters
import Familiarization.SubModuleSamples as SubModuleSamples

class FamiliarizationNotebook(wx.aui.AuiNotebook):
    def __init__(self, parent, samples, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.__init__")
        logger.info("Starting")
        wx.aui.AuiNotebook.__init__(self, parent, style=Constants.NOTEBOOK_MOVEABLE, size=size)

        self.name = "familiarization_module"
        self.samples = samples
        self.sample_panels = {}

        #Submodules
        self.inspect_submodule = DatasetsGUIs.DataNotebook(self, size=size)
        self.inspect_submodule.Hide()
        self.filters_submodule = SubModuleTokenFilters.TokenFiltersNotebook(self, size=size)
        self.filters_submodule.Hide()
        self.sample_list_panel = SamplesGUIs.SampleListPanel(self, self.samples, size=size)
        self.sample_list_panel.Hide()
        self.sample_list_panel.Bind(dv.EVT_DATAVIEW_ITEM_EDITING_DONE, self.OnSampleKeyChange)


        #Notes panel for module
        main_frame = wx.GetApp().GetTopWindow()
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.FAMILIARIZATION_LABEL)

        #Menu for Module
        main_frame = wx.GetApp().GetTopWindow()
        self.view_menu = wx.Menu()   
        self.toggle_inspect_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                        GUIText.INSPECT_LABEL,
                                                        GUIText.SHOW_HIDE+GUIText.INSPECT_LABEL,
                                                        kind=wx.ITEM_CHECK)
        main_frame.Bind(wx.EVT_MENU, self.OnToggleInspect, self.toggle_inspect_menuitem)
        self.toggle_filters_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                              GUIText.FILTERS_LABEL,
                                                              GUIText.SHOW_HIDE+GUIText.FILTERS_LABEL,
                                                              kind=wx.ITEM_CHECK)
        main_frame.Bind(wx.EVT_MENU, self.OnToggleTokenFilters, self.toggle_filters_menuitem)
        self.toggle_samples_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                       GUIText.SAMPLES_LABEL,
                                                       GUIText.SHOW_HIDE+GUIText.SAMPLES_LABEL,
                                                       kind=wx.ITEM_CHECK)
        main_frame.Bind(wx.EVT_MENU, self.OnToggleSamples, self.toggle_samples_menuitem)

        #actions that can be run against module or submodules
        #TODO need to put these somewhere or move to the GUI for the different modules
        self.menu = wx.Menu()
        
        #setup the default visable state
        self.toggle_inspect_menuitem.Check(True)
        self.OnToggleInspect(None)
        self.toggle_filters_menuitem.Check(True)
        self.OnToggleTokenFilters(None)
        self.toggle_samples_menuitem.Check(True)
        self.OnToggleSamples(None)

        logger.info("Finished")

    #overide to handle renaming sample panels
    def OnSampleKeyChange(self, event):
        item = event.GetItem()
        value = event.GetValue().replace(" ", "_")
        sample = self.sample_list_panel.samples_model.ItemToObject(item)
        if sample.key != value:
            sample_panel = self.sample_panels.pop(sample.key)
            sample_panel.menu_menuitem.SetItemLabel(value)
            self.sample_panels[value] = sample_panel
            index = self.GetPageIndex(sample_panel)
            if index is not wx.NOT_FOUND:
                self.SetPageText(index, value)
            self.sample_list_panel.OnSampleKeyChange(event)

    def OnToggleInspect(self, event):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.OnToggleInspect")
        logger.info("Starting")
        if self.toggle_inspect_menuitem.IsChecked():
            index = self.GetPageIndex(self.inspect_submodule)
            if index is wx.NOT_FOUND:
                self.AddPage(self.inspect_submodule, GUIText.INSPECT_LABEL)
                #if self.inspect_submodule.menu_menuitem is None:
                #    self.inspect_submodule.menu_menuitem = self.menu.AppendSubMenu(self.inspect_submodule.menu, GUIText.FILTERS_LABEL)
                #else:
                #    self.menu.Append(self.inspect_submodule.menu_menuitem)
        else:
            index = self.GetPageIndex(self.inspect_submodule)
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
                self.inspect_submodule.Hide()
                #if self.inspect_submodule.menu_menuitem is not None:
                #    self.menu.Remove(self.inspect_submodule.menu_menuitem)
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

    #toggles on or off all samples
    #TODO decide whether to split it up
    def OnToggleSamples(self, event):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.OnToggleSamples")
        logger.info("Starting")
        if self.toggle_samples_menuitem.IsChecked():
            index = self.GetPageIndex(self.sample_list_panel)
            if index is wx.NOT_FOUND:
                self.AddPage(self.sample_list_panel, GUIText.SAMPLES_LABEL)
                if self.sample_list_panel.menu_menuitem is None:
                    self.sample_list_panel.menu_menuitem = self.menu.AppendSubMenu(self.sample_list_panel.menu, GUIText.SAMPLES_LABEL)
                else:
                    self.menu.Append(self.sample_list_panel.menu_menuitem)
            for key in self.sample_panels:
                index = self.GetPageIndex(self.sample_panels[key])
                if index is wx.NOT_FOUND:
                    self.AddPage(self.sample_panels[key], str(key))
                    if self.sample_panels[key].menu_menuitem is None:
                        self.sample_panels[key].menu_menuitem = self.menu.AppendSubMenu(self.sample_panels[key].menu, str(key))
                    else:
                        self.menu.Append(self.sample_panels[key].menu_menuitem)
        else:
            index = self.GetPageIndex(self.sample_list_panel)
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
                self.sample_list_panel.Hide()
                if self.sample_list_panel.menu_menuitem is not None:
                    self.menu.Remove(self.sample_list_panel.menu_menuitem)
            for key in self.sample_panels:
                index = self.GetPageIndex(self.sample_panels[key])
                if index is not wx.NOT_FOUND:
                    self.RemovePage(index)
                    self.sample_panels[key].Hide()
                    if self.sample_panels[key].menu_menuitem is not None:
                        self.menu.Remove(self.sample_panels[key].menu_menuitem)
            
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.DatasetsUpdated")
        logger.info("Starting")
        #trigger refresh of submodules that depend on dataset
        self.Freeze()
        self.inspect_submodule.DatasetsUpdated()
        self.filters_submodule.DatasetsUpdated()
        self.Thaw()
        logger.info("Finished")

    def SamplesUpdated(self):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.SamplesUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.sample_list_panel.samples_model.Cleared()
        for key in list(self.sample_panels.keys()):
            if key not in main_frame.samples:
                #remove review_panel and menu
                sample_panel = self.sample_panels[key]
                index = self.GetPageIndex(sample_panel)
                if index is not wx.NOT_FOUND:
                    self.RemovePage(index)
                if sample_panel.menu_menuitem is not None:
                    self.menu.Remove(sample_panel.menu_menuitem)
                del self.sample_panels[key]

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.DatasetsUpdated")
        logger.info("Starting")
        #trigger refresh of submodules that depend on dataset
        self.Freeze()
        for key in self.sample_panels:
            self.sample_panels[key].DocumentsUpdated()
        self.Thaw()
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.Load")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_BUSY_MSG_CONFIG)
        #refresh the dataview generating the sample list
        self.sample_list_panel.samples_model.Cleared()
        #remove all current sample panels
        for key in self.sample_panels:
            index = self.GetPageIndex(self.sample_panels[key])
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
                self.menu.Remove(self.sample_panels[key].menu_menuitem)
        self.sample_panels.clear()
            
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        
        if 'filters_submodule' in saved_data:
            self.filters_submodule.Load(saved_data['filters_submodule'])
        if 'filters_toggle_flag' in saved_data:
            self.toggle_filters_menuitem.Check(saved_data['filters_toggle_flag'])
            self.OnToggleTokenFilters(None)
        if len(main_frame.samples) > 0:
            #self.samples_submodule.Load(saved_data['samples_submodule'])
            #create new sample_panels for each sample
            for sample_key in self.samples:
                sample = self.samples[sample_key]
                new_sample_panel = None
                if sample.sample_type == "Random":
                    new_sample_panel = SamplesGUIs.RandomSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                elif sample.sample_type == "LDA":
                    new_sample_panel = SamplesGUIs.TopicSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                elif sample.sample_type == "Biterm":
                    new_sample_panel = SamplesGUIs.TopicSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                if new_sample_panel is not None:
                    self.sample_panels[sample_key] = new_sample_panel
                    if saved_data['samples_toggle_flag']:
                        self.AddPage(new_sample_panel, str(sample_key))
                        new_sample_panel.menu_menuitem = self.menu.AppendSubMenu(new_sample_panel.menu, str(sample_key))
                    else:
                        new_sample_panel.Hide()
        if 'samples_toggle_flag' in saved_data:
            self.toggle_samples_menuitem.Check(saved_data['samples_toggle_flag'])
            self.OnToggleSamples(None)
        
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FamiliarizationNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        #trigger save for submodules
        saved_data['filters_submodule'] = self.filters_submodule.Save()
        saved_data['samples_submodule'] = self.samples
        saved_data['notes'] = self.notes_panel.Save()
        #Save configurations
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
        saved_data['filters_toggle_flag'] = self.toggle_filters_menuitem.IsChecked()
        saved_data['samples_toggle_flag'] = self.toggle_samples_menuitem.IsChecked()
        logger.info("Finished")
        return saved_data
