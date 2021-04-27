import logging
import locale

import wx
import wx.lib.mixins.inspection

#
class RootApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
    '''Defines Root Application'''
    def InitLocale(self):
        '''Overides default local settings to handle windows issue with wxpython'''
        logger = logging.getLogger(__name__+".RootApp.InitLocale")
        logger.info("Starting")
        wx.App.InitLocale(self)
        self.ResetLocale()
        lang, enc = locale.getdefaultlocale()
        self._initial_locale = wx.Locale(lang, lang[:2], lang)
        locale.setlocale(locale.LC_ALL, lang)
        logger.info("Finished")
