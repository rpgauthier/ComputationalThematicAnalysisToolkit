import logging
import webbrowser

import wx
import wx.dataview as dv

from Common.GUIText import Samples as GUIText
import Common.Objects.Datasets as Datasets
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Common.Objects.Samples as Samples
import Common.Objects.GUIs.Datasets as SamplesGUIs

# This model acts as a bridge between the SamplesViewCtrl and the Samples to
# This model provides these data columns:
#     0. Sample Name:   string
#     1. Dataset Name: string
#     2. Sample Type: string
#     3. Datetime Created:    string
class SamplesViewModel(dv.PyDataViewModel):
    def __init__(self, data):
        dv.PyDataViewModel.__init__(self)
        self.data = data
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 4

    def GetColumnType(self, col):
        col_type = "string"
        return col_type

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for model in self.data:
                children.append(self.ObjectToItem(model))
            return len(self.data)
        return 0

    def IsContainer(self, item):
        ''' Return Trtue for root but False otherwise for this model.'''
        # The hidden root is a container
        if not item:
            return True
        # but everything else is not
        return False

    def GetParent(self, item):
        return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Samples.Sample):
            if node.end_dt is None or node.start_dt is None:
                generate_time = "In Progress"
            else:
                generate_time = node.end_dt - node.start_dt
            mapper = { 0 : str(node.key),
                       1 : str(node.dataset_key),
                       2 : str(node.sample_type),
                       3 : node.created_dt.strftime("%Y-%m-%d, %H:%M:%S"),
                       4 : str(generate_time)
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        '''retrieves custom attributes for item'''
        return False

    def SetValue(self, value, item, col):
        '''only allowing updating of key as rest is connected to data that was sampled'''
        node = self.ItemToObject(item)
        if col == 0:
            node.key = value.replace(" ", "_")
        return True

#This view enables displaying samples
class SamplesViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model):
        dv.DataViewCtrl.__init__(self, parent, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES)

        self.AssociateModel(model)
        #model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        text_renderer = dv.DataViewTextRenderer()

        column0 = dv.DataViewColumn(GUIText.SAMPLE_NAME, editabletext_renderer, 0,
                                    flags=dv.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        column1 = dv.DataViewColumn(GUIText.DATASET_NAME, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column2 = dv.DataViewColumn(GUIText.SAMPLE_TYPE, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        column3 = dv.DataViewColumn(GUIText.CREATED_ON, text_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)
        column4 = dv.DataViewColumn("Time to Generate", text_renderer, 4, align=wx.ALIGN_LEFT)
        self.AppendColumn(column4)

        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
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
            sample_key = model.GetValue(item, 0)
            dataset_key = model.GetValue(item, 1)
            sample_type = model.GetValue(item, 2)
            created_dt = model.GetValue(item, 3)
            selected_items.append('\t'.join([sample_key, dataset_key, sample_type, created_dt]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

# This model acts as a bridge between the PartsViewCtrl and the parts of a sample for a particular dataset/grouped_dataset to
# organizes it hierarchically.
# This model provides these data columns:
#     0. ID:   string
#     1. Notes: string
#     2. Data:    string
class PartsViewModel(dv.PyDataViewModel):
    def __init__(self, sample_data, dataset_data):
        dv.PyDataViewModel.__init__(self)
        self.sample_data = sample_data
        self.dataset_data = dataset_data
        self.UseWeakRefs(True)

        self.column_names = []
    
    def UpdateColumnNames(self):
        self.column_names = [GUIText.ID, GUIText.NOTES]
        if isinstance(self.dataset_data, Datasets.GroupedDataset):
            for merged_field_key in self.dataset_data.merged_fields:
                for field_key in self.dataset_data.merged_fields[merged_field_key].chosen_fields:
                    self.column_names.append((merged_field_key, field_key))
            for dataset_key in self.dataset_data.datasets:
                for merged_field_key in self.dataset_data.datasets[dataset_key].merged_fields:
                    for field_key in self.dataset_data.datasets[dataset_key].merged_fields[merged_field_key].chosen_fields:
                        self.column_names.append((merged_field_key, field_key))
                for field_key in self.dataset_data.datasets[dataset_key].chosen_fields:
                    self.column_names.append(field_key)
        elif isinstance(self.dataset_data, Datasets.Dataset):
            for merged_field_key in self.dataset_data.merged_fields:
                for field_key in self.dataset_data.merged_fields[merged_field_key].chosen_fields:
                    self.column_names.append((merged_field_key, field_key))
            for field_key in self.dataset_data.chosen_fields:
                self.column_names.append(field_key)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return len(column_names)

    def GetChildren(self, parent, children):
        row_num = 0
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for key in self.sample_data:
                node = self.sample_data[key]
                children.append(self.ObjectToItem(node))
                row_num += 1
                #if isinstance(node.parent, Samples.Part):
                #    if row_num >= node.parent.document_num:
                #        break
            return len(children)
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Samples.MergedPart):
            for part_key in node.parts_dict:
                children.append(self.ObjectToItem(node.parts_dict[part_key]))
        elif isinstance(node, Samples.Part):
            for document_key in node.documents:
                if isinstance(self.dataset_data, Datasets.GroupedDataset):
                    children.append(self.ObjectToItem(self.dataset_data.grouped_documents[document_key]))
                elif isinstance(self.dataset_data, Datasets.Dataset):
                    children.append(self.ObjectToItem(self.dataset_data.documents[document_key]))
                row_num += 1
                if row_num >= node.document_num:
                    break
        elif isinstance(node, Datasets.GroupedDocuments):
            for document_key in node.documents:
                children.append(self.ObjectToItem(node.documents[document_key]))
        #elif isinstance(node, Samples.Document):
        #    for field_key in node.fields_dict:
        #       children.append(self.ObjectToItem(node.fields_dict[field_key]))
        return len(children)

    def IsContainer(self, item):
        ''' Return True for GroupedDataset, False otherwise for this model.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node, Samples.MergedPart):
            return True
        if isinstance(node, Samples.Part):
            return True
        if isinstance(node, Datasets.GroupedDocuments):
            return True
        #if isinstance(node, Samples.Document):
        #    return True
        # but everything else is not
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)

        if isinstance(node, Samples.MergedPart):
            return dv.NullDataViewItem
        elif isinstance(node, Samples.Part):
            if isinstance(node.parent, Samples.MergedPart):
                return self.ObjectToItem(node.parent)
            else:
                return dv.NullDataViewItem
        elif isinstance(node, Datasets.GroupedDocuments):
            for key in self.sample_data:
                if isinstance(self.sample_data[key], Samples.MergedPart):
                    for subkey in self.sample_data[key].parts_dict:
                        if node.key in self.sample_data[key].parts_dict[subkey].documents:
                            return self.ObjectToItem(self.sample_data[key].parts_dict[subkey])
                elif isinstance(self.sample_data[key], Samples.Part):
                    if node.key in self.sample_data[key].documents:
                        return self.ObjectToItem(self.sample_data[key])
        elif isinstance(node, Datasets.Document):
            possible_grouped_documents = []
            for key in self.sample_data:
                if isinstance(self.sample_data[key], Samples.MergedPart):
                    for subkey in self.sample_data[key].parts_dict:
                        if node.key in self.sample_data[key].parts_dict[subkey].documents:
                            return self.ObjectToItem(self.sample_data[key].parts_dict[subkey])
                        else:
                            possible_grouped_documents.extend(self.sample_data[key].parts_dict[subkey].documents)
                elif isinstance(self.sample_data[key], Samples.Part):
                    if node.key in self.sample_data[key].documents:
                        return self.ObjectToItem(self.sample_data[key])
                    else:
                        possible_grouped_documents.extend(self.sample_data[key].documents)
            if isinstance(self.dataset_data, Datasets.GroupedDataset):
                for key in self.dataset_data.grouped_documents:
                    if key in possible_grouped_documents:
                        if node.key in self.dataset_data.grouped_documents[key].documents:
                            return self.ObjectToItem(self.dataset_data.grouped_documents[key])

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Samples.MergedPart):
            mapper = { 0 : str(node.name) +": "+str(node.label),
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       }
            for i in range(2, len(self.column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.Part):
            mapper = { 0 : str(node.name) +": "+str(node.label),
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       }
            for i in range(2, len(self.column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Datasets.GroupedDocuments):
            mapper = { 0 : str(node.key),
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       }
            for i in range(2, len(self.column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            mapper = { 0 : str(node.url),
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       }
            for i in range(2, len(self.column_names)):
                if self.column_names[i] in node.data_dict:
                    mapper[i] = str(node.data_dict[self.column_names[i]])
                else:
                    mapper[i] = ""
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

#This view enables displaying datasets and how they are grouped
class PartsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model):
        dv.DataViewCtrl.__init__(self, parent, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES|dv.DV_VARIABLE_LINE_HEIGHT)

        self.AssociateModel(model)
        #model.DecRef()

        text_renderer = dv.DataViewTextRenderer()

        column0 = dv.DataViewColumn(GUIText.ID, text_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        column0.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        column1 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column1.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.UpdateColumns()
        
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

    def UpdateColumns(self):
        model = self.GetModel()
        text_renderer = dv.DataViewTextRenderer()

        #remove exisitng data columns
        if len(model.column_names) > 2:
            for i in reversed(range(2, len(model.column_names))):
                self.DeleteColumn(self.GetColumn(i))

        #add data columns
        model.UpdateColumnNames()
        for i in range(2, len(model.column_names)):
            name = model.column_names[i][1][1]
            data_column = dv.DataViewColumn(str(name), text_renderer, i, align=wx.ALIGN_LEFT)
            self.AppendColumn(data_column)
            data_column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        
        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
        
        self.Refresh()

    def OnShowPopup(self, event):
        logger = logging.getLogger(__name__+".PartsViewCtrl.OnShowPopup")
        logger.info("Starting")
        menu = wx.Menu()
        menu.Append(1, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.OnCopyItems)
        self.PopupMenu(menu)
        logger.info("Finished")

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".PartsViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        node = self.GetModel().ItemToObject(item)

        if isinstance(node, Datasets.Document):
            if event.GetColumn() == 0:
                logger.info("Call to access url[%s]", node.url)
                webbrowser.open_new_tab(node.url)
            else:
                DatasetsGUIs.DocumentDialog(self, node).Show()
        logger.info("Finished")

    def OnCopyItems(self, event):
        logger = logging.getLogger(__name__+".PartsViewCtrl.OnCopyItems")
        logger.info("Starting")
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
        logger.info("Finished")

# This model acts as a bridge between the LDATopicViewCtrl and an LDA model to
# organizes it's list of topics.
# This model provides these data columns:
#     0. ID:   string
#     1. Label: string
#     2. Words: string
class TopicViewModel(dv.PyDataViewModel):
    def __init__(self, data):
        dv.PyDataViewModel.__init__(self)
        self.data = data
        self.UseWeakRefs(False)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for topic in self.data:
                children.append(self.ObjectToItem(topic))
            return len(children)
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Samples.TopicMergedPart):
            for part_key in node.parts_dict:
                children.append(self.ObjectToItem(node.parts_dict[part_key]))
            return len(children)
        return 0

    def IsContainer(self, item):
        ''' Return True for GroupedDataset, False otherwise for this model.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node, Samples.TopicMergedPart):
            return True
        # but everything elseare not
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Samples.TopicMergedPart):
            return dv.NullDataViewItem
        else:
            if isinstance(node.parent, Samples.LDATopicPart):
                if isinstance(node.parent, Samples.TopicMergedPart):
                    return self.ObjectToItem(node.parent)
                else:
                    return dv.NullDataViewItem
            else:
                return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Samples.TopicMergedPart):
            mapper = { 0 : str(node.key),
                       1 : str(node.label),
                       2 : str([word[0] for word in node.GetTopicKeywordsList()])
                       }
            return mapper[col]
        elif isinstance(node, Samples.TopicPart):
            mapper = { 0 : str(node.key),
                       1 : str(node.label),
                       2 : str([word[0] for word in node.GetTopicKeywordsList()])
                       }
            return mapper[col]
        elif isinstance(node, Samples.TopicUnknownPart):
            mapper = { 0 : str(node.key),
                       1 : str(node.label),
                       2 : ""
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def SetValue(self, value, item, col):
        '''only allowing updating of labels as rest is connected to model that was generated'''
        node = self.ItemToObject(item)
        if col == 1:
            node.label = value
        return True
    
    def HasContainerColumns(self, item):
        return True

class TopicViewCtrl(dv.DataViewCtrl):
    '''For rendering lda topics'''
    def __init__(self, parent, model):
        logger = logging.getLogger(__name__+".LDATopicViewCtrl.__init__")
        logger.info("Starting")
        dv.DataViewCtrl.__init__(self, parent, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES)

        self.AssociateModel(model)
        #model.DecRef()

        text_render = dv.DataViewTextRenderer()
        #int_render = dv.DataViewTextRenderer(varianttype="long")
        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)

        column0 = dv.DataViewColumn(GUIText.TOPIC_NUM, text_render, 0,
                                    align=wx.ALIGN_RIGHT)
        self.AppendColumn(column0)
        column1 = dv.DataViewColumn(GUIText.LABELS, editabletext_renderer, 1,
                                    flags=dv.DATAVIEW_CELL_EDITABLE,
                                    align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column2 = dv.DataViewColumn(GUIText.WORDS, text_render, 2,
                                    align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        columns = self.GetColumns()
        for column in reversed(columns):
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        copy_id = wx.ID_ANY
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=copy_id)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), copy_id )])
        self.SetAcceleratorTable(accel_tbl)

        logger.info("Finished")

    def OnShowPopup(self, event):
        '''create popup menu with options that can be performed on the list'''
        logger = logging.getLogger(__name__+".LDATopicViewCtrl.OnShowPopup")
        logger.info("Starting")
        menu = wx.Menu()
        menu.Append(1, "Copy")
        menu.Bind(wx.EVT_MENU, self.OnCopyItems)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        '''copies what is selected in the list to the user's clipboard'''
        logger = logging.getLogger(__name__+".LDATopicViewCtrl.OnCopyItems")
        logger.info("Starting")
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            topic_num = model.GetValue(item, 0)
            labels = model.GetValue(item, 1)
            words = model.GetValue(item, 2)
            selected_items.append('\t'.join([str(topic_num), labels, words]).strip())

        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
