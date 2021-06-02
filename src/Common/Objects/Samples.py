import logging
import random
import os
import bz2
import pickle
from datetime import datetime
from shutil import copytree
from collections import OrderedDict

#ML Libraries
import pandas as pd
import numpy as np
import gensim
import bitermplus as btm

import Common.Constants as Constants
from Common.Objects.Generic import GenericObject
import Common.Objects.Threads.Samples as SamplesThreads

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

    def Load(self, current_workspace):
        logger = logging.getLogger(__name__+".Sample["+str(self.key)+"].Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self, current_workspace):
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
        #fixed properties that may be externally accessed but do not change after being initialized
        self._tokensets = model_parameters['tokensets']
        self._num_topics = model_parameters['num_topics']

        #dictionary that is managed with setters

        #objects that have their own last_changed_dt and thus need to be checked dynamically
        
        #variable that should only be used internally and are never accessed from outside
    
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
    def num_topics(self):
        return self._num_topics
    
    @property
    def tokensets(self):
        return self._tokensets

    def ApplyDocumentCutoff(self):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].ApplyDocumentCutoff")
        logger.info("Starting")
        document_set = set()
        document_topic_prob_df = pd.DataFrame(data=self.document_topic_prob).transpose()

        def UpdateLDATopicPart(topic):
            document_list = []
            document_s = document_topic_prob_df[topic].sort_values(ascending=False)
            document_list = document_s.index[document_s >= self.document_cutoff].tolist()
            document_set.update(document_list)
            self.parts_dict[topic].part_data = document_list

        for topic in self.parts_dict:
            if isinstance(self.parts_dict[topic], Part) and topic != 'unknown':
                UpdateLDATopicPart(topic)
            elif isinstance(self.parts_dict[topic], MergedPart):
                for subtopic in self.parts_dict[topic].parts_dict:
                    if isinstance(self.parts_dict[topic].parts_dict[subtopic], Part) and topic != 'unknown':
                        UpdateLDATopicPart(topic)
        
        unknown_list = set(self.tokensets.keys()) - document_set
        unknown_df = document_topic_prob_df[document_topic_prob_df.index.isin(unknown_list)]
        unknown_series = unknown_df.max(axis=1).sort_values()
        new_unknown_list = list(unknown_series.index.values)
        
        document_topic_prob_df["unknown"] = 0.0
        document_topic_prob_df.loc[unknown_list, "unknown"] = 1.0
        self.document_topic_prob = document_topic_prob_df.to_dict(orient='index')

        self.parts_dict['unknown'].part_data = list(new_unknown_list)
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

        #these need to be removed before pickling during saving due to threading and use of multiple processes
        #see __getstate__ for removal and Load and Reload for readdition
        self.training_thread = None
        self.dictionary = None
        self.corpus = None
        logger.info("Finished")

    def __getstate__(self):
        state = dict(self.__dict__)
        #state['res'] = None
        state['training_thread'] = None
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

    def GenerateStart(self, notify_window, current_workspace_path):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].GenerateStart")
        logger.info("Starting")
        self.start_dt = datetime.now()
        self.training_thread = SamplesThreads.LDATrainingThread(notify_window,
                                                                current_workspace_path,
                                                                self.key,
                                                                self.tokensets,
                                                                self.num_topics,
                                                                self._num_passes,
                                                                self.alpha,
                                                                self.eta)
        logger.info("Finished")
    
    def GenerateFinish(self, result, dataset, current_workspace):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].GenerateFinish")
        logger.info("Starting")
        self.generated_flag = True
        self.training_thread.join()
        self.training_thread = None
        self.dictionary = gensim.corpora.Dictionary.load(current_workspace+"/Samples/"+self.key+'/ldadictionary.dict')
        self.corpus = gensim.corpora.MmCorpus(current_workspace+"/Samples/"+self.key+'/ldacorpus.mm')
        self.model = gensim.models.ldamodel.LdaModel.load(current_workspace+"/Samples/"+self.key+'/ldamodel.lda')

        self.document_topic_prob = result['document_topic_prob']

        for i in range(self.num_topics):
            topic_num = i+1
            self.parts_dict[topic_num] = LDATopicPart(self, topic_num, dataset)
        self.parts_dict['unknown'] = TopicUnknownPart(self, 'unknown', [], dataset)

        self.word_num = 10
        self.ApplyDocumentCutoff()
        
        self.end_dt = datetime.now()
        logger.info("Finished")

    #TODO change to new temporary file saving structure
    def OldLoad(self, workspace_path):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].Load")
        logger.info("Starting")
        self._workspace_path = workspace_path
        if self.generated_flag:
            self.dictionary = gensim.corpora.Dictionary.load(self._workspace_path+self._filedir+'/ldadictionary.dict')
            self.corpus = gensim.corpora.MmCorpus(self._workspace_path+self._filedir+'/ldacorpus.mm')
            self.model = gensim.models.ldamodel.LdaModel.load(self._workspace_path+self._filedir+'/ldamodel.lda')
        logger.info("Finished")

    def Load(self, current_workspace):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].Load")
        logger.info("Starting")
        if self.generated_flag:
            self.dictionary = gensim.corpora.Dictionary.load(current_workspace+"/Samples/"+self.key+'/ldadictionary.dict')
            self.corpus = gensim.corpora.MmCorpus(current_workspace+"/Samples/"+self.key+'/ldacorpus.mm')
            self.model = gensim.models.ldamodel.LdaModel.load(current_workspace+"/Samples/"+self.key+'/ldamodel.lda')
        logger.info("Finished")

    def Save(self, current_workspace):
        logger = logging.getLogger(__name__+".LDASample["+str(self.key)+"].Save")
        logger.info("Starting")
        if self.model is not None:
            self.model.save(current_workspace+"/Samples/"+self.key+'/ldamodel.lda', 'wb')
        if self.dictionary is not None:
            self.dictionary.save(current_workspace+"/Samples/"+self.key+'/ldadictionary.dict')
        if self.corpus is not None:
            gensim.corpora.MmCorpus.serialize(current_workspace+"/Samples/"+self.key+'/ldacorpus.mm', self.corpus)

#TODO figure out why samples dont have any documents attached for biterm when run on grouped documents (might also effect LDASample)
class BitermSample(TopicSample):
    def __init__(self, key, dataset_key, model_parameters):
        logger = logging.getLogger(__name__+".BitermSample["+str(key)+"].__init__")
        logger.info("Starting")
        TopicSample.__init__(self, key, dataset_key, "Biterm", model_parameters)

        #fixed properties that may be externally accessed but do not change after being initialized
        self._num_passes = model_parameters['num_passes']

        #these need to be removed before pickling during saving due to threading and use of multiple processes
        #see __getstate__ for removal and Load and Reload for readdition
        self.training_thread = None
        self.transformed_texts = None
        self.vocab = None
        logger.info("Finished")

    def __getstate__(self):
        state = dict(self.__dict__)
        state['training_thread'] = None
        state['transformed_texts'] = None
        state['vocab'] = None
        state['model'] = None
        return state
    def __repr__(self):
        return 'BitermSample: %s' % (self.key,)

    @property
    def num_passes(self):
        return self._num_passes
    
    def GenerateStart(self, notify_window, current_workspace_path):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].GenerateStart")
        logger.info("Starting")
        self.start_dt = datetime.now()
        self.training_thread = SamplesThreads.BitermTrainingThread(notify_window,
                                                                   current_workspace_path,
                                                                   self.key,
                                                                   self.tokensets,
                                                                   self.num_topics,
                                                                   self._num_passes)
        logger.info("Finished")
    
    def GenerateFinish(self, result, dataset, current_workspace):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].GenerateFinish")
        logger.info("Starting")
        self.generated_flag = True
        self.training_thread.join()
        self.training_thread = None
        with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/transformed_texts.pk', 'rb') as infile:
            self.transformed_texts = pickle.load(infile)
        with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/vocab.pk', 'rb') as infile:
            self.vocab = pickle.load(infile)
        with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/btm.pk', 'rb') as infile:
            self.model = pickle.load(infile)

        self.document_topic_prob = result['document_topic_prob']

        for i in range(self.num_topics):
            topic_num = i+1
            self.parts_dict[topic_num] = BitermTopicPart(self, topic_num, dataset)
        self.parts_dict['unknown'] = TopicUnknownPart(self, 'unknown', [], dataset)

        self.word_num = 10
        self.ApplyDocumentCutoff()
        
        self.end_dt = datetime.now()
        logger.info("Finished")

    #TODO change to new temporary file saving structure
    def OldLoad(self, workspace_path):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].Load")
        logger.info("Starting")
        self._workspace_path = workspace_path
        if self.generated_flag:
            with bz2.BZ2File(self._workspace_path+self.filedir+'/transformed_texts.pk', 'rb') as infile:
                self.transformed_texts = pickle.load(infile)
            with bz2.BZ2File(self._workspace_path+self.filedir+'/vocab.pk', 'rb') as infile:
                self.vocab = pickle.load(infile)
            with bz2.BZ2File(self._workspace_path+self.filedir+'/btm.pk', 'rb') as infile:
                self.model = pickle.load(infile)
        logger.info("Finished")

    def Load(self, current_workspace):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].Load")
        logger.info("Starting")
        if self.generated_flag:
            with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/transformed_texts.pk', 'rb') as infile:
                self.transformed_texts = pickle.load(infile)
            with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/vocab.pk', 'rb') as infile:
                self.vocab = pickle.load(infile)
            with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/btm.pk', 'rb') as infile:
                self.model = pickle.load(infile)
        logger.info("Finished")

    def Save(self, current_workspace):
        logger = logging.getLogger(__name__+".BitermSample["+str(self.key)+"].Save")
        logger.info("Starting")
        if self.transformed_texts is not None:
            with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/transformed_texts.pk', 'wb') as outfile:
                pickle.dump(self.transformed_texts, outfile)
        if self.vocab is not None:
            with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/vocab.pk', 'wb') as outfile:
                pickle.dump(self.vocab, outfile)
        if self.model is not None:
            with bz2.BZ2File(current_workspace+"/Samples/"+self.key+'/btm.pk', 'wb') as outfile:
                pickle.dump(self.model, outfile)

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
                key = str(self.part_data[i])
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
                    prob_list.append(self.parent.parent.model.matrix_topics_words_[self.key-1][word_idx][0])
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

#TODO needs to be integrated to removed
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
