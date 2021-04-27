import wx
import wx.dataview as dv

from Common.GUIText import Datasets as GUIText
import Common.Objects.Datasets as Datasets

# This model acts as a bridge between the DatasetsViewCtrl and the dataset to
# organizes it hierarchically as a collection of Datasets and GroupedDatasets.
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
        if isinstance(node, Datasets.GroupedDataset):
            for dataset_key in node.datasets:
                children.append(self.ObjectToItem(node.datasets[dataset_key]))
            for merged_field_name in node.merged_fields:
                children.append(self.ObjectToItem(node.merged_fields[merged_field_name]))
            return len(children)
        elif isinstance(node, Datasets.Dataset):
            for chosen_field_name in node.chosen_fields:
                children.append(self.ObjectToItem(node.chosen_fields[chosen_field_name]))
            for merged_field_name in node.merged_fields:
                children.append(self.ObjectToItem(node.merged_fields[merged_field_name]))
            return len(children)
        elif isinstance(node, Datasets.MergedField):
            for chosen_field_name in node.chosen_fields:
                children.append(self.ObjectToItem(node.chosen_fields[chosen_field_name]))
            return len(children)
        return 0

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            return dv.NullDataViewItem
        else:
            if node.parent == None:
                return dv.NullDataViewItem
            else:
                return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            mapper = { 0 : node.name,
                       1 : "",
                       2 : "",
                       3 : "",
                       4 : len(node.metadata),
                       5 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S")
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Dataset) and node.grouping_field is None:
            mapper = { 0 : node.name,
                       1 : node.dataset_source,
                       2 : node.dataset_type,
                       3 : "",
                       4 : len(node.data),
                       5 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S")
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Dataset) and node.grouping_field is not None:
            mapper = { 0 : node.name,
                       1 : node.dataset_source,
                       2 : node.dataset_type,
                       3 : node.grouping_field.key,
                       4 : len(node.data),
                       5 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S")
                       }
            return mapper[col]
        elif isinstance(node, Datasets.MergedField):
            mapper = { 0 : node.key,
                       1 : "",
                       2 : "",
                       3 : "",
                       4 : "",
                       5 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S")
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Field):
            mapper = { 0 : node.key,
                       1 : "",
                       2 : "",
                       3 : "",
                       4 : "",
                       5 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S")
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
        ''' Return True for GroupedDataset, False otherwise for this model.'''
        # The hidden root is a container
        if not item:
            return True
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Field):
            return False
        # but everything elseare not
        return True

    def SetValue(self, value, item, col):
        '''only allowing updating of GroupedDataset and Dataset names as rest is connected to data being retrieved'''
        node = self.ItemToObject(item)
        if col == 0:
            if isinstance(node, Datasets.GroupedDataset) or isinstance(node, Datasets.Dataset):
                node.name = value
        return True

#This view enables displaying datasets and how they are grouped
class DatasetsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model):
        dv.DataViewCtrl.__init__(self, parent, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES)

        self.AssociateModel(model)
        #model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        text_renderer = dv.DataViewTextRenderer()
        int_renderer = dv.DataViewTextRenderer(varianttype="long")

        column0 = dv.DataViewColumn(GUIText.NAME, editabletext_renderer, 0,
                               flags=dv.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        column1 = dv.DataViewColumn(GUIText.SOURCE, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column2 = dv.DataViewColumn(GUIText.TYPE, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        column3 = dv.DataViewColumn(GUIText.GROUPING_FIELD, text_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)
        column4 = dv.DataViewColumn(GUIText.DOCUMENT_NUM, int_renderer, 4, align=wx.ALIGN_LEFT)
        self.AppendColumn(column4)
        column5 = dv.DataViewColumn(GUIText.RETRIEVED_ON, text_renderer, 5, align=wx.ALIGN_LEFT)
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
            grouping_field = model.GetValue(item, 3)
            selected_items.append('\t'.join([dataset, source, datasettype, grouping_field]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()


# This model acts as a bridge between the FieldViewCtrl and the dataset and
# organizes it hierarchically using GroupedDataset, Dataset, Field objects.
# it provides data for displaying avaliable fields for a particular Dataset
# This model provides these data columns:
#   0. Name:   string
#   1. Source:  string
#   2. Type:   string
#   3. Field:    string
#   4. Description: string   
class AvaliableFieldsViewModel(dv.PyDataViewModel):
    def __init__(self, data):
        dv.PyDataViewModel.__init__(self)
        self.data = data
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 5

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
        if isinstance(node, Datasets.GroupedDataset):
            for dataset_key in node.datasets:
                children.append(self.ObjectToItem(node.datasets[dataset_key]))
            return len(node.datasets)
        if isinstance(node, Datasets.Dataset):
            for field_name in node.avaliable_fields:
                children.append(self.ObjectToItem(node.avaliable_fields[field_name]))
            return len(node.avaliable_fields)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            return True
        if isinstance(node, Datasets.Dataset):
            return True
        # but everything elseare not
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Dataset):
            return True
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            return dv.NullDataViewItem
        else:
            if node.parent == None:
                return dv.NullDataViewItem
            else:
                return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            mapper = { 0 : node.name,
                       1 : "",
                       2 : "",
                       3 : "",
                       4 : "" 
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Dataset):
            mapper = { 0 : node.name,
                       1 : node.dataset_source,
                       2 : node.dataset_type,
                       3 : "",
                       4 : ""
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Field):
            mapper = { 0 : node.parent.name,
                       1 : node.parent.dataset_source,
                       2 : node.parent.dataset_type,
                       3 : node.key,
                       4 : node.desc
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        '''retrieves custom attributes for item'''
        return False

    def SetValue(self, value, item, col):
        '''do not allowing updating contents through the ctrls'''
        return True

# This model acts as a bridge between the DataViewCtrl and the dataset and
# organizes it hierarchically using GroupedDataset, Dataset, MergedField, Field objects.
# It controls displaying chosen and merged fields for a particular dataset
# This model provides these data columns:
#   0. Name:   string
#   1. Source:  string
#   2. Type:   string
#   3. Field:    string
#   4. Description: string
class ChosenFieldsViewModel(dv.PyDataViewModel):
    def __init__(self, data):
        dv.PyDataViewModel.__init__(self)
        self.data = data
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 5

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
        if isinstance(node, Datasets.GroupedDataset):
            for dataset in node.datasets:
                children.append(self.ObjectToItem(node.datasets[dataset]))
            for merged_fields in node.merged_fields:
                children.append(self.ObjectToItem(node.merged_fields[merged_fields]))
            return len(node.datasets) + len(node.merged_fields)
        elif isinstance(node, Datasets.Dataset):
            for field in node.chosen_fields:
                children.append(self.ObjectToItem(node.chosen_fields[field]))
            for merged_field in node.merged_fields:
                children.append(self.ObjectToItem(node.merged_fields[merged_field]))
            return len(node.chosen_fields) + len(node.merged_fields)
        elif isinstance(node, Datasets.MergedField):
            for field in node.chosen_fields:
                children.append(self.ObjectToItem(node.chosen_fields[field]))
            return len(node.chosen_fields)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            return True
        if isinstance(node, Datasets.Dataset):
            return True
        if isinstance(node, Datasets.MergedField):
            return True
        # but everything elseare not
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Dataset):
            return True
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            return dv.NullDataViewItem
        else:
            if node.parent == None:
                return dv.NullDataViewItem
            else:
                return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            mapper = { 0 : node.name,
                       1 : "",
                       2 : "",
                       3 : "",
                       4 : "" 
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Dataset):
            mapper = { 0 : node.name,
                       1 : node.dataset_source,
                       2 : node.dataset_type,
                       3 : "",
                       4 : ""
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Field):
            mapper = { 0 : node.dataset.name,
                       1 : node.dataset.dataset_source,
                       2 : node.dataset.dataset_type,
                       3 : node.key,
                       4 : node.desc
                       }
            return mapper[col]
        elif isinstance(node, Datasets.MergedField):
            mapper = { 0 : node.key,
                       1 : '',
                       2 : '',
                       3 : '',
                       4 : ''
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        '''retrieves custom attributes for item'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.MergedField) and col == 0:
            attr.SetColour('blue')
            attr.SetBold(True)
            return True
        return False

    def SetValue(self, value, item, col):
        '''only allowing updating of MergedField names'''
        node = self.ItemToObject(item)
        if col == 0:
            if isinstance(node, Datasets.MergedField):
                node.key = value
        return True

#this view enables displaying of fields for different datasets
class FieldsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.AssociateModel(model)
        #model.DecRef()

        text_renderer = dv.DataViewTextRenderer()
        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
                
        column0 = dv.DataViewColumn(GUIText.NAME, editabletext_renderer, 0,
                                    flags=dv.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        column1 = dv.DataViewColumn(GUIText.SOURCE, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column2 = dv.DataViewColumn(GUIText.TYPE, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        column3 = dv.DataViewColumn(GUIText.FIELD, text_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)
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


# This model acts as a bridge between the DocumentViewCtrl and the datasets to
# organizes it hierarchically.
# This model provides these data columns:
#     0. ID:   string
#     1. Notes: string
#     2. Data:    string
class DocumentViewModel(dv.PyDataViewModel):
    def __init__(self, dataset_data):
        dv.PyDataViewModel.__init__(self)
        self.dataset_data = dataset_data
        self.UseWeakRefs(True)

        self.usefulness_filter = []
        self.notes_contain_filter = ""

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for key in self.dataset_data:
                node = self.dataset_data[key]
                children.append(self.ObjectToItem(node))
            return len(children)
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Datasets.GroupedDataset):
            for key in node.grouped_documents:
                include = True
                if self.notes_contain_filter != "":
                    if self.notes_contain_filter not in node.grouped_documents[key].notes:
                        include = False
                if len(self.usefulness_filter) > 0:
                    if node.grouped_documents[key].usefulness_flag not in self.usefulness_filter:
                        include = False
                if include:
                    children.append(self.ObjectToItem(node.grouped_documents[key]))
            for key in node.datasets:
                children.append(self.ObjectToItem(node.datasets[key]))
        elif isinstance(node, Datasets.Dataset):
            #documents that are part of a grouped document should displayed under that group and not displayed under the dataset
            skip_node_keys = []
            if isinstance(node.parent, Datasets.GroupedDataset):
                for key in node.parent.grouped_documents:
                    for subkey in node.parent.grouped_documents[key].documents:
                         if subkey[0] == node.key:
                            skip_node_keys.append(subkey[1])
            for key in node.documents:
                if key not in skip_node_keys:
                    include = True
                    if self.notes_contain_filter != "":
                        if self.notes_contain_filter not in node.documents[key].notes:
                            include = False
                    if len(self.usefulness_filter) > 0:
                        if node.documents[key].usefulness_flag not in self.usefulness_filter:
                            include = False
                    if include:
                        children.append(self.ObjectToItem(node.documents[key]))
        elif isinstance(node, Datasets.GroupedDocuments):
            for key in node.documents:
                include = True
                if self.notes_contain_filter != "":
                    if self.notes_contain_filter not in node.documents[key].notes:
                        include = False
                if len(self.usefulness_filter) > 0:
                    if node.documents[key].usefulness_flag not in self.usefulness_filter:
                        include = False
                if include:
                    children.append(self.ObjectToItem(node.documents[key]))
        return len(children)

    def IsContainer(self, item):
        ''' Return True for GroupedDataset, False otherwise for this model.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            return True
        if isinstance(node, Datasets.Dataset):
            return True
        if isinstance(node, Datasets.GroupedDocuments):
            return True
        # but everything else is not
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)

        if isinstance(node, Datasets.GroupedDataset):
            return dv.NullDataViewItem
        elif isinstance(node, Datasets.Dataset):
            if isinstance(node.parent, Datasets.GroupedDataset):
                return self.ObjectToItem(node.parent)
            else:
                return dv.NullDataViewItem
        elif isinstance(node, Datasets.GroupedDocuments):
            return self.ObjectToItem(node.parent)
        elif isinstance(node, Datasets.Document):
            if isinstance(node.parent.parent, Datasets.GroupedDataset):
                for key in node.parent.parent.grouped_documents:
                    if node.key in node.parent.parent.grouped_documents[key].documents:
                        return self.ObjectToItem(node.parent.parent.grouped_documents[key])
            return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            mapper = { 0 : str(node.name)+" / group",
                       1 : "",
                       2 : ""
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Dataset):
            mapper = { 0 : str(node.name)+" / "+str(node.dataset_source)+" / "+str(node.dataset_type),
                       1 : "",
                       2 : ""
                       }
            return mapper[col]
        elif isinstance(node, Datasets.GroupedDocuments):
            mapper = { 0 : str(node.key),
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       2 : ""
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            mapper = { 0 : str(node.url) if node.url != '' else str(node.key),
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       2 : str({key: node.data_dict[key] for key in node.data_dict})
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        '''retrieves custom attributes for item'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Document) or isinstance(node, Datasets.GroupedDocuments):
            if node.usefulness_flag:
                attr.SetColour(wx.Colour(red=0, green=102, blue=0))
                attr.SetBold(True)
                attr.SetStrikethrough(False)
                return True
            elif node.usefulness_flag is False:
                attr.SetColour(wx.Colour(red=255, green=0, blue=0))
                attr.SetBold(False)
                attr.SetStrikethrough(True)
                return True
        return False

    def SetValue(self, value, item, col):
        '''only allowing updating of notes as rest is connected to data retrieved'''
        node = self.ItemToObject(item)
        if col == 1:
            node.notes = value
        return True
    
    def HasContainerColumns(self, item):
        return True

#This view enables displaying documents
class DocumentViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model):
        dv.DataViewCtrl.__init__(self, parent, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES|dv.DV_VARIABLE_LINE_HEIGHT)

        self.AssociateModel(model)
        #model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        text_renderer = dv.DataViewTextRenderer()

        column0 = dv.DataViewColumn(GUIText.ID, text_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        column0.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        column1 = dv.DataViewColumn(GUIText.NOTES, editabletext_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column1.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        column2 = dv.DataViewColumn("Data", text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        column2.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

    def OnShowPopup(self, event):
        menu = wx.Menu()
        menu.Append(1, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.OnCopyItems)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            document_id = model.GetValue(item, 0)
            notes = model.GetValue(item, 1)
            fields = model.GetValue(item, 2)
            selected_items.append('\t'.join([document_id, notes, fields]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
