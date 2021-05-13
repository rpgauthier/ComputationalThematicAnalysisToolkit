import logging
from threading import Thread

import wx

import Common.Objects.Utilities.Datasets as DatasetUtilities
import Common.CustomEvents as CustomEvents

class TokenizerThread(Thread):
    """Tokenize Datasets Thread Class."""
    def __init__(self, notify_window, main_frame, dataset_objects):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.main_frame = main_frame
        self.dataset_objects = dataset_objects
        self.start()
    
    def run(self):
        DatasetUtilities.TokenizeDatasetObjects(self.dataset_objects, self._notify_window, self.main_frame)
        result = {}
        wx.PostEvent(self._notify_window, CustomEvents.TokenizerResultEvent(result))