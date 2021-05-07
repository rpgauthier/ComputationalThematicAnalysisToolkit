import logging
import random
import os
import bz2
from datetime import datetime
from shutil import copytree
from collections import OrderedDict

#LDA libraries
import gensim
#biterm libraries
import numpy as np
import bitermplus as btm
import pandas as pd
import _pickle as cPickle

import Common.Objects.Datasets as Datasets
from Common.Objects.Generic import GenericObject

class Sample(GenericObject):
    '''Instances of Sample objects'''
    def __init__(self, key, dataset_key, sample_type):
        logger = logging.getLogger(__name__+".Sample["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key)

        #properties that automatically update last_changed_dt
        self._dataset_key = dataset_key
        self._sample_type = sample_type
        self._model = None
        self._generated_flag = False
        self._start_dt = None
        self._end_dt = None
        
        #objects that have their own last_changed_dt and thus need to be checked dynamically
        self.parts_dict = OrderedDict()
        
        logger.info("Finished")
    def __repr__(self):
        return 'Sample: %s' % (self.key,)

    @property
    def dataset_key(self):
        return self._dataset_key
    @dataset_key.setter
    def dataset_key(self, value):
        self._dataset_key = value
        self.last_changed_dt = datetime.now()

    @property
    def sample_type(self):
        return self._sample_type
    @sample_type.setter
    def sample_type(self, value):
        self._sample_type = value
        self.last_changed_dt = datetime.now()
    
    @property
    def model(self):
        return self._model
    @model.setter
    def model(self, value):
        self._model = value
        self.last_changed_dt = datetime.now()
    
    @property
    def generated_flag(self):
        return self._generated_flag
    @generated_flag.setter
    def generated_flag(self, value):
        self._generated_flag = value
        self.last_changed_dt = datetime.now()
    
    @property
    def start_dt(self):
        return self._start_dt
    @start_dt.setter
    def start_dt(self, value):
        self._start_dt = value
        self.last_changed_dt = datetime.now()
    
    @property
    def end_dt(self):
        return self._end_dt
    @end_dt.setter
    def end_dt(self, value):
        self._end_dt = value
        self.last_changed_dt = datetime.now()

    @property
    def last_changed_dt(self):
        for part_name in self.parts_dict:
            tmp_last_changed_dt = self.parts_dict[part_name].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value

    def Generate(self):
        logger = logging.getLogger(__name__+".Sample["+str(self.key)+"].Generate")
        logger.info("Starting")
        logger.info("Finished")

    def DestroyObject(self):
        logger = logging.getLogger(__name__+".Sample["+str(self.key)+"].DestroyObject")
        logger.info("Starting")
        #any children models or reviews
        for part_key in list(self.parts_dict.keys()):
            self.parts_dict[part_key].DestroyObject()
        logger.info("Finished")

    def Reload(self):
        logger = logging.getLogger(__name__+".Sample["+str(self.key)+"].Reload")
        logger.info("Starting")
        logger.info("Finished")

    def Load(self, workspace_path):
        logger = logging.getLogger(__name__+".Sample["+str(self.key)+"].Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self, workspace_path):
        logger = logging.getLogger(__name__+".Sample["+str(self.key)+"].Save")
        logger.info("Starting")
        logger.info("Finished")

class RandomSample(Sample):
    def __init__(self, key, dataset_key, model_parameters):
        logger = logging.getLogger(__name__+".RandomSample["+str(key)+"].__init__")
        logger.info("Starting")
        Sample.__init__(self, key, dataset_key, "Random")

        #list that is managed
        #TODO they have not yet been converted into properties due to complexity
        self.metdataset_key_list = list(model_parameters['metadataset'].keys())

        logger.info("Finished")

    def __repr__(self):
        return 'RandomSample: %s' % (self.key,)

    def Generate(self, datasets):
        logger = logging.getLogger(__name__+".RandomSample["+str(self.key)+"].Generate")
        logger.info("Starting")
        self.start_dt = datetime.now()
        if not self.generated_flag:
            random.shuffle(self.metdataset_key_list)
            self.last_changed_dt = datetime.now()
            self.generated_flag = True
            self.parts_dict["Randomly Ordered Documents"] = ModelPart(self, "Randomly Ordered Documents", self.metdataset_key_list, datasets)
        self.end_dt = datetime.now()
        logger.info("Finished")

class TopicSample(Sample):
    def __init__(self, key, dataset_key, sample_type, model_parameters):
        logger = logging.getLogger(__name__+".TopicSample["+str(key)+"].__init__")
        logger.info("Starting")
        Sample.__init__(self, key, dataset_key, sample_type)

        #properties that automatically update last_changed_dt
        self._word_num = 0
        self._document_cutoff = 0.75
        self._document_topic_prob = None
        self._topic_documents_prob = None
        #fixed properties that may be externally accessed but do not change after being initialized
        self._tokensets = model_parameters['tokensets']
        self._num_topics = model_parameters['num_topics']

        #dictionary that is managed with setters

        #objects that have their own last_changed_dt and thus need to be checked dynamically
        
        #variable that should only be used internally and are never accessed from outside
        self._workspace_path = model_parameters['workspace_path']
        self._filedir = "/"+self.sample_type+"/"+key
        self._new_filedir = "/"+self.sample_type+"/"+key

        #setup directories if needed
        if not os.path.exists(self._workspace_path+"/"+self.sample_type):
            os.makedirs(self._workspace_path+"/"+self.sample_type)
        if not os.path.exists(self._workspace_path+"/"+self.sample_type+"/"+self.key):
            os.makedirs(self._workspace_path+"/"+self.sample_type+"/"+self.key)
    
    @property
    def key(self):
        return self._key
    @key.setter
    def key(self, value):
        self._key = value
        self._new_filedir = "/"+self.sample_type+"/"+self._key
        self._last_changed_dt = datetime.now()

    @property
    def word_num(self):
        return self._word_num
    @word_num.setter
    def word_num(self, value):
        for part_key in self.parts_dict:
            self.parts_dict[part_key].word_num = value
        self._word_num = value
        self.last_changed_dt = datetime.now()

    @property
    def document_cutoff(self):
        return self._document_cutoff
    @document_cutoff.setter
    def document_cutoff(self, value):
        self._document_cutoff = value
        self.last_changed_dt = datetime.now()

    @property
    def document_topic_prob(self):
        return self._document_topic_prob
    @document_topic_prob.setter
    def document_topic_prob(self, value):
        self._document_topic_prob = value
        self.last_changed_dt = datetime.now()

    @property
    def topic_documents_prob(self):
        return self._topic_documents_prob
    @topic_documents_prob.setter
    def topic_documents_prob(self, value):
        self._topic_documents_prob = value
        self.last_changed_dt = datetime.now()

    @property
    def num_topics(self):
        return self._num_topics
    
    @property
    def tokensets(self):
        return self._tokensets

    def ApplyDocumentCutoff(self):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].ApplyDocumentCutoff")
        logger.info("Starting")
        document_set = set()

        def UpdateLDATopicPart(topic):
            document_list = []
            for document in self.topic_documents_prob[topic]:
                if document[1] >= self.document_cutoff:
                    document_list.append(document[0])
                    document_set.add(document[0])
            self.parts_dict[topic].part_data = document_list

        for topic in self.parts_dict:
            if isinstance(self.parts_dict[topic], Part) and topic != 'unknown':
                UpdateLDATopicPart(topic)
            elif isinstance(self.parts_dict[topic], MergedPart):
                for subtopic in self.parts_dict[topic].parts_dict:
                    if isinstance(self.parts_dict[topic].parts_dict[subtopic], Part) and topic != 'unknown':
                        UpdateLDATopicPart(topic)
        
        unknown_list = set(self.tokensets.keys()) - document_set
        unknown_df = pd.DataFrame(data=self.document_topic_prob).transpose()
        unknown_df = unknown_df[unknown_df.index.isin(unknown_list)]
        unknown_series = unknown_df.max(axis=1).sort_values()
        new_unknown_list = list(unknown_series.index.values)
        for key in self.document_topic_prob:
            if key in new_unknown_list:
                self.document_topic_prob[key]["unknown"] = 1.0
            else:
                self.document_topic_prob[key]["unknown"] = 0.0

        self.parts_dict['unknown'].part_data = new_unknown_list
        logger.info("Finished")

    def Save(self, new_workspace_path):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].Save")
        logger.info("Starting")
        #copy associated saved model components to new workspace location if it was changed
        if self.generated_flag and (self._filedir != self._new_filedir or self._workspace_path != new_workspace_path):
            if not os.path.exists(new_workspace_path+"/"+self.sample_type):
                os.makedirs(new_workspace_path+"/"+self.sample_type)
            if os.path.exists(new_workspace_path + self._new_filedir):
                os.rename(new_workspace_path+self._new_filedir, new_workspace_path+self._new_filedir+"_old")
            copytree(self._workspace_path+self._filedir, new_workspace_path+self._new_filedir)
            self._workspace_path = new_workspace_path
            self._filedir = self._new_filedir
        logger.info("Finished")

class LDASample(TopicSample):
    def __init__(self, key, dataset_key, model_parameters):
        logger = logging.getLogger(__name__+".LDASample["+str(key)+"].__init__")
        logger.info("Starting")
        TopicSample.__init__(self, key, dataset_key, "LDA", model_parameters)

        #fixed properties that may be externally accessed but do not change after being initialized
        self._num_passes = model_parameters['num_passes']
        self._alpha = model_parameters['alpha']
        self._eta = model_parameters['eta']

        #these need to be removed before pickling during saving due to threading and use of pool
        #see __getstate__ for removal and Load and Reload for readdition
        self.res = None
        self.dictionary = None
        self.corpus = None
        logger.info("Finished")

    def __getstate__(self):
        state = dict(self.__dict__)
        state['res'] = None
        state['dictionary'] = None
        state['corpus'] = None
        state['model'] = None
        return state
    def __repr__(self):
        return 'LDASample: %s' % (self.key,)
    
    @property
    def num_passes(self):
        return self._num_passes

    @property
    def alpha(self):
        return self._alpha

    @property
    def eta(self):
        return self._eta

    def GenerateStart(self, pool):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].GenerateStart")
        logger.info("Starting")
        self.start_dt = datetime.now()
        self.res = pool.apply_async(LDAPoolFunction, (self.tokensets,
                                                      self.num_topics,
                                                      self.num_passes,
                                                      self.alpha,
                                                      self.eta,
                                                      self._workspace_path,
                                                      self._filedir))
        logger.info("Finished")

    def GenerateFinish(self, dataset):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].GenerateFinish")
        logger.info("Starting")
        self.generated_flag = True
        self.dictionary = gensim.corpora.Dictionary.load(self._workspace_path+self._filedir+'/ldadictionary.dict')
        self.corpus = gensim.corpora.MmCorpus(self._workspace_path+self._filedir+'/ldacorpus.mm')
        self.model = gensim.models.ldamodel.LdaModel.load(self._workspace_path+self._filedir+'/ldamodel.lda')
        topic_document_prob, document_topic_prob = self.res.get()
        self.topic_documents_prob = topic_document_prob
        self.document_topic_prob = document_topic_prob

        for topic_num in self.topic_documents_prob:
            self.parts_dict[topic_num] = LDATopicPart(self, topic_num, dataset)
        self.parts_dict['unknown'] = TopicUnknownPart(self, 'unknown', [], dataset)

        self.word_num = 10
        self.ApplyDocumentCutoff()
        
        self.end_dt = datetime.now()
        logger.info("Finished")

    def Load(self, workspace_path):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].Load")
        logger.info("Starting")
        self._workspace_path = workspace_path
        if self.generated_flag:
            self.dictionary = gensim.corpora.Dictionary.load(self._workspace_path+self._filedir+'/ldadictionary.dict')
            self.corpus = gensim.corpora.MmCorpus(self._workspace_path+self._filedir+'/ldacorpus.mm')
            self.model = gensim.models.ldamodel.LdaModel.load(self._workspace_path+self._filedir+'/ldamodel.lda')
        logger.info("Finished")

class BitermSample(TopicSample):
    def __init__(self, key, dataset_key, model_parameters):
        logger = logging.getLogger(__name__+".BitermSample["+str(key)+"].__init__")
        logger.info("Starting")
        TopicSample.__init__(self, key, dataset_key, "Biterm", model_parameters)

        #fixed properties that may be externally accessed but do not change after being initialized
        self._num_iterations = model_parameters['num_iterations']

        #these need to be removed before pickling during saving due to threading and use of pool
        #see __getstate__ for removal and Load and Reload for readdition
        self.res = None
        self.transformed_texts = None
        self.vocab = None
        logger.info("Finished")

    def __getstate__(self):
        state = dict(self.__dict__)
        state['res'] = None
        state['transformed_texts'] = None
        state['vocab'] = None
        state['model'] = None
        return state
    def __repr__(self):
        return 'BitermSample: %s' % (self.key,)

    @property
    def num_iterations(self):
        return self._num_iterations

    def GenerateStart(self, pool):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].GenerateStart")
        logger.info("Starting")
        self.start_dt = datetime.now()
        self.res = pool.apply_async(BitermPoolFunction, (self.tokensets,
                                                         self.num_topics,
                                                         self.num_iterations,
                                                         self._workspace_path,
                                                         self._filedir))
        logger.info("Finished")

    def GenerateFinish(self, dataset):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].GenerateFinish")
        logger.info("Starting")
        self.generated_flag = True
        with bz2.BZ2File(self._workspace_path+self._filedir+'/transformed_texts.pk', 'rb') as infile:
            self.transformed_texts = cPickle.load(infile)
        with bz2.BZ2File(self._workspace_path+self._filedir+'/vocab.pk', 'rb') as infile:
            self.vocab = cPickle.load(infile)
        with bz2.BZ2File(self._workspace_path+self._filedir+'/btm.pk', 'rb') as infile:
            self.model = cPickle.load(infile)
        
        topic_document_prob, document_topic_prob = self.res.get()
        self.topic_documents_prob = topic_document_prob
        self.document_topic_prob = document_topic_prob

        for topic_num in self.topic_documents_prob:
            self.parts_dict[topic_num] = BitermTopicPart(self, topic_num, dataset)
        self.parts_dict['unknown'] = TopicUnknownPart(self, 'unknown', [], dataset)

        self.word_num = 10
        self.ApplyDocumentCutoff()
        
        self.end_dt = datetime.now()
        logger.info("Finished")

    def Load(self, workspace_path):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].Load")
        logger.info("Starting")
        self._workspace_path = workspace_path
        if self.generated_flag:
            with bz2.BZ2File(self._workspace_path+self.filedir+'/transformed_texts.pk', 'rb') as infile:
                self.transformed_texts = cPickle.load(infile)
            with bz2.BZ2File(self._workspace_path+self.filedir+'/vocab.pk', 'rb') as infile:
                self.vocab = cPickle.load(infile)
            with bz2.BZ2File(self._workspace_path+self.filedir+'/btm.pk', 'rb') as infile:
                self.model = cPickle.load(infile)
        logger.info("Finished")

class MergedPart(GenericObject):
    def __init__(self, parent, key, name=None):
        logger = logging.getLogger(__name__+".MergedPart["+str(key)+"].__init__")
        logger.info("Starting")
        if name is None:
            name="Merged Part: "+str(key)
        GenericObject.__init__(self, key, parent=parent, name=name)

        #properties that automatically update last_changed_dt

        #objects that have their own last_changed_dt and thus need to be checked dynamically
        self.parts_dict = OrderedDict()

        logger.info("Finished")

    def __repr__(self):
        return 'MergedPart: %s' % (self.key,)

    @property
    def last_changed_dt(self):
        for part_key in self.parts_dict:
            tmp_last_changed_dt = self.parts_dict[part_key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value

    def DestroyObject(self):
        #any children Samples or GroupedSamples
        for part_key in list(self.parts_dict.keys()):
            self.parts_dict[part_key].DestroyObject()
        del self.parent.parts_dict[self.key]
        self.parent.last_changed_dt = datetime.now()

class ModelMergedPart(MergedPart):
    def __repr__(self):
        return 'ModelMergedPart: %s' % (self.key,)

    def UpdateDocumentNum(self, document_num, dataset):
        logger = logging.getLogger(__name__+".ModelMergedPart["+str(self.key)+"].UpdateDocumentNum")
        logger.info("Starting")
        for part_key in self.parts_dict:
            self.parts_dict[part_key].UpdateDocumentNum(document_num, dataset)
        self.last_changed_dt = datetime.now()
        logger.info("Finished")

class TopicMergedPart(ModelMergedPart):
    '''Instances of Merged LDA Topic objects'''
    def __init__(self, parent, key, name=None):
        logger = logging.getLogger(__name__+".TopicMergedPart["+str(key)+"].__init__")
        logger.info("Starting")
        if name is None:
            name = "Merged Topic: "+str(key)
        ModelMergedPart.__init__(self, parent, key, name=name)

        #properties that automatically update last_changed_dt
        self._word_num = 0

        logger.info("Finished")
    
    @property
    def word_num(self):
        return self._word_num
    @word_num.setter
    def word_num(self, value):
        self._word_num = value
        for part_key in self.parts_dict:
            self.parts_dict[part_key].word_num = value
        self.last_changed_dt = datetime.now()

    def GetTopicKeywordsList(self):
        keyword_set = set()
        for part_key in self.parts_dict:
            part_keywords = self.parts_dict[part_key].GetTopicKeywordsList()
            keyword_set.update({(keyword[0], 1) for keyword in part_keywords})
        return list(keyword_set)

class Part(GenericObject):
    def __init__(self, parent, key, name=None):
        logger = logging.getLogger(__name__+".Part["+str(key)+"].__init__")
        logger.info("Starting")
        if name is None:
            name = "Part: "+str(key)
        GenericObject.__init__(self, key, parent=parent, name=name)

        #properties that automatically update last_changed_dt
        self._document_num = 0
        
        #dictionary that is managed with setters
        #TODO they have not yet been converted into properties due to complexity
        self.documents = []
        
        #properties that track datetime of creation and change
        logger.info("Finished")

    def __repr__(self):
        return 'Part: %s' % (self.key,)

    @property
    def document_num(self):
        return self._document_num
    @document_num.setter
    def document_num(self, value):
        self._document_num = value
        self.last_changed_dt = datetime.now()

    def DestroyObject(self):
        del self.parent.parts_dict[self.key]
        self.parent.last_changed_dt = datetime.now()

class ModelPart(Part):
    '''Instances of a part'''
    def __init__(self, parent, key, part_data, dataset, name=None):
        logger = logging.getLogger(__name__+".ModelPart["+str(key)+"].__init__")
        logger.info("Starting")
        if name is None:
            name = "Model Part: "+str(key)
        Part.__init__(self, parent, key, name=name)

        #properties that automatically update last_changed_dt
        self._part_data = part_data

        self.UpdateDocumentNum(10, dataset)
        logger.info("Finished")

    def __repr__(self):
        return 'ModelPart: %s' % (self.key,)

    @property
    def part_data(self):
        return self._part_data
    @part_data.setter
    def part_data(self, value):
        self._part_data = value
        self.last_changed_dt = datetime.now()

    def UpdateDocumentNum(self, document_num, dataset):
        logger = logging.getLogger(__name__+".ModelPart["+str(self.key)+"].UpdateDocumentNum")
        logger.info("Starting")

        if isinstance(self.parent, ModelMergedPart):
            sample_key = self.parent.parent.key
        else:
            sample_key = self.parent.key

        #cannot have more documents than what is avaliable
        if document_num > len(self.part_data):
            document_num = len(self.part_data)
        #shrink if appropriate
        if document_num < self.document_num:
            self.documents = self.documents[:document_num]
            self.last_changed_dt = datetime.now()
            self.document_num = document_num
        #grow if approrpriate
        elif document_num > self.document_num:
            for i in range(self.document_num, document_num):
                key = self.part_data[i]
                document = dataset.SetupDocument(key)
                if document is not None:
                    self.documents.append(key)
                    document.AddSampleConnections(self)
                    self.last_changed_dt = datetime.now()
            self.document_num = document_num
        logger.info("Finished")

class TopicPart(ModelPart):
    '''Instances of Topic objects'''
    def __init__(self, parent, key, dataset, name=None):
        logger = logging.getLogger(__name__+".TopicPart["+str(key)+"].__init__")
        logger.info("Starting")
        if name is None:
            name = "Topic: "+str(key)
        ModelPart.__init__(self, parent, key, [], dataset, name)
        
        #properties that automatically update last_changed_dt
        self._word_num = 0
        self._word_list = []

        logger.info("Finished")
    
    @property
    def word_num(self):
        return self._word_num
    @word_num.setter
    def word_num(self, value):
        self._word_num = value
        self.last_changed_dt = datetime.now()
    
    @property
    def word_list(self):
        return self._word_list
    @word_list.setter
    def word_list(self, value):
        self._word_list = value
        self.last_changed_dt = datetime.now()

    def GetTopicKeywordsList(self):
        return self.word_list[0:self.word_num]

class LDATopicPart(TopicPart):
    '''Instances of LDA Topic objects'''
    def __init__(self, parent, key, dataset, name=None):
        logger = logging.getLogger(__name__+".LDATopicPart["+str(key)+"].__init__")
        logger.info("Starting")
        TopicPart.__init__(self, parent, key, dataset, name=name)
        logger.info("Finished")

    @property
    def word_num(self):
        return self._word_num
    @word_num.setter
    def word_num(self, value):
        logger = logging.getLogger(__name__+".LDATopicPart["+str(self.key)+"].word_num")
        logger.info("Starting")
        self._word_num = value
        if len(self.word_list) < value:
            self.word_list.clear()
            if isinstance(self.parent, ModelMergedPart):
                self.word_list.extend(self.parent.parent.model.show_topic(self.key-1, topn=value))
            else:
                self.word_list.extend(self.parent.model.show_topic(self.key-1, topn=value))
        self.last_changed_dt = datetime.now()
        logger.info("Finished")

class BitermTopicPart(TopicPart):
    '''Instances of Biterm Topic objects'''
    def __init__(self, parent, key, dataset, name=None):
        logger = logging.getLogger(__name__+".BitermTopicPart["+str(key)+"].__init__")
        logger.info("Starting")
        TopicPart.__init__(self, parent, key, dataset, name=name)
        logger.info("Finished")

    @property
    def word_num(self):
        return self._word_num
    @word_num.setter
    def word_num(self, value):
        logger = logging.getLogger(__name__+".BitermTopicPart["+str(self.key)+"].word_num")
        logger.info("Starting")
        if len(self.word_list) < value:
            self.word_list.clear()
            if isinstance(self.parent, ModelMergedPart):
                word_df = btm.get_top_topic_words(self.parent.parent.model, words_num=value, topics_idx=[self.key-1])
                word_list = word_df.values.tolist()
                prob_list = []
                for word in word_list:
                    word_idx = np.where(self.parent.model.vocabulary_ == word)
                    prob_list.append(self.parent.parent.model.matrix_topics_words_[self.key-1][idx][0])
                self.word_list = list(zip(word_list, prob_list))
            else:
                word_df = btm.get_top_topic_words(self.parent.model, words_num=value, topics_idx=[self.key-1])
                word_list = []
                prob_list = []
                for word in word_df.values.tolist():
                    word_idx = np.where(self.parent.model.vocabulary_ == word[0])
                    word_list.append(word[0])
                    prob_list.append(self.parent.model.matrix_topics_words_[self.key-1][word_idx[0]][0])
                self.word_list = list(zip(word_list, prob_list))
        self._word_num = value
        logger.info("Finished")

class TopicUnknownPart(ModelPart):
    '''Instances of Topic Unknown Part objects'''
    def __init__(self, parent, key, word_list, dataset, name="Unknown"):
        logger = logging.getLogger(__name__+".TopicUnknownPart["+str(key)+"].__init__")
        logger.info("Starting")
        ModelPart.__init__(self, parent, key, [], dataset, name=name)
        
        #properties that automatically update last_changed_dt
        self._word_num = 0
        self._word_list = []
        logger.info("Finished")

    @property
    def word_num(self):
        return self._word_num
    @word_num.setter
    def word_num(self, value):
        self._word_num = 0

    @property
    def word_list(self):
        return self._word_list
    @word_list.setter
    def word_list(self, value):
        _word_list = []

    def GetTopicKeywordsList(self):
        return []

class CustomPart(Part):
    def __init__(self, parent, key, name=None):
        logger = logging.getLogger(__name__+".CustomPart["+str(key)+"].__init__")
        logger.info("Starting")
        if name is None:
            name = "Custom Part: "+key
        Part.__init__(self, parent, key, name=name)

    def AddDocument(self, key, dataset):
        dataset.GetDocument(key)
        self.documents.append(key)
        self.document_num =+ 1
        self.last_changed_dt = datetime.now()

    def DeleteDocument(self, key):
        self.documents.remove(key)
        self.document_num =- 1
        self.last_changed_dt = datetime.now()

#training code to be run asyncronously
def LDAPoolFunction(tokensets, num_topics, num_passes, alpha, eta, workspace_path, filedir):
    '''Generates an LDA model'''
    logger = logging.getLogger(__name__+"LDAPoolFunction["+str(num_topics)+", "+str(num_passes)+", "+str(alpha)+", "+str(eta)+", "+str(filedir)+"].__init__")
    logger.info("Starting")
    logger.info("Starting generation of model")
    tokensets_keys = list(tokensets.keys())
    tokensets_values = list(tokensets.values())
    dictionary = gensim.corpora.Dictionary(tokensets_values)
    dictionary.compactify()
    if not os.path.exists(workspace_path+"/LDA"):
        os.makedirs(workspace_path+"/LDA")
    if not os.path.exists(workspace_path+filedir):
        os.makedirs(workspace_path+filedir)
    dictionary.save(workspace_path+filedir+'/ldadictionary.dict')
    logger.info("Dictionary created")
    raw_corpus = [dictionary.doc2bow(tokenset) for tokenset in tokensets_values]
    gensim.corpora.MmCorpus.serialize(workspace_path+filedir+'/ldacorpus.mm', raw_corpus)
    corpus = gensim.corpora.MmCorpus(workspace_path+filedir+'/ldacorpus.mm')
    logger.info("Corpus created")
    model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                            id2word=dictionary,
                                            num_topics=num_topics,
                                            passes=num_passes,
                                            alpha='auto',
                                            eta='auto')
    model.save(workspace_path+filedir+'/ldamodel.lda', 'wb')
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
    for i in range(num_topics):
        tmp_df = topic_document_prob_df.loc[topic_document_prob_df['topic_id'] == i+1].sort_values(by='prob', ascending=False)[['tokenset_key', 'prob']]
        topic_document_prob[i+1] = list(tmp_df.to_records(index=False))  

    logger.info("Finished")
    return topic_document_prob, document_topic_prob

def BitermPoolFunction(tokensets, num_topics, num_iterations, workspace_path, filedir):
    '''Generates an Biterm model'''
    logger = logging.getLogger(__name__+"BitermPoolFunction["+str(num_topics)+", "+str(num_iterations)+", "+str(filedir)+"].__init__")
    logger.info("Starting")
    
    if not os.path.exists(workspace_path+"/Biterm"):
        os.makedirs(workspace_path+"/Biterm")
    if not os.path.exists(workspace_path+filedir):
        os.makedirs(workspace_path+filedir)

    text_keys = []
    texts = []
    for key in tokensets:
        text_keys.append(key)
        text = ' '.join(tokensets[key])
        texts.append(text)

    logger.info("Starting generation of biterm model")
    X, vocab, vocab_dict = btm.get_words_freqs(texts)
    
    with bz2.BZ2File(workspace_path+filedir+'/vocab.pk', 'wb') as outfile:
        cPickle.dump(vocab, outfile)
    logger.info("Vocab created")

    tf = np.array(X.sum(axis=0)).ravel()
    # Vectorizing documents
    docs_vec = btm.get_vectorized_docs(texts, vocab)
    docs_lens = list(map(len, docs_vec))
    with bz2.BZ2File(workspace_path+filedir+'/transformed_texts.pk', 'wb') as outfile:
        cPickle.dump(docs_vec, outfile)
    logger.info("Texts transformed")

    logger.info("Starting Generation of BTM")
    biterms = btm.get_biterms(docs_vec)

    model = btm.BTM(X, vocab, T=num_topics, W=vocab.size, M=20, alpha=50/8, beta=0.01)
    topics = model.fit_transform(docs_vec, biterms, iterations=num_iterations, verbose=False)
    with bz2.BZ2File(workspace_path+filedir+'/btm.pk', 'wb') as outfile:
        cPickle.dump(model, outfile)
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
    for i in range(num_topics):
        tmp_df = topic_document_prob_df.loc[topic_document_prob_df['topic_id'] == i+1].sort_values(by='prob', ascending=False)[['tokenset_key', 'prob']]
        topic_document_prob[i+1] = list(tmp_df.to_records(index=False))

    logger.info("Finished")
    return topic_document_prob, document_topic_prob