import logging


import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB
import wx.grid

from Common.GUIText import Datasets as GUIText
import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
import Common.Notes as Notes
import Common.Objects.Datasets as Datasets
import Common.Objects.Threads.Datasets as DatasetsThreads
import Common.Objects.DataViews.Datasets as DatasetsDataViews
import Common.Database as Database
import Collection.SubModuleFields as SubModuleFields

class DataNotebook(FNB.FlatNotebook):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)

        #create dictionary to hold instances of dataset data panels for each field available
        self.dataset_data_tabs = {}

        self.menu = wx.Menu()
        self.menu_menuitem = None
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.DatasetsUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        dataset_data_tab_keys = list(self.dataset_data_tabs.keys())
        self.Freeze()
        for key in dataset_data_tab_keys:
            index = self.GetPageIndex(self.dataset_data_tabs[key])
            if index is not wx.NOT_FOUND:
                self.DeletePage(index)
            del self.dataset_data_tabs[key]
        for key in main_frame.datasets:
            main_frame.PulseProgressDialog(GUIText.REFRESHING_DATASETS_BUSY_MSG+str(key))
            if key in self.dataset_data_tabs:
                self.dataset_data_tabs[key].Update()
            else:
                if isinstance(main_frame.datasets[key], Datasets.Dataset):
                    if len(main_frame.datasets[key].data) > 0:
                        self.dataset_data_tabs[key] = DatasetDataPanel(self, main_frame.datasets[key], self.GetSize())
                        self.AddPage(self.dataset_data_tabs[key], str(key))
        self.Thaw()
        logger.info("Finished")
    
    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.DocumentsUpdated")
        logger.info("Starting")
        for key in self.dataset_data_tabs:
            self.dataset_data_tabs[key].Update()
        logger.info("Finished")

    def ShowData(self, node):
        if node.key in self.dataset_data_tabs:
            index = self.GetPageIndex(self.dataset_data_tabs[node.key])
            self.SetSelection(index)
        elif node.parent is not None:
            self.ShowData(node.parent)

    def Load(self, saved_data):
        #NOT CURRENTLY USED as dataset objects contain all that is needed
        logger = logging.getLogger(__name__+".DatasetDataNotebook.Load")
        logger.info("Starting")
        for key in saved_data["groups"]:
            self.dataset_data_tabs[key].Load(saved_data["groups"][key])
        logger.info("Finished")

    def Save(self):
        #NOT CURRENTLY USED as dataset objects contain all that is needed
        logger = logging.getLogger(__name__+".DatasetDataNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['datasets'] = {}
        saved_data["groups"] = {}
        for key in self.dataset_data_tabs:
            if isinstance(self.dataset_data_tabs[key], DatasetsDataViews.DatasetsDataGrid):
                saved_data["datasets"][key] = {} 
            if isinstance(self.dataset_data_tabs[key], DataNotebook):
                saved_data["groups"][key] = self.dataset_data_tabs[key].Save()
        logger.info("Finished")
        return saved_data

class DatasetDetailsDialog(wx.Dialog):
    def __init__(self, parent, dataset):
        logger = logging.getLogger(__name__+".DatasetDetailsDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title="", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)

        self.dataset = dataset
        self.tokenization_thread = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        if dataset.dataset_source == "Reddit":
            self.SetTitle(GUIText.RETRIEVED_REDDIT_LABEL)
        elif dataset.dataset_source == "CSV":
            self.SetTitle(GUIText.RETRIEVED_CSV_LABEL)
        dataset_panel = DatasetPanel(self, dataset)
        self.sizer.Add(dataset_panel)

        self.SetSizer(self.sizer)
        
        self.Layout()
        self.Fit()

        CustomEvents.TOKENIZER_EVT_RESULT(self, self.OnTokenizerEnd)
        logger.info("Finished")
    
    def OnChangeDatasetKey(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsDialog.OnChangeDatasetKey")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multiprocessing_inprogress_flag:
            wx.MessageBox(GUIText.MULTIPROCESSING_WARNING_MSG,
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
            return

        main_frame.CreateProgressDialog(GUIText.CHANGING_NAME_BUSY_LABEL,
                                        freeze=True)
        updated_flag = False
        tokenizing_flag = False
        try:
            main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_PREPARING_MSG)
            node = self.dataset
            if isinstance(node, Datasets.Dataset):
                new_name = self.name_ctrl.GetValue()
                
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
                        if old_key in main_frame.datasets:
                            main_frame.datasets[new_key] = main_frame.datasets[old_key]
                            del main_frame.datasets[old_key]
                        elif node.parent is not None:
                            node.parent.datasets[new_key] = node
                            del node.parent.datasets[old_key]
                        Database.DatabaseConnection(main_frame.current_workspace.name).UpdateDatasetKey(old_key, new_key)
                        main_frame.DatasetKeyChange(old_key, new_key)
                        updated_flag = True
                language_index = self.language_ctrl.GetSelection()
                if node.language != Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]:
                    main_frame.PulseProgressDialog(GUIText.CHANGING_LANGUAGE_BUSY_PREPARING_MSG)
                    node.language = Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]
                    main_frame.multiprocessing_inprogress_flag = True
                    self.tokenization_thread = DatasetsThreads.TokenizerThread(self, main_frame, node, True)
                    tokenizing_flag = True
        finally:
            if not tokenizing_flag:
                if updated_flag:
                    main_frame.DatasetsUpdated()
                main_frame.CloseProgressDialog(thaw=True)
                self.Close()
        logger.info("Finished")
    
    def OnTokenizerEnd(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsDialog.OnTokenizerEnd")
        logger.info("Starting")
        self.tokenization_thread.join()
        self.tokenization_thread = None
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DatasetsUpdated()
        main_frame.CloseProgressDialog(thaw=True)
        main_frame.multiprocessing_inprogress_flag = False
        self.Close()
        logger.info("Finished")

class DatasetPanel(wx.Panel):
    def __init__(self, parent, dataset, header=False, size=wx.DefaultSize):
        wx.Panel.__init__(self, parent, size=size)

        self.dataset = dataset

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        if header:
            details_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
            details_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        else:
            details_sizer1 = wx.BoxSizer(wx.VERTICAL)
            details_sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(details_sizer1, 0, wx.ALL, 5)
        self.sizer.Add(details_sizer2, 0, wx.ALL, 5)

        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multipledatasets_mode:
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_label = wx.StaticText(self, label=GUIText.NAME + ":")
            name_sizer.Add(name_label)
            self.name_ctrl = wx.TextCtrl(
                self, value=dataset.name, style=wx.TE_PROCESS_ENTER)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            self.name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDatasetKey)
            name_sizer.Add(self.name_ctrl)
            details_sizer1.Add(name_sizer, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details_sizer1.AddSpacer(10)

        if dataset.parent is None:
            selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(
                dataset.language)
            language_label = wx.StaticText(
                self, label=GUIText.LANGUAGE + ": ")
            self.language_ctrl = wx.Choice(
                self, choices=Constants.AVALIABLE_DATASET_LANGUAGES2)
            self.language_ctrl.Select(selected_lang)
            language_sizer = wx.BoxSizer(wx.HORIZONTAL)
            language_sizer.Add(language_label, 0, wx.ALIGN_CENTRE_VERTICAL)
            language_sizer.Add(self.language_ctrl)
            details_sizer1.Add(language_sizer, 0, wx.ALL, 5)
            details_sizer1.AddSpacer(10)
            self.language_ctrl.Bind(wx.EVT_CHOICE, self.OnChangeDatasetLanguage)
        else:
            selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(
                dataset.language)
            language_label = wx.StaticText(
                self, label=GUIText.LANGUAGE + ": " + Constants.AVALIABLE_DATASET_LANGUAGES2[selected_lang])
            details_sizer1.Add(language_label, 0, wx.ALL, 5)
            details_sizer1.AddSpacer(10)

        type_label = wx.StaticText(self, label=GUIText.TYPE + ": "
                                            + dataset.dataset_type)
        details_sizer2.Insert(0, type_label, 0, wx.ALL, 5)
        details_sizer2.InsertSpacer(1, 10)

        if dataset.dataset_source == 'Reddit':
            subreddit_label = wx.StaticText(self, label=GUIText.REDDIT_SUBREDDIT + ": "
                                            + dataset.retrieval_details['subreddit'])
            if main_frame.multipledatasets_mode:
                details_sizer2.Insert(0, subreddit_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
                details_sizer2.InsertSpacer(1, 10)
            else:
                details_sizer1.Insert(0, subreddit_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
                details_sizer1.InsertSpacer(1, 10)

            if dataset.retrieval_details['pushshift_flg']:
                if dataset.retrieval_details['replace_archive_flg']:
                    if dataset.retrieval_details['redditapi_flg']:
                        retrieveonline_label = wx.StaticText(
                            self, label=GUIText.SOURCE+": "+GUIText.REDDIT_FULL_REDDITAPI)
                    else:
                        retrieveonline_label = wx.StaticText(
                            self, label=GUIText.SOURCE+": "+GUIText.REDDIT_FULL_PUSHSHIFT)
                else:
                    if dataset.retrieval_details['redditapi_flg']:
                        retrieveonline_label = wx.StaticText(
                            self, label=GUIText.SOURCE+": "+GUIText.REDDIT_UPDATE_REDDITAPI)
                    else:
                        retrieveonline_label = wx.StaticText(
                            self, label=GUIText.SOURCE+": "+GUIText.REDDIT_UPDATE_PUSHSHIFT)
            else:
                retrieveonline_label = wx.StaticText(
                    self, label=GUIText.SOURCE+": "+GUIText.REDDIT_ARCHIVED)
            details_sizer2.Add(retrieveonline_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details_sizer2.AddSpacer(10)

            start_date_label = wx.StaticText(self, label=GUIText.START_DATE + ": "
                                             + dataset.retrieval_details['start_date'])
            details_sizer2.Add(start_date_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details_sizer2.AddSpacer(10)

            end_date_label = wx.StaticText(self, label=GUIText.END_DATE + ": "
                                           + dataset.retrieval_details['end_date'])
            details_sizer2.Add(end_date_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details_sizer2.AddSpacer(10)

        retrieved_date_label = wx.StaticText(self, label=GUIText.RETRIEVED_ON + ": "
                                             + dataset.created_dt.strftime("%Y-%m-%d, %H:%M:%S"))
        details_sizer2.Add(retrieved_date_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details_sizer2.AddSpacer(10)
        document_num_label = wx.StaticText(
            self, label=GUIText.DOCUMENT_NUM+": " + str(len(self.dataset.data)))
        details_sizer2.Add(document_num_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details_sizer2.AddSpacer(10)

        if dataset.dataset_source == 'Twitter':
            if dataset.retrieval_details['query']:
                query_label = wx.StaticText(self, label=GUIText.QUERY + ": " + dataset.retrieval_details['query'])
                details_sizer2.Add(query_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)

        customizemetdata_ctrl = wx.Button(self, label=GUIText.CUSTOMIZE_METADATAFIELDS)
        customizemetdata_ctrl.Bind(wx.EVT_BUTTON, self.OnCustomizeMetadataFields)
        details_sizer1.Add(customizemetdata_ctrl, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details_sizer1.AddSpacer(10)
        
        customizeincluded_ctrl = wx.Button(self, label=GUIText.CUSTOMIZE_INCLUDEDFIELDS)
        customizeincluded_ctrl.Bind(wx.EVT_BUTTON, self.OnCustomizeIncludedFields)
        details_sizer1.Add(customizeincluded_ctrl, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details_sizer1.AddSpacer(10)

        self.SetSizer(self.sizer)
        self.Layout()

        CustomEvents.TOKENIZER_EVT_RESULT(self, self.OnTokenizerEnd)

    def OnCustomizeMetadataFields(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnCustomizeMetadataFields")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        SubModuleFields.FieldsDialog(parent=main_frame,
                                     title=str(self.dataset.key)+" "+GUIText.CUSTOMIZE_METADATAFIELDS,
                                     dataset=self.dataset,
                                     fields=self.dataset.metadata_fields,
                                     metadata_fields=True).Show()
        logger.info("Finished")

    def OnCustomizeIncludedFields(self, event):
        logger = logging.getLogger(__name__+".DatasetsPanel.OnCustomizeIncludedFields")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        SubModuleFields.FieldsDialog(parent=main_frame,
                                     title=str(self.dataset.key)+" "+GUIText.CUSTOMIZE_INCLUDEDFIELDS,
                                     dataset=self.dataset,
                                     fields=self.dataset.included_fields).Show()
        logger.info("Finished")

    def OnChangeDatasetKey(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnChangeDatasetKey")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.CHANGING_NAME_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_PREPARING_MSG)
            node = self.dataset
            if isinstance(node, Datasets.Dataset):
                new_name = self.name_ctrl.GetValue()
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
                        if old_key in main_frame.datasets:
                            main_frame.datasets[new_key] = main_frame.datasets[old_key]
                            del main_frame.datasets[old_key]
                        elif node.parent is not None:
                            node.parent.datasets[new_key] = node
                            del node.parent.datasets[old_key]
                        Database.DatabaseConnection(main_frame.current_workspace.name).UpdateDatasetKey(old_key, new_key)
                        main_frame.DatasetKeyChange(old_key, new_key)
                        main_frame.DatasetsUpdated()
        finally:
            main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")
    
    def OnChangeDatasetLanguage(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnChangeDatasetLanguage")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multiprocessing_inprogress_flag:
            wx.MessageBox(GUIText.MULTIPROCESSING_WARNING_MSG,
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
            return
        node = self.dataset
        language_index = self.language_ctrl.GetSelection()
        if node.language != Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]:
            main_frame.CreateProgressDialog(GUIText.CHANGING_LANGUAGE_BUSY_LABEL, freeze=True)
            main_frame.PulseProgressDialog(GUIText.CHANGING_LANGUAGE_BUSY_PREPARING_MSG)
            node.language = Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]
            main_frame.multiprocessing_inprogress_flag = True
            self.tokenization_thread = DatasetsThreads.TokenizerThread(self, main_frame, node, rerun=True)
        logger.info("Finished")

        
    def OnTokenizerEnd(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsDialog.OnTokenizerEnd")
        logger.info("Starting")
        self.tokenization_thread.join()
        self.tokenization_thread = None
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DatasetsUpdated()
        main_frame.CloseProgressDialog(thaw=True)
        main_frame.multiprocessing_inprogress_flag = False
        logger.info("Finished")

class DatasetDataPanel(wx.Panel):
    def __init__(self, parent, dataset, size=wx.DefaultSize):
        wx.Panel.__init__(self, parent=parent, size=size)
        self.dataset = dataset

        sizer = wx.BoxSizer(orient=wx.VERTICAL)

        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.search_ctrl = wx.SearchCtrl(self)
        self.search_ctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.search_ctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.search_ctrl.SetDescriptiveText(GUIText.SEARCH)
        self.search_ctrl.ShowCancelButton(True)
        controls_sizer.Add(self.search_ctrl, 0, wx.ALL, 5)
        self.search_count_text = wx.StaticText(self)
        controls_sizer.Add(self.search_count_text, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer.Add(controls_sizer, 0, wx.ALL, 5)

        self.datasetdata_grid = DatasetsDataViews.DatasetsDataGrid(self, dataset, self.GetSize())
        sizer.Add(self.datasetdata_grid)

        self.SetSizer(sizer)
    
    def OnSearch(self, event):
        logger = logging.getLogger(__name__+".DatasetDataPanel.OnSearch")
        logger.info("Starting")
        search_ctrl = event.GetEventObject()
        search_value = search_ctrl.GetValue()
        self.datasetdata_grid.Search(search_value)
        self.search_count_text.SetLabel(GUIText.SEARCH_COUNT_LABEL+str(len(self.datasetdata_grid.gridtable.data_df)))
        logger.info("Finished")

    def OnSearchCancel(self, event):
        logger = logging.getLogger(__name__+".DatasetDataPanel.OnSearchCancel")
        logger.info("Starting")
        search_ctrl = event.GetEventObject()
        search_ctrl.SetValue("")
        self.OnSearch(event)
        self.search_count_text.SetLabel("")
        logger.info("Finished")
