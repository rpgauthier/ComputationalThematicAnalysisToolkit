import logging
import bz2
import os.path
from threading import Thread
from shutil import copyfile

import wx
import pickle

import Common.CustomEvents as CustomEvents
from Common.GUIText import Main as GUIText
import Common.Objects.Datasets as Datasets

# Thread class that executes processing
class LoadThread(Thread):
    """Load Thread Class."""
    def __init__(self, notify_window, workspace_path):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.workspace_path = workspace_path
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+".LoadThread.run")
        logger.info("Starting")
        result = {}
        try:
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_CONFIG))
            with bz2.BZ2File(self.workspace_path+"/config.mta", 'rb') as infile:
                result['config'] = pickle.load(infile)

            result['datasets'] = {}
            if "datasets" in result['config']:
                for key in result['config']['datasets']:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_DATASET+str(key)))
                    dataset_filename = ""
                    for key_part in key:
                        dataset_filename = dataset_filename + str(key_part)+"_"
                    dataset_filename = dataset_filename + "datasets.mta"
                    if os.path.isfile(self.workspace_path+"/"+dataset_filename):
                        with bz2.BZ2File(self.workspace_path+"/"+dataset_filename, 'rb') as infile:
                            result['datasets'][key] = pickle.load(infile)

            result['samples'] = {}
            if 'samples' in result['config']:
                for key in result['config']['samples']:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.LOAD_BUSY_MSG_SAMPLE+str(key)))
                    sample_filename = str(key)+"_sample.mta"
                    if os.path.isfile(self.workspace_path+"/"+sample_filename):
                        with bz2.BZ2File(self.workspace_path+"/"+sample_filename, 'rb') as infile:
                            result['samples'][key] = pickle.load(infile)
                            result['samples'][key].Load(self.workspace_path)

            result['codes'] = {}
            if "codes" in result['config']:
                with bz2.BZ2File(self.workspace_path+"/codes.mta", 'rb') as infile:
                    result['codes'] = pickle.load(infile)

        except (TypeError, FileNotFoundError):
            wx.LogError(GUIText.LOAD_FAILURE + self.workspace_path)
            logger.exception("Failed to load workspace[%s]", self.workspace_path)
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.LoadResultEvent(result))


# Thread class that executes processing
class SaveThread(Thread):
    """Load Thread Class."""
    def __init__(self, notify_window, workspace_path, config_data, datasets, samples, codes, last_load_dt):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.workspace_path = workspace_path
        self.config_data = config_data
        self.datasets = datasets
        self.samples = samples
        self.codes = codes
        self.last_load_dt = last_load_dt
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        logger = logging.getLogger(__name__+".SaveThread.run")
        logger.info("Starting")
        result = {}
        try:
            if os.path.isfile(self.workspace_path+"/config.mta"):
                copyfile(self.workspace_path+"/config.mta",
                self.workspace_path+"/config.mta_bk")
            with bz2.BZ2File(self.workspace_path+"/config.mta", 'wb') as outfile:
                pickle.dump(self.config_data, outfile)

            for key in self.datasets:
                if self.datasets[key].last_changed_dt > self.last_load_dt:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_DATASETS+str(key)))
                    if isinstance(self.datasets[key], Datasets.Dataset):
                        dataset_filename = str(key[0])+"_"+str(key[1])+"_"+str(key[2])+"_datasets.mta"
                    elif isinstance(self.datasets[key], Datasets.GroupedDataset):
                        dataset_filename = str(key[0])+"_"+str(key[1])+"_datasets.mta"
                    if os.path.isfile(self.workspace_path+"/"+dataset_filename):
                        copyfile(self.workspace_path+"/"+dataset_filename,
                                 self.workspace_path+"/"+dataset_filename+"_bk")
                    with bz2.BZ2File(self.workspace_path+"/"+dataset_filename, 'wb') as outfile:
                        pickle.dump(self.datasets[key], outfile)
                
            for key in self.samples:
                if self.samples[key].last_changed_dt > self.last_load_dt:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.SAVE_BUSY_MSG_SAMPLES+str(key)))
                    sample_filename = str(key)+"_sample.mta"
                    if os.path.isfile(self.workspace_path+"/"+sample_filename):
                        copyfile(self.workspace_path+"/"+sample_filename,
                                 self.workspace_path+"/"+sample_filename+"_bk")
                    with bz2.BZ2File(self.workspace_path+"/"+sample_filename, 'wb') as outfile:
                        pickle.dump(self.samples[key], outfile)
                    #trigger save of each sample incase samples or thier components have components that can not be saved by pickling
                    self.samples[key].Save(self.workspace_path)

            if os.path.isfile(self.workspace_path+"/codes.mta"):
                copyfile(self.workspace_path+"/codes.mta",
                self.workspace_path+"/codes.mta_bk")
            with bz2.BZ2File(self.workspace_path+"/codes.mta", 'wb') as outfile:
                pickle.dump(self.codes, outfile)

        except (TypeError, FileNotFoundError):
            wx.LogError(GUIText.LOAD_FAILURE + self.workspace_path)
            logger.exception("Failed to save workspace[%s]", self.workspace_path)
        logger.info("Finished")
        wx.PostEvent(self._notify_window, CustomEvents.SaveResultEvent(result))
