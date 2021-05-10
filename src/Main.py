'''Main Program for MachineThematicAnalysisToolkit'''
import logging
from logging.handlers import RotatingFileHandler
import bz2
import os.path
from threading import *
from multiprocessing import cpu_count, get_context
import psutil
from shutil import copyfile
from datetime import datetime

import faulthandler


import wx
import wx.lib.agw.labelbook as LB
import External.wxPython.labelbook_fix as LB_fix
import _pickle as cPickle

import RootApp
import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
from Common.GUIText import Main as GUIText
import Common.Objects.Datasets as Datasets
import Common.Notes as cn
import Collection.ModuleCollection as cm
import Familiarization.ModuleFamiliarization as fm
import Coding.ModuleCoding as cdm
import MainThreads

class MainFrame(wx.Frame):
    '''the Main GUI'''
    def __init__(self, parent, ID, title, pool,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        logger = logging.getLogger(__name__+".MainFrame.__init__")
        logger.info("Starting")
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)

        self.SetMinSize(wx.Size(400, 400))
        self.Maximize(True)

        self.pool = pool
        self.pool_num = self.pool._processes
        self.threaded_inprogress_flag = False
        self.datasets = {}
        self.samples = {}
        self.codes = {}
        self.workspace_path = ''
        self.last_load_dt = datetime.now()
        self.load_thread = None
        self.progress_dialog = None
        self.progress_dialog_references = 0

        self.closing = False

        #frame and notebook for notes to make accessible when moving between modules
        self.notes_frame = wx.Frame(self,
                                    title=GUIText.NOTES_LABEL,
                                    style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        self.notes_notebook = cn.NotesNotebook(self.notes_frame)
        #Project's General Notes panel
        self.notes_panel = cn.NotesPanel(self.notes_notebook, None)
        self.notes_notebook.AddPage(self.notes_panel, GUIText.GENERAL_LABEL)

        #notebook for managing layout and tabs of modules
        self.main_notebook = LB_fix.LabelBook(self, agwStyle=LB.INB_LEFT|LB.INB_SHOW_ONLY_TEXT|LB.INB_GRADIENT_BACKGROUND, size=self.GetSize())
        #label_font = wx.Font(Constants.PHASE_LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, underline=Constants.LABEL_UNDERLINE)
        #self.main_notebook.SetSelectedFont(label_font)
        self.main_notebook.SetColour(LB.INB_TAB_AREA_BACKGROUND_COLOUR, self.GetBackgroundColour())

        #Modules
        self.collection_module = cm.CollectionPanel(self.main_notebook, size=self.GetSize())
        self.main_notebook.InsertPage(0, self.collection_module, GUIText.COLLECTION_LABEL)
        #self.collection_module.Hide()
        self.familiarization_module = fm.FamiliarizationNotebook(self.main_notebook, self.samples, size=self.GetSize())
        self.main_notebook.InsertPage(1, self.familiarization_module, GUIText.FAMILIARIZATION_LABEL)
        #self.familiarization_module.Hide()
        self.coding_module = cdm.CodingPanel(self.main_notebook, size=self.GetSize())
        self.main_notebook.InsertPage(2, self.coding_module, GUIText.CODING_LABEL)
        #self.coding_module.Hide()

        #Sizer for Frame
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel_sizer.Add(self.main_notebook, 1, wx.EXPAND)
        self.SetSizer(self.panel_sizer)

        #Actions For Main Frame
        self.Bind(wx.EVT_CLOSE, self.OnCloseStart)

        #Actions For Notes Frame
        self.notes_frame.Bind(wx.EVT_CLOSE, self.OnNotesClose)

        #Initializing Static Menus
        self.menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        #options
        #options_file_menuitem = file_menu.Append(wx.ID_ANY,
        #                                         "GUI Inspecter")
        #self.Bind(wx.EVT_MENU, self.OnOptions, options_file_menuitem)
        #file_menu.AppendSeparator()
        new_file_menuitem = file_menu.Append(wx.ID_ANY,
                                             GUIText.NEW,
                                             GUIText.NEW_TOOLTIP)
        self.Bind(wx.EVT_MENU, self.OnNew, new_file_menuitem)
        file_menu.AppendSeparator()
        load_file_menuitem = file_menu.Append(wx.ID_OPEN,
                                              GUIText.LOAD,
                                              GUIText.LOAD_TOOLTIP)
        self.Bind(wx.EVT_MENU, self.OnLoadStart, load_file_menuitem)
        CustomEvents.LOAD_EVT_RESULT(self, self.OnLoadEnd)
        save_file_menuitem = file_menu.Append(wx.ID_SAVE,
                                              GUIText.SAVE,
                                              GUIText.SAVE_TOOLTIP)
        #self.Bind(wx.EVT_MENU, self.OnSave, save_file_menuitem)
        self.Bind(wx.EVT_MENU, self.OnSaveStart, save_file_menuitem)
        CustomEvents.SAVE_EVT_RESULT(self, self.OnSaveEnd)
        saveas_file_menuitem = file_menu.Append(wx.ID_SAVEAS,
                                                GUIText.SAVE_AS,
                                                GUIText.SAVE_AS_TOOLTIP)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, saveas_file_menuitem)
        file_menu.AppendSeparator()
        exit_file_menuitem = file_menu.Append(wx.ID_EXIT,
                                         GUIText.EXIT,
                                         GUIText.EXIT_TOOLTIP)
        self.Bind(wx.EVT_MENU, self.OnCloseStart, exit_file_menuitem)
        self.menu_bar.Append(file_menu, GUIText.FILE_MENU)

        self.view_menu = wx.Menu()
        self.toggle_collection_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                           GUIText.SHOW_HIDE+GUIText.COLLECTION_LABEL,
                                                           kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnToggleCollection, self.toggle_collection_menuitem)
        self.toggle_familiarization_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                                GUIText.SHOW_HIDE+GUIText.FAMILIARIZATION_LABEL,
                                                                kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnToggleFamiliarization, self.toggle_familiarization_menuitem)
        self.toggle_coding_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                                GUIText.SHOW_HIDE+GUIText.CODING_LABEL,
                                                                kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnToggleCoding, self.toggle_coding_menuitem)
        
        self.view_menu.AppendSeparator()
        self.toggle_notes_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                      GUIText.SHOW_HIDE + GUIText.NOTES_LABEL,
                                                      kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnToggleNotes, self.toggle_notes_menuitem)

        self.view_menu.AppendSeparator()
        self.view_menu.AppendSubMenu(self.collection_module.view_menu, GUIText.COLLECTION_LABEL)
        #TODO need to move actions new submenu syste for Familiarization submodules
        self.view_menu.AppendSubMenu(self.familiarization_module.view_menu, GUIText.FAMILIARIZATION_LABEL)
        self.view_menu.AppendSubMenu(self.coding_module.view_menu, GUIText.CODING_LABEL)
        
        self.menu_bar.Append(self.view_menu, GUIText.VIEW_MENU)

        self.SetMenuBar(self.menu_bar)

        CustomEvents.EVT_PROGRESS(self, self.OnProgress)

        #setup default visable state
        self.toggle_collection_menuitem.Check(True)
        #self.OnToggleCollection(None)
        self.toggle_familiarization_menuitem.Check(True)
        #self.OnToggleFamiliarization(None)
        self.toggle_coding_menuitem.Check(True)
        #self.OnToggleCoding(None)

        self.Layout()
        self.Fit()
        self.Show(True)

        logger.info("Finished")

    #Functions called by actions on the GUI (menus or buttons)
    def OnToggleCollection(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnToggleCollection")
        logger.info("Starting")
        if self.toggle_collection_menuitem.IsChecked():
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.collection_module:
                    index = idx
            if index is None:
                self.main_notebook.InsertPage(0, self.collection_module,
                                              GUIText.COLLECTION_LABEL)
            #index = self.view_menu.FindItem(GUIText.COLLECTION_LABEL)
            #if index is wx.NOT_FOUND:
            #    self.view_menu.AppendSubMenu(self.collection_module.menu, GUIText.COLLECTION_LABEL)
        else:
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.collection_module:
                    index = idx
            if index is not None:
                self.main_notebook.RemovePage(index)
                self.collection_module.Hide()
            #index = self.view_menu.FindItem(GUIText.COLLECTION_LABEL)
            #if index is not wx.NOT_FOUND:
            #    self.view_menu.Remove(index)
        logger.info("Finished")

    def OnToggleFamiliarization(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnToggleFamiliarization")
        logger.info("Starting")
        if self.toggle_familiarization_menuitem.IsChecked():
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.familiarization_module:
                    index = idx
            if index is None:
                self.main_notebook.InsertPage(1, self.familiarization_module,
                                              GUIText.FAMILIARIZATION_LABEL)
            #index = self.menu_bar.FindMenu(GUIText.FAMILIARIZATION_LABEL)
            #if index is wx.NOT_FOUND:
            #    self.menu_bar.Append(self.familiarization_module.menu, GUIText.FAMILIARIZATION_LABEL)
        else:
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.familiarization_module:
                    index = idx
            if index is not None:
                self.main_notebook.RemovePage(index)
                self.familiarization_module.Hide()
            #index = self.menu_bar.FindMenu(GUIText.FAMILIARIZATION_LABEL)
            #if index is not wx.NOT_FOUND:
            #    self.menu_bar.Remove(index)
        logger.info("Finished")
    
    def OnToggleCoding(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnToggleCoding")
        logger.info("Starting")
        if self.toggle_coding_menuitem.IsChecked():
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.coding_module:
                    index = idx
            if index is None:
                self.main_notebook.InsertPage(2, self.coding_module,
                                              GUIText.CODING_LABEL)
            #index = self.menu_bar.FindMenu(GUIText.CODING_LABEL)
            #if index is wx.NOT_FOUND:
            #    self.menu_bar.Append(self.coding_module.menu, GUIText.CODING_LABEL)
        else:
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.coding_module:
                    index = idx
            if index is not None:
                self.main_notebook.RemovePage(index)
                self.coding_module.Hide()
            #index = self.menu_bar.FindMenu(GUIText.CODING_LABEL)
            #if index is not wx.NOT_FOUND:
            #    self.menu_bar.Remove(index)
        logger.info("Finished")

    def OnToggleNotes(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnToggleNotes")
        logger.info("Starting")
        if self.toggle_notes_menuitem.IsChecked():
            self.notes_frame.Show()
        else:
            self.notes_frame.Hide()
        logger.info("Finished")

    def OnNotesClose(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnNotesClose")
        logger.info("Starting")
        self.notes_frame.Hide()
        self.toggle_notes_menuitem.Check(False)
        logger.info("Finished")
    
    def OnOptions(self, event):
        wx.GetApp().ShowInspectionTool()

    def OnNew(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnLoadStart")
        logger.info("Starting")
        if wx.MessageBox(GUIText.NEW_WARNING,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished")
            return
        self.CreateProgressDialog(title=GUIText.NEW_BUSY_LABEL,
                                  warning=GUIText.SIZE_WARNING_MSG,
                                  freeze=True)
        self.PulseProgressDialog(GUIText.NEW_BUSY_MSG)

        #reset objects
        for key in self.datasets:
            self.datasets[key].DestroyObject()
        self.datasets.clear()
        for key in self.samples:
            self.samples[key].DestroyObject()
        self.samples.clear()
        self.DatasetsUpdated()
        self.SamplesUpdated()
        self.DocumentsUpdated()

        #reset view
        self.toggle_collection_menuitem.Check(True)
        self.OnToggleCollection(None)
        self.toggle_familiarization_menuitem.Check(True)
        self.OnToggleFamiliarization(None)
        self.toggle_coding_menuitem.Check(True)
        self.OnToggleCoding(None)

        self.CloseProgressDialog(thaw=True)

    def OnLoadStart(self, event):
        #start up load thread that performs all backend load operations that take a long time
        '''Menu Function for loading data'''
        logger = logging.getLogger(__name__+".MainFrame.OnLoadStart")
        logger.info("Starting")
        if wx.MessageBox(GUIText.LOAD_WARNING,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished")
            return
        #ask the user what workspace to open
        base_path = os.path.dirname(__file__)
        dir_name = os.path.abspath(os.path.join(base_path, '..', 'Workspaces'))
        with wx.DirDialog(self,
                          message=GUIText.LOAD_REQUEST,
                          defaultPath=dir_name,
                          style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST) as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                self.workspace_path = dir_dialog.GetPath()
                self.CreateProgressDialog(title=GUIText.LOAD_BUSY_LABEL,
                                          warning=GUIText.SIZE_WARNING_MSG,
                                          freeze=True)
                self.PulseProgressDialog(GUIText.LOAD_BUSY_MSG)
                self.load_thread = MainThreads.LoadThread(self, self.workspace_path)
        logger.info("Finished")

    def OnLoadEnd(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnLoadEnd")
        logger.info("Starting")
        #once load thread has finished loading data files into memory run the GUI with the loaded data
        
        saved_data = event.data['config']
        
        datasets = event.data['datasets']                
        for key in self.datasets:
            self.datasets[key].DestroyObject()
        self.datasets.clear()
        self.datasets.update(datasets)

        samples = event.data['samples']
        for key in self.samples:
            self.samples[key].DestroyObject()
        self.samples.clear()
        self.samples.update(samples)

        self.DatasetsUpdated()

        self.toggle_collection_menuitem.Check(check=saved_data['collection_check'])
        self.OnToggleCollection(None)
        if 'collection_module' in saved_data:
            self.collection_module.Load(saved_data['collection_module'])
        self.toggle_familiarization_menuitem.Check(check=saved_data['familiarization_check'])
        self.OnToggleFamiliarization(None)
        if 'familiarization_module' in saved_data:
            self.familiarization_module.Load(saved_data['familiarization_module'])
        if 'coding_module' in saved_data:
            self.coding_module.Load(saved_data['coding_module'])
            self.toggle_coding_menuitem.Check(check=saved_data['coding_check'])
        self.OnToggleCoding(None)
        self.toggle_notes_menuitem.Check(check=saved_data['notes_check'])
        self.OnToggleNotes(None)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])

        self.last_load_dt = datetime.now()
        self.load_thread = None
        self.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnSaveStart(self, event):
        '''Menu Function for updating save of data'''
        logger = logging.getLogger(__name__+".MainFrame.OnSave")
        logger.info("Starting")
        if self.workspace_path == '':
            self.OnSaveAs(event)
        else:
            self.CreateProgressDialog(title=GUIText.SAVE_BUSY_LABEL,
                                      warning=GUIText.SIZE_WARNING_MSG,
                                      freeze=True)
            self.PulseProgressDialog(GUIText.SAVE_BUSY_MSG)
            
            self.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_NOTES)
            self.notes_notebook.Save()

            self.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
            config_data = {}
            config_data['collection_check'] = self.toggle_collection_menuitem.IsChecked()
            config_data['familiarization_check'] = self.toggle_familiarization_menuitem.IsChecked()
            config_data['coding_check'] = self.toggle_coding_menuitem.IsChecked()
            config_data['notes_check'] = self.toggle_notes_menuitem.IsChecked()
            config_data['notes'] = self.notes_panel.Save()
            config_data['datasets'] = list(self.datasets.keys())
            config_data['samples'] = list(self.samples.keys())
            config_data['collection_module'] = self.collection_module.Save()
            config_data['familiarization_module'] = self.familiarization_module.Save()
            config_data['coding_module'] = self.coding_module.Save()

            self.save_thread = MainThreads.SaveThread(self, self.workspace_path, config_data, self.datasets, self.samples, self.last_load_dt)

    def OnSaveEnd(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnSaveEnd")
        logger.info("Starting")
        #once load thread has finished loading data files into memory run the GUI with the loaded data
        self.last_load_dt = datetime.now()
        self.save_thread = None
        self.CloseProgressDialog(thaw=True)

        if self.closing:
            self.OnCloseEnd(event)
            

    def OnSaveAs(self, event):
        '''Menu Function for creating new save of data'''
        logger = logging.getLogger(__name__+".MainFrame.OnSaveAs")
        logger.info("Starting")
        base_path = os.path.dirname(__file__)
        dir_name = os.path.abspath(os.path.join(base_path, '..', 'Workspaces'))
        with wx.DirDialog(self, message=GUIText.SAVE_AS_REQUEST,
                          defaultPath=dir_name) as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                self.workspace_path = dir_dialog.GetPath()
                try:
                    self.last_load_dt = datetime(1990, 1, 1)
                    self.OnSaveStart(event)
                except IOError:
                    wx.LogError(GUIText.SAVE_AS_FAILURE + self.workspace_path)
                    logger.error("Failed to save in chosen directory[%s]", self.workspace_path)
            else:
                if self.closing:
                    self.closing = False
                    self.CloseProgressDialog(thaw=True, message="Canceled")


        logger.info("Finished")
    
    def OnProgress(self, event):
        self.PulseProgressDialog(event.data)

    def OnCloseStart(self, event):
        '''Menu Function for Closing Application'''
        logger = logging.getLogger(__name__+".MainFrame.OnCloseStart")
        logger.info("Starting")

        self.closing = True

        self.CreateProgressDialog(title=GUIText.SHUTDOWN_BUSY_LABEL,
                                  freeze=True)
        if wx.MessageBox(GUIText.CLOSE_WARNING,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
            self.PulseProgressDialog(text="Saving Workspace")
            self.OnSaveStart(None)
        else:
            self.OnCloseEnd(event)

        logger.info("\nFinished")

    def OnCloseEnd(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnCloseEnd")
        logger.info("Starting")

        self.PulseProgressDialog(GUIText.SHUTDOWN_BUSY_POOL)
        logger.info("Starting to shut down of process pool")
        self.pool.close()
        self.pool.join()
        logger.info("Finished shutting down process pool")

        #hunting for cause of heap corruption on exit
        #import objgraph
        #import random
        #tmp = objgraph.by_type('DatasetsViewCtrl')
        #objgraph.show_backrefs(tmp, max_depth=10, filename="backref1.png")
        #objgraph.show_refs(tmp, max_depth=10, filename="ref1.png")

        #tmp = objgraph.by_type('SamplesViewCtrl')
        #objgraph.show_backrefs(tmp, max_depth=10, filename="backref2.png")
        #objgraph.show_refs(tmp, max_depth=10, filename="ref2.png")

        #self.PulseProgressDialog(GUIText.SHUTDOWN_BUSY_FAMILIARIZATION)
        #self.familiarization_module.Shutdown()

        #self.PulseProgressDialog(GUIText.SHUTDOWN_BUSY_COLLECTION)
        #self.collection_module.Shutdown()

        logger.info("\nFinished")
        #temporary fix to kill python vm and prevent core dumps
        os._exit(0)
        #self.Destroy()

    #Functions called by other modules

    def CreateProgressDialog(self, title, warning="", freeze=False):
        if freeze:
            self.Freeze()
            self.Disable()
        if self.progress_dialog_references == 0:
            self.progress_dialog = CustomProgressDialog(parent=self,
                                                        title=title,
                                                        warning=warning)
            self.progress_dialog.Show()
            #self.progress_dialog = wx.ProgressDialog(title=title,
            #                                         message=GUIText.BUSY_MSG_DEFAULT,
            #                                         parent=self,
            #                                         style=wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE)
        self.progress_dialog_references += 1
    
    def PulseProgressDialog(self, text=""):
        if self.progress_dialog is not None:
            self.progress_dialog.Pulse(text)
    
    def CloseProgressDialog(self, message="Finished", thaw=False):
        if self.progress_dialog is not None:
            self.progress_dialog_references -= 1
            if self.progress_dialog_references == 0:
                self.progress_dialog.EndPulse("\n"+message)
        if thaw:
            self.Enable()
            self.Thaw()

    def DatasetKeyChange(self, old_key, new_key):
        logger = logging.getLogger(__name__+".MainFrame.DatasetKeyChange")
        logger.info("Starting")
        for sample_key in self.samples:
            if self.samples[sample_key].dataset_key == old_key:
                self.samples[sample_key].dataset_key = new_key
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".MainFrame.DatasetsUpdated")
        logger.info("Starting")
        self.collection_module.DatasetsUpdated()
        self.familiarization_module.DatasetsUpdated()
        self.coding_module.DatasetsUpdated()
        logger.info("Finished")

    def SamplesUpdated(self):
        logger = logging.getLogger(__name__+".MainFrame.SamplesUpdated")
        logger.info("Starting")
        #self.collection_module.SamplesUpdated()
        self.familiarization_module.SamplesUpdated()
        #self.coding_module.SamplesUpdated()
        logger.info("Finished")

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".MainFrame.DocumentsUpdated")
        logger.info("Starting")
        self.collection_module.DocumentsUpdated()
        self.familiarization_module.DocumentsUpdated()
        self.coding_module.DocumentsUpdated()
        logger.info("Finished")

class CustomProgressDialog(wx.Dialog):
    def __init__(self, parent, title, warning=""):
        wx.Dialog.__init__(self, parent, title=title, style=wx.CAPTION|wx.RESIZE_BORDER)
       
        #h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        v_sizer = wx.BoxSizer(wx.VERTICAL)

        if warning != "":
            warning_text = wx.StaticText(self, label=warning)
            v_sizer.Add(warning_text, 0, wx.EXPAND|wx.ALL, 5)

        self.gauge = wx.Gauge(self)
        v_sizer.Add(self.gauge, 0, wx.EXPAND|wx.ALL, 5)

        self.timer = wx.Timer(self)
        self.start_time = datetime.now()
        elapsed_time = self.start_time - self.start_time
        self.Bind(wx.EVT_TIMER, self.OnUpdateTime, self.timer)
        self.timer_label = wx.StaticText(self, label=str(elapsed_time).split('.')[0])
        v_sizer.Add(self.timer_label, 0, wx.EXPAND|wx.ALL, 5)
        self.timer.Start(1000)

        self.text = wx.TextCtrl(self, -1, "Starting\n", size=(320,240), style=wx.TE_MULTILINE | wx.TE_READONLY)
        v_sizer.Add(self.text, 1, wx.EXPAND|wx.ALL, 5)

        btnsizer = wx.BoxSizer()
        self.ok_btn = wx.Button(self, wx.ID_OK)
        self.ok_btn.Disable()
        btnsizer.Add(self.ok_btn, 0, wx.ALL, 5)
        v_sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

        self.SetSizerAndFit (v_sizer)
    
    def OnUpdateTime(self, event):
        current_time = datetime.now()
        elapsed_time = current_time - self.start_time
        self.timer_label.SetLabel(str(elapsed_time).split('.')[0])

    def Pulse(self, text):
        self.text.AppendText("\n"+text)
        self.gauge.Pulse()
    
    def EndPulse(self, text):
        self.timer.Stop()
        self.text.AppendText("\n"+text)
        self.gauge.SetValue(self.gauge.GetRange())
        current_time = datetime.now()
        elapsed_time = current_time - self.start_time
        self.timer_label.SetLabel(str(elapsed_time).split('.')[0])
        self.ok_btn.Enable()

def Main():
    '''setup the main tasks for the application'''
    log_path = "../Logs/MachineThematicAnalysis.log"
    faulthandler.enable()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    #handler = logging.FileHandler("../Logs/MachineThematicAnalysis.log")
    handler = RotatingFileHandler(log_path, maxBytes=200000, backupCount=200)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    cpus = psutil.cpu_count(logical=False)
    if cpus is None or cpus < 2:
        pool_num = 1
    else:
        pool_num = cpus-1
    with get_context("spawn").Pool(processes=pool_num) as pool:
        #start up the GUI
        app = RootApp.RootApp()
        MainFrame(None, -1, GUIText.APP_NAME,
                  style=wx.DEFAULT_FRAME_STYLE, pool=pool)
        #start up the main loop
        app.MainLoop()

if __name__ == '__main__':
    Main()
