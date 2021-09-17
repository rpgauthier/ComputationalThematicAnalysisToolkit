import logging
from re import sub
from threading import main_thread
import webbrowser
from datetime import datetime

import wx
import wx.dataview as dv

from Common.GUIText import Coding as GUIText
import Common.Constants as Constants
import Common.Objects.Codes as Codes
import Common.Objects.Utilities.Codes as CodesUtilities
import Common.Objects.GUIs.Codes as CodesGUIs
import Common.Objects.Datasets as Datasets
import Common.Objects.Samples as Samples

# This model acts as a bridge between the CodesViewCtrl and the codes of the workspace.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class CodesViewModel(dv.PyDataViewModel):
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
                if isinstance(self.codes[code_key], Codes.Code):
                    children.append(self.ObjectToItem(self.codes[code_key]))
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        else:
            node = self.ItemToObject(parent)
            if isinstance(node, Codes.Code):
                for code_key in node.subcodes:
                    children.append(self.ObjectToItem(node.subcodes[code_key]))
        return len(children)

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            if self.GetChildren(item, []) > 0:
                return True
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            return True
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            if node.parent != None:
                return self.ObjectToItem(node.parent)
            else:
                return dv.NullDataViewItem

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

    def SetValue(self, value, item, col):
        '''only allowing updating of key as rest is connected to data retrieved'''
        node = self.ItemToObject(item)
        if col == 0 and node.key != value:
            if value == "":
                wx.MessageBox(GUIText.RENAME_CODE_BLANK_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            elif CodesUtilities.CodeKeyUniqueCheck(value, self.codes):
                old_key = node.key
                node.key = value
                node.name = value
                if node.parent == None:
                    self.codes[node.key] = node
                    del self.codes[old_key]
                else:
                    node.parent.subcodes[node.key] = node
                    del node.parent.subcodes[old_key]
                main_frame = wx.GetApp().GetTopWindow()
                for obj in node.GetConnections(main_frame.datasets, main_frame.samples):
                    obj.codes.remove(old_key)
                    obj.codes.append(node.key)
                main_frame.DocumentsUpdated()
                main_frame.CodesUpdated()
            else:
                wx.MessageBox(GUIText.RENAME_CODE_NOTUNIQUE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
        return True

#this view enables displaying of fields for different datasets
class CodesViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.selected_item = None

        self.AssociateModel(model)
        model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column0 = dv.DataViewColumn(GUIText.CODES, editabletext_renderer, 0, flags=dv.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column2 = dv.DataViewColumn(GUIText.REFERENCES, int_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        for i in range(0, len(self.Columns)):
            column = self.Columns[i]
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

        self.Bind(dv.EVT_DATAVIEW_ITEM_BEGIN_DRAG, self.OnDrag)
        self.Bind(dv.EVT_DATAVIEW_ITEM_DROP_POSSIBLE, self.OnDropPossible)
        self.Bind(dv.EVT_DATAVIEW_ITEM_DROP, self.OnDrop)
        self.EnableDragSource(wx.DataFormat(wx.DF_UNICODETEXT))
        self.EnableDropTarget(wx.DataFormat(wx.DF_UNICODETEXT))
        self.dragnode = None

        self.Expander(None)

    def Expander(self, item):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)

    def OnDrag(self, event):
        item = event.GetItem()
        self.drag_node = self.GetModel().ItemToObject(item)
        key = self.drag_node.key
        obj = wx.TextDataObject()
        obj.SetText(key)
        event.SetDataObject(obj)
    
    def OnDropPossible(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return

    def OnDrop(self, event):
        item = event.GetItem()
        main_frame = wx.GetApp().GetTopWindow()
        model = self.GetModel()
        if item.IsOk():
            node = model.ItemToObject(item)
            if self.drag_node.parent is not None:
                del self.drag_node.parent.subcodes[self.drag_node.key]
            else:
                del main_frame.codes[self.drag_node.key]
            node.subcodes[self.drag_node.key] = self.drag_node
            self.drag_node.parent = node
        else:
            if self.drag_node.parent is not None:
                del self.drag_node.parent.subcodes[self.drag_node.key]
            else:
                del main_frame.codes[self.drag_node.key]
            main_frame.codes[self.drag_node.key] = self.drag_node
            self.drag_node.parent = None
        self.drag_node = None
        model.Cleared()
        self.Expander(None)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        CodesGUIs.CodeConnectionsDialog(main_frame, node, size=wx.Size(400,400)).Show()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY,
                                    GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        if isinstance(self.GetModel(), CodesViewModel):
            add_code_menuitem = menu.Append(wx.ID_ADD, GUIText.ADD_NEW_CODE)
            self.Bind(wx.EVT_MENU, self.OnAddCode, add_code_menuitem)
            self.selected_item = event.GetItem()
            if self.selected_item:
                add_code_menuitem = menu.Append(wx.ID_ANY, GUIText.ADD_NEW_SUBCODE)
                self.Bind(wx.EVT_MENU, self.OnAddSubCode, add_code_menuitem)
            if self.HasSelection():
                delete_codes_menuitem = menu.Append(wx.ID_ANY, GUIText.DELETE_CODES)
                self.Bind(wx.EVT_MENU, self.OnDeleteCodes, delete_codes_menuitem)
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
    def OnAddCode(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnAddCode")
        logger.info("Starting")
        new_name = None
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()
        add_dialog = wx.TextEntryDialog(main_frame, message=GUIText.ADD_NEW_CODE, caption=GUIText.NEW_CODE)
        
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                elif CodesUtilities.CodeKeyUniqueCheck(new_name, main_frame.codes):
                    main_frame.codes[new_name] = Codes.Code(new_name)
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
                else:
                    wx.MessageBox(GUIText.NEW_CODE_NOTUNIQUE_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
            else:
                break
        logger.info("Finished")
    
    #bring up menu on right click
    def OnAddSubCode(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnAddSubCode")
        logger.info("Starting")
        new_name = None
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()
        item = self.selected_item
        node = model.ItemToObject(item)
        add_dialog = wx.TextEntryDialog(main_frame, message=GUIText.ADD_NEW_SUBCODE, caption=GUIText.NEW_SUBCODE)
        
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                elif CodesUtilities.CodeKeyUniqueCheck(new_name, main_frame.codes):
                    node.subcodes[new_name] = Codes.Code(new_name)
                    node.subcodes[new_name].parent = node
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
                else:
                    wx.MessageBox(GUIText.NEW_CODE_NOTUNIQUE_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
            else:
                break
        logger.info("Finished")

    def OnDeleteCodes(self, event):
        logger = logging.getLogger(__name__+".CodesViewCtrl.OnDeleteCodes")
        logger.info("Starting")
        #confirmation
        if wx.MessageBox(GUIText.CONFIRM_DELETE_CODES,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished - Cancelled")
            return

        model = self.GetModel() 
        main_frame = wx.GetApp().GetTopWindow()
        delete_codes = []
        for item in self.GetSelections():
            delete_codes.append(model.ItemToObject(item))
        
        for code in delete_codes:
            def DeleteCode(code):
                for subcode_key in list(code.subcodes.keys()):
                    DeleteCode(code.subcodes[subcode_key])
                connection_objs = code.GetConnections(main_frame.datasets, main_frame.samples)
                for obj in connection_objs:
                    obj.RemoveCode(code.key)
                    code.RemoveConnection(obj)

                if code.parent != None:
                    code.DestroyObject()
                elif code.key in main_frame.codes:
                    code.DestroyObject()
                    del main_frame.codes[code.key]
            DeleteCode(code)

        model.Cleared()
        self.Expander(None)
        main_frame.CodesUpdated()
        logger.info("Finished")

# This model acts as a bridge between the ObjectCodesViewCtrl and the codes of an object.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class ObjectCodesViewModel(CodesViewModel):
    def __init__(self, codes, obj):
        CodesViewModel.__init__(self, codes)
        self.obj = obj

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 4

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            mapper = { 0 : True if node.key in self.obj.codes else False,
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       3 : len(node.connections),
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def SetValue(self, value, item, col):
        '''only allowing updating of key as rest is connected to data retrieved'''
        node = self.ItemToObject(item)
        if col == 0:
            if value and node.key not in self.obj.codes:
                self.obj.codes.append(node.key)
                self.obj.last_changed_dt = datetime.now()
                node.AddConnection(self.obj)
                main_frame = wx.GetApp().GetTopWindow()
                main_frame.DocumentsUpdated()
                main_frame.CodesUpdated()
            elif  node.key in self.obj.codes:
                self.obj.codes.remove(node.key)
                self.obj.last_changed_dt = datetime.now()
                node.RemoveConnection(self.obj)
                main_frame = wx.GetApp().GetTopWindow()
                main_frame.DocumentsUpdated()
                main_frame.CodesUpdated()
        elif col == 1 and node.key != value:
            if value == "":
                wx.MessageBox(GUIText.RENAME_CODE_BLANK_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            elif CodesUtilities.CodeKeyUniqueCheck(value, self.codes):
                old_key = node.key
                node.key = value
                node.name = value
                self.codes[node.key] = node
                del self.codes[old_key]
                main_frame = wx.GetApp().GetTopWindow()
                for obj in node.GetConnections(main_frame.datasets, main_frame.samples):
                    obj.codes.remove(old_key)
                    obj.codes.append(node.key)
                main_frame.DocumentsUpdated()
                main_frame.CodesUpdated()
            else:
                wx.MessageBox(GUIText.RENAME_CODE_NOTUNIQUE_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
        return True

#this view enables displaying of fields for different datasets
class ObjectCodesViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.selected_item = None

        self.AssociateModel(model)
        model.DecRef()

        renderer = dv.DataViewToggleRenderer(mode=dv.DATAVIEW_CELL_ACTIVATABLE)
        column0 = dv.DataViewColumn("", renderer, 0, flags=dv.DATAVIEW_CELL_ACTIVATABLE)
        self.AppendColumn(column0)
        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column1 = dv.DataViewColumn(GUIText.CODES, editabletext_renderer, 1, flags=dv.DATAVIEW_CELL_EDITABLE, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_renderer = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column3 = dv.DataViewColumn(GUIText.REFERENCES, int_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)

        for i in range(1, len(self.Columns)):
            column = self.Columns[i]
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

        self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

        self.Bind(dv.EVT_DATAVIEW_ITEM_BEGIN_DRAG, self.OnDrag)
        self.Bind(dv.EVT_DATAVIEW_ITEM_DROP_POSSIBLE, self.OnDropPossible)
        self.Bind(dv.EVT_DATAVIEW_ITEM_DROP, self.OnDrop)
        self.EnableDragSource(wx.DataFormat(wx.DF_UNICODETEXT))
        self.EnableDropTarget(wx.DataFormat(wx.DF_UNICODETEXT))
        self.dragnode = None

        self.Expander(None)

    def Expander(self, item):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)

    def OnDrag(self, event):
        item = event.GetItem()
        self.drag_node = self.GetModel().ItemToObject(item)
        key = self.drag_node.key
        obj = wx.TextDataObject()
        obj.SetText(key)
        event.SetDataObject(obj)
    
    def OnDropPossible(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return

    def OnDrop(self, event):
        item = event.GetItem()
        main_frame = wx.GetApp().GetTopWindow()
        model = self.GetModel()
        if item.IsOk():
            node = model.ItemToObject(item)
            if self.drag_node.parent is not None:
                del self.drag_node.parent.subcodes[self.drag_node.key]
            else:
                del main_frame.codes[self.drag_node.key]
            node.subcodes[self.drag_node.key] = self.drag_node
            self.drag_node.parent = node
        else:
            if self.drag_node.parent is not None:
                del self.drag_node.parent.subcodes[self.drag_node.key]
            else:
                del main_frame.codes[self.drag_node.key]
            main_frame.codes[self.drag_node.key] = self.drag_node
            self.drag_node.parent = None
        self.drag_node = None
        model.Cleared()
        self.Expander(None)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        CodesGUIs.CodeConnectionsDialog(main_frame, node, size=wx.Size(400,400)).Show()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY,
                                    GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        if isinstance(self.GetModel(), ObjectCodesViewModel):
            add_code_menuitem = menu.Append(wx.ID_ADD, GUIText.ADD_NEW_CODE)
            self.Bind(wx.EVT_MENU, self.OnAddCode, add_code_menuitem)
            self.selected_item = event.GetItem()
            if self.selected_item:
                add_code_menuitem = menu.Append(wx.ID_ANY, GUIText.ADD_NEW_SUBCODE)
                self.Bind(wx.EVT_MENU, self.OnAddSubCode, add_code_menuitem)
            if self.HasSelection():
                delete_codes_menuitem = menu.Append(wx.ID_ANY, GUIText.DELETE_CODES)
                self.Bind(wx.EVT_MENU, self.OnDeleteCodes, delete_codes_menuitem)
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
    def OnAddCode(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnAddCode")
        logger.info("Starting")
        new_name = None
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()
        add_dialog = wx.TextEntryDialog(main_frame, message=GUIText.ADD_NEW_CODE, caption=GUIText.NEW_CODE)
        
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                elif CodesUtilities.CodeKeyUniqueCheck(new_name, main_frame.codes):
                    main_frame.codes[new_name] = Codes.Code(new_name)
                    model.obj.AppendCode(new_name)
                    main_frame.codes[new_name].AddConnection(model.obj)
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
                else:
                    wx.MessageBox(GUIText.NEW_CODE_NOTUNIQUE_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
            else:
                break
        logger.info("Finished")
    
    #bring up menu on right click
    def OnAddSubCode(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnAddSubCode")
        logger.info("Starting")
        new_name = None
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()
        item = self.selected_item
        node = model.ItemToObject(item)
        add_dialog = wx.TextEntryDialog(main_frame, message=GUIText.ADD_NEW_SUBCODE, caption=GUIText.NEW_SUBCODE)
        
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                elif CodesUtilities.CodeKeyUniqueCheck(new_name, main_frame.codes):
                    node.subcodes[new_name] = Codes.Code(new_name)
                    node.subcodes[new_name].parent = node
                    model.obj.AppendCode(new_name)
                    node.subcodes[new_name].AddConnection(model.obj)
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
                else:
                    wx.MessageBox(GUIText.NEW_CODE_NOTUNIQUE_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
            else:
                break
        logger.info("Finished")

    def OnDeleteCodes(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnDeleteCodes")
        logger.info("Starting")
        #confirmation
        if wx.MessageBox(GUIText.CONFIRM_DELETE_CODES,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.NO:
            logger.info("Finished - Cancelled")
            return

        model = self.GetModel() 
        main_frame = wx.GetApp().GetTopWindow()
        delete_codes = []
        for item in self.GetSelections():
            delete_codes.append(model.ItemToObject(item))
        
        for code in delete_codes:
            def DeleteCode(code):
                for subcode_key in list(code.subcodes.keys()):
                    DeleteCode(code.subcodes[subcode_key])
                connection_objs = code.GetConnections(main_frame.datasets, main_frame.samples)
                for obj in connection_objs:
                    obj.RemoveCode(code.key)
                    code.RemoveConnection(obj)

                if code.parent != None:
                    code.DestroyObject()
                elif code.key in main_frame.codes:
                    code.DestroyObject()
                    del main_frame.codes[code.key]
            DeleteCode(code)

        model.Cleared()
        self.Expander(None)
        main_frame.CodesUpdated()
        logger.info("Finished")

# This model acts as a bridge between the CodeConnectionsViewCtrl and the codes.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
#TODO need to rework ViewModel to show dynamic metadata columns instead of just system ids
class CodeConnectionsViewModel(dv.PyDataViewModel):
    def __init__(self, objs):
        dv.PyDataViewModel.__init__(self)
        self.objs = objs
        self.UseWeakRefs(True)
    
    def UpdateColumnNames(self):
        if hasattr(self.dataset, 'metadata_fields'):
            if len(self.dataset.metadata_fields) == 0:
                self.metadata_column_names.append('id')
                self.metadata_column_types.append('string')
            else:
                for field_name in self.dataset.metadata_fields:
                    self.metadata_column_names.append(field_name)
                    self.metadata_column_types.append(self.dataset.metadata_fields[field_name].field_type)
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
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for obj in self.objs:
                while obj.parent != None:
                    obj = obj.parent
                child_item = self.ObjectToItem(obj)
                if child_item not in children:
                    children.append(child_item)
            return len(children)
        node = self.ItemToObject(parent)
        if isinstance(node, Datasets.Dataset):
            for key in node.documents:
                if node.documents[key] in self.objs:
                    children.append(self.ObjectToItem(node.documents[key]))
            return len(children)
        if isinstance(node, Samples.Sample):
            for key in node.parts_dict:
                if node.parts_dict[key] in self.objs:
                    children.append(self.ObjectToItem(node.parts_dict[key]))
            return len(children)
        return 0

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        node = self.ItemToObject(item)
        if self.GetChildren(item, []) > 0:
            return True
        else:
            return False
    
    def HasContainerColumns(self, item):
        return True

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
            mapper = { 0 : repr(node),
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            mapper = { 0 : repr(node),
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.Sample):
            mapper = { 0 : repr(node),
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.TopicMergedPart):
            mapper = { 0 : repr(node),
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.MergedPart):
            mapper = { 0 : repr(node),
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.TopicPart):
            mapper = { 0 : repr(node),
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.Part):
            mapper = { 0 : repr(node),
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

#this view enables displaying of fields for different datasets
#TODO need to rework ViewModel to show dynamic metadata columns instead of just system ids
class CodeConnectionsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.AssociateModel(model)
        model.DecRef()
    
        text_renderer = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn(GUIText.TYPE, text_renderer, 0, align=wx.ALIGN_LEFT)
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

        self.Expander(None)

    def Expander(self, item):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".CodeConnectionsViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(node, Datasets.Document):
            CodesGUIs.DocumentDialog(main_frame, node).Show()
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
            notes = model.GetValue(item, 2)
            selected_items.append('\t'.join([obj_type, name, notes]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

# This model acts as a bridge between the DocumentViewCtrl and a dataset's documents and samples to
# organizes it hierarchically.
# This model provides these data columns:
#     0. ID:   string
#     1. Notes: string
#     2. Data:    string
class DocumentViewModel(dv.PyDataViewModel):
    def __init__(self, dataset_data, samples_data):
        dv.PyDataViewModel.__init__(self)
        self.dataset_data = dataset_data
        self.samples_data = samples_data
        self.UseWeakRefs(True)

        self.search_filter = ""
        self.usefulness_filter = []
        self.samples_filter = []

        self.metadata_column_names = []
        self.metadata_column_types = []
        self.data_column_names = []
        self.data_column_types = []
        self.column_names = []
        self.UpdateColumnNames()

    def UpdateColumnNames(self):
        self.metadata_column_names.clear()
        self.metadata_column_types.clear()
        if len(self.dataset_data.metadata_fields) == 0:
            self.metadata_column_names.append('id')
            self.metadata_column_types.append('string')
        else:
            for field_name in self.dataset_data.metadata_fields:
                self.metadata_column_names.append(field_name)
                self.metadata_column_types.append(self.dataset_data.metadata_fields[field_name].fieldtype)

        self.data_column_names.clear()
        self.data_column_types.clear()
        for field_name in self.dataset_data.included_fields:
            if field_name not in self.metadata_column_names and field_name not in self.data_column_names:
                self.data_column_names.append(field_name)
                self.data_column_types.append(self.dataset_data.included_fields[field_name].fieldtype)

        self.column_names.clear()
        self.column_names.extend([GUIText.NOTES, GUIText.CODES])

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return len(self.metadata_column_names) +  len(self.data_column_names) + len(self.column_names)

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            possible_children = []
            subchildren = []
            if 'dataset' in self.samples_filter: 
                item = self.ObjectToItem(self.dataset_data)
                dataset_children = []
                self.GetChildren(item, dataset_children)
                if len(dataset_children) > 0:
                    subchildren.extend(dataset_children)
                    possible_children.append(item)
            for sample_key in self.samples_data:
                if sample_key in self.samples_filter:
                    item = self.ObjectToItem(self.samples_data[sample_key])
                    sample_children = []
                    self.GetChildren(item, sample_children)
                    if len(sample_children) > 0:
                        subchildren.extend(sample_children)
                        possible_children.append(item)
            if len(possible_children) == 1:
                for child in subchildren:
                    children.append(child)
            else:
                for child in possible_children:
                    children.append(child)
            return len(children)
                
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        node = self.ItemToObject(parent)
        if isinstance(node, Datasets.Dataset):
            for document_key in node.selected_documents:
                include = False
                if self.search_filter != '':
                    for i in range(0, len(self.metadata_column_names)):
                        col_name = self.metadata_column_names[i]
                        col_type = self.metadata_column_types[i]
                        value = node.data[document_key][col_name]
                        if isinstance(value, list):
                            value_str = ""
                            for entry in value:
                                if col_type == 'int':
                                    value_str = value_str + " " + str(entry)
                                elif col_type == 'UTC-timestamp':
                                    value_str = value_str + " " + datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT)
                                else:
                                    value_str = value_str + " " + entry
                            value = value_str
                        else:
                            if col_type == 'int':
                                value = str(value)
                            elif col_type == 'UTC-timestamp':
                                value = datetime.utcfromtimestamp(value).strftime(Constants.DATETIME_FORMAT)
                        if self.search_filter in value:
                            include = True
                            break
                    for i in range(0, len(self.data_column_names)):
                        col_name = self.data_column_names[i]
                        col_type = self.data_column_types[i]
                        value = node.data[document_key][col_name]
                        if isinstance(value, list):
                            value_str = ""
                            for entry in value:
                                if col_type == 'int':
                                    value_str = value_str + " " + str(entry)
                                elif col_type == 'UTC-timestamp':
                                    value_str = value_str + " " + datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT)
                                else:
                                    value_str = value_str + " " + entry
                            value = value_str
                        else:
                            if col_type == 'int':
                                value = str(value)
                            elif col_type == 'UTC-timestamp':
                                value = datetime.utcfromtimestamp(value).strftime(Constants.DATETIME_FORMAT)
                        if self.search_filter in value:
                            include = True
                            break
                else:
                    include = True
                if len(self.usefulness_filter) > 0:
                    if node.documents[document_key].usefulness_flag not in self.usefulness_filter:
                        include = False
                if include:
                    children.append(self.ObjectToItem(node.documents[document_key]))
        elif isinstance(node, Samples.Sample) or isinstance(node, Samples.MergedPart):
            for part_key in node.parts_dict:
                part = node.parts_dict[part_key]
                item = self.ObjectToItem(part)
                if self.GetChildren(item, []) > 0:
                    children.append(item)
        elif isinstance(node, Samples.Part):
            for document_key in node.documents:
                sample = node.parent
                if isinstance(sample, Samples.MergedPart):
                    sample = sample.parent
                if hasattr(sample, 'selected_documents') and document_key in sample.selected_documents:
                    include = False
                    if self.search_filter != '':
                        for i in range(0, len(self.metadata_column_names)):
                            col_name = self.metadata_column_names[i]
                            col_type = self.metadata_column_types[i]
                            value = node.documents[document_key][col_name]
                            if isinstance(value, list):
                                value_str = ""
                                for entry in value:
                                    if col_type == 'int':
                                        value_str = value_str + " " + str(entry)
                                    elif col_type == 'UTC-timestamp':
                                        value_str = value_str + " " + datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT)
                                    else:
                                        value_str = value_str + " " + entry
                                value = value_str
                            else:
                                if col_type == 'int':
                                    value = str(value)
                                elif col_type == 'UTC-timestamp':
                                    value = datetime.utcfromtimestamp(value).strftime(Constants.DATETIME_FORMAT)
                            if self.search_filter in value:
                                include = True
                                break
                        for i in range(0, len(self.data_column_names)):
                            col_name = self.data_column_names[i]
                            col_type = self.data_column_types[i]
                            value = node.documents[document_key][col_name]
                            if isinstance(value, list):
                                value_str = ""
                                for entry in value:
                                    if col_type == 'int':
                                        value_str = value_str + " " + str(entry)
                                    elif col_type == 'UTC-timestamp':
                                        value_str = value_str + " " + datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT)
                                    else:
                                        value_str = value_str + " " + entry
                                value = value_str
                            else:
                                if col_type == 'int':
                                    value = str(value)
                                elif col_type == 'UTC-timestamp':
                                    value = datetime.utcfromtimestamp(value).strftime(Constants.DATETIME_FORMAT)
                            if self.search_filter in value:
                                include = True
                                break
                    else:
                        include = True
                    if len(self.usefulness_filter) > 0:
                        if node.documents[document_key].usefulness_flag not in self.usefulness_filter:
                            include = False
                    if include:
                        children.append(self.ObjectToItem(self.dataset_data.documents[document_key]))
        return len(children)

    def IsContainer(self, item):
        ''' Return False for Documents and True otherwise for this model.'''
        if not item:
            return True
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Document):
            return False
        return True

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)

        if isinstance(node, Datasets.Dataset) or isinstance(node, Samples.Sample):
            return dv.NullDataViewItem
        else:
            if isinstance(node, Samples.Part) or isinstance(node, Samples.MergedPart):
                parent_children = []
                parent_item = self.ObjectToItem(node.parent)
                self.GetChildren(parent_item, parent_children)
                if item in parent_children:
                    return parent_item
            else:
                parent_children = []
                parent_item = self.ObjectToItem(self.dataset_data)
                self.GetChildren(parent_item, parent_children)
                if item in parent_children:
                    return parent_item
                
                for sample_key in self.samples_data:
                    sample_children = []
                    sample_item = self.ObjectToItem(self.samples_data[sample_key])
                    self.GetChildren(sample_item, sample_children)
                    for part_item in sample_children:
                        part_node = self.ItemToObject(part_item)
                        if isinstance(part_node, Samples.Part):
                            part_children = []
                            self.GetChildren(part_item, part_children)
                            if item in part_children:
                                return part_item
                        elif isinstance(part_node, Samples.MergedPart):
                            for part_item in sample_children:
                                part_node = self.ItemToObject(part_item)
                                if isinstance(part_node, Samples.Part):
                                    part_children = self.GetChildren(part_item, part_children)
                                    if item in part_children:
                                        return part_item
        return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Dataset):
            col_start = len(self.metadata_column_names)+len(self.data_column_names)
            mapper = { 0 : str(node.name)+" / "+str(node.dataset_source)+" / "+str(node.dataset_type),
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.metadata_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.Sample):
            col_start = len(self.metadata_column_names)+len(self.data_column_names)
            mapper = { 0 : repr(node),
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.metadata_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.MergedPart):
            col_start = len(self.metadata_column_names)+len(self.data_column_names)
            mapper = { 0 : repr(node),
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.metadata_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.Part):
            col_start = len(self.metadata_column_names)+len(self.data_column_names)
            mapper = { 0 : repr(node),
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.metadata_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            col_start = len(self.metadata_column_names)+len(self.data_column_names)
            mapper = { col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes),
                       }
            idx = 0
            for field_name in self.metadata_column_names:
                if field_name in node.parent.data[node.key]:
                    value = node.parent.data[node.key][field_name]
                    if self.metadata_column_types[idx] == 'url':
                        segmented_url = value.split("/")
                        value = "<span color=\"#0645ad\"><u>"+segmented_url[len(segmented_url)-1]+"</u></span>"
                    elif self.metadata_column_types[idx] == 'UTC-timestamp':
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
                    elif self.metadata_column_types[idx] == 'int':
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
            for field_name in self.data_column_names:
                if field_name not in self.metadata_column_names and field_name in node.parent.data[node.key]:
                    value = node.parent.data[node.key][field_name]
                    if self.data_column_types[idx-len(self.metadata_column_types)] == 'url':
                        segmented_url = value.split("/")
                        value = "<span color=\"#0645ad\"><u>"+segmented_url[len(segmented_url)-1]+"</u></span>"
                    elif self.data_column_types[idx-len(self.metadata_column_types)] == 'UTC-timestamp':
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
                    elif self.data_column_types[idx-len(self.metadata_column_types)] == 'int':
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

#This view enables displaying documents
class DocumentViewCtrl(dv.DataViewCtrl):
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

    def UpdateColumns(self):
        model = self.GetModel()
        if self.ColumnCount:
            for i in reversed(range(0, self.ColumnCount)):
                self.DeleteColumn(self.GetColumn(i))

        idx = 0
        for field_name in model.metadata_column_names:
            if model.metadata_column_types[idx] == 'int':
                renderer = dv.DataViewTextRenderer(varianttype="long")
            else:
                renderer = dv.DataViewTextRenderer()
                renderer.EnableMarkup()
            column = dv.DataViewColumn(field_name, renderer, idx, align=wx.ALIGN_LEFT)
            self.AppendColumn(column)
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
            idx = idx+1

        for field_name in model.data_column_names:
            if model.data_column_types[idx-len(model.metadata_column_names)] == 'int':
                renderer = dv.DataViewTextRenderer(varianttype="long")
            else:
                renderer = dv.DataViewTextRenderer()
                renderer.EnableMarkup()
            column = dv.DataViewColumn(field_name, renderer, idx, align=wx.ALIGN_LEFT)
            self.AppendColumn(column)
            idx = idx+1

        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.NOTES, text_renderer, idx, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        column1.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        idx = idx+1

        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column2 = dv.DataViewColumn(GUIText.CODES, int_renderer, idx, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        column2.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        idx = idx+1
        
        idx = 0
        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            if idx == 0:
                self.SetExpanderColumn(column)
            idx = idx + 1
        
        columns = self.GetColumns()
        for column in reversed(columns):
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

    def OnShowPopup(self, event):
        logger = logging.getLogger(__name__+".DocumentViewCtrl.OnShowPopup")
        logger.info("Starting")
        menu = wx.Menu()
        menu.Append(1, GUIText.COPY)
        menu.Bind(wx.EVT_MENU, self.OnCopyItems)
        self.PopupMenu(menu)
        logger.info("Finished")

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".DocumentViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)

        main_frame = wx.GetApp().GetTopWindow()

        if isinstance(node, Datasets.Document):
            col = event.GetColumn()
            if col < len(model.metadata_column_names) and model.metadata_column_types[col] == 'url':
                logger.info("Call to access url[%s]", node.url)
                webbrowser.open_new_tab(node.url)
            elif event.GetColumn() == 3:
                #open sample list
                print(node.GetSampleConnections(main_frame.samples, selected=True))
            else:
                CodesGUIs.DocumentDialog(self, node).Show()
        logger.info("Finished")

    def OnCopyItems(self, event):
        logger = logging.getLogger(__name__+".DocumentViewCtrl.OnCopyItems")
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

# This model acts as a bridge between the DocumentConnectionsViewCtrl and the connections.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class DocumentConnectionsViewModel(dv.PyDataViewModel):
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
        if isinstance(node, Datasets.Dataset):
            mapper = { 0 : GUIText.DATASET,
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            if node.url != "":
                node_url = node.url.split("/")
                node_id = node_url[len(node_url)-1]
            else:
                node_id = node.key
            mapper = { 0 : GUIText.DOCUMENT,
                       1 : node_id,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.Sample):
            mapper = { 0 : GUIText.SAMPLE,
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.MergedTopicPart):
            mapper = { 0 : GUIText.MERGED_TOPIC,
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
        elif isinstance(node, Samples.TopicPart):
            mapper = { 0 : GUIText.TOPIC,
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
        elif isinstance(node, Samples.MergedPart):
            mapper = { 0 : GUIText.MERGED_PART,
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.Part):
            mapper = { 0 : GUIText.PART,
                       1 : node.name,
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

#this view enables displaying of connection objects
class DocumentConnectionsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.AssociateModel(model)
        model.DecRef()

        text_renderer = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn(GUIText.TYPE, text_renderer, 0, align=wx.ALIGN_LEFT)
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
        logger = logging.getLogger(__name__+".DocumentConnectionsViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(node, Datasets.Document):
            CodesGUIs.DocumentDialog(main_frame, node).Show()
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

class QuotationsViewModel(dv.PyDataViewModel):
    def __init__(self, codes):
        dv.PyDataViewModel.__init__(self)
        self.codes = codes
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 4

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for code_key in self.codes:
                children.append(self.ObjectToItem(self.codes[code_key]))
            return len(children)

        node = self.ItemToObject(parent)
        if isinstance(node, Codes.Code):
            for subcode_key in node.subcodes:
                children.append(self.ObjectToItem(node.subcodes[subcode_key]))
            for quotation in node.quotations:
                children.append(self.ObjectToItem(quotation))
        return len(children)

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any Code is a container
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            return True
        return False
    
    def HasContainerColumns(self, item):
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            if node.parent != None:
                return self.ObjectToItem(node.parent)
            else:
                return dv.NullDataViewItem
        if isinstance(node, Codes.Quotation):
            return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            mapper = { 0 : node.key,
                       1 : "",
                       2 : "",
                       3 : "",
                       }
            return mapper[col]
        elif isinstance(node, Codes.Quotation):
            mapper = { 0 : str(node.key[1][2]),
                       1 : str(node.key[0][0]),
                       2 : str(node.original_data),
                       3 : str(node.paraphrased_data),
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def SetValue(self, value, item, col):
        '''only allowing updating of key as rest is connected to data retrieved'''
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Quotation):
            if col == 1:
                node.original_data = value
            elif col == 2:
                node.paraphrased_data = value
        return True

class QuotationsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.selected_item = None

        self.AssociateModel(model)
        model.DecRef()

        self.UpdateColumns()

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
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

    def UpdateColumns(self):
        if self.ColumnCount:
            for i in reversed(range(0, self.ColumnCount)):
                self.DeleteColumn(self.GetColumn(i))

        text_renderer = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn(GUIText.ID, text_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        self.SetExpanderColumn(column0)

        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multipledatasets_mode:
            text_renderer = dv.DataViewTextRenderer()
            column1 = dv.DataViewColumn(GUIText.DATASET, text_renderer, 1, align=wx.ALIGN_LEFT)
            self.AppendColumn(column1)

        text_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column2 = dv.DataViewColumn(GUIText.QUOTATIONS, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        text_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column3 = dv.DataViewColumn(GUIText.PARAPHRASES, text_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)

        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        
        

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".QuotationsViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(node, Codes.Code):
            CodesGUIs.CodeDialog(main_frame, node, size=wx.Size(400,400)).Show()
        elif isinstance(node, Codes.Quotation):
            document = main_frame.datasets[node.key[0]].documents[node.key[1]]
            CodesGUIs.DocumentDialog(main_frame, document).Show()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY,
                                    GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        item = event.GetItem()
        model = self.GetModel()
        if item:
            node = model.ItemToObject(item)
            if isinstance(node, Codes.Code):
                add_menuitem = menu.Append(wx.ID_ADD,
                                    GUIText.ADD)
                self.Bind(wx.EVT_MENU, self.OnAddItem, add_menuitem)
                self.selected_item = item
        
        if self.HasSelection():
            contains_quotations = False
            for item in self.GetSelections():
                node = model.ItemToObject(item)
                if isinstance(node, Codes.Quotation):
                    contains_quotations = True
                    break
            if contains_quotations:    
                delete_menuitem = menu.Append(wx.ID_DELETE,
                                              GUIText.DELETE)
                self.Bind(wx.EVT_MENU, self.OnDeleteItems, delete_menuitem)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            document = model.GetValue(item, 0) 
            quotation = model.GetValue(item, 1)
            paraphrase = model.GetValue(item, 2)
            selected_items.append('\t'.join([document, quotation, paraphrase]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
    
    def OnAddItem(self, event):
        model = self.GetModel()
        item = self.selected_item
        node = model.ItemToObject(item)
        if isinstance(node, Codes.Code):
            main_frame = wx.GetApp().GetTopWindow()
            
            dialog = CodesGUIs.CreateQuotationDialog(main_frame, node)

            if dialog.ShowModal() == wx.ID_OK:
                quote_item = dialog.connections_ctrl.GetSelection()
                quote_node = dialog.connections_model.ItemToObject(quote_item)
                if isinstance(quote_node, Datasets.Document):
                    node.quotations.append(Codes.Quotation((quote_node.parent.key, quote_node.key), node))
                    
            model.Cleared()
            self.Expander(None)
    
    def OnDeleteItems(self, event):
        model = self.GetModel()
        if wx.MessageBox(GUIText.CONFIRM_DELETE_QUOTATIONS,
                         GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.YES_NO, self) == wx.YES:
            for item in self.GetSelections():
                node = model.ItemToObject(item)
                if isinstance(node, Codes.Quotation):
                    node.DestroyObject()
            model.Cleared()
            self.Expander(None)
