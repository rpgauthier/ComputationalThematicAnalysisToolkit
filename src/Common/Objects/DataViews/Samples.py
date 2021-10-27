import logging
import webbrowser
from datetime import datetime

import wx
import wx.dataview as dv

from Common.GUIText import Samples as GUIText
import Common.Constants as Constants
import Common.Objects.Datasets as Datasets
import Common.Objects.Samples as Samples
import Common.Objects.Utilities.Samples as SamplesUtilities
import Common.Objects.GUIs.Codes as CodesGUIs

# This model acts as a bridge between the PartsViewCtrl and the parts of a sample for a particular dataset to
# organizes it hierarchically.
# This model provides these data columns:
#     0. ID:   string
#     1. Notes: string
#     2. Data:    string
class PartsViewModel(dv.PyDataViewModel):
    def __init__(self, sample, dataset):
        dv.PyDataViewModel.__init__(self)
        self.sample = sample
        self.dataset = dataset
        self.UseWeakRefs(True)

        self.metadata_column_names = []
        self.metadata_column_types = []
        self.column_names = []
        self.UpdateColumnNames()
    
    def UpdateColumnNames(self):
        if hasattr(self.dataset, 'metadata_fields'):
            if len(self.dataset.metadata_fields) == 0:
                self.metadata_column_names.append('id')
                self.metadata_column_types.append('string')
            else:
                for field_name in self.dataset.metadata_fields:
                    self.metadata_column_names.append(field_name)
                    self.metadata_column_types.append(self.dataset.metadata_fields[field_name].fieldtype)
        else:
            if self.dataset.dataset_source == "Reddit":
                self.metadata_column_names.append('url')
                self.metadata_column_types.append('url')
                if self.dataset.dataset_type == "discussion" or self.dataset.dataset_type == "submission":
                    self.metadata_column_names.append('title')
                    self.metadata_column_types.append('string')
                elif self.dataset.dataset_type == "comment":
                    self.metadata_column_names.append('body')
                    self.metadata_column_types.append('string')
            else:
                self.metadata_column_names.append('id')
                self.metadata_column_types.append('string')
        
        self.column_names.clear()
        self.column_names.extend([GUIText.NOTES])

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return len(self.metadata_column_names) + len(self.column_names)

    def GetChildren(self, parent, children):
        row_num = 0
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for key in self.sample.parts_dict:
                node = self.sample.parts_dict[key]
                children.append(self.ObjectToItem(node))
            return len(children)
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Samples.MergedPart):
            for part_key in node.parts_dict:
                children.append(self.ObjectToItem(node.parts_dict[part_key]))
        elif isinstance(node, Samples.Part):
            for document_key in node.documents:
                if isinstance(self.dataset, Datasets.Dataset):
                    children.append(self.ObjectToItem(self.dataset.documents[document_key]))
                row_num += 1
                if row_num >= node.document_num:
                    break
        return len(children)

    def IsContainer(self, item):
        ''' Return True for MergedPart or Part, False otherwise for this model.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node, Samples.MergedPart):
            return True
        if isinstance(node, Samples.Part):
            return True
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
        elif isinstance(node, Datasets.Document):
            for key in self.sample.parts_dict:
                if isinstance(self.sample.parts_dict[key], Samples.MergedPart):
                    for subkey in self.sample.parts_dict[key].parts_dict:
                        if node.key in self.sample.parts_dict[key].parts_dict[subkey].documents:
                            return self.ObjectToItem(self.sample.parts_dict[key].parts_dict[subkey])
                elif isinstance(self.sample.parts_dict[key], Samples.Part):
                    if node.key in self.sample.parts_dict[key].documents:
                        return self.ObjectToItem(self.sample.parts_dict[key])

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Samples.MergedPart):
            mapper = { 0 : node.selected if hasattr(node, "selected") and node.selected == True  else False,
                       1 : str(node.name) +": "+str(node.label),
                       len(self.metadata_column_names)+1 : "\U0001F6C8" if node.notes != "" else "",
                       }
            for i in range(2, len(self.metadata_column_names)+1):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.Part):
            mapper = { 0 : node.selected if hasattr(node, "selected") and node.selected == True else False,
                       1 : str(node.name) +": "+str(node.label),
                       len(self.metadata_column_names)+1 : "\U0001F6C8" if node.notes != "" else "",
                       }
            for i in range(2, len(self.metadata_column_names)+1):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            if hasattr(self.sample, "selected_documents") and node.key in self.sample.selected_documents:
                selected = True
            else:
                selected = False

            mapper = { 0 : selected,
                       len(self.metadata_column_names)+1 : "\U0001F6C8" if node.notes != "" else "", }
            idx = 1
            for field_name in self.metadata_column_names:
                if field_name in node.parent.data[node.key]:
                    value = node.parent.data[node.key][field_name]
                    if self.metadata_column_types[idx-1] == 'url':
                        segmented_url = value.split("/")
                        value = "<span color=\"#0645ad\"><u>"+segmented_url[len(segmented_url)-1]+"</u></span>"
                    elif self.metadata_column_types[idx-1] == 'UTC-timestamp':
                        if isinstance(value, list):
                            value_str = ""
                            for entry in value:
                                value_str = str(datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT))+"UTC "
                                break
                            if len(value) > 1:
                                value = value_str + "..."
                            else:
                                value = value_str
                        else:
                            value = datetime.utcfromtimestamp(value).strftime(Constants.DATETIME_FORMAT)+"UTC"
                    elif self.metadata_column_types[idx-1] == 'int':
                        if isinstance(value, list):
                            value = value[0]
                        else:
                            value = value
                    else:
                        if isinstance(value, list):
                            first_entry = ""
                            for entry in value:
                                if entry != "":
                                    first_entry = ' '.join(entry.split())
                                    break
                            if len(value) > 1:
                                first_entry = str(first_entry) + " ..."
                            value = first_entry
                        value = str(value).split('\n')[0]
                else:
                    value = ""
                mapper[idx] = value
                idx = idx+1
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def GetAttr(self, item, col, attr):
        '''retrieves custom attributes for item'''
        node = self.ItemToObject(item)
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
    
    def HasContainerColumns(self, item):
        return True
    
    def SetValue(self, value, item, col):
        node = self.ItemToObject(item)
        if col == 0:
            SamplesUtilities.SamplesSelected(self.sample, self.dataset, node, value)
            main_frame = wx.GetApp().GetTopWindow()
            main_frame.DocumentsUpdated()
        return True

#This view enables displaying datasets and how they are grouped
class PartsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model):
        dv.DataViewCtrl.__init__(self, parent, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES|dv.DV_VARIABLE_LINE_HEIGHT)

        self.AssociateModel(model)
        model.DecRef()

        self.UpdateColumns()
        
        self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
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
        for column in self.Columns:
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

    def UpdateColumns(self):
        model = self.GetModel()
        if self.ColumnCount:
            for i in reversed(range(0, self.ColumnCount)):
                self.DeleteColumn(self.GetColumn(i))

        renderer = dv.DataViewToggleRenderer(mode=dv.DATAVIEW_CELL_ACTIVATABLE)
        column0 = dv.DataViewColumn("", renderer, 0, flags=dv.DATAVIEW_CELL_ACTIVATABLE)
        self.AppendColumn(column0)
        self.SetExpanderColumn(column0)

        #add data columns
        idx = 1
        for field_name in model.metadata_column_names:
            if model.metadata_column_types[idx-1] == 'int':
                renderer = dv.DataViewTextRenderer(varianttype="long")
            elif model.metadata_column_types[idx-1] == 'url':
                renderer = dv.DataViewTextRenderer()
                renderer.EnableMarkup()
            else:
                renderer = dv.DataViewTextRenderer()

            column = dv.DataViewColumn(field_name, renderer, idx, align=wx.ALIGN_LEFT)
            self.AppendColumn(column)
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
            idx = idx+1

        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.NOTES, text_renderer, idx, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column1.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        idx = idx+1
        
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
        model = self.GetModel()
        item = event.GetItem()
        node = model.ItemToObject(item)

        if isinstance(node, Datasets.Document):
            col = event.GetColumn()
            if 0 < col < len(model.metadata_column_names)+1 and model.metadata_column_types[col-1] == 'url':
                logger.info("Call to access url[%s]", node.url)
                webbrowser.open_new_tab(node.url)
            else:
                CodesGUIs.DocumentDialog(self, node).Show()
        logger.info("Finished")

    def OnCopyItems(self, event):
        logger = logging.getLogger(__name__+".PartsViewCtrl.OnCopyItems")
        logger.info("Starting")
        selected_items = []
        model = self.GetModel()
        for row in self.GetSelections():
            line = ''
            for col in range(0, model.metadata_column_names):
                line = line + str(model.GetValue(row, col)) + '\t'
            selected_items.append(line.strip())
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
        ''' Return True for TopicMergedPart, False otherwise for this model.'''
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
            words = [word[0] for word in node.GetTopicKeywordsList()]
            mapper = { 0 : str(node.key),
                       1 : str(node.label),
                       2 : str(', '.join(words))
                       }
            return mapper[col]
        elif isinstance(node, Samples.TopicPart):
            words = [word[0] for word in node.GetTopicKeywordsList()]
            mapper = { 0 : str(node.key),
                       1 : str(node.label),
                       2 : str(', '.join(words))
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
            if node.label != value:
                node.label = value
                main_frame = wx.GetApp().GetTopWindow()
                main_frame.SamplesUpdated()

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
        model.DecRef()

        #int_render = dv.DataViewTextRenderer(varianttype="long")
        
        text_render = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn(GUIText.TOPIC_NUM, text_render, 0,
                                    align=wx.ALIGN_RIGHT)
        self.AppendColumn(column0)
        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column1 = dv.DataViewColumn(GUIText.LABEL, editabletext_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_render = dv.DataViewTextRenderer()
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

        self.Expander(None)
        logger.info("Finished")

    def Expander(self, item):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)
        for column in self.Columns:
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

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
