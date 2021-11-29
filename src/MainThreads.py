import logging
import os
import re
import tarfile
from threading import Thread
import shutil
from datetime import datetime
from packaging import version
import uuid
from scipy.sparse import data

import wx
import pickle

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
from Common.GUIText import Main as GUIText
import Common.Objects.Datasets as Datasets
import Common.Objects.Samples as Samples
import Common.Database as Database
import Common.Objects.Codes as Codes

# Thread class that executes processing
class SaveThread(Thread):
    """Load Thread Class."""
    def __init__(self, notify_window, save_path, current_workspace_path, config_data, datasets, samples, codes, notes_text, last_load_dt, autosave=False):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.save_path = save_path
        self.current_workspace_path = current_workspace_path
        self.config_data = config_data
        self.datasets = datasets
        self.samples = samples
        self.codes = codes
        self.notes_text = notes_text
        self.last_load_dt = last_load_dt
        self.autosave = autosave
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+".SaveThread.run")
        logger.info("Starting")
        result = {}
        try:
            self.config_data['version'] = Constants.CUR_VER
            with open(self.current_workspace_path+"/config.pk", 'wb') as outfile:
                pickle.dump(self.config_data, outfile)

            if not os.path.exists(self.current_workspace_path+"/Datasets"):
                os.mkdir(self.current_workspace_path+"/Datasets")
            existing_datasets = []
            for key in self.datasets:
                if isinstance(self.datasets[key], Datasets.Dataset):
                    dataset_filename = str(key)+".pk"
                existing_datasets.append(dataset_filename)
                if self.datasets[key].last_changed_dt > self.last_load_dt:
                    if not self.autosave:
                        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_DATASETS+str(self.datasets[key].name)))
                    with open(self.current_workspace_path+"/Datasets/"+dataset_filename, 'wb') as outfile:
                        pickle.dump(self.datasets[key], outfile)
            #remove any datasets that no longer exist
            dataset_filenames = os.listdir(self.current_workspace_path+"/Datasets/")
            for dataset_filename in dataset_filenames:
                if dataset_filename not in existing_datasets:
                    os.remove(self.current_workspace_path+"/Datasets/"+dataset_filename)

            if not os.path.exists(self.current_workspace_path+"/Samples/"):
                os.mkdir(self.current_workspace_path+"/Samples")
            existing_samples = []
            for key in self.samples:
                sample_dirname = str(key)
                existing_samples.append(sample_dirname)
                if self.samples[key].last_changed_dt > self.last_load_dt:
                    if not self.autosave:
                        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_SAMPLES+str(self.samples[key].name)))
                    if not os.path.exists(self.current_workspace_path+"/Samples/"+sample_dirname):
                        os.mkdir(self.current_workspace_path+"/Samples/"+sample_dirname)
                    with open(self.current_workspace_path+"/Samples/"+sample_dirname+"/sample.pk", 'wb') as outfile:
                        pickle.dump(self.samples[key], outfile)
                    #trigger save of each sample incase they have components that can not be saved by pickling the sample
                    self.samples[key].Save(self.current_workspace_path)
            #remove any samples that no longer exist
            sample_dirnames = os.listdir(self.current_workspace_path+"/Samples/")
            for sample_dirname in sample_dirnames:
                if sample_dirname not in existing_samples:
                    shutil.rmtree(self.current_workspace_path+"/Samples/"+sample_dirname)

            if not self.autosave:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_CODES))
            with open(self.current_workspace_path+"/codes.pk", 'wb') as outfile:
                pickle.dump(self.codes, outfile)

            if not self.autosave:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_COMPRESSING))
                logger.info("Archiving Files to tar")
                with tarfile.open(self.save_path, 'w') as tar_file:
                    tar_file.add(self.current_workspace_path, arcname='.')
                with open(self.save_path + "_notes.txt", 'w') as text_file:
                    text_file.write(self.notes_text)
            else:
                logger.info("Moving Files to autsave folder")
                if os.path.exists(self.save_path):
                    shutil.rmtree(self.save_path)
                shutil.copytree(self.current_workspace_path, self.save_path)

        except (FileExistsError):
            wx.LogError(GUIText.SAVE_FAILURE + self.save_path)
            logger.exception("Failed to save workspace[%s]", self.save_path)
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.SaveResultEvent(result))

class LoadThread(Thread):
    """Load Thread Class."""
    def __init__(self, notify_window, save_path, current_workspace_path, restoreload=False):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.save_path = save_path
        self.current_workspace_path = current_workspace_path
        self.restoreload = restoreload
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+".LoadThread.run")
        logger.info("Starting")
        result = {}
        try:
            if not self.restoreload:
                with tarfile.open(self.save_path, "r") as tar_file:
                    tar_file.extractall(self.current_workspace_path)
            else:
                shutil.copytree(self.save_path, self.current_workspace_path, dirs_exist_ok=True)

            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_CONFIG))
            with open(self.current_workspace_path+"/config.pk", 'rb') as infile:
                result['config'] = pickle.load(infile)

            if 'version' in result['config']:
                ver = version.parse(result['config']['version'])
            else:
                ver = version.parse('0.0.0')

            if ver > version.parse(Constants.CUR_VER):
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_VERSION_FAILURE1 + str(ver)))
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_VERSION_FAILURE2))
                result = {'error': ""}
            else:

                result['datasets'] = {}
                if "datasets" in result['config']:
                    for key in result['config']['datasets']:
                        if not isinstance(key, str):
                            dataset_filename = '_'.join(key)
                        else:
                            dataset_filename = key
                        dataset_filename = dataset_filename + ".pk"
                        if os.path.isfile(self.current_workspace_path+"/Datasets/"+dataset_filename):
                            with open(self.current_workspace_path+"/Datasets/"+dataset_filename, 'rb') as infile:
                                result['datasets'][key] = pickle.load(infile)
                            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_DATASET+str(result['datasets'][key].name)))
                        

                result['samples'] = {}
                if 'samples' in result['config']:
                    for key in result['config']['samples']:
                        sample_dirname = str(key)
                        if os.path.exists(self.current_workspace_path+"/Samples/"+sample_dirname):
                            with open(self.current_workspace_path+"/Samples/"+sample_dirname+"/sample.pk", 'rb') as infile:
                                result['samples'][key] = pickle.load(infile)
                                result['samples'][key].Load(self.current_workspace_path)
                            if result['samples'][key].name != None:
                                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_SAMPLE+str(result['samples'][key].name)))
                            else:
                                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_SAMPLE+str(key)))
                        

                result['codes'] = {}
                if "codes" in result['config']:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_CODES))
                    with open(self.current_workspace_path+"/codes.pk", 'rb') as infile:
                        result['codes'] = pickle.load(infile)
            
                if ver < version.parse('0.8.5'):
                    self.Upgrade0_8_5(result, ver)
                    ver = version.parse('0.8.5')
                if ver < version.parse('0.8.6'):
                    self.Upgrade0_8_6(result, ver)
                    ver = version.parse('0.8.6')
                if ver < version.parse('0.8.7'):
                    self.Upgrade0_8_7(result, ver)
                    ver = version.parse('0.8.7')

        except:
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_OPEN_FAILURE + self.save_path))
            logger.exception("Failed to load workspace[%s]", self.save_path)
            result = {'error' : ""}
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.LoadResultEvent(result))

    def Upgrade0_8_5(self, result, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_WORKSPACE1 + str(ver) \
                                                                     + GUIText.UPGRADE_BUSY_MSG_WORKSPACE2 + '0.8.5'))
        def UpgradeConfig(config, ver):
            if ver < version.parse('0.8.1'):
                config['options'] = {}
                if 'multipledatasets_mode' in config:
                    config['options']['multipledatasets_mode'] = config['multipledatasets_mode']
                else:
                    config['options']['multipledatasets_mode'] = False
                if 'adjustable_metadata_mode' in config:
                    config['options']['adjustable_label_fields_mode'] = config['adjustable_metadata_mode']
                else:
                    config['options']['adjustable_label_fields_mode'] = False
                if 'adjustable_includedfields_mode' in config:
                    config['options']['adjustable_computation_fields_mode'] = config['adjustable_includedfields_mode']
                else:
                    config['options']['adjustable_computation_fields_mode'] = False
            if ver < version.parse('0.8.5'):
                if 'adjustable_metadata_mode' in config['options']:
                    config['options']['adjustable_label_fields_mode'] = config['options']['adjustable_metadata_mode']
                    del config['options']['adjustable_metadata_mode']

        def UpgradeDatasets(result, ver):
            for dataset in result['datasets'].values():
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_DATASETS))
                if ver < version.parse('0.8.1'):
                    #convert metadata fields list to dict of objects
                    if hasattr(dataset, "_metadata_fields_list"):
                        dataset.label_fields = {}
                        for field_name, field_info in dataset._metadata_fields_list:
                            new_field = Datasets.Field(dataset,
                                                    field_name,
                                                    dataset,
                                                    field_info['desc'],
                                                    field_info['type'])
                            dataset.label_fields[field_name] = new_field
                        del dataset._metadata_fields_list
                        #update rules
                        dataset.last_changed_dt = datetime.now()

                    #update variables names
                    if hasattr(dataset, '_total_unique_tokens'):
                        dataset._total_uniquetokens = dataset._total_unique_tokens
                        dataset.last_changed_dt = datetime.now()
                    if hasattr(dataset, '_total_unique_tokens_remaining'):
                        dataset._total_uniquetokens_remaining = dataset._total_unique_tokens_remaining
                        dataset.last_changed_dt = datetime.now()
                    if hasattr(dataset, 'available_fields'):
                        dataset.available_fields = dataset.available_fields
                        dataset.last_changed_dt = datetime.now()
                    if hasattr(dataset, 'chosen_fields'):
                        dataset.computational_fields = dataset.chosen_fields
                        dataset.last_changed_dt = datetime.now()

                    #cleanup attributes changed by switching to database
                    if hasattr(dataset, "_metadata"):
                        del dataset._metadata
                        dataset.last_changed_dt = datetime.now()
                    if hasattr(dataset, '_words_df'):
                        del dataset._words_df
                        for idx, rule in enumerate(dataset.filter_rules):
                            if isinstance(rule[3], tuple):
                                if rule[3][0] == Constants.FILTER_TFIDF_REMOVE or rule[3][0] == Constants.FILTER_TFIDF_INCLUDE:
                                    new_rule = (rule[0], rule[1], rule[2], (rule[3][0], rule[3][1], rule[3][2]*100 ))
                                    dataset.filter_rules[idx] = new_rule
                        dataset.last_changed_dt = datetime.now()
                if ver < version.parse('0.8.5'):
                    if dataset.dataset_source == 'Reddit':
                        if dataset.dataset_type == 'discussion':
                            dataset.retrieval_details['submission_count'] = len(dataset.data)
                            comment_count = 0
                            for field_name in dataset.data:
                                if 'comment.id' in dataset.data[field_name]:
                                    comment_count = comment_count + len(dataset.data[field_name]['comment.id'])
                            dataset.retrieval_details['comment_count'] = comment_count
                            dataset.last_changed_dt = datetime.now()
                        if dataset.dataset_type == 'discussion':
                            dataset.retrieval_details['submission_count'] = len(dataset.data)
                            dataset.last_changed_dt = datetime.now()
                        if dataset.dataset_type == 'comment':
                            dataset.retrieval_details['comment_count'] = len(dataset.data)
                            dataset.last_changed_dt = datetime.now()
                    
                    if hasattr(dataset, 'metadata_fields'):
                        dataset.label_fields = dataset.metadata_fields
                        del dataset.metadata_fields
                        dataset.last_changed_dt = datetime.now()
                    if hasattr(dataset, 'included_fields'):
                        dataset.computational_fields = dataset.included_fields
                        del dataset.included_fields
                        dataset.last_changed_dt = datetime.now()

                    dataset._uuid = str(uuid.uuid4())
                    for field_key in dataset.available_fields:
                        dataset.available_fields[field_key]._uuid = str(uuid.uuid4())
                    for field_key in dataset.label_fields:
                        dataset.label_fields[field_key]._uuid = str(uuid.uuid4())
                    for field_key in dataset.computational_fields:
                        dataset.computational_fields[field_key]._uuid = str(uuid.uuid4())
                    for document_key in dataset.documents:
                        dataset.documents[document_key]._uuid = str(uuid.uuid4())

        def UpgradeDatabase(result, ver):
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_DATABASE))
            if ver < version.parse('0.8.1'):
                #create database for token based operations
                if not os.path.isfile(self.current_workspace_path+"\\workspace_sqlite3.db"):
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_DATABASE_CREATE))
                    db_conn = Database.DatabaseConnection(self.current_workspace_path)
                    db_conn.Create()
                    for dataset_key in result['datasets']:
                        word_idx = result['datasets'][dataset_key].tokenization_choice
                        if word_idx == Constants.TOKEN_TEXT_IDX:
                            db_conn.InsertDataset(dataset_key, 'text')
                        elif word_idx == Constants.TOKEN_STEM_IDX:
                            db_conn.InsertDataset(dataset_key, 'stem')
                        elif word_idx == Constants.TOKEN_STEM_IDX:
                            db_conn.InsertDataset(dataset_key, 'lemma')
                        db_conn.InsertDocuments(dataset_key, result['datasets'][dataset_key].data.keys())
                        for field_key in result['datasets'][dataset_key].computational_fields:
                            db_conn.InsertField(dataset_key, field_key)
                            if result['datasets'][dataset_key].computational_fields[field_key].fieldtype == "string":
                                db_conn.InsertStringTokens(dataset_key, field_key, result['datasets'][dataset_key].computational_fields[field_key].tokenset)
                                result['datasets'][dataset_key].computational_fields[field_key].tokenset = None
                        db_conn.UpdateStringTokensTFIDF(dataset_key)
                        db_conn.ApplyAllDatasetRules(dataset_key, result['datasets'][dataset_key].filter_rules)
                        db_conn.RefreshStringTokensIncluded(dataset_key)
                        db_conn.RefreshStringTokensRemoved(dataset_key)
                        included_counts = db_conn.GetStringTokensCounts(dataset_key)
                        result['datasets'][dataset_key].total_docs = included_counts['documents']
                        result['datasets'][dataset_key].total_tokens = included_counts['tokens']
                        result['datasets'][dataset_key].total_uniquetokens = included_counts['unique_tokens']    
                        included_counts = db_conn.GetIncludedStringTokensCounts(dataset_key)
                        result['datasets'][dataset_key].total_docs_remaining = included_counts['documents']
                        result['datasets'][dataset_key].total_tokens_remaining = included_counts['tokens']
                        result['datasets'][dataset_key].total_uniquetokens_remaining = included_counts['unique_tokens']
                        result['datasets'][dataset_key].last_changed_dt = datetime.now()
                else:
                    db_conn = Database.DatabaseConnection(self.current_workspace_path)
                    db_conn.Upgrade0_8_5()
                    for dataset_key in result['datasets']:
                        db_conn.UpdateStringTokensTFIDF(dataset_key)
                        db_conn.ApplyAllDatasetRules(dataset_key, result['datasets'][dataset_key].filter_rules)    
                        db_conn.RefreshStringTokensIncluded(dataset_key)
                        db_conn.RefreshStringTokensRemoved(dataset_key)
                        included_counts = db_conn.GetIncludedStringTokensCounts(dataset_key)
                        result['datasets'][dataset_key].total_docs_remaining = included_counts['documents']
                        result['datasets'][dataset_key].total_tokens_remaining = included_counts['tokens']
                        result['datasets'][dataset_key].total_uniquetokens_remaining = included_counts['unique_tokens']
                        result['datasets'][dataset_key].last_changed_dt = datetime.now()
            elif ver < version.parse('0.8.2'):
                db_conn = Database.DatabaseConnection(self.current_workspace_path)
                db_conn.Upgrade0_8_5()

        def UpgradeSamples(result, ver):
            for sample in result['samples'].values():
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_SAMPLES))
                if ver < version.parse('0.8.1'):
                    if not hasattr(sample, "_field_list"):
                        sample._fields_list = list(result['datasets'][sample.dataset_key].computational_fields.keys())
                        sample.last_changed_dt = datetime.now()
                    
                    if hasattr(sample, 'metadataset_key_list'):
                        sample.document_keys = sample.metadataset_key_list
                        sample.last_changed_dt = datetime.now()
                if ver < version.parse('0.8.3'):
                    #reduce amount of data in each sample that has been generated to help speed up saving
                    if hasattr(sample, "_tokenset") and isinstance(sample._tokenset, dict) and sample.generated_flag:
                        sample.tokensets = sample.tokensets.keys()
                if ver < version.parse('0.8.5'):
                    sample._uuid = str(uuid.uuid4())
                    if isinstance(sample, Samples.Sample):
                        for part_key in sample.parts_dict:
                            sample.parts_dict[part_key]._uuid = str(uuid.uuid4())
                            if isinstance(sample.parts_dict[part_key], Samples.MergedPart):
                                for subpart_key in sample.parts_dict[part_key]:
                                    sample.parts_dict[part_key].parts_dict[subpart_key]._uuid = str(uuid.uuid4())

        def UpgradeCodes(result, ver):
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_CODES))
            for code_key in result['codes']:
                code = result['codes'][code_key]
                if ver < version.parse('0.8.1'):
                    if not hasattr(code, "doc_positions"):
                        code.doc_positions = {}
                        code.last_changed_dt = datetime.now()
                    if not hasattr(code, "_colour_rgb"):
                        code._colour_rgb = (0,0,0,)
                        code.last_changed_dt = datetime.now()
                if ver < version.parse('0.8.3'):
                    new_doc_positions = {}
                    for key in code.doc_positions:
                        new_doc_positions[(list(result['datasets'].keys())[0], key)] =  code.doc_positions[key]
                    code.doc_positions = new_doc_positions
                    new_quotations = []
                    for quotation in code.quotations:
                        new_quotations.append(Codes.Quotation(code, quotation.key[0], quotation.key[1], quotation.original_data, quotation.paraphrased_data))
                    code.quotations = new_quotations
                    code.last_changed_dt = datetime.now()
                if ver < version.parse('0.8.5'):
                    if not hasattr(code, "_uuid"):
                        #recursively add a uuid to every object
                        def UpdateCodeUUIDs(code):
                            code._uuid = str(uuid.uuid4())
                            for subcode_key in code.subcodes:
                                UpdateCodeUUIDs(code.subcodes[subcode_key])
                            for quotation in code.quotations:
                                quotation._uuid = str(uuid.uuid4())
                        UpdateCodeUUIDs(code)
            if ver < version.parse('0.8.5'):
                #changes code keys to use uuid instead of user name fields
                def CodeRekey(codes):
                    code_keys = list(codes.keys())
                    for old_key in code_keys:
                        code = codes[old_key]
                        new_key = code._uuid
                        code.key = new_key
                        #updates codes
                        codes[new_key] = code
                        del codes[old_key]
                        #update other objects
                        for obj in code.GetConnections(result['datasets'], result['samples']):
                            obj.codes.remove(old_key)
                            obj.codes.append(code.key)
                            obj.last_changed_dt = datetime.now()
                        CodeRekey(code.subcodes)
                CodeRekey(result['codes'])

        UpgradeConfig(result['config'], ver)
        #upgrade datasets
        UpgradeDatasets(result, ver)
        #upgrade database
        UpgradeDatabase(result, ver)
        #upgrade samples
        UpgradeSamples(result, ver)
        #upgrade codes
        UpgradeCodes(result, ver)

    def Upgrade0_8_6(self, result, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_WORKSPACE1 + str(ver) \
                                                                     + GUIText.UPGRADE_BUSY_MSG_WORKSPACE2 + '0.8.6'))
        #Updated config
        if 'adjustable_includedfields_mode' in result['config']['options']:
            result['config']['options']['adjustable_computation_fields_mode'] = result['config']['options']['adjustable_includedfields_mode']
            del result['config']['options']['adjustable_includedfields_mode']
        if 'model_iter' not in result['config']:
            result['config']['model_iter'] = 0
        for key in result['config']['filtering_module']['filters']:
            if 'applying_rules_paused' in result['config']['filtering_module']['filters'][key]:
                result['config']['filtering_module']['filters'][key]['autoapply'] = result['config']['filtering_module']['filters'][key]['applying_rules_paused']
                del result['config']['filtering_module']['filters'][key]['applying_rules_paused']
        
        #Update Codes
        def UpgradeCodes(codes):
            for old_key in list(codes.keys()):
                code = codes[old_key]
                new_key = code._uuid
                code.key = new_key
                codes[new_key] = code
                del codes[old_key]
                #update other objects and connections to other objects
                new_connections = []
                for obj in code.GetConnections(result['datasets'], result['samples']):
                    obj.codes.remove(old_key)
                    obj.codes.append(code.key)
                    obj.last_changed_dt = datetime.now()
                    obj_module = getattr(obj, '__module__', None)
                    key_path = []
                    key_path.append((type(obj), obj._uuid))
                    while obj.parent != None:
                        obj = obj.parent
                        key_path.append((type(obj), obj._uuid))
                    key_path.reverse()
                    new_connections.append((obj_module, key_path))
                code.connections = new_connections
                #Update doc_positions
                new_doc_positions = {}
                for key in code.doc_positions:
                    old_doc_position = code.doc_positions[key]
                    new_doc_position = []
                    old_dataset_key, old_doc_key = key
                    dataset = result['datasets'][old_dataset_key]
                    document = dataset.documents[old_doc_key]
                    for field_key, start, end in old_doc_position:
                        field = dataset.available_fields[field_key]
                        new_doc_position.append((field._uuid, start, end))
                    new_doc_positions[(dataset._uuid, document._uuid)] = new_doc_position
                code.doc_positions = new_doc_positions
                code.last_changed_dt = datetime.now()
                UpgradeCodes(code.subcodes)
                for quotation in code.quotations:
                    #TODO check what else is needed to update Quotations
                    quotation.key = quotation._uuid
                    old_dataset_key = quotation.dataset_key
                    quotation._dataset_key = result['datasets'][old_dataset_key]._uuid
                    old_doc_key = quotation.document_key
                    quotation._document_key = result['datasets'][old_dataset_key].documents[old_doc_key]._uuid

        UpgradeCodes(result['codes'])

        #Update Documents' Sample Connections as they will only work before Samples are updated
        for dataset in result['datasets'].values():
            for doc in dataset.documents.values():
                new_sample_connections = []
                for obj in doc.GetSampleConnections(result['samples']):
                    if isinstance(obj, list):
                        obj = obj[-1]
                    obj_module = getattr(obj, '__module__', None)
                    key_path = []
                    if isinstance(obj, Samples.Sample):
                        key = obj._uuid
                    else:
                        key = obj.key
                    key_path.append((type(obj), key))
                    while obj.parent != None:
                        obj = obj.parent
                        if isinstance(obj, Samples.Sample):
                            key = obj._uuid
                        else:
                            key = obj.key
                        key_path.insert(0, (type(obj), key))
                    new_sample_connections.append((obj_module, key_path))
                doc.sample_connections = new_sample_connections

        #Update Samples
        for old_key in list(result['samples'].keys()):
            sample = result['samples'][old_key]
            dataset = result['datasets'][sample.dataset_key]
            sample._dataset_key = dataset._uuid
            new_key = sample._uuid
            sample.key = new_key
            sample.name = old_key
            result['samples'][new_key] = sample
            del result['samples'][old_key]
            #Update Selected Documents
            new_selected_documents = []
            for doc_key in sample.selected_documents:
                new_selected_documents.append(dataset.documents[doc_key]._uuid)
            sample.selected_documents = new_selected_documents
            #Update Field List
            if sample.fields_list != None:
                new_fields_list = []
                for field_key in sample.fields_list:
                    new_fields_list.append(dataset.available_fields[field_key]._uuid)
                sample.fields_list = new_fields_list
            #Update lower part and merged_part objects
            for key in sample.parts_dict:
                part = sample.parts_dict[key]
                if isinstance(part, Samples.MergedPart):
                    for sub_key in part.parts_dict:
                        sub_part = part.parts_dict[sub_key]
                        new_documents = []
                        for old_doc_key in sub_part.documents:
                            doc = dataset.documents[old_doc_key]
                            new_documents.append(doc._uuid)
                        sub_part.documents = new_documents
                else:
                    new_documents = []
                    for old_doc_key in part.documents:
                        doc = dataset.documents[old_doc_key]
                        new_documents.append(doc._uuid)
                    part.documents = new_documents
            sample.last_changed_dt = datetime.now()

        #Update Datasets
        for old_dataset_key in list(result['datasets'].keys()):
            dataset = result['datasets'][old_dataset_key]
            new_dataset_key = dataset._uuid
            dataset.key = new_dataset_key
            result['datasets'][new_dataset_key] = dataset
            del result['datasets'][old_dataset_key]
            #Update Fields
            for old_field_key in list(dataset.label_fields.keys()):
                field = dataset.available_fields[old_field_key]
                del dataset.label_fields[old_field_key]
                dataset.label_fields[field._uuid] = field
            for old_field_key in list(dataset.computational_fields.keys()):
                field = dataset.available_fields[old_field_key]
                del dataset.computational_fields[old_field_key]
                dataset.computational_fields[field._uuid] = field
            for old_field_key in list(dataset.available_fields.keys()):
                field = dataset.available_fields[old_field_key]
                del dataset.available_fields[old_field_key]
                field.key = field._uuid
                dataset.available_fields[field.key] = field
            #Update Selected Documents
            new_selected_documents = []
            for doc_key in dataset.selected_documents:
                new_selected_documents.append(dataset.documents[doc_key]._uuid)
            dataset.selected_documents = new_selected_documents
            #Update Documents
            for old_doc_key in list(dataset.documents.keys()):
                document = dataset.documents[old_doc_key]
                document.doc_id = old_doc_key
                new_doc_key = dataset.documents[old_doc_key]._uuid
                document.key = new_doc_key
                dataset.documents[new_doc_key] = document
                del dataset.documents[old_doc_key]
            dataset.last_changed_dt = datetime.now()

        #Update database
        db_conn = Database.DatabaseConnection(self.current_workspace_path)
        for dataset_key in result['datasets']:
            dataset = result['datasets'][dataset_key]
            db_conn.UpdateDatasetKey((dataset.name, dataset.dataset_source, dataset.dataset_type,), dataset.key)
            for field_key in dataset.computational_fields:
                field = dataset.computational_fields[field_key]
                db_conn.UpdateFieldKey(dataset_key, field.name, field.key)
            db_conn.RefreshStringTokensIncluded(dataset.key)
            db_conn.RefreshStringTokensRemoved(dataset.key)
        
        #update csv datasets to be able to show start and end dates of data if they were created
        for dataset_key in result['datasets']:
            dataset = result['datasets'][dataset_key]
            if dataset.dataset_source == "CSV":
                start_datetime = None
                end_datetime = None
                for key in dataset.data:
                    if start_datetime == None or start_datetime > dataset.data[key]['created_utc']:
                        start_datetime = dataset.data[key]['created_utc']
                    if end_datetime == None or end_datetime < dataset.data[key]['created_utc']:
                        end_datetime = dataset.data[key]['created_utc']
                if start_datetime!= None and start_datetime != 0:
                    dataset.retrieval_details['start_date'] = start_datetime
                if end_datetime != None and end_datetime != 0:
                    dataset.retrieval_details['end_date'] = end_datetime
                dataset.last_changed_dt = datetime.now()

    def Upgrade0_8_7(self, result, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_WORKSPACE1 + str(ver) \
                                                                     + GUIText.UPGRADE_BUSY_MSG_WORKSPACE2 + '0.8.7'))

        def UpgradeDatabase(result, ver):
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_DATABASE))
            db_conn = Database.DatabaseConnection(self.current_workspace_path)
            db_conn.Upgrade0_8_7()
            for dataset_key in result['datasets']:
                db_conn.RefreshStringTokensIncluded(dataset_key)
                db_conn.RefreshStringTokensRemoved(dataset_key)
        
        UpgradeDatabase(result, ver)