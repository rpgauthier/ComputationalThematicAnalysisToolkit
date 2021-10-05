import logging
import os.path
import tarfile
from threading import Thread
import shutil
from datetime import datetime
from packaging import version

import wx
import pickle

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
from Common.GUIText import Main as GUIText
import Common.Objects.Datasets as Datasets
import Common.Database as Database

# Thread class that executes processing
class SaveThread(Thread):
    """Load Thread Class."""
    def __init__(self, notify_window, save_path, current_workspace_path, config_data, datasets, samples, codes, notes_text, last_load_dt):
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
                    dataset_filename = str(key[0])+"_"+str(key[1])+"_"+str(key[2])+".pk"
                existing_datasets.append(dataset_filename)
                if self.datasets[key].last_changed_dt > self.last_load_dt:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_DATASETS+str(key)))
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
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_SAMPLES+str(key)))
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

            with open(self.current_workspace_path+"/codes.pk", 'wb') as outfile:
                pickle.dump(self.codes, outfile)

            with tarfile.open(self.save_path, 'w|gz') as tar_file:
                tar_file.add(self.current_workspace_path, arcname='.')

            with open(self.save_path + "_notes.txt", 'w') as text_file:
                text_file.write(self.notes_text)

        except (FileExistsError):
            wx.LogError(GUIText.SAVE_FAILURE + self.save_path)
            logger.exception("Failed to save workspace[%s]", self.save_path)
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.SaveResultEvent(result))

class LoadThread(Thread):
    """Load Thread Class."""
    def __init__(self, notify_window, save_path, current_workspace_path):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.save_path = save_path
        self.current_workspace_path = current_workspace_path
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+".LoadThread.run")
        logger.info("Starting")
        result = {}
        try:
            with tarfile.open(self.save_path, "r") as tar_file:
                tar_file.extractall(self.current_workspace_path)

            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_CONFIG))
            with open(self.current_workspace_path+"/config.pk", 'rb') as infile:
                result['config'] = pickle.load(infile)

            result['datasets'] = {}
            if "datasets" in result['config']:
                for key in result['config']['datasets']:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_DATASET+str(key)))
                    dataset_filename = '_'.join(key)
                    dataset_filename = dataset_filename + ".pk"
                    if os.path.isfile(self.current_workspace_path+"/Datasets/"+dataset_filename):
                        with open(self.current_workspace_path+"/Datasets/"+dataset_filename, 'rb') as infile:
                            result['datasets'][key] = pickle.load(infile)

            result['samples'] = {}
            if 'samples' in result['config']:
                for key in result['config']['samples']:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_SAMPLE+str(key)))
                    sample_dirname = str(key)
                    if os.path.exists(self.current_workspace_path+"/Samples/"+sample_dirname):
                        with open(self.current_workspace_path+"/Samples/"+sample_dirname+"/sample.pk", 'rb') as infile:
                            result['samples'][key] = pickle.load(infile)
                            result['samples'][key].Load(self.current_workspace_path)

            result['codes'] = {}
            if "codes" in result['config']:
                with open(self.current_workspace_path+"/codes.pk", 'rb') as infile:
                    result['codes'] = pickle.load(infile)
        
            
            if 'version' in result['config']:
                ver = version.parse(result['config']['version'])
            else:
                ver = version.parse('0.0.0')

            if ver <  version.parse(Constants.CUR_VER):
                self.UpgradeWorkspace(result, ver)

        except (FileNotFoundError):
            wx.LogError(GUIText.LOAD_FAILURE + self.save_path)
            logger.exception("Failed to load workspace[%s]", self.save_path)
            result=['error']
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.LoadResultEvent(result))

    def UpgradeWorkspace(self, result, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_WORKSPACE + Constants.CUR_VER))
        #upgrade datasets
        for dataset_key in result['datasets']:
            self.UpgradeDataset(result['datasets'][dataset_key], ver)
        #upgrade database
        self.UpgradeDatabase(result, ver)
        #upgrade samples
        for sample_key in result['samples']:
            self.UpgradeSample(result['samples'][sample_key], result['datasets'][result['samples'][sample_key].dataset_key], ver)
        #upgrade codes
        for code_key in result['codes']:
            self.UpgradeCode(result['codes'][code_key], ver)

    def UpgradeDataset(self, dataset, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_DATASETS))
        if ver < version.parse('0.8.1'):
            #convert metdata fields list to dict of objects
            if hasattr(dataset, "_metadata_fields_list"):
                dataset.metadata_fields = {}
                for field_name, field_info in dataset._metadata_fields_list:
                    new_field = Datasets.Field(dataset,
                                            field_name,
                                            dataset,
                                            field_info['desc'],
                                            field_info['type'])
                    dataset.metadata_fields[field_name] = new_field
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
            if hasattr(dataset, 'avaliable_fields'):
                dataset.available_fields = dataset.avaliable_fields
                dataset.last_changed_dt = datetime.now()
            if hasattr(dataset, 'chosen_fields'):
                dataset.included_fields = dataset.chosen_fields
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

    def UpgradeDatabase(self, result, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_DATABASE))
        if ver < version.parse('0.8.1'):
            db_conn = Database.DatabaseConnection(self.current_workspace_path)
            #create database for token based operations
            if not os.path.isfile(self.current_workspace_path+"\\workspace_sqlite3.db"):
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_DATABASE_CREATE))
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
                    for field_key in result['datasets'][dataset_key].included_fields:
                        db_conn.InsertField(dataset_key, field_key)
                        if result['datasets'][dataset_key].included_fields[field_key].fieldtype == "string":
                            db_conn.InsertStringTokens(dataset_key, field_key, result['datasets'][dataset_key].included_fields[field_key].tokenset)
                            result['datasets'][dataset_key].included_fields[field_key].tokenset = None
                    db_conn.UpdateStringTokensTFIDF(dataset_key)
                    db_conn.ApplyDatasetRules(dataset_key, result['datasets'][dataset_key].filter_rules)
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
                db_conn.Upgrade()
                for dataset_key in result['datasets']:
                    db_conn.UpdateStringTokensTFIDF(dataset_key)
                    db_conn.ApplyDatasetRules(dataset_key, result['datasets'][dataset_key].filter_rules)    
                    db_conn.RefreshStringTokensIncluded(dataset_key)
                    db_conn.RefreshStringTokensRemoved(dataset_key)
                    included_counts = db_conn.GetIncludedStringTokensCounts(dataset_key)
                    result['datasets'][dataset_key].total_docs_remaining = included_counts['documents']
                    result['datasets'][dataset_key].total_tokens_remaining = included_counts['tokens']
                    result['datasets'][dataset_key].total_uniquetokens_remaining = included_counts['unique_tokens']
                    result['datasets'][dataset_key].last_changed_dt = datetime.now()

    def UpgradeSample(self, sample, dataset, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_SAMPLES))
        if ver < version.parse('0.8.1'):
            if not hasattr(sample, "_field_list"):
                sample._fields_list = list(dataset.included_fields.keys())
                sample.last_changed_dt = datetime.now()
            
            if hasattr(sample, 'metadataset_key_list'):
                sample.document_keys = sample.metadataset_key_list
                sample.last_changed_dt = datetime.now()

    def UpgradeCode(self, code, ver):
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.UPGRADE_BUSY_MSG_CODES))
        if ver < version.parse('0.8.1'):
            if not hasattr(code, "doc_positions"):
                code.doc_positions = {}
                code.last_changed_dt = datetime.now()
            if not hasattr(code, "_colour_rgb"):
                code._colour_rgb = (0,0,0,)
                code.last_changed_dt = datetime.now()

    
