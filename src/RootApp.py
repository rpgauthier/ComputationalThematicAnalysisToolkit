import logging
import locale

import wx

class RootApp(wx.App):
    '''Defines Root Application'''
    def InitLocale(self):
        '''Overides default local settings to handle windows issue with wxpython'''
        logger = logging.getLogger(__name__+".RootApp.InitLocale")
        logger.info("Starting")
        wx.App.InitLocale(self)
        wx.App.OSXEnableAutomaticTabbing(self, False)
        self.ResetLocale()
        lang, enc = locale.getdefaultlocale()
        self._initial_locale = wx.Locale(lang, lang[:2], lang)
        locale.setlocale(locale.LC_ALL, lang)
        logger.info("Finished")
