import logging
import copy
from datetime import datetime
from sys import setprofile

import pandas as pd

import wx
import wx.adv
import wx.dataview as dv
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB

from Common.GUIText import Filtering, Samples as GUIText
from Common.GUIText import Filtering as FilteringGUIText
from Common.CustomPlots import ChordPlotPanel#, pyLDAvisPanel, TreemapPlotPlanel, NetworkPlotPlanel
import Common.Constants as Constants
import Common.Database as Database
import Common.CustomEvents as CustomEvents
import Common.Objects.DataViews.Datasets as DatasetsDataViews
import Common.Objects.Threads.Datasets as DatasetsThreads
import Common.Objects.Samples as Samples
import Common.Objects.Threads.Samples as SamplesThreads
import Common.Objects.DataViews.Samples as SamplesDataViews

class SampleCreatePanel(wx.Panel):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".SampleCreatePanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)
        
        self.capture_thread = None

        label_font = wx.Font(Constants.LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, underline=Constants.LABEL_UNDERLINE)

        sizer = wx.BoxSizer(wx.VERTICAL)
        generic_label_box = wx.StaticBox(self, label=GUIText.GENERIC_SECTION_LABEL)
        generic_label_box.SetFont(label_font)
        generic_sizer = wx.StaticBoxSizer(generic_label_box, orient=wx.VERTICAL)
        sizer.Add(generic_sizer, 0, wx.ALL, 5)
        create_random_sizer = wx.BoxSizer(wx.HORIZONTAL)
        generic_sizer.Add(create_random_sizer)
        create_random_button = wx.Button(self, label=GUIText.RANDOM_LABEL)
        create_random_button.SetToolTip(GUIText.CREATE_RANDOM_TOOLTIP)
        self.Bind(wx.EVT_BUTTON, lambda event: self.OnStartCreateSample(event, 'Random'), create_random_button)
        create_random_sizer.Add(create_random_button, 0, wx.ALL, 5)
        create_random_description = wx.StaticText(self, label=GUIText.RANDOM_DESC)
        create_random_sizer.Add(create_random_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        create_random_link = wx.adv.HyperlinkCtrl(self, label="1", url=GUIText.RANDOM_URL)
        create_random_sizer.Add(create_random_link, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)

        
        topicmodel_label_box = wx.StaticBox(self, label=GUIText.TOPICMODEL_SECTION_LABEL)
        topicmodel_label_box.SetFont(label_font)
        topicmodel_sizer = wx.StaticBoxSizer(topicmodel_label_box, orient=wx.VERTICAL)
        sizer.Add(topicmodel_sizer, 0, wx.ALL, 5)
        description_sizer = wx.BoxSizer(wx.HORIZONTAL)
        topicmodel_sizer.Add(description_sizer, 0, wx.ALL, 5)
        topicmodelling_description = wx.StaticText(self, label=GUIText.TOPICMODEL_SECTION_DESC)
        description_sizer.Add(topicmodelling_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        #TODO choose approriate reference/s
        #topicmodelling_link = wx.adv.HyperlinkCtrl(self, label="", url=GUIText.TOPICMODEL_SECTION_LINK)
        #description_sizer.Add(topicmodelling_link, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        create_lda_sizer = wx.BoxSizer(wx.HORIZONTAL)
        topicmodel_sizer.Add(create_lda_sizer)
        create_lda_button = wx.Button(self, label=GUIText.LDA_LABEL)
        create_lda_button.SetToolTip(GUIText.CREATE_LDA_TOOLTIP)
        self.Bind(wx.EVT_BUTTON, lambda event: self.OnStartCreateSample(event, 'LDA'), create_lda_button)
        create_lda_sizer.Add(create_lda_button, 0, wx.ALL, 5)
        create_lda_description = wx.StaticText(self, label=GUIText.LDA_DESC)
        create_lda_sizer.Add(create_lda_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        create_lda_link = wx.adv.HyperlinkCtrl(self, label="2", url=GUIText.LDA_URL)
        create_lda_sizer.Add(create_lda_link, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        create_biterm_sizer = wx.BoxSizer(wx.HORIZONTAL)
        topicmodel_sizer.Add(create_biterm_sizer)
        create_biterm_button = wx.Button(self, label=GUIText.BITERM_LABEL)
        create_biterm_button.SetToolTip(GUIText.CREATE_BITERM_TOOLTIP)
        self.Bind(wx.EVT_BUTTON, lambda event: self.OnStartCreateSample(event, 'Biterm'), create_biterm_button)
        create_biterm_sizer.Add(create_biterm_button, 0, wx.ALL, 5)
        create_biterm_description = wx.StaticText(self, label=GUIText.BITERM_DESC)
        create_biterm_sizer.Add(create_biterm_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        create_biterm_link = wx.adv.HyperlinkCtrl(self, label="3", url=GUIText.BITERM_URL)
        create_biterm_sizer.Add(create_biterm_link, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        create_nmf_sizer = wx.BoxSizer(wx.HORIZONTAL)
        topicmodel_sizer.Add(create_nmf_sizer)
        create_nmf_button = wx.Button(self, label=GUIText.NMF_LABEL)
        create_nmf_button.SetToolTip(GUIText.CREATE_NMF_TOOLTIP)
        self.Bind(wx.EVT_BUTTON, lambda event: self.OnStartCreateSample(event, 'NMF'), create_nmf_button)
        create_nmf_sizer.Add(create_nmf_button, 0, wx.ALL, 5)
        #TODO: check description is ok
        create_nmf_description = wx.StaticText(self, label=GUIText.NMF_DESC)
        create_nmf_sizer.Add(create_nmf_description, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        #TODO: check URL is ok
        create_nmf_link = wx.adv.HyperlinkCtrl(self, label="4", url=GUIText.NMF_URL) 
        create_nmf_sizer.Add(create_nmf_link, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)

        
        #actions for different gui element's triggers
        CustomEvents.CAPTURE_EVT_RESULT(self, self.OnFinishCreateSample)

        self.SetSizer(sizer)
        self.Layout()
        logger.info("Finished")
    
    def OnStartCreateSample(self, event, model_type):
        logger = logging.getLogger(__name__+".SampleCreatePanel.OnStartCreateSample")
        logger.info("Starting")
        parent_notebook = self.GetParent()
        main_frame = wx.GetApp().GetTopWindow()
                    
        new_sample = None
        self.Freeze()
        main_frame.CreateProgressDialog(GUIText.GENERATING_DEFAULT_LABEL,
                                        warning=GUIText.GENERATE_WARNING+"\n"+GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        main_frame.PulseProgressDialog(GUIText.GENERATING_DEFAULT_MSG)
        if main_frame.multiprocessing_inprogress_flag:
            wx.MessageBox(GUIText.MULTIPROCESSING_WARNING_MSG,
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
            main_frame.CloseProgressDialog(message=GUIText.CANCELED, thaw=False)
            self.Thaw()
        elif model_type == 'Random':
            with RandomModelCreateDialog(self) as create_dialog:
                if create_dialog.ShowModal() == wx.ID_OK:
                    model_parameters = create_dialog.model_parameters
                    name = model_parameters['name']
                    main_frame.PulseProgressDialog(GUIText.GENERATING_RANDOM_SUBLABEL+str(name))
                    dataset_key = model_parameters['dataset_key']
                    dataset = main_frame.datasets[dataset_key]
                    model_parameters['document_keys'] = list(dataset.data.keys())
                    new_sample = Samples.RandomSample(name, dataset_key, model_parameters)
                    new_sample.Generate(dataset)
                    new_sample_panel = RandomSamplePanel(parent_notebook, new_sample, dataset, self.GetParent().GetSize())
                    main_frame.samples[new_sample.key] = new_sample
                    parent_notebook.InsertPage(len(parent_notebook.sample_panels), new_sample_panel, new_sample.key, select=True)
                    parent_notebook.sample_panels[new_sample.key] = new_sample_panel
                    main_frame.DocumentsUpdated()
                    main_frame.CloseProgressDialog(thaw=False)
                else:
                    main_frame.CloseProgressDialog(message=GUIText.CANCELED, thaw=False)
                self.Thaw()
        elif model_type == 'LDA':
            main_frame.multiprocessing_inprogress_flag = True
            with LDAModelCreateDialog(self) as create_dialog:
                if create_dialog.ShowModal() == wx.ID_OK:
                    model_parameters = create_dialog.model_parameters
                    name = model_parameters['name']
                    main_frame.PulseProgressDialog(GUIText.GENERATING_LDA_SUBLABEL+str(name))
                    self.capture_thread = SamplesThreads.CaptureThread(self,
                                                                        main_frame,
                                                                        model_parameters,
                                                                        model_type)
                else:
                    main_frame.CloseProgressDialog(message=GUIText.CANCELED, thaw=False)
                    main_frame.multiprocessing_inprogress_flag = False
                    self.Thaw()
        elif model_type == 'Biterm':
            with BitermModelCreateDialog(self) as create_dialog:
                if create_dialog.ShowModal() == wx.ID_OK:
                    model_parameters = create_dialog.model_parameters
                    name = model_parameters['name']
                    main_frame.PulseProgressDialog(GUIText.GENERATING_BITERM_SUBLABEL+str(name))
                    self.capture_thread = SamplesThreads.CaptureThread(self,
                                                                        main_frame,
                                                                        model_parameters,
                                                                        model_type)
                else:
                    main_frame.CloseProgressDialog(message=GUIText.CANCELED, thaw=False)
                    self.Thaw()
        elif model_type == 'NMF':
            with NMFModelCreateDialog(self) as create_dialog:
                if create_dialog.ShowModal() == wx.ID_OK:
                    model_parameters = create_dialog.model_parameters
                    name = model_parameters['name']
                    main_frame.PulseProgressDialog(GUIText.GENERATING_NMF_SUBLABEL+str(name))
                    self.capture_thread = SamplesThreads.CaptureThread(self,
                                                                        main_frame,
                                                                        model_parameters,
                                                                        model_type)
                else:
                    main_frame.CloseProgressDialog(message=GUIText.CANCELED, thaw=False)
                    self.Thaw()
        else:
            main_frame.PulseProgressDialog(GUIText.TYPE_UNKNOWN_ERROR)
            main_frame.CloseProgressDialog(thaw=False)
            self.Thaw()
        logger.info("Finished")

    def OnFinishCreateSample(self, event):
        logger = logging.getLogger(__name__+".SampleCreatePanel.OnFinishSample")
        logger.info("Starting")
        parent_notebook = self.GetParent()
        main_frame = wx.GetApp().GetTopWindow()

        self.capture_thread.join()
        self.capture_thread = None

        model_type = event.model_type
        model_parameters = event.model_parameters
        name = model_parameters['name']
        dataset_key = model_parameters['dataset_key']
        dataset = main_frame.datasets[dataset_key]
        fields_list = event.field_list
        
        if model_type == 'LDA':
            main_frame.PulseProgressDialog(GUIText.GENERATING_LDA_MSG2)
            new_sample = Samples.LDASample(name, dataset_key, model_parameters)
            new_sample.fields_list = fields_list
            new_sample.applied_filter_rules = copy.deepcopy(dataset.filter_rules)
            new_sample.tokenization_choice = dataset.tokenization_choice
            new_sample.tokenization_package_versions = dataset.tokenization_package_versions
            new_sample_panel = TopicSamplePanel(parent_notebook, new_sample, dataset, self.GetParent().GetSize())  
            main_frame.samples[new_sample.key] = new_sample
            new_sample.GenerateStart(new_sample_panel, main_frame.current_workspace.name)
            main_frame.PulseProgressDialog(GUIText.GENERATING_LDA_MSG3)
            parent_notebook.InsertPage(len(parent_notebook.sample_panels), new_sample_panel, new_sample.key, select=True)
            parent_notebook.sample_panels[new_sample.key] = new_sample_panel
            main_frame.CloseProgressDialog(message=GUIText.GENERATED_LDA_COMPLETED_PART1,
                                            thaw=False)
            self.Thaw()
        elif model_type == 'Biterm':
            main_frame.PulseProgressDialog(GUIText.GENERATING_BITERM_MSG2)
            new_sample = Samples.BitermSample(name, dataset_key, model_parameters)
            new_sample.fields_list = fields_list
            new_sample.applied_filter_rules = copy.deepcopy(dataset.filter_rules)
            new_sample.tokenization_choice = dataset.tokenization_choice
            new_sample.tokenization_package_versions = dataset.tokenization_package_versions
            new_sample_panel = TopicSamplePanel(parent_notebook, new_sample, dataset, self.GetParent().GetSize())  
            main_frame.samples[new_sample.key] = new_sample
            new_sample.GenerateStart(new_sample_panel, main_frame.current_workspace.name)
            main_frame.PulseProgressDialog(GUIText.GENERATING_BITERM_MSG3)
            parent_notebook.InsertPage(len(parent_notebook.sample_panels), new_sample_panel, new_sample.key, select=True)
            parent_notebook.sample_panels[new_sample.key] = new_sample_panel
            main_frame.CloseProgressDialog(message=GUIText.GENERATED_BITERM_COMPLETED_PART1,
                                            thaw=False)
            self.Thaw()
        elif model_type == 'NMF':
            main_frame.PulseProgressDialog(GUIText.GENERATING_NMF_MSG2)
            new_sample = Samples.NMFSample(name, dataset_key, model_parameters)
            new_sample.fields_list = fields_list
            new_sample.applied_filter_rules = copy.deepcopy(dataset.filter_rules)
            new_sample.tokenization_choice = dataset.tokenization_choice
            new_sample.tokenization_package_versions = dataset.tokenization_package_versions
            new_sample_panel = TopicSamplePanel(parent_notebook, new_sample, dataset, self.GetParent().GetSize())  
            main_frame.samples[new_sample.key] = new_sample
            new_sample.GenerateStart(new_sample_panel, main_frame.current_workspace.name)
            main_frame.PulseProgressDialog(GUIText.GENERATING_NMF_MSG3)
            parent_notebook.InsertPage(len(parent_notebook.sample_panels), new_sample_panel, new_sample.key, select=True)
            parent_notebook.sample_panels[new_sample.key] = new_sample_panel
            main_frame.CloseProgressDialog(message=GUIText.GENERATED_NMF_COMPLETED_PART1,
                                            thaw=False)
            self.Thaw()
        logger.info("Finished")

class AbstractSamplePanel(wx.Panel):
    '''general class for features all model panels should have'''
    def __init__(self, parent, sample, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".AbstractSamplePanel["+sample.key+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)
        self.sample = sample
        self.dataset = dataset

        self.parts_panel = None

        self.menu = wx.Menu()
        self.menu_menuitem = None
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".AbstractSamplePanel["+self.sample.key+"].DatasetsUpdated")
        logger.info("Starting")
        self.Freeze()
        if self.parts_panel != None:
            self.parts_panel.DatasetsUpdated()
        self.Thaw()
        logger.info("Finished")

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".AbstractSamplePanel["+self.sample.key+"].DocumentsUpdated")
        logger.info("Starting")
        if self.parts_panel != None:
            self.parts_panel.DocumentsUpdated()
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".AbstractSamplePanel["+self.sample.key+"].Load")
        logger.error("function missing")

    def Save(self):
        logger = logging.getLogger(__name__+".AbstractSamplePanel["+self.sample.key+"].Save")
        logger.error("function missing")
        return {}

class PartPanel(wx.Panel):
    def __init__(self, parent, sample, dataset, parts={}):
        logger = logging.getLogger(__name__+".PartPanel["+str(sample.key)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)

        self.sample = sample
        self.dataset = dataset
        self.parts = {}
        self.parts.update(parts)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        controls_sizer = wx.BoxSizer()
        sample_label = wx.StaticText(self, label=GUIText.SAMPLE_REQUEST)
        controls_sizer.Add(sample_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.sample_num = wx.SpinCtrl(self, min=1, max=100, initial=10)
        self.sample_num.Bind(wx.EVT_SPINCTRL, self.OnChangeDocumentNumber)
        controls_sizer.Add(self.sample_num, 0, wx.ALL, 5)
        
        toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        useful_tool = toolbar.AddTool(wx.ID_ANY, label=GUIText.NOT_SURE, bitmap=wx.Bitmap(1, 1),
                                      shortHelp=GUIText.NOT_SURE_HELP)
        toolbar.Bind(wx.EVT_MENU, self.OnUseful, useful_tool)
        
        useful_tool = toolbar.AddTool(wx.ID_ANY, label=GUIText.USEFUL, bitmap=wx.Bitmap(1, 1),
                                      shortHelp=GUIText.USEFUL_HELP)
        toolbar.Bind(wx.EVT_MENU, self.OnUseful, useful_tool)
        notuseful_tool = toolbar.AddTool(wx.ID_ANY, label=GUIText.NOT_USEFUL, bitmap=wx.Bitmap(1, 1),
                                         shortHelp=GUIText.NOT_USEFUL_HELP)
        toolbar.Bind(wx.EVT_MENU, self.OnNotUseful, notuseful_tool)
        toolbar.Realize()
        controls_sizer.Add(toolbar, 0, wx.ALL, 5)

        self.sizer.Add(controls_sizer, 0, wx.ALL, 5)
        
        self.parts_model = SamplesDataViews.PartsViewModel(self.sample, self.dataset)
        self.parts_ctrl = SamplesDataViews.PartsViewCtrl(self, self.parts_model)
        self.parts_model.Cleared()
        self.parts_ctrl.Expander(None)
        columns = self.parts_ctrl.GetColumns()
        for column in reversed(columns):
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        self.sizer.Add(self.parts_ctrl, 1, wx.EXPAND, 5)

        self.SetSizer(self.sizer)

        logger.info("Finished")

    def OnChangeDocumentNumber(self, event):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].OnChangeDocumentNumber")
        logger.info("Starting")
        document_num = self.sample_num.GetValue()
        for part_key in self.parts:
            parent = self.parts[part_key].parent
            while parent is not None and not isinstance(parent, Samples.Sample):
                parent = parent.parent
            dataset_key = parent.dataset_key

            if dataset_key in wx.GetApp().GetTopWindow().datasets:
                self.parts[part_key].UpdateDocumentNum(document_num, wx.GetApp().GetTopWindow().datasets[dataset_key])
            else:
                self.parts[part_key].UpdateDocumentNum(document_num, None)
        self.parts_model.Cleared()
        self.parts_ctrl.Expander(None)
        logger.info("Finished")

    def OnNotSure(self, event):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].OnNotSure")
        logger.info("Starting")
        for item in self.parts_ctrl.GetSelections():
            node = self.parts_model.ItemToObject(item)
            node.usefulness_flag = None
            self.parts_model.ItemChanged(item)
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()
        logger.info("Finished")

    def OnUseful(self, event):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].OnUseful")
        logger.info("Starting")
        for item in self.parts_ctrl.GetSelections():
            node = self.parts_model.ItemToObject(item)
            node.usefulness_flag = True
            self.parts_model.ItemChanged(item)
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()
        logger.info("Finished")

    def OnNotUseful(self, event):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].OnNotUseful")
        logger.info("Starting")
        for item in self.parts_ctrl.GetSelections():
            node = self.parts_model.ItemToObject(item)
            node.usefulness_flag = False
            self.parts_model.ItemChanged(item)
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()
        logger.info("Finished")

    def ChangeSelectedParts(self, selected_parts):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].ChangeSelectedParts")
        logger.info("Starting")
        self.parts.clear()
        self.parts.update(selected_parts)
        self.parts_model.Cleared()
        self.parts_ctrl.Expander(None)
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].DatasetsUpdated")
        logger.info("Starting")
        new_parts_model = SamplesDataViews.PartsViewModel(self.sample, self.dataset)
        new_parts_ctrl = SamplesDataViews.PartsViewCtrl(self, new_parts_model)
        self.sizer.Replace(self.parts_ctrl, new_parts_ctrl)
        self.Layout()
        self.parts_ctrl.Destroy()
        self.parts_model = new_parts_model
        self.parts_ctrl = new_parts_ctrl
        self.DocumentsUpdated()
        logger.info("Finished")

    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].DocumentsUpdated")
        logger.info("Starting")
        self.parts_model.Cleared()
        self.parts_ctrl.Expander(None)
        logger.info("Finished")

    #Module Control commands
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".PartPanel["+str(self.sample.key)+"].Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data

class SampleRulesDialog(wx.Dialog):
    def __init__(self, parent, sample, dataset, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        logger = logging.getLogger(__name__+".SampleRulesDialog["+str(sample.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=FilteringGUIText.FILTERS_RULES+": "+repr(sample), style=style, size=wx.Size(600,400))
        self.sample = sample
        self.dataset = dataset
        
        package_list = list(sample.tokenization_package_versions)
        tokenizer_package = sample.tokenization_package_versions[0]
        package_list[0] = FilteringGUIText.FILTERS_RAWTOKENS
        package_list[1] = FilteringGUIText.FILTERS_STEMMER + package_list[1]
        package_list[2] = FilteringGUIText.FILTERS_LEMMATIZER + package_list[2]
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_HORZ_TEXT|wx.TB_NOICONS)
        restore_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.RESTORE_RULES,
                                            bitmap=wx.Bitmap(1, 1),
                                            shortHelp=GUIText.RESTORE_RULES_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.OnRestore, restore_tool)
        self.toolbar.Realize()
        sizer.Add(self.toolbar, proportion=0, flag=wx.ALL, border=5)

        tokenization_sizer = wx.BoxSizer(wx.HORIZONTAL)
        tokenization_package_label1 = wx.StaticText(self, label=FilteringGUIText.FILTERS_TOKENIZER)
        tokenization_package_label1.SetFont(wx.Font(-1, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        tokenization_sizer.Add(tokenization_package_label1, proportion=0, flag=wx.ALL, border=5)
        tokenization_package_label2 = wx.StaticText(self, label=tokenizer_package)
        tokenization_sizer.Add(tokenization_package_label2, proportion=0, flag=wx.ALL, border=5)
        tokenization_choice_label = wx.StaticText(self, label=FilteringGUIText.FILTERS_METHOD)
        tokenization_choice_label.SetFont(wx.Font(-1, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        tokenization_sizer.Add(tokenization_choice_label, proportion=0, flag=wx.ALL, border=5)
        tokenization_label = wx.StaticText(self, label=package_list[sample.tokenization_choice])
        tokenization_sizer.Add(tokenization_label, proportion=0, flag=wx.ALL, border=5)
        sizer.Add(tokenization_sizer, proportion=0, flag=wx.ALL, border=5)
        
        self.rules_list = DatasetsDataViews.FilterRuleDataViewListCtrl(self)
        self.DisplayFilterRules(sample.applied_filter_rules)
        sizer.Add(self.rules_list, proportion=1, flag=wx.EXPAND, border=5)

        self.SetSizer(sizer)
        self.Layout()

        logger.info("Finished")

    def DisplayFilterRules(self, filter_rules):
        column_options = {Constants.TOKEN_NUM_WORDS:FilteringGUIText.FILTERS_NUM_WORDS,
                          Constants.TOKEN_PER_WORDS:FilteringGUIText.FILTERS_PER_WORDS,
                          Constants.TOKEN_NUM_DOCS:FilteringGUIText.FILTERS_NUM_DOCS,
                          Constants.TOKEN_PER_DOCS:FilteringGUIText.FILTERS_PER_DOCS}
        self.rules_list.DeleteAllItems()
        i = 1
        for field, word, pos, action in filter_rules:
            if isinstance(action, tuple):
                if action[0] == Constants.FILTER_TFIDF_REMOVE or action[0] == Constants.FILTER_TFIDF_INCLUDE:
                    action = str(action[0])+str(action[1])+str(action[2]*100)+"%"
                else:
                    action = str(action[0]) + " ("+str(column_options[action[1]])+str(action[2])+str(action[3])+")"
                
            self.rules_list.AppendItem([i, field, word, pos, str(action)])
            i += 1
    
    def OnRestore(self, event):
        logger = logging.getLogger(__name__+".SampleIncludedFieldsDialog["+str(self.sample.key)+"].OnRestore")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()

        if wx.MessageBox(GUIText.CONFIRM_RESTORE_RULES,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished - Cancelled")
            return

        main_frame.CreateProgressDialog(GUIText.RESTORE_RULES,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=True)
        main_frame.PulseProgressDialog(GUIText.RESTORE_BEGINNING_MSG)

        main_frame.PulseProgressDialog(GUIText.RESTORE_REPLACINGRULES_MSG)
        self.dataset.tokenization_choice = self.sample.tokenization_choice
        self.dataset.filter_rules.clear()
        self.dataset.filter_rules.extend(self.sample.applied_filter_rules)
        main_frame.DatasetsUpdated()

        main_frame.CloseProgressDialog(message=GUIText.RESTORE_COMPLETED_MSG,
                                       thaw=True)
        logger.info("Finished")

class SampleIncludedFieldsDialog(wx.Dialog):
    def __init__(self, parent, sample, dataset, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        logger = logging.getLogger(__name__+".SampleIncludedFieldsDialog["+str(sample.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=FilteringGUIText.INCLUDEDFIELDS+": "+repr(sample), style=style, size=wx.Size(600,400))
        self.sample = sample
        self.dataset = dataset
        self.tokenization_thread = None
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.fields = {}
        for field_key in self.sample.fields_list:
            self.fields[field_key] = self.dataset.available_fields[field_key]
        
        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_HORZ_TEXT|wx.TB_NOICONS)
        restore_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.RESTORE_INCLUDEDFIELDS,
                                            bitmap=wx.Bitmap(1, 1),
                                            shortHelp=GUIText.RESTORE_INCLUDEDFIELDS_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.OnRestoreStart, restore_tool)
        CustomEvents.TOKENIZER_EVT_RESULT(self, self.OnRestoreFinish)
        self.toolbar.Realize()
        sizer.Add(self.toolbar, proportion=0, flag=wx.ALL, border=5)

        self.included_fields_model = DatasetsDataViews.ChosenFieldsViewModel(self.fields)
        self.included_fields_ctrl = DatasetsDataViews.FieldsViewCtrl(self, self.included_fields_model)
        sizer.Add(self.included_fields_ctrl, proportion=1, flag=wx.EXPAND, border=5)

        self.SetSizer(sizer)
        self.Layout()

        logger.info("Finished")
    
    def OnRestoreStart(self, event):
        logger = logging.getLogger(__name__+".SampleIncludedFieldsDialog["+str(self.sample.key)+"].OnRestoreStart")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()

        if wx.MessageBox(GUIText.CONFIRM_RESTORE_INCLUDEDFIELDS,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished - Cancelled")
            return

        main_frame.CreateProgressDialog(GUIText.RESTORE_RULES,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=True)
        main_frame.PulseProgressDialog(GUIText.RESTORE_BEGINNING_MSG)

        db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)

        main_frame.PulseProgressDialog(GUIText.RESTORE_REPLACINGFIELDS_MSG)
        #1) remove from the dataset any currently included fields
        for field_key in list(self.dataset.included_fields.keys()):
            if field_key not in self.fields:
                db_conn.DeleteField(self.dataset.key, field_key)
            self.dataset.included_fields[field_key].DestroyObject()
        #2) add to the dataset any fields from sample's field_list that are not included fields dataset
        for field_key in self.fields:
            self.dataset.included_fields[field_key] = copy.copy(self.fields[field_key])
            
        main_frame.multiprocessing_inprogress_flag = True
        self.tokenization_thread = DatasetsThreads.TokenizerThread(self, main_frame, self.dataset)
        logger.info("Finished")

    def OnRestoreFinish(self, event):
        logger = logging.getLogger(__name__+".SampleIncludedFieldsDialog["+str(self.sample.key)+"].OnRestoreFinish")
        logger.info("Starting")
        self.tokenization_thread.join()
        self.tokenization_thread = None
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.multiprocessing_inprogress_flag = False
        main_frame.DatasetsUpdated()
        main_frame.CloseProgressDialog(message=GUIText.RESTORE_COMPLETED_MSG,
                                       thaw=True)
        logger.info("Finished")

class RandomSamplePanel(AbstractSamplePanel):
    '''general class for features RandomSample panels should have'''
    def __init__(self, parent, sample, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".RandomSamplePanel["+str(sample.key)+"].__init__")
        logger.info("Starting")
        AbstractSamplePanel.__init__(self, parent, sample, dataset, size)

        sizer = wx.BoxSizer(wx.VERTICAL)

        details_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_frame = wx.GetApp().GetTopWindow()
        type_label = wx.StaticText(self, label=GUIText.SAMPLE_TYPE+": "+str(sample.sample_type))
        details_sizer.Add(type_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details_sizer.AddSpacer(10)
        if main_frame.multipledatasets_mode:
            dataset_label = wx.StaticText(self, label=GUIText.DATASET+": "+str(sample.dataset_key))
            details_sizer.Add(dataset_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details_sizer.AddSpacer(10)
        created_dt_label = wx.StaticText(self, label=GUIText.CREATED_ON+": "+self.sample.start_dt.strftime("%Y-%m-%d %H:%M:%S"))
        details_sizer.Add(created_dt_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer.Add(details_sizer, 0, wx.ALL, 5)

        self.parts_panel = PartPanel(self, self.sample, self.dataset, sample.parts_dict)
        sizer.Add(self.parts_panel, 1, wx.EXPAND, 5)
        
        self.SetSizer(sizer)
        logger.info("Finished")
    
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".RandomSamplePanel["+str(self.sample.key)+"].Load")
        logger.info("Starting")
        logger.info("Finished")
        return

    def Save(self):
        logger = logging.getLogger(__name__+".RandomSamplePanel["+str(self.sample.key)+"].Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data

class RandomModelCreateDialog(wx.Dialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".ModelCreateDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.CREATE_RANDOM, )

        self.model_parameters = {}

        sizer = wx.BoxSizer(wx.VERTICAL)
        name_label = wx.StaticText(self, label=GUIText.NAME+":")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        name_sizer.Add(self.name_ctrl, 0, wx.ALL, 5)
        sizer.Add(name_sizer)

        main_frame = wx.GetApp().GetTopWindow()
        self.usable_datasets = list(main_frame.datasets.keys())
        usable_datasets_strings = [str(dataset_key) for dataset_key in self.usable_datasets]
        if len(self.usable_datasets) > 1: 
            dataset_label = wx.StaticText(self, label=GUIText.DATASET+":")
            self.dataset_ctrl = wx.Choice(self, choices=usable_datasets_strings)
            dataset_sizer = wx.BoxSizer(wx.HORIZONTAL)
            dataset_sizer.Add(dataset_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            dataset_sizer.Add(self.dataset_ctrl, 0, wx.ALL, 5)
            sizer.Add(dataset_sizer)

        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK, )
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label=GUIText.CANCEL)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.Add(ok_button)
        controls_sizer.Add(cancel_button)
        sizer.Add(controls_sizer)
        self.SetSizer(sizer)
        
        self.Layout()
        self.Fit()
        logger.info("Finished")

    def OnOK(self, event):
        logger = logging.getLogger(__name__+".ModelCreateDialog.OnOK")
        logger.info("Starting")
        app = wx.GetApp()
        main_frame = wx.GetApp().GetTopWindow()
        #check that name exists and is unique
        status_flag = True

        model_name = self.name_ctrl.GetValue()
        model_name = model_name.replace(" ", "_")
        if model_name != "":
            if model_name in main_frame.samples:
                wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('name[%s] is not unique', model_name)
                status_flag = False
        else:
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('name field is empty')
            status_flag = False

        if len(self.usable_datasets) > 1: 
            dataset_id = self.dataset_ctrl.GetSelection()
            if dataset_id is wx.NOT_FOUND:
                wx.MessageBox(GUIText.DATASET_MISSING_ERROR,
                            GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('dataset was not chosen')
                status_flag = False
        elif len(self.usable_datasets) == 1:
            dataset_id = 0
        else:
            wx.MessageBox(GUIText.DATASET_NOTAVALIABLE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('no dataset available')
            status_flag = False

        if status_flag:
            self.model_parameters['name'] = model_name
            self.model_parameters['dataset_key'] = self.usable_datasets[dataset_id]
        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)

class TopicSamplePanel(AbstractSamplePanel):
    '''general class for features TopicSample panels should have'''
    def __init__(self, parent, sample, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(sample.key)+"].__init__")
        logger.info("Starting")
        AbstractSamplePanel.__init__(self, parent, sample, dataset, size=size)

        self.selected_parts = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        details1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_frame = wx.GetApp().GetTopWindow()
        type_label = wx.StaticText(self, label=GUIText.SAMPLE_TYPE+": "+str(sample.sample_type))
        details1_sizer.Add(type_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details1_sizer.AddSpacer(10)
        if main_frame.multipledatasets_mode:
            dataset_label = wx.StaticText(self, label=GUIText.DATASET+": "+str(sample.dataset_key))
            details1_sizer.Add(dataset_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details1_sizer.AddSpacer(10)
        created_dt_label = wx.StaticText(self, label=GUIText.CREATED_ON+": "+self.sample.created_dt.strftime("%Y-%m-%d %H:%M:%S"))
        details1_sizer.Add(created_dt_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        self.sizer.Add(details1_sizer, 0, wx.ALL, 5)

        details2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        num_topics_label = wx.StaticText(self, label=GUIText.NUMBER_OF_TOPICS+" "+str(sample.num_topics))
        details2_sizer.Add(num_topics_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details2_sizer.AddSpacer(10)
        if hasattr(sample, 'num_passes'):
            num_passes_label = wx.StaticText(self, label=GUIText.NUMBER_OF_PASSES+" "+str(sample.num_passes))
            details2_sizer.Add(num_passes_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details2_sizer.AddSpacer(10)
        used_documents_label = wx.StaticText(self, label=GUIText.NUMBER_OF_DOCUMENTS+str(len(self.sample.tokensets)))
        details2_sizer.Add(used_documents_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        rules_button = wx.Button(self, label=FilteringGUIText.FILTERS_RULES)
        rules_button.Bind(wx.EVT_BUTTON, self.OnShowRules)
        details2_sizer.Add(rules_button, 0, wx.ALL, 5)
        includefields_button = wx.Button(self, label=FilteringGUIText.INCLUDEDFIELDS)
        includefields_button.Bind(wx.EVT_BUTTON, self.OnShowIncludedFields)
        details2_sizer.Add(includefields_button, 0, wx.ALL, 5)
        self.sizer.Add(details2_sizer, 0, wx.ALL, 5)


        #initialize and show an inprogress panel for display while model is generating
        inprogress_panel = wx.Panel(self)
        inprogress_sizer = wx.BoxSizer(wx.VERTICAL)
        inprogress_text = wx.StaticText(inprogress_panel, label=GUIText.CURRENTLY_GENERATING)
        inprogress_sizer.Add(inprogress_text, 0, wx.ALL, 5)
        inprogress_panel.SetSizer(inprogress_sizer)
        self.sizer.Add(inprogress_panel, 1, wx.EXPAND, 5)
        self.SetSizer(self.sizer)

        #actions for different gui element's triggers
        CustomEvents.MODELCREATED_EVT_RESULT(self, self.OnFinish)

        self.Layout()

        logger.info("Finished")
    
    def OnFinish(self, event):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].OnFinish")
        logger.info("Starting")
        self.Freeze()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.GENERATED_DEFAULT_LABEL,
                                        warning=GUIText.GENERATE_WARNING+"\n"+GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        try:
            main_frame.PulseProgressDialog(GUIText.GENERATED_DEFAULT_LABEL+": "+str(self.sample.key))
            dataset = None
            if self.sample.dataset_key in main_frame.datasets:
                dataset = main_frame.datasets[self.sample.dataset_key]
            self.sample.GenerateFinish(event.data, dataset, main_frame.current_workspace.name)
            self.DisplayModel()
            main_frame.DocumentsUpdated()
        finally:
            main_frame.multiprocessing_inprogress_flag = False
            main_frame.CloseProgressDialog(thaw=False)
            self.Thaw()
        logger.info("Finished")
    
    def OnShowRules(self, event):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].OnShowRules")
        logger.info("Starting")
        SampleRulesDialog(self, self.sample, self.dataset).Show()
        logger.info("Finished")

    def OnShowIncludedFields(self, event):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].OnShowIncludedFields")
        logger.info("Starting")
        SampleIncludedFieldsDialog(self, self.sample, self.dataset).Show()
        logger.info("Finished")
    
    def OnChangeTopicWordNum(self, event):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].OnChangeTopicWordNum")
        logger.info("Starting")
        self.sample.word_num = self.topiclist_panel.topic_list_num.GetValue()
        self.topiclist_panel.topic_list_model.Cleared()
        self.topiclist_panel.topic_list_ctrl.Expander(None)
        #self.visualization_panel.Refresh(self.selected_parts)
        self.DrawLDAPlot(self.selected_parts)
        logger.info("Finished")

    def OnMergeTopics(self, event):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].OnMergeTopics")
        logger.info("Starting")
        selections = self.topiclist_panel.topic_list_ctrl.GetSelections()
        nodes = []
        old_mergedparts = []
        for item in selections:
            node = self.topiclist_panel.topic_list_model.ItemToObject(item)
            if isinstance(node, Samples.TopicPart):
                nodes.append(node)
                if isinstance(node.parent, Samples.TopicMergedPart):
                    if node.parent not in old_mergedparts:
                        old_mergedparts.append(node.parent)
            if isinstance(node, Samples.TopicMergedPart):
                if node not in old_mergedparts:
                    old_mergedparts.append(node)
                for part_key in node.parts_dict:
                    nodes.append(node.parts_dict[part_key])
        if len(nodes) > 1:
            tmp_id = 0
            while 'M'+str(tmp_id) in self.sample.parts_dict:
                tmp_id += 1
            key = 'M'+str(tmp_id)
            new_parent = Samples.TopicMergedPart(self.sample, key)
            self.sample.parts_dict[key] = new_parent
            for node in nodes:
                del node.parent.parts_dict[node.key]
                node.parent.last_changed_dt = datetime.now()
                node.parent = new_parent
                new_parent.parts_dict[node.key] = node
            for row in self.sample.document_topic_prob:
                doc_topic_prob = 0.0
                row_dict = self.sample.document_topic_prob[row]
                for topic_key in new_parent.parts_dict:
                    doc_topic_prob = max(doc_topic_prob, row_dict[topic_key])
                self.sample.document_topic_prob[row][key] = doc_topic_prob
            if len(old_mergedparts) > 0:
                for node in old_mergedparts:
                    for document_key in self.sample.document_topic_prob:
                        to_remove_entry = None
                        for entry_key in self.sample.document_topic_prob[document_key]:
                            if entry_key == node.key:
                                to_remove_entry = entry_key
                                break
                        if to_remove_entry != None:
                            del self.sample.document_topic_prob[document_key][to_remove_entry]
                    if len(node.parts_dict) == 0:
                        node.DestroyObject()
                    else:
                        for row in self.sample.document_topic_prob:
                            doc_topic_prob = 0.0
                            row_dict = dict(row)
                            for topic_key in node.parts_dict:
                                doc_topic_prob = max(doc_topic_prob, row_dict[topic_key])
                            row.append((node.key, doc_topic_prob,))
            self.sample.ApplyDocumentCutoff()
            self.topiclist_panel.topic_list_model.Cleared()
            self.topiclist_panel.topic_list_ctrl.Expander(None)
            self.topiclist_panel.topic_list_ctrl.UnselectAll()
            self.ChangeSelections()
            self.parts_panel.ChangeSelectedParts(self.selected_parts)
            self.parts_panel.OnChangeDocumentNumber(None)
            #self.visualization_panel.Refresh(self.selected_parts)
            self.DrawLDAPlot(self.selected_parts)
            
        logger.info("Finished")
    
    def OnSplitTopics(self, event):
        logger = logging.getLogger(__name__+"TopicSamplePanel["+str(self.sample.key)+"].OnSplitTopics")
        logger.info("Starting")
        selections = self.topiclist_panel.topic_list_ctrl.GetSelections()
        nodes = []
        old_mergedparts = []
        for item in selections:
            node = self.topiclist_panel.topic_list_model.ItemToObject(item)
            if isinstance(node, Samples.TopicPart):
                if isinstance(node.parent, Samples.TopicMergedPart):
                    nodes.append(node)
                    if node.parent not in old_mergedparts:
                        old_mergedparts.append(node.parent)
            if isinstance(node, Samples.TopicMergedPart):
                if node not in old_mergedparts:
                        old_mergedparts.append(node)
                for part_key in node.parts_dict:
                    nodes.append(node.parts_dict[part_key])
        if len(nodes) > 0:
            for node in nodes:
                new_parent = node.parent.parent
                del node.parent.parts_dict[node.key]
                node.parent.last_changed_dt = datetime.now()
                node.parent = new_parent
                new_parent.parts_dict[node.key] = node
            if len(old_mergedparts) > 0:
                for node in old_mergedparts:
                    for document_key in self.sample.document_topic_prob:
                        to_remove_entry = None
                        for entry_key in self.sample.document_topic_prob[document_key]:
                            if entry_key == node.key:
                                to_remove_entry = entry_key
                                break
                        if to_remove_entry != None:
                            del self.sample.document_topic_prob[document_key][to_remove_entry]
                    if len(node.parts_dict) == 0:
                        node.DestroyObject()
                    else:
                        for row in self.sample.document_topic_prob:
                            doc_topic_prob = 0.0
                            row_dict = dict(row)
                            for topic_key in node.parts_dict:
                                doc_topic_prob = max(doc_topic_prob, row_dict[topic_key])
                            row.append((node.key, doc_topic_prob,))
            self.sample.ApplyDocumentCutoff()
            self.topiclist_panel.topic_list_model.Cleared()
            self.topiclist_panel.topic_list_ctrl.Expander(None)
            self.topiclist_panel.topic_list_ctrl.UnselectAll()
            self.ChangeSelections()
            self.parts_panel.ChangeSelectedParts(self.selected_parts)
            self.parts_panel.OnChangeDocumentNumber(None)
            #self.visualization_panel.Refresh(self.selected_parts)
            self.DrawLDAPlot(self.selected_parts)
            
        logger.info("Finished")

    def OnRemoveTopics(self, event):
        logger = logging.getLogger(__name__+"TopicSamplePanel["+str(self.sample.key)+"].OnRemoveTopics")
        logger.info("Starting")
        selections = self.topiclist_panel.topic_list_ctrl.GetSelections()
        nodes = []
        old_mergedparts = []
        for item in selections:
            node = self.topiclist_panel.topic_list_model.ItemToObject(item)
            if isinstance(node, Samples.TopicPart):
                nodes.append(node)
                if isinstance(node.parent, Samples.TopicMergedPart):
                    if node.parent not in old_mergedparts:
                        old_mergedparts.append(node.parent)
            if isinstance(node, Samples.TopicMergedPart):
                if node not in old_mergedparts:
                    old_mergedparts.append(node)
                for part_key in node.parts_dict:
                    nodes.append(node.parts_dict[part_key])

        #confirmation
        if wx.MessageBox(GUIText.CONFIRM_DELETE_TOPICS,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished - Cancelled")
            return

        if len(nodes) > 0:
            for node in nodes:
                del node.parent.parts_dict[node.key]
                node.parent = None
            if len(old_mergedparts) > 0:
                for node in old_mergedparts:
                    if len(node.parts_dict) == 0:
                        node.DestroyObject()
                    else:
                        for row in self.sample.document_topic_prob:
                            doc_topic_prob = 0.0
                            row_dict = self.sample.document_topic_prob[row]
                            for topic_key in node.parts_dict:
                                doc_topic_prob = max(doc_topic_prob, row_dict[topic_key])
                            self.sample.document_topic_prob[row][node.key] = doc_topic_prob
            self.sample.ApplyDocumentCutoff()
            self.topiclist_panel.topic_list_model.Cleared()
            self.topiclist_panel.topic_list_ctrl.Expander(None)
            self.ChangeSelections()
            self.parts_panel.ChangeSelectedParts(self.selected_parts)
            self.parts_panel.OnChangeDocumentNumber(None)
            #self.visualization_panel.Refresh(self.selected_parts)
            self.DrawLDAPlot(self.selected_parts)
            
        logger.info("Finished")

    def OnChangeCutoff(self, event):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].OnChangeCutoff")
        logger.info("Starting")

        obj = event.GetEventObject()
        #if obj is self.topiclist_panel.cutoff_slider:
        #    new_cutoff = self.topiclist_panel.cutoff_slider.GetValue()/1000
        #    self.topiclist_panel.cutoff_spin.SetValue(new_cutoff)
        #elif obj is self.topiclist_panel.cutoff_spin:
        new_cutoff = self.topiclist_panel.cutoff_spin.GetValue()
        #    self.topiclist_panel.cutoff_slider.SetValue(int(new_cutoff*1000))
        
        if self.sample.document_cutoff != new_cutoff:
            self.sample.document_cutoff = new_cutoff
            self.sample.ApplyDocumentCutoff()

        #self.visualization_panel.Refresh(self.selected_parts)
        self.DrawLDAPlot(self.selected_parts)
        self.parts_panel.OnChangeDocumentNumber(None)

        logger.info("Finished")

    def OnTopicsSelected(self, event):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].OnTopicsSelected")
        logger.info("Starting")
        self.Freeze()

        #figure out what topics have been selected
        self.ChangeSelections()
        self.parts_panel.ChangeSelectedParts(self.selected_parts)
        #update the data and visualizations of selected topics
        #self.visualization_panel.DrawLDAPlots(self.selected_parts)
        self.DrawLDAPlot(self.selected_parts)
        
        self.Thaw()
        logger.info("Finished")

    def DisplayModel(self):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].DisplayModel")
        logger.info("Starting")
        self.Freeze()
        self.sizer.Clear(True)

        #initialize but do not show panels that will be used when displaying the sample after it is generated
        self.vertical_splitter = wx.SplitterWindow(self)
        self.vertical_splitter.SetMinimumPaneSize(20)
        self.horizontal_splitter = wx.SplitterWindow(self.vertical_splitter)
        self.horizontal_splitter.SetMinimumPaneSize(20)

        self.topiclist_panel = TopicListPanel(self.horizontal_splitter, self.sample, self.dataset)
        self.topiclist_panel.toolbar.Bind(wx.EVT_MENU, self.OnMergeTopics, self.topiclist_panel.merge_topics_tool)
        self.topiclist_panel.toolbar.Bind(wx.EVT_MENU, self.OnSplitTopics, self.topiclist_panel.split_topics_tool)
        self.topiclist_panel.toolbar.Bind(wx.EVT_MENU, self.OnRemoveTopics, self.topiclist_panel.remove_topics_tool)
        self.topiclist_panel.topic_list_num.Bind(wx.EVT_SPINCTRL, self.OnChangeTopicWordNum)
        #turned off for performance reasons
        self.topiclist_panel.topic_list_ctrl.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.OnTopicsSelected)
        #self.topiclist_panel.cutoff_slider.Bind(wx.EVT_SLIDER, self.OnChangeCutoff)
        self.topiclist_panel.cutoff_spin.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnChangeCutoff)

        #self.visualization_panel = TopicVisualizationsNotebook(self.vertical_splitter, self.sample)
        self.visualization_panel = ChordPlotPanel(self.vertical_splitter)

        self.parts_panel = PartPanel(self.horizontal_splitter, self.sample, self.dataset, self.sample.parts_dict)

        self.horizontal_splitter.SplitHorizontally(self.topiclist_panel, self.parts_panel)
        self.horizontal_splitter.SetSashPosition(int(self.GetSize().GetHeight()/4))
        self.vertical_splitter.SplitVertically(self.horizontal_splitter, self.visualization_panel)
        self.vertical_splitter.SetSashPosition(int(self.GetSize().GetWidth()/3.5))

        self.sizer.Add(self.vertical_splitter, 1, wx.EXPAND, 5)

        self.topiclist_panel.topic_list_model.Cleared()
        self.topiclist_panel.topic_list_ctrl.Expander(None)
        self.ChangeSelections()
        #self.visualization_panel.Refresh(self.selected_parts)
        self.DrawLDAPlot(self.selected_parts)
        self.parts_panel.ChangeSelectedParts(self.selected_parts)
        self.parts_panel.OnChangeDocumentNumber(None)
        
        self.Layout()
        self.Thaw()
        logger.info("Finished")
    
    def ChangeSelections(self):
        selections = self.topiclist_panel.topic_list_ctrl.GetSelections()
        self.selected_parts = {}
        if len(selections) == 1:
            for item in selections:
                part = self.topiclist_panel.topic_list_model.ItemToObject(item)
                if isinstance(part, Samples.TopicMergedPart):
                    for part_key in part.parts_dict:
                        self.selected_parts[part_key] = part.parts_dict[part_key]
                else:
                    for key in self.sample.parts_dict:
                        self.selected_parts[key] = self.sample.parts_dict[key]
        elif len(selections) > 1:
            for item in selections:
                    part = self.topiclist_panel.topic_list_model.ItemToObject(item)
                    self.selected_parts[part.key] = part
        else:
            for key in self.sample.parts_dict:
                self.selected_parts[key] = self.sample.parts_dict[key]
    
    def DrawLDAPlot(self, topics):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].DrawLDAPlot")
        logger.info("Starting")

        weight_map = {}
        def GetTopicData(topic):
            topicprob_weights = {keyword[0]: keyword[1] for keyword in topic.GetTopicKeywordsList()}
            #corpusfreq_weights = {keyword[0]: self.sample.dictionary.cfs[self.sample.dictionary.token2id[keyword[0]]] for keyword in topic.GetTopicKeywordsList()}
            #docfreq_weights = {keyword[0]: self.sample.dictionary.dfs[self.sample.dictionary.token2id[keyword[0]]] for keyword in topic.GetTopicKeywordsList()}
            nonlocal weight_map
            weight_map[topic.key] = topicprob_weights

        included_topics = {}
        for topic_key in topics:
            GetTopicData(topics[topic_key])
            included_topics[topic_key] = topics[topic_key]

        self.visualization_panel.Draw(model_documenttopart_prob=list(self.sample.document_topic_prob.values()),
                                      parts=included_topics, cutoff=self.sample.document_cutoff, word_cloud_freq=weight_map)
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].Load")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if self.sample.generated_flag == False:
            main_frame.multiprocessing_inprogress_flag = True
            self.sample.GenerateStart(self)
        else:
            self.DisplayModel()
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".TopicSamplePanel["+str(self.sample.key)+"].Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data

#TODO reactivate and test to allow plugins (reviewer suggestion)
class TopicVisualizationsNotebook(FNB.FlatNotebook):
    def __init__(self, parent, sample):
        logger = logging.getLogger(__name__+".TopicVisualizationsNotebook["+str(sample.key)+"].__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, style=Constants.FNB_STYLE)
        self.sample = sample

        self.chordplot_panel = ChordPlotPanel(self)
        self.AddPage(self.chordplot_panel, "Chord Plot")

        #TODO choose:
        # 1) augment to handle unknown topic 
        # 2) consider if it is ok to ignore unknown topics
        #self.pyLDAvis_panel = pyLDAvisPanel(self)
        #self.AddPage(self.pyLDAvis_panel, "pyLDAvis")#self.wordnetworkgraph_panel = NetworkPlotPlanel(self)
        #self.AddPage(self.wordnetworkgraph_panel, "Word Network Graph")
        #self.wordcloudnetworkgraph_panel = NetworkPlotPlanel(self)
        #self.AddPage(self.wordcloudnetworkgraph_panel, "WordCloud Network Graph")
        #self.wordcloudnetworkgraph_panel = NetworkPlotPlanel(self)
        #self.AddPage(self.wordcloudnetworkgraph_panel, "WordCloud Network Graph")
        
        #self.treemap_topic_panels = {}
        #self.treemap_panel = TreemapPlotPlanel(self)
        #self.AddPage(self.treemap_panel, "Treemap")

        logger.info("Finished")

    def DrawLDAPlots(self, topics):
        logger = logging.getLogger(__name__+".TopicVisualizationsNotebook["+str(self.sample.key)+"].DrawLDATopicNetworkGraph")
        logger.info("Starting")

        edge_map = {}
        weight_map = {}
        label_dict = {}
        annot_dict = {}
        def GetTopicData(topic):
            keywords = [keyword[0] for keyword in topic.GetTopicKeywordsList()]
            nonlocal edge_map
            edge_map[topic.key] = keywords

            topicprob_weights = {keyword[0]: keyword[1] for keyword in topic.GetTopicKeywordsList()}
            corpusfreq_weights = {keyword[0]: self.sample.dictionary.cfs[self.sample.dictionary.token2id[keyword[0]]] for keyword in topic.GetTopicKeywordsList()}
            docfreq_weights = {keyword[0]: self.sample.dictionary.dfs[self.sample.dictionary.token2id[keyword[0]]] for keyword in topic.GetTopicKeywordsList()}
            nonlocal weight_map
            weight_map[topic.key] = topicprob_weights

            nonlocal label_dict
            nonlocal annot_dict
            if topic.label != "":
                label_dict[topic.key] = "Topic "+str(topic.key) + "\n"+topic.label
            else:
                label_dict[topic.key] = "Topic "+str(topic.key)
            for keyword in keywords:
                label_dict[keyword] = keyword
                annot_dict[keyword] = keyword + "\nTopic Contribution: " + str(topicprob_weights[keyword]) + "\nWord Count: " + str(corpusfreq_weights[keyword]) + "\nDocument Count: " + str(docfreq_weights[keyword])

        included_topics = {}
        for topic_key in topics:
            GetTopicData(topics[topic_key])
            included_topics[topic_key] = topics[topic_key]

        #self.wordcloudnetworkgraph_panel.Draw(edge_map, label_dict, word_cloud_freq=weight_map)
        #self.wordnetworkgraph_panel.Draw(edge_map, label_dict, annot_dict=annot_dict)

        self.chordplot_panel.Draw(model_documenttopart_prob=list(self.sample.document_topic_prob.values()),
                                  parts=included_topics, cutoff=self.sample.document_cutoff, word_cloud_freq=weight_map)
        logger.info("Finished")

    def Refresh(self, selected_parts):
        self.DrawLDAPlots(selected_parts)

class TopicListPanel(wx.Panel):
    def __init__(self, parent, sample, dataset):
        logger = logging.getLogger(__name__+".TopicListPanel["+str(sample.key)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)

        self.sample = sample
        self.dataset = dataset

        topic_list_sizer = wx.BoxSizer(wx.VERTICAL)

        details1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_frame = wx.GetApp().GetTopWindow()
        type_label = wx.StaticText(self, label=GUIText.SAMPLE_TYPE+": "+str(self.sample.sample_type))
        details1_sizer.Add(type_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details1_sizer.AddSpacer(10)
        if main_frame.multipledatasets_mode:
            dataset_label = wx.StaticText(self, label=GUIText.DATASET+": "+str(self.sample.dataset_key))
            details1_sizer.Add(dataset_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details1_sizer.AddSpacer(10)
        created_dt_label = wx.StaticText(self, label=GUIText.CREATED_ON+": "+self.sample.start_dt.strftime("%Y-%m-%d %H:%M:%S"))
        details1_sizer.Add(created_dt_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details1_sizer.AddSpacer(10)
        generate_time_label = wx.StaticText(self, label=GUIText.GENERATE_TIME+": "+str(self.sample.end_dt - self.sample.start_dt).split('.')[0])
        details1_sizer.Add(generate_time_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        topic_list_sizer.Add(details1_sizer, 0, wx.ALL, 5)

        details2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        num_topics_label = wx.StaticText(self, label=GUIText.NUMBER_OF_TOPICS+str(self.sample.num_topics))
        details2_sizer.Add(num_topics_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        details2_sizer.AddSpacer(10)
        if hasattr(self.sample, 'num_passes'):
            num_passes_label = wx.StaticText(self, label=GUIText.NUMBER_OF_PASSES+str(self.sample.num_passes))
            details2_sizer.Add(num_passes_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            details2_sizer.AddSpacer(10)
        used_documents_label = wx.StaticText(self, label=GUIText.NUMBER_OF_DOCUMENTS+str(len(self.sample.tokensets)))
        details2_sizer.Add(used_documents_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        rules_button = wx.Button(self, label=FilteringGUIText.FILTERS_RULES)
        rules_button.Bind(wx.EVT_BUTTON, self.OnShowRules)
        details2_sizer.Add(rules_button, 0, wx.ALL, 5)
        includefields_button = wx.Button(self, label=FilteringGUIText.INCLUDEDFIELDS)
        includefields_button.Bind(wx.EVT_BUTTON, self.OnShowIncludedFields)
        details2_sizer.Add(includefields_button, 0, wx.ALL, 5)
        topic_list_sizer.Add(details2_sizer, 0, wx.ALL, 5)

        topic_list_label1 = wx.StaticText(self, label=GUIText.WORDS_PER_TOPIC1)
        self.topic_list_num = wx.SpinCtrl(self, min=1, max=100, initial=10)
        topic_list_label2 = wx.StaticText(self, label=GUIText.WORDS_PER_TOPIC2)
        topic_list_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        topic_list_label_sizer.Add(topic_list_label1, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        topic_list_label_sizer.Add(self.topic_list_num, 0, wx.ALL, 5)
        topic_list_label_sizer.Add(topic_list_label2, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)

        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        self.merge_topics_tool = self.toolbar.AddTool(wx.ID_ANY,
                                                      label=GUIText.MERGE_TOPIC_LABEL,
                                                      bitmap=wx.Bitmap(1, 1),
                                                      shortHelp=GUIText.MERGE_TOPIC_SHORTHELP)
        self.split_topics_tool = self.toolbar.AddTool(wx.ID_ANY,
                                                      label=GUIText.SPLIT_TOPIC_LABEL,
                                                      bitmap=wx.Bitmap(1, 1),
                                                      shortHelp=GUIText.SPLIT_TOPIC_SHORTHELP)
        self.remove_topics_tool = self.toolbar.AddTool(wx.ID_ANY,
                                                      label=GUIText.REMOVE_TOPIC_LABEL,
                                                      bitmap=wx.Bitmap(1, 1),
                                                      shortHelp=GUIText.REMOVE_TOPIC_SHORTHELP)
        self.toolbar.Realize()
        topic_list_label_sizer.Add(self.toolbar, proportion=0, flag=wx.ALL, border=5)

        cutoff_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cutoff_label = wx.StaticText(self, label=GUIText.PROBABILITY_CUTOFF_LABEL)
        #self.cutoff_slider = wx.Slider(self, value=int(sample.document_cutoff*1000), minValue=0, maxValue=1000,
        #                               style = wx.SL_HORIZONTAL)
        #self.cutoff_slider.SetToolTip("Include documents in a topic when the probability of the topic being present in the document is greater or equal to the cutoff")
        #cutoff_sizer.Add(self.cutoff_slider, 1, wx.EXPAND)
        self.cutoff_spin = wx.SpinCtrlDouble(self, initial=sample.document_cutoff, min=0.0, max=1.0)
        self.cutoff_spin.SetDigits(2)
        self.cutoff_spin.SetIncrement(0.01)
        self.cutoff_spin.SetToolTip(GUIText.PROBABILITY_CUTOFF_TOOLTIP)
        cutoff_sizer.Add(cutoff_label, 0, wx.ALIGN_CENTER)
        cutoff_sizer.Add(self.cutoff_spin, 0, wx.ALIGN_CENTER)
        topic_list_label_sizer.Add(cutoff_sizer, proportion=0, flag=wx.ALL, border=5)

        topic_list_sizer.Add(topic_list_label_sizer, 0, wx.ALL, 5)
        
        self.topic_list_model = SamplesDataViews.TopicViewModel(sample.parts_dict.values())
        self.topic_list_ctrl = SamplesDataViews.TopicViewCtrl(self, self.topic_list_model)
        topic_list_sizer.Add(self.topic_list_ctrl, 1, wx.EXPAND)

        self.SetSizer(topic_list_sizer)
        logger.info("Finished")
    
    def OnShowRules(self, event):
        logger = logging.getLogger(__name__+".TopicListPanel["+str(self.sample.key)+"].OnShowRules")
        logger.info("Starting")
        SampleRulesDialog(self, self.sample, self.dataset).Show()
        logger.info("Finished")

    def OnShowIncludedFields(self, event):
        logger = logging.getLogger(__name__+".TopicListPanel["+str(self.sample.key)+"].OnShowIncludedFields")
        logger.info("Starting")
        SampleIncludedFieldsDialog(self, self.sample, self.dataset).Show()
        logger.info("Finished")

class LDAModelCreateDialog(wx.Dialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".LDAModelCreateDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.CREATE_LDA)

        self.model_parameters = {}

        sizer = wx.BoxSizer(wx.VERTICAL)

        name_label = wx.StaticText(self, label=GUIText.NAME+":")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        name_sizer.Add(self.name_ctrl, 0, wx.ALL, 5)
        sizer.Add(name_sizer)

        #need to only show tokensets that have fields containing data
        self.usable_datasets = []
        main_frame = wx.GetApp().GetTopWindow()
        for dataset in main_frame.datasets.values():
            if len(dataset.included_fields) > 0:
                self.usable_datasets.append(dataset.key)
        if len(self.usable_datasets) > 1: 
            dataset_label = wx.StaticText(self, label=GUIText.DATASET+":")
            usable_datasets_strings = [str(dataset_key) for dataset_key in self.usable_datasets]
            self.dataset_ctrl = wx.Choice(self, choices=usable_datasets_strings)
            dataset_sizer = wx.BoxSizer(wx.HORIZONTAL)
            dataset_sizer.Add(dataset_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            dataset_sizer.Add(self.dataset_ctrl, 0, wx.ALL, 5)
            sizer.Add(dataset_sizer)

        num_topics_label = wx.StaticText(self, label=GUIText.NUMBER_OF_TOPICS_CHOICE)
        self.num_topics_ctrl = wx.SpinCtrl(self, min=1, max=10000, initial=10)
        self.num_topics_ctrl.SetToolTip(GUIText.NUMBER_OF_TOPICS_TOOLTIP)
        num_topics_sizer = wx.BoxSizer(wx.HORIZONTAL)
        num_topics_sizer.Add(num_topics_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        num_topics_sizer.Add(self.num_topics_ctrl, 0, wx.ALL, 5)
        sizer.Add(num_topics_sizer)

        num_passes_label = wx.StaticText(self, label=GUIText.NUMBER_OF_PASSES_CHOICE)
        self.num_passes_ctrl = wx.SpinCtrl(self, min=1, max=1000, initial=100)
        self.num_passes_ctrl.SetToolTip(GUIText.NUMBER_OF_PASSES_TOOLTIP)
        num_passes_sizer = wx.BoxSizer(wx.HORIZONTAL)
        num_passes_sizer.Add(num_passes_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        num_passes_sizer.Add(self.num_passes_ctrl, 0, wx.ALL, 5)
        sizer.Add(num_passes_sizer)

        #fields to choose specific fields for model
        #--- not part of mvp so default is to use all fields

        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK, )
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label=GUIText.CANCEL)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.Add(ok_button)
        controls_sizer.Add(cancel_button)
        sizer.Add(controls_sizer)

        self.SetSizer(sizer)
        
        self.Layout()
        self.Fit()
        logger.info("Finished")

    def OnOK(self, event):
        logger = logging.getLogger(__name__+".LDAModelCreateDialog.OnOK")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        #check that name exists and is unique
        status_flag = True

        model_name = self.name_ctrl.GetValue()
        model_name = model_name.replace(" ", "_")
        model_name = model_name.lower()
        if model_name != "":
            if model_name in main_frame.samples:
                wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('name[%s] is not unique', model_name)
                status_flag = False
        else:
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('name field is empty')
            status_flag = False

        if len(self.usable_datasets) > 1:
            dataset_id = self.dataset_ctrl.GetSelection()
            if dataset_id is wx.NOT_FOUND:
                wx.MessageBox(GUIText.DATASET_MISSING_ERROR,
                            GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('dataset was not chosen')
                status_flag = False
        elif len(self.usable_datasets) == 1:
            dataset_id = 0
        else:
            wx.MessageBox(GUIText.DATASET_NOTAVALIABLE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('no dataset available')
            status_flag = False

        if status_flag:
            self.model_parameters['name'] = model_name
            self.model_parameters['dataset_key'] = self.usable_datasets[dataset_id]
            self.model_parameters['num_topics'] = self.num_topics_ctrl.GetValue()
            self.model_parameters['num_passes'] = self.num_passes_ctrl.GetValue()
            self.model_parameters['alpha'] = None
            self.model_parameters['eta'] = None
        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)

class BitermModelCreateDialog(wx.Dialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".BiTermModelCreateDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.CREATE_BITERM)

        self.model_parameters = {}

        sizer = wx.BoxSizer(wx.VERTICAL)

        name_label = wx.StaticText(self, label=GUIText.NAME+":")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        name_sizer.Add(self.name_ctrl, 0, wx.ALL, 5)
        sizer.Add(name_sizer)

        #need to only show tokensets that have fields containing data
        self.usable_datasets = []
        
        main_frame = wx.GetApp().GetTopWindow()
        for dataset in main_frame.datasets.values():
            if len(dataset.included_fields) > 0:
                self.usable_datasets.append(dataset.key)
        if len(self.usable_datasets) > 1: 
            dataset_label = wx.StaticText(self, label=GUIText.DATASET+":")
            usable_datasets_strings = [str(dataset_key) for dataset_key in self.usable_datasets]
            self.dataset_ctrl = wx.Choice(self, choices=usable_datasets_strings)
            dataset_sizer = wx.BoxSizer(wx.HORIZONTAL)
            dataset_sizer.Add(dataset_label)
            dataset_sizer.Add(self.dataset_ctrl)
            sizer.Add(dataset_sizer)

        num_topics_label = wx.StaticText(self, label=GUIText.NUMBER_OF_TOPICS_CHOICE)
        self.num_topics_ctrl = wx.SpinCtrl(self, min=1, max=10000, initial=10)
        self.num_topics_ctrl.SetToolTip(GUIText.NUMBER_OF_TOPICS_TOOLTIP)
        num_topics_sizer = wx.BoxSizer(wx.HORIZONTAL)
        num_topics_sizer.Add(num_topics_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        num_topics_sizer.Add(self.num_topics_ctrl, 0, wx.ALL, 5)
        sizer.Add(num_topics_sizer)

        num_passes_label = wx.StaticText(self, label=GUIText.NUMBER_OF_PASSES_CHOICE)
        self.num_passes_ctrl = wx.SpinCtrl(self, min=1, max=1000, initial=100)
        self.num_passes_ctrl.SetToolTip(GUIText.NUMBER_OF_PASSES_TOOLTIP)
        num_passes_sizer = wx.BoxSizer(wx.HORIZONTAL)
        num_passes_sizer.Add(num_passes_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        num_passes_sizer.Add(self.num_passes_ctrl, 0, wx.ALL, 5)
        sizer.Add(num_passes_sizer)

        #fields to choose specific fields for model
        #--- not part of mvp so default is to use all fields

        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK, )
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label=GUIText.CANCEL)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.Add(ok_button)
        controls_sizer.Add(cancel_button)
        sizer.Add(controls_sizer)

        self.SetSizer(sizer)
        
        self.Layout()
        self.Fit()
        logger.info("Finished")

    def OnOK(self, event):
        logger = logging.getLogger(__name__+".BiTermModelCreateDialog.OnOK")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        #check that name exists and is unique
        status_flag = True

        model_name = self.name_ctrl.GetValue()
        model_name = model_name.replace(" ", "_")
        model_name = model_name.lower()
        if model_name != "":
            if model_name in main_frame.samples:
                wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('name[%s] is not unique', model_name)
                status_flag = False
        else:
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('name field is empty')
            status_flag = False

        if len(self.usable_datasets) > 1:
            dataset_id = self.dataset_ctrl.GetSelection()
            if dataset_id is wx.NOT_FOUND:
                wx.MessageBox(GUIText.DATASET_MISSING_ERROR,
                            GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('dataset was not chosen')
                status_flag = False
        elif len(self.usable_datasets) == 1:
            dataset_id = 0
        else:
            wx.MessageBox(GUIText.DATASET_NOTAVALIABLE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('no dataset available')
            status_flag = False

        if status_flag:
            self.model_parameters['name'] = model_name
            self.model_parameters['dataset_key'] = self.usable_datasets[dataset_id]
            self.model_parameters['num_topics'] = self.num_topics_ctrl.GetValue()
            self.model_parameters['num_passes'] = self.num_passes_ctrl.GetValue()
        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)

class NMFModelCreateDialog(wx.Dialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".NMFModelCreateDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.CREATE_NMF)

        self.model_parameters = {}

        sizer = wx.BoxSizer(wx.VERTICAL)

        name_label = wx.StaticText(self, label=GUIText.NAME+":")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label, 0, wx.ALL, 5)
        name_sizer.Add(self.name_ctrl, 0, wx.ALL, 5)
        sizer.Add(name_sizer)

        #need to only show tokensets that have fields containing data
        self.usable_datasets = []
        
        main_frame = wx.GetApp().GetTopWindow()
        for dataset in main_frame.datasets.values():
            if len(dataset.included_fields) > 0:
                self.usable_datasets.append(dataset.key)
        if len(self.usable_datasets) > 1: 
            dataset_label = wx.StaticText(self, label=GUIText.DATASET+":")
            usable_datasets_strings = [str(dataset_key) for dataset_key in self.usable_datasets]
            self.dataset_ctrl = wx.Choice(self, choices=usable_datasets_strings)
            dataset_sizer = wx.BoxSizer(wx.HORIZONTAL)
            dataset_sizer.Add(dataset_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
            dataset_sizer.Add(self.dataset_ctrl, 0, wx.ALL, 5)
            sizer.Add(dataset_sizer)

        num_topics_label = wx.StaticText(self, label=GUIText.NUMBER_OF_TOPICS_CHOICE)
        self.num_topics_ctrl = wx.SpinCtrl(self, min=1, max=10000, initial=10)
        self.num_topics_ctrl.SetToolTip(GUIText.NUMBER_OF_TOPICS_TOOLTIP)
        num_topics_sizer = wx.BoxSizer(wx.HORIZONTAL)
        num_topics_sizer.Add(num_topics_label, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        num_topics_sizer.Add(self.num_topics_ctrl, 0, wx.ALL, 5)
        sizer.Add(num_topics_sizer)

        #fields to choose specific fields for model
        #--- not part of mvp so default is to use all fields

        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK, )
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label=GUIText.CANCEL)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.Add(ok_button)
        controls_sizer.Add(cancel_button)
        sizer.Add(controls_sizer)

        self.SetSizer(sizer)
        
        self.Layout()
        self.Fit()
        logger.info("Finished")

    def OnOK(self, event):
        logger = logging.getLogger(__name__+".NMFModelCreateDialog.OnOK")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        #check that name exists and is unique
        status_flag = True

        model_name = self.name_ctrl.GetValue()
        model_name = model_name.replace(" ", "_")
        model_name = model_name.lower()
        if model_name != "":
            if model_name in main_frame.samples:
                wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('name[%s] is not unique', model_name)
                status_flag = False
        else:
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('name field is empty')
            status_flag = False

        if len(self.usable_datasets) > 1:
            dataset_id = self.dataset_ctrl.GetSelection()
            if dataset_id is wx.NOT_FOUND:
                wx.MessageBox(GUIText.DATASET_MISSING_ERROR,
                            GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('dataset was not chosen')
                status_flag = False
        elif len(self.usable_datasets) == 1:
            dataset_id = 0
        else:
            wx.MessageBox(GUIText.DATASET_NOTAVALIABLE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('no dataset available')
            status_flag = False

        if status_flag:
            self.model_parameters['name'] = model_name
            self.model_parameters['dataset_key'] = self.usable_datasets[dataset_id]
            self.model_parameters['num_topics'] = self.num_topics_ctrl.GetValue()
        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)
