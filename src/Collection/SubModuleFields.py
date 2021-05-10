import logging
import copy
from datetime import datetime

import wx
import wx.aui
import wx.lib.scrolledpanel

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
import Common.Objects.Datasets as Datasets
import Common.Objects.DataViews.Datasets as DatasetsDataViews
from Common.GUIText import Collection as GUIText
import Collection.CollectionThreads as CollectionThreads
#import Collection.DataTokenizer as DataTokenizer

class FieldsDialog(wx.Dialog):
    def __init__(self, parent, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FieldsDialog["+str(dataset.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(dataset.key)+" "+GUIText.FIELDS_LABEL, size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer()

        self.fields_notebook = FieldsNotebook(self, dataset, size=self.GetSize())
        sizer.Add(self.fields_notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FieldsDialog.Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FieldsDialog.Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data

class FieldsNotebook(wx.aui.AuiNotebook):
    def __init__(self, parent, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FieldsNotebook.__init__")
        logger.info("Starting")
        wx.aui.AuiNotebook.__init__(self, parent, style=Constants.NOTEBOOK_MOVEABLE, size=size)

        self.dataset = dataset
        self.tokenization_thread = None

        avaliable_panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        avaliable_sizer = wx.BoxSizer(wx.VERTICAL)
        avaliable_toolbar = wx.ToolBar(avaliable_panel, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        add_tool = avaliable_toolbar.AddTool(wx.ID_ANY, label=GUIText.ADD, bitmap=wx.Bitmap(1, 1),
                                             shortHelp=GUIText.FIELDS_ADD_TOOLTIP)
        avaliable_toolbar.Bind(wx.EVT_MENU, self.OnAddFields, add_tool)

        avaliable_toolbar.Realize()
        avaliable_sizer.Add(avaliable_toolbar, proportion=0, flag=wx.ALL, border=5)

        self.avaliable_fields_model = DatasetsDataViews.AvaliableFieldsViewModel([dataset])
        self.avaliable_fields_ctrl = DatasetsDataViews.FieldsViewCtrl(avaliable_panel, self.avaliable_fields_model)
        avaliable_sizer.Add(self.avaliable_fields_ctrl, proportion=1, flag=wx.EXPAND, border=5)
        avaliable_panel.SetSizer(avaliable_sizer)
        avaliable_panel.SetupScrolling()
        self.AddPage(avaliable_panel, GUIText.FIELDS_AVALIABLE_LABEL)

        chosen_panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        chosen_sizer = wx.BoxSizer(wx.VERTICAL)
        chosen_toolbar = wx.ToolBar(chosen_panel, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        remove_tool = chosen_toolbar.AddTool(wx.ID_ANY, label=GUIText.REMOVE, bitmap=wx.Bitmap(1, 1),
                                             shortHelp=GUIText.FIELDS_REMOVE_TOOLTIP)
        chosen_toolbar.Bind(wx.EVT_MENU, self.OnRemoveFields, remove_tool)
        merge_tool = chosen_toolbar.AddTool(wx.ID_ANY, label=GUIText.MERGE, bitmap=wx.Bitmap(1, 1),
                                            shortHelp=GUIText.FIELDS_MERGE_TOOLTIP)
        chosen_toolbar.Bind(wx.EVT_MENU, self.OnMergeFields, merge_tool)
        unmerge_tool = chosen_toolbar.AddTool(wx.ID_ANY, label=GUIText.UNMERGE, bitmap=wx.Bitmap(1, 1),
                                            shortHelp=GUIText.FIELDS_UNMERGE_TOOLTIP)
        chosen_toolbar.Bind(wx.EVT_MENU, self.OnUnmergeFields, unmerge_tool)
        chosen_toolbar.Realize()
        chosen_sizer.Add(chosen_toolbar, proportion=0, flag=wx.ALL, border=5)
        self.chosen_fields_model = DatasetsDataViews.ChosenFieldsViewModel([dataset])
        self.chosen_fields_ctrl = DatasetsDataViews.FieldsViewCtrl(chosen_panel, self.chosen_fields_model)
        chosen_sizer.Add(self.chosen_fields_ctrl, proportion=1, flag=wx.EXPAND, border=5)
        chosen_panel.SetSizer(chosen_sizer)
        chosen_panel.SetupScrolling()
        self.AddPage(chosen_panel, GUIText.FIELDS_CHOSEN_LABEL)

        self.Split(1, wx.LEFT)
        self.Split(0, wx.LEFT)
        

        self.menu = wx.Menu()
        self.menu_menuitem = None

        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
        CustomEvents.TOKENIZER_EVT_RESULT(self, self.OnTokenizerEnd)
        
        logger.info("Finished")

    def OnAddFields(self, event):
        logger = logging.getLogger(__name__+".FieldsNotebook.OnAddFieldsStart")
        logger.info("Starting")
        tokenize_fields = []

        def FieldAdder(field):
            add_flag = True
            for chosen_field_name in field.parent.chosen_fields:
                if field.key == chosen_field_name :
                    wx.MessageBox(GUIText.FIELDS_EXISTS_ERROR+str(node.key),
                                  GUIText.WARNING, wx.OK | wx.ICON_WARNING)
                    add_flag = False
                    break
            if add_flag:
                new_field = copy.copy(field)
                field.parent.chosen_fields[new_field.key] = (new_field)
                nonlocal tokenize_fields
                tokenize_fields.append(new_field)

        def DatasetAdder(dataset):
            for field in dataset.avaliable_fields:
                FieldAdder(field)

        def GroupedDatasetAdder(grouped_dataset):
            for dataset in grouped_dataset.datasets:
                DatasetAdder(dataset)

        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.threaded_inprogress_flag == True:
            wx.MessageBox("A memory intensive operation is currently in progress."\
                          "\n Please try current action again after this operation has completed",
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
            return
        main_frame.CreateProgressDialog(GUIText.ADDING_FIELDS_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=True)
        main_frame.PulseProgressDialog(GUIText.ADDING_FIELDS_BUSY_PREPARING_MSG)
        for item in self.avaliable_fields_ctrl.GetSelections():
            node = self.avaliable_fields_model.ItemToObject(item)
            main_frame.PulseProgressDialog(GUIText.ADDING_FIELDS_BUSY_MSG+str(node.key))
            if isinstance(node, Datasets.Field):
                FieldAdder(node)
            if isinstance(node, Datasets.Dataset):
                DatasetAdder(node)
            if isinstance(node, Datasets.GroupedDataset):
                GroupedDatasetAdder(node)
        if len(tokenize_fields) > 0:
            main_frame.threaded_inprogress_flag == True
            self.tokenization_thread = CollectionThreads.TokenizerThread(self, main_frame, tokenize_fields)
        else:
            main_frame.CloseProgressDialog(thaw=True)
            self.GetTopLevelParent().Enable()
            self.GetTopLevelParent().SetFocus()

    def OnMergeFields(self, event):
        logger = logging.getLogger(__name__+".FieldsNotebook.OnMergeFields")
        logger.info("Starting")

        #default is merging at dataset level but can be escalated to group level by assigning root
        root = None
        nodes = []
        items = []
        merged_fields_list = []
        main_frame = wx.getApp().GetTopWindow()
        if main_frame.threaded_inprogress_flag == True:
            wx.MessageBox("A memory intensive operation is currently in progress."\
                          "\n Please try current action again after this operation has completed",
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
            return
        main_frame.CreateProgressDialog(GUIText.MERGING_FIELDS_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=True)
        main_frame.PulseProgressDialog(GUIText.MERGING_FIELDS_BUSY_PREPARING_MSG)
        for item in self.chosen_fields_ctrl.GetSelections():
            node = self.chosen_fields_model.ItemToObject(item)
            if not isinstance(node, Datasets.Field):
                wx.MessageBox(GUIText.FIELDS_MERGE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.error("Could not merge non-field selection[%s", str(type(node)))
                return
            else:
                if root is None:
                    root = node.dataset
                    nodes.append(node)
                    items.append(item)
                elif node.dataset is root:
                    nodes.append(node)
                    items.append(item)
                elif node.dataset is not root:
                    if isinstance(root, Datasets.Dataset):
                        root = root.parent
                    if root is None or node.dataset.parent is None:
                        wx.MessageBox(GUIText.FIELDS_MERGE_ERROR,
                                    GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                        logger.error("Could not merge fields from ungrouped datasets ")
                        node = []
                        break
                    elif root is not node.dataset.parent:
                        wx.MessageBox(GUIText.FIELDS_MERGE_ERROR,
                                    GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                        logger.warning("Could not merge fields from different dataset groups [%s] [%s]", root.key, node.dataset.parent.key)
                        node = []
                        break
                    else:
                        nodes.append(node)
                        items.append(item)

        if len(nodes) > 0:
            with wx.TextEntryDialog(self, message=GUIText.FIELDS_MERGED_NAME, 
                                    caption=GUIText.INPUT_REQUEST, value="") as name_ctrl:
                if name_ctrl.ShowModal() == wx.ID_OK:
                    key = name_ctrl.GetValue()
                    main_frame.PulseProgressDialog(GUIText.MERGING_FIELDS_BUSY_CREATING_MSG+str(key))
                    new_merged_field = Datasets.MergedField(root, key)
                    merged_fields_list.append(new_merged_field)
                    root.merged_fields[new_merged_field.key] = new_merged_field
                    for node in nodes:
                        main_frame.PulseProgressDialog(GUIText.MERGING_FIELDS_BUSY_MSG1+str(node.key)\
                                              +GUIText.MERGING_FIELDS_BUSY_MSG2+str(key))
                        old_parent = node.parent
                        if isinstance(old_parent, Datasets.MergedField):
                            del old_parent.chosen_fields[(node.dataset.key, node.key)]
                            if len(old_parent.chosen_fields) == 0:
                                old_parent.DestroyObject()
                        else:
                            del old_parent.chosen_fields[node.key]
                        new_merged_field.chosen_fields[(node.dataset.key, node.key)] = node
                        node.parent = new_merged_field

        if len(merged_fields_list) > 0:
            main_frame.threaded_inprogress_flag == True
            self.tokenization_thread = CollectionThreads.TokenizerThread(self, main_frame, merged_fields_list)
        else:
            main_frame.CloseProgressDialog(thaw=True)
            self.GetTopLevelParent().Enable()
            self.GetTopLevelParent().SetFocus()
        logger.info("Finished")

    def OnUnmergeFields(self, event):
        logger = logging.getLogger(__name__+".FieldsNotebook.OnUnmergeFields")
        logger.info("Starting")
        performed_flag = True
        tokenize_fields = []

        def FieldSplitter(field):
            nonlocal main_frame
            old_parent = field.parent
            main_frame.PulseProgressDialog(GUIText.UNMERGING_FIELDS_BUSY_MSG1+str(node.key)\
                                  +GUIText.UNMERGING_FIELDS_BUSY_MSG2+str(old_parent.key))
            if isinstance(old_parent, Datasets.MergedField):
                del old_parent.chosen_fields[(field.dataset.key, field.key)]
                if len(old_parent.chosen_fields) == 0:
                    old_parent.DestroyObject()
                if field.key not in field.dataset.chosen_fields:
                    field.dataset.chosen_fields[field.key] = field
                    field.parent = field.dataset
                    if field.tokenset == None:
                        nonlocal tokenize_fields
                        tokenize_fields.append(field)
                else:
                    field.DestroyObject()
                nonlocal performed_flag
                performed_flag = True

        def MergedFieldSplitter(merged_field):
            for field in list(reversed(merged_field.chosen_fields)):
                FieldSplitter(merged_field.chosen_fields[field])

        def DatasetSplitter(dataset):
            for merged_field in list(reversed(dataset.merged_fields)):
                MergedFieldSplitter(dataset.merged_fields[merged_field])

        def GroupedDatasetSplitter(grouped_dataset):
            for merged_field in list(reversed(grouped_dataset.merged_fields)):
                MergedFieldSplitter(grouped_dataset.merged_fields[merged_field])
            for dataset in grouped_dataset.datasets:
                DatasetSplitter(dataset)

        main_frame = wx.getApp().GetTopWindow()
        if main_frame.threaded_inprogress_flag == True:
            wx.MessageBox("A memory intensive operation is currently in progress."\
                          "\n Please try current action again after this operation has completed",
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
            return
        main_frame.CreateProgressDialog(GUIText.UNMERGING_FIELDS_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.UNMERGING_FIELDS_BUSY_PREPARING_MSG)
            for item in self.chosen_fields_ctrl.GetSelections():
                node = self.chosen_fields_model.ItemToObject(item)
                if isinstance(node, Datasets.Field):
                    FieldSplitter(node)
                elif isinstance(node, Datasets.MergedField):
                    MergedFieldSplitter(node)
                elif isinstance(node, Datasets.Dataset):
                    DatasetSplitter(node)
                elif isinstance(node, Datasets.GroupedDataset):
                    GroupedDatasetSplitter(node)
        finally:
            if len(tokenize_fields) > 0:
                main_frame.threaded_inprogress_flag == True
                self.tokenization_thread = CollectionThreads.TokenizerThread(self, main_frame, tokenize_fields)
            else:
                if performed_flag:
                    main_frame = self.GetGrandParent().GetTopLevelParent()
                    self.chosen_fields_model.Cleared()
                    main_frame.DatasetsUpdated()
                main_frame.CloseProgressDialog(thaw=True)
                self.GetTopLevelParent().Enable()
                self.GetTopLevelParent().SetFocus()
        logger.info("Finished")

    def OnRemoveFields(self, event):
        logger = logging.getLogger(__name__+".FieldsNotebook.OnRemoveFields")
        logger.info("Starting")
        performed_flag = False

        def FieldRemover(field):
            item = self.chosen_fields_model.ObjectToItem(field)
            parent_item = self.chosen_fields_model.ObjectToItem(field.parent)
            self.chosen_fields_model.ItemDeleted(parent_item, item)
            field.DestroyObject()
            nonlocal performed_flag
            performed_flag = True
        
        def MergedFieldRemover(merged_field):
            item = self.chosen_fields_model.ObjectToItem(merged_field)
            parent_item = self.chosen_fields_model.ObjectToItem(merged_field.parent)
            self.chosen_fields_model.ItemDeleted(parent_item, item)
            merged_field.DestroyObject()
            nonlocal performed_flag
            performed_flag = True

        def DatasetRemover(dataset):
            if wx.MessageBox(GUIText.FIELDS_REMOVE_DATASET_WARNING+str(dataset.key)+"?",
                             GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
                for field in list(reversed(dataset.chosen_fields)):
                    FieldRemover(dataset.chosen_fields[field])
                for merged_field in list(reversed(dataset.merged_fields)):
                    MergedFieldRemover(dataset.merged_fields[merged_field])

        def GroupedDatasetRemover(grouped_dataset):
            for dataset in list(reversed(grouped_dataset.datasets)):
                DatasetRemover(grouped_dataset.dataset[dataset])
            for merged_field in list(reversed(grouped_dataset.merged_fields)):
                MergedFieldRemover(grouped_dataset.merged_fields[merged_field])

        main_frame = self.GetGrandParent().GetTopLevelParent()
        main_frame.CreateProgressDialog(GUIText.REMOVING_FIELDS_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.REMOVING_FIELDS_BUSY_PREPARING_MSG)
            for item in self.chosen_fields_ctrl.GetSelections():
                node = self.chosen_fields_model.ItemToObject(item)
                main_frame.PulseProgressDialog(GUIText.REMOVING_FIELDS_BUSY_MSG+str(node.key))
                if isinstance(node, Datasets.Field):
                    FieldRemover(node)
                elif isinstance(node, Datasets.MergedField):
                    MergedFieldRemover(node)
                elif isinstance(node, Datasets.Dataset):
                    DatasetRemover(node)
                elif isinstance(node, Datasets.GroupedDataset):
                    GroupedDatasetRemover(node)
            if performed_flag:
                main_frame = self.GetGrandParent().GetTopLevelParent()
                self.dataset.last_changed_dt = datetime.now()
                main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
            self.GetTopLevelParent().Enable()
            self.GetTopLevelParent().SetFocus()
        logger.info("Finished")

    def OnProgress(self, event):
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(event.data)

    def OnTokenizerEnd(self, event):
        logger = logging.getLogger(__name__+".FieldsNotebook.OnAddFieldsEnd")
        logger.info("Starting")
        self.tokenization_thread = None
        self.chosen_fields_model.Cleared()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DatasetsUpdated()
        main_frame.CloseProgressDialog(thaw=True)
        main_frame.threaded_inprogress_flag == False
        self.GetTopLevelParent().Enable()
        self.GetTopLevelParent().SetFocus()
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FieldsNotebook.Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FieldsNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data
