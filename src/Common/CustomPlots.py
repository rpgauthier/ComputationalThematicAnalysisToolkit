'''For Plotting visualizations with wx'''
import logging

from wordcloud import WordCloud
import squarify
import matplotlib as mpl
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
mpl.use('WXAgg')
import networkx as nx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import pyLDAvis
from External.mpl_chord_diagram import chord_diagram
#from External.matplotlib_zoom import simp_zoom
import pandas as pd

import wx
import wx.html2

class NetworkPlotPlanel(wx.Panel):
    '''Panel for a TreemapPlot'''
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".NetworkPlotPlanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)
        self.figure = mpl.figure.Figure(tight_layout=True)
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.labels = {}
        self.annots = {}

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

        self.canvas.mpl_connect('motion_notify_event', OnHover)
        self.canvas.draw()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizer(sizer)
        logger.info("Finished")

    def Draw(self, edge_map, label_dict, word_cloud_freq=None, weight_map=None, annot_dict={}):
        '''Draw the Treemap'''
        logger = logging.getLogger(__name__+".NetworkPlotPlanel.Update")
        logger.info("Starting")

        G = nx.Graph()
        #G = nx.MultiGraph()
        #Add children nodes that connect to parent nodes
        parent_nodes = []
        parent_labels = {}
        single_parent_child_nodes = []
        single_parent_child_labels = {}
        single_parent_child_annots = {}
        multiple_parent_child_nodes = []
        multiple_parent_child_labels = {}
        multiple_parent_child_annots = {}
        for parent in edge_map:
            parent_labels[parent] = label_dict[parent]
            for child in edge_map[parent]:
                if child not in single_parent_child_nodes and child not in multiple_parent_child_nodes:
                    single_parent_child_nodes.append(child)
                    single_parent_child_labels[child] = label_dict[child]
                    if child in annot_dict:
                        single_parent_child_annots[child] = annot_dict[child]
                elif child not in multiple_parent_child_nodes:
                     multiple_parent_child_nodes.append(child)
                     multiple_parent_child_labels[child] = label_dict[child]
                     if child in annot_dict:
                        multiple_parent_child_annots[child] = annot_dict[child]
                     single_parent_child_nodes.remove(child)
                     del single_parent_child_labels[child]
                     if child in annot_dict:
                        del single_parent_child_annots[child]
                if parent not in parent_nodes:
                    parent_nodes.append(parent)
                if weight_map is not None:
                    G.add_edge(parent, child, weight=weight_map[parent][child])
                else:
                    G.add_edge(parent, child)
        if word_cloud_freq != None:
            G.remove_nodes_from(single_parent_child_nodes)

        #pos = nx.kamada_kawai_layout(G)
        #pos = nx.circular_layout(G)
        pos = nx.shell_layout(G, nlist=[multiple_parent_child_nodes, parent_nodes, single_parent_child_nodes])
        pos = nx.spring_layout(G, fixed=parent_nodes, pos=pos)
        #pos = nx.spectral_layout(G)

        if word_cloud_freq != None:
            parent_wordcloudimages = {}
            for parent in parent_nodes:
                wordcloud = WordCloud().fit_words(word_cloud_freq[parent])
                parent_wordcloudimages[parent] = wordcloud.to_image()

        self.figure.clf()
        self.labels = {}
        self.annots = {}
        axis = self.figure.add_subplot(111)
        axis.axis("off")
        if word_cloud_freq == None:
            nx.draw_networkx_nodes(G, pos, ax=axis, nodelist=parent_nodes, node_color='red', alpha=0)
            nx.draw_networkx_labels(G, pos, ax=axis, labels=parent_labels, font_weight='bold', bbox=dict(fc="red"))
            nx.draw_networkx_nodes(G, pos, ax=axis, nodelist=single_parent_child_nodes, node_color='green', alpha=0)
            self.labels.update(nx.draw_networkx_labels(G, pos, ax=axis, labels=single_parent_child_labels, bbox=dict(fc="green")))
            self.annots.update(nx.draw_networkx_labels(G, pos, ax=axis, labels=single_parent_child_annots, bbox=dict(fc="green")))
        else:
            for parent in parent_nodes:
                G.add_node(parent, image=parent_wordcloudimages[parent])
            nx.draw_networkx_nodes(G, pos, ax=axis)

            for n in parent_nodes:
                im = OffsetImage(parent_wordcloudimages[n], zoom=0.25)
                xx,yy=pos[n] # figure coordinates
                ab = AnnotationBbox(im, (xx, yy), frameon=False)
                axis.add_artist(ab)


            #x, y = np.atleast_1d(x, y)
            #artists = []
            #for x0, y0 in zip(x, y):
            #    ab = AnnotationBbox(im, (x0, y0), xycoords='data', frameon=False)
            #    artists.append(ax.add_artist(ab))

            #trans=axis.transData.transform
            #trans2=self.figure.transFigure.inverted().transform
            #piesize=0.2 # this is the image size
            #p2=piesize/2.0
            #for n in parent_nodes:
            #    xx,yy=trans(pos[n]) # figure coordinates
            #    xa,ya=trans2((xx,yy)) # axes coordinates
            #    a = self.figure.add_axes([xa-p2,ya-p2, piesize, piesize])
            #    a.set_aspect('equal')
            #    a.imshow(parent_wordcloudimages[n])
            #    a.axis('off')
        nx.draw_networkx_nodes(G, pos, ax=axis, nodelist=multiple_parent_child_nodes, node_color='green', alpha=0)
        self.labels.update(nx.draw_networkx_labels(G, pos, ax=axis, labels=multiple_parent_child_labels, bbox=dict(fc="green")))
        self.annots.update(nx.draw_networkx_labels(G, pos, ax=axis, labels=multiple_parent_child_annots, bbox=dict(fc="green")))
        nx.draw_networkx_edges(G, pos, ax=axis)

        for key in self.annots:
            self.annots[key].set_visible(False)

        self.canvas.draw()

        logger.info("Finished")

class TreemapPlotPlanel(wx.Panel):
    '''Panel for a TreemapPlot'''
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".TreemapPlotPlanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)
        self.figure = mpl.figure.Figure()
        self.canvas = FigureCanvas(self, -1, self.figure)

        axis = self.figure.add_subplot(111)
        axis.axis("off")
        self.canvas.draw()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.info("Finished")

    def Draw(self, values, labels):
        '''Draw the Treemap'''
        logger = logging.getLogger(__name__+".TreemapPlotPlanel.Update")
        logger.info("Starting")

        if len(values) > 0:
            cmap = mpl.cm.get_cmap("Oranges")
            mini = min(values)
            maxi = max(values)
            norm = mpl.colors.Normalize(vmin=mini, vmax=maxi)
            colors = [cmap(norm(value)) for value in values]

            self.figure.clf()
            axis = self.figure.add_subplot(111)
            axis.axis("off")

            axis = squarify.plot(sizes=values, label=labels, color=colors, ax=axis)
            #axis.imshow()
            self.canvas.draw()
        else:
            logger.info("No data values to plot")
        logger.info("Finished")

class WordCloudPlotPlanel(wx.Panel):
    '''Panel for a WordCloudPlot'''
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".WordCloudPlotPlanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)
        self.figure = mpl.figure.Figure(dpi=None)
        self.canvas = FigureCanvas(self, -1, self.figure)

        axis = self.figure.add_subplot(111)
        axis.axis("off")
        self.canvas.draw()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)
        logger.info("Finished")

    def Draw(self, word_frequencies):
        '''Draw the WordCloud'''
        logger = logging.getLogger(__name__+".WordCloudPlotPlanel.Update")
        logger.info("Starting")
        self.figure.clf()
        axis = self.figure.add_subplot(111)
        axis.axis("off")
        wordcloud = WordCloud().fit_words(dict(word_frequencies))
        axis.imshow(wordcloud)
        self.canvas.draw()
        logger.info("Finished")


class pyLDAvisPanel(wx.Panel):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".pyLDAvisPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)

        
        self.browser = wx.html2.WebView.New(self)
        self.browser.MSWSetEmulationLevel()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.browser, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        logger.info("Finished")
    
    def Render(self, path, dictionary, corpus, lda):
        logger = logging.getLogger(__name__+"pyLDAvisPanel.__init__")
        logger.info("Starting")

        data = pyLDAvis.gensim.prepare(lda, corpus, dictionary, sort_topics=False)
        try:
            html = pyLDAvis.prepared_data_to_html(data)
            html_file = open(path+"/pyLDAvis.html","w")
            html_file.write(html)
            html_file.close()

            self.browser.LoadURL(path+"/pyLDAvis.html")
        except TypeError:
            self.browser.SetPage("", "")

        logger.info("Finished")

class ChordPlotPanel(wx.Panel):
    '''Panel for a TreemapPlot'''
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".ChordPlotPanel.__init__")
        logger.info("Starting")
        wx.Panel.__init__(self, parent)

        self.dt_df = None
        self.cutoff = None
        self.part_keys = None
        self.part_names = None
        self.td_dist = None
        self.outer_circle = None

        self.figure = mpl.figure.Figure()
        axis = self.figure.add_subplot(111, frameon=False)
        #self.figure.add_axes([0,0,1,1])
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.canvas.draw()

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizer(sizer)
        logger.info("Finished")

    def Draw(self, model_documenttopart_prob, parts, cutoff, word_cloud_freq):
        '''Draw the Treemap'''
        logger = logging.getLogger(__name__+".ChordPlotPanel.Draw")
        logger.info("Starting")
        
        self.dt_df = pd.DataFrame(model_documenttopart_prob)

        #dt_maxs = self.dt_df.max(axis=1)
        #self.cutoff = dt_maxs.min()
        self.cutoff = cutoff

        #merge parts as approriate based on parts map
        self.part_keys = []
        self.part_names = []
        for part_key in parts:
            self.part_keys.append(part_key)
            if parts[part_key].label != "":
                self.part_names.append(parts[part_key].label)
            else:
                self.part_names.append(parts[part_key].name)

        self.CreateTopicDocumentDistribution()

        if word_cloud_freq != None:
            parent_wordcloudimages = []
            for part_key in parts:
                if len(word_cloud_freq[part_key]) > 0:
                    for word in word_cloud_freq[part_key]:
                        if word_cloud_freq[part_key][word] == 0:
                            word_cloud_freq[part_key][word] = 10**-15
                    wordcloud = WordCloud(background_color='white').fit_words(word_cloud_freq[part_key])
                    parent_wordcloudimages.append(wordcloud.to_image())
                else:
                    parent_wordcloudimages.append(None)

        self.figure.clf()

        axis = self.figure.add_subplot(111)
        chord_diagram(self.td_dist, outer_circle=self.outer_circle, names=self.part_names, chordwidth=0.1,
                      sort="size", rotate_names=True, ax=axis, name_images=parent_wordcloudimages)
        self.canvas.draw()

        axis.set_xlim([1.2, -1.2])
        axis.set_ylim([1.2, -1.2])
        axis.figure.canvas.draw_idle()
        #bugged in that all mouse wheel scrolls count as down on windows
        #simp_zoom.zoom_factory(axis, base_scale=1.5)
        
        logger.info("Finished")

    def CreateTopicDocumentDistribution(self):
        logger = logging.getLogger(__name__+".ChordPlotPanel.CreateTopicDocumentDistribution")
        logger.info("Starting")

        if "Other" in self.part_names:
            self.part_names.remove("Other")

        self.td_dist = []
        self.outer_circle = []
        categorized_docs = set()
        for key in self.part_keys:
            if key in self.dt_df.columns:
                topic_docs_df = self.dt_df[self.dt_df[key] >= self.cutoff]
                self.outer_circle.append(len(topic_docs_df))
                shared_docs = set()
                td_first_half = []
                td_middle = []
                td_last_half = []

                # before topic
                if self.part_keys.index(key) > 0:
                    for j in self.part_keys[0:self.part_keys.index(key)]:
                        shared_docs_df = topic_docs_df[topic_docs_df[j] >= self.cutoff]
                        shared_docs.update(list(shared_docs_df.index.values))
                        if len(topic_docs_df) > 0:
                            td_first_half.append(round(len(shared_docs_df)/len(topic_docs_df), 2))
                        else:
                            td_first_half.append(0)

                # after topic
                if self.part_keys.index(key) < len(self.part_keys)-1:
                    for j in self.part_keys[self.part_keys.index(key)+1:len(self.part_keys)]:
                        shared_docs_df = topic_docs_df[topic_docs_df[j] >= self.cutoff]
                        shared_docs.update(list(shared_docs_df.index.values))
                        if len(topic_docs_df) > 0:
                            td_last_half.append(round(len(shared_docs_df)/len(topic_docs_df), 2))
                        else:
                            td_last_half.append(0)

                # after topic
                if len(topic_docs_df) > 0:
                    td_middle.append(round((len(topic_docs_df)-len(shared_docs))/len(topic_docs_df), 2))
                else:
                    td_middle.append(0)

                td_row = td_first_half + td_middle + td_last_half
                self.td_dist.append(td_row)
                categorized_docs.update(list(topic_docs_df.index.values))

        logger.info("Finished")
