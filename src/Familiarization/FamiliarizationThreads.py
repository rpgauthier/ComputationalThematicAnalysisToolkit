from threading import Thread
import pandas as pd
import math

import wx

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents

class CreateWordDataFrameThread(Thread):
    def __init__(self, notify_window, tokenset, word_idx):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.tokenset = tokenset
        self.word_idx = word_idx
        self.start()
    
    def run(self):
        #identify entries based on tokenization modes and calculate associated counts
        L = [(k, *t) for k, v in self.tokenset.items() for t in v]
        df = pd.DataFrame(L, columns=['key', 'order',
                          Constants.TOKEN_TEXT_IDX,
                          Constants.TOKEN_NLTK_PORTERSTEM_IDX,
                          Constants.TOKEN_SPACY_LEMMA_IDX,
                          Constants.TOKEN_POS_IDX,
                          Constants.TOKEN_SPACY_STOPWORD_IDX,
                          Constants.TOKEN_TEXT_TFIDF_IDX,
                          Constants.TOKEN_STEM_TFIDF_IDX,
                          Constants.TOKEN_LEMMA_TFIDF_IDX])

        total_words = df[self.word_idx].count()
        total_doc = pd.to_numeric(df['key'].nunique(), downcast='float')

        if self.word_idx == Constants.TOKEN_TEXT_IDX:
            words_df = df.groupby([self.word_idx,
                                Constants.TOKEN_POS_IDX,
                                Constants.TOKEN_SPACY_STOPWORD_IDX]).agg(key=('key', lambda x: list(x)),
                                                                         order=('order', lambda x: list(x)),
                                                                         num_of_words=(self.word_idx, 'count'),
                                                                         num_of_docs=('key', 'nunique'),
                                                                         tfidf=(Constants.TOKEN_TEXT_TFIDF_IDX, lambda x: list(x)))
        elif self.word_idx == Constants.TOKEN_NLTK_PORTERSTEM_IDX:
            words_df = df.groupby([self.word_idx,
                                Constants.TOKEN_POS_IDX,
                                Constants.TOKEN_SPACY_STOPWORD_IDX]).agg(key=('key', lambda x: list(x)),
                                                                         order=('order', lambda x: list(x)),
                                                                         num_of_words=(self.word_idx, 'count'),
                                                                         num_of_docs=('key', 'nunique'),
                                                                         tfidf=(Constants.TOKEN_STEM_TFIDF_IDX, lambda x: list(x)))
        elif self.word_idx == Constants.TOKEN_SPACY_LEMMA_IDX:
            words_df = df.groupby([self.word_idx,
                                Constants.TOKEN_POS_IDX,
                                Constants.TOKEN_SPACY_STOPWORD_IDX]).agg(key=('key', lambda x: list(x)),
                                                                         order=('order', lambda x: list(x)),
                                                                         num_of_words=(self.word_idx, 'count'),
                                                                         num_of_docs=('key', 'nunique'),
                                                                         tfidf=(Constants.TOKEN_LEMMA_TFIDF_IDX, lambda x: list(x)))
        words_df = words_df.reset_index()
        words_df[Constants.TOKEN_ENTRIES] = words_df[[self.word_idx, Constants.TOKEN_POS_IDX]].to_records(index=False)
        words_df[Constants.TOKEN_PER_WORDS] = words_df[Constants.TOKEN_NUM_WORDS].div(float(total_words)).mul(100.00).round(2)
        words_df[Constants.TOKEN_PER_DOCS] = words_df[Constants.TOKEN_NUM_DOCS].div(float(total_doc)).mul(100.00).round(2)

        #return event from thread
        result = {}
        result['words_df'] = words_df
        wx.PostEvent(self._notify_window, CustomEvents.CreateWordDataFrameResultEvent(result))

class ApplyFilterRulesThread(Thread):
    def __init__(self, notify_window, word_idx, words_df, filter_rules):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.word_idx = word_idx
        self.words_df = words_df
        self.filter_rules = filter_rules
        self.start()

    def run(self):
        self.words_df[Constants.TOKEN_REMOVE_FLG] = False
        for word, pos, action in self.filter_rules:
            if action == Constants.FILTER_RULE_REMOVE:
                if pos == Constants.FILTER_RULE_ANY:
                    self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | self.words_df[self.word_idx].isin([word])
                elif word == Constants.FILTER_RULE_ANY:
                    self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | self.words_df[Constants.TOKEN_POS_IDX].isin([pos])
                else:
                    self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | self.words_df[Constants.TOKEN_ENTRIES].isin([(word, pos)])
            elif action == Constants.FILTER_RULE_INCLUDE:
                if pos == Constants.FILTER_RULE_ANY:
                    self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~self.words_df[self.word_idx].isin([word])
                elif word == Constants.FILTER_RULE_ANY:
                    self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~self.words_df[Constants.TOKEN_POS_IDX].isin([pos])
                else:
                    self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~self.words_df[Constants.TOKEN_ENTRIES].isin([(word, pos)])
            elif action == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | self.words_df[Constants.TOKEN_SPACY_STOPWORD_IDX]
            else:
                if isinstance(action, tuple):
                    if pos == Constants.FILTER_RULE_ANY and word == Constants.FILTER_RULE_ANY:
                        selector_df = True
                    elif word == Constants.FILTER_RULE_ANY:
                        selector_df = self.words_df[Constants.TOKEN_POS_IDX].isin([pos])
                    elif pos == Constants.FILTER_RULE_ANY:
                        selector_df = self.words_df[self.word_idx].isin([word])
                    else:
                        selector_df = self.words_df[Constants.TOKEN_ENTRIES].isin([(word, pos)])
                    if action[0] == Constants.FILTER_RULE_REMOVE:
                        if action[2] == ">":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | (self.words_df[action[1]].gt(action[3]) & selector_df)
                        elif action[2] == ">=":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | (self.words_df[action[1]].ge(action[3]) & selector_df)
                        elif action[2] == "=":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | (self.words_df[action[1]].eq(action[3]) & selector_df)
                        elif action[2] == "<=":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | (self.words_df[action[1]].le(action[3]) & selector_df)
                        elif action[2] == "<":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | (self.words_df[action[1]].lt(action[3]) & selector_df)
                    elif action[0] == Constants.FILTER_RULE_INCLUDE:
                        if action[2] == ">":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.words_df[action[1]].gt(action[3]) & selector_df)
                        elif action[2] == ">=":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.words_df[action[1]].ge(action[3]) & selector_df)
                        elif action[2] == "=":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.words_df[action[1]].eq(action[3]) & selector_df)
                        elif action[2] == "<=":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.words_df[action[1]].le(action[3]) & selector_df)
                        elif action[2] == "<":
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.words_df[action[1]].lt(action[3]) & selector_df)
                    elif action[0] == Constants.FILTER_TFIDF_REMOVE:
                        all_columns = set(self.words_df.columns)
                        list_columns = {'key', 'order', 'tfidf'}
                        nonlist_columns = list(all_columns - list_columns)
                        self.words_df = self.words_df.set_index(nonlist_columns).apply(pd.Series.explode).reset_index()
                        if action[1] == Constants.FILTER_TFIDF_LOWER:
                            self.words_df.sort_values(by=['tfidf'], inplace=True, ascending=True)
                        elif action[1] == Constants.FILTER_TFIDF_UPPER:
                            self.words_df.sort_values(by=['tfidf'], inplace=True, ascending=False)
                        cutoff_pos = len(self.words_df.index)*action[2]
                        if cutoff_pos.is_integer():
                            tfidf_cutoff = self.words_df.iloc[int(cutoff_pos)]['tfidf']
                        else:
                            lower_cutoff_pos = math.floor(cutoff_pos)
                            lower_cutoff = self.words_df.iloc[int(lower_cutoff_pos)]['tfidf']
                            upper_cutoff_pos = math.ceil(cutoff_pos)
                            upper_cutoff = self.words_df.iloc[int(upper_cutoff_pos)]['tfidf']
                            upper_ratio = cutoff_pos-lower_cutoff_pos
                            lower_ratio = 1-upper_ratio
                            tfidf_cutoff = lower_cutoff*lower_ratio+upper_cutoff*upper_ratio
                        if action[1] == Constants.FILTER_TFIDF_LOWER:
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | (self.words_df['tfidf'].lt(tfidf_cutoff) & selector_df)
                        elif action[1] == Constants.FILTER_TFIDF_UPPER:
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] | (self.words_df['tfidf'].gt(tfidf_cutoff) & selector_df)
                        total_words = self.words_df[self.word_idx].count()
                        total_doc = pd.to_numeric(self.words_df['key'].nunique(), downcast='float')
                        self.words_df = self.words_df.groupby([self.word_idx,
                                                               Constants.TOKEN_POS_IDX,
                                                               Constants.TOKEN_SPACY_STOPWORD_IDX,
                                                               Constants.TOKEN_REMOVE_FLG]).agg(key=('key', lambda x: list(x)),
                                                                                                order=('order', lambda x: list(x)),
                                                                                                num_of_words=('tfidf', 'count'),
                                                                                                num_of_docs=('key', 'nunique'),
                                                                                                tfidf=('tfidf', lambda x: list(x)))
                        self.words_df = self.words_df.reset_index()
                        self.words_df[Constants.TOKEN_ENTRIES] = self.words_df[[self.word_idx, Constants.TOKEN_POS_IDX]].to_records(index=False)
                        self.words_df[Constants.TOKEN_PER_WORDS] = self.words_df[Constants.TOKEN_NUM_WORDS].div(float(total_words)).mul(100.00).round(2)
                        self.words_df[Constants.TOKEN_PER_DOCS] = self.words_df[Constants.TOKEN_NUM_DOCS].div(float(total_doc)).mul(100.00).round(2)
                    elif action[0] == Constants.FILTER_TFIDF_INCLUDE:
                        all_columns = set(self.words_df.columns)
                        list_columns = {'key', 'order', 'tfidf'}
                        nonlist_columns = list(all_columns - list_columns)
                        self.words_df = self.words_df.set_index(nonlist_columns).apply(pd.Series.explode).reset_index()
                        if action[1] == Constants.FILTER_TFIDF_LOWER:
                            self.words_df.sort_values(by=['tfidf'], inplace=True, ascending=True)
                        elif action[1] == Constants.FILTER_TFIDF_UPPER:
                            self.words_df.sort_values(by=['tfidf'], inplace=True, ascending=False)
                        cutoff_pos = len(self.words_df.index)*action[2]
                        if cutoff_pos.is_integer():
                            tfidf_cutoff = self.words_df.iloc[int(cutoff_pos)]['tfidf']
                        else:
                            lower_cutoff_pos = math.floor(cutoff_pos)
                            lower_cutoff = self.words_df.iloc[int(lower_cutoff_pos)]['tfidf']
                            upper_cutoff_pos = math.ceil(cutoff_pos)
                            upper_cutoff = self.words_df.iloc[int(upper_cutoff_pos)]['tfidf']
                            upper_ratio = cutoff_pos-lower_cutoff_pos
                            lower_ratio = 1-upper_ratio
                            tfidf_cutoff = lower_cutoff*lower_ratio+upper_cutoff*upper_ratio
                        if action[1] == Constants.FILTER_TFIDF_LOWER:
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.words_df['tfidf'].lt(tfidf_cutoff) & selector_df)
                        elif action[1] == Constants.FILTER_TFIDF_UPPER:
                            self.words_df[Constants.TOKEN_REMOVE_FLG] = self.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.words_df['tfidf'].gt(tfidf_cutoff) & selector_df)
                        total_words = self.words_df[self.word_idx].count()
                        total_doc = pd.to_numeric(self.words_df['key'].nunique(), downcast='float')
                        self.words_df = self.words_df.groupby([self.word_idx,
                                                               Constants.TOKEN_POS_IDX,
                                                               Constants.TOKEN_SPACY_STOPWORD_IDX,
                                                               Constants.TOKEN_REMOVE_FLG]).agg(key=('key', lambda x: list(x)),
                                                                                                order=('order', lambda x: list(x)),
                                                                                                num_of_words=('tfidf', 'count'),
                                                                                                num_of_docs=('key', 'nunique'),
                                                                                                tfidf=('tfidf', lambda x: list(x)))
                        self.words_df = self.words_df.reset_index()
                        self.words_df[Constants.TOKEN_ENTRIES] = self.words_df[[self.word_idx, Constants.TOKEN_POS_IDX]].to_records(index=False)
                        self.words_df[Constants.TOKEN_PER_WORDS] = self.words_df[Constants.TOKEN_NUM_WORDS].div(float(total_words)).mul(100.00).round(2)
                        self.words_df[Constants.TOKEN_PER_DOCS] = self.words_df[Constants.TOKEN_NUM_DOCS].div(float(total_doc)).mul(100.00).round(2)

        #return event from thread
        result = {}
        result['words_df'] = self.words_df
        result['included_words_df'] = self.words_df.loc[~self.words_df[Constants.TOKEN_REMOVE_FLG]]
        result['removed_words_df'] = self.words_df.loc[self.words_df[Constants.TOKEN_REMOVE_FLG]]
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))
