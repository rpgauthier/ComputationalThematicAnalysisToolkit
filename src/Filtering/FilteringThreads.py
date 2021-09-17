from threading import Thread
import pandas as pd
import math

import wx

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
import Common.Database as Database

class ApplyFilterRulesThread(Thread):
    def __init__(self, notify_window, dataset, current_workspace_path):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.dataset = dataset
        self.current_workspace_path = current_workspace_path
        self.start()

    def run(self):
        db_conn = Database.DatabaseConnection(self.current_workspace_path)
        db_conn.ApplyDatasetRules(self.dataset.key, self.dataset.filter_rules)
        included_counts = db_conn.GetIncludedStringTokensCounts(self.dataset.key)
        self.dataset.total_docs_remaining = included_counts['documents']
        self.dataset.total_tokens_remaining = included_counts['tokens']
        self.dataset.total_uniquetokens_remaining = included_counts['unique_tokens']

        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))

class ApplyFilterLatestRuleThread(Thread):
    def __init__(self, notify_window, dataset, current_workspace_path):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.dataset = dataset
        self.current_workspace_path = current_workspace_path
        self.start()

    def run(self):
        if len(self.dataset.filter_rules) > 0:
            db_conn = Database.DatabaseConnection(self.current_workspace_path)
            db_conn.ApplyDatasetRule(self.dataset.key, self.dataset.filter_rules[-1])
        included_counts = db_conn.GetIncludedStringTokensCounts(self.dataset.key)
        self.dataset.total_docs_remaining = included_counts['documents']
        self.dataset.total_tokens_remaining = included_counts['tokens']
        self.dataset.total_uniquetokens_remaining = included_counts['unique_tokens']

        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))
