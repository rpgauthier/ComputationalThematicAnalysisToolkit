'''Constants for MachineThematicAnalysis Toolkit'''
import sys
import os
import shutil
import platform
import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB

CUR_VER = '0.8.5'

#Variables to configure GUI
FNB_STYLE = FNB.FNB_DEFAULT_STYLE|FNB.FNB_HIDE_ON_SINGLE_TAB|FNB.FNB_NO_X_BUTTON|FNB.FNB_FF2

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

PHASE_LABEL_SIZE = 16
SUBMODULE_LABEL_SIZE = 15
LABEL_SIZE = 14
LABEL_FAMILY = wx.DEFAULT
LABEL_STYLE = wx.NORMAL
LABEL_WEIGHT = wx.NORMAL
LABEL_UNDERLINE = True

if getattr(sys, 'frozen', False):
    # this is a Pyinstaller bundle
    ROOT_PATH = sys._MEIPASS
else:
    # normal python process
    ROOT_PATH = os.getcwd()
FONTS_PATH = os.path.join(ROOT_PATH, 'Fonts')
IMAGES_PATH = os.path.join(ROOT_PATH, 'Images')

SAVE_DATA_PATH = os.path.realpath(os.path.expanduser('~/Documents/ComputationalThematicAnalysisToolkit.nosync'))
old_SAVE_DATA_PATH = os.path.realpath(os.path.expanduser('~/Documents/ComputationalThematicAnalysisToolkit'))
if not os.path.exists(SAVE_DATA_PATH):
    if os.path.exists(old_SAVE_DATA_PATH):
        os.rename(old_SAVE_DATA_PATH, SAVE_DATA_PATH)
    else:
        os.makedirs(SAVE_DATA_PATH)
if platform.system() == 'Windows':
    APP_DATA_PATH = os.path.realpath(os.path.expanduser('~/AppData/Local/ComputationalThematicAnalysisToolkit'))
else:
    APP_DATA_PATH = os.path.realpath(os.path.expanduser('~/Library/ComputationalThematicAnalysisToolkit'))
if not os.path.exists(APP_DATA_PATH):
    os.makedirs(APP_DATA_PATH)

SAVED_WORKSPACES_PATH = os.path.realpath(os.path.join(SAVE_DATA_PATH, 'Saved_Workspaces'))
if not os.path.exists(SAVED_WORKSPACES_PATH):
    os.makedirs(SAVED_WORKSPACES_PATH)

DATA_PATH = os.path.realpath(os.path.join(SAVE_DATA_PATH, 'Data'))
if not os.path.exists(DATA_PATH):
    old_DATA = os.path.realpath(os.path.join(APP_DATA_PATH, 'Data'))
    if os.path.exists(old_DATA):
        shutil.move(old_DATA, SAVE_DATA_PATH)
    else:
        os.makedirs(DATA_PATH)

CURRENT_WORKSPACE_PATH = os.path.realpath(os.path.join(APP_DATA_PATH, 'Current_Workspace'))
old_CURRENT_WORKSPACE = os.path.realpath(os.path.join(SAVE_DATA_PATH, 'Current_Workspace'))
if not os.path.exists(CURRENT_WORKSPACE_PATH):
    if os.path.exists(old_CURRENT_WORKSPACE):
        shutil.move(old_CURRENT_WORKSPACE, APP_DATA_PATH)
    else:
        os.makedirs(CURRENT_WORKSPACE_PATH)

AUTOSAVE_PATH = os.path.realpath(os.path.join(CURRENT_WORKSPACE_PATH, 'AutoSave'))

LOG_PATH = os.path.realpath(os.path.join(APP_DATA_PATH, 'Logs'))
old_LOG = os.path.realpath(os.path.join(SAVE_DATA_PATH, 'Logs'))
if not os.path.exists(LOG_PATH):
    if os.path.exists(old_LOG):
        shutil.move(old_LOG, APP_DATA_PATH)
    else:
        os.makedirs(LOG_PATH)


#Menu Options
# removed to use built in id generator wx.ID_ANY

#Module Specific Variables
##Filtering
TOKEN_TEXT_IDX = 0
TOKEN_STEM_IDX = 1
TOKEN_LEMMA_IDX = 2
TOKEN_POS_IDX = 3
TOKEN_SPACY_STOPWORD_IDX = 4
TOKEN_TEXT_TFIDF_IDX = 5
TOKEN_STEM_TFIDF_IDX = 6
TOKEN_LEMMA_TFIDF_IDX = 7
TOKEN_ENTRIES = 'entries'
TOKEN_WORDS = 'words'
TOKEN_POS = 'pos'
TOKEN_NUM_WORDS = 'num_of_words'
TOKEN_PER_WORDS = 'per_of_words'
TOKEN_NUM_DOCS = 'num_of_docs'
TOKEN_PER_DOCS = 'per_of_docs'
TOKEN_SPACY_STOPWORD = 'spacy_stopword'
TOKEN_REMOVE_FLG = 'removed_flg'
TOKEN_TFIDF = 'tfidf_range'
FILTER_RULE_ANY = '<ANY>'
FILTER_RULE_REMOVE = 'remove'
FILTER_RULE_INCLUDE = 'include'
FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS = 'remove spacy auto stopwords'
FILTER_TFIDF_REMOVE = 'remove tokens where their tfidf is '
FILTER_TFIDF_INCLUDE = 'include tokens where their tfidf is '
FILTER_TFIDF_LOWER = ' in the lower '
FILTER_TFIDF_UPPER = ' in the upper  '
###Token Filters
AVALIABLE_DATASET_LANGUAGES1 = ['eng-sm', 'fre-sm'] #removed eng-trf and fre-trf due to difficulties with preparing installations -- Sept 21, 2021
AVALIABLE_DATASET_LANGUAGES2 = ['English', 'French']

# dialogs
TWITTER_DIALOG_SIZE = wx.Size(350, -1)
OPTIONS_DIALOG_SIZE = wx.Size(350, 300)

#definition of fields available for use from the retrievers
available_fields = {
    ('Reddit', 'submission',): {
        'id': {
            'desc': "the unique Reddit Submission id (may not be unique across other sources/types",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'url': {
            'desc': "a url link to the original source of the data",
            'type': 'url',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'created_utc': {
            'desc': "The UTC time stamp of when the submission was created",
            'type': 'UTC-timestamp',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'title': {
            'desc': "the raw title of the submission.",
            'type': 'string',
            'computation_fields_default': True,
            'label_fields_default': True,
            },
        },
        'selftext': {
            'desc': "the raw text of the submission.",
            'type': 'string',
            'computation_fields_default': True,
            'label_fields_default': False,
            },
        'author': {
            'desc': "the account name of the poster",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'author_flair_css_class': {
            'desc': "the CSS class f the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'num_comments': {
            'desc': "the number of comments made under this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'num_crossposts': {
            'desc': "the number of crossposts of this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
    ('Reddit', 'comment',): {
        'id': {
            'desc': 'unique Reddit Comment id (may not be unique across other sources/types)',
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'url': {
            'desc': "a url link to the original source of the data",
            'type': 'url',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'created_utc': {
            'desc': "The UTC time stamp of when the comment was created",
            'type': 'UTC-timestamp',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'body': {
            'desc': "the raw text of the comment.",
            'type': 'string',
            'computation_fields_default': True,
            'label_fields_default': True,
            },
        'author': {
            'desc': "the account name of the poster",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'author_flair_css_class': {
            'desc': "the CSS class of the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'link_id': {
            'desc': "A reference id that can link a comment to it's associated submission's id.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'parent_id': {
            'desc': "A reference id for the item (a comment or submission) that this comment is a reply to",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission_id':{
            'desc': 'the id of the submission that comment is a response to',
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        },
    ('Reddit', 'discussion',): {
        'id': {
            'desc': 'unique Reddit Comment id (may not be unique across other sources/types)',
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'url': {
            'desc': "a url link to the original source of the data",
            'type': 'url',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'created_utc': {
            'desc': "The UTC time stamp of when the comment was created",
            'type': 'UTC-timestamp',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'title': {
            'desc': "the raw title of the discussion.",
            'type': 'string',
            'computation_fields_default': True,
            'label_fields_default': True,
            },
        'text': {
            'desc': "the raw text of the discussion.",
            'type': 'string',
            'computation_fields_default': True,
            'label_fields_default': False,
            },
        'submission.author': {
            'desc': "the account name of the poster",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.author_flair_css_class': {
            'desc': "the CSS class f the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.created_utc': {
            'desc': "The UTC time stamp of when the submission was created",
            'type': 'UTC-timestamp',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.id': {
            'desc': "the unique Reddit Submission id (may not be unique across other sources/types",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.num_comments': {
            'desc': "the number of comments made under this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.num_crossposts': {
            'desc': "the number of crossposts of this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.selftext': {
            'desc': "the raw text of the submission.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'submission.title': {
            'desc': "the raw title of the submission.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.author': {
            'desc': "the account name of the poster",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.author_flair_css_class': {
            'desc': "the CSS class of the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.body': {
            'desc': "the raw text of the comment.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.created_utc': {
            'desc': "The UTC time stamp of when the comment was created",
            'type': 'UTC-timestamp',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.id': {
            'desc': 'unique Reddit Comment id (may not be unique across other sources/types)',
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.link_id': {
            'desc': "A reference id that can link a comment to it's associated submission's id.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.parent_id': {
            'desc': "A reference id for the item (a comment or submission) that this comment is a reply to",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'comment.subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string',
            'computation_fields_default': False, 
            'label_fields_default': False,
            },
        },
    ('Twitter', 'tweet',): {
        'created_utc': { # not a field in tweet object; created using 'created_at'
            'desc': "The UTC time stamp of when the tweet was posted.",
            'type': 'UTC-timestamp',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'url': { # not a field in tweet object; created using tweet 'id'
            'desc': "a url link to the original tweet",
            'type': 'url',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'full_text': {
            'desc': "The full text of this tweet.",
            'type': "string",
            'computation_fields_default': True,
            'label_fields_default': True,
            },
        'text': {
            'desc': "The text in the tweet, truncated to 140 characters.",
            'type': "string",
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        },
    ('CSV', 'documents',): {
        'id': {
            'desc': "unique id of the row's data",
            'type': 'string',
            'computation_fields_default': False,
            'label_fields_default': True,
            },
        'url': {
            'desc': "a url link to the original source of the row's data",
            'type': 'url',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        'created_utc': {
            'desc': "The UTC time stamp of when the row's data was created",
            'type': 'UTC-timestamp',
            'computation_fields_default': False,
            'label_fields_default': False,
            },
        }
    }
