import logging
import bz2
import os.path
from shutil import copyfile

import _pickle as cPickle
import wx
import wx.aui
import wx.dataview as dv

import Common.Constants as Constants
from Common.GUIText import Familiarization as GUIText
import Common.Objects.Samples as Samples
import Common.Objects.DataViews.Samples as SamplesDataViews
import Common.Objects.GUIs.Samples as SamplesGUIs

class SamplesNotebook(wx.aui.AuiNotebook):
    def __init__(self, parent, samples, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".SamplesNotebook.__init__")
        logger.info("Starting")
        wx.aui.AuiNotebook.__init__(self, parent, style=Constants.NOTEBOOK_MOVEABLE, size=size)

        #holder for instances of samples and thier panels
        self.samples = samples
        self.sample_panels = {}

        #generator panel instance
        self.sample_list_panel = SamplesGUIs.SampleListPanel(self, self.samples, size=size)
        self.AddPage(self.sample_list_panel, "Sample List")

        self.sample_list_panel.Bind(dv.EVT_DATAVIEW_ITEM_EDITING_DONE, self.OnSampleKeyChange)
        
        self.menu = wx.Menu()
        self.menu_menuitem = None
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
            self.sample_list_panel.OnSampleKeyChange(self, event)
    
    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".SamplesNotebook.DatasetsUpdated")
        logger.info("Starting")
        logger.info("Finished")
    
    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".SamplesNotebook.DatasetsUpdated")
        logger.info("Starting")
        for key in self.sample_panels:
            self.sample_panels[key].DocumentsUpdated()
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".SamplesNotebook.Load")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        #remove all current sample panels
        for key in self.sample_panels:
            index = self.GetPageIndex(self.sample_panels[key])
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
                self.menu.Remove(self.sample_panels[key].menu_menuitem)
        self.sample_panels.clear()

        #create new sample_panels for each sample
        for sample_key in self.samples:
            sample = self.samples[sample_key]
            new_sample_panel = None
            if sample.sample_type == "Random":
                new_sample_panel = SamplesGUIs.RandomSamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
                main_frame.DocumentsUpdated()
            elif sample.sample_type == "LDA":
                #TODO panel is not creating properly when LDA generate needs to be resumed
                new_sample_panel = SamplesGUIs.LDASamplePanel(self, sample, main_frame.datasets[sample.dataset_key], size=self.GetSize())
            #TODO create custom sample panel
            #elif self.samples[key].sample_type == "Custom"
            #    new_sample_panel = SamplesGUIs.CustomSamplePanel(self, self.samples[key], size=self.GetSize())
            if new_sample_panel is not None:
                self.sample_panels[sample_key] = new_sample_panel
                self.AddPage(new_sample_panel, str(sample_key))
                new_sample_panel.menu_menuitem = self.menu.AppendSubMenu(new_sample_panel.menu, str(sample_key))
        self.sample_list_panel.samples_model.Cleared()
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".SamplesNotebook.Save")
        logger.info("Starting")
        logger.info("Finished")
        return {}
