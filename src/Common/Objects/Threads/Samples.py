import logging
from threading import Thread
import os
import psutil
import bz2
import pickle

import pandas as pd
import wx
import numpy as np

#ML libraries
import gensim
import bitermplus as btm

import Common.CustomEvents as CustomEvents

class LDATrainingThread(Thread):
    """LDATrainingThread Class."""
    def __init__(self, notify_window, key, tokensets, num_topics, num_passes, alpha, eta, workspace_path, filedir):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.key = key
        self.tokensets = tokensets
        self.num_topics = num_topics
        self.num_passes = num_passes
        self.alpha = alpha
        self.eta = eta
        self.workspace_path = workspace_path
        self.filedir = filedir
        self.start()

    #training code to be run asyncronously
    def run(self):
        '''Generates an LDA model'''
        logger = logging.getLogger(__name__+"LDATrainingThread["+str(self.key)+"].run")
        logger.info("Starting")
        logger.info("Starting generation of model")
        tokensets_keys = list(self.tokensets.keys())
        tokensets_values = list(self.tokensets.values())
        dictionary = gensim.corpora.Dictionary(tokensets_values)
        dictionary.compactify()
        if not os.path.exists(self.workspace_path+"/LDA"):
            os.makedirs(self.workspace_path+"/LDA")
        path = self.workspace_path+self.filedir
        if not os.path.exists(path):
            os.makedirs(path)
        dictionary.save(path+'/ldadictionary.dict')
        logger.info("Dictionary created")
        raw_corpus = [dictionary.doc2bow(tokenset) for tokenset in tokensets_values]
        gensim.corpora.MmCorpus.serialize(path+'/ldacorpus.mm', raw_corpus)
        corpus = gensim.corpora.MmCorpus(path+'/ldacorpus.mm')
        logger.info("Corpus created")

        if self.alpha is not None:
            alpha = self.alpha
        else:
            alpha = 'symmetric'
        if self.eta is not None:
            eta = self.eta
        else:
            eta = 'auto'
        
        cpus = psutil.cpu_count(logical=False)
        if cpus is None or cpus < 2:
            workers = 1
        else:
            workers = cpus-1

        model = gensim.models.ldamulticore.LdaMulticore(workers=workers,
                                                        corpus=corpus,
                                                        id2word=dictionary,
                                                        num_topics=self.num_topics,
                                                        passes=self.num_passes,
                                                        alpha=alpha,
                                                        eta=eta)
        model.save(path+'/ldamodel.lda', 'wb')
        logger.info("Completed generation of model")
        # Init output
        # capture all document topic probabilities both by document and by topic
        document_topic_prob = {}
        topic_document_prob_df = pd.DataFrame()
        model_document_topics = model.get_document_topics(corpus, minimum_probability=0.0, minimum_phi_value=0)
        for doc_num in range(len(corpus)):
            doc_row = model_document_topics[doc_num]
            doc_topic_prob_row = {}
            for i, prob in doc_row:
                doc_topic_prob_row[i+1] = prob
                topic_document_prob_df = topic_document_prob_df.append(pd.Series([tokensets_keys[doc_num],
                                                                                int(i+1),
                                                                                round(prob, 4)]),
                                                                    ignore_index=True)
            document_topic_prob[tokensets_keys[doc_num]] = doc_topic_prob_row
        topic_document_prob_df.columns = ['tokenset_key', 'topic_id', 'prob']
        topic_document_prob = {}
        for i in range(self.num_topics):
            tmp_df = topic_document_prob_df.loc[topic_document_prob_df['topic_id'] == i+1].sort_values(by='prob', ascending=False)[['tokenset_key', 'prob']]
            topic_document_prob[i+1] = list(tmp_df.to_records(index=False))  

        logger.info("Finished")
        result={'key': self.key, 'topic_document_prob':topic_document_prob, 'document_topic_prob':document_topic_prob}
        wx.PostEvent(self._notify_window, CustomEvents.ModelCreatedResultEvent(result))

class BitermTrainingThread(Thread):
    """BitermTrainingThread Class."""
    def __init__(self, notify_window, key, tokensets, num_topics, num_iterations, workspace_path, filedir):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.key = key
        self.tokensets = tokensets
        self.num_topics = num_topics
        self.num_iterations = num_iterations
        self.workspace_path = workspace_path
        self.filedir = filedir
        self.start()

    def run(self):
        '''Generates an Biterm model'''
        logger = logging.getLogger(__name__+"BitermTrainingThread["+str(self.key)+"].run")
        logger.info("Starting")
        
        if not os.path.exists(self.workspace_path+"/Biterm"):
            os.makedirs(self.workspace_path+"/Biterm")
        path = self.workspace_path+self.filedir
        if not os.path.exists(path):
            os.makedirs(path)

        text_keys = []
        texts = []
        for key in self.tokensets:
            text_keys.append(key)
            text = ' '.join(self.tokensets[key])
            texts.append(text)

        logger.info("Starting generation of biterm model")
        X, vocab, vocab_dict = btm.get_words_freqs(texts)
        
        with bz2.BZ2File(path+'/vocab.pk', 'wb') as outfile:
            pickle.dump(vocab, outfile)
        logger.info("Vocab created")

        tf = np.array(X.sum(axis=0)).ravel()
        # Vectorizing documents
        docs_vec = btm.get_vectorized_docs(texts, vocab)
        docs_lens = list(map(len, docs_vec))
        with bz2.BZ2File(path+'/transformed_texts.pk', 'wb') as outfile:
            pickle.dump(docs_vec, outfile)
        logger.info("Texts transformed")

        logger.info("Starting Generation of BTM")
        biterms = btm.get_biterms(docs_vec)

        model = btm.BTM(X, vocab, T=self.num_topics, W=vocab.size, M=20, alpha=50/8, beta=0.01)
        topics = model.fit_transform(docs_vec, biterms, iterations=self.num_iterations, verbose=False)
        with bz2.BZ2File(path+'/btm.pk', 'wb') as outfile:
            pickle.dump(model, outfile)
        logger.info("Completed Generation of BTM")

        document_topic_prob = {}
        topic_document_prob_df = pd.DataFrame()
        for doc_num in range(len(topics)):
            doc_row = topics[doc_num]
            doc_topic_prob_row = {}
            for topic_num in range(len(doc_row)):
                doc_topic_prob_row[topic_num+1] = doc_row[topic_num]
                topic_document_prob_df = topic_document_prob_df.append(pd.Series([text_keys[doc_num],
                                                                                int(topic_num+1),
                                                                                round(doc_row[topic_num], 4)]),
                                                                    ignore_index=True)
            document_topic_prob[text_keys[doc_num]] = doc_topic_prob_row
        topic_document_prob_df.columns = ['tokenset_key', 'topic_id', 'prob']
        topic_document_prob = {}
        for i in range(self.num_topics):
            tmp_df = topic_document_prob_df.loc[topic_document_prob_df['topic_id'] == i+1].sort_values(by='prob', ascending=False)[['tokenset_key', 'prob']]
            topic_document_prob[i+1] = list(tmp_df.to_records(index=False))

        logger.info("Finished")
        result={'key': self.key, 'topic_document_prob':topic_document_prob, 'document_topic_prob':document_topic_prob}
        wx.PostEvent(self._notify_window, CustomEvents.ModelCreatedResultEvent(result))
