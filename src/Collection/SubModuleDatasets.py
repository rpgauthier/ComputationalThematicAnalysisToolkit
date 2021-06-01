'''Code for the submodule that controls grouping of data'''
import logging
from datetime import datetime

import wx
import wx.dataview as dv
import wx.lib.scrolledpanel

from Common.GUIText import Collection as GUIText
import Common.Constants as Constants
import Common.Objects.Datasets as Datasets
import Common.Objects.Utilities.Datasets as DatasetsUtilities
import Common.Objects.DataViews.Datasets as DatasetsDataViews
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Common.CustomEvents as CustomEvents
import Collection.CollectionDialogs as CollectionDialogs
import Collection.SubModuleFields as SubModuleFields

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
        create_toolbar.Realize()
        create_sizer.Add(create_toolbar)
        toolbar_sizer.Add(create_sizer, 0, wx.ALL, 5)

        modify_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.MODIFY)
        modify_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        group_tool = modify_toolbar.AddTool(wx.ID_ANY, label=GUIText.GROUP, bitmap=wx.Bitmap(1, 1),
                                            shortHelp=GUIText.DATASETS_GROUP_TOOLTIP)
        modify_toolbar.Bind(wx.EVT_MENU, self.OnGroupDatasets, group_tool)
        ungroup_tool = modify_toolbar.AddTool(wx.ID_ANY, label=GUIText.UNGROUP, bitmap=wx.Bitmap(1, 1),
                                              shortHelp=GUIText.DATASETS_UNGROUP_TOOLTIP)
        modify_toolbar.Bind(wx.EVT_MENU, self.OnUngroupDatasets, ungroup_tool)
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
        fields_menuitem = menu.Append(wx.ID_ANY, GUIText.CUSTOMIZE_FIELDS)
        menu.Bind(wx.EVT_MENU, self.OnCustomizeFields, fields_menuitem)
        menu.AppendSeparator()
        copy_menu_item = menu.Append(wx.ID_ANY, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.datasets_ctrl.OnCopyItems, copy_menu_item)
        self.PopupMenu(menu)
        logger.info("Finished")

    def OnCustomizeFields(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnCustomizeFields")
        logger.info("Starting")
        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            node = self.datasets_model.ItemToObject(item)
            while node.parent is not None:
                node = node.parent
            SubModuleFields.FieldsDialog(self, node).Show()
        logger.info("Finished")

    def OnAccessDetails(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAccessDetails")
        logger.info("Starting")

        selections = self.datasets_ctrl.GetSelections()
        for item in selections:
            if item is not None:
                node = self.datasets_model.ItemToObject(item)
                if isinstance(node, Datasets.GroupedDataset) or isinstance(node, Datasets.Dataset):
                    DatasetsGUIs.DatasetDetailsDialog(self, node).Show()
                #elif isinstance(node, Datasets.MergedField):
                #elif isinstance(node, Datasets.Field):
        logger.info("Finished")

    def OnAddRedditDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddRedditDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        main_frame = wx.GetApp().GetTopWindow()
        CollectionDialogs.RedditDatasetRetrieverDialog(self).Show()
        logger.info("Finished")
    
    def OnAddCSVDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnAddCSVDataset")
        logger.info("Starting")
        #create a retriever of chosen type in a popup
        main_frame = wx.GetApp().GetTopWindow()
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
            if isinstance(node, Datasets.Dataset) or isinstance(node, Datasets.GroupedDataset):
                new_name = event.GetValue()
                if node.name != new_name:
                    old_key = node.key
                    if isinstance(node, Datasets.GroupedDataset):
                        new_key = (new_name, 'group')
                    elif isinstance(node, Datasets.Dataset):
                        new_key = (new_name, node.dataset_source, node.dataset_type,)
                    if new_key in main_frame.datasets:
                        wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                                        GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                        logger.error("Duplicate name[%s] entered by user", str(new_key))
                    else:
                        continue_flag = True
                        for key in main_frame.datasets:
                            if isinstance(main_frame.datasets[key], Datasets.GroupedDataset):
                                if new_key in main_frame.datasets[key].datasets:
                                    continue_flag = False
                                    wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                                        GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                                    logger.error("Duplicate name[%s] entered by user", str(new_key))
                                    break
                        if continue_flag:
                            main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_MSG1+str(node.key)\
                                                           +GUIText.CHANGING_NAME_BUSY_MSG2+str(new_key))
                            node.key = new_key
                            node.name = new_name
                            if old_key in main_frame.datasets:
                                main_frame.datasets[new_key] = main_frame.datasets[old_key]
                                del main_frame.datasets[old_key]
                            elif node.parent is not None:
                                node.parent.datasets[new_key] = node
                                del node.parent.datasets[old_key]
                            main_frame.DatasetKeyChange(old_key, new_key)
                            main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnGroupDatasets(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnGroupDatasets")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        selections = self.datasets_ctrl.GetSelections()
        main_frame.CreateProgressDialog(GUIText.GROUPING_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.GROUPING_BUSY_PREPARING_MSG)
            nodes = []
            impacted_groupeddatasets = []
            #check whether any selections are already grouped and if so break down into datasets
            for item in selections:
                node = self.datasets_model.ItemToObject(item)
                if isinstance(node, Datasets.GroupedDataset):
                    for dataset in node.datasets:
                        if dataset not in nodes:
                            nodes.append(dataset)
                if isinstance(node, Datasets.Dataset):
                    if node not in nodes:
                        nodes.append(node)
            if len(nodes) > 0:
                with wx.TextEntryDialog(self, message=GUIText.DATASETS_GROUP_NAME,
                                        caption=GUIText.INPUT_REQUEST, value="") as name_dialog:
                    if name_dialog.ShowModal() == wx.ID_OK:
                        name = name_dialog.GetValue()
                        key = (name, "group")
                        if key not in main_frame.datasets:
                            main_frame.PulseProgressDialog(GUIText.GROUPING_BUSY_CREATING_MSG+name)
                            group = Datasets.GroupedDataset(key, name)
                            main_frame.datasets[group.key] = group
                            for node in nodes:
                                main_frame.PulseProgressDialog(GUIText.GROUPING_BUSY_ADDING_MSG1+str(node.key)\
                                                      +GUIText.GROUPING_BUSY_ADDING_MSG2+str(key))
                                with CollectionDialogs.GroupingFieldDialog(self, node) as groupingfield_dialog:
                                    if groupingfield_dialog.ShowModal() == wx.ID_OK:
                                        #get the one element selected
                                        if node.parent is not None:
                                            old_parent = node.parent
                                            del old_parent.datasets[node.name]
                                            if len(old_parent.datasets) > 0:
                                                old_parent.last_changed_dt = datetime.now()
                                                if old_parent not in impacted_groupeddatasets:
                                                    impacted_groupeddatasets.append(old_parent)
                                            else:
                                                if old_parent in impacted_groupeddatasets:
                                                    impacted_groupeddatasets.remove(old_parent)
                                        else:
                                            del main_frame.datasets[node.key]
                                        node.parent = group
                                        group.datasets[node.key] = node
                            impacted_groupeddatasets.append(group)
                            for grouped_dataset in impacted_groupeddatasets:
                                main_frame.PulseProgressDialog(GUIText.GROUPING_BUSY_UPDATING_MSG+str(grouped_dataset.key))
                                #TODO need to move into a thread
                                DatasetsUtilities.CreateDatasetObjectsMetadata(grouped_dataset)
                            self.datasets_model.Cleared()
                            main_frame.DatasetsUpdated()
                        else:
                            wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                                        GUIText.ERROR, wx.OK | wx.ICON_ERROR)
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnUngroupDatasets(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnUngroupDatasets")
        logger.info("Starting")
        performed_flag = False
        impacted_groupeddatasets = []
        def DatasetUngrouper(dataset):
            if dataset.key not in main_frame.datasets:
                nonlocal impacted_groupeddatasets
                nonlocal performed_flag
                old_parent = dataset.parent
                main_frame.PulseProgressDialog(GUIText.UNGROUPING_BUSY_REMOVING_MSG1+str(node.key)\
                                      +GUIText.UNGROUPING_BUSY_REMOVING_MSG2+str(old_parent.key))
                dataset.parent = None
                dataset.grouping_field = None
                main_frame.datasets[dataset.key] = dataset
                del old_parent.datasets[dataset.key]
                if len(old_parent.datasets) == 0:
                    old_parent.DestroyObject()
                    del main_frame.datasets[old_parent.key]
                    if old_parent in impacted_groupeddatasets:
                        impacted_groupeddatasets.remove(old_parent)
                else:
                    old_parent.last_changed_dt = datetime.now()
                    if old_parent not in impacted_groupeddatasets:
                        impacted_groupeddatasets.append(old_parent)
                performed_flag = True
        def GroupedDatasetUngrouper(grouped_dataset):
            for dataset in list(grouped_dataset.datasets.values()):
                DatasetUngrouper(dataset)

        main_frame = wx.GetApp().GetTopWindow()
        selections = self.datasets_ctrl.GetSelections()
        main_frame.CreateProgressDialog(GUIText.UNGROUPING_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.UNGROUPING_BUSY_PREPARING_MSG)
            #perform ungroup on any selected groups or grouped datasets
            for item in selections:
                node = self.datasets_model.ItemToObject(item)
                
                if isinstance(node, Datasets.Dataset):
                    DatasetUngrouper(node)
                elif isinstance(node, Datasets.GroupedDataset):
                    GroupedDatasetUngrouper(node)
            if performed_flag:
                for grouped_dataset in impacted_groupeddatasets:
                    main_frame.PulseProgressDialog(GUIText.UNGROUPING_BUSY_UPDATING_MSG+str(grouped_dataset.key))
                    #TODO need to move into a thread
                    DatasetsUtilities.CreateDatasetObjectsMetadata(grouped_dataset)
                main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnDeleteDatasets(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnDeleteDatasets")
        logger.info("Starting")
        delete_nodes = []
        impacted_groupeddatasets = []
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.DELETING_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_PREPARING_MSG)
            #perform delete on any selected groups or grouped datasets
            for item in self.datasets_ctrl.GetSelections():
                node = self.datasets_model.ItemToObject(item)
                if isinstance(node, Datasets.Dataset) or isinstance(node, Datasets.GroupedDataset):
                    if wx.MessageBox(str(node.key) + GUIText.DELETE_CONFIRMATION
                                    + GUIText.DATASETS_DELETE_CONFIRMATION_WARNING,
                                    GUIText.WARNING, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
                        delete_nodes.append(node)
            if len(delete_nodes) > 0:
                for node in delete_nodes:
                    main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_REMOVING_MSG+str(node.key))
                    if node.parent is None:
                        if node.key in main_frame.datasets:
                            del main_frame.datasets[node.key]
                    else:
                        old_parent = node.parent
                        if len(old_parent.datasets) == 0:
                            old_parent.DestroyObject()
                            del main_frame.datasets[old_parent.key]
                            if old_parent in impacted_groupeddatasets:
                                impacted_groupeddatasets.remove(old_parent)
                        else:
                            old_parent.last_changed_dt = datetime.now()
                            if old_parent not in impacted_groupeddatasets:
                                impacted_groupeddatasets.append(old_parent)
                    node.DestroyObject()
                for grouped_dataset in impacted_groupeddatasets:
                    main_frame.PulseProgressDialog(GUIText.DELETING_BUSY_UPDATING_MSG+str(grouped_dataset.key))
                    #TODO need to move into a thread
                    DatasetsUtilities.CreateDatasetObjectsMetadata(grouped_dataset)
                main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def DatasetsUpdated(self):
        '''loads data specifications into submodule after a retrieval'''
        logger = logging.getLogger(__name__+".DatasetsPanel.DatasetsUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.UPDATING_DATASET_BUSY_MSG)
        self.datasets_model.Cleared()

        logger.info("Finished")
    
    def DocumentsUpdated(self):
        '''loads data specifications into submodule after a retrieval'''
        logger = logging.getLogger(__name__+".DatasetsPanel.DocumentsUpdated")
        logger.info("Starting")
        self.datasets_model.Cleared()
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

    def OnAddCSVDataset(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnAddRedditDataset")
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
        
        if isinstance(dataset, Datasets.GroupedDataset):
            details_sizer = wx.GridSizer(2, gap=wx.Size(0,0))
            self.sizer.Add(details_sizer)

            name_label = wx.StaticText(self, label=GUIText.NAME + ":")
            self.name_ctrl = wx.TextCtrl(self, value=self.dataset.name, style=wx.TE_PROCESS_ENTER)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            #TODO fix this maybe
            #self.name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDatasetKey)
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_sizer.Add(name_label)
            name_sizer.Add(self.name_ctrl)
            details_sizer.Add(name_sizer)

            created_date_label = wx.StaticText(self, label=GUIText.CREATED_ON + ": "
                                               +self.dataset.created_dt.strftime("%Y-%m-%d, %H:%M:%S"))
            details_sizer.Add(created_date_label)

            selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(dataset.language)
            language_label = wx.StaticText(self, label=GUIText.LANGUAGE + ": ")
            self.language_ctrl = wx.Choice(self, choices=Constants.AVALIABLE_DATASET_LANGUAGES2)
            self.language_ctrl.Select(selected_lang)
            language_sizer = wx.BoxSizer(wx.HORIZONTAL)
            language_sizer.Add(language_label)
            language_sizer.Add(self.language_ctrl)
            details_sizer.Add(language_sizer, 0, wx.ALL, 5)
            #TODO fix this maybe
            #self.language_ctrl.Bind(wx.EVT_CHOICE, self.OnChangeDatasetLanguage)
        elif isinstance(dataset, Datasets.Dataset):
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