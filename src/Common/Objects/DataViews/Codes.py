import logging

import wx
import wx.dataview as dv

from Common.GUIText import Datasets as GUIText
import Common.Objects.Codes as Codes
import Common.Objects.GUIs.Codes as CodesGUIs
import Common.Objects.Datasets as Datasets
import Common.Objects.GUIs.Datasets as DatasetsGUIs
import Common.Objects.Samples as Samples

# This model acts as a bridge between the CodesViewCtrl and all codes in the project.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class AllCodesViewModel(dv.PyDataViewModel):
    def __init__(self, codes):
        dv.PyDataViewModel.__init__(self)
        self.codes = codes
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for code_key in self.codes:
                children.append(self.ObjectToItem(self.codes[code_key]))
            return len(children)
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Codes.Code):
            for code_key in node.codes:
                if code_key != node.key:
                    children.append(self.ObjectToItem(self.codes[code_key]))
            return len(children)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        #TODO allow nested codes?
        # Any node that has a list of lower nodes
        #node = self.ItemToObject(item)
        #if isinstance(node, Codes.Code):
        #    return True
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            return True
        #TODO allow nested codes?
        #if isinstance(node, Codes.Code):
        #    return True
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        #TODO allow nested codes?
        if isinstance(node, Codes.Code):
            if node.id in self.obj.codes:
                return dv.NullDataViewItem
            else:
               return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            mapper = { 0 : node.name,
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       2 : len(node.connections),
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

# This model acts as a bridge between the CodesViewCtrl and the codes of an object.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class ObjectCodesViewModel(dv.PyDataViewModel):
    def __init__(self, codes, obj):
        dv.PyDataViewModel.__init__(self)
        self.obj = obj
        self.codes = codes
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for code_key in self.obj.codes:
                children.append(self.ObjectToItem(self.codes[code_key]))
            return len(children)
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Codes.Code):
            for code_key in node.codes:
                if code_key != node.key:
                    children.append(self.ObjectToItem(self.codes[code_key]))
            return len(children)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        #TODO allow nested codes?
        # Any node that has a list of lower nodes
        #node = self.ItemToObject(item)
        #if isinstance(node, Codes.Code):
        #    return True
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            return True
        #TODO allow nested codes?
        #if isinstance(node, Codes.Code):
        #    return True
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        #TODO allow nested codes?
        if isinstance(node, Codes.Code):
            if node.id in self.obj.codes:
                return dv.NullDataViewItem
            else:
               return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            mapper = { 0 : node.name,
                       1 : "\U0001F6C8" if node.notes != "" else "",
                       2 : len(node.connections),
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

#this view enables displaying of fields for different datasets
class CodesViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.AssociateModel(model)
        model.DecRef()

        text_renderer = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn("Code", text_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column2 = dv.DataViewColumn("References", int_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".CodesViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        CodesGUIs.CodeDialog(main_frame, node).Show()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY,
                                    GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        if isinstance(self.GetModel(), ObjectCodesViewModel):
            add_code_menuitem = menu.Append(wx.ID_ADD,
                                            "Add Codes")
            self.Bind(wx.EVT_MENU, self.OnAddCodes, add_code_menuitem)
            remove_codes_menuitem = menu.Append(wx.ID_REMOVE,
                                                "Remove Codes")
            self.Bind(wx.EVT_MENU, self.OnRemoveCodes, remove_codes_menuitem)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            name = model.GetValue(item, 0)
            notes = model.GetValue(item, 1)
            num_connections = model.GetValue(item, 2)
            selected_items.append('\t'.join([name, notes, num_connections]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
    
    #bring up menu on right click
    def OnAddCodes(self, event):
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()

        add_dialog = CodesGUIs.AddCodesDialog(main_frame, model.obj)
        if add_dialog.ShowModal() == wx.ID_OK:
            model.Cleared()

    def OnRemoveCodes(self, event):
        logger = logging.getLogger(__name__+".CodesViewCtrl.OnRemoveCode")
        logger.info("Starting")
        #confirmation
        if wx.MessageBox("Are you sure you want to remove selected codes?",
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished - Cancelled")
            return

        model = self.GetModel() 
        obj = model.obj
        for item in self.GetSelections():
            node = model.ItemToObject(item)
            node.RemoveConnection(obj)
            obj.RemoveCode(node.key)

        model.Cleared()

# This model acts as a bridge between the CodeConnectionsViewCtrl and the codes.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class CodeConnectionsViewModel(dv.PyDataViewModel):
    def __init__(self, objs):
        dv.PyDataViewModel.__init__(self)
        self.objs = objs
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for obj in self.objs:
                children.append(self.ObjectToItem(obj))
            return len(children)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        return False
    
    def HasContainerColumns(self, item):
        return False

    def GetParent(self, item):
        return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.GroupedDataset):
            mapper = { 0 : "Grouped Dataset",
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Dataset):
            mapper = { 0 : "Dataset",
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Datasets.GroupedDocuments):
            mapper = { 0 : "Grouped Documents",
                       1 : str(node.url) if node.url != '' else str(node.key),
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            mapper = { 0 : "Document",
                       1 : str(node.url) if node.url != '' else str(node.key),
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.Sample):
            mapper = { 0 : "Sample",
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

#this view enables displaying of fields for different datasets
class CodeConnectionsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.AssociateModel(model)
        model.DecRef()
    
        text_renderer = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn("Type", text_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.NAME, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_renderer = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".CodesViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(node, Datasets.Document):
            DatasetsGUIs.DocumentDialog(main_frame, node).Show()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY,
                                    GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            obj_type = model.GetValue(item, 0) 
            name = model.GetValue(item, 1)
            notes = model.GetValue(item, 3)
            selected_items.append('\t'.join([obj_type, name, notes]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
