'''Code for the submodule that controls grouping of data'''
from datetime import datetime, timedelta
import logging

import wx
import wx.adv
import wx.dataview as dv
import wx.lib.scrolledpanel

from Common.GUIText import Collection as GUIText
import Common.Objects.Datasets as Datasets
import Common.Objects.DataViews.Datasets as DatasetsDataViews
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Common.CustomEvents as CustomEvents
import Common.Database as Database
import Collection.CollectionDialogs as CollectionDialogs
import Collection.SubModuleFields as SubModuleFields

#TODO rethink create layout to have more description of the sources similar to create samples panel
class DatasetsListPanel(wx.Panel):
    def __init__(self, parent, module, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetsPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        self.parent = parent
        self.module = module
        main_frame = wx.GetApp().GetTopWindow()

        self.dataset_dialogs = {}
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        create_box = wx.StaticBox(self, label=GUIText.CREATE)
        create_box.SetFont(main_frame.DETAILS_LABEL_FONT)
        create_sizer = wx.StaticBoxSizer(create_box, wx.HORIZONTAL)
        
        add_reddit_btn = wx.Button(self, label=GUIText.DATASETS_RETRIEVE_REDDIT)
        add_reddit_btn.SetToolTip(GUIText.DATASETS_RETRIEVE_REDDIT_TOOLTIP)
        add_reddit_btn.Bind(wx.EVT_BUTTON, self.OnAddRedditDataset)
        create_sizer.Add(add_reddit_btn)
        add_csv_btn = wx.Button(self, label=GUIText.DATASETS_IMPORT_CSV)
        add_csv_btn.SetToolTip(GUIText.DATASETS_IMPORT_CSV_TOOLTIP)
        add_csv_btn.Bind(wx.EVT_BUTTON, self.OnAddCSVDataset)
        create_sizer.Add(add_csv_btn)
        if 'twitter_enabled' in main_frame.options_dict:
            add_twitter_btn = wx.Button(self, label=GUIText.DATASETS_RETRIEVE_TWITTER)
            add_twitter_btn.SetToolTip(GUIText.DATASETS_RETRIEVE_TWITTER_TOOLTIP)
            add_twitter_btn.Bind(wx.EVT_BUTTON, self.OnAddTwitterDataset)
            create_sizer.Add(add_twitter_btn)
        toolbar_sizer.Add(create_sizer, 0, wx.ALL, 5)

        modify_box = wx.StaticBox(self, label=GUIText.MODIFY)
        modify_box.SetFont(main_frame.DETAILS_LABEL_FONT)
        modify_sizer = wx.StaticBoxSizer(modify_box, wx.HORIZONTAL)
        remove_btn = wx.Button(self, label=GUIText.DELETE)
        remove_btn.SetToolTip(GUIText.DATASETS_DELETE_TOOLTIP)
        remove_btn.Bind(wx.EVT_BUTTON, self.OnDeleteDatasets)
        modify_sizer.Add(remove_btn)
        toolbar_sizer.Add(modify_sizer, 0, wx.ALL, 5)
        sizer.Add(toolbar_sizer)

        self.datasets_model = DatasetsDataViews.DatasetsViewModel(main_frame.datasets.values())
        self.datasets_ctrl = DatasetsDataViews.DatasetsViewCtrl(self, self.datasets_model)
        self.datasets_ctrl.Bind(dv.EVT_DATAVIEW_ITEM_EDITING_DONE, self.OnChangeDatasetName)
        self.datasets_ctrl.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        sizer.Add(self.datasets_ctrl, 1, wx.EXPAND, 5)

        self.SetSizer(sizer)

        #create menu for submodule
        self.menu = wx.Menu()
        self.menu_menuitem = None

        logger.info("Finished")

    def OnShowPopup(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnShowPopup")
        logger.info("Starting")
        menu = wx.Menu()
        details_menuitem = menu.Append(wx.ID_ANY, GUIText.VIEW_DETAILS)
        menu.Bind(wx.EVT_MENU, self.OnAccessDetails, details_menuitem)
        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.options_dict['adjustable_label_fields_mode']:
            label_fields_menuitem = menu.Append(wx.ID_ANY, GUIText.CUSTOMIZE_LABEL_FIELDS)
            menu.Bind(wx.EVT_MENU, self.OnCustomizeLabelFields, label_fields_menuitem)
        if main_frame.options_dict['adjustable_computation_fields_mode']:
            computation_fields_menuitem = menu.Append(wx.ID_ANY, GUIText.CUSTOMIZE_COMPUTATIONAL_FIELDS)
            menu.Bind(wx.EVT_MENU, self.OnCustomizeComputationalFields, computation_fields_menuitem)
        menu.AppendSeparator()
        copy_menu_item = menu.Append(wx.ID_ANY, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.datasets_ctrl.OnCopyItems, copy_menu_item)
        self.PopupMenu(menu)
        logger.info("Finished")

    def OnCustomizeLabelFields(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnCustomizeLabelFields")
        logger.info("Starting")
        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            node = self.datasets_model.ItemToObject(item)
            while node.parent is not None:
                node = node.parent

            if node.key not in self.module.labelfields_dialogs:
                self.module.labelfields_dialogs[node.key] = SubModuleFields.FieldsDialog(parent=self.module,
                                                                                          title=str(node.name)+" "+GUIText.CUSTOMIZE_LABEL_FIELDS,
                                                                                          dataset=node,
                                                                                          fields=node.label_fields,
                                                                                          label_fields=True)
            self.module.labelfields_dialogs[node.key].Show()
            self.module.labelfields_dialogs[node.key].SetFocus()
        logger.info("Finished")

    def OnCustomizeComputationalFields(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnCustomizeComputationalFields")
        logger.info("Starting")
        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            node = self.datasets_model.ItemToObject(item)
            while node.parent is not None:
                node = node.parent
            if node.key not in self.module.computationfields_dialogs:
                self.module.computationfields_dialogs[node.key] = SubModuleFields.FieldsDialog(parent=self.module,
                                                                                                title=str(node.name)+" "+GUIText.CUSTOMIZE_COMPUTATIONAL_FIELDS,
                                                                                                dataset=node,
                                                                                                fields=node.computational_fields)
            self.module.computationfields_dialogs[node.key].Show()
            self.module.computationfields_dialogs[node.key].SetFocus()
        logger.info("Finished")

    def OnAccessDetails(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAccessDetails")
        logger.info("Starting")

        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            if item is not None:
                node = self.datasets_model.ItemToObject(item)
                if isinstance(node, Datasets.Dataset):
                    if node.key not in self.dataset_dialogs:
                        self.dataset_dialogs[node.key] = DatasetsGUIs.DatasetDetailsDialog(self, self.module, node)
                    self.dataset_dialogs[node.key].Show()
                    self.dataset_dialogs[node.key].SetFocus()
        logger.info("Finished")

    def OnAddRedditDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddRedditDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        CollectionDialogs.RedditDatasetRetrieverDialog(self).ShowModal()
        logger.info("Finished")
    
    def OnAddTwitterDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddTwitterDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        main_frame = wx.GetApp().GetTopWindow()
        CollectionDialogs.TwitterDatasetRetrieverDialog(self).ShowModal()
        logger.info("Finished")
    
    def OnAddCSVDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddCSVDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        CollectionDialogs.CSVDatasetRetrieverDialog(self).ShowModal()
        logger.info("Finished")

    def OnChangeDatasetName(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnChangeDatasetName")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.CHANGING_NAME_LABEL,
                                        freeze=True)
        try:
            main_frame.StepProgressDialog(GUIText.CHANGING_NAME_STEP, enable=True)
            node = self.datasets_model.ItemToObject(event.GetItem())
            if isinstance(node, Datasets.Dataset):
                new_name = event.GetValue()
                if node.name != new_name:
                    main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_MSG1 + node.name + GUIText.CHANGING_NAME_MSG2 + new_name)
                    node.name = new_name
                    main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnDeleteDatasets(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnDeleteDatasets")
        logger.info("Starting")
        delete_nodes = []
        cancelled = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.DELETING_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.StepProgressDialog(GUIText.DELETING_BUSY_LABEL, enable=True)
            main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_PREPARING_MSG)
            start_time = datetime.now()
            remaining_loops = len(delete_nodes)
            #perform delete on any selected groups or grouped datasets
            for item in self.datasets_ctrl.GetSelections():
                node = self.datasets_model.ItemToObject(item)
                if isinstance(node, Datasets.Dataset):
                    confirm_dialog = wx.MessageDialog(self, str(node.key)+GUIText.DELETE_CONFIRMATION
                                                      + GUIText.DATASETS_DELETE_CONFIRMATION_WARNING,
                                                      GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
                    confirm_dialog.SetYesNoLabels(GUIText.DATASETS_DELETE_DATASET, GUIText.SKIP)
                    confirm_flg = confirm_dialog.ShowModal()
                    if confirm_flg  == wx.ID_YES:
                        delete_nodes.append(node)
                    elif confirm_flg == wx.ID_CANCEL:
                        delete_nodes = []
                        cancelled = True
                        break
            if len(delete_nodes) > 0:
                remaining_loops = len(delete_nodes)
                estimated_loop_time = timedelta()
                db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
                for node in delete_nodes:
                    start_loop_time = datetime.now()
                    main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_REMOVING_MSG+str(node.name))
                    if node.key in main_frame.datasets:
                        del main_frame.datasets[node.key]
                    db_conn.DeleteDatasetFromStringTokens(node.key)
                    node.DestroyObject()
                    remaining_loops -= 1
                    current_time = datetime.now()
                    new_loop_time = current_time - start_loop_time
                    if new_loop_time > estimated_loop_time:
                        estimated_loop_time = new_loop_time
                    main_frame.UpdateStepEstimatedTimeProgressDialog((current_time-start_time)+(estimated_loop_time*remaining_loops))
                main_frame.DatasetsUpdated()

        finally:
            if cancelled:
                main_frame.CloseProgressDialog(GUIText.CANCELED, thaw=True)
            else:
                main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetsPanel.DatasetsUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if len(self.dataset_dialogs.keys()) > 0:
            main_frame.StepProgressDialog(GUIText.UPDATING_DATASET_BUSY_MSG, enable=True)
        self.datasets_model.Cleared()
        self.datasets_ctrl.Expander(None)
        for key in list(self.dataset_dialogs.keys()):
            dataset = self.dataset_dialogs[key].dataset
            if dataset.key not in main_frame.datasets:
                self.dataset_dialogs[key].Destroy()
                del self.dataset_dialogs[key]
            else:
                self.dataset_dialogs[key].RefreshDetails()
        logger.info("Finished")
    
    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetsPanel.DocumentsUpdated")
        logger.info("Starting")
        self.datasets_model.Cleared()
        self.datasets_ctrl.Expander(None)
        logger.info("Finished")

class DatasetDetailsPanel(wx.Panel):
    def __init__(self, parent, module, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        self.parent = parent
        self.module = module
        self.dataset = None
        self.tokenization_thread = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.ChangeDataset(self.dataset)

        CustomEvents.TOKENIZER_EVT_RESULT(self, self.OnTokenizerEnd)

        logger.info("Finished")

    def OnAddRedditDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnAddRedditDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        main_frame = wx.GetApp().GetTopWindow()
        CollectionDialogs.RedditDatasetRetrieverDialog(main_frame).Show()
        logger.info("Finished")
    
    def OnAddTwitterDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddTwitterDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        main_frame = wx.GetApp().GetTopWindow()
        CollectionDialogs.TwitterDatasetRetrieverDialog(self).Show()
        logger.info("Finished")

    def OnAddCSVDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnAddCSVDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        main_frame = wx.GetApp().GetTopWindow()
        CollectionDialogs.CSVDatasetRetrieverDialog(main_frame).Show()
        logger.info("Finished")

    def OnDeleteDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnDeleteDatasets")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.DELETING_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.StepProgressDialog(GUIText.DELETING_BUSY_LABEL, enable=True)
            main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_PREPARING_MSG)
            confirm_dialog = wx.MessageDialog(self, str(self.dataset.key)+GUIText.DELETE_CONFIRMATION
                                              + GUIText.DATASETS_DELETE_CONFIRMATION_WARNING,
                                              GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
            confirm_dialog.SetOKLabel(GUIText.DATASETS_DELETE_DATASET)
            if confirm_dialog.ShowModal() == wx.ID_YES:
                main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_REMOVING_MSG+str(self.dataset.name))
                if self.dataset.parent is None:
                    del main_frame.datasets[self.dataset.key]
                Database.DatabaseConnection(main_frame.current_workspace.name).DeleteDataset(self.dataset.key)
                self.dataset.DestroyObject()
                main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def ChangeDataset(self, dataset):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.ChangeDataset")
        logger.info("Starting")
        self.dataset = dataset
        self.sizer.Clear(True)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(dataset, Datasets.Dataset):
            dataset_panel = DatasetsGUIs.DatasetPanel(self, self.module, dataset, header=True)
            if hasattr(dataset_panel, 'delete_btn'):
                dataset_panel.delete_btn.Bind(wx.EVT_BUTTON, self.OnDeleteDataset)
            self.sizer.Add(dataset_panel)
        else:
            online_box = wx.StaticBox(self, label=GUIText.ONLINE_SOURCES)
            online_box.SetFont(main_frame.DETAILS_LABEL_FONT)
            online_sizer = wx.StaticBoxSizer(online_box, wx.VERTICAL)
            self.sizer.Add(online_sizer, 0, wx.ALL, 5)

            reddit_sizer = wx.BoxSizer()
            online_sizer.Add(reddit_sizer)
            add_reddit_btn = wx.Button(self, label=GUIText.DATASETS_RETRIEVE_REDDIT)
            add_reddit_btn.SetToolTip(GUIText.DATASETS_RETRIEVE_REDDIT_TOOLTIP)
            add_reddit_btn.Bind(wx.EVT_BUTTON, self.OnAddRedditDataset)
            reddit_sizer.Add(add_reddit_btn, 0, wx.ALL, 5)
            add_reddit_description = wx.StaticText(self, label=GUIText.REDDIT_DESC)
            reddit_sizer.Add(add_reddit_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            add_reddit_link = wx.adv.HyperlinkCtrl(self, label="1", url=GUIText.REDDIT_URL)
            reddit_sizer.Add(add_reddit_link, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            
            if 'twitter_enabled' in main_frame.options_dict:
                twitter_sizer = wx.BoxSizer()
                online_sizer.Add(twitter_sizer)
                add_twitter_btn = wx.Button(self, label=GUIText.DATASETS_RETRIEVE_TWITTER)
                add_twitter_btn.SetToolTip(GUIText.DATASETS_RETRIEVE_TWITTER_TOOLTIP)
                add_twitter_btn.Bind(wx.EVT_BUTTON, self.OnAddTwitterDataset)
                twitter_sizer.Add(add_twitter_btn, 0, wx.ALL, 5)
                add_twitter_description = wx.StaticText(self, label=GUIText.TWITTER_DESC)
                twitter_sizer.Add(add_twitter_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
                add_twitter_link = wx.adv.HyperlinkCtrl(self, label="2", url=GUIText.TWITTER_URL)
                twitter_sizer.Add(add_twitter_link, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            
            local_box = wx.StaticBox(self, label=GUIText.LOCAL_SOURCES)
            local_box.SetFont(main_frame.DETAILS_LABEL_FONT)
            local_sizer = wx.StaticBoxSizer(local_box, wx.VERTICAL)
            self.sizer.Add(local_sizer, 0, wx.ALL, 5)

            csv_sizer = wx.BoxSizer()
            local_sizer.Add(csv_sizer)
            add_csv_btn = wx.Button(self, label=GUIText.DATASETS_IMPORT_CSV)
            add_csv_btn.SetToolTip(GUIText.DATASETS_IMPORT_CSV_TOOLTIP)
            add_csv_btn.Bind(wx.EVT_BUTTON, self.OnAddCSVDataset)
            csv_sizer.Add(add_csv_btn, 0, wx.ALL, 5)
            add_csv_description = wx.StaticText(self, label=GUIText.CSV_DESC)
            csv_sizer.Add(add_csv_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            
        self.Layout()
        logger.info("Finished")

    def OnTokenizerEnd(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnTokenizerEnd")
        logger.info("Starting")
        self.tokenization_thread.join()
        self.tokenization_thread = None
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DatasetsUpdated()
        main_frame.CloseProgressDialog(thaw=True)
        main_frame.multiprocessing_inprogress_flag = False
        logger.info("Finished")