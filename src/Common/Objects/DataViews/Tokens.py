import logging

import wx
import wx.grid

from Common.GUIText import Filtering as GUIText
import Common.Database as Database

#TODO finish changing to us database as source of virtual table
class TokenGridTable(wx.grid.GridTableBase):
    def __init__(self, dataset, word_type):
        self.dataset = dataset
        self.word_type = word_type
        main_frame = wx.GetApp().GetTopWindow()
        
        self.word_search_term = ""
        self.pos_search_term = ""
        self.sort_col = GUIText.FILTERS_NUM_WORDS
        self.sort_ascending = False

        db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
        if self.word_type == "Included":
            self.data = db_conn.GetIncludedStringTokens(self.dataset.key, self.word_search_term, self.pos_search_term, self.sort_col, self.sort_ascending)
        else:
            self.data = db_conn.GetRemovedStringTokens(self.dataset.key, self.word_search_term, self.pos_search_term, self.sort_col, self.sort_ascending)

        wx.grid.GridTableBase.__init__(self)
        self._rows = self.GetNumberRows()
        self.col_names = [GUIText.FILTERS_WORDS,
                          GUIText.FILTERS_POS,
                          GUIText.FILTERS_NUM_WORDS,
                          GUIText.FILTERS_NUM_DOCS,
                          GUIText.FILTERS_SPACY_AUTO_STOPWORDS,
                          GUIText.FILTERS_TFIDF_MIN,
                          GUIText.FILTERS_TFIDF_MAX]

        self._cols = len(self.col_names)

    def GetColLabelValue(self, col):
        name = str(self.col_names[col])
        return name
    
    def GetColTupleValue(self, col):
        return self.col_names[col]

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.data)

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.col_names)

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return wx.grid.GRID_VALUE_TEXT

    def GetValue(self, row, col):
        """Return the value of a cell"""
        row_data = self.data[row]
        if self.col_names[col] == GUIText.FILTERS_NUM_WORDS:
            return str(row_data[col]) +" (" +str(round((row_data[col]/self.dataset.total_tokens)*100, 4))+"%)"
        elif self.col_names[col] == GUIText.FILTERS_NUM_DOCS:
            return str(row_data[col]) +" (" +str(round((row_data[col]/self.dataset.total_docs)*100, 4))+"%)"
        elif self.col_names[col] == GUIText.FILTERS_SPACY_AUTO_STOPWORDS:
            if row_data[col] == 0:
                return str(False)
            else:
                return str(True)
        else:
            return str(row_data[col])

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        pass

    def ResetView(self, grid):
        main_frame = wx.GetApp().GetTopWindow()
        db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
        if self.word_type == "Included":
            self.data = db_conn.GetIncludedStringTokens(self.dataset.key, self.word_search_term, self.pos_search_term, self.sort_col, self.sort_ascending)
        else:
            self.data = db_conn.GetRemovedStringTokens(self.dataset.key, self.word_search_term, self.pos_search_term, self.sort_col, self.sort_ascending)

        grid.BeginBatch()
        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,
            wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
            wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
            ]:
            if new < current:
                msg = wx.grid.GridTableMessage(self, delmsg, new, current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(self, addmsg, new-current)
                grid.ProcessTableMessage(msg)
        self.UpdateValues(grid)
        grid.EndBatch()
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        h,w = grid.GetSize()
        grid.SetSize((h+1, w))
        grid.SetSize((h, w))
        grid.ForceRefresh()
        self.UpdateValues(grid)
    
    def UpdateValues(self, grid):
        """Update all displayed values without changing the grid size"""
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

class TokenGrid(wx.grid.Grid):
    def __init__(self, parent, dataset, word_type, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".TokenGrid.__init__")
        logger.info("Starting")
        wx.grid.Grid.__init__(self, parent, size=size)
        self.gridtable = TokenGridTable(dataset, word_type)
        self.SetTable(self.gridtable, takeOwnership=True)
        self.EnableEditing(False)
        self.UseNativeColHeader(True)
        self.HideRowLabels()
        self.SetSelectionMode(wx.grid.Grid.SelectRows)
        self.SetCellHighlightPenWidth(0)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnSelect)
        self.Bind(wx.grid.EVT_GRID_COL_SORT, self.OnSort)
        logger.info("Finished")

    def OnSelect(self, event):
        self.SelectRow(event.GetRow())

    def OnSort(self, event):
        logger = logging.getLogger(__name__+".TokenGrid.OnSort")
        logger.info("Starting")
        col = event.GetCol()
        col_string = self.gridtable.GetColTupleValue(event.GetCol())
        if col == self.GetSortingColumn():
            self.gridtable.sort_col = col_string
            if self.IsSortOrderAscending():
                self.gridtable.sort_ascending = True
            else:
                self.gridtable.sort_ascending = False
        else:
            self.SetSortingColumn(col)
            self.gridtable.sort_col = col_string
            self.gridtable.sort_ascending = True
        self.gridtable.ResetView(self)
        logger.info("Finish")

    def Update(self, word_search_term, pos_search_term):
        logger = logging.getLogger(__name__+".TokenGrid.Update")
        logger.info("Starting")
        self.gridtable.word_search_term = word_search_term
        self.gridtable.pos_search_term = pos_search_term
        self.gridtable.ResetView(self)
        for i in range(0, len(self.gridtable.col_names)):
            self.SetColLabelValue(i, self.gridtable.GetColLabelValue(i))
        self.ForceRefresh()
        logger.info("Finish")
