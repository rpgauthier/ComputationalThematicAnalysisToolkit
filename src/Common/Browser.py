import wx

from cefpython3 import cefpython as cef
import platform
import sys
import os

class BrowserPanel(wx.Panel):
    def __init__(self, parent, size=wx.DefaultSize):
        wx.Panel.__init__(self, parent, size=size, style=wx.WANTS_CHARS)

        self.browser = None

        self.WINDOWS = (platform.system() == "Windows")
        self.LINUX = (platform.system() == "Linux")
        self.MAC = (platform.system() == "Darwin")

        if self.MAC:
            try:
                # noinspection PyUnresolvedReferences
                from AppKit import NSApp
            except ImportError:
                print("[wxpython.py] Error: PyObjC package is missing, "
                    "cannot fix Issue #371")
                print("[wxpython.py] To install PyObjC type: "
                    "pip install -U pyobjc")
                sys.exit(1)

        def scale_window_size_for_high_dpi(width, height):
            """Scale window size for high DPI devices. This func can be
            called on all operating systems, but scales only for Windows.
            If scaled value is bigger than the work area on the display
            then it will be reduced."""
            if not self.WINDOWS:
                return width, height
            (_, _, max_width, max_height) = wx.GetClientDisplayRect().Get()
            # noinspection PyUnresolvedReferences
            (width, height) = cef.DpiAware.Scale((width, height))
            if width > max_width:
                width = max_width
            if height > max_height:
                height = max_height
            return width, height
        
        

        if self.LINUX:
            cef.WindowUtils.InstallX11ErrorHandlers()

        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        if self.MAC:
            # Make the content view for the window have a layer.
            # This will make all sub-views have layers. This is
            # necessary to ensure correct layer ordering of all
            # child views and their layers. This fixes Window
            # glitchiness during initial loading on Mac (Issue #371).
            NSApp.windows()[0].contentView().setWantsLayer_(True)
        if self.LINUX:
            # On Linux must show before embedding browser, so that handle
            # is available (Issue #347).
            self.Show()
            # In wxPython 3.0 and wxPython 4.0 on Linux handle is
            # still not yet available, so must delay embedding browser
            # (Issue #349).
            if wx.version().startswith("3.") or wx.version().startswith("4."):
                wx.CallLater(100, self.embed_browser)
            else:
                # This works fine in wxPython 2.8 on Linux
                self.embed_browser()
        else:
            self.embed_browser()
            self.Show()

    def embed_browser(self):
        window_info = cef.WindowInfo()
        (width, height) = self.GetClientSize().Get()
        assert self.GetHandle(), "Window handle not available"
        window_info.SetAsChild(self.GetHandle(),
                               [0, 0, width, height])
        self.browser = cef.CreateBrowserSync(window_info,
                                             url="https://www.google.com/")
        self.browser.SetClientHandler(FocusHandler())

    def OnSetFocus(self, _):
        if not self.browser:
            return
        if self.WINDOWS:
            cef.WindowUtils.OnSetFocus(self.GetHandle(),
                                       0, 0, 0)
        self.browser.SetFocus(True)

    def OnSize(self, _):
        if not self.browser:
            return
        if self.WINDOWS:
            cef.WindowUtils.OnSize(self.GetHandle(),
                                   0, 0, 0)
        elif self.LINUX:
            (x, y) = (0, 0)
            (width, height) = self.GetSize().Get()
            self.browser.SetBounds(x, y, width, height)
        self.browser.NotifyMoveOrResizeStarted()

    def OnClose(self, event):
        print("[wxpython.py] OnClose called")
        if not self.browser:
            # May already be closing, may be called multiple times on Mac
            return

        if self.MAC:
            # On Mac things work differently, other steps are required
            self.browser.CloseBrowser()
            self.clear_browser_references()
            self.Destroy()
            cef.Shutdown()
            wx.GetApp().ExitMainLoop()
            # Call _exit otherwise app exits with code 255 (Issue #162).
            # noinspection PyProtectedMember
            os._exit(0)
        else:
            # Calling browser.CloseBrowser() and/or self.Destroy()
            # in OnClose may cause app crash on some paltforms in
            # some use cases, details in Issue #107.
            self.browser.ParentWindowWillClose()
            event.Skip()
            self.clear_browser_references()

    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None

class FocusHandler(object):
    def OnGotFocus(self, browser, **_):
        # Temporary fix for focus issues on Linux (Issue #284).
        if (platform.system() == "Linux"):
            print("[wxpython.py] FocusHandler.OnGotFocus:"
                        " keyboard focus fix (Issue #284)")
            browser.SetFocus(True)