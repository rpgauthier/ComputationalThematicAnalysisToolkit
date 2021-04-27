import logging
from datetime import datetime

import Common.Constants as Constants
from Common.Objects.Generic import GenericObject

#Object classes to facilitate controlling datasets
class GroupedDataset(GenericObject):
    '''Instances of Dataset objects to be grouped into one dataset'''
    def __init__(self, key, name):
        logger = logging.getLogger(__name__+".GroupedDataset["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, name=name)
        
        #properties that automatically update last_changed_dt
        self._language = "eng-sm"
        self._metadata = {}
        
        #objects that have their own last_changed_dt and thus need to be checked dynamically
        self.datasets = {}
        self.merged_fields = {}
        self.grouped_documents = {}
        
        logger.info("Finished")
    def __repr__(self):
        return 'GroupedDatasets: %s' % (str(self.key),)

    @property
    def language(self):
        return self._language
    @language.setter
    def language(self, value):
        self._language = value
        for key in self.datasets:
            self.datasets[key].language = value
        self.last_changed_dt = datetime.now()

    @property
    def metadata(self):
        return self._metadata
    @metadata.setter
    def metadata(self, value):
        self._metadata = value
        self.last_changed_dt = datetime.now()

    @property
    def last_changed_dt(self):
        for key in self.datasets:
            tmp_last_changed_dt = self.datasets[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        for key in self.merged_fields:
            tmp_last_changed_dt = self.merged_fields[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        for key in self.grouped_documents:
            tmp_last_changed_dt = self.grouped_documents[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value
    
    def DestroyObject(self):
        #any children Dataset
        for dataset_key in list(self.datasets.keys()):
            self.datasets[dataset_key].DestroyObject()
        #any children MergedField
        for field_key in list(self.merged_fields.keys()):
            self.merged_fields[field_key].DestroyObject()
        #any children GroupedDocuments:
        for document_key in list(self.grouped_documents.keys()):
            self.grouped_documents[document_key].DestroyObject()

    def SetupDocument(self, key):
        if key in self.metadata:
            if key not in self.grouped_documents:
                self.grouped_documents[key] = GroupedDocuments(self, key)
                for subkey in self.metadata[key]['submetadata']:
                    dataset = self.datasets[self.metadata[key]['submetadata'][subkey]['dataset']]
                    dataset.SetupDocument(subkey)
                    self.grouped_documents[key].documents[(dataset.key, subkey)] = dataset.documents[subkey]
            return self.grouped_documents[key]

class Dataset(GenericObject):
    '''instances of Datasets.'''
    def __init__(self, key, name, dataset_source, dataset_type, retrieval_details):
        logger = logging.getLogger(__name__+".Dataset["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, name=name)
        
        #properties that automatically update last_changed_dt
        self._language = "eng-sm"
        self._dataset_source = dataset_source
        self._dataset_type = dataset_type
        self._retrieval_details = retrieval_details
        self._grouping_field = None
        self._data = {}
        self._metadata = {}

        #objects that have their own last_changed_dt and thus need to be checked dynamically
        self.avaliable_fields = {}
        self.chosen_fields = {}
        self.merged_fields = {}
        self.documents = {}

        logger.info("Finished")

    def __repr__(self):
        return 'Dataset: %s' % (str(self.key),)

    @property
    def language(self):
        return self._language
    @language.setter
    def language(self, value):
        self._language = value
        self.last_changed_dt = datetime.now()

    @property
    def dataset_source(self):
        return self._dataset_source
    @dataset_source.setter
    def dataset_source(self, value):
        self._dataset_source = value
        self.last_changed_dt = datetime.now()

    @property
    def dataset_type(self):
        return self._dataset_type
    @dataset_type.setter
    def dataset_type(self, value):
        self._dataset_type = value
        self.last_changed_dt = datetime.now()

    @property
    def retrieval_details(self):
        return self._retrieval_details
    @retrieval_details.setter
    def retrieval_details(self, value):
        self._retrieval_details = value
        self.last_changed_dt = datetime.now()

    @property
    def grouping_field(self):
        return self._grouping_field
    @grouping_field.setter
    def grouping_field(self, value):
        self._grouping_field = value
        self.last_changed_dt = datetime.now()
    
    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        self._data = value
        self.last_changed_dt = datetime.now()
    
    @property
    def metadata(self):
        return self._metadata
    @metadata.setter
    def metadata(self, value):
        self._metadata = value
        self.last_changed_dt = datetime.now()

    @property
    def last_changed_dt(self):
        for key in self.avaliable_fields:
            tmp_last_changed_dt = self.avaliable_fields[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        for key in self.chosen_fields:
            tmp_last_changed_dt = self.chosen_fields[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        for key in self.merged_fields:
            tmp_last_changed_dt = self.merged_fields[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        for key in self.documents:
            tmp_last_changed_dt = self.documents[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value
    
    def DestroyObject(self):
        #any children MergedField
        for merged_field_name in list(self.merged_fields.keys()):
            self.merged_fields[merged_field_name].DestroyObject()
        #any children Fields
        for chosen_field_name in list(self.chosen_fields.keys()):
            self.chosen_fields[chosen_field_name].DestroyObject()
        for avaliable_field_name in list(self.avaliable_fields.keys()):
            self.avaliable_fields[avaliable_field_name].DestroyObject()
        if self.grouping_field is not None:
            self.grouping_field.DestroyObject()
        #any children GroupedDocuments and Documents:
        for document_key in list(self.documents.keys()):
            self.documents[document_key].DestroyObject()
        #remove self from parent if any
        if self.parent is not None:
            if self.key in self.parent.datasets:
                if self.parent.datasets[self.key] == self:
                    del self.parent.datasets[self.key]
            self.parent.last_changed_dt = datetime.now()
            self.parent = None

    def SetupDocument(self, key):
        if key in self._metadata:
            if key not in self.documents:
                self.documents[key] = Document(self, key)
            return self.documents[key]
        else:
            return None

class MergedField(GenericObject):
    '''Instances of Field objects to be merged into one field.'''
    def __init__(self, parent, key):
        logger = logging.getLogger(__name__+".MergedField["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, parent=parent, name=str(key))
        
        #properties that automatically update last_changed_dt
        self._tokenization_choice = 0
        self._tokenset = None
        self._included_tokenset_df = None
        
        #dictionary that is managed with setters
        #TODO they have not yet been converted into properties due to complexity
        self.filter_rules = []
        
        #objects that have their own last_changed_dt and thus need to be checked dynamically
        self.chosen_fields = {}
        
        #Default filter_rules
        self.filter_rules.append((Constants.FILTER_RULE_ANY, 'SPACE', Constants.FILTER_RULE_REMOVE))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, 'PUNCT', Constants.FILTER_RULE_REMOVE))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, 'NUM', Constants.FILTER_RULE_REMOVE))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, (Constants.FILTER_TFIDF_REMOVE, Constants.FILTER_TFIDF_LOWER, 0.25)))
        logger.info("Finished")

    def __repr__(self):
        return 'MergedField: %s' % (self.key,)

    @property
    def tokenization_choice(self):
        return self._tokenization_choice
    @tokenization_choice.setter
    def tokenization_choice(self, value):
        self._tokenization_choice = value
        for field in self.chosen_fields:
            self.chosen_fields[field].tokenization_choice = value
        self.last_changed_dt = datetime.now()

    @property
    def tokenset(self):
        return self._tokenset
    @tokenset.setter
    def tokenset(self, value):
        self._tokenset = value
        self.last_changed_dt = datetime.now()
    
    @property
    def included_tokenset_df(self):
        return self._included_tokenset_df
    @included_tokenset_df.setter
    def included_tokenset_df(self, value):
        self._included_tokenset_df = value
        self.last_changed_dt = datetime.now()
    
    @property
    def last_changed_dt(self):
        for key in self.chosen_fields:
            tmp_last_changed_dt = self.chosen_fields[key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value
    
    def DestroyObject(self):
        #any children Field
        for chosen_field_name in list(self.chosen_fields.keys()):
            self.chosen_fields[chosen_field_name].DestroyObject()
        #remove self from parent if any
        if self.parent is not None:
            if self.key in self.parent.merged_fields:
                if self.parent.merged_fields[self.key] == self:
                    del self.parent.merged_fields[self.key]
            self.parent.last_changed_dt = datetime.now()
            self.parent = None

    def AddFilterRule(self, new_rule):
        self.filter_rules.append(new_rule)
        self._last_changed_dt = datetime.now()

class Field(GenericObject):
    '''instances of Fields.'''
    def __init__(self, parent, key, dataset, desc, fieldtype):
        logger = logging.getLogger(__name__+".Field["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, parent=parent, name=str(key))
        
        #properties that automatically update last_changed_dt
        self._dataset = dataset
        self._desc = desc
        self._fieldtype = fieldtype
        self._tokenization_choice = 0
        self._tokenset = None
        self._included_tokenset_df = None

        #dictionary that is managed with setters
        #TODO they have not yet been converted into properties due to complexity
        self.filter_rules = []
        
        #objects that have their own last_changed_dt and thus need to be checked dynamically

        #Default filter_rules
        self.filter_rules.append((Constants.FILTER_RULE_ANY, 'SPACE', Constants.FILTER_RULE_REMOVE))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, 'PUNCT', Constants.FILTER_RULE_REMOVE))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, 'NUM', Constants.FILTER_RULE_REMOVE))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS))
        self.filter_rules.append((Constants.FILTER_RULE_ANY, Constants.FILTER_RULE_ANY, (Constants.FILTER_TFIDF_REMOVE, Constants.FILTER_TFIDF_LOWER, 0.25)))
        logger.info("Finished")

    def __repr__(self):
        return 'Field: %s' % (self.key,)
    
    @property
    def dataset(self):
        return self._dataset
    @dataset.setter
    def dataset(self, value):
        self._dataset = value
        self.last_changed_dt = datetime.now()
    
    @property
    def desc(self):
        return self._desc
    @desc.setter
    def desc(self, value):
        self._desc = value
        self.last_changed_dt = datetime.now()

    @property
    def fieldtype(self):
        return self._fieldtype
    @fieldtype.setter
    def fieldtype(self, value):
        self._fieldtype = value
        self.last_changed_dt = datetime.now()

    @property
    def tokenization_choice(self):
        return self._tokenization_choice
    @tokenization_choice.setter
    def tokenization_choice(self, value):
        self.tokenization_choice = value
        for field in self.chosen_fields:
            self.chosen_fields[field].tokenization_choice = value
        self.last_changed_dt = datetime.now()

    @property
    def tokenset(self):
        return self._tokenset
    @tokenset.setter
    def tokenset(self, value):
        self._tokenset = value
        self.last_changed_dt = datetime.now()
    
    @property
    def included_tokenset_df(self):
        return self._included_tokenset_df
    @included_tokenset_df.setter
    def included_tokenset_df(self, value):
        self._included_tokenset_df = value
        self.last_changed_dt = datetime.now()
    
    def DestroyObject(self):
        #remove self from Dataset
        if self.key in self.dataset.chosen_fields:
            if self.dataset.chosen_fields[self.key] == self:
                del self.dataset.chosen_fields[self.key]
        if self.key in self.dataset.avaliable_fields:
            if self.dataset.avaliable_fields[self.key] == self:
                del self.dataset.avaliable_fields[self.key]
        if self is self.dataset.grouping_field:
            self.dataset.grouping_field = None
        #remove self from parent MergedField
        if isinstance(self.parent, MergedField):
            if (self.dataset.key, self.key) in self.parent.chosen_fields:
                if self.parent.chosen_fields[(self.dataset.key, self.key)] == self:
                    del self.parent.chosen_fields[(self.dataset.key, self.key)]
            self.parent.last_changed_dt = datetime.now()
        self.parent = None
        self.dataset = None
        
    def AddFilterRule(self, new_rule):
        self.filter_rules.append(new_rule)
        self.last_changed_dt = datetime.now()

class GroupedDocuments(GenericObject):
    '''Instances of Groups of Document objects'''
    def __init__(self, parent, key):
        logger = logging.getLogger(__name__+".GroupedDocuments["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, parent=parent, name=str(key))

        #properties that automatically update last_changed_dt
        self.sample_connections = []
        
        #objects that have their own last_changed_dt and thus need to be checked dynamically
        self.documents = {}

        logger.info("Finished")
    
    def __repr__(self):
        return 'GroupedSample: %s' % (self.key,)

    @property
    def last_changed_dt(self):
        for document_key in self.documents:
            tmp_last_changed_dt = self.documents[document_key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value

    def DestroyObject(self):
        if self.parent is not None:
            if self.key in self.parent.grouped_documents:
                if self.parent.grouped_documents[key] == self:
                    del self.parent.grouped_documents[self.key]
            self.parent.last_changed_dt = datetime.now()
            self.parent = None

    def AddSampleConnections(self, obj):
        obj_module = getattr(obj, '__module__', None)
        key_path = []
        key_path.append((type(obj), obj.key))
        while obj.parent != None:
            obj = obj.parent
            key_path.append((type(obj), obj.key))
        key_path.reverse()
        self.sample_connections.append((obj_module, key_path))
        self.last_changed_dt = datetime.now()

    def RemoveSampleConnections(self, obj):
        obj_module = getattr(obj, '__module__', None)
        key_path = []
        key_path.append((type(obj), obj.key))
        while obj.parent != None:
            obj = obj.parent
            key_path.append((type(obj), obj.key))
        key_path.reverse()
        self.sample_connections.remove((obj_module, key_path))
        self.last_changed_dt = datetime.now()

    def GetSampleConnections(self, samples):
        connection_objects = []
        for key_path in self.sample_connections:
            if key_path[0] == Samples.__name__:
                current_parent = samples
                for key in key_path[1]:
                    if isinstance(current_parent, dict):
                        if key in current_parent:
                            current_parent = current_parent[key[1]]
                        else:
                            self.sample_connections.remove(key_path)
                            current_parent = None
                            break
                    elif isinstance(current_parent, Samples.Sample):
                        if key[1] in current_parent.parts_dict:
                            current_parent = current_parent.parts_dict[key[1]]
                        else:
                            self.sample_connections.remove(key_path)
                            current_parent = None
                            break
                    elif isinstance(current_parent, Samples.MergedPart):
                        if key[1] in current_parent.parts_dict:
                            current_parent = current_parent.parts_dict[key[1]]
                        else:
                            self.sample_connections.remove(key_path)
                            current_parent = None
                            break
                    else:
                        self.sample_connections.remove(key_path)
                        current_parent = None
                        break
                if current_parent is not None:
                    connection_objects.append(current_parent)

        return connection_objects

class Document(GenericObject):
    '''instances of Document.'''
    def __init__(self, parent, key):
        logger = logging.getLogger(__name__+".Document["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, parent=parent, name=str(key))

        #properties that automatically update last_changed_dt
        self._url = parent.metadata[key]['url']
        
        #dictionary that is managed with setters
        #TODO they have not yet been converted into properties due to complexity
        self.data_dict = {}
        self.sample_connections = []

        #objects that have their own last_changed_dt and thus need to be checked dynamically

        self.SetDocumentFields()
        logger.info("Finished")

    def __repr__(self):
        return 'Document: %s' % (self.key, )

    @property
    def url(self):
        return self._url
    @url.setter
    def url(self, value):
        self._url = value
        self.last_changed_dt = datetime.now() 

    def DestroyObject(self):
        if self.parent is not None:
            if self.key in self.parent.documents:
                if self.parent.documents[self.key] == self:
                    del self.parent.documents[self.key]
            self.parent.last_changed_dt = datetime.now()
            self.parent = None

    def SetDocumentFields(self):
        for field_key in self.parent.chosen_fields:
            if field_key in self.parent.data[self.key]:
                self.data_dict[field_key] = self.parent.data[self.key][field_key]
        for merged_key in self.parent.merged_fields:
            for field_key in self.parent.merged_fields[merged_key].chosen_fields:
                if field_key[0] == self.parent.key and field_key[1] in self.parent.data[self.key]:
                    self.data_dict[(merged_key, field_key)] = self.parent.data[self.key][field_key[1]]
        if self.parent.parent != None:
            for merged_key in self.parent.parent.merged_fields:
                for field_key in self.parent.parent.merged_fields[merged_key].chosen_fields:
                    if field_key[0] == self.parent.key  and field_key[1] in self.parent.data[self.key]:
                        self.data_dict[(merged_key, field_key)] = self.parent.data[self.key][field_key[1]]
        self.last_changed_dt = datetime.now()

    def AddSampleConnections(self, obj):
        obj_module = getattr(obj, '__module__', None)
        key_path = []
        key_path.append((type(obj), obj.key))
        while obj.parent != None:
            obj = obj.parent
            key_path.append((type(obj), obj.key))
        key_path.reverse()
        self.sample_connections.append((obj_module, key_path))
        self.last_changed_dt = datetime.now()

    def RemoveSampleConnections(self, obj):
        obj_module = getattr(obj, '__module__', None)
        key_path = []
        key_path.append((type(obj), obj.key))
        while obj.parent != None:
            obj = obj.parent
            key_path.append((type(obj), obj.key))
        key_path.reverse()
        self.sample_connections.remove((obj_module, key_path))
        self.last_changed_dt = datetime.now()

    def GetSampleConnections(self, samples):
        connection_objects = []
        for key_path in self.sample_connections:
            if key_path[0] == Samples.__name__:
                current_parent = samples
                for key in key_path[1]:
                    if isinstance(current_parent, dict):
                        if key in current_parent:
                            current_parent = current_parent[key[1]]
                        else:
                            self.sample_connections.remove(key_path)
                            current_parent = None
                            break
                    elif isinstance(current_parent, Samples.Sample):
                        if key[1] in current_parent.parts_dict:
                            current_parent = current_parent.parts_dict[key[1]]
                        else:
                            self.sample_connections.remove(key_path)
                            current_parent = None
                            break
                    elif isinstance(current_parent, Samples.MergedPart):
                        if key[1] in current_parent.parts_dict:
                            current_parent = current_parent.parts_dict[key[1]]
                        else:
                            self.sample_connections.remove(key_path)
                            current_parent = None
                            break
                    else:
                        self.sample_connections.remove(key_path)
                        current_parent = None
                        break
                if current_parent is not None:
                    connection_objects.append(current_parent)

        return connection_objects
