import logging
import webbrowser
from datetime import datetime

import wx
import wx.dataview as dv

from Common.GUIText import Coding as GUIText
from Common.GUIText import Datasets as DatasetsGUIText
import Common.Constants as Constants
import Common.Objects.Generic as Generic
import Common.Objects.Utilities.Generic as GenericUtilities
import Common.Objects.Codes as Codes
import Common.Objects.GUIs.Codes as CodesGUIs
import Common.Objects.Datasets as Datasets
import Common.Objects.Utilities.Datasets as DatasetsUtilities
import Common.Objects.Samples as Samples

# This model acts as a bridge between the CodesViewCtrl and the codes of the workspace.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class CodesViewModel(dv.PyDataViewModel):
    def __init__(self):
        dv.PyDataViewModel.__init__(self)
        main_frame = wx.GetApp().GetTopWindow()
        self.codes = main_frame.codes
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
        if col == 0 and node.name != value:
            if value == "":
                wx.MessageBox(GUIText.RENAME_CODE_BLANK_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            else:
                node.name = value
                main_frame = wx.GetApp().GetTopWindow()
                main_frame.DocumentsUpdated(self)
                main_frame.CodesUpdated()
        return True
    
    def GetAttr(self, item, col, attr):
        res = super().GetAttr(item, col, attr)
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            bg_colour, fg_colour = GenericUtilities.BackgroundAndForegroundColour(node.colour_rgb)
            attr.SetBackgroundColour(bg_colour)
            attr.SetColour(fg_colour)
        return res

#this view enables displaying of fields for different datasets
class CodesViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.selected_item = None

        self.AssociateModel(model)
        model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column0 = dv.DataViewColumn(GUIText.CODES, editabletext_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column2 = dv.DataViewColumn(GUIText.REFERENCES, int_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        for i in range(0, len(self.Columns)):
            column = self.Columns[i]
            column.SetSortable(True)
            column.SetReorderable(True)
            column.SetResizeable(True)
        
        self.Expander(None)

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

    def Expander(self, item, autosize_flg=True):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child, False)
        if autosize_flg:
            self.AutoSize()
    
    def AutoSize(self):
        for column in self.GetColumns():
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

    def OnDrag(self, event):
        item = event.GetItem()
        if item:
            self.drag_node = self.GetModel().ItemToObject(item)
            key = self.drag_node.key
            obj = wx.TextDataObject()
            obj.SetText(key)
            event.SetDataObject(obj)
    
    def OnDropPossible(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return True
        else:
            node = self.GetModel().ItemToObject(item)
            if node == self.drag_node:
                return False
            else:
                return True

    def OnDrop(self, event):
        item = event.GetItem()
        main_frame = wx.GetApp().GetTopWindow()
        model = self.GetModel()
        if item.IsOk():
            node = model.ItemToObject(item)
            if node != self.drag_node and node not in self.drag_node.GetDescendants():
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
        main_frame.CodesUpdated()
        
    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        if item:
            model = self.GetModel()
            node = model.ItemToObject(item)
            main_frame = wx.GetApp().GetTopWindow()
            if node.key not in main_frame.code_dialogs:
                main_frame.code_dialogs[node.key] = CodesGUIs.CodeDialog(main_frame, node, size=wx.Size(400,400))
            main_frame.code_dialogs[node.key].Show()
            main_frame.code_dialogs[node.key].SetFocus()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY, GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        if isinstance(self.GetModel(), CodesViewModel):
            self.selected_item = event.GetItem()
            if self.selected_item:
                change_colour_menuitem = menu.Append(wx.ID_ANY, GUIText.CHANGE_COLOUR)
                self.Bind(wx.EVT_MENU, self.OnChangeColour, change_colour_menuitem) 
            add_code_menuitem = menu.Append(wx.ID_ADD, GUIText.ADD_NEW_CODE)
            self.Bind(wx.EVT_MENU, self.OnAddCode, add_code_menuitem)
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
            selected_items.append('\t'.join([name, notes, str(num_connections)]).strip())
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
        ok_button = wx.FindWindowById(wx.ID_OK, add_dialog)
        ok_button.SetLabel(GUIText.ADD_NEW_CODE)
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                else:
                    new_code = Codes.Code(new_name)
                    main_frame.codes[new_code.key] = new_code
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
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
        ok_button = wx.FindWindowById(wx.ID_OK, add_dialog)
        ok_button.SetLabel(GUIText.ADD_NEW_SUBCODE)
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                else:
                    new_subcode = Codes.Code(new_name, parent=node)
                    node.subcodes[new_subcode.key] = new_subcode
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
            else:
                break
        logger.info("Finished")

    def OnDeleteCodes(self, event):
        logger = logging.getLogger(__name__+".CodesViewCtrl.OnDeleteCodes")
        logger.info("Starting")
        #confirmation
        confirm_dialog = wx.MessageDialog(self, GUIText.CONFIRM_DELETE_CODES,
                                          GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        confirm_dialog.SetOKLabel(GUIText.DELETE_CODES)
        if confirm_dialog.ShowModal() == wx.ID_OK:
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

    def OnChangeColour(self, event):
        logger = logging.getLogger(__name__+".CodesViewCtrl.OnChangeColour")
        logger.info("Starting")

        model = self.GetModel() 
        item = self.selected_item
        node = model.ItemToObject(item)

        cur_colour = wx.Colour(node.colour_rgb[0], node.colour_rgb[1], node.colour_rgb[2])

        cur_colour_data = wx.ColourData()
        cur_colour_data.SetColour(cur_colour)

        colour_dlg = wx.ColourDialog(self, cur_colour_data)
        
        if colour_dlg.ShowModal() == wx.ID_OK:
            new_colour_data = colour_dlg.GetColourData()
            new_colour = new_colour_data.GetColour()
            node.colour_rgb = (new_colour.Red(), new_colour.Green(), new_colour.Blue(),)
            main_frame = wx.GetApp().GetTopWindow()
            main_frame.CodesUpdated()
            self.UnselectAll()
        logger.info("Finished")

# This model acts as a bridge between the ObjectCodesViewCtrl and the codes of an object.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class ObjectCodesViewModel(CodesViewModel):
    def __init__(self, obj):
        CodesViewModel.__init__(self)
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
                main_frame.DocumentsUpdated(self)
                main_frame.CodesUpdated()
            elif  node.key in self.obj.codes:
                self.obj.codes.remove(node.key)
                self.obj.last_changed_dt = datetime.now()
                node.RemoveConnection(self.obj)
                main_frame = wx.GetApp().GetTopWindow()
                main_frame.DocumentsUpdated(self)
                main_frame.CodesUpdated()
        elif col == 1 and node.name != value:
            if value == "":
                wx.MessageBox(GUIText.RENAME_CODE_BLANK_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            else:
                node.name = value
                main_frame = wx.GetApp().GetTopWindow()
                main_frame.DocumentsUpdated(self)
                main_frame.CodesUpdated()
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
        column1 = dv.DataViewColumn(GUIText.CODES, editabletext_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_renderer = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column3 = dv.DataViewColumn(GUIText.REFERENCES, int_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)

        for i in range(0, len(self.Columns)):
            column = self.Columns[i]
            column.SetSortable(True)
            column.SetReorderable(True)
            column.SetResizeable(True)

        self.Expander(None)

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

    def Expander(self, item, autosize_flg=True):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)
        if autosize_flg:
            self.AutoSize()
        
    def AutoSize(self):
        for column in self.GetColumns():
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

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
            return True
        else:
            node = self.GetModel().ItemToObject(item)
            if node == self.drag_node:
                return False
            else:
                return True

    def OnDrop(self, event):
        item = event.GetItem()
        main_frame = wx.GetApp().GetTopWindow()
        model = self.GetModel()
        if item.IsOk():
            node = model.ItemToObject(item)
            if node != self.drag_node and node not in self.drag_node.GetDescendants():
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
        main_frame.CodesUpdated()
        wx.PostEvent(self.GetEventHandler(), dv.DataViewEvent(dv.EVT_DATAVIEW_SELECTION_CHANGED.typeId, self, dv.DataViewItem()))

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        if item.IsOk():
            model = self.GetModel()
            node = model.ItemToObject(item)
            main_frame = wx.GetApp().GetTopWindow()
            if node.key not in main_frame.code_dialogs:
                main_frame.code_dialogs[node.key] = CodesGUIs.CodeDialog(main_frame, node, size=wx.Size(400,400))
            main_frame.code_dialogs[node.key].Show()
            main_frame.code_dialogs[node.key].SetFocus()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY, GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        if isinstance(self.GetModel(), CodesViewModel):
            self.selected_item = event.GetItem()
            if self.selected_item.IsOk():
                change_colour_menuitem = menu.Append(wx.ID_ANY, GUIText.CHANGE_COLOUR)
                self.Bind(wx.EVT_MENU, self.OnChangeColour, change_colour_menuitem) 
            add_code_menuitem = menu.Append(wx.ID_ADD, GUIText.ADD_NEW_CODE)
            self.Bind(wx.EVT_MENU, self.OnAddCode, add_code_menuitem)
            if self.selected_item.IsOk():
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
            included = str(model.GetValue(item, 0))
            name = model.GetValue(item, 1)
            notes = model.GetValue(item, 2)
            num_connections = str(model.GetValue(item, 3))
            selected_items.append('\t'.join([included, name, notes, num_connections]).strip())
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
        ok_button = wx.FindWindowById(wx.ID_OK, add_dialog)
        ok_button.SetLabel(GUIText.ADD_NEW_CODE)
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                else:
                    new_code = Codes.Code(new_name)
                    main_frame.codes[new_code.key] = new_code
                    model.obj.AppendCode(new_code.key)
                    main_frame.codes[new_code.key].AddConnection(model.obj)
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
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
        ok_button = wx.FindWindowById(wx.ID_OK, add_dialog)
        ok_button.SetLabel(GUIText.ADD_NEW_SUBCODE)
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_CODE_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                else:
                    new_subcode = Codes.Code(new_name, parent=node)
                    node.subcodes[new_subcode.key] = new_subcode
                    model.obj.AppendCode(new_subcode.key)
                    node.subcodes[new_subcode.key].AddConnection(model.obj)
                    model.Cleared()
                    self.Expander(None)
                    main_frame.CodesUpdated()
                    break
            else:
                break
        logger.info("Finished")

    def OnDeleteCodes(self, event):
        logger = logging.getLogger(__name__+".ObjectCodesViewCtrl.OnDeleteCodes")
        logger.info("Starting")
        #confirmation
        confirm_dialog = wx.MessageDialog(self, GUIText.CONFIRM_DELETE_CODES,
                                          GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        confirm_dialog.SetOKLabel(GUIText.DELETE_CODES)
        if confirm_dialog.ShowModal() == wx.ID_OK:
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
            wx.PostEvent(self.GetEventHandler(), dv.DataViewEvent(dv.EVT_DATAVIEW_SELECTION_CHANGED.typeId, self, dv.DataViewItem()))
        
        logger.info("Finished")
        

    def OnChangeColour(self, event):
        logger = logging.getLogger(__name__+".CodesViewCtrl.OnChangeColour")
        logger.info("Starting")

        model = self.GetModel() 
        item = self.selected_item
        node = model.ItemToObject(item)

        cur_colour = wx.Colour(node.colour_rgb[0], node.colour_rgb[1], node.colour_rgb[2])

        cur_colour_data = wx.ColourData()
        cur_colour_data.SetColour(cur_colour)

        colour_dlg = wx.ColourDialog(self, cur_colour_data)
        
        if colour_dlg.ShowModal() == wx.ID_OK:
            new_colour_data = colour_dlg.GetColourData()
            new_colour = new_colour_data.GetColour()
            node.colour_rgb = (new_colour.Red(), new_colour.Green(), new_colour.Blue(),)
            main_frame = wx.GetApp().GetTopWindow()
            main_frame.CodesUpdated()
            if self:
                self.UnselectAll()
                wx.PostEvent(self.GetEventHandler(), dv.DataViewEvent(dv.EVT_DATAVIEW_SELECTION_CHANGED.typeId, self, dv.DataViewItem()))
        logger.info("Finished")

# This model acts as a bridge between the CodeConnectionsViewCtrl and the codes.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
#TODO need to rework ViewModel to show dynamic label columns instead of just document ids
class CodeConnectionsViewModel(dv.PyDataViewModel):
    def __init__(self, code):
        dv.PyDataViewModel.__init__(self)
        self.code = code
        main_frame = wx.GetApp().GetTopWindow()
        self.datasets = main_frame.datasets
        self.samples = main_frame.samples

        self.connection_objs = {}

        self.UseWeakRefs(True)
    
    def UpdateColumnNames(self):
        if hasattr(self.dataset, 'label_fields'):
            if len(self.dataset.label_fields) == 0:
                self.label_column_names.append('id')
                self.label_column_types.append('string')
            else:
                for key in self.dataset.label_fields:
                    field = self.dataset.label_fields[key]
                    self.label_column_names.append(field.name)
                    self.label_column_types.append(field.field_type)
        else:
            if self.dataset.dataset_source == "Reddit":
                self.label_column_names.append('url')
                self.label_column_types.append('url')
                if self.dataset.dataset_type == "discussion" or self.dataset.dataset_type == "submission":
                    self.label_column_names.append('title')
                    self.label_column_types.append('string')
                elif self.dataset.dataset_type == "comment":
                    self.label_column_names.append('body')
                    self.label_column_types.append('string')
            else:
                self.label_column_names.append('id')
                self.label_column_types.append('string')
        
        self.column_names.clear()
        self.column_names.extend([GUIText.NOTES])

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        objs = self.code.GetConnections(self.datasets, self.samples)
        objs_dict = dict(zip([obj.key for obj in objs], objs))
        if not parent:
            for dataset_key in self.datasets:
                include_flag = False
                for doc_key in self.datasets[dataset_key].selected_documents:
                    if doc_key in objs_dict:
                        include_flag = True
                        break
                if include_flag:
                    child_item = self.ObjectToItem(self.datasets[dataset_key])
                    children.append(child_item)
            for sample_key in self.samples:
                include_flag = False
                for doc_key in self.samples[sample_key].selected_documents:
                    if doc_key in objs_dict:
                        include_flag = True
                        break
                if include_flag:
                    child_item = self.ObjectToItem(self.samples[sample_key])
                    children.append(child_item)
            return len(children)
        node = self.ItemToObject(parent)
        if isinstance(node, Datasets.Dataset) or isinstance(node, Samples.Sample):
            for key in objs_dict:
                if key in node.selected_documents:
                    connection_key = (node.key, objs_dict[key])
                    if connection_key not in self.connection_objs:
                        self.connection_objs[connection_key] = Generic.Connection(node, objs_dict[key])
                    children.append(self.ObjectToItem(self.connection_objs[connection_key]))
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
        if isinstance(node, Datasets.Dataset) or isinstance(node, Samples.Sample):
            return dv.NullDataViewItem
        elif isinstance(node, Generic.Connection):
            return self.ObjectToItem(node.parent)

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Dataset):
            mapper = { 0 : node.name,
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Samples.Sample):
            mapper = { 0 : node.name,
                       1 : "",
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        elif isinstance(node, Generic.Connection):
            node = node.obj
            if node.url != "":
                segmented_url = node.url.split("/")
                if segmented_url[len(segmented_url)-1] != '':
                    node_id = segmented_url[len(segmented_url)-1]
                else:
                    node_id = segmented_url[len(segmented_url)-2]
            else:
                node_id = node.doc_id[2]
            mapper = { 0 : "",
                       1 : str(node_id),
                       2 : "\U0001F6C8" if node.notes != "" else "",
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

#this view enables displaying of fields for different datasets
#TODO need to rework ViewModel to show dynamic label columns instead of just document ids
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
        
        self.Expander(None)

        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

    def Expander(self, item, autosize_flg=True):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child, False)
        if autosize_flg:
            self.AutoSize()
        
    def AutoSize(self):
        for column in self.GetColumns():
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".CodeConnectionsViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(node, Generic.Connection):
            node = node.obj
            if node.key not in main_frame.document_dialogs:
                main_frame.document_dialogs[node.key] = CodesGUIs.DocumentDialog(main_frame, node)
            main_frame.document_dialogs[node.key].Show()
            main_frame.document_dialogs[node.key].SetFocus()
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
    def __init__(self, dataset):
        dv.PyDataViewModel.__init__(self)
        self.dataset = dataset
        main_frame = wx.GetApp().GetTopWindow()
        self.samples = main_frame.samples
        self.UseWeakRefs(True)

        self.search_filter = ""
        self.usefulness_filter = []
        self.samples_filter = []

        self.label_column_names = []
        self.label_column_types = []
        self.data_column_names = []
        self.data_column_types = []
        self.column_names = []
        self.UpdateColumnNames()

    def UpdateColumnNames(self):
        self.label_column_names.clear()
        self.label_column_types.clear()
        if len(self.dataset.label_fields) == 0:
            self.label_column_names.append('id')
            self.label_column_types.append('string')
        else:
            for key in self.dataset.label_fields:
                field = self.dataset.label_fields[key]
                self.label_column_names.append(field.name)
                self.label_column_types.append(field.fieldtype)

        self.data_column_names.clear()
        self.data_column_types.clear()
        for key in self.dataset.computational_fields:
            field = self.dataset.computational_fields[key]
            if field.name not in self.label_column_names and field.name not in self.data_column_names:
                self.data_column_names.append(field.name)
                self.data_column_types.append(field.fieldtype)

        self.column_names.clear()
        self.column_names.extend([GUIText.NOTES, GUIText.CODES])

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return len(self.label_column_names) +  len(self.data_column_names) + len(self.column_names)

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            possible_children = []
            subchildren = []
            if 'dataset' in self.samples_filter: 
                item = self.ObjectToItem(self.dataset)
                dataset_children = []
                self.GetChildren(item, dataset_children)
                if len(dataset_children) > 0:
                    subchildren.extend(dataset_children)
                    possible_children.append(item)
            for key in self.samples:
                if key in self.samples_filter:
                    item = self.ObjectToItem(self.samples[key])
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
                    for i in range(0, len(self.label_column_names)):
                        col_name = self.label_column_names[i]
                        col_type = self.label_column_types[i]
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
                        for i in range(0, len(self.label_column_names)):
                            col_name = self.label_column_names[i]
                            col_type = self.label_column_types[i]
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
                        if self.dataset.documents[document_key].usefulness_flag not in self.usefulness_filter:
                            include = False
                    if include:
                        children.append(self.ObjectToItem(self.dataset.documents[document_key]))
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
                parent_item = self.ObjectToItem(self.dataset)
                self.GetChildren(parent_item, parent_children)
                if item in parent_children:
                    return parent_item
                
                for sample_key in self.samples:
                    sample_children = []
                    sample_item = self.ObjectToItem(self.samples[sample_key])
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
                                    part_children = []
                                    self.GetChildren(part_item, part_children)
                                    if item in part_children:
                                        return part_item
        return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, Datasets.Dataset):
            col_start = len(self.label_column_names)+len(self.data_column_names)
            dataset_type = DatasetsUtilities.DatasetTypeLabel(node)
            mapper = { 0 : str(node.name)+" / "+str(node.dataset_source)+" / "+str(dataset_type),
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.label_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.Sample):
            col_start = len(self.label_column_names)+len(self.data_column_names)
            mapper = { 0 : node.name,
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.label_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.MergedPart):
            col_start = len(self.label_column_names)+len(self.data_column_names)
            mapper = { 0 : repr(node),
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.label_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Samples.Part):
            col_start = len(self.label_column_names)+len(self.data_column_names)
            mapper = { 0 : repr(node),
                       col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes)
                       }
            for i in range(1, len(self.label_column_names)+len(self.data_column_names)):
                mapper[i] = ""
            return mapper[col]
        elif isinstance(node, Datasets.Document):
            col_start = len(self.label_column_names)+len(self.data_column_names)
            mapper = { col_start+0 : "\U0001F6C8" if node.notes != "" else "",
                       col_start+1 : len(node.codes),
                       }
            idx = 0
            for field_name in self.label_column_names:
                if field_name in node.parent.data[node.doc_id]:
                    value = node.parent.data[node.doc_id][field_name]
                    if self.label_column_types[idx] == 'url':
                        segmented_url = value.split("/")
                        if segmented_url[len(segmented_url)-1] != '':
                            segment_id = segmented_url[len(segmented_url)-1]
                        else:
                            segment_id = segmented_url[len(segmented_url)-2]
                        value = "<span color=\"#0645ad\"><u>"+segment_id+"</u></span>"
                    elif self.label_column_types[idx] == 'UTC-timestamp':
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
                    elif self.label_column_types[idx] == 'int':
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
                if field_name not in self.label_column_names and field_name in node.parent.data[node.doc_id]:
                    value = node.parent.data[node.doc_id][field_name]
                    if self.data_column_types[idx-len(self.label_column_types)] == 'url':
                        segmented_url = value.split("/")
                        if segmented_url[len(segmented_url)-1] != '':
                            segment_id = segmented_url[len(segmented_url)-1]
                        else:
                            segment_id = segmented_url[len(segmented_url)-2]
                        value = "<span color=\"#0645ad\"><u>"+segment_id+"</u></span>"
                    elif self.data_column_types[idx-len(self.label_column_types)] == 'UTC-timestamp':
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
                    elif self.data_column_types[idx-len(self.label_column_types)] == 'int':
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

    def Expander(self, item, autosize_flg=True):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child, False)
        if autosize_flg:
            self.AutoSize()
    
    def AutoSize(self, width=None):
        if width is None:
            remaining_width = self.GetSize().GetWidth()*0.98
        else:
            remaining_width = width*0.98
        col_count = self.GetColumnCount()-2
        column = self.GetColumn(col_count)
        column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        remaining_width = remaining_width - column.GetWidth()
        column = self.GetColumn(col_count+1)
        col_width = column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
        remaining_width = remaining_width - column.GetWidth()
        col = 0
        for column in self.GetColumns():
            if col < col_count:
                column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
                col_width = column.GetWidth()
                if col_width > remaining_width/(col_count-col):
                    col_width = remaining_width/(col_count-col)
                    column.SetWidth(col_width)
                remaining_width = remaining_width - col_width
            else:
                column.SetWidth(wx.COL_WIDTH_AUTOSIZE)
            col = col+1

    def UpdateColumns(self):
        model = self.GetModel()
        self.ClearColumns()

        idx = 0
        for field_name in model.label_column_names:
            if model.label_column_types[idx] == 'int':
                renderer = dv.DataViewTextRenderer(varianttype="long")
            elif model.label_column_types[idx] == 'url':
                renderer = dv.DataViewTextRenderer()
                renderer.EnableMarkup()
            else:
                renderer = dv.DataViewTextRenderer()
            column = dv.DataViewColumn(field_name, renderer, idx, align=wx.ALIGN_LEFT)
            self.AppendColumn(column)
            idx = idx+1

        for field_name in model.data_column_names:
            if model.data_column_types[idx-len(model.label_column_names)] == 'int':
                renderer = dv.DataViewTextRenderer(varianttype="long")
            elif model.data_column_types[idx-len(model.label_column_names)] == 'url':
                renderer = dv.DataViewTextRenderer()
                renderer.EnableMarkup()
            else:
                renderer = dv.DataViewTextRenderer()
            column = dv.DataViewColumn(field_name, renderer, idx, align=wx.ALIGN_LEFT)
            self.AppendColumn(column)
            idx = idx+1

        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.NOTES, text_renderer, idx, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        idx = idx+1

        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column2 = dv.DataViewColumn(GUIText.CODES, int_renderer, idx, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        idx = idx+1
        
        idx = 0
        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            if idx == 0:
                self.SetExpanderColumn(column)
            idx = idx + 1
        
        self.Expander(None)

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
            if col < len(model.label_column_names) and model.label_column_types[col] == 'url':
                logger.info("Call to access url[%s]", node.url)
                webbrowser.open_new_tab(node.url)
            elif event.GetColumn() == 3:
                #open sample list
                print(node.GetSampleConnections(main_frame.samples, selected=True))
            else:
                if node.key not in main_frame.document_dialogs:
                    main_frame.document_dialogs[node.key] = CodesGUIs.DocumentDialog(main_frame, node)
                main_frame.document_dialogs[node.key].Show()
                main_frame.document_dialogs[node.key].SetFocus()
        logger.info("Finished")

    def OnCopyItems(self, event):
        logger = logging.getLogger(__name__+".DocumentViewCtrl.OnCopyItems")
        logger.info("Starting")
        selected_items = []
        model = self.GetModel()
        for row in self.GetSelections():
            line = ''
            for col in range(0, model.label_column_names):
                line = line + str(model.GetValue(row, col)) + '\t'
            selected_items.append(line.strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
        logger.info("Finished")

# This model acts as a bridge between the CodesViewCtrl and the codes of the workspace.
# This model provides these data columns:
#   0. Node:   string
#   1. Code:   string
#   2. Notes: string
#   3. Number of Codes:  int
class ThemesViewModel(dv.PyDataViewModel):
    def __init__(self, theme=None):
        dv.PyDataViewModel.__init__(self)
        main_frame = wx.GetApp().GetTopWindow()
        self.theme = theme
        if theme == None:
            self.themes = main_frame.themes
        else:
            self.themes = {theme.key: theme}
        self.codes = main_frame.codes

        self.connection_objs = {}
        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 4

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            if self.theme != None:
                theme = self.theme
                for subtheme_key in theme.subthemes:
                    child_key = (subtheme_key,)
                    if child_key not in self.connection_objs:
                        self.connection_objs[child_key] = Generic.Connection(None, theme.subthemes[subtheme_key])
                    children.append(self.ObjectToItem(self.connection_objs[child_key]))
                for code in self.theme.GetCodes(self.codes):
                    child_key = (code.key,)
                    if child_key not in self.connection_objs:
                        self.connection_objs[child_key] = Generic.Connection(None, code)
                    children.append(self.ObjectToItem(self.connection_objs[child_key]))
            else:
                for theme_key in self.themes:
                    if isinstance(self.themes[theme_key], Codes.Theme):
                        child_key = (theme_key,)
                        if child_key not in self.connection_objs:
                            self.connection_objs[child_key] = Generic.Connection(None, self.themes[theme_key])
                        children.append(self.ObjectToItem(self.connection_objs[child_key]))
        # Otherwise we'll fetch the python object associated with the parent
        # item and make DV items for each of it's child objects.
        else:
            node = self.ItemToObject(parent)
            if isinstance(node, Generic.Connection) and isinstance(node.obj, Codes.Theme):
                node_key = node.GetKey()
                for subtheme_key in node.obj.subthemes:
                    child_key = (node_key, subtheme_key,)
                    if child_key not in self.connection_objs:
                        self.connection_objs[child_key] = Generic.Connection(node, node.obj.subthemes[subtheme_key])
                    children.append(self.ObjectToItem(self.connection_objs[child_key]))
                for code in node.obj.GetCodes(self.codes):
                    child_key = (node_key, code.key,)
                    if child_key not in self.connection_objs:
                        self.connection_objs[child_key] = Generic.Connection(node, code)
                    children.append(self.ObjectToItem(self.connection_objs[child_key]))
        return len(children)

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any node that has a list of lower nodes
        node = self.ItemToObject(item)
        if isinstance(node.obj, Codes.Theme):
            return True
        return False
    
    def HasContainerColumns(self, item):
        if not item:
            return False
        node = self.ItemToObject(item)
        if isinstance(node.obj, Codes.Theme):
            return True
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Generic.Connection):
            if node.parent != None:
                return self.ObjectToItem(node.parent)
            else:
                return dv.NullDataViewItem

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node.obj, Codes.Theme):
            mapper = { 0 : node.obj.name,
                       1 : GUIText.THEME,
                       2 : "\U0001F6C8" if node.obj.notes != "" else "",
                       3 : len(node.obj.code_keys),
                       }
            return mapper[col]
        elif isinstance(node.obj, Codes.Code):
            mapper = { 0 : node.obj.name,
                       1 : GUIText.CODE,
                       2 : "\U0001F6C8" if node.obj.notes != "" else "",
                       3 : 1,
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")

    def SetValue(self, value, item, col):
        '''only allowing updating of key as rest is connected to data retrieved'''
        node = self.ItemToObject(item)
        if col == 0 and isinstance(node.obj, Codes.Theme) and node.obj.name != value:
            if value == "":
                wx.MessageBox(GUIText.RENAME_THEME_BLANK_ERROR,
                              GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            else:
                node.obj.name = value
        return True
    
    def GetAttr(self, item, col, attr):
        res = super().GetAttr(item, col, attr)
        node = self.ItemToObject(item)
        if isinstance(node.obj, Codes.Theme) or isinstance(node.obj, Codes.Code):
            bg_colour, fg_colour = GenericUtilities.BackgroundAndForegroundColour(node.obj.colour_rgb)
            attr.SetBackgroundColour(bg_colour)
            attr.SetColour(fg_colour)
        return res
    
    def Cleared(self):
        self.connection_objs.clear()
        res = super().Cleared()
        return res

#this view enables displaying of fields for different datasets
class ThemesViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES, theme=None):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.theme = theme
        self.selected_item = None

        self.AssociateModel(model)
        model.DecRef()

        editabletext_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        column0 = dv.DataViewColumn(GUIText.NAMES, editabletext_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.TYPE, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_renderer = dv.DataViewTextRenderer()
        column2 = dv.DataViewColumn(GUIText.NOTES, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)
        int_renderer = dv.DataViewTextRenderer(varianttype="long")
        column3 = dv.DataViewColumn(GUIText.NUMBER_OF_CODES, int_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)

        for i in range(0, len(self.Columns)):
            column = self.Columns[i]
            column.SetSortable(True)
            column.SetReorderable(True)
            column.SetResizeable(True)
        
        self.Expander(None)

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

    def Expander(self, item, autosize_flg=True):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child, False)
        if autosize_flg:
            self.AutoSize()
    
    def AutoSize(self):
        for column in self.GetColumns():
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

    def OnDrag(self, event):
        item = event.GetItem()
        if item:
            self.drag_node = self.GetModel().ItemToObject(item)
            key = self.drag_node.GetKey()
            obj = wx.TextDataObject()
            obj.SetText(str(key))
            event.SetDataObject(obj)
    
    def OnDropPossible(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return True
        else:
            node = self.GetModel().ItemToObject(item)
            if node == self.drag_node:
                return False
            else:
                return True

    def OnDrop(self, event):
        item = event.GetItem()
        main_frame = wx.GetApp().GetTopWindow()
        model = self.GetModel()
        if item.IsOk():
            node = model.ItemToObject(item)
            if node != self.drag_node and isinstance(node.obj, Codes.Theme):
                if isinstance(self.drag_node.obj, Codes.Theme) and node not in self.drag_node.obj.GetDescendants():
                    if self.drag_node.obj.parent is not None:
                        del self.drag_node.obj.parent.subthemes[self.drag_node.obj.key]
                    else:
                        del main_frame.themes[self.drag_node.obj.key]
                    node.obj.subthemes[self.drag_node.obj.key] = self.drag_node.obj
                    self.drag_node.obj.parent = node.obj
                if isinstance(self.drag_node.obj, Codes.Code) and self.drag_node.obj.key not in node.obj.code_keys:
                    node.obj.code_keys.append(self.drag_node.obj.key)
        else:
            if isinstance(self.drag_node.obj, Codes.Theme):
                if self.drag_node.obj.parent is not None:
                    del self.drag_node.obj.parent.subthemes[self.drag_node.obj.key]
                else:
                    if self.theme == None:
                        del main_frame.themes[self.drag_node.obj.key]
                    else:
                        del self.drag_node.obj.parent.subthemes[self.drag_node.obj.key]
                if self.theme == None:
                    main_frame.themes[self.drag_node.obj.key] = self.drag_node.obj
                else:
                    self.theme.subthemes[self.drag_node.obj.key] = self.drag_node.obj
                self.drag_node.obj.parent = None
            if self.theme != None and isinstance(self.drag_node.obj, Codes.Code) and self.drag_node.obj.key not in self.theme.code_keys:
                self.theme.code_keys.append(self.drag_node.obj.key)
        self.drag_node = None
        model.Cleared()
        self.Expander(None)
        main_frame.ThemesUpdated()

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".ThemesViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        if item:
            model = self.GetModel()
            node = model.ItemToObject(item)
            main_frame = wx.GetApp().GetTopWindow()
            if isinstance(node, Generic.Connection) and isinstance(node.obj, Codes.Code):
                if node.obj.key not in main_frame.code_dialogs:
                    main_frame.code_dialogs[node.obj.key] = CodesGUIs.CodeDialog(main_frame, node.obj, size=wx.Size(400,400))
                main_frame.code_dialogs[node.obj.key].Show()
                main_frame.code_dialogs[node.obj.key].SetFocus()
            elif isinstance(node, Generic.Connection) and isinstance(node.obj, Codes.Theme):
                if node.obj.key not in main_frame.theme_dialogs:
                    main_frame.theme_dialogs[node.obj.key] = CodesGUIs.ThemeDialog(main_frame, node.obj, size=wx.Size(400,400))
                main_frame.theme_dialogs[node.obj.key].Show()
                main_frame.theme_dialogs[node.obj.key].SetFocus()
        logger.info("Finished")

    def OnShowPopup(self, event):
        menu = wx.Menu()
        copy_menuitem = menu.Append(wx.ID_COPY, GUIText.COPY)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, copy_menuitem)
        menu.AppendSeparator()
        if isinstance(self.GetModel(), ThemesViewModel):
            model = self.GetModel()
            multiple_selected = False
            has_themes_selected = False
            has_codes_selected = False
            if self.HasSelection():
                count = 0
                self.selected_item = None
                for item in self.GetSelections():
                    node = model.ItemToObject(item)
                    count = count + 1
                    if isinstance(node.obj, Codes.Theme):
                        has_themes_selected = True
                    if isinstance(node.obj, Codes.Code):
                        has_codes_selected = True
                
                if count == 1:
                    self.selected_item = event.GetItem()
                elif count > 1:
                    multiple_selected = True
                    self.selected_item = None

            add_theme_menuitem = menu.Append(wx.ID_ADD, GUIText.ADD_NEW_THEME)
            self.Bind(wx.EVT_MENU, self.OnAddTheme, add_theme_menuitem)
            if not multiple_selected and has_themes_selected:
                add_subtheme_menuitem = menu.Append(wx.ID_ANY, GUIText.ADD_NEW_SUBTHEME)
                self.Bind(wx.EVT_MENU, self.OnAddSubTheme, add_subtheme_menuitem)
            if has_themes_selected:
                delete_codes_menuitem = menu.Append(wx.ID_ANY, GUIText.DELETE_THEMES)
                self.Bind(wx.EVT_MENU, self.OnDeleteThemes, delete_codes_menuitem)
            menu.AppendSeparator()
            if (has_themes_selected or has_codes_selected) and not multiple_selected:
                change_colour_menuitem = menu.Append(wx.ID_ANY, GUIText.CHANGE_COLOUR)
                self.Bind(wx.EVT_MENU, self.OnChangeColour, change_colour_menuitem)
                menu.AppendSeparator()
            if not multiple_selected and (has_themes_selected or self.theme != None):
                add_code_menuitem = menu.Append(wx.ID_ANY, GUIText.INCLUDE_CODES)
                self.Bind(wx.EVT_MENU, self.OnIncludeCodes, add_code_menuitem)
            if has_codes_selected:
                add_code_menuitem = menu.Append(wx.ID_ANY, GUIText.REMOVE_CODES)
                self.Bind(wx.EVT_MENU, self.OnRemoveCodes, add_code_menuitem)
        self.PopupMenu(menu)

    def OnCopyItems(self, event):
        selected_items = []
        model = self.GetModel()
        for item in self.GetSelections():
            obj_name = model.GetValue(item, 0)
            obj_type = model.GetValue(item, 1)
            notes = model.GetValue(item, 2)
            num_codes = model.GetValue(item, 3)
            selected_items.append('\t'.join([obj_name, obj_type, notes, str(num_codes)]).strip())
        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selected_items))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
    
    #bring up menu on right click
    def OnAddTheme(self, event):
        logger = logging.getLogger(__name__+".ThemesViewCtrl.OnAddTheme")
        logger.info("Starting")
        new_name = None
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()
        add_dialog = wx.TextEntryDialog(main_frame, message=GUIText.ADD_NEW_THEME, caption=GUIText.NEW_THEME)
        ok_button = wx.FindWindowById(wx.ID_OK, add_dialog)
        ok_button.SetLabel(GUIText.ADD_NEW_THEME)
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_THEME_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                else:
                    if self.theme != None:
                        new_subtheme = Codes.Theme(new_name, parent = self.theme)
                        self.theme.subthemes[new_subtheme.key] = new_subtheme
                    else:
                        new_theme = Codes.Theme(new_name)
                        main_frame.themes[new_theme.key] = new_theme
                    model.Cleared()
                    self.Expander(None)
                    main_frame.ThemesUpdated()
                    break
            else:
                break
        logger.info("Finished")
    
    #bring up menu on right click
    def OnAddSubTheme(self, event):
        logger = logging.getLogger(__name__+".ThemesViewCtrl.OnAddSubTheme")
        logger.info("Starting")
        new_name = None
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()
        item = self.selected_item
        node = model.ItemToObject(item)
        add_dialog = wx.TextEntryDialog(main_frame, message=GUIText.ADD_NEW_SUBTHEME, caption=GUIText.NEW_SUBTHEME)
        ok_button = wx.FindWindowById(wx.ID_OK, add_dialog)
        ok_button.SetLabel(GUIText.ADD_NEW_SUBTHEME)
        while new_name is None:
            rc = add_dialog.ShowModal()
            if rc == wx.ID_OK:
                new_name = add_dialog.GetValue()
                if new_name == '':
                    wx.MessageBox(GUIText.NEW_THEME_BLANK_ERROR,
                                  GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                    new_name = None
                else:
                    new_subtheme = Codes.Theme(new_name, parent=node.obj)
                    node.obj.subthemes[new_subtheme.key] = new_subtheme
                    model.Cleared()
                    self.Expander(None)
                    main_frame.ThemesUpdated()
                    break
            else:
                break
        logger.info("Finished")

    def OnDeleteThemes(self, event):
        logger = logging.getLogger(__name__+".ThemesViewCtrl.OnDeleteCodes")
        logger.info("Starting")
        #confirmation
        confirm_dialog = wx.MessageDialog(self, GUIText.CONFIRM_DELETE_THEME,
                                          GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        confirm_dialog.SetOKLabel(GUIText.DELETE_THEMES)
        if confirm_dialog.ShowModal() == wx.ID_OK:
            model = self.GetModel() 
            main_frame = wx.GetApp().GetTopWindow()
            delete_themes = []
            for item in self.GetSelections():
                node = model.ItemToObject(item)
                if isinstance(node.obj, Codes.Theme):
                    delete_themes.append(node.obj)
            
            for theme in delete_themes:
                def DeleteTheme(theme):
                    for subtheme_key in list(theme.subthemes.keys()):
                        DeleteTheme(theme.subthemes[subtheme_key])

                    if theme.parent != None:
                        theme.DestroyObject()
                    elif theme.key in main_frame.themes:
                        theme.DestroyObject()
                        del main_frame.themes[theme.key]
                DeleteTheme(theme)
            self.selected_item = None
            model.Cleared()
            self.Expander(None)
            main_frame.ThemesUpdated()
        logger.info("Finished")

    #bring up menu on right click
    def OnIncludeCodes(self, event):
        logger = logging.getLogger(__name__+".ThemesViewCtrl.OnIncludeCode")
        logger.info("Starting")
        included_codes = None
        model = self.GetModel()
        main_frame = wx.GetApp().GetTopWindow()
        if self.selected_item != None:
            item = self.selected_item
            theme = model.ItemToObject(item).obj
        elif self.theme != None:
            theme = self.theme
        include_codes_dialog = CodesGUIs.IncludeCodesDialog(main_frame, wx.Size(400, 400))
        while included_codes == None:
            rc = include_codes_dialog.ShowModal()
            if rc == wx.ID_OK:
                included_code_keys = include_codes_dialog.included_code_keys
                for code_key in included_code_keys:
                    if code_key not in theme.code_keys:
                        theme.code_keys.append(code_key)
                theme.last_changed_dt = datetime.now()
                model.Cleared()
                self.Expander(None)
                main_frame.ThemesUpdated()
                break
            else:
                break
        logger.info("Finished")
    
    def OnRemoveCodes(self, event):
        logger = logging.getLogger(__name__+".ThemesViewCtrl.OnRemoveCodes")
        logger.info("Starting")
        #confirmation
        model = self.GetModel() 
        main_frame = wx.GetApp().GetTopWindow()
        remove_codes = []
        for item in self.GetSelections():
            node = model.ItemToObject(item)
            if isinstance(node.obj, Codes.Code):
                remove_codes.append(node)
        for node in remove_codes:
            if node.parent != None:
                node.parent.obj.code_keys.remove(node.obj.key)
                node.parent.obj.last_changed_dt = datetime.now()
            elif self.theme != None:
                self.theme.code_keys.remove(node.obj.key)
                self.theme.last_changed_dt = datetime.now()
        self.selected_item = None
        model.Cleared()
        self.Expander(None)
        main_frame.ThemesUpdated()
        logger.info("Finished")

    def OnChangeColour(self, event):
        logger = logging.getLogger(__name__+".ThemesViewCtrl.OnChangeColour")
        logger.info("Starting")

        model = self.GetModel() 
        main_frame = wx.GetApp().GetTopWindow()
        item = self.selected_item
        node = model.ItemToObject(item)
        
        cur_colour = wx.Colour(node.obj.colour_rgb[0], node.obj.colour_rgb[1], node.obj.colour_rgb[2])

        cur_colour_data = wx.ColourData()
        cur_colour_data.SetColour(cur_colour)

        colour_dlg = wx.ColourDialog(self, cur_colour_data)
        
        if colour_dlg.ShowModal() == wx.ID_OK:
            new_colour_data = colour_dlg.GetColourData()
            new_colour = new_colour_data.GetColour()
            node.obj.colour_rgb = (new_colour.Red(), new_colour.Green(), new_colour.Blue(),)
            self.UnselectAll()
            main_frame.ThemesUpdated()
        logger.info("Finished")

# This model acts as a bridge between the DocumentConnectionsViewCtrl and the connections.
# This model provides these data columns:
#   0. Code:   string
#   1. References:  int
#   2. Notes: string
class DocumentPositionsViewModel(dv.PyDataViewModel):
    def __init__(self, node):
        dv.PyDataViewModel.__init__(self)
        self.root_node = node
        main_frame = wx.GetApp().GetTopWindow()
        self.datasets = main_frame.datasets
        self.codes = main_frame.codes

        self.connection_objs = {}

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 3

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            if isinstance(self.root_node, Codes.Theme):
                for subtheme_key in self.root_node.subthemes:
                    child_key = (subtheme_key,)
                    if child_key not in self.connection_objs:
                        self.connection_objs[child_key] = Generic.Connection(None, self.root_node.subthemes[subtheme_key])
                    children.append(self.ObjectToItem(self.connection_objs[child_key]))
                for code in self.root_node.GetCodes(self.codes):
                    child_key = (code.key,)
                    if child_key not in self.connection_objs:
                        self.connection_objs[child_key] = Generic.Connection(None, code)
                    children.append(self.ObjectToItem(self.connection_objs[child_key]))
            elif isinstance(self.root_node, Codes.Code):
                if len(self.datasets) != 1:
                    for dataset_key in self.datasets:
                        child_key = (dataset_key,)
                        if child_key not in self.connection_objs:
                            self.connection_objs[child_key] = Generic.Connection(None, self.datasets[dataset_key])
                        children.append(self.ObjectToItem(self.connection_objs[child_key]))
                else:
                    for obj in self.root_node.GetConnections(self.datasets, {}):
                        if isinstance(obj, Datasets.Document):
                            child_key = (obj.key,)
                            if child_key not in self.connection_objs:
                                self.connection_objs[child_key] = Generic.Connection(None, obj)
                            children.append(self.ObjectToItem(self.connection_objs[child_key]))
                for subcode_key in self.root_node.subcodes:
                    child_key = (subcode_key,)
                    if child_key not in self.connection_objs:
                        self.connection_objs[child_key] = Generic.Connection(None, self.root_node.subcodes[subcode_key])
                    children.append(self.ObjectToItem(self.connection_objs[child_key]))
        else:
            node = self.ItemToObject(parent)
            if isinstance(node, Generic.Connection):
                node_key = node.GetKey()
                if isinstance(node.obj, Codes.Theme):
                    for subtheme_key in node.obj.subthemes:
                        child_key = (node_key, subtheme_key,)
                        if child_key not in self.connection_objs:
                            self.connection_objs[child_key] = Generic.Connection(node, node.obj.subthemes[subtheme_key])
                        children.append(self.ObjectToItem(self.connection_objs[child_key]))
                    for code in self.root_node.GetCodes(self.codes):
                        child_key = (node_key, code.key,)
                        if child_key not in self.connection_objs:
                            self.connection_objs[child_key] = Generic.Connection(node, code)
                        children.append(self.ObjectToItem(self.connection_objs[child_key]))
                elif isinstance(node.obj, Codes.Code):
                    if len(self.datasets) != 1:
                        for dataset_key in self.datasets:
                            child_key = (node_key, dataset_key,)
                            if child_key not in self.connection_objs:
                                self.connection_objs[child_key] = Generic.Connection(node, self.datasets[dataset_key])
                            children.append(self.ObjectToItem(self.connection_objs[child_key]))
                    else:
                        for obj in node.obj.GetConnections(self.datasets, {}):
                            if isinstance(obj, Datasets.Document):
                                child_key = (node_key, obj.key,)
                                if child_key not in self.connection_objs:
                                    self.connection_objs[child_key] = Generic.Connection(node, obj)
                                children.append(self.ObjectToItem(self.connection_objs[child_key]))
                    for subcode_key in node.obj.subcodes:
                        child_key = (node_key, subcode_key,)
                        if child_key not in self.connection_objs:
                            self.connection_objs[child_key] = Generic.Connection(node, node.obj.subcodes[subcode_key])
                        children.append(self.ObjectToItem(self.connection_objs[child_key]))
                elif isinstance(node.obj, Datasets.Dataset):
                    for dataset_key, document_key in node.parent.doc_positions:
                        if dataset_key == node.obj.key:
                            child_key = (node_key, document_key,)
                            if child_key not in self.connection_objs:
                                self.connection_objs[child_key] = Generic.Connection(node, self.datasets[dataset_key].documents[document_key])
                            children.append(self.ObjectToItem(self.connection_objs[child_key]))
                elif isinstance(node.obj, Datasets.Document):
                    doc_position_key = (node.obj.parent.key, node.obj.key,)
                    if isinstance(node.parent, Generic.Connection):
                        if isinstance(node.parent.obj, Datasets.Dataset):
                            parent_code = node.parent.parent.obj
                        elif isinstance(node.parent.obj, Codes.Code):
                            parent_code = node.parent.obj
                    else:
                        parent_code = self.root_node
                    if doc_position_key in parent_code.doc_positions:
                        positions = parent_code.doc_positions[doc_position_key]
                        for field_key, start, end in positions:
                            field = self.datasets[doc_position_key[0]].available_fields[field_key]
                            field_data = self.datasets[doc_position_key[0]].data[node.obj.doc_id][field.name]
                            field_string = '------'+str(field.name)+'------\n'
                            if isinstance(field_data, list):
                                for entry in field_data:
                                    if field.fieldtype == 'url':
                                        field_string = field_string + entry + '\n------------\n'
                                    elif field.fieldtype == 'UTC-timestamp':
                                        value_str = datetime.utcfromtimestamp(entry).strftime(Constants.DATETIME_FORMAT)
                                        field_string = field_string + value_str + ' UTC\n------------\n'
                                    else:
                                        field_string = field_string + str(entry) + '\n------------\n'
                            else:
                                if field.fieldtype == 'url':
                                    field_string = field_string + field_data + '\n------------\n'
                                elif field.fieldtype == 'UTC-timestamp':
                                    value_str = datetime.utcfromtimestamp(field_data).strftime(Constants.DATETIME_FORMAT)
                                    field_string = field_string + value_str+' UTC\n------------\n'
                                else:
                                    field_string = field_string + field_data + '\n------------\n'
                            selected_text = (node, field.name, field_string[start:end])
                            children.append(self.ObjectToItem(selected_text))
        return len(children)

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        node = self.ItemToObject(item)
        if isinstance(node, Generic.Connection):
            return True
        return False
    
    def HasContainerColumns(self, item):
        return False

    def GetParent(self, item):
        parent = dv.NullDataViewItem
        if item:
            node = self.ItemToObject(item)
            if isinstance(node, Generic.Connection):
                if node.parent != None:
                    parent = self.ObjectToItem(node.parent)
            elif isinstance(node, tuple):
                parent = self.ObjectToItem(node[0])
        return parent

    def GetValue(self, item, col):
        ''''Fetch the data object for this item's column.'''
        node = self.ItemToObject(item)
        if isinstance(node, tuple):
            mapper = { 0 : "",
                       1 : str(node[1]),
                       2 : str(node[2]),
                       }
            return mapper[col]
        elif isinstance(node, Generic.Connection) and isinstance(node.obj, Datasets.Document):
            if node.obj.url != "":
                segmented_url = node.obj.url.split("/")
                if segmented_url[len(segmented_url)-1] != '':
                    node_id = segmented_url[len(segmented_url)-1]
                else:
                    node_id = segmented_url[len(segmented_url)-2]
            else:
                node_id = node.obj.doc_id[2]
            mapper = { 0 : str(node_id),
                       1 : "",
                       2 : "",
                       }
            return mapper[col]
        elif isinstance(node, Generic.Connection):
            mapper = { 0: str(node.obj.name),
                       1 : "",
                       2 : "",
                       }
            return mapper[col]
        else:
            raise RuntimeError("unknown node type")
    
    def GetAttr(self, item, col, attr):
        res = super().GetAttr(item, col, attr)
        node = self.ItemToObject(item)
        if isinstance(node, Generic.Connection) and (isinstance(node.obj, Codes.Theme) or isinstance(node.obj, Codes.Code)):
            bg_colour, fg_colour = GenericUtilities.BackgroundAndForegroundColour(node.obj.colour_rgb)
            attr.SetBackgroundColour(bg_colour)
            attr.SetColour(fg_colour)
        return res
    
    def Cleared(self):
        self.connection_objs.clear()
        return super().Cleared()

#this view enables displaying of connection objects
class DocumentPositionsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.AssociateModel(model)
        model.DecRef()

        text_renderer = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn(GUIText.SOURCE, text_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        text_renderer = dv.DataViewTextRenderer()
        column1 = dv.DataViewColumn(GUIText.FIELD, text_renderer, 1, align=wx.ALIGN_LEFT)
        self.AppendColumn(column1)
        text_renderer = dv.DataViewTextRenderer()
        text_renderer.EnableEllipsize(mode=wx.ELLIPSIZE_END)
        column2 = dv.DataViewColumn(GUIText.QUOTATIONS, text_renderer, 2, align=wx.ALIGN_LEFT)
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

    def Expander(self, item):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".DocumentConnectionsViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(node, Datasets.Document):
            if node.key not in main_frame.document_dialogs:
                main_frame.document_dialogs[node.key] = CodesGUIs.DocumentDialog(main_frame, node)
            main_frame.document_dialogs[node.key].Show()
            main_frame.document_dialogs[node.key].SetFocus()
        elif isinstance(node, tuple):
            doc = model.dataset.documents[node[0]]
            if doc.key not in main_frame.document_dialogs:
                main_frame.document_dialogs[doc.key] = CodesGUIs.DocumentDialog(main_frame, doc)
            main_frame.document_dialogs[doc.key].Show()
            main_frame.document_dialogs[doc.key].SetFocus()
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

class SelectedQuotationsViewModel(dv.PyDataViewModel):
    def __init__(self):
        dv.PyDataViewModel.__init__(self)
        main_frame = wx.GetApp().GetTopWindow()
        self.codes = main_frame.codes
        self.themes = main_frame.themes
        
        self.search_filter = ""
        self.theme_usefulness_filter = []
        self.code_usefulness_filter = []
        self.quote_usefulness_filter = []

        self.UseWeakRefs(True)

    def GetColumnCount(self):
        '''Report how many columns this model provides data for.'''
        return 4

    def GetChildren(self, parent, children):
        # If the parent item is invalid then it represents the hidden root
        # item, so we'll use the genre objects as its children and they will
        # end up being the collection of visible roots in our tree.
        if not parent:
            for theme_key in self.themes:
                theme = self.themes[theme_key]
                if theme.usefulness_flag in self.theme_usefulness_filter:
                    children.append(self.ObjectToItem(theme))
            for code_key in self.codes:
                code = self.codes[code_key]
                if code.usefulness_flag in self.code_usefulness_filter:
                    children.append(self.ObjectToItem(code))
            return len(children)

        node = self.ItemToObject(parent)
        if isinstance(node, Codes.Theme):
            for quotation in node.quotations:
                if quotation.usefulness_flag in self.quote_usefulness_filter:
                    children.append(self.ObjectToItem(quotation))
            for subtheme_key in node.subthemes:
                subtheme = node.subthemes[subtheme_key]
                if subtheme.usefulness_flag in self.theme_usefulness_filter:
                    children.append(self.ObjectToItem(subtheme))
        elif isinstance(node, Codes.Code):
            for quotation in node.quotations:
                if quotation.usefulness_flag in self.quote_usefulness_filter:
                    children.append(self.ObjectToItem(quotation))
            for subcode_key in node.subcodes:
                subcode = node.subcodes[subcode_key]
                if subcode.usefulness_flag in self.code_usefulness_filter:
                    children.append(self.ObjectToItem(subcode))
        return len(children)

    def IsContainer(self, item):
        ''' Return True if the item has children, False otherwise.'''
        # The hidden root is a container
        if not item:
            return True
        # Any Code is a container
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code) or isinstance(node, Codes.Theme):
            return True
        return False
    
    def HasContainerColumns(self, item):
        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Theme):
            if node.parent != None:
                return self.ObjectToItem(node.parent)
            else:
                return dv.NullDataViewItem
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
        if isinstance(node, Codes.Theme):
            mapper = { 0 : node.name,
                       1 : "",
                       2 : "",
                       3 : "",
                       }
            return mapper[col]
        if isinstance(node, Codes.Code):
            mapper = { 0 : node.name,
                       1 : "",
                       2 : "",
                       3 : "",
                       }
            return mapper[col]
        elif isinstance(node, Codes.Quotation):
            main_frame = wx.GetApp().GetTopWindow()
            dataset = main_frame.datasets[node.dataset_key]
            document = dataset.documents[node.document_key]
            if document.url != "":
                segmented_url = document.url.split("/")
                if segmented_url[len(segmented_url)-1] != '':
                    document_id = segmented_url[len(segmented_url)-1]
                else:
                    document_id = segmented_url[len(segmented_url)-2]
            else:
                document_id = document.doc_id[2]
            mapper = { 0 : str(document_id),
                       1 : str(dataset.name),
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
            if col == 2:
                node.original_data = value
            elif col == 3:
                node.paraphrased_data = value
        return True
    
    def GetAttr(self, item, col, attr):
        res = super().GetAttr(item, col, attr)
        node = self.ItemToObject(item)
        if isinstance(node, Codes.Code):
            bg_colour, fg_colour = GenericUtilities.BackgroundAndForegroundColour(node.colour_rgb)
            attr.SetBackgroundColour(bg_colour)
            attr.SetColour(fg_colour)
        return res

class SelectedQuotationsViewCtrl(dv.DataViewCtrl):
    def __init__(self, parent, model, style=dv.DV_MULTIPLE|dv.DV_ROW_LINES):
        dv.DataViewCtrl.__init__(self, parent, style=style)

        self.selected_item = None

        self.AssociateModel(model)
        model.DecRef()

        self.UpdateColumns()

        self.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.OnShowPopup)
        self.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.Bind(wx.EVT_MENU, self.OnCopyItems, id=wx.ID_COPY)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('C'), wx.ID_COPY)])
        self.SetAcceleratorTable(accel_tbl)

    def Expander(self, item, autosize_flg=True):
        model = self.GetModel()
        if item != None:
            self.Expand(item)
        children = []
        model.GetChildren(item, children)
        for child in children:
            self.Expander(child, False)
        if autosize_flg:
            self.AutoSize()
    
    def AutoSize(self):
        for column in self.GetColumns():
            column.SetWidth(wx.COL_WIDTH_AUTOSIZE)

    def UpdateColumns(self):
        self.ClearColumns()

        text_renderer = dv.DataViewTextRenderer()
        column0 = dv.DataViewColumn(GUIText.ID, text_renderer, 0, align=wx.ALIGN_LEFT)
        self.AppendColumn(column0)
        self.SetExpanderColumn(column0)

        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.options_dict['multipledatasets_mode']:
            text_renderer = dv.DataViewTextRenderer()
            column1 = dv.DataViewColumn(GUIText.DATASET, text_renderer, 1, align=wx.ALIGN_LEFT)
            self.AppendColumn(column1)

        text_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        text_renderer.EnableEllipsize(mode=wx.ELLIPSIZE_END)
        column2 = dv.DataViewColumn(GUIText.QUOTATIONS, text_renderer, 2, align=wx.ALIGN_LEFT)
        self.AppendColumn(column2)

        text_renderer = dv.DataViewTextRenderer(mode=dv.DATAVIEW_CELL_EDITABLE)
        text_renderer.EnableEllipsize(mode=wx.ELLIPSIZE_END)
        column3 = dv.DataViewColumn(GUIText.PARAPHRASES, text_renderer, 3, align=wx.ALIGN_LEFT)
        self.AppendColumn(column3)

        idx = 0
        for column in self.Columns:
            column.Sortable = True
            column.Reorderable = True
            column.Resizeable = True
            idx = idx + 1
        
        self.Expander(None)

    def OnOpen(self, event):
        logger = logging.getLogger(__name__+".QuotationsViewCtrl.OnOpen")
        logger.info("Starting")
        item = event.GetItem()
        model = self.GetModel()
        node = model.ItemToObject(item)
        main_frame = wx.GetApp().GetTopWindow()
        if isinstance(node, Codes.Theme):
            if node.key not in main_frame.theme_dialogs:
                main_frame.theme_dialogs[node.key] = CodesGUIs.ThemeDialog(main_frame, node, size=wx.Size(400,400))
            main_frame.theme_dialogs[node.key].Show()
            main_frame.theme_dialogs[node.key].SetFocus()
        if isinstance(node, Codes.Code):
            if node.key not in main_frame.code_dialogs:
                main_frame.code_dialogs[node.key] = CodesGUIs.CodeDialog(main_frame, node, size=wx.Size(400,400))
            main_frame.code_dialogs[node.key].Show()
            main_frame.code_dialogs[node.key].SetFocus()
        elif isinstance(node, Codes.Quotation):
            document = main_frame.datasets[node.dataset_key].documents[node.document_key]
            if node.key not in main_frame.document_dialogs:
                main_frame.document_dialogs[document.key] = CodesGUIs.DocumentDialog(main_frame, document)
            main_frame.document_dialogs[document.key].Show()
            main_frame.document_dialogs[document.key].SetFocus()
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
            if isinstance(node, Codes.Code) or isinstance(node, Codes.Theme):
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
    
    #TODO figure out why this is not working with themes
    def OnAddItem(self, event):
        model = self.GetModel()
        item = self.selected_item
        node = model.ItemToObject(item)
        if isinstance(node, Codes.Code) or isinstance(node, Codes.Theme):
            main_frame = wx.GetApp().GetTopWindow()
            dialog = CodesGUIs.CreateQuotationDialog(main_frame, node)
            if dialog.ShowModal() == wx.ID_OK:
                quote_item = dialog.positions_ctrl.GetSelection()
                quote_node = dialog.positions_model.ItemToObject(quote_item)
                if isinstance(quote_node, Generic.Connection) and isinstance(quote_node.obj, Datasets.Document):
                    node.quotations.append(Codes.Quotation(node, quote_node.obj.parent.key, quote_node.obj.key))
                elif isinstance(quote_node, tuple):
                    node.quotations.append(Codes.Quotation(node, quote_node[0].obj.parent.key, quote_node[0].obj.key, quote_node[2]))
                    
            model.Cleared()
            self.Expander(None)
    
    def OnDeleteItems(self, event):
        model = self.GetModel()
        confirm_dialog = wx.MessageDialog(self, GUIText.CONFIRM_DELETE_QUOTATIONS,
                                          GUIText.CONFIRM_REQUEST, wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        confirm_dialog.SetOKLabel(GUIText.DELETE_QUOTATIONS)
        if confirm_dialog.ShowModal() == wx.ID_OK:
            for item in self.GetSelections():
                node = model.ItemToObject(item)
                if isinstance(node, Codes.Quotation):
                    node.DestroyObject()
            model.Cleared()
            self.Expander(None)

