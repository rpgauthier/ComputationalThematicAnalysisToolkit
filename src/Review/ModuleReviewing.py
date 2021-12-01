import logging

import matplotlib as mpl
mpl.use('WXAgg')
import networkx as nx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import wx

import Common.Objects.Utilities.Generic as GenericUtilities
from Common.GUIText import Reviewing as GUIText
import Common.Objects.DataViews.Codes as Codes
import Common.Objects.GUIs.Codes as CodesGUIs
import Common.Notes as Notes

class ReviewingPanel(wx.Panel):
    def __init__(self, *args, **kw):
        logger = logging.getLogger(__name__+".ReportingPanel.__init__")
        logger.info("Starting")
        super().__init__(*args, **kw)
        main_frame = wx.GetApp().GetTopWindow()
        
        self.sizer = wx.BoxSizer()

        self.splitter = wx.SplitterWindow(self)

        self.themes_list_panel = wx.Panel(self.splitter)
        themes_sizer = wx.BoxSizer()
        self.themes_list_panel.SetSizer(themes_sizer)
        self.themes_model = Codes.ThemesViewModel() 
        self.themes_ctrl = Codes.ThemesViewCtrl(self.themes_list_panel, self.themes_model)
        themes_sizer.Add(self.themes_ctrl, 1, wx.ALL|wx.EXPAND, 5)

        self.themes_plot_panel = ThemePlotPlanel(self.splitter)

        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitVertically(self.themes_list_panel, self.themes_plot_panel)
        self.splitter.SetSashPosition(400)

        self.sizer.Add(self.splitter, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)


        self.SetSizerAndFit(self.sizer)

        #Notes panel for module
        self.notes_panel = Notes.NotesPanel(main_frame.notes_notebook, self)
        main_frame.notes_notebook.AddPage(self.notes_panel, GUIText.REVIEWING_LABEL)

        #Menu for Module
        self.actions_menu = wx.Menu()
        self.actions_menu_menuitem = None

        #setup the default visable state
        
        logger.info("Finished")

    def CodesUpdated(self):
        #Triggered by any function from this module or sub modules.
        #updates the datasets to perform a global refresh
        logger = logging.getLogger(__name__+".ReviewingPanel.CodesUpdated")
        logger.info("Starting")
        self.themes_model.Cleared()
        self.themes_ctrl.Expander(None)
        self.themes_plot_panel.Draw()
        logger.info("Finished")
    
    def ModeChange(self):
        logger = logging.getLogger(__name__+".ReportingPanel.CodesUpdated")
        logger.info("Starting")
        logger.info("Finished")

    def Load(self, saved_data):
        '''initalizes Reviewing Module with saved_data'''
        logger = logging.getLogger(__name__+".ReviewingPanel.Load")
        logger.info("Starting")
        self.Freeze()
        self.themes_model.Cleared()
        self.themes_ctrl.Expander(None)
        self.themes_plot_panel.Draw()
        if 'notes' in saved_data:
            self.notes_panel.Load(saved_data['notes'])
        self.Thaw()
        logger.info("Finished")

    def Save(self):
        '''saves current Collection Module's data'''
        logger = logging.getLogger(__name__+".ReviewingPanel.Save")
        logger.info("Starting")
        saved_data = {}
        saved_data['notes'] = self.notes_panel.Save()
        logger.info("Finished")
        return saved_data


class ThemePlotPlanel(wx.Panel):
    '''Panel for a TreemapPlot'''
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".NetworkPlotPlanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)
        self.figure = mpl.figure.Figure(tight_layout=True)
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.labels = {}
        self.annots = {}
        self.codes = {}
        self.themes = {}

        axis = self.figure.add_subplot(111)
        axis.axis("off")

        def OnHover(event):
            #if event.inaxes == axis:
            for key in self.annots:
                cont, ind = self.labels[key].contains(event)
                if cont:
                    self.annots[key].set_visible(True)
                else:
                    self.annots[key].set_visible(False)
            self.canvas.draw_idle()
        
        def OnClick(event):
            def ShowDialog(key):
                main_frame = wx.GetApp().GetTopWindow()
                if key in self.themes:
                    if key not in main_frame.theme_dialogs:
                        main_frame.theme_dialogs[key] = CodesGUIs.ThemeDialog(main_frame, self.themes[key], size=wx.Size(400,400))
                    main_frame.theme_dialogs[key].Show()
                    main_frame.theme_dialogs[key].SetFocus()
                elif key in self.themes:
                    if key not in main_frame.code_dialogs:
                        main_frame.code_dialogs[key] = CodesGUIs.CodeDialog(main_frame, self.codes[key], size=wx.Size(400,400))
                    main_frame.code_dialogs[key].Show()
                    main_frame.code_dialogs[key].SetFocus()
            found = False
            for key in self.labels:
                cont, ind = self.labels[key].contains(event)
                if cont:
                    ShowDialog(key)
                    found = True
            if not found:
                for key in self.annots:
                    cont, ind = self.annots[key].contains(event)
                    if cont:
                        ShowDialog(key)
                        break
            
                   

        self.canvas.mpl_connect('motion_notify_event', OnHover)
        self.canvas.mpl_connect('button_press_event', OnClick)
        self.canvas.draw()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizer(sizer)
        logger.info("Finished")

    def Draw(self):
        '''Draw the Treemap'''
        logger = logging.getLogger(__name__+".NetworkPlotPlanel.Draw")
        logger.info("Starting")

        main_frame = wx.GetApp().GetTopWindow()

        G = nx.Graph()
        top_theme_nodes = []
        colours_nodes = {}
        colours_labels = {}
        colours_annots = {}
        self.themes = {}
        self.codes = {}
        
        def FindThemeEdges(theme):
            self.themes[theme.key] = theme
            G.add_node(theme.key)
            if theme.colour_rgb not in colours_nodes:
                colours_nodes[theme.colour_rgb] = [theme.key]
                colours_labels[theme.colour_rgb] = {theme.key:GUIText.THEME+": "+theme.name}
                colours_annots[theme.colour_rgb] = {}
            else:
                colours_nodes[theme.colour_rgb].append(theme.key)
                colours_labels[theme.colour_rgb][theme.key] = GUIText.THEME+": "+theme.name
            for code in theme.GetCodes(main_frame.codes):
                if code.key not in self.codes:
                    self.codes[code.key] = code
                    G.add_node(code.key)
                    if code.colour_rgb not in colours_nodes:
                        colours_nodes[code.colour_rgb] = [code.key]
                        colours_labels[code.colour_rgb] = {code.key:GUIText.CODE+": "+code.name}
                        colours_annots[code.colour_rgb] = {code.key:GUIText.CODE+": "+code.name+"\n"+str(len(code.connections))+" "+GUIText.DOCUMENT}
                    else:
                        colours_nodes[code.colour_rgb].append(code.key)
                        colours_labels[code.colour_rgb][code.key] = GUIText.CODE+": "+code.name
                        colours_annots[code.colour_rgb][code.key] = GUIText.CODE+": "+code.name+"\n"+str(len(code.connections))+" "+GUIText.DOCUMENT
                G.add_edge(theme.key, code.key)
            for subtheme_key in theme.subthemes:
                FindThemeEdges(theme.subthemes[subtheme_key])
                G.add_edge(theme.key, subtheme_key)

        for theme_key in main_frame.themes:
            top_theme_nodes.append(theme_key)
            FindThemeEdges(main_frame.themes[theme_key])
        
        def FindCodeEdges(code):
            if code.key not in self.codes:
                self.codes[code.key] = code
                G.add_node(code.key)
                if code.colour_rgb not in colours_nodes:
                    colours_nodes[code.colour_rgb] = [code.key]
                    colours_labels[code.colour_rgb] = {code.key:GUIText.CODE+": "+code.name}
                    colours_annots[code.colour_rgb] = {code.key:GUIText.CODE+": "+code.name+"\n"+str(len(code.connections))+" "+GUIText.DOCUMENT}
                else:
                    colours_nodes[code.colour_rgb].append(code.key)
                    colours_labels[code.colour_rgb][code.key] = GUIText.CODE+": "+code.name
                    colours_annots[code.colour_rgb][code.key] = GUIText.CODE+": "+code.name+"\n"+str(len(code.connections))+" "+GUIText.DOCUMENT
            for subcode_key in code.subcodes:
                FindCodeEdges(code.subcodes[subcode_key])
                G.add_edge(code.key, subcode_key)

        for code_key in main_frame.codes:
            FindCodeEdges(main_frame.codes[code_key])
        
        pos = nx.kamada_kawai_layout(G)
        #pos = nx.circular_layout(G)
        #pos = nx.spectral_layout(G)
        #pos = nx.shell_layout(G, nlist=[theme_nodes, code_nodes])
        #pos = nx.spring_layout(G, fixed=top_theme_nodes, pos=pos)

        self.figure.clf()
        self.labels = {}
        self.annots = {}
        axis = self.figure.add_subplot(111)
        axis.axis("off")
        for colour_rgb in colours_nodes:
            bg_colour, fg_colour = GenericUtilities.BackgroundAndForegroundColour(colour_rgb)
            colour_rgb_background = (bg_colour.Red()/255, bg_colour.Green()/255, bg_colour.Blue()/255,)
            colour_rgb_foreground = (fg_colour.Red()/255, fg_colour.Green()/255, fg_colour.Blue()/255,)
            nx.draw_networkx_nodes(G, pos, ax=axis, nodelist=colours_nodes[colour_rgb], alpha=0)
            if len(colours_labels[colour_rgb]) > 0:
                ret = nx.draw_networkx_labels(G, pos, ax=axis, labels=colours_labels[colour_rgb], font_color=colour_rgb_foreground, bbox=dict(facecolor=colour_rgb_background, alpha=1))
                self.labels.update(ret)
            if len(colours_annots[colour_rgb]) > 0:
                ret = nx.draw_networkx_labels(G, pos, ax=axis, labels=colours_annots[colour_rgb], font_color=colour_rgb_foreground, bbox=dict(facecolor=colour_rgb_background, alpha=1))
                self.annots.update(ret)
        nx.draw_networkx_edges(G, pos, ax=axis)

        for key in self.annots:
            self.annots[key].set_visible(False)

        self.canvas.draw()

        logger.info("Finished")


