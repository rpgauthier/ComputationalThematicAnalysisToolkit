import logging

import wx
import wx.grid

from Common.GUIText import Filtering as GUIText

class TokenGridTable(wx.grid.GridTableBase):
    def __init__(self, token_df):
        wx.grid.GridTableBase.__init__(self)
        self.token_df = token_df
        self._rows = len(self.token_df)
        self.col_names = [GUIText.FILTERS_WORDS,
                          GUIText.FILTERS_POS,
                          GUIText.FILTERS_NUM_WORDS,
                          GUIText.FILTERS_NUM_DOCS,
                          GUIText.FILTERS_SPACY_AUTO_STOPWORDS,
                          GUIText.FILTERS_TFIDF]
        self._cols = len(self.col_names)

    def GetColLabelValue(self, col):
        name = str(self.col_names[col])
        return name
    
    def GetColTupleValue(self, col):
        return self.col_names[col]

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.token_df)

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.col_names)

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return wx.grid.GRID_VALUE_TEXT

    def GetValue(self, row, col):
        """Return the value of a cell"""
        if self.col_names[col] == GUIText.FILTERS_TFIDF:
            return str(round(max(self.token_df.iloc[row][GUIText.FILTERS_TFIDF]), 4)) + " - " + str(round(min(self.token_df.iloc[row][GUIText.FILTERS_TFIDF]), 4))
        elif self.col_names[col] == GUIText.FILTERS_NUM_WORDS:
            return str(self.token_df.iloc[row][self.col_names[col]]) +" (" +str(self.token_df.iloc[row][GUIText.FILTERS_PER_WORDS])+"%)"
        elif self.col_names[col] == GUIText.FILTERS_NUM_DOCS:
            return str(self.token_df.iloc[row][self.col_names[col]]) +" (" +str(self.token_df.iloc[row][GUIText.FILTERS_PER_DOCS])+"%)"
        else:
            return str(self.token_df.iloc[row][self.col_names[col]])

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        pass

    def ResetView(self, grid):
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
        # XXX
        # Okay, this is really stupid, we need to "jiggle" the size
        # to get the scrollbars to recalibrate when the underlying
        # grid changes.
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
    def __init__(self, parent, tokens_df, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".TokenGrid.__init__")
        logger.info("Starting")
        wx.grid.Grid.__init__(self, parent, size=size)
        self.tokens_df = tokens_df
        self.gridtable = TokenGridTable(tokens_df)
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
            if self.IsSortOrderAscending():
                self.gridtable.token_df.sort_values(by=[col_string], inplace=True)
            else:
                self.gridtable.token_df.sort_values(by=[col_string], ascending=False, inplace=True)
        else:
            self.SetSortingColumn(col)
            self.gridtable.token_df.sort_values(by=[col_string], inplace=True)
        logger.info("Finish")

    def Update(self, tokens_df):
        logger = logging.getLogger(__name__+".TokenGrid.Update")
        logger.info("Starting")
        self.tokens_df = tokens_df
        self.gridtable = TokenGridTable(tokens_df)
        self.SetTable(self.gridtable, takeOwnership=True)
        self.gridtable.ResetView(self)
        for i in range(0, len(self.gridtable.col_names)):
            self.SetColLabelValue(i, self.gridtable.GetColLabelValue(i))
        self.ForceRefresh()
        logger.info("Finish")
