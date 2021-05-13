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
import Common.Objects.DataViews.Codes as CodesDataViews

class DataNotebook(FNB.FlatNotebook):
    def __init__(self, parent, grouped_dataset=None, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)
        self.dataset = grouped_dataset

        #create dictionary to hold instances of dataset data panels for each field avaliable
        self.dataset_data_tabs = {}

        self.menu = wx.Menu()
        self.menu_menuitem = None
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.DatasetsUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        dataset_data_tab_keys = list(self.dataset_data_tabs.keys())
        
        for key in dataset_data_tab_keys:
            index = self.GetPageIndex(self.dataset_data_tabs[key])
            if index is not wx.NOT_FOUND:
                self.DeletePage(index)
            del self.dataset_data_tabs[key]
        if self.dataset != None:
            current_parent = self.dataset
        else:
            current_parent = main_frame
        for key in current_parent.datasets:
            main_frame.PulseProgressDialog(GUIText.REFRESHING_DATASETS_BUSY_MSG+str(key))
            if key in self.dataset_data_tabs:
                self.dataset_data_tabs[key].Update()
            else:
                if isinstance(current_parent.datasets[key], Datasets.Dataset):
                    if len(current_parent.datasets[key].data) > 0:
                        self.dataset_data_tabs[key] = DatasetsDataViews.DatasetsDataGrid(self, current_parent.datasets[key], self.GetSize())
                        self.AddPage(self.dataset_data_tabs[key], str(key))
                elif isinstance(current_parent.datasets[key], Datasets.GroupedDataset):
                    self.dataset_data_tabs[key] = DataNotebook(self, grouped_dataset=current_parent.datasets[key], size=self.GetSize())
                    self.dataset_data_tabs[key].DatasetsUpdated()
                    self.AddPage(self.dataset_data_tabs[key], str(key))
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

        if isinstance(dataset, Datasets.GroupedDataset):
            self.SetTitle(GUIText.GROUPED_DATASET_LABEL)

            name_label = wx.StaticText(self, label=GUIText.NAME + ":")
            self.name_ctrl = wx.TextCtrl(self, value=self.dataset.name, style=wx.TE_PROCESS_ENTER)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            self.name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDatasetKey)
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_sizer.Add(name_label)
            name_sizer.Add(self.name_ctrl)
            self.sizer.Add(name_sizer, 0, wx.ALL, 5)

            created_date_label = wx.StaticText(self, label=GUIText.CREATED_ON + ": "
                                               +self.dataset.created_dt.strftime("%Y-%m-%d, %H:%M:%S"))
            self.sizer.Add(created_date_label, 0, wx.ALL, 5)

            selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(dataset.language)
            language_label = wx.StaticText(self, label=GUIText.LANGUAGE + ": ")
            self.language_ctrl = wx.Choice(self, choices=Constants.AVALIABLE_DATASET_LANGUAGES2)
            self.language_ctrl.Select(selected_lang)
            language_sizer = wx.BoxSizer(wx.HORIZONTAL)
            language_sizer.Add(language_label)
            language_sizer.Add(self.language_ctrl)
            self.sizer.Add(language_sizer, 0, wx.ALL, 5)

        elif isinstance(dataset, Datasets.Dataset):
            if dataset.dataset_source == "Reddit":
                self.SetTitle(GUIText.RETRIEVED_REDDIT_LABEL)
            elif dataset.dataset_source == "CSV":
                self.SetTitle(GUIText.RETRIEVED_CSV_LABEL)
            dataset_panel = DatasetPanel(self, dataset)
            self.sizer.Add(dataset_panel)

        self.SetSizer(self.sizer)
        
        self.Layout()
        self.Fit()

        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
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
            if isinstance(node, Datasets.Dataset) or isinstance(node, Datasets.GroupedDataset):
                new_name = self.name_ctrl.GetValue()
                
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
                            updated_flag = True
                language_index = self.language_ctrl.GetSelection()
                if node.language != Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]:
                    main_frame.PulseProgressDialog(GUIText.CHANGING_LANGUAGE_BUSY_PREPARING_MSG)
                    node.language = Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]
                    main_frame.multiprocessing_inprogress_flag = True
                    self.tokenization_thread = DatasetsThreads.TokenizerThread(self, main_frame, [node])
                    tokenizing_flag = True
        finally:
            if not tokenizing_flag:
                if updated_flag:
                    main_frame.DatasetsUpdated()
                main_frame.CloseProgressDialog(thaw=True)
                self.Close()
        logger.info("Finished")
    
    def OnProgress(self, event):
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(event.data)

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
            details_sizer1.Add(name_sizer, 0, wx.ALL, 5)
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
            language_sizer.Add(language_label)
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
                details_sizer2.Insert(0, subreddit_label, 0, wx.ALL, 5)
                details_sizer2.InsertSpacer(1, 10)
            else:
                details_sizer1.Insert(0, subreddit_label, 0, wx.ALL, 5)
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
            details_sizer2.Add(retrieveonline_label, 0, wx.ALL, 5)
            details_sizer2.AddSpacer(10)

            start_date_label = wx.StaticText(self, label=GUIText.START_DATE + ": "
                                             + dataset.retrieval_details['start_date'])
            details_sizer2.Add(start_date_label, 0, wx.ALL, 5)
            details_sizer2.AddSpacer(10)

            end_date_label = wx.StaticText(self, label=GUIText.END_DATE + ": "
                                           + dataset.retrieval_details['end_date'])
            details_sizer2.Add(end_date_label, 0, wx.ALL, 5)
            details_sizer2.AddSpacer(10)

        #TODO add metadata details
        #elif dataset.dataset_source == 'CSV':

        retrieved_date_label = wx.StaticText(self, label=GUIText.RETRIEVED_ON + ": "
                                             + dataset.created_dt.strftime("%Y-%m-%d, %H:%M:%S"))
        details_sizer2.Add(retrieved_date_label, 0, wx.ALL, 5)
        details_sizer2.AddSpacer(10)
        document_num_label = wx.StaticText(
            self, label=GUIText.DOCUMENT_NUM+": " + str(len(self.dataset.data)))
        details_sizer2.Add(document_num_label, 0, wx.ALL, 5)

        self.SetSizer(self.sizer)
        self.Layout()

    def OnChangeDatasetKey(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsPanel.OnChangeDatasetKey")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.CHANGING_NAME_BUSY_LABEL,
                                        freeze=True)
        try:
            main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_PREPARING_MSG)
            node = self.dataset
            if isinstance(node, Datasets.Dataset) or isinstance(node, Datasets.GroupedDataset):
                new_name = self.name_ctrl.GetValue()
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
            self.tokenization_thread = DatasetsThreads.TokenizerThread(self, main_frame, [node])
        logger.info("Finished")

class DocumentDialog(wx.Dialog):
    def __init__(self, parent, node, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DocumentDialog["+str(node.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(node.key), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer()
        self.document_panel = DocumentPanel(self, node, size=self.GetSize())
        sizer.Add(self.document_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.info("Finished")

class DocumentPanel(wx.Panel):
    def __init__(self, parent, node, size):
        wx.Panel.__init__(self, parent, size=size)

        self.node = node

        label_font = wx.Font(Constants.LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, Constants.LABEL_UNDERLINE)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(frame_sizer)

        frame_splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        frame_sizer.Add(frame_splitter, 1, wx.EXPAND)

        top_frame_splitter = wx.SplitterWindow(frame_splitter, style=wx.SP_BORDER)

        data_panel = wx.ScrolledWindow(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)
        data_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        url = wx.adv.HyperlinkCtrl(data_panel, url=node.url, style=wx.ALIGN_LEFT)
        data_panel_sizer.Add(url, 0, wx.ALL, 5)

        field_ctrl = wx.TextCtrl(data_panel, value="", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.BORDER_NONE)
        data_panel_sizer.Add(field_ctrl, 1, wx.EXPAND, 5)
        for field in node.data_dict:
            #field_ctrl.AppendText(str(field)+"\n")
            #field_label.Wrap(self.GetSizer().GetWidth())
            #field_label.SetFont(label_font)
            #data_panel_sizer.Add(field_label, 0, wx.ALL, 5)
            if isinstance(node.data_dict[field], list):
                for entry in node.data_dict[field]:
                    field_ctrl.AppendText(str(entry)+'\n------------\n')
                    #field_value = infobar.AutoWrapStaticText(data_panel, label=str(entry)+'\n------------')
                    #field_value.Wrap(self.GetSizer().GetWidth())
                    #data_panel_sizer.Add(field_value, 0, wx.ALL, 5)
            else:
                field_ctrl.AppendText(str(node.data_dict[field])+'\n------------\n')
                #field_value = infobar.AutoWrapStaticText(data_panel, label=str(node.data_dict[field]))
                #field_value.Wrap(self.GetSizer().GetWidth())
                #data_panel_sizer.Add(field_value, 0, wx.ALL, 5)
        data_panel.SetSizer(data_panel_sizer)

        codes_panel = wx.Panel(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        codes_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        main_frame = wx.GetApp().GetTopWindow()
        self.codes_model = CodesDataViews.ObjectCodesViewModel(main_frame.codes, self.node)
        self.codes_ctrl = CodesDataViews.CodesViewCtrl(codes_panel, self.codes_model)
        codes_panel_sizer.Add(self.codes_ctrl, 1, wx.EXPAND, 5)
        codes_panel.SetSizer(codes_panel_sizer)

        edit_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        edit_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        usefulness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        usefulness_label = wx.StaticText(edit_panel, label="Usefullness: ", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALL, 5)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=["Unsure", "Useful", "Not Useful"], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl, 0, wx.ALL, 5)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.node.usefulness_flag == None:
            self.usefulness_ctrl.Select(0)
        elif self.node.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.node.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer)
        
        #notes_label = wx.StaticText(edit_panel, label="Notes", style=wx.ALIGN_LEFT)
        #notes_label.SetFont(label_font)
        #edit_panel_sizer.Add(notes_label, 0, wx.ALL, 5)
        #self.notes_ctrl = wx.TextCtrl(edit_panel, value=node.notes, style=wx.TE_LEFT|wx.TE_MULTILINE)
        #self.notes_ctrl.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        #edit_panel_sizer.Add(self.notes_ctrl, 1, wx.EXPAND, 5)
        self.notes_panel = Notes.NotesPanel(edit_panel)
        self.notes_panel.SetNote(node.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        edit_panel_sizer.Add(self.notes_panel, 1, wx.EXPAND, 5)
        
        edit_panel.SetSizer(edit_panel_sizer)

        top_frame_splitter.SetMinimumPaneSize(20)
        top_frame_splitter.SplitVertically(data_panel, codes_panel)
        top_frame_splitter.SetSashPosition(int(self.GetSize().GetWidth()/2))

        frame_splitter.SetMinimumPaneSize(20)
        frame_splitter.SplitHorizontally(top_frame_splitter, edit_panel)
        frame_splitter.SetSashPosition(int(self.GetSize().GetHeight()/2))



        #initialize scrolling
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        data_panel.SetScrollRate(fontsz.x, fontsz.y)
        data_panel.EnableScrolling(True, True)

        self.Layout()
    
    def OnUpdateUsefulness(self, event):
        choice = self.usefulness_ctrl.GetSelection()
        if choice == 0:
            self.node.usefulness_flag = None
        elif choice == 1:
            self.node.usefulness_flag = True
        elif choice == 2:
            self.node.usefulness_flag = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()

    def OnUpdateNotes(self, event):
        self.node.notes = self.notes_panel.GetNote()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()
    
    def DocumentUpdated(self):
        codes_model = self.codes_ctrl.GetModel()
        codes_model.Cleared()
        self.notes_panel.Unbind(wx.EVT_TEXT)
        self.notes_panel.SetNote(self.node.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)

class DocumentListPanel(wx.Panel):
    def __init__(self, parent, dataset_key):
        logger = logging.getLogger(__name__+".DocumentListPanel["+str(dataset_key)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)

        sizer = wx.BoxSizer(wx.VERTICAL)

        controls_sizer = wx.BoxSizer()

        #TODO add text to GUIText
        actions_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.ACTIONS)
        actions_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        notsure_tool = actions_toolbar.AddTool(wx.ID_ANY, label="Not Sure", bitmap=wx.Bitmap(1, 1),
                                      shortHelp="Flags selected entries usefulness as not sure")
        actions_toolbar.Bind(wx.EVT_MENU, self.OnNotSure, notsure_tool)
        useful_tool = actions_toolbar.AddTool(wx.ID_ANY, label="Useful", bitmap=wx.Bitmap(1, 1),
                                      shortHelp="Flags selected entries usefulness as useful")
        actions_toolbar.Bind(wx.EVT_MENU, self.OnUseful, useful_tool)
        notuseful_tool = actions_toolbar.AddTool(wx.ID_ANY, label="Not Useful", bitmap=wx.Bitmap(1, 1),
                                         shortHelp="Flags selected entries usefulness as not useful")
        actions_toolbar.Bind(wx.EVT_MENU, self.OnNotUseful, notuseful_tool)
        actions_toolbar.Realize()
        actions_sizer.Add(actions_toolbar)
        controls_sizer.Add(actions_sizer, 0, wx.ALL, 5)

        #TODO add text to GUIText
        view_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.VIEW)
        view_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        self.notsure_toggle = view_toolbar.AddTool(wx.ID_ANY, label="Show Not Sure", bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_CHECK)
        view_toolbar.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.notsure_toggle)
        self.useful_toggle = view_toolbar.AddTool(wx.ID_ANY, label="Show Useful", bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_CHECK)
        view_toolbar.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.useful_toggle)
        self.notuseful_toggle = view_toolbar.AddTool(wx.ID_ANY, label="Show Not Useful", bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_CHECK)
        view_toolbar.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.notuseful_toggle)
        view_toolbar.Realize()
        view_sizer.Add(view_toolbar)
        controls_sizer.Add(view_sizer, 0, wx.ALL, 5)

        sizer.Add(controls_sizer, 0, wx.ALL, 5)
        
        #single dataset mode
        main_frame = wx.GetApp().GetTopWindow()
        self.documents_model = DatasetsDataViews.DocumentViewModel(main_frame.datasets[dataset_key])
        self.documents_ctrl = DatasetsDataViews.DocumentViewCtrl(self, self.documents_model)
        self.documents_model.Cleared()

        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
        columns = self.documents_ctrl.GetColumns()
        for column in reversed(columns):
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        sizer.Add(self.documents_ctrl, 1, wx.EXPAND)

        self.SetSizer(sizer)

        logger.info("Finished")
    
    def OnNotSure(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotSure")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = None
                self.documents_model.ItemChanged(item)
        logger.info("Finished")

    def OnUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = True
                self.documents_model.ItemChanged(item)
        logger.info("Finished")

    def OnNotUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = False
                self.documents_model.ItemChanged(item)
        logger.info("Finished")
    
    def OnToggleShowUsefulness(self, event):

        notsure_toggled = self.notsure_toggle.IsToggled()
        if not notsure_toggled:
            if None in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(None)
        elif notsure_toggled:
            if None not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(None)
        
        useful_toggled = self.useful_toggle.IsToggled()
        if not useful_toggled:
            if True in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(True)
        elif useful_toggled:
            if True not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(True)
        
        notuseful_toggled = self.notuseful_toggle.IsToggled()
        if not notuseful_toggled:
            if False in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(False)
        elif notuseful_toggled:
            if False not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(False)
        self.documents_model.Cleared()
        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
            subchildren = []
            self.documents_model.GetChildren(child, subchildren)
            for subchild in subchildren:
                self.documents_ctrl.Expand(subchild)
            

    def DatasetsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".DocumentListPanel.DatasetsUpdated")
        logger.info("Starting")
        self.documents_ctrl.UpdateColumns()
        self.documents_model.Cleared()
        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
            subchildren = []
            self.documents_model.GetChildren(child, subchildren)
            for subchild in subchildren:
                self.documents_ctrl.Expand(subchild)
        logger.info("Finished")

    def DocumentsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".DocumentListPanel.DocumentsUpdated")
        logger.info("Starting")
        self.documents_model.Cleared()
        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
            subchildren = []
            self.documents_model.GetChildren(child, subchildren)
            for subchild in subchildren:
                self.documents_ctrl.Expand(subchild)
        logger.info("Finished")

    #Module Control commands
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".DocumentListPanel.Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".DocumentListPanel.Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data
