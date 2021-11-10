'''Token Filtering Sub Module'''
import logging
import json
from datetime import datetime
import re

import jsonpickle
import nltk
import spacy.lang.en.stop_words
import spacy.lang.fr.stop_words

import wx
import wx.grid
import wx.lib.splitter as splitter
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB
import wx.lib.scrolledpanel

import Common.Constants as Constants
import Common.Objects.DataViews.Tokens as TokenDataViews
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Common.Objects.Threads.Datasets as DatasetsThreads
import Common.CustomEvents as CustomEvents
from Common.GUIText import Filtering as GUIText

class FilteringNotebook(FNB.FlatNotebook):
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".FilteringNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)

        #create dictionary to hold instances of filter panels for each dataset
        self.filters = {}

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
            if len(main_frame.datasets[key].computational_fields) > 0:
                if key in self.filters:
                    self.filters[key].rules_panel.DisplayFilterRules(main_frame.datasets[key].filter_rules)
                    self.filters[key].UpdateImpact()
                else:
                    self.filters[key] = FilterPanel(self, main_frame.datasets[key].name, main_frame.datasets[key], size=self.GetSize())
                    self.filters[key].rules_panel.DisplayFilterRules(main_frame.datasets[key].filter_rules)
                    self.filters[key].UpdateImpact()
                    self.AddPage(self.filters[key], main_frame.datasets[key].name)
                    self.filters[key].actions_menu_menuitem = self.actions_menu.AppendSubMenu(self.filters[key].actions_menu, main_frame.datasets[key].name)
            else:
                if key in self.filters:
                    index = self.GetPageIndex(self.filters[key])
                    if index is not wx.NOT_FOUND:
                        self.RemovePage(index)
                        self.actions_menu.Remove(self.filters[key].actions_menu_menuitem)
                    self.filters[key].Hide()
                    del self.filters[key]
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
            if key in saved_data['filters']:
                self.filters[key].Load(saved_data['filters'][key])
            else:
                self.filters[key].rules_panel.DisplayFilterRules(main_frame.datasets[key].filter_rules)
                self.filters[key].UpdateImpact()
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
        self.autosave = False

        self.drag_source = None

        panel_splitter = wx.SplitterWindow(self, size=self.GetSize(), style=wx.SP_BORDER)
        
        self.rules_panel = RulesPanel(panel_splitter, self, style=wx.TAB_TRAVERSAL)

        right_splitter = wx.SplitterWindow(panel_splitter, style=wx.SP_BORDER)
        self.included_words_panel = IncludedWordsPanel(right_splitter, self, dataset,  style=wx.TAB_TRAVERSAL)
        self.removed_words_panel = RemovedWordsPanel(right_splitter, self, dataset, style=wx.TAB_TRAVERSAL) 
        
        rules_width = int(self.rules_panel.GetBestSize().GetWidth())
        halfway_width = int(self.GetSize().GetWidth()/2)
        right_splitter.SplitHorizontally(self.included_words_panel, self.removed_words_panel, int(self.GetSize().GetHeight()/2))
        right_splitter.SetMinimumPaneSize(200)
        panel_splitter.SplitVertically(self.rules_panel, right_splitter, min(rules_width, halfway_width))
        panel_splitter.SetMinimumPaneSize(200)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel_splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

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
        CustomEvents.CHANGE_TOKENIZATION_CHOICE_EVT_RESULT(self, self.OnTokenizationChoiceEnd)
        CustomEvents.APPLY_FILTER_RULES_EVT_RESULT(self, self.OnApplyFilterRulesEnd)

        self.included_words_panel.words_list.SetDropTarget(WordsTextDropTarget(Constants.FILTER_RULE_INCLUDE, self.removed_words_panel.words_list, self))
        self.removed_words_panel.words_list.SetDropTarget(WordsTextDropTarget(Constants.FILTER_RULE_REMOVE, self.included_words_panel.words_list, self))

        logger.info("Finished")

    ######
    #functions called by the interface
    ######

    def OnRemoveRows(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveRows")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            new_rules = []
            for row in selection:
                word = self.included_words_panel.words_list.GetCellValue(row, 0)
                pos = self.included_words_panel.words_list.GetCellValue(row, 1)
                new_rules.append((Constants.FILTER_RULE_ANY, word, pos, Constants.FILTER_RULE_REMOVE))
            if self.rules_panel.autoapply:
                for new_rule in new_rules:
                    self.dataset.AddFilterRule(new_rule)
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyFilterNewRulesStart(new_rules)
            else:
                self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")

    def OnAddRows(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnAddRows")
        logger.info("Starting")
        selection = self.removed_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            new_rules = []
            for row in selection:
                word = self.removed_words_panel.words_list.GetCellValue(row, 0)
                pos = self.removed_words_panel.words_list.GetCellValue(row, 1)
                new_rules.append((Constants.FILTER_RULE_ANY, word, pos, Constants.FILTER_RULE_INCLUDE))
            if self.rules_panel.autoapply:
                for new_rule in new_rules:
                    self.dataset.AddFilterRule(new_rule)
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyFilterNewRulesStart(new_rules)
            else:
                self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")

    def OnRemoveWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemoveWords")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            new_rules = []
            for row in selection:
                word = self.included_words_panel.words_list.GetCellValue(row, 0)
                new_rules.append((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
            if self.rules_panel.autoapply:
                for new_rule in new_rules:
                    self.dataset.AddFilterRule(new_rule)
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyFilterNewRulesStart(new_rules)
            else:
                self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")

    def OnAddWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnAddWords")
        logger.info("Starting")
        selection = self.removed_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            new_rules = []
            for row in selection:
                word = self.removed_words_panel.words_list.GetCellValue(row, 0)
                new_rules.append((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_INCLUDE))
            if self.rules_panel.autoapply:
                for new_rule in new_rules:
                    self.dataset.AddFilterRule(new_rule)
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyFilterNewRulesStart(new_rules)
            else:
                self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")

    def OnRemovePOS(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnRemovePOS")
        logger.info("Starting")
        selection = self.included_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            new_rules = []
            for row in selection:
                pos = self.included_words_panel.words_list.GetCellValue(row, 1)
                new_rules.append((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, pos, Constants.FILTER_RULE_REMOVE))
            if self.rules_panel.autoapply:
                for new_rule in new_rules:
                    self.dataset.AddFilterRule(new_rule)
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyFilterNewRulesStart(new_rules)
            else:
                self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")

    def OnAddPOS(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnAddPOS")
        logger.info("Starting")
        selection = self.removed_words_panel.words_list.GetSelectedRows()
        if len(selection) > 0:
            new_rules = []
            for row in selection:
                pos = self.removed_words_panel.words_list.GetCellValue(row, 1)
                new_rules.append((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, pos, Constants.FILTER_RULE_INCLUDE))
            if self.rules_panel.autoapply:
                for new_rule in new_rules:
                    self.dataset.AddFilterRule(new_rule)
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyFilterNewRulesStart(new_rules)
            else:
                self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")

    def OnCreateCustomRule(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnCreateCustomRule")
        logger.info("Starting")
        #custom dialog to choose direction (greater or less), number, and words or docs
        with CreateCustomRuleDialog(self, self.dataset) as create_dialog:
            if create_dialog.ShowModal() == wx.ID_OK:
                rule = create_dialog.action
                new_rule = (create_dialog.field, create_dialog.word, create_dialog.pos, rule)
                if self.rules_panel.autoapply:
                    self.dataset.AddFilterRule(new_rule)
                    self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                    self.ApplyFilterNewRulesStart([new_rule])
                else:
                    self.rules_panel.DraftNewFilterRules([new_rule])
        logger.info("Finished")
    
    def OnRemoveSpacyAutoStopword(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnSpacyAutoStopword")
        logger.info("Starting")
        new_rule = (Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS)
        if self.rules_panel.autoapply:
            self.dataset.AddFilterRule(new_rule)
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyFilterNewRulesStart([new_rule])
        else:
            self.rules_panel.DraftNewFilterRules([new_rule])
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
                new_rule = (create_dialog.field, create_dialog.word, create_dialog.pos, rule)
                if self.rules_panel.autoapply:
                    self.dataset.AddFilterRule(new_rule)
                    self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                    self.ApplyFilterNewRulesStart([new_rule])
                else:
                    self.rules_panel.DraftNewFilterRules([new_rule])
        logger.info("Finished")
    
    def OnCreateTfidfFilter(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnCreateTfidfFilter")
        logger.info("Starting")
        with CreateTfidfFilterDialog(self, self.dataset) as create_dialog:
            if create_dialog.ShowModal() == wx.ID_OK:
                rule = (create_dialog.action1,
                        create_dialog.action2,
                        create_dialog.rank,)
                new_rule = (create_dialog.field, create_dialog.word, create_dialog.pos, rule)
                if self.rules_panel.autoapply:
                    self.dataset.AddFilterRule(new_rule)
                    self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                    self.ApplyFilterNewRulesStart([new_rule])
                else:
                    self.rules_panel.DraftNewFilterRules([new_rule])
        logger.info("Finished")

    def OnDeleteRule(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnDeleteRule")
        logger.info("Starting")
        removed_rule_idxs = []
        selected_item = self.rules_panel.rules_list.GetFirstSelected()
        while selected_item != -1:
            removed_rule_idxs.append(selected_item)
            selected_item = self.rules_panel.rules_list.GetNextSelected(selected_item)
        if len(removed_rule_idxs) > 0:
            if self.rules_panel.autoapply:
                for idx in reversed(removed_rule_idxs):
                    del self.dataset.filter_rules[idx]
                    self.dataset.last_changed_dt = datetime.now()
                self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                self.ApplyFilterAllRulesStart()
            else:
                self.rules_panel.DraftRemovedFilterRules(removed_rule_idxs)
        logger.info("Finished")
 
    def OnImportNLTKStopWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportNLTKStopWords")
        logger.info("Starting")
        if self.dataset.language == 'fre-sm':
            nltk_stopwords = set(nltk.corpus.stopwords.words('french'))
        elif self.dataset.language == 'eng-sm':
            nltk_stopwords = set(nltk.corpus.stopwords.words('english'))
        new_rules = []
        for word in nltk_stopwords:
            new_rules.append((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
        if self.rules_panel.autoapply:
            for new_rule in new_rules:
                self.dataset.AddFilterRule(new_rule)
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyFilterNewRulesStart(new_rules)
        else:
            self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")

    def OnImportSpacyStopWords(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportSpacyStopWords")
        logger.info("Starting")
        if self.dataset.language == 'fre-sm':
            spacy_stopwords = spacy.lang.fr.stop_words.STOP_WORDS
        elif self.dataset.language == 'eng-sm':
            spacy_stopwords = spacy.lang.en.stop_words.STOP_WORDS
        new_rules = []
        for word in spacy_stopwords:
            new_rules.append((Constants.FILTER_RULE_ANY, word, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE))
        if self.rules_panel.autoapply:
            for new_rule in new_rules:
                self.dataset.AddFilterRule(new_rule)
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.ApplyFilterNewRulesStart(new_rules)
        else:
            self.rules_panel.DraftNewFilterRules(new_rules)
        logger.info("Finished")
 
    def OnImportFilterRules(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnImportRemovalSettings")
        logger.info("Starting")
        confirm_dialog = wx.MessageDialog(self, GUIText.FILTERS_IMPORT_CONFIRMATION_REQUEST,
                                          GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        confirm_dialog.SetOKLabel(GUIText.FILTERS_IMPORT)
        if confirm_dialog.ShowModal() == wx.ID_OK:
            # otherwise ask the user what new file to open
            with wx.FileDialog(self, GUIText.FILTERS_IMPORT, defaultDir=Constants.SAVED_WORKSPACES_PATH,
                            wildcard="Rules JSON files (*.rules_json)|*.rules_json",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                # cancel if the user changed their mind
                if file_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                # Proceed loading the file chosen by the user
                pathname = file_dialog.GetPath()
                try:
                    with open(pathname, 'r') as file:
                        new_rules = jsonpickle.decode(json.load(file))
                        if self.rules_panel.autoapply:
                            self.dataset.filter_rules = new_rules
                            self.dataset.last_changed_dt = datetime.now()
                            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                            self.ApplyFilterAllRulesStart()
                        else:
                            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
                            self.rules_panel.DraftRemovedFilterRules(range(0, len(self.dataset.filter_rules)))
                            self.rules_panel.DraftNewFilterRules(new_rules)
                except IOError:
                    wx.LogError("Cannot open file '%s'", self.saved_name)
                    logger.error("Failed to open file '%s'", self.saved_name)
        logger.info("Finished")

    def OnPauseRules(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnPauseRules")
        logger.info("Starting")
        self.rules_panel.autoapply = not self.rules_panel.autoapply
        if not self.rules_panel.autoapply:
            self.rules_panel.pauserules_tool.SetLabel(GUIText.FILTERS_AUTOAPPLY_RESUME)
        else:
            self.rules_panel.pauserules_tool.SetLabel(GUIText.FILTERS_AUTOAPPLY_PAUSE)
            menuitems = self.rules_panel.pauserules_menu.GetMenuItems()
            if self.rules_panel.applyrules_menuitem in menuitems:
                self.rules_panel.pauserules_menu.Remove(self.rules_panel.applyrules_menuitem)
            if self.rules_panel.cancelrules_menuitem in menuitems:
                self.rules_panel.pauserules_menu.Remove(self.rules_panel.cancelrules_menuitem)
            self.dataset.filter_rules = self.rules_panel.GetDraftedRules()
            self.dataset.last_changed_dt = datetime.now()
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
            self.autosave = True
            self.ApplyFilterAllRulesStart()
        logger.info("Finished")
    
    def OnCancelRules(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnCancelRules")
        logger.info("Starting")
        self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
        menuitems = self.rules_panel.pauserules_menu.GetMenuItems()
        if self.rules_panel.applyrules_menuitem in menuitems:
            self.rules_panel.pauserules_menu.Remove(self.rules_panel.applyrules_menuitem)
        if self.rules_panel.cancelrules_menuitem in menuitems:
            self.rules_panel.pauserules_menu.Remove(self.rules_panel.cancelrules_menuitem)
        logger.info("Finished")
    
    def OnApplyRules(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnApplyRules")
        logger.info("Starting")
        self.dataset.filter_rules = self.rules_panel.GetDraftedRules()
        self.dataset.last_changed_dt = datetime.now()
        self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)
        menuitems = self.rules_panel.pauserules_menu.GetMenuItems()
        if self.rules_panel.applyrules_menuitem in menuitems:
            self.rules_panel.pauserules_menu.Remove(self.rules_panel.applyrules_menuitem)
        if self.rules_panel.cancelrules_menuitem in menuitems:
            self.rules_panel.pauserules_menu.Remove(self.rules_panel.cancelrules_menuitem)
        self.autosave = True
        self.ApplyFilterAllRulesStart()
        logger.info("Finished")

    def OnExportFilterRules(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnExportRemovalSettings")
        logger.info("Starting")
        with wx.FileDialog(self, GUIText.FILTERS_EXPORT, defaultDir=Constants.SAVED_WORKSPACES_PATH,
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

    def OnTokenizationChoiceStart(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnTokenizationChoiceStart")
        logger.info("Starting")
        choice = self.rules_panel.tokenization_choice.GetSelection()
        if choice != self.dataset.tokenization_choice:
            self.Freeze()
            main_frame = wx.GetApp().GetTopWindow()
            main_frame.CreateProgressDialog(GUIText.FILTERS_CHANGING_TOKENIZATION_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
            self.dataset.tokenization_choice = choice
            if choice == Constants.TOKEN_TEXT_IDX:
                new_choice = 'text'
            elif choice == Constants.TOKEN_STEM_IDX:
                new_choice = 'stem'
            elif choice == Constants.TOKEN_LEMMA_IDX:
                new_choice = 'lemma'
            self.thread = DatasetsThreads.ChangeTokenizationChoiceThread(self, main_frame, self.dataset, new_choice)
        logger.info("Finished")

    def OnTokenizationChoiceEnd(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnTokenizationChoiceEnd")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.thread.join()
        self.thread = None
        
        self.UpdateImpact()

        main_frame.AutoSaveStart()
        main_frame.CloseProgressDialog(thaw=False)
        self.Thaw()
        logger.info("Finished")

    def ApplyFilterAllRulesStart(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].ApplyFilterAllRulesStart")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.FILTERS_APPLYING_RULES_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        self.Freeze()
        self.thread = DatasetsThreads.ApplyFilterAllRulesThread(self, main_frame, self.dataset)
        logger.info("Finished")

    def ApplyFilterNewRulesStart(self, new_rules):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].ApplyFilterNewRulesStart")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.CreateProgressDialog(GUIText.FILTERS_APPLYING_RULES_BUSY_LABEL,
                                        warning=GUIText.SIZE_WARNING_MSG,
                                        freeze=False)
        self.Freeze()
        self.thread = DatasetsThreads.ApplyFilterNewRulesThread(self, main_frame, self.dataset, new_rules)
        logger.info("Finished")

    def OnApplyFilterRulesEnd(self, event):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].OnApplyFilterRulesEnd")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.thread.join()
        self.thread = None
        self.UpdateImpact()

        if self.autosave:
            self.autosave = False
            main_frame.AutoSaveStart()
        self.Thaw()
        self.rules_panel.toolbar.Realize()
        main_frame.CloseProgressDialog(thaw=False)
        logger.info("Finished")
    
    def UpdateImpact(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].UpdateImpact")
        logger.info("Starting")
        self.included_words_panel.UpdateWords()
        self.removed_words_panel.UpdateWords()
        self.rules_panel.document_num_original.SetLabel(str(self.dataset.total_docs))
        self.rules_panel.token_num_original.SetLabel(str(self.dataset.total_tokens))
        self.rules_panel.uniquetoken_num_original.SetLabel(str(self.dataset.total_uniquetokens))
        self.rules_panel.document_num_remaining.SetLabel(str(self.dataset.total_docs_remaining))
        self.rules_panel.token_num_remaining.SetLabel(str(self.dataset.total_tokens_remaining))
        self.rules_panel.uniquetoken_num_remaining.SetLabel(str(self.dataset.total_uniquetokens_remaining))
        logger.info("Finished")

    #Required Functions
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].Load")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(GUIText.LOAD_FILTERING_BUSY_MSG+str(self.name))

        self.rules_panel.tokenization_choice.SetSelection(self.dataset.tokenization_choice)

        if 'included_search_word' in saved_data:
            self.included_words_panel.searchctrl.SetValue(saved_data['included_search_word'])
        if 'removed_search_word' in saved_data:
            self.removed_words_panel.searchctrl.SetValue(saved_data['removed_search_word'])
        
        if 'autoapply' in saved_data:
            self.rules_panel.autoapply = saved_data['autoapply']
        if not self.rules_panel.autoapply:
            self.rules_panel.pauserules_tool.SetLabel(GUIText.FILTERS_AUTOAPPLY_RESUME)
        else:
            self.rules_panel.pauserules_tool.SetLabel(GUIText.FILTERS_AUTOAPPLY_PAUSE)
        
        if not self.rules_panel.autoapply and 'draft_rules' in saved_data:
            self.rules_panel.DisplayDraftFilterRules(saved_data['draft_rules'])
        else:
            self.rules_panel.DisplayFilterRules(self.dataset.filter_rules)

        self.UpdateImpact()

        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".FilterPanel["+str(self.name)+"].Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['included_search_word'] = self.included_words_panel.searchctrl.GetValue()
        saved_data['removed_search_word'] = self.removed_words_panel.searchctrl.GetValue()
        saved_data['autoapply'] = self.rules_panel.autoapply
        if not self.rules_panel.autoapply:
            saved_data['draft_rules'] = self.rules_panel.current_rules
        logger.info("Finished")
        return saved_data

#TODO continue converting to virutal backed onto database
# differeniate between included and removed
class WordsPanel(wx.Panel):
    def __init__(self, parent, parent_frame, dataset, word_type, style):
        logger = logging.getLogger(__name__+".WordsPanel["+word_type+"]["+str(parent_frame.name)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, style=style)
        self.parent_frame = parent_frame
        self.dataset = dataset 
        self.word_type = word_type

        main_frame = wx.GetApp().GetTopWindow()
        
        self.col_names = [GUIText.FILTERS_WORDS,
                          GUIText.FILTERS_POS,
                          GUIText.FILTERS_NUM_WORDS,
                          GUIText.FILTERS_PER_WORDS,
                          GUIText.FILTERS_NUM_DOCS,
                          GUIText.FILTERS_PER_DOCS,
                          GUIText.FILTERS_TFIDF_MIN,
                          GUIText.FILTERS_TFIDF_MAX]

        #setup the included entries panel
        #self.SetScrollbars(1, 1, 1, 1)
        #border and Label for area
        self.label_box = wx.StaticBox(self, label="")
        self.label_box.SetFont(main_frame.GROUP_LABEL_FONT)
        sizer = wx.StaticBoxSizer(self.label_box, wx.VERTICAL)

        #create search sizer
        search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.searchctrl = wx.SearchCtrl(self)
        self.searchctrl.Bind(wx.EVT_SEARCH, self.OnSearch)
        self.searchctrl.Bind(wx.EVT_SEARCH_CANCEL, self.OnSearchCancel)
        self.searchctrl.SetDescriptiveText(GUIText.SEARCH)
        self.searchctrl.ShowCancelButton(True)
        extent = self.searchctrl.GetTextExtent(GUIText.FILTERS_WORD_SEARCH)
        size = self.searchctrl.GetSizeFromTextSize(extent.GetWidth()*2, -1)
        self.searchctrl.SetMinSize(size)
        search_sizer.Add(self.searchctrl, 0, wx.ALL, 5)
        self.search_count_text = wx.StaticText(self)
        search_sizer.Add(self.search_count_text, 0, wx.ALL|wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer.Add(search_sizer, flag=wx.ALIGN_LEFT)
        #create the list to be shown
        self.words_list = TokenDataViews.TokenGrid(self, self.dataset, word_type)
        sizer.Add(self.words_list, proportion=0, flag=wx.EXPAND, border=5)

        border = wx.BoxSizer()
        border.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(border)
        logger.info("Finished")

    def OnSearch(self, event):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].OnSearch")
        logger.info("Starting")
        self.DisplayWordsList()
        self.search_count_text.SetLabel(str(self.words_list.GetNumberRows())+GUIText.SEARCH_RESULTS_LABEL)
        self.Layout()
        logger.info("Finished")

    def OnSearchCancel(self, event):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].OnSearchCancel")
        logger.info("Starting")
        search_ctrl = event.GetEventObject()
        search_ctrl.SetValue("")
        self.DisplayWordsList()
        if self.searchctrl.GetValue() == "":
            self.search_count_text.SetLabel("")
        else:
            self.search_count_text.SetLabel(str(self.words_list.GetNumberRows())+GUIText.SEARCH_RESULTS_LABEL)
        self.Layout()
        logger.info("Finished")

    def UpdateWords(self):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].UpdateWords")
        logger.info("Starting")
        self.DisplayWordsList()
        logger.info("Finished")

    def DisplayWordsList(self):
        logger = logging.getLogger(__name__+".WordsPanel["+self.word_type+"]["+str(self.parent_frame.name)+"].DisplayWordsList")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        self.Freeze()
        main_frame.PulseProgressDialog(GUIText.FILTERS_DISPLAY_STRINGS_BUSY_MSG1+self.word_type+GUIText.FILTERS_DISPLAY_STRINGS_BUSY_MSG2+str(self.parent_frame.name))
        try:
            search_term = self.searchctrl.GetValue()
            self.words_list.Update(search_term)
        finally:
            self.Thaw()
        logger.info("Finished")

class IncludedWordsPanel(WordsPanel):
    def __init__(self, parent, parent_frame, dataset, style):
        logger = logging.getLogger(__name__+".IncludedWordsPanel["+str(parent_frame.name)+"]__init__")
        logger.info("Starting")
        WordsPanel.__init__(self, parent, parent_frame, dataset, "Included", style=style)
        self.label_box.SetLabel(GUIText.FILTERS_INCLUDED_LIST)

        self.words_list.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.OnDragStart)
        self.words_list.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnPopupMenu)

        self.words_list.EnableDragCell()

        logger.info("Finished")

    def OnDragStart(self, event):
        row = event.GetRow()
        selected = self.words_list.GetSelectedRows()
        if row not in selected:
            for selected_row in selected:
                self.words_list.DeselectRow(selected_row)
            self.words_list.SelectRow(row)
            selected = self.words_list.GetSelectedRows()
        
        tobj = wx.TextDataObject(Constants.FILTER_RULE_REMOVE)
        src = wx.DropSource(self.words_list)
        self.parent_frame.drag_source = self.words_list
        src.SetData(tobj) 
        src.DoDragDrop(True)
    
    def OnPopupMenu(self, event):
        row = event.GetRow()
        selected = self.words_list.GetSelectedRows()
        if row not in selected:
            for selected_row in selected:
                self.words_list.DeselectRow(selected_row)
            self.words_list.SelectRow(row)
        popup_menu = wx.Menu()
        rows_menuitem = popup_menu.Append(wx.ID_ANY, GUIText.FILTERS_REMOVE_ROWS, GUIText.FILTERS_REMOVE_ROWS_TOOLTIP)
        popup_menu.Bind(wx.EVT_MENU, self.parent_frame.OnRemoveRows, rows_menuitem)
        words_menuitem = popup_menu.Append(wx.ID_ANY, GUIText.FILTERS_REMOVE_WORDS, GUIText.FILTERS_REMOVE_WORDS_TOOLTIP)
        popup_menu.Bind(wx.EVT_MENU, self.parent_frame.OnRemoveWords, words_menuitem)
        pos_menuitem = popup_menu.Append(wx.ID_ANY, GUIText.FILTERS_REMOVE_POS, GUIText.FILTERS_REMOVE_POS_TOOLTIP)
        popup_menu.Bind(wx.EVT_MENU, self.parent_frame.OnRemovePOS, pos_menuitem)
        self.words_list.PopupMenu(popup_menu)

class RemovedWordsPanel(WordsPanel):
    def __init__(self, parent, parent_frame, dataset, style):
        logger = logging.getLogger(__name__+".RemovedWordsPanel["+str(parent_frame.name)+"].__init__")
        logger.info("Starting")

        WordsPanel.__init__(self, parent, parent_frame, dataset, "Removed", style=style)
        self.label_box.SetLabel(GUIText.FILTERS_REMOVED_LIST)

        self.words_list.Bind(wx.grid.EVT_GRID_CELL_BEGIN_DRAG, self.OnDragStart)
        self.words_list.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnPopupMenu)

        self.words_list.EnableDragCell()
        
        logger.info("Finished")

    def OnDragStart(self, event):
        row = event.GetRow()
        selected = self.words_list.GetSelectedRows()
        if row not in selected:
            for selected_row in selected:
                self.words_list.DeselectRow(selected_row)
            self.words_list.SelectRow(row)
            selected = self.words_list.GetSelectedRows()
        
        tobj = wx.TextDataObject(Constants.FILTER_RULE_INCLUDE)
        src = wx.DropSource(self.words_list) 
        self.parent_frame.drag_source = self.words_list
        src.SetData(tobj) 
        src.DoDragDrop(True)
    
    def OnPopupMenu(self, event):
        row = event.GetRow()
        selected = self.words_list.GetSelectedRows()
        if row not in selected:
            for selected_row in selected:
                self.words_list.DeselectRow(selected_row)
            self.words_list.SelectRow(row)
        popup_menu = wx.Menu()
        rows_menuitem = popup_menu.Append(wx.ID_ANY, GUIText.FILTERS_ADD_ROWS, GUIText.FILTERS_ADD_ENTRIES_TOOLTIP)
        popup_menu.Bind(wx.EVT_MENU, self.parent_frame.OnAddRows, rows_menuitem)
        words_menuitem = popup_menu.Append(wx.ID_ANY, GUIText.FILTERS_ADD_WORDS, GUIText.FILTERS_ADD_WORDS_TOOLTIP)
        popup_menu.Bind(wx.EVT_MENU, self.parent_frame.OnAddWords, words_menuitem)
        pos_menuitem = popup_menu.Append(wx.ID_ANY, GUIText.FILTERS_ADD_POS, GUIText.FILTERS_ADD_POS_TOOLTIP)
        popup_menu.Bind(wx.EVT_MENU, self.parent_frame.OnAddPOS, pos_menuitem)
        self.words_list.PopupMenu(popup_menu)

class WordsTextDropTarget(wx.TextDropTarget):
    def __init__(self, action, source, filter_panel):
        wx.TextDropTarget.__init__(self)
        self.action = action
        self.source = source
        self.filter_panel = filter_panel
    
    def OnDragOver(self, x, y, defResult):
        res = super().OnDragOver(x, y, defResult)
        if self.source == self.filter_panel.drag_source:
            return res
        return wx.DragNone
        
    def OnDropText(self, x, y, data):
        if self.action == Constants.FILTER_RULE_REMOVE:
            if self.action == data:
                self.filter_panel.OnRemoveRows(None)
        elif self.action == Constants.FILTER_RULE_INCLUDE:
            if self.action == data:
                self.filter_panel.OnAddRows(None)
        return True

class RulesPanel(wx.Panel):
    '''For rendering nlp word data'''
    def __init__(self, parent, parent_frame, style):
        logger = logging.getLogger(__name__+".RulesPanel["+str(parent_frame.name)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, style=style)
        self.parent_frame = parent_frame

        main_frame = wx.GetApp().GetTopWindow()

        self.autoapply = True
        self.current_rules = []

        package_list = list(self.parent_frame.dataset.tokenization_package_versions)
        tokenizer_package = self.parent_frame.dataset.tokenization_package_versions[0]
        package_list[0] = GUIText.FILTERS_RAWTOKENS
        package_list[1] = GUIText.FILTERS_STEMMER+": "+package_list[1]
        package_list[2] = GUIText.FILTERS_LEMMATIZER+": "+package_list[2]

        #Label for area
        label_box = wx.StaticBox(self, label=GUIText.FILTERS_RULES_LIST)
        label_box.SetFont(main_frame.GROUP_LABEL_FONT)
        
        sizer = wx.StaticBoxSizer(label_box, wx.VERTICAL)

        tokenization_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(tokenization_sizer)
        tokenization_package_label1 = wx.StaticText(self, label=GUIText.FILTERS_TOKENIZER)
        tokenization_package_label1.SetFont(main_frame.DETAILS_LABEL_FONT)
        tokenization_sizer.Add(tokenization_package_label1, proportion=0, flag=wx.ALL, border=5)
        self.tokenization_package_label2 = wx.StaticText(self, label=tokenizer_package)
        tokenization_sizer.Add(self.tokenization_package_label2, proportion=0, flag=wx.ALL, border=5)
        tokenization_choice_label = wx.StaticText(self, label=GUIText.FILTERS_METHOD)
        tokenization_choice_label.SetFont(main_frame.DETAILS_LABEL_FONT)
        tokenization_sizer.Add(tokenization_choice_label, proportion=0, flag=wx.ALL, border=5)
        self.tokenization_choice = wx.Choice(self, choices=package_list)
        self.tokenization_choice.SetSelection(self.parent_frame.dataset.tokenization_choice)
        self.tokenization_choice.Bind(wx.EVT_CHOICE, self.parent_frame.OnTokenizationChoiceStart)
        tokenization_sizer.Add(self.tokenization_choice, proportion=0, flag=wx.ALL, border=5)
        
        self.toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_HORZ_TEXT|wx.TB_NOICONS)

        self.pauserules_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_AUTOAPPLY_PAUSE,
                                                    bitmap=wx.Bitmap(1,1),
                                                    shortHelp=GUIText.FILTERS_AUTOAPPLY_TOOLTIP,
                                                    kind=wx.ITEM_DROPDOWN)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnPauseRules, self.pauserules_tool)
        
        self.pauserules_menu = wx.Menu()
        self.applyrules_menuitem = self.pauserules_menu.Append(wx.ID_APPLY, GUIText.FILTERS_MANUALAPPLY,
                                                               GUIText.FILTERS_MANUALAPPLY_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnApplyRules, self.applyrules_menuitem)
        self.cancelrules_menuitem = self.pauserules_menu.Append(wx.ID_CANCEL, GUIText.FILTERS_MANUALCANCEL,
                                                                GUIText.FILTERS_MANUALCANCEL_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnCancelRules, self.cancelrules_menuitem)
        self.pauserules_menu.Remove(self.applyrules_menuitem)
        self.pauserules_menu.Remove(self.cancelrules_menuitem)
        self.pauserules_tool.SetDropdownMenu(self.pauserules_menu)

        self.toolbar.AddSeparator()
        
        customrules_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_CREATE_RULE, bitmap=wx.Bitmap(1,1),
                                                shortHelp=GUIText.FILTERS_CREATE_RULE_TOOLTIP, kind=wx.ITEM_DROPDOWN)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnCreateCustomRule, customrules_tool)
        customrules_menu = wx.Menu()
        spacyautoremove_menuitem = customrules_menu.Append(wx.ID_ANY, GUIText.FILTERS_REMOVE_SPACY_AUTO_STOPWORDS,
                                                           GUIText.FILTERS_REMOVE_SPACY_AUTO_STOPWORDS_TOOLTIP)
        customrules_menu.Bind(wx.EVT_MENU, self.parent_frame.OnRemoveSpacyAutoStopword, spacyautoremove_menuitem)
        countfilter_menuitem = customrules_menu.Append(wx.ID_ANY, GUIText.FILTERS_CREATE_COUNT_RULE,
                                                       GUIText.FILTERS_CREATE_COUNT_RULE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnCreateCountFilter, countfilter_menuitem)
        tfidffilter_menuitem = customrules_menu.Append(wx.ID_ANY, GUIText.FILTERS_CREATE_TFIDF_RULE,
                                                       GUIText.FILTERS_CREATE_TFIDF_RULE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnCreateTfidfFilter, tfidffilter_menuitem)
        customrules_tool.SetDropdownMenu(customrules_menu)
        
        remove_tool = self.toolbar.AddTool(wx.ID_ANY, label=GUIText.FILTERS_RULES_DELETE,
                                           bitmap=wx.Bitmap(1, 1),
                                           shortHelp=GUIText.FILTERS_RULE_DELETE_TOOLTIP)
        self.toolbar.Bind(wx.EVT_MENU, self.parent_frame.OnDeleteRule, remove_tool)

        self.toolbar.Realize()
        sizer.Add(self.toolbar, proportion=0, flag=wx.ALL, border=5)

        self.rules_list = DatasetsGUIs.FilterRuleListCtrl(self)
        sizer.Add(self.rules_list, proportion=1, flag=wx.EXPAND, border=5)

        impact_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(impact_sizer)

        document_num_sizer = wx.BoxSizer()
        document_num_label1 = wx.StaticText(self, label=GUIText.FILTERS_NUM_DOCS+":")
        document_num_sizer.Add(document_num_label1, 0, wx.ALL, 5)
        self.document_num_remaining = wx.StaticText(self, label="")
        document_num_sizer.Add(self.document_num_remaining, 0, wx.ALL, 5)
        document_num_label2 = wx.StaticText(self, label=" / ")
        document_num_sizer.Add(document_num_label2, 0, wx.ALL, 5)
        self.document_num_original = wx.StaticText(self, label="")
        document_num_sizer.Add(self.document_num_original, 0, wx.ALL, 5)
        impact_sizer.Add(document_num_sizer)

        token_num_sizer = wx.BoxSizer()
        token_num_label1 = wx.StaticText(self, label=GUIText.FILTERS_NUM_WORDS+":")
        token_num_sizer.Add(token_num_label1, 0, wx.ALL, 5)
        self.token_num_remaining = wx.StaticText(self, label="")
        token_num_sizer.Add(self.token_num_remaining, 0, wx.ALL, 5)
        token_num_label2 = wx.StaticText(self, label=" / ")
        token_num_sizer.Add(token_num_label2, 0, wx.ALL, 5)
        self.token_num_original = wx.StaticText(self, label="")
        token_num_sizer.Add(self.token_num_original, 0, wx.ALL, 5)
        impact_sizer.Add(token_num_sizer)

        uniquetoken_num_sizer = wx.BoxSizer()
        uniquetoken_num_label1 = wx.StaticText(self, label=GUIText.FILTERS_NUM_UNIQUEWORDS+":")
        uniquetoken_num_sizer.Add(uniquetoken_num_label1, 0, wx.ALL, 5)
        self.uniquetoken_num_remaining = wx.StaticText(self, label="")
        uniquetoken_num_sizer.Add(self.uniquetoken_num_remaining, 0, wx.ALL, 5)
        uniquetoken_num_label2 = wx.StaticText(self, label=" / ")
        uniquetoken_num_sizer.Add(uniquetoken_num_label2, 0, wx.ALL, 5)
        self.uniquetoken_num_original = wx.StaticText(self, label="")
        uniquetoken_num_sizer.Add(self.uniquetoken_num_original, 0, wx.ALL, 5)
        impact_sizer.Add(uniquetoken_num_sizer)

        border = wx.BoxSizer()
        border.Add(sizer, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizerAndFit(border)

        self.rules_list.SetDropTarget(RulesTextDropTarget(self.rules_list, self.parent_frame))
        self.rules_list.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnDragStart)

        logger.info("Finished")

    def DisplayFilterRules(self, filter_rules):
        package_list = list(self.parent_frame.dataset.tokenization_package_versions)
        tokenizer_package = self.parent_frame.dataset.tokenization_package_versions[0]
        package_list[0] = GUIText.FILTERS_RAWTOKENS
        package_list[1] = GUIText.FILTERS_STEMMER+": "+package_list[1]
        package_list[2] = GUIText.FILTERS_LEMMATIZER+": "+package_list[2]

        self.tokenization_package_label2.SetLabel(tokenizer_package)
        self.tokenization_choice.SetString(0, package_list[0])
        self.tokenization_choice.SetString(1, package_list[1])
        self.tokenization_choice.SetString(2, package_list[2])

        self.current_rules = []
        for rule in filter_rules:
            self.current_rules.append([rule, ""])

        column_options = {Constants.TOKEN_NUM_WORDS:GUIText.FILTERS_NUM_WORDS,
                          Constants.TOKEN_PER_WORDS:GUIText.FILTERS_PER_WORDS,
                          Constants.TOKEN_NUM_DOCS:GUIText.FILTERS_NUM_DOCS,
                          Constants.TOKEN_PER_DOCS:GUIText.FILTERS_PER_DOCS}
        self.rules_list.DeleteAllItems()
        i = 0
        for field, word, pos, action in filter_rules:
            i += 1
            if isinstance(action, tuple):
                if action[0] == Constants.FILTER_TFIDF_REMOVE or action[0] == Constants.FILTER_TFIDF_INCLUDE:
                    action = str(action[0])+str(action[1])+str(action[2])+"%"
                else:
                    action = str(action[0]) + " ("+str(column_options[action[1]])+str(action[2])+str(action[3])+")"
            self.rules_list.Append([str(i), field, word, pos, str(action)])
        self.rules_list.AutoSizeColumns()
        self.Refresh()
    
    def DisplayDraftFilterRules(self, draft_rules=None):
        if draft_rules != None:
            self.current_rules = draft_rules
        column_options = {Constants.TOKEN_NUM_WORDS:GUIText.FILTERS_NUM_WORDS,
                          Constants.TOKEN_PER_WORDS:GUIText.FILTERS_PER_WORDS,
                          Constants.TOKEN_NUM_DOCS:GUIText.FILTERS_NUM_DOCS,
                          Constants.TOKEN_PER_DOCS:GUIText.FILTERS_PER_DOCS}
        self.rules_list.DeleteAllItems()
        i = 0
        num_changed = 0
        for rule, state in self.current_rules:
            i += 1
            field = rule[0]
            word = rule[1]
            pos = rule[2]
            action = rule[3]
            if isinstance(action, tuple):
                if action[0] == Constants.FILTER_TFIDF_REMOVE or action[0] == Constants.FILTER_TFIDF_INCLUDE:
                    action = str(action[0])+str(action[1])+str(action[2])+"%"
                else:
                    action = str(action[0]) + " ("+str(column_options[action[1]])+str(action[2])+str(action[3])+")"
            self.rules_list.Append([str(i), field, word, pos, str(action)])
            if "R" in state:
                #D55E00
                self.rules_list.SetItemBackgroundColour(i-1, wx.Colour(red=213, green=94, blue=0))
                num_changed = num_changed + 1
            elif "A" in state:
                #009E73
                self.rules_list.SetItemBackgroundColour(i-1, wx.Colour(red=0, green=158, blue=115))
                num_changed = num_changed + 1
            elif "M" in state:
                #56B4E9
                self.rules_list.SetItemBackgroundColour(i-1, wx.Colour(red=86, green=180, blue=223))
                num_changed = num_changed + 1
        self.rules_list.AutoSizeColumns()
        
        if self.toolbar.FindById(wx.ID_APPLY) == None and num_changed > 0:
            menuitems = self.pauserules_menu.GetMenuItems()
            if self.applyrules_menuitem not in menuitems:
                self.pauserules_menu.Append(self.applyrules_menuitem)
            if self.cancelrules_menuitem not in menuitems:
                self.pauserules_menu.Append(self.cancelrules_menuitem)
        self.Refresh()

    def DraftNewFilterRules(self, new_rules):
        for new_rule in new_rules:
            self.current_rules.append([new_rule, "A"])
        self.DisplayDraftFilterRules()

    def DraftRemovedFilterRules(self, removed_idxs):
        for idx in removed_idxs:
            state = self.current_rules[idx][1]
            if "A" not in state:
                self.current_rules[idx][1] = state + "R"
            elif state == "A":
                self.current_rules.pop(idx)
        self.DisplayDraftFilterRules()
    
    def DraftMovedFilterRules(self, moved_idxs):
        for old_idx, new_idx in moved_idxs:
            state = self.current_rules[old_idx][1]
            if "M" not in state:
                state = state + "M"
                self.current_rules[old_idx][1] = state
            rule = self.current_rules.pop(old_idx)
            self.current_rules.insert(new_idx, rule)
        self.DisplayDraftFilterRules()
            
    def GetDraftedRules(self):
        rules = []
        for rule, state in self.current_rules:
            if "R" not in state:
                rules.append(rule)
        return rules

    def OnDragStart(self, event):
        text = str(event.GetIndex())
        tobj = wx.TextDataObject(text)
        src = wx.DropSource(self.rules_list) 
        self.parent_frame.drag_source = self.rules_list
        src.SetData(tobj) 
        src.DoDragDrop(True)

class RulesTextDropTarget(wx.TextDropTarget):
    def __init__(self, rule_list, filter_panel):
        wx.TextDropTarget.__init__(self)
        self.rule_list = rule_list
        self.filter_panel = filter_panel
    
    def OnDragOver(self, x, y, defResult):
        res = super().OnDragOver(x, y, defResult)
        if self.filter_panel.drag_source == self.rule_list:
            return res
        return wx.DragNone
    
    def OnDropText(self, x, y, data):
        old_idx = int(data)
        new_idx, where = self.rule_list.HitTest((x,y))
        if new_idx == -1:
            new_idx = self.rule_list.GetItemCount()-1
        if old_idx != new_idx:
            if self.filter_panel.rules_panel.autoapply:
                if old_idx < new_idx:
                    impacted_rules = self.filter_panel.dataset.filter_rules[old_idx+1:new_idx+1]
                else:
                    impacted_rules = self.filter_panel.dataset.filter_rules[new_idx:old_idx]
                
                rule = self.filter_panel.dataset.filter_rules.pop(old_idx)
                self.filter_panel.dataset.filter_rules.insert(new_idx, rule)
                self.filter_panel.dataset.last_changed_dt = datetime.now()
                action = rule[3]
                if isinstance(action, tuple):
                    action = action[0]
                    if action == Constants.FILTER_TFIDF_REMOVE:
                        action = Constants.FILTER_RULE_REMOVE
                    elif action == Constants.FILTER_TFIDF_INCLUDE:
                        action = Constants.FILTER_RULE_INCLUDE
                elif action == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                    action = Constants.FILTER_RULE_REMOVE
                apply_needed = False
                for reordered_rule in impacted_rules:
                    new_action = reordered_rule[3]
                    if isinstance(new_action, tuple):
                        new_action = new_action[0]
                        if new_action == Constants.FILTER_TFIDF_REMOVE:
                            new_action = Constants.FILTER_RULE_REMOVE
                        elif new_action == Constants.FILTER_TFIDF_INCLUDE:
                            new_action = Constants.FILTER_RULE_INCLUDE
                    elif new_action == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                        new_action = Constants.FILTER_RULE_REMOVE
                    if new_action != action:
                        apply_needed = True
                        break
                self.filter_panel.rules_panel.DisplayFilterRules(self.filter_panel.dataset.filter_rules)
                if apply_needed:
                    self.filter_panel.ApplyFilterAllRulesStart()
            else:    
                self.filter_panel.rules_panel.DraftMovedFilterRules([(old_idx, new_idx)])
        return True

class CreateCustomRuleDialog(wx.Dialog):
    def __init__(self, parent, dataset):
        logger = logging.getLogger(__name__+".CreateCustomRuleDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.FILTERS_CREATE_RULE)

        self.field_options = []
        self.field_options.append(GUIText.FILTER_CREATE_RULE_ANY)
        for field in dataset.computational_fields.values():
            self.field_options.append(field.name)
        action_options = [Constants.FILTER_RULE_REMOVE,
                          Constants.FILTER_RULE_INCLUDE]
        
        self.field = None
        self.word = None
        self.pos = None
        self.action = None
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        field_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_FIELD+" ")
        self.field_ctrl = wx.Choice(self, choices=self.field_options)
        self.field_ctrl.SetSelection(0)
        self.field_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_FIELD_TOOLTIP)
        field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        field_sizer.Add(field_label, 0, wx.ALIGN_CENTER_VERTICAL)
        field_sizer.Add(self.field_ctrl)
        sizer.Add(field_sizer, 0, wx.ALL, 5)

        word_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_WORD+" ")
        self.word_ctrl = wx.TextCtrl(self)
        self.word_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_WORD_TOOLTIP)
        self.word_ctrl.SetHint(GUIText.FILTER_CREATE_RULE_ANY)
        word_sizer = wx.BoxSizer(wx.HORIZONTAL)
        word_sizer.Add(word_label, 0, wx.ALIGN_CENTER_VERTICAL)
        word_sizer.Add(self.word_ctrl)
        sizer.Add(word_sizer, 0, wx.ALL, 5)

        pos_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_POS+" ")
        self.pos_ctrl = wx.TextCtrl(self)
        self.pos_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_POS_TOOLTIP)
        self.pos_ctrl.SetHint(GUIText.FILTER_CREATE_RULE_ANY)
        pos_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer.Add(pos_label, 0, wx.ALIGN_CENTER_VERTICAL)
        pos_sizer.Add(self.pos_ctrl)
        sizer.Add(pos_sizer, 0, wx.ALL, 5)

        rule_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_ACTION+" ")
        self.action_ctrl = wx.Choice(self, choices=action_options)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_label, 0, wx.ALIGN_CENTER_VERTICAL)
        rule_sizer.Add(self.action_ctrl)
        sizer.Add(rule_sizer, 0, wx.ALL, 5)

        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.SetLabel(GUIText.FILTERS_CREATE_RULE)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)
        sizer.Add(controls_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

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
        if self.field not in self.field_options:
            wx.MessageBox(GUIText.FILTERS_CREATE_RULE_FIELD_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('invalid field selected['+self.field+"]")
            status_flag = False
        elif self.field == GUIText.FILTER_CREATE_RULE_ANY:
            self.field = Constants.FILTER_RULE_ANY

        self.word = self.word_ctrl.GetValue()
        if self.word == "":
            self.word = Constants.FILTER_RULE_ANY
        self.pos = self.pos_ctrl.GetValue()
        if self.pos == "":
            self.pos = Constants.FILTER_RULE_ANY
        self.action = self.action_ctrl.GetStringSelection()
        if self.action == "":
            wx.MessageBox(GUIText.FILTERS_CREATE_RULE_INCOMPLETE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('rule incomplete action['+self.action+"]")
            status_flag = False

        logger.info("Finished")
        if status_flag:
            self.EndModal(wx.ID_OK)

class CreateCountFilterDialog(wx.Dialog):
    def __init__(self, parent, dataset):
        logger = logging.getLogger(__name__+".CreateCountFilterDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.FILTERS_CREATE_COUNT_RULE)

        self.field_options = []
        self.field_options.append(GUIText.FILTER_CREATE_RULE_ANY)
        for field in dataset.computational_fields.values():
            self.field_options.append(field.name)
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

        field_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_FIELD+" ")
        self.field_ctrl = wx.Choice(self, choices=self.field_options)
        self.field_ctrl.SetSelection(0)
        self.field_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_FIELD_TOOLTIP)
        field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        field_sizer.Add(field_label, 0, wx.ALIGN_CENTER_VERTICAL)
        field_sizer.Add(self.field_ctrl)
        sizer.Add(field_sizer, 0, wx.ALL, 5)

        word_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_WORD+" ")
        self.word_ctrl = wx.TextCtrl(self)
        self.word_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_WORD_TOOLTIP)
        self.word_ctrl.SetHint(GUIText.FILTER_CREATE_RULE_ANY)
        word_sizer = wx.BoxSizer(wx.HORIZONTAL)
        word_sizer.Add(word_label, 0, wx.ALIGN_CENTER_VERTICAL)
        word_sizer.Add(self.word_ctrl)
        sizer.Add(word_sizer,0, wx.ALL, 5)

        pos_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_POS+" ")
        self.pos_ctrl = wx.TextCtrl(self)
        self.pos_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_POS_TOOLTIP)
        self.pos_ctrl.SetHint(GUIText.FILTER_CREATE_RULE_ANY)
        pos_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer.Add(pos_label, 0, wx.ALIGN_CENTER_VERTICAL)
        pos_sizer.Add(self.pos_ctrl)
        sizer.Add(pos_sizer, 0, wx.ALL, 5)

        rule_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_ACTION+" ")
        self.action_ctrl = wx.Choice(self, choices=action_options)
        self.column_ctrl = wx.Choice(self, choices=list(self.column_options.keys()))
        self.column_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_COLUMN_TOOLTIP)
        self.operation_ctrl = wx.Choice(self, choices=operation_options)
        self.operation_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_OPERATION_TOOLTIP)
        self.number_ctrl = wx.SpinCtrlDouble(self, min=0, max=dataset.total_tokens, inc=0.01)
        self.number_ctrl.SetToolTip(GUIText.FILTERS_CREATE_COUNT_RULE_NUMBER_TOOLTIP)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_label, 0, wx.ALIGN_CENTER_VERTICAL)
        rule_sizer.Add(self.action_ctrl)
        rule_sizer.Add(self.column_ctrl)
        rule_sizer.Add(self.operation_ctrl)
        rule_sizer.Add(self.number_ctrl)
        sizer.Add(rule_sizer, 0, wx.ALL, 5)

        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.SetLabel(GUIText.FILTERS_CREATE_COUNT_RULE)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)
        sizer.Add(controls_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

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
        if self.field not in self.field_options:
            wx.MessageBox(GUIText.FILTERS_CREATE_RULE_FIELD_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('invalid field selected['+self.field+"]")
            status_flag = False
        elif self.field == GUIText.FILTER_CREATE_RULE_ANY:
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

        self.field_options = []
        self.field_options.append(GUIText.FILTER_CREATE_RULE_ANY)
        for field in dataset.computational_fields.values():
            self.field_options.append(field.name)
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

        field_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_FIELD+" ")
        self.field_ctrl = wx.Choice(self, choices=self.field_options)
        self.field_ctrl.SetSelection(0)
        self.field_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_FIELD_TOOLTIP)
        field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        field_sizer.Add(field_label, 0, wx.ALIGN_CENTER_VERTICAL)
        field_sizer.Add(self.field_ctrl)
        sizer.Add(field_sizer, 0, wx.ALL, 5)

        word_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_WORD+" ")
        self.word_ctrl = wx.TextCtrl(self)
        self.word_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_WORD_TOOLTIP)
        self.word_ctrl.SetHint(GUIText.FILTER_CREATE_RULE_ANY)
        word_sizer = wx.BoxSizer(wx.HORIZONTAL)
        word_sizer.Add(word_label, 0, wx.ALIGN_CENTER_VERTICAL)
        word_sizer.Add(self.word_ctrl)
        sizer.Add(word_sizer, 0, wx.ALL, 5)

        pos_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_POS+" ")
        self.pos_ctrl = wx.TextCtrl(self)
        self.pos_ctrl.SetToolTip(GUIText.FILTERS_CREATE_RULE_POS_TOOLTIP)
        self.pos_ctrl.SetHint(GUIText.FILTER_CREATE_RULE_ANY)
        pos_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pos_sizer.Add(pos_label, 0, wx.ALIGN_CENTER_VERTICAL)
        pos_sizer.Add(self.pos_ctrl)
        sizer.Add(pos_sizer, 0, wx.ALL, 5)

        rule_label = wx.StaticText(self, label=GUIText.FILTERS_CREATE_RULE_ACTION+" ")
        self.action1_ctrl = wx.Choice(self, choices=action_options1)
        self.action2_ctrl = wx.Choice(self, choices=action_options2)
        self.rank_ctrl = wx.SpinCtrlDouble(self, min=0, max=100, inc=0.01)
        self.rank_ctrl.SetToolTip(GUIText.FILTERS_CREATE_TFIDF_RULE_NUMBER_TOOLTIP)
        rule_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rule_sizer.Add(rule_label, 0, wx.ALIGN_CENTER_VERTICAL)
        rule_sizer.Add(self.action1_ctrl)
        rule_sizer.Add(self.action2_ctrl)
        rule_sizer.Add(self.rank_ctrl)
        sizer.Add(rule_sizer, 0, wx.ALL, 5)

        controls_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        ok_button = wx.FindWindowById(wx.ID_OK, self)
        ok_button.SetLabel(GUIText.FILTERS_CREATE_TFIDF_RULE)
        ok_button.Bind(wx.EVT_BUTTON, self.OnOK)
        sizer.Add(controls_sizer, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

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
        if self.field not in self.field_options:
            wx.MessageBox(GUIText.FILTERS_CREATE_RULE_FIELD_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('invalid field selected['+self.field+"]")
            status_flag = False
        elif self.field == GUIText.FILTER_CREATE_RULE_ANY:
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
