from threading import Thread
import pandas as pd
import math

import wx

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents

class CreateWordDataFrameThread(Thread):
    def __init__(self, notify_window, dataset):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.dataset = dataset
        self.start()
    
    def run(self):

        fulltokens_list = []
        word_idx = self.dataset.tokenization_choice
        
        for key in self.dataset.chosen_fields:
            #TODO currently only supporting tokenization of Strings need to extend to other fieldtypes
            if self.dataset.chosen_fields[key].fieldtype == "string":
                L = [(key, k, *t) for k, v in self.dataset.chosen_fields[key].tokenset.items() for t in v]
                fulltokens_list.extend(L)

        #convert to dataframe
        df = pd.DataFrame(fulltokens_list, columns=['field_key', 'key', 'order',
                          Constants.TOKEN_TEXT_IDX,
                          Constants.TOKEN_NLTK_PORTERSTEM_IDX,
                          Constants.TOKEN_SPACY_LEMMA_IDX,
                          Constants.TOKEN_POS_IDX,
                          Constants.TOKEN_SPACY_STOPWORD_IDX,
                          Constants.TOKEN_TEXT_TFIDF_IDX,
                          Constants.TOKEN_STEM_TFIDF_IDX,
                          Constants.TOKEN_LEMMA_TFIDF_IDX])

        self.dataset.total_docs = pd.to_numeric(df['key'].nunique(), downcast='float')
        self.dataset.total_tokens = df[word_idx].count()
        self.dataset.total_uniquetokens = df[word_idx].nunique()

        if word_idx == Constants.TOKEN_TEXT_IDX:
            words_df = df.groupby([word_idx,
                                   Constants.TOKEN_POS_IDX,
                                   Constants.TOKEN_SPACY_STOPWORD_IDX]).agg(field_key=('field_key', lambda x: list(x)),
                                                                            key=('key', lambda x: list(x)),
                                                                            order=('order', lambda x: list(x)),
                                                                            num_of_words=(word_idx, 'count'),
                                                                            num_of_docs=('key', 'nunique'),
                                                                            tfidf=(Constants.TOKEN_TEXT_TFIDF_IDX, lambda x: list(x)))
        elif word_idx == Constants.TOKEN_NLTK_PORTERSTEM_IDX:
            words_df = df.groupby([word_idx,
                                   Constants.TOKEN_POS_IDX,
                                   Constants.TOKEN_SPACY_STOPWORD_IDX]).agg(field_key=('field_key', lambda x: list(x)),
                                                                            key=('key', lambda x: list(x)),
                                                                            order=('order', lambda x: list(x)),
                                                                            num_of_words=(word_idx, 'count'),
                                                                            num_of_docs=('key', 'nunique'),
                                                                            tfidf=(Constants.TOKEN_STEM_TFIDF_IDX, lambda x: list(x)))
        elif word_idx == Constants.TOKEN_SPACY_LEMMA_IDX:
            words_df = df.groupby([word_idx,
                                   Constants.TOKEN_POS_IDX,
                                   Constants.TOKEN_SPACY_STOPWORD_IDX]).agg(field_key=('field_key', lambda x: list(x)),
                                                                            key=('key', lambda x: list(x)),
                                                                            order=('order', lambda x: list(x)),
                                                                            num_of_words=(word_idx, 'count'),
                                                                            num_of_docs=('key', 'nunique'),
                                                                            tfidf=(Constants.TOKEN_LEMMA_TFIDF_IDX, lambda x: list(x)))
        words_df = words_df.reset_index()
        if self.dataset.total_tokens > 0:
            words_df[Constants.TOKEN_ENTRIES] = words_df[[word_idx, Constants.TOKEN_POS_IDX]].to_records(index=False)
            words_df[Constants.TOKEN_PER_WORDS] = words_df[Constants.TOKEN_NUM_WORDS].div(float(self.dataset.total_tokens)).mul(100.00).round(2)
            words_df[Constants.TOKEN_PER_DOCS] = words_df[Constants.TOKEN_NUM_DOCS].div(float(self.dataset.total_docs)).mul(100.00).round(2)
        else:
            words_df[[word_idx, Constants.TOKEN_POS_IDX, Constants.TOKEN_SPACY_STOPWORD_IDX]] = ""
            words_df[Constants.TOKEN_ENTRIES] = ""
            words_df[Constants.TOKEN_PER_WORDS] = 0
            words_df[Constants.TOKEN_PER_DOCS] = 0

        self.dataset.words_df = words_df
        #return event from thread
        result = {}
        #result['words_df'] = words_df
        wx.PostEvent(self._notify_window, CustomEvents.CreateWordDataFrameResultEvent(result))

class ApplyFilterRulesThread(Thread):
    def __init__(self, notify_window, dataset):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.dataset = dataset
        self.start()

    def run(self):
        word_idx = self.dataset.tokenization_choice

        self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = False
        if self.dataset.total_tokens == 0:
            self.dataset.total_docs_remaining = 0
            self.dataset.total_tokens_remaining = 0
            self.dataset.total_uniquetokens_remaing = 0
        else:
            #TODO field based filtering
            for field, word, pos, action in self.dataset.filter_rules:
                if action == Constants.FILTER_RULE_REMOVE:
                    if pos == Constants.FILTER_RULE_ANY:
                        self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | self.dataset.words_df[word_idx].isin([word])
                    elif word == Constants.FILTER_RULE_ANY:
                        self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | self.dataset.words_df[Constants.TOKEN_POS_IDX].isin([pos])
                    else:
                        self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | self.dataset.words_df[Constants.TOKEN_ENTRIES].isin([(word, pos)])
                elif action == Constants.FILTER_RULE_INCLUDE:
                    if pos == Constants.FILTER_RULE_ANY:
                        self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~self.dataset.words_df[word_idx].isin([word])
                    elif word == Constants.FILTER_RULE_ANY:
                        self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~self.dataset.words_df[Constants.TOKEN_POS_IDX].isin([pos])
                    else:
                        self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~self.dataset.words_df[Constants.TOKEN_ENTRIES].isin([(word, pos)])
                elif action == Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS:
                    self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | self.dataset.words_df[Constants.TOKEN_SPACY_STOPWORD_IDX]
                else:
                    if isinstance(action, tuple):
                        if pos == Constants.FILTER_RULE_ANY and word == Constants.FILTER_RULE_ANY:
                            selector_df = True
                        elif word == Constants.FILTER_RULE_ANY:
                            selector_df = self.dataset.words_df[Constants.TOKEN_POS_IDX].isin([pos])
                        elif pos == Constants.FILTER_RULE_ANY:
                            selector_df = self.dataset.words_df[word_idx].isin([word])
                        else:
                            selector_df = self.dataset.words_df[Constants.TOKEN_ENTRIES].isin([(word, pos)])
                        if action[0] == Constants.FILTER_RULE_REMOVE:
                            if action[2] == ">":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | (self.dataset.words_df[action[1]].gt(action[3]) & selector_df)
                            elif action[2] == ">=":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | (self.dataset.words_df[action[1]].ge(action[3]) & selector_df)
                            elif action[2] == "=":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | (self.dataset.words_df[action[1]].eq(action[3]) & selector_df)
                            elif action[2] == "<=":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | (self.dataset.words_df[action[1]].le(action[3]) & selector_df)
                            elif action[2] == "<":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | (self.dataset.words_df[action[1]].lt(action[3]) & selector_df)
                        elif action[0] == Constants.FILTER_RULE_INCLUDE:
                            if action[2] == ">":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.dataset.words_df[action[1]].gt(action[3]) & selector_df)
                            elif action[2] == ">=":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.dataset.words_df[action[1]].ge(action[3]) & selector_df)
                            elif action[2] == "=":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.dataset.words_df[action[1]].eq(action[3]) & selector_df)
                            elif action[2] == "<=":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.dataset.words_df[action[1]].le(action[3]) & selector_df)
                            elif action[2] == "<":
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.dataset.words_df[action[1]].lt(action[3]) & selector_df)
                        elif action[0] == Constants.FILTER_TFIDF_REMOVE:
                            all_columns = set(self.dataset.words_df.columns)
                            list_columns = {'field_key', 'key', 'order', 'tfidf'}
                            nonlist_columns = list(all_columns - list_columns)
                            self.dataset.words_df = self.dataset.words_df.set_index(nonlist_columns).apply(pd.Series.explode).reset_index()
                            if action[1] == Constants.FILTER_TFIDF_LOWER:
                                self.dataset.words_df.sort_values(by=['tfidf'], inplace=True, ascending=True)
                            elif action[1] == Constants.FILTER_TFIDF_UPPER:
                                self.dataset.words_df.sort_values(by=['tfidf'], inplace=True, ascending=False)
                            cutoff_pos = len(self.dataset.words_df.index)*action[2]
                            if cutoff_pos.is_integer():
                                tfidf_cutoff = self.dataset.words_df.iloc[int(cutoff_pos)]['tfidf']
                            else:
                                lower_cutoff_pos = math.floor(cutoff_pos)
                                lower_cutoff = self.dataset.words_df.iloc[int(lower_cutoff_pos)]['tfidf']
                                upper_cutoff_pos = math.ceil(cutoff_pos)
                                upper_cutoff = self.dataset.words_df.iloc[int(upper_cutoff_pos)]['tfidf']
                                upper_ratio = cutoff_pos-lower_cutoff_pos
                                lower_ratio = 1-upper_ratio
                                tfidf_cutoff = lower_cutoff*lower_ratio+upper_cutoff*upper_ratio
                            if action[1] == Constants.FILTER_TFIDF_LOWER:
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | (self.dataset.words_df['tfidf'].lt(tfidf_cutoff) & selector_df)
                            elif action[1] == Constants.FILTER_TFIDF_UPPER:
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] | (self.dataset.words_df['tfidf'].gt(tfidf_cutoff) & selector_df)
                            total_words = self.dataset.words_df[word_idx].count()
                            total_doc = pd.to_numeric(self.dataset.words_df['key'].nunique(), downcast='float')
                            self.dataset.words_df = self.dataset.words_df.groupby([word_idx,
                                                                                Constants.TOKEN_POS_IDX,
                                                                                Constants.TOKEN_SPACY_STOPWORD_IDX,
                                                                                Constants.TOKEN_REMOVE_FLG]).agg(field_key=('field_key', lambda x: list(x)),
                                                                                                                    key=('key', lambda x: list(x)),
                                                                                                                    order=('order', lambda x: list(x)),
                                                                                                                    num_of_words=('tfidf', 'count'),
                                                                                                                    num_of_docs=('key', 'nunique'),
                                                                                                                    tfidf=('tfidf', lambda x: list(x)))
                            self.dataset.words_df = self.dataset.words_df.reset_index()
                            self.dataset.words_df[Constants.TOKEN_ENTRIES] = self.dataset.words_df[[word_idx, Constants.TOKEN_POS_IDX]].to_records(index=False)
                            self.dataset.words_df[Constants.TOKEN_PER_WORDS] = self.dataset.words_df[Constants.TOKEN_NUM_WORDS].div(float(total_words)).mul(100.00).round(2)
                            self.dataset.words_df[Constants.TOKEN_PER_DOCS] = self.dataset.words_df[Constants.TOKEN_NUM_DOCS].div(float(total_doc)).mul(100.00).round(2)
                        elif action[0] == Constants.FILTER_TFIDF_INCLUDE:
                            all_columns = set(self.dataset.words_df.columns)
                            list_columns = {'field_key', 'key', 'order', 'tfidf'}
                            nonlist_columns = list(all_columns - list_columns)
                            self.dataset.words_df = self.dataset.words_df.set_index(nonlist_columns).apply(pd.Series.explode).reset_index()
                            if action[1] == Constants.FILTER_TFIDF_LOWER:
                                self.dataset.words_df.sort_values(by=['tfidf'], inplace=True, ascending=True)
                            elif action[1] == Constants.FILTER_TFIDF_UPPER:
                                self.dataset.words_df.sort_values(by=['tfidf'], inplace=True, ascending=False)
                            cutoff_pos = len(self.dataset.words_df.index)*action[2]
                            if cutoff_pos.is_integer():
                                tfidf_cutoff = self.dataset.words_df.iloc[int(cutoff_pos)]['tfidf']
                            else:
                                lower_cutoff_pos = math.floor(cutoff_pos)
                                lower_cutoff = self.dataset.words_df.iloc[int(lower_cutoff_pos)]['tfidf']
                                upper_cutoff_pos = math.ceil(cutoff_pos)
                                upper_cutoff = self.dataset.words_df.iloc[int(upper_cutoff_pos)]['tfidf']
                                upper_ratio = cutoff_pos-lower_cutoff_pos
                                lower_ratio = 1-upper_ratio
                                tfidf_cutoff = lower_cutoff*lower_ratio+upper_cutoff*upper_ratio
                            if action[1] == Constants.FILTER_TFIDF_LOWER:
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.dataset.words_df['tfidf'].lt(tfidf_cutoff) & selector_df)
                            elif action[1] == Constants.FILTER_TFIDF_UPPER:
                                self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] = self.dataset.words_df[Constants.TOKEN_REMOVE_FLG] & ~(self.dataset.words_df['tfidf'].gt(tfidf_cutoff) & selector_df)
                            total_words = self.dataset.words_df[word_idx].count()
                            total_doc = pd.to_numeric(self.dataset.words_df['key'].nunique(), downcast='float')
                            self.dataset.words_df = self.dataset.words_df.groupby([word_idx,
                                                                                Constants.TOKEN_POS_IDX,
                                                                                Constants.TOKEN_SPACY_STOPWORD_IDX,
                                                                                Constants.TOKEN_REMOVE_FLG]).agg(field_key=('field_key', lambda x: list(x)),
                                                                                                                    key=('key', lambda x: list(x)),
                                                                                                                    order=('order', lambda x: list(x)),
                                                                                                                    num_of_words=('tfidf', 'count'),
                                                                                                                    num_of_docs=('key', 'nunique'),
                                                                                                                    tfidf=('tfidf', lambda x: list(x)))
                            self.dataset.words_df = self.dataset.words_df.reset_index()
                            self.dataset.words_df[Constants.TOKEN_ENTRIES] = self.dataset.words_df[[word_idx, Constants.TOKEN_POS_IDX]].to_records(index=False)
                            self.dataset.words_df[Constants.TOKEN_PER_WORDS] = self.dataset.words_df[Constants.TOKEN_NUM_WORDS].div(float(total_words)).mul(100.00).round(2)
                            self.dataset.words_df[Constants.TOKEN_PER_DOCS] = self.dataset.words_df[Constants.TOKEN_NUM_DOCS].div(float(total_doc)).mul(100.00).round(2)

            included_words_df = self.dataset.words_df.loc[~self.dataset.words_df[Constants.TOKEN_REMOVE_FLG]]
            #removed_words_df = self.dataset.words_df.loc[self.dataset.words_df[Constants.TOKEN_REMOVE_FLG]]
            documents_series_remaining = included_words_df['key'].explode()
            self.dataset.total_docs_remaining = documents_series_remaining.nunique()
            self.dataset.total_tokens_remaining = included_words_df[Constants.TOKEN_NUM_WORDS].sum()
            self.dataset.total_uniquetokens_remaing = included_words_df[word_idx].nunique()


        #return event from thread
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.ApplyFilterRulesResultEvent(result))
