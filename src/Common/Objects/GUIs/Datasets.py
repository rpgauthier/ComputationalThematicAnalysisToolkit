import logging
from datetime import datetime

import pandas as pd
import webbrowser

import wx
import wx.aui
import wx.grid
import wx.dataview as dv
import wx.lib.agw.infobar as infobar

from Common import Constants
from Common.GUIText import Datasets as GUIText
import Common.Notes as Notes
import Common.Objects.Datasets as Datasets
import Common.Objects.DataViews.Datasets as DatasetsDataViews
import Common.Objects.DataViews.Codes as CodesDataViews

class DataNotebook(wx.aui.AuiNotebook):
    def __init__(self, parent, grouped_dataset=None, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.__init__")
        logger.info("Starting")
        wx.aui.AuiNotebook.__init__(self, parent, style=Constants.NOTEBOOK_MOVEABLE, size=size)
        self.dataset = grouped_dataset

        self.dataset_data_tabs = {}

        self.menu = wx.Menu()
        self.menu_menuitem = None
        logger.info("Finished")

    def DatasetsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.DatasetsUpdated")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        dataset_data_tab_keys = list(self.dataset_data_tabs.keys())
        
        for key in dataset_data_tab_keys:
            index = self.GetPageIndex(self.dataset_data_tabs[key])
            if index is not wx.NOT_FOUND:
                self.RemovePage(index)
            del self.dataset_data_tabs[key]
        if self.dataset != None:
            current_parent = self.dataset
        else:
            current_parent = main_frame
        for key in current_parent.datasets:
            main_frame.PulseProgressDialog(GUIText.REFRESHING_DATASETS_BUSY_MSG+str(key))
            if key in self.dataset_data_tabs:
                self.dataset_data_tabs[key].Update()
            else:
                if isinstance(current_parent.datasets[key], Datasets.Dataset):
                    if len(current_parent.datasets[key].data) > 0:
                        self.dataset_data_tabs[key] = DataGrid(self, current_parent.datasets[key], self.GetSize())
                        self.AddPage(self.dataset_data_tabs[key], str(key))
                elif isinstance(current_parent.datasets[key], Datasets.GroupedDataset):
                    self.dataset_data_tabs[key] = DataNotebook(self, grouped_dataset=current_parent.datasets[key], size=self.GetSize())
                    self.dataset_data_tabs[key].DatasetsUpdated()
                    self.AddPage(self.dataset_data_tabs[key], str(key))
        logger.info("Finished")
    
    def DocumentsUpdated(self):
        logger = logging.getLogger(__name__+".DatasetDataNotebook.DocumentsUpdated")
        logger.info("Starting")
        for key in self.dataset_data_tabs:
            self.dataset_data_tabs[key].Update()
        logger.info("Finished")

    def ShowData(self, node):
        if node.key in self.dataset_data_tabs:
            index = self.GetPageIndex(self.dataset_data_tabs[node.key])
            self.SetSelection(index)
        elif node.parent is not None:
            self.ShowData(node.parent)

    def Load(self, saved_data):
        #NOT CURRENTLY USED as dataset objects contain all that is needed
        logger = logging.getLogger(__name__+".DatasetDataNotebook.Load")
        logger.info("Starting")
        for key in saved_data["groups"]:
            self.dataset_data_tabs[key].Load(saved_data["groups"][key])
        logger.info("Finished")

    def Save(self):
        #NOT CURRENTLY USED as dataset objects contain all that is needed
        logger = logging.getLogger(__name__+".DatasetDataNotebook.Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['datasets'] = {}
        saved_data["groups"] = {}
        for key in self.dataset_data_tabs:
            if isinstance(self.dataset_data_tabs[key], DataGrid):
                saved_data["datasets"][key] = {} 
            if isinstance(self.dataset_data_tabs[key], DataNotebook):
                saved_data["groups"][key] = self.dataset_data_tabs[key].Save()
        logger.info("Finished")
        return saved_data

#TODO replace dataviewctrl with dynamic columns
#to make only one needed for each entry in main_frame.datasets regardless of which type of dataset is used
class DataGridTable(wx.grid.GridTableBase):
    def __init__(self, dataset):
        wx.grid.GridTableBase.__init__(self)
        self.dataset = dataset
        self.data_df = pd.DataFrame(dataset.data.values())
        self._rows = len(self.data_df)
        self.col_names = []
        self.GetColNames()
        self._cols = len(self.col_names)
        self.data_df['Created UTC'] = pd.to_datetime(self.data_df['created_utc'], unit='s')

    def GetColNames(self):
        self.col_names = []
        self.col_names.append(("", "url"))
        self.col_names.append(("", 'Created UTC'))
        if self.dataset.grouping_field is not None:
            self.col_names.append(("Grouping Field", self.dataset.grouping_field.key))
        self.col_names.extend([("", field_name) for field_name in self.dataset.chosen_fields])
        for merged_field_key in self.dataset.merged_fields:
            self.col_names.extend([(merged_field_key, field_key) for field_key in self.dataset.merged_fields[merged_field_key].chosen_fields])
        if self.dataset.parent is not None:
            for merged_field_key in self.dataset.parent.merged_fields:
                merged_field = self.dataset.parent.merged_fields[merged_field_key]
                for field_key in merged_field.chosen_fields:
                    field = merged_field.chosen_fields[field_key]
                    if field.dataset is self.dataset:
                        self.col_names.append((merged_field.key, field_key))

    def GetColLabelValue(self, col):
        name = ""
        if self.col_names[col][0] == "":
            name = str(self.col_names[col][1])
        else:
            name = str(self.col_names[col][0])+"("+str(self.col_names[col][1])+")"
        return name
    
    def GetColTupleValue(self, col):
        if self.col_names[col][0] == "":
            return self.col_names[col][1]
        else:
            if isinstance(self.col_names[col][1], tuple):
                return self.col_names[col][1][1]
            else:
                return self.col_names[col][1]

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.data_df)

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return len(self.col_names)

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        return wx.grid.GRID_VALUE_TEXT

    def GetValue(self, row, col):
        """Return the value of a cell"""
        col_name = self.col_names[col][1]
        if isinstance(col_name, tuple):
            col_name = col_name[1]
        df_row = self.data_df.iloc[row]
        return str(df_row[col_name])

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        pass

    def ResetView(self, grid):
        self.GetColNames()
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

class DataGrid(wx.grid.Grid):
    def __init__(self, parent, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetDataGrid.__init__")
        logger.info("Starting")
        wx.grid.Grid.__init__(self, parent, size=size)
        self.dataset = dataset
        self.gridtable = DataGridTable(dataset)
        self.SetTable(self.gridtable, takeOwnership=True)
        self.EnableEditing(False)
        self.UseNativeColHeader(True)
        self.HideRowLabels()
        self.AutoSize()
        self.Bind(wx.grid.EVT_GRID_COL_SORT, self.OnSort)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnOpen)
        logger.info("Finished")

    def OnSort(self, event):
        logger = logging.getLogger(__name__+".DatasetDataGrid.OnSort")
        logger.info("Starting")
        col = event.GetCol()
        col_name = self.gridtable.GetColTupleValue(event.GetCol())
        if col == self.GetSortingColumn():
            if self.IsSortOrderAscending():
                #self.SetSortingColumn(col)
                self.gridtable.data_df.sort_values(by=[col_name], inplace=True)
            else:
                #self.SetSortingColumn(col, ascending=False)
                self.gridtable.data_df.sort_values(by=[col_name], ascending=False, inplace=True)
        else:
            self.SetSortingColumn(col)
            self.gridtable.data_df.sort_values(by=[col_name], inplace=True)
        logger.info("Finish")
            
    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".DatasetDataGrid.OnOpen")
        logger.info("Starting")
        col = event.GetCol()
        row = event.GetRow()
        col_name = self.GetColLabelValue(col)
        if col_name == "url":
            url = self.gridtable.GetValue(row, col)
            webbrowser.open_new_tab(url)
        else:
            #frame = wx.Dialog(self, title=col_name, size=(400, 400), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
            #frame_sizer = wx.BoxSizer()
            #panel = wx.ScrolledWindow(frame)
            #panel_sizer = wx.BoxSizer()

            row_data = self.gridtable.data_df.iloc[row]
            key = (row_data['data_source'], row_data['data_type'], row_data['id'])
            
            document = self.dataset.SetupDocument(key)
            main_frame = wx.GetApp().GetTopWindow()
            DocumentDialog(main_frame, document).Show()
        logger.info("Finish")

    def AutoSize(self):
        if self.GetNumberRows() > 0:
            max_size = self.GetSize().GetWidth()*0.98
            dc = wx.ScreenDC()
            font = self.GetLabelFont()
            dc.SetFont(font)
            
            url = self.gridtable.GetValue(0, 0)
            url_size = dc.GetTextExtent(url).GetWidth()
            url_label_size = dc.GetTextExtent("URL").GetWidth()
            self.SetColSize(0, max(url_size, url_label_size))
            max_size = max_size - max(url_size, url_label_size)

            date = self.gridtable.GetValue(0, 1)
            date_size = dc.GetTextExtent(date).GetWidth()
            date_label_size = dc.GetTextExtent("Created UTC").GetWidth()
            self.SetColSize(1, max(date_size, date_label_size))
            max_size = max_size - max(date_size, date_label_size)

            if self.dataset.grouping_field is not None:
                field = self.gridtable.GetValue(0, 2)
                field_size = dc.GetTextExtent(field).GetWidth()
                field_label_size = dc.GetTextExtent(str(("Grouping Field", self.dataset.grouping_field.key))).GetWidth()
                self.SetColSize(1, max(field_size, field_label_size))
                max_size = max_size - max(field_size, field_label_size)
                first_data_col = 3
            else:
                first_data_col = 2
            
            col_num = self.gridtable.GetNumberCols()
            if col_num > first_data_col:
                split_size = max_size / (col_num-first_data_col)
                for col in range(first_data_col, col_num):
                    self.SetColSize(col, int(split_size))

    def Update(self):
        logger = logging.getLogger(__name__+".DatasetDataGrid.Update")
        logger.info("Starting")
        self.gridtable.ResetView(self)
        self.AutoSize()
        for i in range(0, len(self.gridtable.col_names)):
            self.SetColLabelValue(i, self.gridtable.GetColLabelValue(i))
        self.ForceRefresh()
        logger.info("Finish")

class DocumentDialog(wx.Dialog):
    def __init__(self, parent, node, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DocumentDialog["+str(node.key)+"].__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=str(node.key), size=size, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        sizer = wx.BoxSizer()
        self.document_panel = DocumentPanel(self, node, size=self.GetSize())
        sizer.Add(self.document_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.info("Finished")

class DocumentPanel(wx.Panel):
    def __init__(self, parent, node, size):
        wx.Panel.__init__(self, parent, size=size)

        self.node = node

        label_font = wx.Font(Constants.LABEL_SIZE, Constants.LABEL_FAMILY, Constants.LABEL_STYLE, Constants.LABEL_WEIGHT, Constants.LABEL_UNDERLINE)

        frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(frame_sizer)

        frame_splitter = wx.SplitterWindow(self, style=wx.SP_BORDER)
        frame_sizer.Add(frame_splitter, 1, wx.EXPAND)

        top_frame_splitter = wx.SplitterWindow(frame_splitter, style=wx.SP_BORDER)

        data_panel = wx.ScrolledWindow(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL|wx.SUNKEN_BORDER)
        data_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        url = wx.adv.HyperlinkCtrl(data_panel, url=node.url, style=wx.ALIGN_LEFT)
        data_panel_sizer.Add(url, 0, wx.ALL, 5)

        field_ctrl = wx.TextCtrl(data_panel, value="", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.BORDER_NONE)
        data_panel_sizer.Add(field_ctrl, 1, wx.EXPAND, 5)
        for field in node.data_dict:
            #field_ctrl.AppendText(str(field)+"\n")
            #field_label.Wrap(self.GetSizer().GetWidth())
            #field_label.SetFont(label_font)
            #data_panel_sizer.Add(field_label, 0, wx.ALL, 5)
            if isinstance(node.data_dict[field], list):
                for entry in node.data_dict[field]:
                    field_ctrl.AppendText(str(entry)+'\n------------\n')
                    #field_value = infobar.AutoWrapStaticText(data_panel, label=str(entry)+'\n------------')
                    #field_value.Wrap(self.GetSizer().GetWidth())
                    #data_panel_sizer.Add(field_value, 0, wx.ALL, 5)
            else:
                field_ctrl.AppendText(str(node.data_dict[field])+'\n------------\n')
                #field_value = infobar.AutoWrapStaticText(data_panel, label=str(node.data_dict[field]))
                #field_value.Wrap(self.GetSizer().GetWidth())
                #data_panel_sizer.Add(field_value, 0, wx.ALL, 5)
        data_panel.SetSizer(data_panel_sizer)

        codes_panel = wx.Panel(top_frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        codes_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        main_frame = wx.GetApp().GetTopWindow()
        self.codes_model = CodesDataViews.ObjectCodesViewModel(main_frame.codes, self.node)
        self.codes_ctrl = CodesDataViews.CodesViewCtrl(codes_panel, self.codes_model)
        codes_panel_sizer.Add(self.codes_ctrl, 1, wx.EXPAND, 5)
        codes_panel.SetSizer(codes_panel_sizer)

        edit_panel = wx.Panel(frame_splitter, style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        edit_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        usefulness_sizer = wx.BoxSizer(wx.HORIZONTAL)
        usefulness_label = wx.StaticText(edit_panel, label="Usefullness: ", style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(usefulness_label, 0, wx.ALL, 5)
        self.usefulness_ctrl = wx.Choice(edit_panel, choices=["Unsure", "Useful", "Not Useful"], style=wx.ALIGN_LEFT)
        usefulness_sizer.Add(self.usefulness_ctrl, 0, wx.ALL, 5)
        self.usefulness_ctrl.Bind(wx.EVT_CHOICE, self.OnUpdateUsefulness)
        if self.node.usefulness_flag == None:
            self.usefulness_ctrl.Select(0)
        elif self.node.usefulness_flag:
            self.usefulness_ctrl.Select(1)
        elif not self.node.usefulness_flag:
            self.usefulness_ctrl.Select(2)
        edit_panel_sizer.Add(usefulness_sizer)
        
        #notes_label = wx.StaticText(edit_panel, label="Notes", style=wx.ALIGN_LEFT)
        #notes_label.SetFont(label_font)
        #edit_panel_sizer.Add(notes_label, 0, wx.ALL, 5)
        #self.notes_ctrl = wx.TextCtrl(edit_panel, value=node.notes, style=wx.TE_LEFT|wx.TE_MULTILINE)
        #self.notes_ctrl.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        #edit_panel_sizer.Add(self.notes_ctrl, 1, wx.EXPAND, 5)
        self.notes_panel = Notes.NotesPanel(edit_panel)
        self.notes_panel.SetNote(node.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)
        edit_panel_sizer.Add(self.notes_panel, 1, wx.EXPAND, 5)
        
        edit_panel.SetSizer(edit_panel_sizer)

        top_frame_splitter.SetMinimumPaneSize(20)
        top_frame_splitter.SplitVertically(data_panel, codes_panel)
        top_frame_splitter.SetSashPosition(int(self.GetSize().GetWidth()/2))

        frame_splitter.SetMinimumPaneSize(20)
        frame_splitter.SplitHorizontally(top_frame_splitter, edit_panel)
        frame_splitter.SetSashPosition(int(self.GetSize().GetHeight()/2))



        #initialize scrolling
        fontsz = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPixelSize()
        data_panel.SetScrollRate(fontsz.x, fontsz.y)
        data_panel.EnableScrolling(True, True)

        self.Layout()
    
    def OnUpdateUsefulness(self, event):
        choice = self.usefulness_ctrl.GetSelection()
        if choice == 0:
            self.node.usefulness_flag = None
        elif choice == 1:
            self.node.usefulness_flag = True
        elif choice == 2:
            self.node.usefulness_flag = False
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()

    def OnUpdateNotes(self, event):
        self.node.notes = self.notes_panel.GetNote()
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DocumentsUpdated()
    
    def DocumentUpdated(self):
        codes_model = self.codes_ctrl.GetModel()
        codes_model.Cleared()
        self.notes_panel.Unbind(wx.EVT_TEXT)
        self.notes_panel.SetNote(self.node.notes)
        self.notes_panel.Bind(wx.EVT_TEXT, self.OnUpdateNotes)

class DocumentListPanel(wx.Panel):
    def __init__(self, parent, dataset_key):
        logger = logging.getLogger(__name__+".DocumentListPanel["+str(dataset_key)+"].__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)

        sizer = wx.BoxSizer(wx.VERTICAL)

        controls_sizer = wx.BoxSizer()

        #TODO add text to GUIText
        actions_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.ACTIONS)
        actions_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        notsure_tool = actions_toolbar.AddTool(wx.ID_ANY, label="Not Sure", bitmap=wx.Bitmap(1, 1),
                                      shortHelp="Flags selected entries usefulness as not sure")
        actions_toolbar.Bind(wx.EVT_MENU, self.OnNotSure, notsure_tool)
        useful_tool = actions_toolbar.AddTool(wx.ID_ANY, label="Useful", bitmap=wx.Bitmap(1, 1),
                                      shortHelp="Flags selected entries usefulness as useful")
        actions_toolbar.Bind(wx.EVT_MENU, self.OnUseful, useful_tool)
        notuseful_tool = actions_toolbar.AddTool(wx.ID_ANY, label="Not Useful", bitmap=wx.Bitmap(1, 1),
                                         shortHelp="Flags selected entries usefulness as not useful")
        actions_toolbar.Bind(wx.EVT_MENU, self.OnNotUseful, notuseful_tool)
        actions_toolbar.Realize()
        actions_sizer.Add(actions_toolbar)
        controls_sizer.Add(actions_sizer, 0, wx.ALL, 5)

        #TODO add text to GUIText
        view_sizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, label=GUIText.VIEW)
        view_toolbar = wx.ToolBar(self, style=wx.TB_DEFAULT_STYLE|wx.TB_TEXT|wx.TB_NOICONS)
        self.notsure_toggle = view_toolbar.AddTool(wx.ID_ANY, label="Show Not Sure", bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_CHECK)
        view_toolbar.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.notsure_toggle)
        self.useful_toggle = view_toolbar.AddTool(wx.ID_ANY, label="Show Useful", bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_CHECK)
        view_toolbar.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.useful_toggle)
        self.notuseful_toggle = view_toolbar.AddTool(wx.ID_ANY, label="Show Not Useful", bitmap=wx.Bitmap(1, 1), kind=wx.ITEM_CHECK)
        view_toolbar.Bind(wx.EVT_MENU, self.OnToggleShowUsefulness, self.notuseful_toggle)
        view_toolbar.Realize()
        view_sizer.Add(view_toolbar)
        controls_sizer.Add(view_sizer, 0, wx.ALL, 5)

        sizer.Add(controls_sizer, 0, wx.ALL, 5)
        
        #single dataset mode
        main_frame = wx.GetApp().GetTopWindow()
        self.documents_model = DatasetsDataViews.DocumentViewModel(main_frame.datasets[dataset_key])
        self.documents_ctrl = DatasetsDataViews.DocumentViewCtrl(self, self.documents_model)
        self.documents_model.Cleared()

        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
        columns = self.documents_ctrl.GetColumns()
        for column in reversed(columns):
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        sizer.Add(self.documents_ctrl, 1, wx.EXPAND)

        self.SetSizer(sizer)

        logger.info("Finished")
    
    def OnNotSure(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotSure")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = None
                self.documents_model.ItemChanged(item)
        logger.info("Finished")

    def OnUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = True
                self.documents_model.ItemChanged(item)
        logger.info("Finished")

    def OnNotUseful(self, event):
        logger = logging.getLogger(__name__+".DocumentListPanel.OnNotUseful")
        logger.info("Starting")
        for item in self.documents_ctrl.GetSelections():
            node = self.documents_model.ItemToObject(item)
            if hasattr(node, "usefulness_flag"):
                node.usefulness_flag = False
                self.documents_model.ItemChanged(item)
        logger.info("Finished")
    
    def OnToggleShowUsefulness(self, event):

        notsure_toggled = self.notsure_toggle.IsToggled()
        if not notsure_toggled:
            if None in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(None)
        elif notsure_toggled:
            if None not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(None)
        
        useful_toggled = self.useful_toggle.IsToggled()
        if not useful_toggled:
            if True in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(True)
        elif useful_toggled:
            if True not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(True)
        
        notuseful_toggled = self.notuseful_toggle.IsToggled()
        if not notuseful_toggled:
            if False in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.remove(False)
        elif notuseful_toggled:
            if False not in self.documents_model.usefulness_filter:
                self.documents_model.usefulness_filter.append(False)
        self.documents_model.Cleared()
        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
            subchildren = []
            self.documents_model.GetChildren(child, subchildren)
            for subchild in subchildren:
                self.documents_ctrl.Expand(subchild)
            

    def DatasetsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".DocumentListPanel.DatasetsUpdated")
        logger.info("Starting")
        self.documents_ctrl.UpdateColumns()
        self.documents_model.Cleared()
        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
            subchildren = []
            self.documents_model.GetChildren(child, subchildren)
            for subchild in subchildren:
                self.documents_ctrl.Expand(subchild)
        logger.info("Finished")

    def DocumentsUpdated(self):
        '''Triggered by any function from this module or sub modules.
        updates the datasets to perform a global refresh'''
        logger = logging.getLogger(__name__+".DocumentListPanel.DocumentsUpdated")
        logger.info("Starting")
        self.documents_model.Cleared()
        children = []
        self.documents_model.GetChildren(None, children)
        for child in children:
            self.documents_ctrl.Expand(child)
            subchildren = []
            self.documents_model.GetChildren(child, subchildren)
            for subchild in subchildren:
                self.documents_ctrl.Expand(subchild)
        logger.info("Finished")

    #Module Control commands
    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".DocumentListPanel.Load")
        logger.info("Starting")
        logger.info("Finished")

    def Save(self):
        logger = logging.getLogger(__name__+".DocumentListPanel.Save")
        logger.info("Starting")
        saved_data = {}
        logger.info("Finished")
        return saved_data