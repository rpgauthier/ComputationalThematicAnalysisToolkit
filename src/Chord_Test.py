
'''
import gensim
import pyLDAvis.gensim

import wx
import wx.html2

path = 'C:/Users/Robert Gauthier/Documents/School/PHD_Studies/Autobiographical Design/Toolkit/Workspaces/test2/LDA/test2/'

dictionary = gensim.corpora.Dictionary.load(path+'ldadictionary.dict')
corpus = gensim.corpora.MmCorpus(path+'ldacorpus.mm')
lda = gensim.models.ldamodel.LdaModel.load(path+'ldamodel.lda')


print(dictionary.token2id['game'])

print(sum(dictionary.cfs.values()))
print(dictionary.num_pos)

#word freq
print(str(dictionary.cfs[dictionary.token2id['game']]))
print(str(dictionary.cfs[dictionary.token2id['game']]/dictionary.num_pos))

#document freq
print(str(dictionary.dfs[dictionary.token2id['game']]))
print(str(dictionary.dfs[dictionary.token2id['game']]/dictionary.num_docs))
'''

'''
import pandas as pd
import holoviews as hv
from holoviews import opts, dim
from bokeh.sampledata.les_mis import data
import numpy as np


hv.extension('bokeh')
hv.output(size=200)

total_docs = 10000

links = [[0, 1, 2000/total_docs],
         [0, 2, 200/total_docs],
         [1, 2, 8000/total_docs]]


links = pd.DataFrame(links)
links.columns= ['source', 'target', 'value']
#links = hv.Dataset(links)
print(links.head())

nodes = [[0, "Topic 1", 1],
         [1, "Topic 2", 1],
         [2, "Topic 3", 1],
        ]
nodes = pd.DataFrame(nodes)
nodes.columns = ["index", "name", "group"]

print(data['nodes'])

nodes = hv.Dataset(nodes, 'index')
print(nodes.data.head())


chord = hv.Chord((links, nodes))
chord.opts(opts.Chord(cmap='Category20', edge_color=dim('source').str(),
               height=800, labels='name', node_color=dim('index').str(), width=800))


renderer = hv.renderer('bokeh')

# Using renderer save
path = 'C:/Users/Robert Gauthier/Documents/School/PHD_Studies/Autobiographical Design/Toolkit/Workspaces/test2/LDA/test2/'
renderer.save(chord, path+'cordgraph.html')
'''

'''
from chord import Chord

matrix = [[0,  0.5, 0.4, 0.3],
          [0.5,  0, 0.4, 0.3],
          [0.4, 0.3, 0, 0.2],
          [0.3, 0.2, 0.1, 0]]

names = ['One', 'Two', 'Three', 'Four']


path = 'C:/Users/Robert Gauthier/Documents/School/PHD_Studies/Autobiographical Design/Toolkit/Workspaces/test2/LDA/test2/'
Chord(matrix, names, arc_numbers=True,
      symmetric=False).to_html(path+'test1.html')
'''

from External.mpl_chord_diagram import chord_diagram
import matplotlib.pyplot as plt
import pandas as pd
import gensim

path = 'C:/Users/Robert Gauthier/Documents/School/PHD_Studies/Autobiographical Design/Toolkit/Workspaces/StopGaming_20120101-20201231_v2/LDA/test/'
#path = 'C:/Users/Robert Gauthier/Documents/School/PHD_Studies/Autobiographical Design/Toolkit/Workspaces/test2/LDA/test1/'

dictionary = gensim.corpora.Dictionary.load(path+'ldadictionary.dict')
corpus = gensim.corpora.MmCorpus(path+'ldacorpus.mm')
lda = gensim.models.ldamodel.LdaModel.load(path+'ldamodel.lda')

dt_prob = list(lda.get_document_topics(
    corpus, minimum_probability=0.0, minimum_phi_value=0))

dt_prob = [[topic[1] for topic in doc] for doc in dt_prob]

dt_df = pd.DataFrame(dt_prob)


dt_maxs = dt_df.max(axis=1)
dt_mins = dt_df.min(axis=1)

cutoff_max = dt_maxs.max()
dt_maxs.idxmin() 
cutoff_default = dt_maxs.min()
cutoff_min = dt_mins.min()

print(cutoff_default)
print(dt_maxs.idxmin())
print(dt_df.iloc[dt_maxs.idxmin()])

# max_cutoff = max of maxs
# default = min of maxs
# min_cutoff = min of mins


td_dist = []
outer_circle = []
categorized_docs = set()

for i in range(0, len(dt_df.columns)):
    topic_docs_df = dt_df[dt_df[i] >= cutoff_default]
    outer_circle.append(len(topic_docs_df))
    shared_docs = set()
    td_first_half = []
    td_middle = []
    td_last_half = []

    # before topic
    if i > 0:
        for j in range(0, i):
            shared_docs_df = topic_docs_df[topic_docs_df[j] >= cutoff_default]
            shared_docs.update(list(shared_docs_df.index.values))
            if len(topic_docs_df) > 0:
                #td_first_half.append(round(len(shared_docs_df)/len(dt_df), 2))
                td_first_half.append(round(len(shared_docs_df)/len(topic_docs_df), 2))
                # td_first_half.append(len(shared_docs_df))
            else:
                td_first_half.append(0)

    # after topic
    if i < len(dt_df.columns)-1:
        for j in range(i+1, len(dt_df.columns)):
            shared_docs_df = topic_docs_df[topic_docs_df[j] >= cutoff_default]
            shared_docs.update(list(shared_docs_df.index.values))
            if len(topic_docs_df) > 0:
                #td_last_half.append(round(len(shared_docs_df)/len(dt_df), 2))
                td_last_half.append(round(len(shared_docs_df)/len(topic_docs_df), 2))
                # td_last_half.append(len(shared_docs_df))
            else:
                td_last_half.append(0)

    # after topic
    if len(topic_docs_df) > 0:
        #td_middle.append(round((len(topic_docs_df)-len(shared_docs))/len(dt_df), 2))
        td_middle.append(round((len(topic_docs_df)-len(shared_docs))/len(topic_docs_df), 2))
        # td_middle.append(len(topic_docs_df)-len(shared_docs))
    else:
        td_middle.append(0)

    td_row = td_first_half + td_middle + td_last_half
    td_dist.append(td_row)
    categorized_docs.update(list(topic_docs_df.index.values))



#from mpl_chord_diagram import chord_diagram

# matrix = [[0,  10, 20, 25, 15],
#          [10,  0, 40, 13, 11],
#          [20, 40, 0, 8, 14],
#          [25, 13, 8, 0, 19],
#          [15, 11, 14, 19, 0]
#          ]
#matrix = dpt_dist

#names = topic_labels
names = ['Topic 1',
         'Topic 2',
         'Topic 3',
         'Topic 4',
         'Topic 5',
         'Topic 6',
         'Topic 7',
         'Topic 8',
         'Topic 9',
         'Topic 10']

#calculate uncategorized document count to show that is not being captured by current cutoff
if len(categorized_docs) < len(dt_prob):
    new_row = []
    for td_row in td_dist:
        td_row.append(0.0)
        new_row.append(0.0)
    new_row.append(0.0)
    td_dist.append(new_row)
    outer_circle.append(len(dt_prob)-len(categorized_docs))
    names.append("Uncategorized")

print(categorized_docs.difference(set(dt_df.index.values)))
print(set(dt_df.index.values).difference(categorized_docs))
print(pd.DataFrame(td_dist))
print(outer_circle)

chord_diagram(td_dist, outer_circle=outer_circle, names=names, chordwidth=0.1,
              sort="size", rotate_names=True, show=True)

# plt.show()
