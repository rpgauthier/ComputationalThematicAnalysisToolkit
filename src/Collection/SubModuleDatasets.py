'''Code for the submodule that controls grouping of data'''
import logging

import wx
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

#TODO rethink create layout to have more description of the sources
class DatasetsListPanel(wx.Panel):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetsPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        self.parent = parent

        sizer = wx.BoxSizer(wx.VERTICAL)

        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        create_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.CREATE)
        create_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        add_reddit_tool = create_toolbar.AddTool(wx.ID_ANY,
                                                 label=GUIText.DATASETS_RETRIEVE_REDDIT,
                                                 bitmap=wx.Bitmap(1, 1),
                                                 shortHelp=GUIText.DATASETS_RETRIEVE_REDDIT_TOOLTIP)
        create_toolbar.Bind(wx.EVT_MENU, self.OnAddRedditDataset, add_reddit_tool)
        add_csv_tool = create_toolbar.AddTool(wx.ID_ANY,
                                              label=GUIText.DATASETS_RETRIEVE_CSV,
                                              bitmap=wx.Bitmap(1, 1),
                                              shortHelp=GUIText.DATASETS_RETRIEVE_CSV_TOOLTIP)
        create_toolbar.Bind(wx.EVT_MENU, self.OnAddCSVDataset, add_csv_tool)
        add_twitter_tool = create_toolbar.AddTool(wx.ID_ANY,
                                    label=GUIText.DATASETS_RETRIEVE_TWITTER,
                                    bitmap=wx.Bitmap(1, 1),
                                    shortHelp=GUIText.DATASETS_RETRIEVE_TWITTER_TOOLTIP)
        create_toolbar.Bind(wx.EVT_MENU, self.OnAddTwitterDataset, add_twitter_tool)
        create_toolbar.Realize()
        create_sizer.Add(create_toolbar)
        toolbar_sizer.Add(create_sizer, 0, wx.ALL, 5)

        modify_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.MODIFY)
        modify_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        remove_tool = modify_toolbar.AddTool(wx.ID_ANY, label=GUIText.DELETE, bitmap=wx.Bitmap(1, 1),
                                             shortHelp=GUIText.DATASETS_DELETE_TOOLTIP)
        modify_toolbar.Bind(wx.EVT_MENU, self.OnDeleteDatasets, remove_tool)
        modify_toolbar.Realize()
        modify_sizer.Add(modify_toolbar)
        toolbar_sizer.Add(modify_sizer, 0, wx.ALL, 5)
        sizer.Add(toolbar_sizer)

        main_frame = wx.GetApp().GetTopWindow()
        self.datasets_model = DatasetsDataViews.DatasetsViewModel(main_frame.datasets.values())
        self.datasets_ctrl = DatasetsDataViews.DatasetsViewCtrl(self, self.datasets_model)
        self.datasets_ctrl.Bind(dv.EVT_DATAVIEW_ITEM_EDITING_DONE, self.OnChangeDatasetKey)
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
        metadatafields_menuitem = menu.Append(wx.ID_ANY, GUIText.CUSTOMIZE_METADATAFIELDS)
        menu.Bind(wx.EVT_MENU, self.OnCustomizeMetadataFields, metadatafields_menuitem)
        includedfields_menuitem = menu.Append(wx.ID_ANY, GUIText.CUSTOMIZE_INCLUDEDFIELDS)
        menu.Bind(wx.EVT_MENU, self.OnCustomizeIncludedFields, includedfields_menuitem)
        menu.AppendSeparator()
        copy_menu_item = menu.Append(wx.ID_ANY, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.datasets_ctrl.OnCopyItems, copy_menu_item)
        self.PopupMenu(menu)
        logger.info("Finished")

    def OnCustomizeMetadataFields(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnCustomizeMetadataFields")
        logger.info("Starting")
        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            node = self.datasets_model.ItemToObject(item)
            while node.parent is not None:
                node = node.parent
            SubModuleFields.FieldsDialog(parent=self,
                                         title=str(node.key)+" "+GUIText.CUSTOMIZE_METADATAFIELDS,
                                         dataset=node,
                                         fields=node.metadata_fields,
                                         metadata_fields=True).Show()
        logger.info("Finished")

    def OnCustomizeIncludedFields(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnCustomizeIncludedFields")
        logger.info("Starting")
        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            node = self.datasets_model.ItemToObject(item)
            while node.parent is not None:
                node = node.parent
            SubModuleFields.FieldsDialog(parent=self,
                                         title=str(node.key)+" "+GUIText.CUSTOMIZE_INCLUDEDFIELDS,
                                         dataset=node,
                                         fields=node.chosen_fields).Show()
        logger.info("Finished")

    def OnAccessDetails(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAccessDetails")
        logger.info("Starting")

        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            if item is not None:
                node = self.datasets_model.ItemToObject(item)
                if isinstance(node, Datasets.Dataset):
                    DatasetsGUIs.DatasetDetailsDialog(self, node).Show()
                #elif isinstance(node, Datasets.Field):
        logger.info("Finished")

    def OnAddRedditDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddRedditDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        CollectionDialogs.RedditDatasetRetrieverDialog(self).Show()
        logger.info("Finished")
    
    def OnAddTwitterDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddTwitterDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        main_frame = wx.GetApp().GetTopWindow()
        CollectionDialogs.TwitterDatasetRetrieverDialog(self).Show()
        logger.info("Finished")
    
    def OnAddCSVDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddCSVDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        CollectionDialogs.CSVDatasetRetrieverDialog(self).Show()
        logger.info("Finished")

    def OnChangeDatasetKey(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnChangeDatasetKey")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.CHANGING_NAME_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_PREPARING_MSG)
            node = self.datasets_model.ItemToObject(event.GetItem())
            if isinstance(node, Datasets.Dataset):
                new_name = event.GetValue()
                if node.name != new_name:
                    old_key = node.key
                    new_key = (new_name, node.dataset_source, node.dataset_type,)
                    if new_key in main_frame.datasets:
                        wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                                        GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                        logger.error("Duplicate name[%s] entered by user", str(new_key))
                    else:
                        main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_MSG1+str(node.key)\
                                                       +GUIText.CHANGING_NAME_BUSY_MSG2+str(new_key))
                        node.key = new_key
                        node.name = new_name
                        main_frame.datasets[new_key] = main_frame.datasets[old_key]
                        del main_frame.datasets[old_key]
                        Database.DatabaseConnection(main_frame.current_workspace.name).UpdateDatasetKey(old_key, new_key)
                        main_frame.DatasetKeyChange(old_key, new_key)
                        main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnDeleteDatasets(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnDeleteDatasets")
        logger.info("Starting")
        delete_nodes = []
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.DELETING_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_PREPARING_MSG)
            #perform delete on any selected groups or grouped datasets
            for item in self.datasets_ctrl.GetSelections():
                node = self.datasets_model.ItemToObject(item)
                if isinstance(node, Datasets.Dataset):
                    if wx.MessageBox(str(node.key) + GUIText.DELETE_CONFIRMATION
                                    + GUIText.DATASETS_DELETE_CONFIRMATION_WARNING,
                                    GUIText.WARNING, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
                        delete_nodes.append(node)
            if len(delete_nodes) > 0:
                db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
                for node in delete_nodes:
                    main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_REMOVING_MSG+str(node.key))
                    if node.key in main_frame.datasets:
                        del main_frame.datasets[node.key]
                    db_conn.DeleteDatasetFromStringTokens(node.key)
                    node.DestroyObject()
                    #TODO need to either:
                    # 1) update SAMPLES and CODES
                    # 2) delete associated SAMPLES and CODES when associated dataset has been deleted as they will no longr work correctly

                main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetsPanel.DatasetsUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.UPDATING_DATASET_BUSY_MSG)
        self.datasets_model.Cleared()
        self.datasets_ctrl.Expander(None)
        logger.info("Finished")
    
    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetsPanel.DocumentsUpdated")
        logger.info("Starting")
        self.datasets_model.Cleared()
        self.datasets_ctrl.Expander(None)
        logger.info("Finished")

class DatasetDetailsPanel(wx.Panel):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        self.parent = parent
        self.dataset = None
        self.tokenization_thread = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.ChangeDataset(self.dataset)

        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
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
            main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_PREPARING_MSG)
            if wx.MessageBox(str(self.dataset.key) + GUIText.DELETE_CONFIRMATION
                            + GUIText.DATASETS_DELETE_CONFIRMATION_WARNING,
                            GUIText.WARNING, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
                main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_REMOVING_MSG+str(self.dataset.key))
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
        if main_frame.multipledatasets_mode or dataset is None:
            create_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.CREATE)
            toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
            add_reddit_tool = toolbar.AddTool(wx.ID_ANY,
                                            label=GUIText.DATASETS_RETRIEVE_REDDIT,
                                            bitmap=wx.Bitmap(1, 1),
                                            shortHelp=GUIText.DATASETS_RETRIEVE_REDDIT_TOOLTIP)
            toolbar.Bind(wx.EVT_MENU, self.OnAddRedditDataset, add_reddit_tool)
            add_twitter_tool = toolbar.AddTool(wx.ID_ANY,
                                          label=GUIText.DATASETS_RETRIEVE_TWITTER,
                                          bitmap=wx.Bitmap(1, 1),
                                          shortHelp=GUIText.DATASETS_RETRIEVE_TWITTER_TOOLTIP)
            toolbar.Bind(wx.EVT_MENU, self.OnAddTwitterDataset, add_twitter_tool)
            add_csv_tool = toolbar.AddTool(wx.ID_ANY,
                                           label=GUIText.DATASETS_RETRIEVE_CSV,
                                           bitmap=wx.Bitmap(1, 1),
                                           shortHelp=GUIText.DATASETS_RETRIEVE_CSV_TOOLTIP)
            toolbar.Bind(wx.EVT_MENU, self.OnAddCSVDataset, add_csv_tool)
            if dataset is not None:
                remove_tool = toolbar.AddTool(wx.ID_ANY, label=GUIText.DELETE, bitmap=wx.Bitmap(1, 1),
                                            shortHelp=GUIText.DATASETS_DELETE_TOOLTIP)
                toolbar.Bind(wx.EVT_MENU, self.OnDeleteDataset, remove_tool)
            toolbar.Realize()
            create_sizer.Add(toolbar)
            self.sizer.Add(create_sizer, 0, wx.ALL, 5)
        
        if isinstance(dataset, Datasets.Dataset):
            dataset_panel = DatasetsGUIs.DatasetPanel(self, dataset, header=True)
            self.sizer.Add(dataset_panel)
        self.Layout()
        logger.info("Finished")

    def OnProgress(self, event):
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(event.data)
    
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