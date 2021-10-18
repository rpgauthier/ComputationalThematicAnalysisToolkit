import logging
from threading import Thread

import wx

from Common.GUIText import Filtering as GUITextFiltering
import Common.Objects.Utilities.Datasets as DatasetsUtilities
import Common.CustomEvents as CustomEvents
import Common.Database as Database

class TokenizerThread(Thread):
    """Tokenize Datasets Thread Class."""
    def __init__(self, notify_window, main_frame, dataset, rerun=False):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.main_frame = main_frame
        self.dataset = dataset
        self.rerun = rerun
        self.start()
    
    def run(self):
        logger = logging.getLogger(__name__+"TokenizerThread["+str(self.dataset.key)+"].run")
        logger.info("Starting")
        DatasetsUtilities.TokenizeDataset(self.dataset, self._notify_window, self.main_frame, rerun=self.rerun)
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.TokenizerResultEvent(result))
        logger.info("Finished")

class ChangeTokenizationChoiceThread(Thread):
    def __init__(self, notify_window, main_frame, dataset, new_choice):
        Thread.__init__(self)
        self._notify_window = notify_window
        self.dataset = dataset
        self.new_choice = new_choice
        self.main_frame = main_frame
        self.start()
    
    def run(self):
        logger = logging.getLogger(__name__+"ChangeTokenizationChoiceThread["+str(self.dataset.key)+"].run")
        logger.info("Starting")
        db_conn = Database.DatabaseConnection(self.main_frame.current_workspace.name)
        db_conn.UpdateDatasetTokenType(self.dataset.key, self.new_choice)

        wx.PostEvent(self.main_frame, CustomEvents.ProgressEvent(GUITextFiltering.FILTERS_APPLYING_RULES_BUSY_MSG))
        db_conn.ApplyDatasetRules(self.dataset.key, self.dataset.filter_rules)

        db_conn.RefreshStringTokensIncluded(self.dataset.key)
        db_conn.RefreshStringTokensRemoved(self.dataset.key)
        
        
        wx.PostEvent(self.main_frame, CustomEvents.ProgressEvent(GUITextFiltering.FILTERS_UPDATING_COUNTS))
        db_conn.ApplyDatasetRules(self.dataset.key, self.dataset.filter_rules)
        counts = db_conn.GetStringTokensCounts(self.dataset.key)
        self.dataset.total_docs = counts['documents']
        self.dataset.total_tokens = counts['tokens']
        self.dataset.total_uniquetokens = counts['unique_tokens']
        included_counts = db_conn.GetIncludedStringTokensCounts(self.dataset.key)
        self.dataset.total_docs_remaining = included_counts['documents']
        self.dataset.total_tokens_remaining = included_counts['tokens']
        self.dataset.total_uniquetokens_remaining = included_counts['unique_tokens']

        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ChangeTokenizationResultEvent(result))
        logger.info("Finished")

class ApplyFilterRulesThread(Thread):
    def __init__(self, notify_window, main_frame, dataset):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.dataset = dataset
        self.main_frame = main_frame
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+"ApplyFilterRulesThread["+str(self.dataset.key)+"].run")
        logger.info("Starting")
        DatasetsUtilities.ApplyFilterRules(self.dataset, self.main_frame)
        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))
        logger.info("Finished")

class ApplyFilterLatestRuleThread(Thread):
    def __init__(self, notify_window, main_frame, dataset):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.dataset = dataset
        self.main_frame = main_frame
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+"ApplyFilterLatestRuleThread["+str(self.dataset.key)+"].run")
        logger.info("Starting")
        DatasetsUtilities.ApplyFilterLatestRule(self.dataset, self.main_frame)
        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))
        logger.info("Finished")
