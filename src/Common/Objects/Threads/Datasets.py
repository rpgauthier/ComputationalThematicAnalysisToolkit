import logging
from threading import Thread

import wx

from Common.GUIText import Filtering as GUITextFiltering
import Common.Objects.Utilities.Datasets as DatasetsUtilities
import Common.CustomEvents as CustomEvents
import Common.Database as Database

class TokenizerThread(Thread):
    """Tokenize Datasets Thread Class."""
    def __init__(self, notify_window, main_frame, dataset, rerun=False, tfidf_update=False):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.main_frame = main_frame
        self.dataset = dataset
        self.rerun = rerun
        self.tfidf_update = tfidf_update
        self.start()
    
    def run(self):
        logger = logging.getLogger(__name__+"TokenizerThread["+str(self.dataset.key)+"].run")
        logger.info("Starting")
        DatasetsUtilities.TokenizeDataset(self.dataset, self._notify_window, self.main_frame, rerun=self.rerun, tfidf_update=self.tfidf_update)
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

        wx.PostEvent(self.main_frame, CustomEvents.ProgressEvent({'step':GUITextFiltering.FILTERS_APPLYING_RULES_STEP}))
        db_conn.ApplyAllDatasetRules(self.dataset.key, self.dataset.filter_rules)
        db_conn.RefreshStringTokensIncluded(self.dataset.key)
        db_conn.RefreshStringTokensRemoved(self.dataset.key)

        wx.PostEvent(self.main_frame, CustomEvents.ProgressEvent({'step':GUITextFiltering.FILTERS_UPDATING_COUNTS_STEP}))
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

class ApplyFilterAllRulesThread(Thread):
    def __init__(self, notify_window, main_frame, dataset):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.dataset = dataset
        self.main_frame = main_frame
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+"ApplyFilterAllRulesThread["+str(self.dataset.key)+"].run")
        logger.info("Starting")
        DatasetsUtilities.ApplyFilterAllRules(self.dataset, self.main_frame)
        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))
        logger.info("Finished")

class ApplyFilterNewRulesThread(Thread):
    def __init__(self, notify_window, main_frame, dataset, new_rules):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.dataset = dataset
        self.main_frame = main_frame
        self.new_rules = new_rules
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+"ApplyFilterNewRulesThread["+str(self.dataset.key)+"].run")
        logger.info("Starting")
        DatasetsUtilities.ApplyFilterNewRules(self.dataset, self.main_frame, self.new_rules)
        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))
        logger.info("Finished")
