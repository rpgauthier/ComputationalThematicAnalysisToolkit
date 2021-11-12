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
        toolbar = NoteToolPanel(self)

        sizer.Add(toolbar, 0, wx.EXPAND|wx.ALL, 6)
        sizer.Add(self.rich_text_ctrl, 1, wx.EXPAND|wx.ALL, 6)
        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_BUTTON, self.OnBold, id=wx.ID_BOLD)
        self.Bind(wx.EVT_BUTTON, self.OnItalic, id=wx.ID_ITALIC)
        self.Bind(wx.EVT_BUTTON, self.OnUnderline, id=wx.ID_UNDERLINE)
        self.Bind(wx.EVT_BUTTON, self.OnStrikethrough, id=wx.ID_STRIKETHROUGH)
        self.Bind(wx.EVT_BUTTON, self.OnFont, id=wx.ID_SELECT_FONT)
        self.Bind(wx.EVT_BUTTON, self.OnIncreasefontsize, id=wx.ID_ZOOM_OUT)
        self.Bind(wx.EVT_BUTTON, self.OnDecreasefontsize, id=wx.ID_ZOOM_IN)
        self.Bind(wx.EVT_BUTTON, self.OnPaste, id=wx.ID_PASTE)
        self.Bind(wx.EVT_BUTTON, self.OnCopy, id=wx.ID_COPY)
        self.Bind(wx.EVT_BUTTON, self.OnCut, id=wx.ID_CUT)
        self.Bind(wx.EVT_BUTTON, self.OnUndo, id=wx.ID_UNDO)
        self.Bind(wx.EVT_BUTTON, self.OnRedo, id=wx.ID_REDO)
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
            content_string = ""
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

#TODO confirm new approach is OSX compatibile
class NoteToolPanel(wx.Panel):
    '''Toolbar with options for editing notes'''
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        sizer = wx.BoxSizer()

        icon_width = 25
        icon_height = 25
        
        bmp = wx.ArtProvider.GetBitmap(wx.ART_CUT, wx.ART_TOOLBAR)
        image = bmp.ConvertToImage()
        cut_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        cut_btn = wx.BitmapButton(self, wx.ID_CUT, bitmap=cut_bmp)
        cut_btn.SetToolTip(GUIText.CUT)
        sizer.Add(cut_btn)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR)
        image = bmp.ConvertToImage()
        copy_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        copy_btn = wx.BitmapButton(self, wx.ID_COPY, bitmap=copy_bmp)
        copy_btn.SetToolTip(GUIText.COPY)
        sizer.Add(copy_btn)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_PASTE, wx.ART_TOOLBAR)
        image = bmp.ConvertToImage()
        paste_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        paste_btn = wx.BitmapButton(self, wx.ID_PASTE, bitmap=paste_bmp)
        paste_btn.SetToolTip(GUIText.PASTE)
        sizer.Add(paste_btn)

        sizer.AddSpacer(10)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR)
        image = bmp.ConvertToImage()
        undo_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        undo_btn = wx.BitmapButton(self, wx.ID_UNDO, bitmap=undo_bmp)
        undo_btn.SetToolTip(GUIText.UNDO)
        sizer.Add(undo_btn)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR)
        image = bmp.ConvertToImage()
        redo_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        redo_btn = wx.BitmapButton(self, wx.ID_REDO, bitmap=redo_bmp)
        redo_btn.SetToolTip(GUIText.REDO)
        sizer.Add(redo_btn)
        
        sizer.AddSpacer(10)

        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "bold.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        bold_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        bold_btn = wx.BitmapButton(self, wx.ID_BOLD, bitmap=bold_bmp)
        bold_btn.SetToolTip(GUIText.BOLD)
        sizer.Add(bold_btn)
        
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "italic.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        italic_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        italic_btn = wx.BitmapButton(self, wx.ID_ITALIC, bitmap=italic_bmp)
        italic_btn.SetToolTip(GUIText.ITALIC)
        sizer.Add(italic_btn)
        
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "underline.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        underline_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        underline_btn = wx.BitmapButton(self, wx.ID_UNDERLINE, bitmap=underline_bmp)
        underline_btn.SetToolTip(GUIText.UNDERLINE)
        sizer.Add(underline_btn)
        
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "strikethrough.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        strikethrough_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        strikethrough_btn = wx.BitmapButton(self, wx.ID_STRIKETHROUGH, bitmap=strikethrough_bmp)
        strikethrough_btn.SetToolTip(GUIText.STRIKETHROUGH)
        sizer.Add(strikethrough_btn)
        
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "font.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        font_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        font_btn = wx.BitmapButton(self, wx.ID_SELECT_FONT, bitmap=font_bmp)
        font_btn.SetToolTip(GUIText.FONT)
        sizer.Add(font_btn)
        
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "increasefontsize.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        increasefontsize_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        increasefontsize_btn = wx.BitmapButton(self, wx.ID_ZOOM_OUT, bitmap=increasefontsize_bmp)
        increasefontsize_btn.SetToolTip(GUIText.INCREASE_FONT_SIZE)
        sizer.Add(increasefontsize_btn)
        
        bmp = wx.Bitmap(os.path.join(Constants.IMAGES_PATH, "decreasefontsize.bmp"), wx.BITMAP_TYPE_ANY)
        image = bmp.ConvertToImage()
        decreasefontsize_bmp = wx.Bitmap(image.Scale(icon_width, icon_height, quality=wx.IMAGE_QUALITY_HIGH))
        decreasefontsize_btn = wx.BitmapButton(self, wx.ID_ZOOM_IN, bitmap=decreasefontsize_bmp)
        decreasefontsize_btn.SetToolTip(GUIText.DECREASE_FONT_SIZE)
        sizer.Add(decreasefontsize_btn)

        self.SetSizerAndFit(sizer)
