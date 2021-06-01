import logging
import bz2
import os.path
import tarfile
from threading import Thread
import shutil
from datetime import datetime

import tempfile

import wx
import pickle

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
from Common.GUIText import Main as GUIText
import Common.Objects.Datasets as Datasets

# Thread class that executes processing
class OldLoadThread(Thread):
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
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_CONFIG))
            with bz2.BZ2File(self.save_path+"/config.mta", 'rb') as infile:
                result['config'] = pickle.load(infile)

            result['datasets'] = {}
            if "datasets" in result['config']:
                for key in result['config']['datasets']:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_DATASET+str(key)))
                    dataset_filename = ""
                    for key_part in key:
                        dataset_filename = dataset_filename + str(key_part)+"_"
                    dataset_filename = dataset_filename + "datasets.mta"
                    if os.path.isfile(self.save_path+"/"+dataset_filename):
                        with bz2.BZ2File(self.save_path+"/"+dataset_filename, 'rb') as infile:
                            result['datasets'][key] = pickle.load(infile)

            result['samples'] = {}
            if 'samples' in result['config']:
                for key in result['config']['samples']:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_SAMPLE+str(key)))
                    sample_filename = str(key)+"_sample.mta"
                    if os.path.isfile(self.save_path+"/"+sample_filename):
                        with bz2.BZ2File(self.save_path+"/"+sample_filename, 'rb') as infile:
                            result['samples'][key] = pickle.load(infile)
                            result['samples'][key].OldLoad(self.save_path)

            result['codes'] = {}
            if "codes" in result['config']:
                with bz2.BZ2File(self.save_path+"/codes.mta", 'rb') as infile:
                    result['codes'] = pickle.load(infile)

        except (TypeError, FileNotFoundError):
            wx.LogError(GUIText.LOAD_FAILURE + self.save_path)
            logger.exception("Failed to load workspace[%s]", self.save_path)
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.LoadResultEvent(result))


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
            with open(self.current_workspace_path+"/config.pk", 'wb') as outfile:
                pickle.dump(self.config_data, outfile)

            if not os.path.exists(self.current_workspace_path+"/Datasets"):
                os.mkdir(self.current_workspace_path+"/Datasets")
            existing_datasets = []
            for key in self.datasets:
                if isinstance(self.datasets[key], Datasets.Dataset):
                    dataset_filename = str(key[0])+"_"+str(key[1])+"_"+str(key[2])+".pk"
                elif isinstance(self.datasets[key], Datasets.GroupedDataset):
                    dataset_filename = str(key[0])+"_"+str(key[1])+".pk"
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

            #TODO rework this to append files one at a time and see fi that makes it more responsive
            with tarfile.open(self.save_path, 'w|bz2') as tar_file:
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

        except (FileNotFoundError):
            wx.LogError(GUIText.LOAD_FAILURE + self.save_path)
            logger.exception("Failed to load workspace[%s]", self.save_path)
            result=['error']
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.LoadResultEvent(result))

