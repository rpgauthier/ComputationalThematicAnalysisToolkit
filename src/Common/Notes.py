import logging
import io
import os

import wx
import wx.richtext
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB

import Common.Constants as Constants
from Common.GUIText import Common as GUIText

class NotesNotebook(FNB.FlatNotebook):
    '''Manages the Notes Interface'''
    def __init__(self, parent, size=wx.DefaultSize):
        logger = logging.getLogger(__name__+".NotesNotebook.__init__")
        logger.info("Starting")
        FNB.FlatNotebook.__init__(self, parent, agwStyle=Constants.FNB_STYLE, size=size)
        self.name = "notes"
        logger.info("Finished")

    def Load(self, saved_data):
        logger = logging.getLogger(__name__+".NotesNotebook.Load")
        logger.info("Starting")
        '''not used because notes are tied to thier modules rather then to the managing notebook'''
        logger.info("Finished")
        return

    def Save(self):
        logger = logging.getLogger(__name__+".NotesNotebook.Save")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        #dump notes into easy to access text outside of toolkit
        notes_text = ""
        for page_index in range(self.GetPageCount()):
            notes_text+=self.GetPageText(page_index)
            notes_text+="\n"
            notes_text+=self.GetPage(page_index).rich_text_ctrl.GetValue()
            notes_text+="\n\n"
        logger.info("Finished")
        return notes_text

class NotesPanel(wx.Panel):
    '''Creates a Note Panel created based on code from https://play.pixelblaster.ro/blog/2008/10/08/richtext-control-with-wxpython-saving-loading-and-converting-from-internal-xml-to-html/'''
    def __init__(self, parent, module=None):
        logger = logging.getLogger(__name__+".NotePanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)
        #self.module = module

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.rich_text_ctrl = wx.richtext.RichTextCtrl(self)
        self.rich_text_ctrl.BeginSuppressUndo()
        toolbar = NoteToolBar(self)

        sizer.Add(toolbar, 0, wx.EXPAND|wx.ALL, 6)
        sizer.Add(self.rich_text_ctrl, 1, wx.EXPAND|wx.ALL, 6)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_TOOL, self.OnBold, id=wx.ID_BOLD)
        self.Bind(wx.EVT_TOOL, self.OnItalic, id=wx.ID_ITALIC)
        self.Bind(wx.EVT_TOOL, self.OnUnderline, id=wx.ID_UNDERLINE)
        self.Bind(wx.EVT_TOOL, self.OnStrikethrough, id=wx.ID_STRIKETHROUGH)
        self.Bind(wx.EVT_TOOL, self.OnFont, id=wx.ID_SELECT_FONT)
        self.Bind(wx.EVT_TOOL, self.OnIncreasefontsize, id=wx.ID_ZOOM_OUT)
        self.Bind(wx.EVT_TOOL, self.OnDecreasefontsize, id=wx.ID_ZOOM_IN)
        self.Bind(wx.EVT_TOOL, self.OnPaste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_TOOL, self.OnCopy, id=wx.ID_COPY)
        self.Bind(wx.EVT_TOOL, self.OnCut, id=wx.ID_CUT)
        self.Bind(wx.EVT_TOOL, self.OnUndo, id=wx.ID_UNDO)
        self.Bind(wx.EVT_TOOL, self.OnRedo, id=wx.ID_REDO)
        #TODO figure out why undo and redo crash application on coding tab
        #error captured in windows event viewer but doesnt explain what is occuring
        #need to test if this error is being caused by two richtextctrls in the same frame
        self.Bind(wx.EVT_MENU, self.OnUndo, id=wx.ID_UNDO)
        self.Bind(wx.EVT_MENU, self.OnRedo, id=wx.ID_REDO)


        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('B'), wx.ID_BOLD),
                                         (wx.ACCEL_CTRL, ord('I'), wx.ID_ITALIC),
                                         (wx.ACCEL_CTRL, ord('U'), wx.ID_UNDERLINE)])
        self.SetAcceleratorTable(accel_tbl)

        self.rich_text_ctrl.EndSuppressUndo()

    def OnBold(self, event):
        self.rich_text_ctrl.ApplyBoldToSelection()
        self.TriggerTextEvent()

    def OnItalic(self, event):
        self.rich_text_ctrl.ApplyItalicToSelection()
        self.TriggerTextEvent()

    def OnUnderline(self, event):
        self.rich_text_ctrl.ApplyUnderlineToSelection()
        self.TriggerTextEvent()

    def OnStrikethrough(self, event):
        self.rich_text_ctrl.ApplyTextEffectToSelection(wx.TEXT_ATTR_EFFECT_STRIKETHROUGH)
        self.TriggerTextEvent()

    def OnFont(self, event):
        if self.rich_text_ctrl.HasSelection():
            range = self.rich_text_ctrl.GetSelectionRange()
        else:
            range = wx.richtext.RichTextRange(self.rich_text_ctrl.GetInsertionPoint(), self.rich_text_ctrl.GetInsertionPoint()+1)

        pages = wx.richtext.RICHTEXT_FORMAT_FONT \
                | wx.richtext.RICHTEXT_FORMAT_INDENTS_SPACING \
                | wx.richtext.RICHTEXT_FORMAT_TABS \
                | wx.richtext.RICHTEXT_FORMAT_BULLETS

        with wx.richtext.RichTextFormattingDialog(pages, self) as dlg:
            dlg.GetStyle(self.rich_text_ctrl, range)
            if dlg.ShowModal() == wx.ID_OK:
                dlg.ApplyStyle(self.rich_text_ctrl, range)
                self.TriggerTextEvent()

    def OnIncreasefontsize(self, event):
        if self.rich_text_ctrl.HasSelection():
            selection_range = self.rich_text_ctrl.GetSelectionRange()
        else:
            selection_range = wx.richtext.RichTextRange(self.rich_text_ctrl.GetInsertionPoint(), self.rich_text_ctrl.GetInsertionPoint()+1)
        oldstyle = wx.richtext.RichTextAttr()
        self.rich_text_ctrl.GetStyle(self.rich_text_ctrl.GetInsertionPoint(), oldstyle)
        style = wx.richtext.RichTextAttr()
        style.SetFontSize(oldstyle.GetFontSize()+1)
        self.rich_text_ctrl.SetStyleEx(selection_range, style)
        self.TriggerTextEvent()

    def OnDecreasefontsize(self, event):
        if self.rich_text_ctrl.HasSelection():
            selection_range = self.rich_text_ctrl.GetSelectionRange()
        else:
            selection_range = wx.richtext.RichTextRange(self.rich_text_ctrl.GetInsertionPoint(), self.rich_text_ctrl.GetInsertionPoint()+1)
        style = wx.richtext.RichTextAttr()
        self.rich_text_ctrl.GetStyle(self.rich_text_ctrl.GetInsertionPoint(), style)
        if style.GetFontSize() > 1:
            style.SetFontSize(style.GetFontSize()-1)
            self.rich_text_ctrl.SetStyleEx(selection_range, style)
            self.TriggerTextEvent()

    def OnPaste(self, event):
        self.rich_text_ctrl.Paste()
        self.TriggerTextEvent()

    def OnCopy(self, event):
        self.rich_text_ctrl.Copy()

    def OnCut(self, event):
        self.rich_text_ctrl.Cut()
        self.TriggerTextEvent()

    def OnUndo(self, event):
        self.rich_text_ctrl.Undo()
        self.TriggerTextEvent()

    def OnRedo(self, event):
        self.rich_text_ctrl.Redo()
        self.TriggerTextEvent()

    def TriggerTextEvent(self):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_TEXT_UPDATED)
        evt.SetEventObject(self.rich_text_ctrl)
        evt.SetId(self.rich_text_ctrl.GetId())
        self.rich_text_ctrl.GetEventHandler().ProcessEvent(evt)

    def SetNote(self, content):
        if isinstance(content, bytes):
            out = io.BytesIO()
            handler = wx.richtext.RichTextXMLHandler()
            buffer = self.rich_text_ctrl.GetBuffer()
            buffer.AddHandler(handler)
            out.write(content)
            out.seek(0)
            handler.LoadFile(buffer, out)
        else:
            self.rich_text_ctrl.SetValue(content)
        self.rich_text_ctrl.Refresh()

    def GetNote(self):
        self.rich_text_ctrl.Undo
        self.rich_text_ctrl.BeginSuppressUndo()
        if self.rich_text_ctrl.IsEmpty():
            content = ""
        else:
            out = io.BytesIO()
            handler = wx.richtext.RichTextXMLHandler()
            buffer = self.rich_text_ctrl.GetBuffer()
            handler.SaveFile(buffer, out)
            out.seek(0)
            content = out.read()
            content_string = self.rich_text_ctrl.GetValue()
        self.rich_text_ctrl.EndSuppressUndo()
        return content, content_string

    ##Save and Load Functions
    def Load(self, saved_data):
        '''loads saved data into the NotePanel'''
        logger = logging.getLogger(__name__+".NotePanel.Load")
        logger.info("Starting")
        #sub modules
        #retriever_submodule so should always exist

        content = saved_data['RichTextCtrl']

        self.SetNote(content)

        logger.info("Finished")

    def Save(self):
        '''saves current NotePanel's data'''
        logger = logging.getLogger(__name__+".NotePanel.Save")
        logger.info("Starting")
        #data fields
        saved_data = {}

        content, content_string = self.GetNote()

        saved_data['RichTextCtrl'] = content
        saved_data['RichTextCtrl_string'] = content_string

        logger.info("Finished")
        return saved_data

#TODO Rework to be sizer of buttons to avoid Windows to OSX compatibility issues
class NoteToolBar(wx.ToolBar):
    '''Toolbar with options for editing notes'''
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT
        wx.ToolBar.__init__(self, *args, **kwds)
        self.cut_tool = self.AddTool(wx.ID_CUT, GUIText.CUT, wx.ArtProvider.GetBitmap(wx.ART_CUT, wx.ART_TOOLBAR),
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.CUT, "")
        self.copy_tool = self.AddTool(wx.ID_COPY, GUIText.COPY, wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR),
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.COPY, "")
        self.paste_tool = self.AddTool(wx.ID_PASTE, GUIText.PASTE, wx.ArtProvider.GetBitmap(wx.ART_PASTE, wx.ART_TOOLBAR),
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.PASTE, "")
        self.AddSeparator()
        self.undo_tool = self.AddTool(wx.ID_UNDO, GUIText.UNDO, wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR),
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.UNDO, "")
        self.redo_tool = self.AddTool(wx.ID_REDO, GUIText.REDO, wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR),
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.REDO, "")
        self.AddSeparator()
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "bold.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        bold_bmp = wx.Bitmap(image.Scale(32, 32, quality=wx.IMAGE_QUALITY_HIGH))
        self.bold_tool = self.AddTool(wx.ID_BOLD, GUIText.BOLD, bold_bmp,
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.BOLD, "")
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "italic.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        italic_bmp = wx.Bitmap(image.Scale(32, 32, quality=wx.IMAGE_QUALITY_HIGH))
        self.italic_tool = self.AddTool(wx.ID_ITALIC, GUIText.ITALIC, italic_bmp,
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.ITALIC, "")
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "underline.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        underline_bmp = wx.Bitmap(image.Scale(32, 32, quality=wx.IMAGE_QUALITY_HIGH))
        self.underline_tool = self.AddTool(wx.ID_UNDERLINE, GUIText.UNDERLINE, underline_bmp,
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.UNDERLINE, "")
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "strikethrough.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        strikethrough_bmp = wx.Bitmap(image.Scale(32, 32, quality=wx.IMAGE_QUALITY_HIGH))
        self.strikethrough_tool = self.AddTool(wx.ID_STRIKETHROUGH, GUIText.STRIKETHROUGH, strikethrough_bmp,
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.STRIKETHROUGH, "")
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "font.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        font_bmp = wx.Bitmap(image.Scale(32, 32, quality=wx.IMAGE_QUALITY_HIGH))
        self.font_tool = self.AddTool(wx.ID_SELECT_FONT, GUIText.FONT, font_bmp,
                     wx.NullBitmap, wx.ITEM_NORMAL, GUIText.FONT, "")

        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "increasefontsize.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        increasefontsize_bmp = wx.Bitmap(image.Scale(32, 32, quality=wx.IMAGE_QUALITY_HIGH))
        self.increasefontsize_tool = self.AddTool(wx.ID_ZOOM_OUT, "Increase Font Size", increasefontsize_bmp,
                                                  wx.NullBitmap, wx.ITEM_NORMAL, "Increase Font Size", "")
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "decreasefontsize.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        decreasefontsize_bmp = wx.Bitmap(image.Scale(32, 32, quality=wx.IMAGE_QUALITY_HIGH))
        self.decreasefontsize_tool = self.AddTool(wx.ID_ZOOM_IN, "Decrease Font Size", decreasefontsize_bmp,
                                                  wx.NullBitmap, wx.ITEM_NORMAL, "Decrease Font Size", "")
        self.Realize()
