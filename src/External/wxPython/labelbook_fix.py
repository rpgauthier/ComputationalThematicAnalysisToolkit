import wx
import wx.lib.agw.labelbook as LB

# copies of functions from wxPython's wx.lib.agw.labelbook with fixes that cast floats to ints to avoid reoccuring deprication warnings
#
# License: wxWidgets license
# Original C++ Code From Eran, embedded in the FlatMenu source code
# Python Code By:
# Andrea Gavana, @ 03 Nov 2006
# Latest Revision: 22 Jan 2013, 21.00 GMT

class LabelBook(LB.LabelBook):
    def CreateImageContainer(self):
        """ Creates the image container (LabelContainer) class for :class:`FlatImageBook`. """
        return LabelContainer(self, wx.ID_ANY, agwStyle=self.GetAGWWindowStyleFlag())
    
    def ResizeTabArea(self):
        """ Resizes the tab area if the control has the ``INB_FIT_LABELTEXT`` style set. """

        agwStyle = self.GetAGWWindowStyleFlag()

        if agwStyle & LB.INB_FIT_LABELTEXT == 0:
            return

        if agwStyle & LB.INB_LEFT or agwStyle & LB.INB_RIGHT:
            dc = wx.MemoryDC()
            dc.SelectObject(wx.Bitmap(1, 1))
            font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            font.SetPointSize(int(font.GetPointSize()*self._fontSizeMultiple))
            if self.GetFontBold() or agwStyle & LB.INB_BOLD_TAB_SELECTION:
                font.SetWeight(wx.FONTWEIGHT_BOLD)
            dc.SetFont(font)
            maxW = 0

            for page in range(self.GetPageCount()):
                caption = self._pages.GetPageText(page)
                w, h = dc.GetTextExtent(caption)
                maxW = max(maxW, w)

            maxW += 24 #TODO this is 6*4 6 is nPadding from drawlabel

            if not agwStyle & LB.INB_SHOW_ONLY_TEXT:
                maxW += self._pages._nImgSize * 2

            maxW = max(maxW, 100)
            self._pages.SetSizeHints(maxW, -1)
            self._pages._nTabAreaWidth = maxW
    
class LabelContainer(LB.LabelContainer):
    def OnPaint(self, event):
        """
        Handles the ``wx.EVT_PAINT`` event for :class:`LabelContainer`.

        :param `event`: a :class:`PaintEvent` event to be processed.
        """

        style = self.GetParent().GetAGWWindowStyleFlag()

        dc = wx.BufferedPaintDC(self)
        backBrush = wx.Brush(self._coloursMap[LB.INB_TAB_AREA_BACKGROUND_COLOUR])
        if self.HasAGWFlag(LB.INB_BORDER):
            borderPen = wx.Pen(self._coloursMap[LB.INB_TABS_BORDER_COLOUR])
        else:
            borderPen = wx.TRANSPARENT_PEN

        size = self.GetSize()

        # Set the pen & brush
        dc.SetBrush(backBrush)
        dc.SetPen(borderPen)

        # In case user set both flags, we override them to display both
        # INB_SHOW_ONLY_TEXT and INB_SHOW_ONLY_IMAGES
        if style & LB.INB_SHOW_ONLY_TEXT and style & LB.INB_SHOW_ONLY_IMAGES:

            style ^= LB.INB_SHOW_ONLY_TEXT
            style ^= LB.INB_SHOW_ONLY_IMAGES
            self.GetParent().SetAGWWindowStyleFlag(style)

        if self.HasAGWFlag(LB.INB_GRADIENT_BACKGROUND) and not self._skin.IsOk():

            # Draw gradient in the background area
            startColour = self._coloursMap[LB.INB_TAB_AREA_BACKGROUND_COLOUR]
            endColour   = LB.ArtManager.Get().LightColour(self._coloursMap[LB.INB_TAB_AREA_BACKGROUND_COLOUR], 50)
            LB.ArtManager.Get().PaintStraightGradientBox(dc, wx.Rect(0, 0, int(size.x / 2), size.y), startColour, endColour, False)
            LB.ArtManager.Get().PaintStraightGradientBox(dc, wx.Rect(int(size.x / 2), 0, int(size.x / 2), size.y), endColour, startColour, False)

        else:

            # Draw the border and background
            if self._skin.IsOk():

                dc.SetBrush(wx.TRANSPARENT_BRUSH)
                self.DrawBackgroundBitmap(dc)

            dc.DrawRectangle(wx.Rect(0, 0, size.x, size.y))

        # Draw border
        if self.HasAGWFlag(LB.INB_BORDER) and self.HasAGWFlag(LB.INB_GRADIENT_BACKGROUND):

            # Just draw the border with transparent brush
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRectangle(wx.Rect(0, 0, size.x, size.y))

        bUsePin = (self.HasAGWFlag(LB.INB_USE_PIN_BUTTON) and [True] or [False])[0]

        if bUsePin:

            # Draw the pin button
            clientRect = self.GetClientRect()
            pinRect = wx.Rect(clientRect.GetX() + clientRect.GetWidth() - 20, 2, 20, 20)
            self.DrawPin(dc, pinRect, not self._bCollapsed)

            if self._bCollapsed:
                return

        dc.SetPen(wx.BLACK_PEN)
        self.SetSizeHints(self._nTabAreaWidth, -1)

        # We reserve 20 pixels for the pin button
        posy = 20
        count = 0

        for i in range(len(self._pagesInfoVec)):
            count = count+1
            # Default values for the surrounding rectangle
            # around a button
            rectWidth = self._nTabAreaWidth

            if self.HasAGWFlag(LB.INB_SHOW_ONLY_TEXT):
                font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
                font.SetPointSize(int(font.GetPointSize() * self.GetParent().GetFontSizeMultiple()))

                if self.GetParent().GetFontBold():
                    font.SetWeight(wx.FONTWEIGHT_BOLD)
                elif self.HasAGWFlag(LB.INB_BOLD_TAB_SELECTION) and self._nIndex == i:
                    font.SetWeight(wx.FONTWEIGHT_BOLD)

                dc.SetFont(font)
                w, h = dc.GetTextExtent(self._pagesInfoVec[i].GetCaption())
                rectHeight = h * 2
            else:
                rectHeight = self._nImgSize * 2

            # Check that we have enough space to draw the button
            if posy + rectHeight > size.GetHeight():
                break

            # Calculate the button rectangle
            posx = 0

            buttonRect = wx.Rect(posx, posy, rectWidth, rectHeight)
            indx = self._pagesInfoVec[i].GetImageIndex()

            if indx == -1:
                bmp = wx.NullBitmap
            else:
                bmp = self._ImageList.GetBitmap(indx)

            self.DrawLabel(dc, buttonRect, self._pagesInfoVec[i].GetCaption(), bmp,
                           self._pagesInfoVec[i], self.HasAGWFlag(LB.INB_LEFT) or self.HasAGWFlag(LB.INB_TOP),
                           i, self._nIndex == i, self._nHoveredImgIdx == i)

            posy += rectHeight

        # Update all buttons that can not fit into the screen as non-visible
        for ii in range(count, len(self._pagesInfoVec)):
            self._pagesInfoVec[i].SetPosition(wx.Point(-1, -1))

        if bUsePin:

            clientRect = self.GetClientRect()
            pinRect = wx.Rect(clientRect.GetX() + clientRect.GetWidth() - 20, 2, 20, 20)
            self.DrawPin(dc, pinRect, not self._bCollapsed)

    def DrawLabel(self, dc, rect, text, bmp, imgInfo, orientationLeft, imgIdx, selected, hover):
        """
        Draws a label using the specified dc.

        :param `dc`: an instance of :class:`wx.DC`;
        :param `rect`: the text client rectangle;
        :param `text`: the actual text string;
        :param `bmp`: a bitmap to be drawn next to the text;
        :param `imgInfo`: an instance of :class:`wx.ImageInfo`;
        :param `orientationLeft`: ``True`` if the book has the ``INB_RIGHT`` or ``INB_LEFT``
         style set;
        :param `imgIdx`: the tab image index;
        :param `selected`: ``True`` if the tab is selected, ``False`` otherwise;
        :param `hover`: ``True`` if the tab is being hovered with the mouse, ``False`` otherwise.
        """

        dcsaver = LB.DCSaver(dc)
        nPadding = 6

        if orientationLeft:

            rect.x += nPadding
            rect.width -= nPadding

        else:

            rect.width -= nPadding

        textRect = wx.Rect(*rect)
        imgRect = wx.Rect(*rect)

        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPointSize(int(font.GetPointSize() * self.GetParent().GetFontSizeMultiple()))

        if self.GetParent().GetFontBold():
            font.SetWeight(wx.FONTWEIGHT_BOLD)
        elif self.HasAGWFlag(LB.INB_BOLD_TAB_SELECTION) and selected:
            font.SetWeight(wx.FONTWEIGHT_BOLD)

        dc.SetFont(font)

        # First we define the rectangle for the text
        w, h = dc.GetTextExtent(text)

        #-------------------------------------------------------------------------
        # Label layout:
        # [ nPadding | Image | nPadding | Text | nPadding ]
        #-------------------------------------------------------------------------

        # Text bounding rectangle
        textRect.x += nPadding
        textRect.y = rect.y + int((rect.height - h)/2)
        textRect.width = rect.width - 2 * nPadding

        if bmp.IsOk() and not self.HasAGWFlag(LB.INB_SHOW_ONLY_TEXT):
            textRect.x += (bmp.GetWidth() + nPadding)
            textRect.width -= (bmp.GetWidth() + nPadding)

        textRect.height = h

        # Truncate text if needed
        caption = LB.ArtManager.Get().TruncateText(dc, text, textRect.width)

        # Image bounding rectangle
        if bmp.IsOk() and not self.HasAGWFlag(LB.INB_SHOW_ONLY_TEXT):

            imgRect.x += nPadding
            imgRect.width = bmp.GetWidth()
            imgRect.y = rect.y + (rect.height - bmp.GetHeight())/2
            imgRect.height = bmp.GetHeight()

        # Draw bounding rectangle
        if selected:

            # First we colour the tab
            dc.SetBrush(wx.Brush(self._coloursMap[LB.INB_ACTIVE_TAB_COLOUR]))

            if self.HasAGWFlag(LB.INB_BORDER):
                dc.SetPen(wx.Pen(self._coloursMap[LB.INB_TABS_BORDER_COLOUR]))
            else:
                dc.SetPen(wx.Pen(self._coloursMap[LB.INB_ACTIVE_TAB_COLOUR]))

            labelRect = wx.Rect(*rect)

            if orientationLeft:
                labelRect.width += 3
            else:
                labelRect.width += 3
                labelRect.x -= 3

            dc.DrawRoundedRectangle(labelRect, 3)

            if not orientationLeft and self.HasAGWFlag(LB.INB_DRAW_SHADOW):
                dc.SetPen(wx.BLACK_PEN)
                dc.DrawPoint(labelRect.x + labelRect.width - 1, labelRect.y + labelRect.height - 1)

        # Draw the text & bitmap
        if caption != "":

            if selected:
                dc.SetTextForeground(self._coloursMap[LB.INB_ACTIVE_TEXT_COLOUR])
            else:
                dc.SetTextForeground(self._coloursMap[LB.INB_TEXT_COLOUR])

            dc.DrawText(caption, textRect.x, textRect.y)
            imgInfo.SetTextRect(textRect)

        else:

            imgInfo.SetTextRect(wx.Rect())

        if bmp.IsOk() and not self.HasAGWFlag(LB.INB_SHOW_ONLY_TEXT):
            dc.DrawBitmap(bmp, imgRect.x, imgRect.y, True)

        # Drop shadow
        if self.HasAGWFlag(LB.INB_DRAW_SHADOW) and selected:

            sstyle = 0
            if orientationLeft:
                sstyle = BottomShadow
            else:
                sstyle = BottomShadowFull | RightShadow

            if self.HasAGWFlag(LB.INB_WEB_HILITE):

                # Always drop shadow for this style
                ArtManager.Get().DrawBitmapShadow(dc, rect, sstyle)

            else:

                if imgIdx+1 != self._nHoveredImgIdx:
                    ArtManager.Get().DrawBitmapShadow(dc, rect, sstyle)

        # Draw hover effect
        if hover:

            if self.HasAGWFlag(LB.INB_WEB_HILITE) and caption != "":
                self.DrawWebHover(dc, caption, textRect.x, textRect.y, selected)
            else:
                self.DrawRegularHover(dc, rect)

        # Update the page information bout position and size
        imgInfo.SetPosition(rect.GetPosition())
        imgInfo.SetSize(rect.GetSize())