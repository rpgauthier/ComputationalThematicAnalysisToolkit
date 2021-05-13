'''Token Filtering Sub Module'''
import logging
import json
from datetime import datetime

import jsonpickle
import nltk
import spacy
import spacy.lang.en.stop_words
import pandas as pd

import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB
import wx.lib.scrolledpanel
from wx.lib.masked.numctrl import NumCtrl
import wx.dataview as dv

import Common.Constants as Constants
import Common.Objects.DataViews.Tokens as TokenDataViews
import Common.Objects.Datasets as Datasets
import Common.CustomEvents as CustomEvents
from Common.GUIText import Familiarization as GUIText
import Familiarization.FamiliarizationThreads as FamiliarizationThreads

class TokenFiltersNotebook(FNB.FlatNotebook):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".TokenFiltersNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)

        #create dictionary to hold instances of filter panels for each field avaliable
        self.filters = {}

        self.menu = wx.Menu()
        self.menu_menuitem = None

        self.Fit()

        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".TokenFiltersNotebook.RefreshFilters")
        logger.info("Starting")

        def CleanupFilter(filter_key):
            index = self.GetPageIndex(self.filters[filter_key])
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
                self.menu.Remove(self.filters[filter_key].menu_menuitem)
            self.filters[filter_key].Hide()
            del self.filters[filter_key]

        #cleanup fields that no longer exist
        for filter_key in list(self.filters.keys()):
            CleanupFilter(filter_key)

        def AddOrUpdateFilter(key, field):
            filters_key = (key, field.key)
            if filters_key in self.filters:
                self.filters[filters_key].DataRefreshStart()
            else:
                if len(field.tokenset) > 0:
                    name = str(key) + ": "+ str(field.key)
                    self.filters[filters_key] = FilterPanel(self, name, field, size=self.GetSize())
                    self.filters[filters_key].DataRefreshStart()
                    self.AddPage(self.filters[filters_key], name)
                    self.filters[filters_key].menu_menuitem = self.menu.AppendSubMenu(self.filters[filters_key].menu, name)

        def UpdateDataset(key, dataset):
            for field_name in dataset.chosen_fields:
                AddOrUpdateFilter(key, dataset.chosen_fields[field_name])
            for field_name in dataset.merged_fields:
                AddOrUpdateFilter(key, dataset.merged_fields[field_name])

        def UpdateGroupedDataset(grouped_dataset):
            for dataset_key in grouped_dataset.datasets:
                UpdateDataset((grouped_dataset.key, dataset_key), grouped_dataset.datasets[dataset_key])
            for field_name in grouped_dataset.merged_fields:
                AddOrUpdateFilter((grouped_dataset.key,), grouped_dataset.merged_fields[field_name])

        #Create new filters as needed and update existing filters
        main_frame = wx.GetApp().GetTopWindow()
        for key in main_frame.datasets:
            if isinstance(main_frame.datasets[key], Datasets.Dataset):
                UpdateDataset((key,), main_frame.datasets[key])
            elif isinstance(main_frame.datasets[key], Datasets.GroupedDataset):
                UpdateGroupedDataset(main_frame.datasets[key])
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".TokenFiltersNotebook.Load")
        logger.info("Starting")
        #load all filter panels
        for filter_key in self.filters:
            self.filters[filter_key].Load(saved_data['filters'][filter_key])

        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".TokenFiltersNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['filters'] = {}
        for filter_key in self.filters:
            saved_data['filters'][filter_key] = self.filters[filter_key].Save()
        logger.info("Finished")
        return saved_data

class FilterPanel(wx.Panel):
    def __init__(self, parent, name, field, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FilterPanel["+str(name)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        #link to find the associated field object from the datasets
        self.name = name
        self.field = field
        #thread used to generate dataframes for use when display lists
        self.thread = None

        #need to be views of field object or moved into field object
        self.words_df = pd.DataFrame()

        top_splitter = wx.SplitterWindow(self, size=self.GetSize(), style=wx.SP_BORDER)
        vertical_splitter = wx.SplitterWindow(top_splitter, style=wx.SP_BORDER)

        self.included_words_panel = IncludedWordsPanel(vertical_splitter, self,  style=wx.TAB_TRAVERSAL)
        self.removed_words_panel = RemovedWordsPanel(vertical_splitter, self, style=wx.TAB_TRAVERSAL) 
        self.rules_panel = RulesPanel(top_splitter, self, style=wx.TAB_TRAVERSAL)
        
        vertical_splitter.SetMinimumPaneSize(20)
        vertical_splitter.SetSashPosition(int(self.GetSize().GetWidth()/2))
        vertical_splitter.SplitVertically(self.included_words_panel, self.removed_words_panel)
        
        top_splitter.SetMinimumPaneSize(20)
        top_splitter.SetSashPosition(int(self.GetSize().GetHeight()/2))
        top_splitter.SplitHorizontally(vertical_splitter, self.rules_panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(top_splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        #create the menu for the filter
        main_frame = wx.GetApp().GetTopWindow()
        self.menu = wx.Menu()
        self.menu_menuitem = None
        importNLTKStopWordsItem = self.menu.Append(wx.ID_ANY,
                                                   GUIText.FILTERS_IMPORT_NLTK,
                                                   GUIText.FILTERS_IMPORT_NLTK_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnImportNLTKStopWords, importNLTKStopWordsItem)
        importSpacyStopWordsItem = self.menu.Append(wx.ID_ANY,
                                                    GUIText.FILTERS_IMPORT_SPACY,
                                                    GUIText.FILTERS_IMPORT_SPACY_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnImportSpacyStopWords, importSpacyStopWordsItem)
        self.menu.AppendSeparator()
        importRemovalSettingsItem = self.menu.Append(wx.ID_ANY,
                                                     GUIText.FILTERS_IMPORT,
                                                     GUIText.FILTERS_IMPORT_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnImportRemovalSettings, importRemovalSettingsItem)
        exportRemovalSettingsItem = self.menu.Append(wx.ID_ANY,
                                                     GUIText.FILTERS_EXPORT,
                                                     GUIText.FILTERS_EXPORT_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnExportRemovalSettings, exportRemovalSettingsItem)

        #event end points for completed threads
        CustomEvents.CREATE_WORD_DATAFRAME_EVT_RESULT(self, self.OnDataRefreshEnd)
        CustomEvents.APPLY_FILTER_RULES_EVT_RESULT(self, self.OnUpdateWordListsEnd)
        logger.info("Finished")

    ######
    #functions called by the interface
    ######

    def OnRemoveEntry(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveEntry")
        logger.info("Starting")
        selection = self.included_words_panel.panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.included_words_panel.words_list.GetCellValue(row, 0)
                pos = self.included_words_panel.words_list.GetCellValue(row, 1)
                self.field.AddFilterRule((word, pos, Constants.FILTER_RULE_REMOVE))
            self.rules_panel.DisplayFilterRules(self.field.filter_rules)
            self.UpdateWordListsStart()
        logger.info("Finished")

    def OnReaddEntry(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnReaddEntry")
        logger.info("Starting")
        selection = self.removed_words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.removed_words_list.GetCellValue(row, 0)
                pos = self.removed_words_list.GetCellValue(row, 1)
                self.field.AddFilterRule((word, pos, Constants.FILTER_RULE_INCLUDE))
            self.rules_panel.DisplayFilterRules(self.field.filter_rules)
            self.UpdateWordListsStart()
        logger.info("Finished")

    def OnRemoveWord(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveWord")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.included_words_panel.words_list.GetCellValue(row, 0)
                self.field.AddFilterRule((word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
            self.rules_panel.DisplayFilterRules(self.field.filter_rules)
            self.UpdateWordListsStart()
        logger.info("Finished")

    def OnReaddWord(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnReaddWord")
        logger.info("Starting")
        selection = self.removed_words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.removed_words_list.GetCellValue(row, 0)
                self.field.AddFilterRule((word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_INCLUDE))
            self.rules_panel.DisplayFilterRules(self.field.filter_rules)
            self.UpdateWordListsStart()
        logger.info("Finished")

    def OnRemovePOS(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemovePOS")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                pos = self.included_words_panel.words_list.GetCellValue(row, 1)
                self.field.AddFilterRule((Constants.FILTER_RULE_ANY, pos, Constants.FILTER_RULE_REMOVE))
            self.rules_panel.DisplayFilterRules(self.field.filter_rules)
            self.UpdateWordListsStart()
        logger.info("Finished")

    def OnReaddPOS(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnReaddPOS")
        logger.info("Starting")
        selection = self.removed_words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                pos = self.removed_words_list.GetCellValue(row, 1)
                self.field.AddFilterRule((Constants.FILTER_RULE_ANY, pos, Constants.FILTER_RULE_INCLUDE))
            self.rules_panel.DisplayFilterRules(self.field.filter_rules)
            self.UpdateWordListsStart()
        logger.info("Finished")
    
    def OnRemoveSpacyAutoStopword(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnSpacyAutoStopword")
        logger.info("Starting")
        self.field.AddFilterRule((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS))
        self.rules_panel.DisplayFilterRules(self.field.filter_rules)
        self.UpdateWordListsStart()
        logger.info("Finished")
    
    def OnCreateCountFilter(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnCreateCountFilter")
        logger.info("Starting")
        #custom dialog to choose direction (greater or less), number, and words or docs
        with CreateCountFilterDialog(self) as create_dialog:
            if create_dialog.ShowModal() == wx.ID_OK:
                rule = (create_dialog.action,
                        create_dialog.column,
                        create_dialog.operation,
                        create_dialog.number,)
                self.field.AddFilterRule((create_dialog.word, create_dialog.pos, rule))
                self.rules_panel.DisplayFilterRules(self.field.filter_rules)
                self.UpdateWordListsStart()
        logger.info("Finished")
    
    def OnCreateTfidfFilter(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnCreateTfidfFilter")
        logger.info("Starting")
        with CreateTfidfFilterDialog(self) as create_dialog:
            if create_dialog.ShowModal() == wx.ID_OK:
                rule = (create_dialog.action1,
                        create_dialog.action2,
                        create_dialog.rank,)
                self.field.AddFilterRule((create_dialog.word, create_dialog.pos, rule))
                self.rules_panel.DisplayFilterRules(self.field.filter_rules)
                self.UpdateWordListsStart()
        logger.info("Finished")


    def OnRemoveRule(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveRule")
        logger.info("Starting")
        flag = False
        for item in reversed(self.rules_panel.rules_list.GetSelections()):
            row = self.rules_panel.rules_list.ItemToRow(item)
            index = self.rules_panel.rules_list.GetValue(row, 0) - 1
            del self.field.filter_rules[index]
            self.field.last_changed_dt = datetime.now()
            flag = True
        self.rules_panel.DisplayFilterRules(self.field.filter_rules)
        self.UpdateWordListsStart()
        logger.info("Finished")
    
    def OnMoveRuleUp(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnMoveRuleUp")
        logger.info("Starting")
        for item in reversed(self.rules_panel.rules_list.GetSelections()):
            row = self.rules_panel.rules_list.ItemToRow(item)
            index = self.rules_panel.rules_list.GetValue(row, 0)
            if index < len(self.field.filter_rules):
                self.field.filter_rules[index], self.field.filter_rules[index-1] = self.field.filter_rules[index-1], self.field.filter_rules[index]
                self.field.last_changed_dt = datetime.now()
                self.rules_panel.DisplayFilterRules(self.field.filter_rules)
                self.UpdateWordListsStart()
            else:
                break
        logger.info("Finished")
    
    def OnMoveRuleDown(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnMoveRuleDown")
        logger.info("Starting")
        for item in self.rules_panel.rules_list.GetSelections():
            row = self.rules_panel.rules_list.ItemToRow(item)
            index = self.rules_panel.rules_list.GetValue(row, 0)
            if index > 1:
                self.field.filter_rules[index-2], self.field.filter_rules[index-1] = self.field.filter_rules[index-1], self.field.filter_rules[index-2]
                self.field.last_changed_dt = datetime.now()
                self.rules_panel.DisplayFilterRules(self.field.filter_rules)
                self.UpdateWordListsStart()
            else:
                break
        logger.info("Finished")

    def OnImportNLTKStopWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportNLTKStopWords")
        logger.info("Starting")
        nltk_stopwords = set(nltk.corpus.stopwords.words('english'))
        for word in nltk_stopwords:
            self.field.AddFilterRule((word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
        self.rules_panel.DisplayFilterRules(self.field.filter_rules)
        self.UpdateWordListsStart()
        logger.info("Finished")

    def OnImportSpacyStopWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportSpacyStopWords")
        logger.info("Starting")
        spacy_stopwords = spacy.lang.en.stop_words.STOP_WORDS
        for word in spacy_stopwords:
            self.field.AddFilterRule((word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
        self.rules_panel.DisplayFilterRules(self.field.filter_rules)
        self.UpdateWordListsStart()
        logger.info("Finished")
 
    def OnImportRemovalSettings(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportRemovalSettings")
        logger.info("Starting")
        if wx.MessageBox(GUIText.FILTERS_IMPORT_CONFIRMATION_REQUEST,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
            # otherwise ask the user what new file to open
            with wx.FileDialog(self, GUIText.FILTERS_IMPORT, defaultDir='../Workspaces/',
                            wildcard="JSON files (*.json)|*.json",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                # cancel if the user changed their mind
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                # Proceed loading the file chosen by the user
                pathname = file_dialog.GetPath()
                try:
                    with open(pathname, 'r') as file:
                        self.field.filter_rules = jsonpickle.decode(json.load(file))
                        self.field.last_changed_dt = datetime.now()
                except IOError:
                    wx.LogError("Cannot open file '%s'", self.saved_name)
                    logger.error("Failed to open file '%s'", self.saved_name)
            self.rules_panel.DisplayFilterRules(self.field.filter_rules)
            self.UpdateWordListsStart()
        logger.info("Finished")

    def OnExportRemovalSettings(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnExportRemovalSettings")
        logger.info("Starting")
        with wx.FileDialog(self, GUIText.FILTERS_EXPORT, defaultDir='../Workspaces/',
                           wildcard="JSON files (*.json)|*.json",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            # cancel if the user changed their mind
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            # save the current contents in the file
            pathname = file_dialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    json.dump(jsonpickle.encode(self.field.filter_rules), file)
            except IOError:
                wx.LogError("Cannot save current removal settings '%s'", self.saved_name)
                logger.error("Failed to save removal to file '%s'", self.saved_name)
        logger.info("Finished")

    def OnTokenizationChoice(self, event):
        choice = self.rules_panel.tokenization_choice.GetSelection()
        if choice != self.field.tokenization_choice:
            self.field.tokenization_choice = choice
            self.DataRefreshStart()


    ######
    #functions called to complete operation of other functions
    ######

    def DataRefreshStart(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].DataRefresh")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        main_frame.CreateProgressDialog(title=GUIText.FILTERS_REFRESH_BUSY_LABEL+str(self.name),
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        main_frame.PulseProgressDialog(GUIText.FILTERS_REFRESH_BUSY_MSG+str(self.name))
        word_idx = self.field.tokenization_choice
        self.thread = FamiliarizationThreads.CreateWordDataFrameThread(self, self.field.tokenset, word_idx)
        logger.info("Finished")


    def OnDataRefreshEnd(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].DataRefreshEnd")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.thread.join()
        self.thread = None
        self.words_df = event.data['words_df']
        self.rules_panel.DisplayFilterRules(self.field.filter_rules)
        self.UpdateWordListsStart()
        main_frame.CloseProgressDialog(thaw=False)
        self.Thaw()
        logger.info("Finished")

    def UpdateWordListsStart(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].UpdateWordListsStart")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        main_frame.CreateProgressDialog(GUIText.FILTERS_RELOAD_BUSY_LABEL+str(self.name),
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        main_frame.PulseProgressDialog(GUIText.FILTERS_RELOAD_BUSY_MSG+str(self.name))
        word_idx = self.field.tokenization_choice
        self.thread = FamiliarizationThreads.ApplyFilterRulesThread(self, word_idx, self.words_df, self.field.filter_rules)

        logger.info("Finished")
    
    def OnUpdateWordListsEnd(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].UpdateWordListsStart")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.thread.join()
        self.thread = None
        self.included_words_panel.UpdateWords(event.data['included_words_df'])
        self.removed_words_panel.UpdateWords(event.data['removed_words_df'])
        self.field.included_tokenset_df = event.data['included_words_df']
        main_frame.CloseProgressDialog(thaw=False)
        self.Thaw()
        logger.info("Finished")


    #Required Functions
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].Load")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_FIELD_BUSY_MSG+str(self.name))

        self.rules_panel.tokenization_choice.SetSelection(self.field.tokenization_choice)

        if 'included_search_word' in saved_data:
            self.included_words_panel.word_searchctrl.SetValue(saved_data['included_search_word'])
        if 'included_search_pos' in saved_data:
            self.included_words_panel.pos_searchctrl.SetValue(saved_data['included_search_pos'])
        if 'removed_search_word' in saved_data:
            self.removed_words_panel.word_searchctrl.SetValue(saved_data['removed_search_word'])
        if 'removed_search_pos' in saved_data:
            self.removed_words_panel.pos_searchctrl.SetValue(saved_data['removed_search_pos'])
        
        #if saved_data['included_search_word'] != '' or saved_data['included_search_pos'] != '':
        #    self.included_words_panel.OnSearch(None)
        #if saved_data['removed_search_word'] != '' or saved_data['removed_search_pos'] != '':
        #    self.removed_words_panel.OnSearch(None)
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].Save")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_FIELD_BUSY_MSG+str(self.name))
        saved_data = {}
        saved_data['included_search_word'] = self.included_words_panel.word_searchctrl.GetValue()
        saved_data['included_search_pos'] = self.included_words_panel.pos_searchctrl.GetValue()
        saved_data['removed_search_word'] = self.removed_words_panel.word_searchctrl.GetValue()
        saved_data['removed_search_pos'] = self.removed_words_panel.pos_searchctrl.GetValue()
        logger.info("Finished")
        return saved_data

class WordsPanel(wx.Panel):
    def __init__(self, parent, parent_frame, word_type, style):
        logger = logging.getLogger(__name__+".WordsPanel["+word_type+"]["+str(parent_frame.name)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, style=style)
        self.parent_frame = parent_frame 
        self.word_type = word_type

        
        self.col_names = [GUIText.FILTERS_WORDS,
                          GUIText.FILTERS_POS,
                          GUIText.FILTERS_NUM_WORDS,
                          GUIText.FILTERS_PER_WORDS,
                          GUIText.FILTERS_NUM_DOCS,
                          GUIText.FILTERS_PER_DOCS,
                          GUIText.FILTERS_SPACY_AUTO_STOPWORDS,
                          GUIText.FILTERS_TFIDF]

        self.words_df = pd.DataFrame(columns=self.col_names)
        self.search_filter = None

        #setup the included entries panel
        #self.SetScrollbars(1, 1, 1, 1)
        #border and Label for area
        self.label_box = wx.StaticBox(self, label="")
        label_font = wx.Font(Constants.LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, underline=Constants.LABEL_UNDERLINE)
        self.label_box.SetFont(label_font)
        sizer = wx.StaticBoxSizer(self.label_box, wx.VERTICAL)
        #create the toolbar
        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_HORZ_TEXT|wx.TB_NOICONS)
        self.word_searchctrl = wx.SearchCtrl(self.toolbar)
        self.word_searchctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.word_searchctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.word_searchctrl.SetDescriptiveText("Word Search")
        self.word_searchctrl.ShowCancelButton(True)
        self.toolbar.AddControl(self.word_searchctrl)
        self.pos_searchctrl = wx.SearchCtrl(self.toolbar)
        self.pos_searchctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.pos_searchctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.pos_searchctrl.SetDescriptiveText("Part of Speach Search")
        self.pos_searchctrl.ShowCancelButton(True)
        self.toolbar.AddControl(self.pos_searchctrl)
        self.toolbar.AddSeparator()
        self.toolbar.Realize()
        sizer.Add(self.toolbar, proportion=0, flag=wx.ALL, border=5)
        #create the list to be shown
        self.words_list = TokenDataViews.TokenGrid(self, self.words_df)
        sizer.Add(self.words_list, proportion=1, flag=wx.EXPAND, border=5)

        border = wx.BoxSizer()
        border.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(border)
        logger.info("Finished")

    def OnSearch(self, event):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].OnSearch")
        logger.info("Starting")
        word_idx = self.parent_frame.field.tokenization_choice
        word_search_term = self.word_searchctrl.GetValue()
        pos_search_term = self.pos_searchctrl.GetValue()
        if word_search_term != '' and pos_search_term != '':
            self.search_filter = self.tokens_df[word_idx].str.contains(word_search_term, regex=False) & self.tokens_df[Constants.TOKEN_POS_IDX].str.contains(pos_search_term, regex=False)
        elif word_search_term != '':
            self.search_filter = self.tokens_df[word_idx].str.contains(word_search_term, regex=False)
        elif pos_search_term != '':
            self.search_filter = self.tokens_df[Constants.TOKEN_POS_IDX].str.contains(pos_search_term, regex=False)
        else:
            self.search_filter = None
        self.DisplayWordsList()
        logger.info("Finished")

    def OnSearchCancel(self, event):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].OnSearchCancel")
        logger.info("Starting")
        search_ctrl = event.GetEventObject()
        search_ctrl.SetValue("")
        self.OnSearch(event)
        logger.info("Finished")

    def UpdateWords(self, new_words_df):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].UpdateWords")
        logger.info("Starting")
        self.tokens_df = new_words_df
        self.DisplayWordsList()
        logger.info("Finished")

    def DisplayWordsList(self):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].DisplayWordsList")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        main_frame.CreateProgressDialog(GUIText.FILTERS_DISPLAY_BUSY_LABEL+str(self.parent_frame.name)+" "+self.word_type,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        main_frame.PulseProgressDialog(GUIText.FILTERS_DISPLAY_BUSY_MSG+str(self.parent_frame.name)+" "+self.word_type)
        try:
            if self.search_filter is not None:
                searched_df = self.tokens_df[self.search_filter]
            else:
                searched_df = self.tokens_df

            word_idx = self.parent_frame.field.tokenization_choice

            self.words_df = searched_df[[word_idx,
                                      Constants.TOKEN_POS_IDX,
                                      Constants.TOKEN_NUM_WORDS,
                                      Constants.TOKEN_PER_WORDS,
                                      Constants.TOKEN_NUM_DOCS,
                                      Constants.TOKEN_PER_DOCS,
                                      Constants.TOKEN_SPACY_STOPWORD_IDX,
                                      Constants.TOKEN_TFIDF]].copy()
            self.words_df.columns = self.col_names

            self.words_df.sort_values(by=[GUIText.FILTERS_NUM_WORDS], ascending=False, inplace=True)

            self.words_list.Update(self.words_df)
        finally:
            main_frame.CloseProgressDialog(thaw=False)
            self.Thaw()
        logger.info("Finished")


class IncludedWordsPanel(WordsPanel):
    def __init__(self, parent, parent_frame, style):
        logger = logging.getLogger(__name__+".IncludedWordsPanel["+str(parent_frame.name)+"]__init__")
        logger.info("Starting")
        WordsPanel.__init__(self, parent, parent_frame, "Included", style=style)
        self.label_box.SetLabel(GUIText.FILTERS_INCLUDED+GUIText.FILTERS_ENTRIES_LIST)
        #update the toolbar
        remove_entries_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_REMOVE_ENTRIES, bitmap=wx.Bitmap(1, 1),
                                                       shortHelp=GUIText.FILTERS_REMOVE_ENTRIES_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnRemoveEntry, remove_entries_tool)
        remove_words_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_REMOVE_WORDS, bitmap=wx.Bitmap(1, 1),
                                                     shortHelp=GUIText.FILTERS_REMOVE_WORDS_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnRemoveWord, remove_words_tool)
        remove_pos_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_REMOVE_POS, bitmap=wx.Bitmap(1, 1),
                                                   shortHelp=GUIText.FILTERS_REMOVE_POS_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnRemovePOS, remove_pos_tool)
        self.toolbar.Realize()
        logger.info("Finished")

class RemovedWordsPanel(WordsPanel):
    def __init__(self, parent, parent_frame, style):
        logger = logging.getLogger(__name__+".RemovedWordsPanel["+str(parent_frame.name)+"].__init__")
        logger.info("Starting")
        WordsPanel.__init__(self, parent, parent_frame, "Removed", style=style)
        self.label_box.SetLabel(GUIText.FILTERS_REMOVED+GUIText.FILTERS_ENTRIES_LIST)
        #update the toolbar
        readd_entries_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_READD_ENTRIES, bitmap=wx.Bitmap(1, 1),
                                                      shortHelp=GUIText.FILTERS_READD_ENTRIES_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnReaddEntry, readd_entries_tool)
        readd_words_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_READD_WORDS, bitmap=wx.Bitmap(1, 1),
                                                     shortHelp=GUIText.FILTERS_READD_WORDS_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnReaddWord, readd_words_tool)
        readd_pos_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_READD_POS, bitmap=wx.Bitmap(1, 1),
                                                   shortHelp=GUIText.FILTERS_READD_POS_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnReaddPOS, readd_pos_tool)
        self.toolbar.Realize()
        logger.info("Finished")

class RulesPanel(wx.Panel):
    '''For rendering nlp word data'''
    def __init__(self, parent, parent_frame, style):
        logger = logging.getLogger(__name__+".RulesPanel["+str(parent_frame.name)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, style=style)
        self.parent_frame = parent_frame
        #create the Rules tab
        #Label for area
        label_box = wx.StaticBox(self, label=GUIText.FILTERS_RULES)
        label_font = wx.Font(Constants.LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, underline=Constants.LABEL_UNDERLINE)
        label_box.SetFont(label_font)
        
        sizer = wx.StaticBoxSizer(label_box, wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_HORZ_TEXT|wx.TB_NOICONS)
        self.tokenization_choice = wx.Choice(self.toolbar, choices=Constants.TOKENIZER_APPROACH_LISTS[self.parent_frame.field.parent.language])
        self.tokenization_choice.SetSelection(self.parent_frame.field.tokenization_choice)
        self.tokenization_choice.Bind(wx.EVT_CHOICE, self.parent_frame.OnTokenizationChoice)
        self.tokenization_choice.SetSelection(0)
        self.toolbar.AddControl(self.tokenization_choice, "Tokenization Method:")
        remove_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.REMOVE,
                                           bitmap=wx.Bitmap(1, 1),
                                           shortHelp=GUIText.FILTERS_RULE_REMOVE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnRemoveRule, remove_tool)
        moveruledown_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_RULE_DECREASE,
                                                 bitmap=wx.Bitmap(1, 1),
                                                 shortHelp=GUIText.FILTERS_RULE_DECREASE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnMoveRuleDown, moveruledown_tool)
        moveruleup_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_RULE_INCREASE,
                                               bitmap=wx.Bitmap(1, 1),
                                               shortHelp=GUIText.FILTERS_RULE_INCREASE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnMoveRuleUp, moveruleup_tool)
        self.toolbar.AddSeparator()
        spacyautoremove_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_REMOVE_SPACY_AUTO_STOPWORDS,
                                                    bitmap=wx.Bitmap(1, 1),
                                                    shortHelp=GUIText.FILTERS_REMOVE_SPACY_AUTO_STOPWORDS_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnRemoveSpacyAutoStopword, spacyautoremove_tool)
        countfilter_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_CREATE_COUNT_RULE,
                                                bitmap=wx.Bitmap(1, 1),
                                                shortHelp=GUIText.FILTERS_CREATE_COUNT_RULE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnCreateCountFilter, countfilter_tool)
        tfidffilter_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_CREATE_TFIDF_RULE,
                                                bitmap=wx.Bitmap(1, 1),
                                                shortHelp=GUIText.FILTERS_CREATE_TFIDF_RULE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnCreateTfidfFilter, tfidffilter_tool)

        
        self.toolbar.Realize()
        sizer.Add(self.toolbar, proportion=0, flag=wx.ALL, border=5)
        self.rules_list = FilterRuleDataViewListCtrl(self)
        sizer.Add(self.rules_list, proportion=1, flag=wx.EXPAND, border=5)

        border = wx.BoxSizer()
        border.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(border)
        logger.info("Finished")

    def DisplayFilterRules(self, filter_rules):
        column_options = {Constants.TOKEN_NUM_WORDS:GUIText.FILTERS_NUM_WORDS,
                          Constants.TOKEN_PER_WORDS:GUIText.FILTERS_PER_WORDS,
                          Constants.TOKEN_NUM_DOCS:GUIText.FILTERS_NUM_DOCS,
                          Constants.TOKEN_PER_DOCS:GUIText.FILTERS_PER_DOCS}
        self.rules_list.DeleteAllItems()
        i = 1
        for word, pos, action in filter_rules:
            if isinstance(action, tuple):
                if action[0] == Constants.FILTER_TFIDF_REMOVE or action[0] == Constants.FILTER_TFIDF_INCLUDE:
                    action = str(action[0])+str(action[1])+str(action[2]*100)+"%"
                else:
                    action = str(action[0]) + " ("+str(column_options[action[1]])+str(action[2])+str(action[3])+")"
                
            self.rules_list.AppendItem([i, word, pos, str(action)])
            i += 1

class FilterRuleDataViewListCtrl(dv.DataViewListCtrl):
    '''For rendering nlp filter rules'''
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".FilterRuleDataViewListCtrl.__init__")
        logger.info("Starting")
        dv.DataViewListCtrl.__init__(self, parent, style=dv.DV_ROW_LINES|dv.DV_MULTIPLE)

        int_render = dv.DataViewTextRenderer(varianttype="long")
        column0 = dv.DataViewColumn(GUIText.FILTERS_RULES_STEP, int_render, 0,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_RIGHT)
        self.AppendColumn(column0)
        text_render = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.FILTERS_WORDS, text_render, 1,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_render = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(GUIText.FILTERS_POS, text_render, 2,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        text_render = dv.DataViewTextRenderer()
        column3 = dv.DataViewColumn(GUIText.FILTERS_RULES_ACTION, text_render, 3,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)

        columns = self.GetColumns()
        for column in reversed(columns):
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        copy_id = wx.ID_ANY
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=copy_id)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), copy_id )])
        self.SetAcceleratorTable(accel_tbl)

        logger.info("Finished")

    def OnShowPopup(self, event):
        '''create popup menu with options that can be performed on the list'''
        logger = logging.getLogger(__name__+".FilterRuleDataViewListCtrl.OnShowPopup")
        logger.info("Starting")
        menu = wx.Menu()
        menu.Append(1, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.OnCopyItems)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        '''copies what is selected in the list to the user's clipboard'''
        logger = logging.getLogger(__name__+".FilterRuleDataViewListCtrl.OnCopyItems")
        logger.info("Starting")
        selectedItems = []

        for item in self.GetSelections():
            row = self.ItemToRow(item)
            step = self.GetValue(row, 0)
            word = self.GetValue(row, 1)
            pos = self.GetValue(row, 2)
            action = self.GetValue(row, 3)
            selectedItems.append('\t'.join([word,
                                            pos,
                                            action
                                            ]).strip())

        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selectedItems))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

class CreateCountFilterDialog(wx.Dialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".CreateCountFilterDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.FILTERS_CREATE_COUNT_RULE)

        action_options = [Constants.FILTER_RULE_REMOVE,
                          Constants.FILTER_RULE_INCLUDE]
        self.column_options = {GUIText.FILTERS_NUM_WORDS:Constants.TOKEN_NUM_WORDS,
                               GUIText.FILTERS_PER_WORDS:Constants.TOKEN_PER_WORDS,
                               GUIText.FILTERS_NUM_DOCS:Constants.TOKEN_NUM_DOCS,
                               GUIText.FILTERS_PER_DOCS:Constants.TOKEN_PER_DOCS,}
        operation_options = ['>',
                             '>=',
                             '=',
                             '<=',
                             '<']

        self.word = None
        self.pos = None
        self.action = None
        self.column = None
        self.operation = None
        self.number = None

        sizer = wx.BoxSizer(wx.VERTICAL)

        word_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_WORD)
        self.word_ctrl = wx.TextCtrl(self)
        self.word_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_WORD_TOOLTIP)
        word_sizer = wx.BoxSizer(wx.HORIZONTAL)
        word_sizer.Add(word_label)
        word_sizer.Add(self.word_ctrl)
        sizer.Add(word_sizer)

        pos_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_POS)
        self.pos_ctrl = wx.TextCtrl(self)
        self.pos_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_POS_TOOLTIP)
        pos_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer.Add(pos_label)
        pos_sizer.Add(self.pos_ctrl)
        sizer.Add(pos_sizer)

        rule_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_RULE)
        self.action_ctrl = wx.Choice(self, choices=action_options)
        self.column_ctrl = wx.Choice(self, choices=list(self.column_options.keys()))
        self.column_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_COLUMN_TOOLTIP)
        self.operation_ctrl = wx.Choice(self, choices=operation_options)
        self.operation_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_OPERATION_TOOLTIP)
        self.number_ctrl = NumCtrl(self)
        self.number_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_NUMBER_TOOLTIP)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_label)
        rule_sizer.Add(self.action_ctrl)
        rule_sizer.Add(self.column_ctrl)
        rule_sizer.Add(self.operation_ctrl)
        rule_sizer.Add(self.number_ctrl)
        sizer.Add(rule_sizer)

        #fields to choose specific fields for model
        #--- not part of mvp so default is to use all fields

        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK)
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
        logger = logging.getLogger(__name__+".CreateCountFilterDialog.OnOK")
        logger.info("Starting")
        #check that name exists and is unique
        status_flag = True

        self.word = self.word_ctrl.GetValue()
        if self.word == "":
            self.word = Constants.FILTER_RULE_ANY
        self.pos = self.pos_ctrl.GetValue()
        if self.pos == "":
            self.pos = Constants.FILTER_RULE_ANY
        self.action = self.action_ctrl.GetStringSelection()
        self.column = self.column_options[self.column_ctrl.GetStringSelection()]
        self.operation = self.operation_ctrl.GetStringSelection()
        self.number = self.number_ctrl.GetValue()
        if self.action == "" or self.column == "" or self.operation == "" or self.number == "":
            wx.MessageBox(GUIText.FILTERS_CREATE_COUNT_RULE_INCOMPLETE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('rule incomplete action['+self.action+"] column["+self.column+"] operation["+self.operation+"] number["+self.number+"]")
            status_flag = False

        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)

class CreateTfidfFilterDialog(wx.Dialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".CreateTfidfFilterDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.FILTERS_CREATE_TFIDF_RULE)

        action_options1 = [Constants.FILTER_TFIDF_REMOVE,
                           Constants.FILTER_TFIDF_INCLUDE]
        action_options2 = [Constants.FILTER_TFIDF_LOWER,
                           Constants.FILTER_TFIDF_UPPER]

        self.word = None
        self.pos = None
        self.action1 = None
        self.action2 = None
        self.rank = None

        sizer = wx.BoxSizer(wx.VERTICAL)

        word_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_WORD)
        self.word_ctrl = wx.TextCtrl(self)
        self.word_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_WORD_TOOLTIP)
        word_sizer = wx.BoxSizer(wx.HORIZONTAL)
        word_sizer.Add(word_label)
        word_sizer.Add(self.word_ctrl)
        sizer.Add(word_sizer)

        pos_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_POS)
        self.pos_ctrl = wx.TextCtrl(self)
        self.pos_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_POS_TOOLTIP)
        pos_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer.Add(pos_label)
        pos_sizer.Add(self.pos_ctrl)
        sizer.Add(pos_sizer)

        rule_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_RULE)
        self.action1_ctrl = wx.Choice(self, choices=action_options1)
        self.action2_ctrl = wx.Choice(self, choices=action_options2)
        self.rank_ctrl = wx.SpinCtrlDouble(self, min=0, max=1, inc=0.01)
        self.rank_ctrl.SetToolTip(GUIText.FILTERS_CREATE_TFIDF_RULE_NUMBER_TOOLTIP)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_label)
        rule_sizer.Add(self.action1_ctrl)
        rule_sizer.Add(self.action2_ctrl)
        rule_sizer.Add(self.rank_ctrl)
        sizer.Add(rule_sizer)

        #fields to choose specific fields for model
        #--- not part of mvp so default is to use all fields

        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK)
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
        logger = logging.getLogger(__name__+".CreateCountFilterDialog.OnOK")
        logger.info("Starting")
        #check that name exists and is unique
        status_flag = True

        self.word = self.word_ctrl.GetValue()
        if self.word == "":
            self.word = Constants.FILTER_RULE_ANY
        self.pos = self.pos_ctrl.GetValue()
        if self.pos == "":
            self.pos = Constants.FILTER_RULE_ANY
        self.action1 = self.action1_ctrl.GetStringSelection()
        self.action2 = self.action2_ctrl.GetStringSelection()
        self.rank = self.rank_ctrl.GetValue()
        if self.action1 == "" or self.action2 == "" or self.rank == "":
            wx.MessageBox(GUIText.FILTERS_CREATE_TFIDF_RULE_INCOMPLETE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('rule incomplete action1['+self.action1+"] action2["+self.action2+"] rank["+self.rank+"]")
            status_flag = False

        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)
