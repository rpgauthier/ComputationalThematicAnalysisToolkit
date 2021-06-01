'''Main Program for MachineThematicAnalysisToolkit'''
import logging
from logging.handlers import RotatingFileHandler
import os.path
import shutil
import tempfile
from threading import *
from multiprocessing import get_context
import psutil
from datetime import datetime

import wx
import wx.lib.agw.labelbook as LB
import External.wxPython.labelbook_fix as LB_fix

import RootApp
import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
from Common.GUIText import Main as GUIText
import Common.Notes as cn
import Collection.ModuleCollection as cm
import Familiarization.ModuleFamiliarization as fm
import Sampling.ModuleSampling as sm
import Coding.ModuleCoding as cdm
import MainThreads

import wx.lib.mixins.inspection as wit

class MainFrame(wx.Frame):
    '''the Main GUI'''
    def __init__(self, parent, ID, title, pool,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        logger = logging.getLogger(__name__+".MainFrame.__init__")
        logger.info("Starting")
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)

        self.SetMinSize(wx.Size(400, 400))
        self.Maximize(True)

        #multiprocessing controls
        self.pool = pool
        self.pool_num = self.pool._processes
        self.multiprocessing_inprogress_flag = False

        self.datasets = {}
        self.samples = {}
        self.codes = {}
        self.save_path = ''
        #TODO change to allow resuming previous workspace instead of purging
        if not os.path.exists(Constants.CURRENT_WORKSPACE):
            os.mkdir(Constants.CURRENT_WORKSPACE)
        self.current_workspace = tempfile.TemporaryDirectory(dir=Constants.CURRENT_WORKSPACE)
        
        self.last_load_dt = datetime.now()
        self.load_thread = None
        self.progress_dialog = None
        self.progress_dialog_references = 0
        self.closing = False

        #Program's Modes
        self.multipledatasets_mode = False

        #frame and notebook for notes to make accessible when moving between modules
        self.notes_frame = wx.Frame(self,
                                    title=GUIText.NOTES_LABEL,
                                    style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        self.notes_notebook = cn.NotesNotebook(self.notes_frame)
        #Project's General Notes panel
        self.notes_panel = cn.NotesPanel(self.notes_notebook, None)
        self.notes_notebook.AddPage(self.notes_panel, GUIText.GENERAL_LABEL)

        #notebook for managing layout and tabs of modules
        self.main_notebook = LB_fix.LabelBook(self, agwStyle=LB.INB_LEFT|LB.INB_SHOW_ONLY_TEXT|LB.INB_GRADIENT_BACKGROUND|LB.INB_FIT_LABELTEXT, size=self.GetSize())
        self.main_notebook.SetColour(LB.INB_TAB_AREA_BACKGROUND_COLOUR, self.GetBackgroundColour())

        #Modules
        self.collection_module = cm.CollectionPanel(self.main_notebook, size=self.GetSize())
        self.main_notebook.InsertPage(0, self.collection_module, GUIText.COLLECTION_LABEL)
        self.familiarization_module = fm.FamiliarizationNotebook(self.main_notebook, size=self.GetSize())
        self.main_notebook.InsertPage(1, self.familiarization_module, GUIText.FAMILIARIZATION_LABEL)
        self.sampling_module = sm.SamplingNotebook(self.main_notebook, size=self.GetSize())
        self.main_notebook.InsertPage(2, self.sampling_module, GUIText.SAMPLING_LABEL)
        self.coding_module = cdm.CodingNotebook(self.main_notebook, size=self.GetSize())
        self.main_notebook.InsertPage(3, self.coding_module, GUIText.CODING_LABEL)
        
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
        options_file_menuitem = file_menu.Append(wx.ID_ANY,
                                                 GUIText.OPTIONS_LABEL)
        self.Bind(wx.EVT_MENU, self.OnOptions, options_file_menuitem)
        file_menu.AppendSeparator()
        new_file_menuitem = file_menu.Append(wx.ID_ANY,
                                             GUIText.NEW,
                                             GUIText.NEW_TOOLTIP)
        self.Bind(wx.EVT_MENU, self.OnNew, new_file_menuitem)
        file_menu.AppendSeparator()
        load_file_menuitem = file_menu.Append(wx.ID_OPEN,
                                              GUIText.LOAD,
                                              GUIText.LOAD_TOOLTIP)
        self.Bind(wx.EVT_MENU, self.OnLoadStart, load_file_menuitem)
        oldload_file_menuitem = file_menu.Append(wx.ID_ANY,
                                                 "Old Load",
                                                 "use to convert existing save folders to new single file format")
        self.Bind(wx.EVT_MENU, self.OnOldLoadStart, oldload_file_menuitem)
        CustomEvents.LOAD_EVT_RESULT(self, self.OnLoadEnd)
        save_file_menuitem = file_menu.Append(wx.ID_SAVE,
                                              GUIText.SAVE,
                                              GUIText.SAVE_TOOLTIP)
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
                                                                     GUIText.SHOW_HIDE+GUIText.FAMILIARIZATION_MENU_LABEL,
                                                                     kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnToggleFamiliarization, self.toggle_familiarization_menuitem)
        self.toggle_sampling_menuitem = self.view_menu.Append(wx.ID_ANY,
                                                              GUIText.SHOW_HIDE+GUIText.SAMPLING_MENU_LABEL,
                                                              kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnToggleSampling, self.toggle_sampling_menuitem)
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
        self.view_menu.AppendSubMenu(self.familiarization_module.view_menu, GUIText.FAMILIARIZATION_MENU_LABEL)
        #TODO need to move actions new submenu syste for Sampling submodules
        self.view_menu.AppendSubMenu(self.sampling_module.view_menu, GUIText.SAMPLING_MENU_LABEL)
        self.view_menu.AppendSubMenu(self.coding_module.view_menu, GUIText.CODING_LABEL)
        
        self.menu_bar.Append(self.view_menu, GUIText.VIEW_MENU)

        self.SetMenuBar(self.menu_bar)

        CustomEvents.EVT_PROGRESS(self, self.OnProgress)

        #setup default visable state
        self.toggle_collection_menuitem.Check(True)
        self.toggle_familiarization_menuitem.Check(True)
        self.toggle_sampling_menuitem.Check(True)
        self.toggle_coding_menuitem.Check(True)

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

    def OnToggleSampling(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnToggleSampling")
        logger.info("Starting")
        if self.toggle_sampling_menuitem.IsChecked():
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.sampling_module:
                    index = idx
            if index is None:
                self.main_notebook.InsertPage(2, self.sampling_module,
                                              GUIText.SAMPLING_LABEL)
            #index = self.menu_bar.FindMenu(GUIText.FAMILIARIZATION_LABEL)
            #if index is wx.NOT_FOUND:
            #    self.menu_bar.Append(self.familiarization_module.menu, GUIText.FAMILIARIZATION_LABEL)
        else:
            index = None
            for idx in range(self.main_notebook.GetPageCount()):
                if self.main_notebook.GetPage(idx) is self.sampling_module:
                    index = idx
            if index is not None:
                self.main_notebook.RemovePage(index)
                self.sampling_module.Hide()
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
        logger = logging.getLogger(__name__+".MainFrame.OnOptions")
        logger.info("Starting")
        OptionsDialog(self).Show()
        logger.info("Finished")

    def OnNew(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnNew")
        logger.info("Starting")
        if self.multiprocessing_inprogress_flag:
            wx.MessageBox(GUIText.MULTIPROCESSING_WARNING_MSG,
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
        elif wx.MessageBox(GUIText.NEW_WARNING, GUIText.CONFIRM_REQUEST,
                         wx.ICON_QUESTION|wx.YES_NO, self) == wx.YES:
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
            #Do not need to destroy as codes do not have nested reference loops
            self.codes.clear()
            self.save_path = ''
            self.current_workspace.cleanup()
            self.current_workspace = tempfile.TemporaryDirectory(dir=Constants.CURRENT_WORKSPACE)
        
            self.last_load_dt = datetime.now()
            
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
        logger.info("Finished")
    
    def OnOldLoadStart(self, event):
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
        dir_name = os.path.abspath(os.path.join(base_path, '..', 'Saved_Workspaces'))
        with wx.DirDialog(self,
                          message=GUIText.LOAD_REQUEST,
                          defaultPath=dir_name,
                          style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST) as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                self.save_path = dir_dialog.GetPath()
                self.CreateProgressDialog(title=GUIText.LOAD_BUSY_LABEL,
                                          warning=GUIText.SIZE_WARNING_MSG,
                                          freeze=True)
                self.PulseProgressDialog(GUIText.LOAD_BUSY_MSG)
                self.load_thread = MainThreads.OldLoadThread(self, self.save_path)
        logger.info("Finished")

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
        dir_name = os.path.abspath(os.path.join(base_path, '..', 'Saved_Workspaces'))
        with wx.FileDialog(self,
                          message=GUIText.LOAD_REQUEST,
                          defaultDir=dir_name,
                          style=wx.DD_DEFAULT_STYLE|wx.FD_FILE_MUST_EXIST|wx.FD_OPEN,
                          wildcard="*.mta") as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                self.save_path = dir_dialog.GetPath()
                self.current_workspace.cleanup()
                self.current_workspace = tempfile.TemporaryDirectory(dir=Constants.CURRENT_WORKSPACE)

                self.CreateProgressDialog(title=GUIText.LOAD_BUSY_LABEL,
                                          warning=GUIText.SIZE_WARNING_MSG,
                                          freeze=True)
                self.PulseProgressDialog(GUIText.LOAD_BUSY_MSG)
                self.load_thread = MainThreads.LoadThread(self, self.save_path, self.current_workspace.name)
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

        codes = event.data['codes']
        #Do not need to destroy as codes do not have nested reference loops
        self.codes.clear()
        self.codes.update(codes)

        self.DatasetsUpdated()

        if 'multipledatasets_mode' in saved_data:
            self.multipledatasets_mode = saved_data['multipledatasets_mode']
            self.ModeChange()
        self.toggle_collection_menuitem.Check(check=saved_data['collection_check'])
        self.OnToggleCollection(None)
        if 'collection_module' in saved_data:
            self.collection_module.Load(saved_data['collection_module'])
        self.toggle_familiarization_menuitem.Check(check=saved_data['familiarization_check'])
        self.OnToggleFamiliarization(None)
        if 'familiarization_module' in saved_data:
            self.familiarization_module.Load(saved_data['familiarization_module'])
        if 'sampling_module' in saved_data:
            self.sampling_module.SamplesUpdated()
            self.sampling_module.Load(saved_data['sampling_module'])
        else:
            self.sampling_module.SamplesUpdated()
        if 'coding_module' in saved_data:
            self.coding_module.Load(saved_data['coding_module'])
            self.toggle_coding_menuitem.Check(check=saved_data['coding_check'])
        self.OnToggleCoding(None)
        self.toggle_notes_menuitem.Check(check=saved_data['notes_check'])
        self.OnToggleNotes(None)
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])

        self.last_load_dt = datetime.now()
        self.load_thread.join()
        self.load_thread = None
        self.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnSaveAs(self, event):
        '''Menu Function for creating new save of data'''
        logger = logging.getLogger(__name__+".MainFrame.OnSaveAs")
        logger.info("Starting")
        base_path = os.path.dirname(__file__)
        dir_name = os.path.abspath(os.path.join(base_path, '..', 'Saved_Workspaces'))

        with wx.FileDialog(self,
                          message=GUIText.SAVE_AS_REQUEST,
                          defaultDir=dir_name,
                          style=wx.DD_DEFAULT_STYLE|wx.FD_SAVE,
                          wildcard="*.mta") as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                self.save_path = file_dialog.GetPath()
                try:
                    self.last_load_dt = datetime(1990, 1, 1)
                    
                    self.OnSaveStart(event)
                except IOError:
                    wx.LogError(GUIText.SAVE_AS_FAILURE + self.save_path)
                    logger.error("Failed to save in chosen directory[%s]", self.save_path)
            else:
                if self.closing:
                    self.closing = False
                    self.CloseProgressDialog(thaw=True, message="Canceled")

        logger.info("Finished")

    def OnSaveStart(self, event):
        '''Menu Function for updating save of data'''
        logger = logging.getLogger(__name__+".MainFrame.OnSave")
        logger.info("Starting")
        if self.save_path == '':
            self.OnSaveAs(event)
        else:
            self.CreateProgressDialog(title=GUIText.SAVE_BUSY_LABEL,
                                      warning=GUIText.SIZE_WARNING_MSG,
                                      freeze=True)
            self.PulseProgressDialog(GUIText.SAVE_BUSY_MSG)
            
            self.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_NOTES)
            notes_text = self.notes_notebook.Save()

            self.PulseProgressDialog(GUIText.SAVE_BUSY_MSG_CONFIG)
            config_data = {}
            config_data['collection_check'] = self.toggle_collection_menuitem.IsChecked()
            config_data['familiarization_check'] = self.toggle_familiarization_menuitem.IsChecked()
            config_data['coding_check'] = self.toggle_coding_menuitem.IsChecked()
            config_data['notes_check'] = self.toggle_notes_menuitem.IsChecked()
            config_data['notes'] = self.notes_panel.Save()
            config_data['datasets'] = list(self.datasets.keys())
            config_data['multipledatasets_mode'] = self.multipledatasets_mode
            config_data['samples'] = list(self.samples.keys())
            config_data['codes'] = True
            config_data['collection_module'] = self.collection_module.Save()
            config_data['familiarization_module'] = self.familiarization_module.Save()
            config_data['sampling_module'] = self.sampling_module.Save()
            config_data['coding_module'] = self.coding_module.Save()

            self.save_thread = MainThreads.SaveThread(self, self.save_path, self.current_workspace.name, config_data, self.datasets, self.samples, self.codes, notes_text, self.last_load_dt)

    def OnSaveEnd(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnSaveEnd")
        logger.info("Starting")
        #once load thread has finished loading data files into memory run the GUI with the loaded data
        self.last_load_dt = datetime.now()
        self.save_thread.join()
        self.save_thread = None
        self.CloseProgressDialog(thaw=True)

        if self.closing:
            self.OnCloseEnd(event)
    
    def OnProgress(self, event):
        self.PulseProgressDialog(event.data)

    def OnCloseStart(self, event):
        '''Menu Function for Closing Application'''
        logger = logging.getLogger(__name__+".MainFrame.OnCloseStart")
        logger.info("Starting")

        self.CreateProgressDialog(title=GUIText.SHUTDOWN_BUSY_LABEL,
                                  freeze=True)
        cancel_flag = False
        if self.multiprocessing_inprogress_flag:
            if wx.MessageBox(GUIText.MULTIPROCESSING_CLOSING_MSG,
                             GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) != wx.YES:
                cancel_flag = True

        if not cancel_flag:
            if wx.MessageBox(GUIText.CLOSE_WARNING,
                            GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
                self.closing = True
                self.PulseProgressDialog(text=GUIText.SAVE_BUSY_LABEL)
                self.OnSaveStart(None)
            else:
                self.OnCloseEnd(event)
        else:
            self.CloseProgressDialog(GUIText.CANCELED, thaw=True)

        logger.info("\nFinished")

    def OnCloseEnd(self, event):
        logger = logging.getLogger(__name__+".MainFrame.OnCloseEnd")
        logger.info("Starting")

        self.PulseProgressDialog(GUIText.SHUTDOWN_BUSY_POOL)
        logger.info("Starting to shut down of process pool")
        self.pool.close()
        self.pool.join()
        logger.info("Finished shutting down process pool")

        #self.PulseProgressDialog(GUIText.SHUTDOWN_BUSY_FAMILIARIZATION)
        #self.familiarization_module.Shutdown()

        #self.PulseProgressDialog(GUIText.SHUTDOWN_BUSY_COLLECTION)
        #self.collection_module.Shutdown()

        self.CloseProgressDialog(thaw=True, close=True)
        logger.info("\nFinished")

        windows = wx.GetTopLevelWindows()
        for window in windows:
            window.Destroy()
        
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
        self.progress_dialog_references += 1
    
    def PulseProgressDialog(self, text=""):
        if self.progress_dialog is not None:
            self.progress_dialog.Pulse(text)
    
    def CloseProgressDialog(self, message="Finished", thaw=False, close=False):
        if self.progress_dialog is not None:
            self.progress_dialog_references -= 1
            if self.progress_dialog_references == 0:
                self.progress_dialog.EndPulse("\n"+message)
                if close:
                    self.progress_dialog.Close()
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
        self.sampling_module.SamplesUpdated()
        #self.coding_module.SamplesUpdated()
        logger.info("Finished")

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".MainFrame.DocumentsUpdated")
        logger.info("Starting")
        self.sampling_module.DocumentsUpdated()
        self.coding_module.DocumentsUpdated()
        logger.info("Finished")

    def ModeChange(self):
        self.collection_module.ModeChange()
        self.sampling_module.ModeChange()

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

class OptionsDialog(wx.Dialog):
    def __init__(self, parent, size=wx.DefaultSize):
        wx.Dialog.__init__(self, parent, title=GUIText.OPTIONS_LABEL, size=size, style=wx.DEFAULT_DIALOG_STYLE)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        main_frame = wx.GetApp().GetTopWindow()

        self.multipledatasets_ctrl = wx.CheckBox(self, label="Allow Multiple Datasets Mode (not yet fully tested)")
        self.multipledatasets_ctrl.SetValue(main_frame.multipledatasets_mode)
        self.multipledatasets_ctrl.Bind(wx.EVT_CHECKBOX, self.ChangeMultipleDatasetMode)
        sizer.Add(self.multipledatasets_ctrl, 0, wx.ALL, 5)
    
    def ChangeMultipleDatasetMode(self, event):
        main_frame = wx.GetApp().GetTopWindow()
        new_mode = self.multipledatasets_ctrl.GetValue()
        if main_frame.multipledatasets_mode != new_mode:
            main_frame.multipledatasets_mode = new_mode
            main_frame.ModeChange()

def Main():
    '''setup the main tasks for the application'''
    log_path = "../Logs/MachineThematicAnalysis.log"
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

    