import wx

# Define events for communication by threads
EVT_PROGRESS_ID = wx.NewIdRef()
def EVT_PROGRESS(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_PROGRESS_ID, func)
class ProgressEvent(wx.PyEvent):
    """Simple event to carry arbitrary progress data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_PROGRESS_ID)
        self.data = data

RETRIEVE_EVT_RESULT_ID = wx.NewIdRef()
def RETRIEVE_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, RETRIEVE_EVT_RESULT_ID, func)
class RetrieveResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(RETRIEVE_EVT_RESULT_ID)
        self.data = data

TOKENIZER_EVT_RESULT_ID = wx.NewIdRef()
def TOKENIZER_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, TOKENIZER_EVT_RESULT_ID, func)
class TokenizerResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(TOKENIZER_EVT_RESULT_ID)
        self.data = data

LOAD_EVT_RESULT_ID = wx.NewIdRef()
def LOAD_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, LOAD_EVT_RESULT_ID, func)
class LoadResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(LOAD_EVT_RESULT_ID)
        self.data = data

SAVE_EVT_RESULT_ID = wx.NewIdRef()
def SAVE_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, SAVE_EVT_RESULT_ID, func)
class SaveResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(SAVE_EVT_RESULT_ID)
        self.data = data

RETRIEVE_EVT_RESULT_ID = wx.NewIdRef()
def RETRIEVE_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, RETRIEVE_EVT_RESULT_ID, func)
class RetrieveResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(RETRIEVE_EVT_RESULT_ID)
        self.data = data

APPLY_FILTER_RULES_EVT_RESULT_ID = wx.NewIdRef()
def APPLY_FILTER_RULES_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, APPLY_FILTER_RULES_EVT_RESULT_ID, func)
class ApplyFilterRulesResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(APPLY_FILTER_RULES_EVT_RESULT_ID)
        self.data = data

CREATE_WORD_DATAFRAME_EVT_RESULT_ID = wx.NewIdRef()
def CREATE_WORD_DATAFRAME_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, CREATE_WORD_DATAFRAME_EVT_RESULT_ID, func)
class CreateWordDataFrameResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(CREATE_WORD_DATAFRAME_EVT_RESULT_ID)
        self.data = data

MODELCREATED_EVT_RESULT_ID = wx.NewIdRef()
def MODELCREATED_EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, MODELCREATED_EVT_RESULT_ID, func)
class ModelCreatedResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(MODELCREATED_EVT_RESULT_ID)
        self.data = data