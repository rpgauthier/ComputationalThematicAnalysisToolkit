'''Token Filtering Sub Module'''
import logging
import json
from datetime import datetime

import jsonpickle
import nltk
import spacy.lang.en.stop_words
import pandas as pd

import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB
import wx.lib.scrolledpanel

import Common.Constants as Constants
import Common.Objects.DataViews.Tokens as TokenDataViews
import Common.Objects.DataViews.Datasets as DatasetsDataViews
import Common.CustomEvents as CustomEvents
from Common.GUIText import Filtering as GUIText
import Common.Database as Database
import Filtering.FilteringThreads as FilteringThreads

class FilteringNotebook(FNB.FlatNotebook):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FilteringNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)

        #create dictionary to hold instances of filter panels for each dataset
        self.filters = {}

        self.view_menu = wx.Menu()
        self.view_menu_menuitem = None

        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None

        self.Fit()

        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".FilteringNotebook.RefreshFilters")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        for filter_key in list(self.filters.keys()):
            if filter_key not in main_frame.datasets:
                index = self.GetPageIndex(self.filters[filter_key])
                if index is not wx.NOT_FOUND:
                    self.RemovePage(index)
                    self.actions_menu.Remove(self.filters[filter_key].actions_menu_menuitem)
                self.filters[filter_key].Hide()
                del self.filters[filter_key]
        
        for key in main_frame.datasets:
            if key in self.filters:
                self.filters[key].ApplyFilterRulesStart()
                self.filters[key].rules_panel.DisplayFilterRules(main_frame.datasets[key].filter_rules)
            else:
                self.filters[key] = FilterPanel(self, main_frame.datasets[key].name, main_frame.datasets[key], size=self.GetSize())
                self.filters[key].ApplyFilterRulesStart()
                self.filters[key].rules_panel.DisplayFilterRules(main_frame.datasets[key].filter_rules)
                self.AddPage(self.filters[key], main_frame.datasets[key].name)
                self.filters[key].actions_menu_menuitem = self.actions_menu.AppendSubMenu(self.filters[key].actions_menu, main_frame.datasets[key].name)
        self.Thaw()
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FilteringNotebook.Load")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()

        for filter_key in list(self.filters.keys()):
            index = self.GetPageIndex(self.filters[filter_key])
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
                self.actions_menu.Remove(self.filters[filter_key].actions_menu_menuitem)
            self.filters[filter_key].Hide()
            del self.filters[filter_key]
        
        for key in main_frame.datasets:
            self.filters[key] = FilterPanel(self, main_frame.datasets[key].name, main_frame.datasets[key], size=self.GetSize())
            self.AddPage(self.filters[key], main_frame.datasets[key].name)
            self.filters[key].actions_menu_menuitem = self.actions_menu.AppendSubMenu(self.filters[key].actions_menu, main_frame.datasets[key].name)

        #load all filter panels
        for filter_key in self.filters:
            if 'filters' in saved_data and filter_key in saved_data['filters']:
                self.filters[filter_key].Load(saved_data['filters'][filter_key])
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FilteringNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['filters'] = {}
        for filter_key in self.filters:
            saved_data['filters'][filter_key] = self.filters[filter_key].Save()
        logger.info("Finished")
        return saved_data

class FilterPanel(wx.Panel):
    def __init__(self, parent, name, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FilterPanel["+str(name)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, size=size)

        #link to find the associated dataset object from the datasets and the workspace database
        self.name = name
        self.dataset = dataset
        #thread used to generate dataframes for use when display lists
        self.thread = None

        panel_splitter = wx.SplitterWindow(self, size=self.GetSize(), style=wx.SP_BORDER)
        top_splitter = wx.SplitterWindow(panel_splitter, style=wx.SP_BORDER)
        bottom_splitter = wx.SplitterWindow(panel_splitter, style=wx.SP_BORDER)

        self.included_words_panel = IncludedWordsPanel(top_splitter, self,  style=wx.TAB_TRAVERSAL)
        self.removed_words_panel = RemovedWordsPanel(top_splitter, self, style=wx.TAB_TRAVERSAL) 
        self.rules_panel = RulesPanel(bottom_splitter, self, style=wx.TAB_TRAVERSAL)
        self.impact_panel = ImpactPanel(bottom_splitter, self)
        
        top_splitter.SetMinimumPaneSize(20)
        top_splitter.SetSashPosition(int(self.GetSize().GetWidth()/2))
        top_splitter.SplitVertically(self.included_words_panel, self.removed_words_panel)

        bottom_splitter.SetMinimumPaneSize(20)
        bottom_splitter.SetSashPosition(int(self.GetSize().GetWidth()/2))
        bottom_splitter.SplitVertically(self.rules_panel, self.impact_panel)
        
        panel_splitter.SetMinimumPaneSize(20)
        panel_splitter.SetSashPosition(int(self.GetSize().GetHeight()*3/4))
        panel_splitter.SplitHorizontally(top_splitter, bottom_splitter)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel_splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        #create the menu for the filter
        main_frame = wx.GetApp().GetTopWindow()
        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None
        importNLTKStopWordsItem = self.actions_menu.Append(wx.ID_ANY,
                                                   GUIText.FILTERS_IMPORT_NLTK,
                                                   GUIText.FILTERS_IMPORT_NLTK_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnImportNLTKStopWords, importNLTKStopWordsItem)
        importSpacyStopWordsItem = self.actions_menu.Append(wx.ID_ANY,
                                                    GUIText.FILTERS_IMPORT_SPACY,
                                                    GUIText.FILTERS_IMPORT_SPACY_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnImportSpacyStopWords, importSpacyStopWordsItem)
        self.actions_menu.AppendSeparator()
        importRemovalSettingsItem = self.actions_menu.Append(wx.ID_ANY,
                                                     GUIText.FILTERS_IMPORT,
                                                     GUIText.FILTERS_IMPORT_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnImportFilterRules, importRemovalSettingsItem)
        exportRemovalSettingsItem = self.actions_menu.Append(wx.ID_ANY,
                                                     GUIText.FILTERS_EXPORT,
                                                     GUIText.FILTERS_EXPORT_TOOLTIP)
        main_frame.Bind(wx.EVT_MENU, self.OnExportFilterRules, exportRemovalSettingsItem)

        #event end points for completed threads
        CustomEvents.APPLY_FILTER_RULES_EVT_RESULT(self, self.OnApplyFilterRulesEnd)
        logger.info("Finished")

    ######
    #functions called by the interface
    ######

    def OnRemoveEntry(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveEntry")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.included_words_panel.words_list.GetCellValue(row, 0)
                pos = self.included_words_panel.words_list.GetCellValue(row, 1)
                self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, word, pos, Constants.FILTER_RULE_REMOVE))
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyLatestFilterRuleStart()
        logger.info("Finished")

    def OnReaddEntry(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnReaddEntry")
        logger.info("Starting")
        selection = self.removed_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.removed_words_panel.words_list.GetCellValue(row, 0)
                pos = self.removed_words_panel.words_list.GetCellValue(row, 1)
                self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, word, pos, Constants.FILTER_RULE_INCLUDE))
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyLatestFilterRuleStart()
        logger.info("Finished")

    def OnRemoveWord(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveWord")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.included_words_panel.words_list.GetCellValue(row, 0)
                self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyLatestFilterRuleStart()
        logger.info("Finished")

    def OnReaddWord(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnReaddWord")
        logger.info("Starting")
        selection = self.removed_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                word = self.removed_words_panel.words_list.GetCellValue(row, 0)
                self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_INCLUDE))
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyLatestFilterRuleStart()
        logger.info("Finished")

    def OnRemovePOS(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemovePOS")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                pos = self.included_words_panel.words_list.GetCellValue(row, 1)
                self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, pos, Constants.FILTER_RULE_REMOVE))
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyLatestFilterRuleStart()
        logger.info("Finished")

    def OnReaddPOS(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnReaddPOS")
        logger.info("Starting")
        selection = self.removed_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            for row in selection:
                pos = self.removed_words_panel.words_list.GetCellValue(row, 1)
                self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, pos, Constants.FILTER_RULE_INCLUDE))
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyLatestFilterRuleStart()
        logger.info("Finished")
    
    def OnRemoveSpacyAutoStopword(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnSpacyAutoStopword")
        logger.info("Starting")
        self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS))
        self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
        self.ApplyLatestFilterRuleStart()
        logger.info("Finished")
    
    def OnCreateCountFilter(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnCreateCountFilter")
        logger.info("Starting")
        #custom dialog to choose direction (greater or less), number, and words or docs
        with CreateCountFilterDialog(self, self.dataset) as create_dialog:
            if create_dialog.ShowModal() == wx.ID_OK:
                rule = (create_dialog.action,
                        create_dialog.column,
                        create_dialog.operation,
                        create_dialog.number,)
                self.dataset.AddFilterRule((create_dialog.field, create_dialog.word, create_dialog.pos, rule))
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyLatestFilterRuleStart()
        logger.info("Finished")
    
    def OnCreateTfidfFilter(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnCreateTfidfFilter")
        logger.info("Starting")
        with CreateTfidfFilterDialog(self, self.dataset) as create_dialog:
            if create_dialog.ShowModal() == wx.ID_OK:
                rule = (create_dialog.action1,
                        create_dialog.action2,
                        create_dialog.rank,)
                self.dataset.AddFilterRule((create_dialog.field, create_dialog.word, create_dialog.pos, rule))
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyLatestFilterRuleStart()
        logger.info("Finished")

    def OnRemoveRule(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveRule")
        logger.info("Starting")
        flag = False
        for item in reversed(self.rules_panel.rules_list.GetSelections()):
            row = self.rules_panel.rules_list.ItemToRow(item)
            index = self.rules_panel.rules_list.GetValue(row, 0) - 1
            del self.dataset.filter_rules[index]
            self.dataset.last_changed_dt = datetime.now()
            flag = True
        if flag:
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyFilterRulesStart()
        logger.info("Finished")
    
    def OnMoveRuleUp(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnMoveRuleUp")
        logger.info("Starting")
        changecompleted_flag = False
        refreshneeded_flag = False
        for item in reversed(self.rules_panel.rules_list.GetSelections()):
            row = self.rules_panel.rules_list.ItemToRow(item)
            index = self.rules_panel.rules_list.GetValue(row, 0)
            if index < len(self.dataset.filter_rules):
                self.dataset.filter_rules[index], self.dataset.filter_rules[index-1] = self.dataset.filter_rules[index-1], self.dataset.filter_rules[index]
                self.dataset.last_changed_dt = datetime.now()
                changecompleted_flag = True
                action1 = self.dataset.filter_rules[index][3]
                if isinstance(action1, tuple):
                    action1 = action1[0]
                    if action1 == Constants.FILTER_TFIDF_REMOVE:
                        action1 = Constants.FILTER_RULE_REMOVE
                    elif action1 == Constants.FILTER_TFIDF_INCLUDE:
                        action1 = Constants.FILTER_RULE_INCLUDE
                elif action1 == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                    action1 = Constants.FILTER_RULE_REMOVE
                action2 = self.dataset.filter_rules[index-1][3]
                if isinstance(action2, tuple):
                    action2 = action2[0]
                    if action2 == Constants.FILTER_TFIDF_REMOVE:
                        action2 = Constants.FILTER_RULE_REMOVE
                    elif action2 == Constants.FILTER_TFIDF_INCLUDE:
                        action2 = Constants.FILTER_RULE_INCLUDE
                elif action2 == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                    action2 = Constants.FILTER_RULE_REMOVE
                if action1 != action2:
                    refreshneeded_flag = True
            else:
                break
        if changecompleted_flag:
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
        if refreshneeded_flag:
            self.ApplyFilterRulesStart()
        logger.info("Finished")
    
    def OnMoveRuleDown(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnMoveRuleDown")
        logger.info("Starting")
        changecompleted_flag = False
        refreshneeded_flag = False
        for item in self.rules_panel.rules_list.GetSelections():
            row = self.rules_panel.rules_list.ItemToRow(item)
            index = self.rules_panel.rules_list.GetValue(row, 0)
            if index > 1:
                self.dataset.filter_rules[index-2], self.dataset.filter_rules[index-1] = self.dataset.filter_rules[index-1], self.dataset.filter_rules[index-2]
                self.dataset.last_changed_dt = datetime.now()
                changecompleted_flag = True
                action1 = self.dataset.filter_rules[index-2][3]
                if isinstance(action1, tuple):
                    action1 = action1[0]
                    if action1 == Constants.FILTER_TFIDF_REMOVE:
                        action1 = Constants.FILTER_RULE_REMOVE
                    elif action1 == Constants.FILTER_TFIDF_INCLUDE:
                        action1 = Constants.FILTER_RULE_INCLUDE
                elif action1 == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                    action1 = Constants.FILTER_RULE_REMOVE
                action2 = self.dataset.filter_rules[index-1][3]
                if isinstance(action2, tuple):
                    action2 = action2[0]
                    if action2 == Constants.FILTER_TFIDF_REMOVE:
                        action2 = Constants.FILTER_RULE_REMOVE
                    elif action2 == Constants.FILTER_TFIDF_INCLUDE:
                        action2 = Constants.FILTER_RULE_INCLUDE
                elif action2 == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                    action2 = Constants.FILTER_RULE_REMOVE
                if action1 != action2:
                    refreshneeded_flag = True
            else:
                break
        if changecompleted_flag:
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
        if refreshneeded_flag:
            self.ApplyFilterRulesStart()
        logger.info("Finished")

    def OnImportNLTKStopWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportNLTKStopWords")
        logger.info("Starting")
        nltk_stopwords = set(nltk.corpus.stopwords.words('english'))
        for word in nltk_stopwords:
            self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
        self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
        self.ApplyFilterRulesStart()
        logger.info("Finished")

    def OnImportSpacyStopWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportSpacyStopWords")
        logger.info("Starting")
        spacy_stopwords = spacy.lang.en.stop_words.STOP_WORDS
        for word in spacy_stopwords:
            self.dataset.AddFilterRule((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
        self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
        self.ApplyFilterRulesStart()
        logger.info("Finished")
 
    def OnImportFilterRules(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportRemovalSettings")
        logger.info("Starting")
        if wx.MessageBox(GUIText.FILTERS_IMPORT_CONFIRMATION_REQUEST,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
            # otherwise ask the user what new file to open
            with wx.FileDialog(self, GUIText.FILTERS_IMPORT, defaultDir='../Workspaces/',
                            wildcard="Rules JSON files (*.rules_json)|*.rules_json",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                # cancel if the user changed their mind
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                # Proceed loading the file chosen by the user
                pathname = file_dialog.GetPath()
                try:
                    with open(pathname, 'r') as file:
                        self.dataset.filter_rules = jsonpickle.decode(json.load(file))
                        self.dataset.last_changed_dt = datetime.now()
                except IOError:
                    wx.LogError("Cannot open file '%s'", self.saved_name)
                    logger.error("Failed to open file '%s'", self.saved_name)
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyFilterRulesStart()
        logger.info("Finished")

    def OnExportFilterRules(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnExportRemovalSettings")
        logger.info("Starting")
        with wx.FileDialog(self, GUIText.FILTERS_EXPORT, defaultDir='../Workspaces/',
                           wildcard="Rules JSON files (*.rules_json)|*.rules_json",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:
            # cancel if the user changed their mind
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            # save the current contents in the file
            pathname = file_dialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    json.dump(jsonpickle.encode(self.dataset.filter_rules), file)
            except IOError:
                wx.LogError("Cannot save current removal settings '%s'", self.saved_name)
                logger.error("Failed to save removal to file '%s'", self.saved_name)
        logger.info("Finished")

    def OnTokenizationChoice(self, event):
        choice = self.rules_panel.tokenization_choice.GetSelection()
        if choice != self.dataset.tokenization_choice:
            self.dataset.tokenization_choice = choice
            main_frame = wx.GetApp().GetTopWindow()
            db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
            if choice == Constants.TOKEN_TEXT_IDX:
                db_conn.UpdateDatasetTokenType(self.dataset.key, 'text')
            elif choice == Constants.TOKEN_STEM_IDX:
                db_conn.UpdateDatasetTokenType(self.dataset.key, 'stem')
            elif choice == Constants.TOKEN_LEMMA_IDX:
                db_conn.UpdateDatasetTokenType(self.dataset.key, 'lemma')
            counts = db_conn.GetStringTokensCounts(self.dataset.key)
            self.dataset.total_docs = counts['documents']
            self.dataset.total_tokens = counts['tokens']
            self.dataset.total_uniquetokens = counts['unique_tokens']
            self.ApplyFilterRulesStart()

    #functions called to complete operation of other functions
    def ApplyFilterRulesStart(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].ApplyFilterRulesStart")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        main_frame.CreateProgressDialog(GUIText.FILTERS_APPLYING_RULES_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        main_frame.PulseProgressDialog(GUIText.FILTERS_APPLYING_RULES_BUSY_MSG+str(self.name))
        self.thread = FilteringThreads.ApplyFilterRulesThread(self, self.dataset, main_frame.current_workspace.name)
        logger.info("Finished")

    #special function for situations where a single new rule is added and thus can be applied upon existing filtering
    def ApplyLatestFilterRuleStart(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].ApplyFilterRulesStart")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        main_frame.CreateProgressDialog(GUIText.FILTERS_APPLYING_RULES_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        main_frame.PulseProgressDialog(GUIText.FILTERS_APPLYING_RULES_BUSY_MSG+str(self.name))
        self.thread = FilteringThreads.ApplyFilterLatestRuleThread(self, self.dataset, main_frame.current_workspace.name)
        logger.info("Finished")

    def OnApplyFilterRulesEnd(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnApplyFilterRulesEnd")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.thread.join()
        self.thread = None
        
        db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
        self.included_words_panel.UpdateWords(db_conn.GetIncludedStringTokensDataFrame(self.dataset.key))
        self.removed_words_panel.UpdateWords(db_conn.GetRemovedStringTokensDataFrame(self.dataset.key))
        del db_conn

        self.UpdateImpact()

        main_frame.CloseProgressDialog(thaw=False)
        self.Thaw()
        logger.info("Finished")
    
    def UpdateImpact(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].UpdateImpact")
        logger.info("Starting")
        self.impact_panel.document_num_original.SetLabel(str(self.dataset.total_docs))
        self.impact_panel.token_num_original.SetLabel(str(self.dataset.total_tokens))
        self.impact_panel.uniquetoken_num_original.SetLabel(str(self.dataset.total_uniquetokens))

        self.impact_panel.document_num_remaining.SetLabel(str(self.dataset.total_docs_remaining))
        self.impact_panel.token_num_remaining.SetLabel(str(self.dataset.total_tokens_remaining))
        self.impact_panel.uniquetoken_num_remaining.SetLabel(str(self.dataset.total_uniquetokens_remaining))
        self.impact_panel.Update()
        logger.info("Finished")


    #Required Functions
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].Load")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_FILTERING_BUSY_MSG+str(self.name))

        self.rules_panel.tokenization_choice.SetSelection(self.dataset.tokenization_choice)

        if 'included_search_word' in saved_data:
            self.included_words_panel.word_searchctrl.SetValue(saved_data['included_search_word'])
        if 'included_search_pos' in saved_data:
            self.included_words_panel.pos_searchctrl.SetValue(saved_data['included_search_pos'])
        if 'removed_search_word' in saved_data:
            self.removed_words_panel.word_searchctrl.SetValue(saved_data['removed_search_word'])
        if 'removed_search_pos' in saved_data:
            self.removed_words_panel.pos_searchctrl.SetValue(saved_data['removed_search_pos'])

        db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
        self.included_words_panel.UpdateWords(db_conn.GetIncludedStringTokensDataFrame(self.dataset.key))
        self.removed_words_panel.UpdateWords(db_conn.GetRemovedStringTokensDataFrame(self.dataset.key))
        del db_conn

        self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)

        self.UpdateImpact()

        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].Save")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.SAVE_FILTERING_BUSY_MSG+str(self.name))
        saved_data = {}
        saved_data['included_search_word'] = self.included_words_panel.word_searchctrl.GetValue()
        saved_data['included_search_pos'] = self.included_words_panel.pos_searchctrl.GetValue()
        saved_data['removed_search_word'] = self.removed_words_panel.word_searchctrl.GetValue()
        saved_data['removed_search_pos'] = self.removed_words_panel.pos_searchctrl.GetValue()
        logger.info("Finished")
        return saved_data

#TODO check if pandas can function on large datasets here or if it needs instead connect the dataviews to the DB
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
        self.toolbar.Realize()
        sizer.Add(self.toolbar, proportion=0, flag=wx.ALL, border=5)
        #create search sizer
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.word_searchctrl = wx.SearchCtrl(self)
        self.word_searchctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.word_searchctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.word_searchctrl.SetDescriptiveText(GUIText.FILTERS_WORD_SEARCH)
        self.word_searchctrl.ShowCancelButton(True)
        search_sizer.Add(self.word_searchctrl, 0, wx.ALL, 5)
        self.pos_searchctrl = wx.SearchCtrl(self)
        self.pos_searchctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.pos_searchctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.pos_searchctrl.SetDescriptiveText(GUIText.FILTERS_POS_SEARCH)
        self.pos_searchctrl.ShowCancelButton(True)
        search_sizer.Add(self.pos_searchctrl, 0, wx.ALL, 5)
        self.search_count_text = wx.StaticText(self)
        search_sizer.Add(self.search_count_text, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer.Add(search_sizer)
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
        self.DisplayWordsList()
        self.search_count_text.SetLabel(GUIText.SEARCH_COUNT_LABEL+str(len(self.words_list.tokens_df)))
        logger.info("Finished")

    def OnSearchCancel(self, event):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].OnSearchCancel")
        logger.info("Starting")
        search_ctrl = event.GetEventObject()
        search_ctrl.SetValue("")
        self.DisplayWordsList()
        if self.word_searchctrl.GetValue() == "" and self.pos_searchctrl.GetValue() == "":
            self.search_count_text.SetLabel("")
        else:
            self.search_count_text.SetLabel(GUIText.SEARCH_COUNT_LABEL+str(len(self.words_list.tokens_df)))
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
        main_frame.PulseProgressDialog(GUIText.FILTERS_DISPLAY_STRINGS_BUSY_MSG1+self.word_type+GUIText.FILTERS_DISPLAY_STRINGS_BUSY_MSG2+str(self.parent_frame.name))
        try:
            word_search_term = self.word_searchctrl.GetValue()
            pos_search_term = self.pos_searchctrl.GetValue()
            if word_search_term != '' and pos_search_term != '':
                search_filter = self.tokens_df['words'].str.contains(word_search_term, regex=False) & self.tokens_df['pos'].str.contains(pos_search_term, regex=False)
                searched_df = self.tokens_df[search_filter]
            elif word_search_term != '':
                search_filter = self.tokens_df['words'].str.contains(word_search_term, regex=False)
                searched_df = self.tokens_df[search_filter]
            elif pos_search_term != '':
                search_filter = self.tokens_df['pos'].str.contains(pos_search_term, regex=False)
                searched_df = self.tokens_df[search_filter]
            else:
                searched_df = self.tokens_df
            
            searched_df = pd.DataFrame(searched_df)
            searched_df[Constants.TOKEN_PER_WORDS] = searched_df[Constants.TOKEN_NUM_WORDS].div(self.parent_frame.dataset.total_tokens).mul(100).round(4)
            searched_df[Constants.TOKEN_PER_DOCS] = searched_df[Constants.TOKEN_NUM_DOCS].div(self.parent_frame.dataset.total_docs).mul(100).round(4)

            self.words_df = searched_df[[Constants.TOKEN_WORDS,
                                         Constants.TOKEN_POS,
                                         Constants.TOKEN_NUM_WORDS,
                                         Constants.TOKEN_PER_WORDS,
                                         Constants.TOKEN_NUM_DOCS,
                                         Constants.TOKEN_PER_DOCS,
                                         Constants.TOKEN_SPACY_STOPWORD,
                                         Constants.TOKEN_TFIDF]].copy()
            self.words_df.columns = self.col_names

            self.words_df.sort_values(by=[GUIText.FILTERS_NUM_WORDS], ascending=False, inplace=True)

            self.words_list.Update(self.words_df)
        finally:
            self.Thaw()
        logger.info("Finished")

class IncludedWordsPanel(WordsPanel):
    def __init__(self, parent, parent_frame, style):
        logger = logging.getLogger(__name__+".IncludedWordsPanel["+str(parent_frame.name)+"]__init__")
        logger.info("Starting")
        WordsPanel.__init__(self, parent, parent_frame, "Included", style=style)
        self.label_box.SetLabel(GUIText.FILTERS_INCLUDED_LIST)
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
        self.label_box.SetLabel(GUIText.FILTERS_REMOVED_LIST)
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

        package_list = list(self.parent_frame.dataset.tokenization_package_versions)
        tokenizer_package = self.parent_frame.dataset.tokenization_package_versions[0]
        package_list[0] = GUIText.FILTERS_RAWTOKENS
        package_list[1] = GUIText.FILTERS_STEMMER + package_list[1]
        package_list[2] = GUIText.FILTERS_LEMMATIZER + package_list[2]

        #Label for area
        label_box = wx.StaticBox(self, label=GUIText.FILTERS_RULES_LIST)
        label_font = wx.Font(Constants.LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, underline=Constants.LABEL_UNDERLINE)
        label_box.SetFont(label_font)
        
        sizer = wx.StaticBoxSizer(label_box, wx.VERTICAL)

        tokenization_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(tokenization_sizer)
        tokenization_package_label1 = wx.StaticText(self, label=GUIText.FILTERS_TOKENIZER)
        tokenization_package_label1.SetFont(wx.Font(-1, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        tokenization_sizer.Add(tokenization_package_label1, proportion=0, flag=wx.ALL, border=5)
        self.tokenization_package_label2 = wx.StaticText(self, label=tokenizer_package)
        tokenization_sizer.Add(self.tokenization_package_label2, proportion=0, flag=wx.ALL, border=5)
        tokenization_choice_label = wx.StaticText(self, label=GUIText.FILTERS_METHOD)
        tokenization_choice_label.SetFont(wx.Font(-1, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        tokenization_sizer.Add(tokenization_choice_label, proportion=0, flag=wx.ALL, border=5)
        self.tokenization_choice = wx.Choice(self, choices=package_list)
        self.tokenization_choice.SetSelection(self.parent_frame.dataset.tokenization_choice)
        self.tokenization_choice.Bind(wx.EVT_CHOICE, self.parent_frame.OnTokenizationChoice)
        self.tokenization_choice.SetSelection(0)
        tokenization_sizer.Add(self.tokenization_choice, proportion=0, flag=wx.ALL, border=5)
        
        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_HORZ_TEXT|wx.TB_NOICONS)
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

        self.rules_list = DatasetsDataViews.FilterRuleDataViewListCtrl(self)
        sizer.Add(self.rules_list, proportion=1, flag=wx.EXPAND, border=5)

        border = wx.BoxSizer()
        border.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(border)
        logger.info("Finished")

    def DisplayFilterRules(self, filter_rules):

        package_list = list(self.parent_frame.dataset.tokenization_package_versions)
        tokenizer_package = self.parent_frame.dataset.tokenization_package_versions[0]
        package_list[0] = GUIText.FILTERS_RAWTOKENS
        package_list[1] = GUIText.FILTERS_STEMMER + package_list[1]
        package_list[2] = GUIText.FILTERS_LEMMATIZER + package_list[2]

        self.tokenization_package_label2.SetLabel(tokenizer_package)
        self.tokenization_choice.SetString(0, package_list[0])
        self.tokenization_choice.SetString(1, package_list[1])
        self.tokenization_choice.SetString(2, package_list[2])

        column_options = {Constants.TOKEN_NUM_WORDS:GUIText.FILTERS_NUM_WORDS,
                          Constants.TOKEN_PER_WORDS:GUIText.FILTERS_PER_WORDS,
                          Constants.TOKEN_NUM_DOCS:GUIText.FILTERS_NUM_DOCS,
                          Constants.TOKEN_PER_DOCS:GUIText.FILTERS_PER_DOCS}
        self.rules_list.DeleteAllItems()
        i = 1
        for field, word, pos, action in filter_rules:
            if isinstance(action, tuple):
                if action[0] == Constants.FILTER_TFIDF_REMOVE or action[0] == Constants.FILTER_TFIDF_INCLUDE:
                    action = str(action[0])+str(action[1])+str(action[2])+"%"
                else:
                    action = str(action[0]) + " ("+str(column_options[action[1]])+str(action[2])+str(action[3])+")"
                
            self.rules_list.AppendItem([i, field, word, pos, str(action)])
            i += 1

class ImpactPanel(wx.Panel):
    def __init__(self, parent, parent_frame):
        wx.Panel.__init__(self, parent)

        self.label_box = wx.StaticBox(self, label=GUIText.IMPACT_LABEL)
        label_font = wx.Font(Constants.LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, underline=Constants.LABEL_UNDERLINE)
        self.label_box.SetFont(label_font)

        sizer = wx.StaticBoxSizer(self.label_box, wx.VERTICAL)
        
        document_num_sizer = wx.BoxSizer()
        document_num_label1 = wx.StaticText(self, label=GUIText.FILTERS_NUM_DOCS+":")
        document_num_sizer.Add(document_num_label1, 0, wx.ALL, 5)
        self.document_num_remaining = wx.StaticText(self, label="")
        document_num_sizer.Add(self.document_num_remaining, 0, wx.ALL, 5)
        document_num_label2 = wx.StaticText(self, label=" / ")
        document_num_sizer.Add(document_num_label2, 0, wx.ALL, 5)
        self.document_num_original = wx.StaticText(self, label="")
        document_num_sizer.Add(self.document_num_original, 0, wx.ALL, 5)
        sizer.Add(document_num_sizer)

        token_num_sizer = wx.BoxSizer()
        token_num_label1 = wx.StaticText(self, label=GUIText.FILTERS_NUM_WORDS+":")
        token_num_sizer.Add(token_num_label1, 0, wx.ALL, 5)
        self.token_num_remaining = wx.StaticText(self, label="")
        token_num_sizer.Add(self.token_num_remaining, 0, wx.ALL, 5)
        token_num_label2 = wx.StaticText(self, label=" / ")
        token_num_sizer.Add(token_num_label2, 0, wx.ALL, 5)
        self.token_num_original = wx.StaticText(self, label="")
        token_num_sizer.Add(self.token_num_original, 0, wx.ALL, 5)
        sizer.Add(token_num_sizer)

        uniquetoken_num_sizer = wx.BoxSizer()
        uniquetoken_num_label1 = wx.StaticText(self, label=GUIText.FILTERS_NUM_UNIQUEWORDS+":")
        uniquetoken_num_sizer.Add(uniquetoken_num_label1, 0, wx.ALL, 5)
        self.uniquetoken_num_remaining = wx.StaticText(self, label="")
        uniquetoken_num_sizer.Add(self.uniquetoken_num_remaining, 0, wx.ALL, 5)
        uniquetoken_num_label2 = wx.StaticText(self, label=" / ")
        uniquetoken_num_sizer.Add(uniquetoken_num_label2, 0, wx.ALL, 5)
        self.uniquetoken_num_original = wx.StaticText(self, label="")
        uniquetoken_num_sizer.Add(self.uniquetoken_num_original, 0, wx.ALL, 5)
        sizer.Add(uniquetoken_num_sizer)

        border = wx.BoxSizer()
        border.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(border)

class CreateCountFilterDialog(wx.Dialog):
    def __init__(self, parent, dataset):
        logger = logging.getLogger(__name__+".CreateCountFilterDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.FILTERS_CREATE_COUNT_RULE)

        field_options = list(dataset.included_fields.keys())
        field_options.insert(0, "")
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

        self.field = None
        self.word = None
        self.pos = None
        self.action = None
        self.column = None
        self.operation = None
        self.number = None

        sizer = wx.BoxSizer(wx.VERTICAL)

        field_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_FIELD)
        self.field_ctrl = wx.Choice(self, choices=field_options)
        self.field_ctrl.SetSelection(0)
        self.field_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_FIELD_TOOLTIP)
        field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        field_sizer.Add(field_label, 0, wx.ALL, 5)
        field_sizer.Add(self.field_ctrl, 0, wx.ALL, 5)
        sizer.Add(field_sizer)

        word_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_WORD)
        self.word_ctrl = wx.TextCtrl(self)
        self.word_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_WORD_TOOLTIP)
        word_sizer = wx.BoxSizer(wx.HORIZONTAL)
        word_sizer.Add(word_label, 0, wx.ALL, 5)
        word_sizer.Add(self.word_ctrl, 0, wx.ALL, 5)
        sizer.Add(word_sizer)

        pos_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_POS)
        self.pos_ctrl = wx.TextCtrl(self)
        self.pos_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_POS_TOOLTIP)
        pos_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer.Add(pos_label, 0, wx.ALL, 5)
        pos_sizer.Add(self.pos_ctrl, 0, wx.ALL, 5)
        sizer.Add(pos_sizer)

        rule_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_RULE)
        self.action_ctrl = wx.Choice(self, choices=action_options)
        self.column_ctrl = wx.Choice(self, choices=list(self.column_options.keys()))
        self.column_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_COLUMN_TOOLTIP)
        self.operation_ctrl = wx.Choice(self, choices=operation_options)
        self.operation_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_OPERATION_TOOLTIP)
        self.number_ctrl = wx.SpinCtrlDouble(self, min=0, max=dataset.total_tokens, inc=0.01)
        self.number_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_NUMBER_TOOLTIP)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_label, 0, wx.ALL, 5)
        rule_sizer.Add(self.action_ctrl, 0, wx.ALL, 5)
        rule_sizer.Add(self.column_ctrl, 0, wx.ALL, 5)
        rule_sizer.Add(self.operation_ctrl, 0, wx.ALL, 5)
        rule_sizer.Add(self.number_ctrl, 0, wx.ALL, 5)
        sizer.Add(rule_sizer)

        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)
        sizer.Add(controls_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

        logger.info("Finished")

    def OnOK(self, event):
        logger = logging.getLogger(__name__+".CreateCountFilterDialog.OnOK")
        logger.info("Starting")
        #check that name exists and is unique
        status_flag = True

        self.field = self.field_ctrl.GetStringSelection()
        if self.field == "":
            self.field = Constants.FILTER_RULE_ANY
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
    def __init__(self, parent, dataset):
        logger = logging.getLogger(__name__+".CreateTfidfFilterDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.FILTERS_CREATE_TFIDF_RULE)

        field_options = list(dataset.included_fields.keys())
        field_options.insert(0, "")
        action_options1 = [Constants.FILTER_TFIDF_REMOVE,
                           Constants.FILTER_TFIDF_INCLUDE]
        action_options2 = [Constants.FILTER_TFIDF_LOWER,
                           Constants.FILTER_TFIDF_UPPER]

        self.field = None
        self.word = None
        self.pos = None
        self.action1 = None
        self.action2 = None
        self.rank = None

        sizer = wx.BoxSizer(wx.VERTICAL)

        field_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_FIELD)
        self.field_ctrl = wx.Choice(self, choices=field_options)
        self.field_ctrl.SetSelection(0)
        self.field_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_FIELD_TOOLTIP)
        field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        field_sizer.Add(field_label)
        field_sizer.Add(self.field_ctrl)
        sizer.Add(field_sizer)

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
        self.rank_ctrl = wx.SpinCtrlDouble(self, min=0, max=100, inc=0.01)
        self.rank_ctrl.SetToolTip(GUIText.FILTERS_CREATE_TFIDF_RULE_NUMBER_TOOLTIP)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_label)
        rule_sizer.Add(self.action1_ctrl)
        rule_sizer.Add(self.action2_ctrl)
        rule_sizer.Add(self.rank_ctrl)
        sizer.Add(rule_sizer)

        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)
        sizer.Add(controls_sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

        logger.info("Finished")

    def OnOK(self, event):
        logger = logging.getLogger(__name__+".CreateCountFilterDialog.OnOK")
        logger.info("Starting")
        #check that name exists and is unique
        status_flag = True

        self.field = self.field_ctrl.GetStringSelection()
        if self.field == "":
            self.field = Constants.FILTER_RULE_ANY
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
