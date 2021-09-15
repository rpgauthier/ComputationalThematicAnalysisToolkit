import logging
from random import sample
from re import search
import webbrowser
from datetime import datetime

import pandas as pd

import wx
import wx.grid
import wx.dataview as dv

from Common.GUIText import Datasets as GUIText
from Common.GUIText import Filtering as FilteringGUIText
import Common.Constants as Constants
import Common.Objects.Datasets as Datasets
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Common.Objects.Samples as Samples
import Common.Objects.GUIs.Codes as CodesGUIs

# This model acts as a bridge between the DatasetsViewCtrl and the dataset to
# organizes it hierarchically as a collection of Datasets.
# This model provides these data columns:
#     0. Name:   string
#     1. Source:  string
#     2. Type:   string
#     3. Grouping Field:    string
#     4. Number of documents: int
#     5. Created datetime
class DatasetsViewModel(dv.PyDataViewModel):
    def __init__(self, data):
        dv.PyDataViewModel.__init__(self)
        self.data = data
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 6

    def GetColumnType(self, col):
        return "string"

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for dataset in self.data:
                children.append(self.ObjectToItem(dataset))
            return len(self.data)
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Datasets.Dataset):
            for chosen_field_name in node.chosen_fields:
                children.append(self.ObjectToItem(node.chosen_fields[chosen_field_name]))
            return len(children)
        return 0

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if node.parent == None:
            return dv.NullDataViewItem
        else:
            return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Dataset):
            mapper = { 0 : node.name,
                       1 : node.dataset_source,
                       2 : node.dataset_type,
                       3 : len(node.data),
                       4 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S")
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Field):
            mapper = { 0 : node.key,
                       1 : "",
                       2 : "",
                       3 : "",
                       4 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S")
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        '''retrieves custom attributes for item'''
        node = self.ItemToObject(item)
        if col == 0:
            attr.SetColour('blue')
            attr.SetBold(True)
            return True
        return False

    def HasContainerColumns(self, item):
        if not item:
            return False
        return True

    def IsContainer(self, item):
        ''' Return False for Field, True otherwise for this model.'''
        # The hidden root is a container
        if not item:
            return True
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Field):
            return False
        # but everything elseare not
        return True

    def SetValue(self, value, item, col):
        '''only allowing updating of Dataset names as rest is connected to data being retrieved'''
        node = self.ItemToObject(item)
        if col == 0:
            if isinstance(node, Datasets.Dataset):
                main_frame = wx.GetApp().GetTopWindow()
                if value != node.name:
                    if value not in main_frame.datasets:
                        node.name = value
                        main_frame.DatasetsUpdated()
                    else:
                        wx.MessageBox(GUIText.NAME_EXISTS_ERROR,
                                    GUIText.ERROR, wx.OK | wx.ICON_ERROR)
        return True

#This view enables displaying datasets and how they are grouped
class DatasetsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model):
        dv.DataViewCtrl.__init__(self, parent, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES)

        self.AssociateModel(model)
        #model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column0 = dv.DataViewColumn(GUIText.NAME, editabletext_renderer, 0,
                               flags=dv.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.SOURCE, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_renderer = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(GUIText.TYPE, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column4 = dv.DataViewColumn(GUIText.DOCUMENT_NUM, int_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column4)
        text_renderer = dv.DataViewTextRenderer()
        column5 = dv.DataViewColumn(GUIText.RETRIEVED_ON, text_renderer, 4, align=wx.ALIGN_LEFT)
        self.AppendColumn(column5)

        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

        self.Expander(None)

    def Expander(self, item):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)

    def OnShowPopup(self, event):
        menu = wx.Menu()
        menu.Append(1, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.OnCopyItems)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            dataset = model.GetValue(item, 0)
            source = model.GetValue(item, 1)
            datasettype = model.GetValue(item, 2)
            selected_items.append('\t'.join([dataset, source, datasettype]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

#to make only one needed for each entry in main_frame.datasets regardless of which type of dataset is used
class DatasetsDataGridTable(wx.grid.GridTableBase):
    def __init__(self, dataset):
        wx.grid.GridTableBase.__init__(self)
        self.dataset = dataset
        self.data_df = pd.DataFrame(self.dataset.data.values())
        self.metadata_column_names = []
        self.metadata_col_types = []
        self.data_column_names = []
        
        self.GetColNames()

        if not hasattr(self.dataset, 'metadata_fields'):
            self.data_df['created_utc']= pd.to_datetime(self.data_df['created_utc'], unit='s', utc=True).dt.strftime(Constants.DATETIME_FORMAT)
        else:
            for col_num in range(0, len(self.metadata_column_names)):
                if self.metadata_col_types[col_num] == 'UTC-timestamp':
                    try:
                        self.data_df[self.metadata_column_names[col_num]] = pd.to_datetime(self.data_df[self.metadata_column_names[col_num]], unit='s', utc=True).dt.strftime(Constants.DATETIME_FORMAT)
                    except ValueError:
                        def ListConvert(list_):
                            value_list = []
                            if isinstance(list_, list):
                                for value in list_:
                                    value_list.append(str(datetime.utcfromtimestamp(value).strftime(Constants.DATETIME_FORMAT))+'UTC')
                            return value_list
                        self.data_df[self.metadata_column_names[col_num]] = self.data_df[self.metadata_column_names[col_num]].apply(ListConvert)
        
        self._rows = len(self.data_df)
        self._cols = 1+len(self.metadata_column_names)+len(self.data_column_names)

    def GetColNames(self):
        self.metadata_column_names = []
        self.metadata_col_types = []
        self.data_column_names = []
        self.data_col_types = []

        if not hasattr(self.dataset, 'metadata_fields'):
            #CODE for datasets created before metadata enhancements
            if self.dataset.dataset_source != 'CSV':
                self.data_column_names.append(("", "url"))
                self.data_col_types.append("url") 
            else:
                self.data_column_names.append(("", "id"))
                self.data_col_types.append("string")
            self.data_column_names.append(("", 'created_utc'))
            self.data_col_types.append("UTC-timestamp")
        else:
            #CODE for datasets created after metadata enhancements
            for field_name in self.dataset.metadata_fields:
                self.metadata_column_names.append(field_name)
                self.metadata_col_types.append(self.dataset.metadata_fields[field_name].fieldtype)
    
        #CODE to collect approriate fields based on what has been chosen to be included and/or merged
        for field_name in self.dataset.chosen_fields:
            if field_name not in self.metadata_column_names and field_name not in self.data_column_names:
                self.data_column_names.append(field_name)
                self.data_col_types.append(self.dataset.chosen_fields[field_name].fieldtype)

    def GetColLabelValue(self, col):
        name = ""
        if col == 0:
            name = ""
        elif 0 < col < len(self.metadata_column_names)+1:
            col = col-1
            name = self.metadata_column_names[col]
        else:
            col = col - (len(self.metadata_column_names)+1)
            if self.data_column_names[col][0] == "":
                name = self.data_column_names[col][1]
            else:
                if isinstance(self.data_column_names[col], str):
                    name = self.data_column_names[col]
                else:
                    name = self.data_column_names[col][1]
        return str(name)
    
    def GetColTupleValue(self, col):
        if col == 0:
            return ""
        elif 0 < col < len(self.metadata_column_names)+1:
            col = col-1
            return self.metadata_column_names[col]
        else:
            col = col - (len(self.metadata_column_names)+1)
            if self.data_column_names[col][0] == "":
                return self.data_column_names[col][1]
            else:
                if isinstance(self.data_column_names[col], str):
                    return self.data_column_names[col]
                else:
                    return self.data_column_names[col][1]

    def GetNumberRows(self):
        """Return the number of rows in the grid"""
        return len(self.data_df)

    def GetNumberCols(self):
        """Return the number of columns in the grid"""
        return 1+len(self.metadata_column_names)+len(self.data_column_names)

    def GetTypeName(self, row, col):
        """Return the name of the data type of the value in the cell"""
        if col == 0:
            field_type = "boolean"
        elif 0 < col < len(self.metadata_column_names)+1:
            col = col-1
            field_type = self.metadata_col_types[col]
        else:
            col = col - (len(self.metadata_column_names)+1)
            field_type = self.data_col_types[col]
        if field_type == 'integer':
            grid_field_type = wx.grid.GRID_VALUE_LONG
        elif field_type == 'UTC-timestamp':
            grid_field_type = wx.grid.GRID_VALUE_TEXT
        elif field_type == 'boolean':
            grid_field_type = wx.grid.GRID_VALUE_BOOL
        else:
            grid_field_type = wx.grid.GRID_VALUE_TEXT
        return grid_field_type 

    def GetValue(self, row, col):
        """Return the value of a cell"""
        data = ""
        if col == 0:
            row_data = self.data_df.iloc[row]
            key = (row_data['data_source'], row_data['data_type'], row_data['id'])
            if key in self.dataset.selected_documents:
                data = '1'
        elif col < len(self.metadata_column_names)+1:
            col = col-1
            col_name = self.metadata_column_names[col]
            df_row = self.data_df.iloc[row]
            if self.metadata_col_types[col] == 'url':
                segmented_url = df_row[col_name].split("/")
                data = segmented_url[len(segmented_url)-1]
            else:
                data = df_row[col_name]
                if isinstance(data, list):
                    first_entry = ""
                    for entry in data:
                        if entry != "":
                            first_entry = ' '.join(entry.split())
                            break
                    first_entry = str(first_entry)
                    if len(data) > 1:
                        data = first_entry.split('. ')[0] + "..."
                    else:
                        if len(first_entry.split('. ')) > 1:
                            data = first_entry.split('. ')[0] + "..."
                        else:
                            data = first_entry
        else:
            col = col - (len(self.metadata_column_names)+1)
            col_name = self.data_column_names[col]
            if isinstance(col_name, tuple):
                col_name = col_name[1]
            df_row = self.data_df.iloc[row]
            #TODO rework to handle lists of dates, ints and urls
            if self.data_col_types[col] == 'url':
                segmented_url = df_row[col_name].split("/")
                data = segmented_url[len(segmented_url)-1]
            else:
                data = df_row[col_name]
                if isinstance(data, list):
                    first_entry = ""
                    for entry in data:
                        if entry != "":
                            if self.data_col_types[col] == 'string':
                                first_entry = ' '.join(entry.split())
                            elif self.data_col_types[col] == 'UTC-timestamp':
                                first_entry = str(datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT))+'UTC'
                            else:
                                first_entry = str(entry)
                            break
                    if len(data) > 1:
                        data = first_entry.split('. ')[0] + "..."
                    else:
                        if len(first_entry.split('. ')) > 1:
                            data = first_entry.split('. ')[0] + "..."
                        else:
                            data = first_entry
        type_name = self.GetTypeName(row, col)
        if type_name == wx.grid.wx.grid.GRID_VALUE_TEXT:
            return str(data)
        else:
            return data

    def SetValue(self, row, col, value):
        """Set the value of a cell"""
        if col == 0:
            row_data = self.data_df.iloc[row]
            key = (row_data['data_source'], row_data['data_type'], row_data['id'])
            if key not in self.dataset.selected_documents:
                self.dataset.SetupDocument(key)
                self.dataset.selected_documents.append(key)
                self.dataset.last_changed_dt = datetime.now()
            else:
                self.dataset.selected_documents.remove(key)
                self.dataset.last_changed_dt = datetime.now()
            main_frame = wx.GetApp().GetTopWindow()
            main_frame.DocumentsUpdated()
        else:
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
        h,w = grid.GetSize()
        grid.SetSize((h+1, w))
        grid.SetSize((h, w))
        grid.ForceRefresh()
        self.UpdateValues(grid)
    
    def UpdateValues(self, grid):
        """Update all displayed values without changing the grid size"""
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

class DatasetsDataGrid(wx.grid.Grid):
    def __init__(self, parent, dataset, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".DatasetsDataGrid.__init__")
        logger.info("Starting")
        wx.grid.Grid.__init__(self, parent, size=size)
        self.dataset = dataset
        self.gridtable = DatasetsDataGridTable(dataset)
        self.SetTable(self.gridtable, takeOwnership=True)
        self.EnableEditing(False)
        self.UseNativeColHeader(True)

        attr = wx.grid.GridCellAttr()
        attr.SetReadOnly(False)
        attr.SetRenderer(wx.grid.GridCellBoolRenderer())
        attr.SetEditor(wx.grid.GridCellBoolEditor())
        self.SetColAttr(0, attr)
        
        for col_num in range(1, self.gridtable.GetColsCount()):
            attr = wx.grid.GridCellAttr()
            attr.SetReadOnly(True)
            self.SetColAttr(col_num, attr)
        

        self.HideRowLabels()
        self.AutoSize()
        self.Bind(wx.grid.EVT_GRID_COL_SORT, self.OnSort)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.OnMouse)
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnOpen)
        logger.info("Finished")
    
    def OnSort(self, event):
        logger = logging.getLogger(__name__+".DatasetsDataGrid.OnSort")
        logger.info("Starting")
        col = event.GetCol()
        col_name = self.gridtable.GetColTupleValue(event.GetCol())
        if col != 0:
            if col == self.GetSortingColumn():
                if self.IsSortOrderAscending():
                    self.gridtable.data_df.sort_values(by=[col_name], ascending=True, inplace=True, key=lambda x: x.str.lower() if x.dtype == object else x)
                else:
                    self.gridtable.data_df.sort_values(by=[col_name], ascending=False, inplace=True, key=lambda x: x.str.lower() if x.dtype == object else x)
            else:
                self.SetSortingColumn(col)
                self.gridtable.data_df.sort_values(by=[col_name], inplace=True, key=lambda x: x.str.lower() if x.dtype == object else x)
        logger.info("Finish")

    def OnMouse(self, event):
        col = event.GetCol()
        row = event.GetRow()
        if col == 0:
            self.gridtable.SetValue(row, col, "")
            self.gridtable.ResetView(self)
        event.Skip()
            
    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".DatasetsDataGrid.OnOpen")
        logger.info("Starting")
        col = event.GetCol()
        row = event.GetRow()
        col_name = self.GetColLabelValue(col)
        if col > 0 and col <= len(self.gridtable.metadata_col_types):
            col_type = self.gridtable.metadata_col_types[col-1]
        elif col > len(self.gridtable.metadata_col_types):
            col_type = self.gridtable.data_col_types[col-(len(self.gridtable.metadata_col_types)+1)]
        else:
            col_type = 'boolean'
        if col_type == "url":
            row_data = self.gridtable.data_df.iloc[row]
            url = row_data[col_name]
            webbrowser.open_new_tab(url)
        else:
            row_data = self.gridtable.data_df.iloc[row]
            key = (row_data['data_source'], row_data['data_type'], row_data['id'])
            
            document = self.dataset.SetupDocument(key)
            main_frame = wx.GetApp().GetTopWindow()
            CodesGUIs.DocumentDialog(main_frame, document).Show()
        logger.info("Finish")

    def AutoSize(self):
        if self.GetNumberRows() > 0:
            max_size = self.GetSize().GetWidth()*0.98
            dc = wx.ScreenDC()
            font = self.GetLabelFont()
            dc.SetFont(font)

            content_size = dc.GetTextExtent(str("True")).GetWidth()
            self.SetColSize(0, content_size)
            max_size = max_size - content_size

            col_count = 1
            for col_name in self.gridtable.metadata_column_names:
                col_type = self.gridtable.metadata_col_types[col_count-1]
                if col_type == 'url':
                    attr = wx.grid.GridCellAttr()
                    attr.SetTextColour(wx.Colour(6,69,173))
                    attr.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL, underline=True))
                    self.SetColAttr(col_count, attr)

                if col_type == 'string':
                    field_length = self.gridtable.data_df[col_name].astype(str).map(len)
                    contents = self.gridtable.data_df.loc[field_length.argmax(), col_name]
                else:
                    contents = self.gridtable.GetValue(0, col_count)
                contents_size = dc.GetTextExtent(str(contents)).GetWidth()
                label_size = dc.GetTextExtent(col_name).GetWidth()
                self.SetColSize(col_count, max(contents_size, label_size))
                max_size = max_size - max(contents_size, label_size)
                col_count = col_count + 1
            
            data_col_count = len(self.gridtable.data_column_names)
            if data_col_count > 0:
                if max_size > 200:
                    split_size = max_size / (data_col_count)
                else:
                    split_size = 200 / (data_col_count)
                for col_num in range(col_count, col_count + data_col_count):
                    self.SetColSize(col_num, int(split_size))

    def Search(self, value):
        self.gridtable.data_df = pd.DataFrame(self.gridtable.dataset.data.values())
        if not hasattr(self.dataset, 'metadata_fields'):
            self.data_df['created_utc']= pd.to_datetime(self.gridtable.data_df['created_utc'], unit='s', utc=True).dt.strftime(Constants.DATETIME_FORMAT)
        else:
            for col_num in range(0, len(self.gridtable.metadata_column_names)):
                if self.gridtable.metadata_col_types[col_num] == 'UTC-timestamp':
                    self.gridtable.data_df[self.gridtable.metadata_column_names[col_num]]= pd.to_datetime(self.gridtable.data_df[self.gridtable.metadata_column_names[col_num]], unit='s', utc=True).dt.strftime(Constants.DATETIME_FORMAT)
        
        if value != "":
            self.gridtable.data_df = self.gridtable.data_df[self.gridtable.data_df.applymap(lambda x: value in str(x)).any(1)]
            self.gridtable.data_df.reset_index(inplace=True)
        self.gridtable.ResetView(self)
        self.ForceRefresh()
        self.AutoSize()

# This model acts as a bridge between the FieldViewCtrl and the dataset and
# organizes it hierarchically using Dataset, Field objects.
# it provides data for displaying avaliable fields for a particular Dataset
# This model provides these data columns:
#   0. Name:   string
#   1. Source:  string
#   2. Type:   string
#   3. Field:    string
#   4. Description: string   
class AvaliableFieldsViewModel(dv.PyDataViewModel):
    def __init__(self, dataset):
        dv.PyDataViewModel.__init__(self)
        self.dataset = dataset
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 5

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for field_name in self.dataset.avaliable_fields:
                children.append(self.ObjectToItem(self.dataset.avaliable_fields[field_name]))
            return len(children)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        # everything else is not
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Field):
            return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Field):
            mapper = { 0 : node.parent.name,
                       1 : node.parent.dataset_source,
                       2 : node.parent.dataset_type,
                       3 : node.key,
                       4 : node.desc
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

# This model acts as a bridge between the DataViewCtrl and the dataset and
# organizes it hierarchically using Dataset and Field objects.
# It controls displaying chosen and merged fields for a particular dataset
# This model provides these data columns:
#   0. Name:   string
#   1. Source:  string
#   2. Type:   string
#   3. Field:    string
#   4. Description: string
class ChosenFieldsViewModel(dv.PyDataViewModel):
    def __init__(self, fields):
        dv.PyDataViewModel.__init__(self)
        self.fields = fields
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 5

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for field in self.fields:
                children.append(self.ObjectToItem(self.fields[field]))
            return len(children)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        # but everything else is not
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Field):
            return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Field):
            mapper = { 0 : node.dataset.name,
                       1 : node.dataset.dataset_source,
                       2 : node.dataset.dataset_type,
                       3 : node.key,
                       4 : node.desc
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        '''retrieves custom attributes for item'''
        node = self.ItemToObject(item)
        return False

#this view enables displaying of fields for different datasets
class FieldsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.AssociateModel(model)
        #model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)        
        column0 = dv.DataViewColumn(GUIText.NAME, editabletext_renderer, 0,
                                    flags=dv.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.SOURCE, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_renderer = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(GUIText.TYPE, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        text_renderer = dv.DataViewTextRenderer()
        column3 = dv.DataViewColumn(GUIText.FIELD, text_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)
        text_renderer = dv.DataViewTextRenderer()
        column4 = dv.DataViewColumn(GUIText.DESCRIPTION, text_renderer, 4, align=wx.ALIGN_LEFT)
        self.AppendColumn(column4)

        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

        self.Expander(None)

    def Expander(self, item):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)

    def OnCopyItems(self, event):
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            name = model.GetValue(item, 0)
            source = model.GetValue(item, 1)
            datasettype = model.GetValue(item, 2)
            field = model.GetValue(item, 3)
            description = model.GetValue(item, 3)
            selected_items.append('\t'.join([name, source, datasettype, field, description]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

class FilterRuleDataViewListCtrl(dv.DataViewListCtrl):
    '''For rendering nlp filter rules'''
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".FilterRuleDataViewListCtrl.__init__")
        logger.info("Starting")
        dv.DataViewListCtrl.__init__(self, parent, style=dv.DV_ROW_LINES|dv.DV_MULTIPLE)

        int_render = dv.DataViewTextRenderer(varianttype="long")
        column0 = dv.DataViewColumn(FilteringGUIText.FILTERS_RULES_STEP, int_render, 0,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_RIGHT)
        self.AppendColumn(column0)
        text_render = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(FilteringGUIText.FILTERS_FIELDS, text_render, 1,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_render = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(FilteringGUIText.FILTERS_WORDS, text_render, 2,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        text_render = dv.DataViewTextRenderer()
        column3 = dv.DataViewColumn(FilteringGUIText.FILTERS_POS, text_render, 3,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)
        text_render = dv.DataViewTextRenderer()
        column4 = dv.DataViewColumn(FilteringGUIText.FILTERS_RULES_ACTION, text_render, 4,
                                    flags=wx.COL_SORTABLE|wx.COL_RESIZABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column4)

        columns = self.GetColumns()
        for column in reversed(columns):
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        copy_id = wx.ID_ANY
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=copy_id)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), copy_id )])
        self.SetAcceleratorTable(accel_tbl)

        logger.info("Finished")

    def OnShowPopup(self, event):
        '''create popup menu with options that can be performed on the list'''
        logger = logging.getLogger(__name__+".FilterRuleDataViewListCtrl.OnShowPopup")
        logger.info("Starting")
        menu = wx.Menu()
        menu.Append(1, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.OnCopyItems)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        '''copies what is selected in the list to the user's clipboard'''
        logger = logging.getLogger(__name__+".FilterRuleDataViewListCtrl.OnCopyItems")
        logger.info("Starting")
        selectedItems = []

        for item in self.GetSelections():
            row = self.ItemToRow(item)
            step = self.GetValue(row, 0)
            field = self.GetValue(row, 1)
            word = self.GetValue(row, 2)
            pos = self.GetValue(row, 3)
            action = self.GetValue(row, 4)
            selectedItems.append('\t'.join([word,
                                            pos,
                                            action
                                            ]).strip())

        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selectedItems))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()