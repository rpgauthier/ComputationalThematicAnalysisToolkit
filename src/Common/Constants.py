'''Constants for MachineThematicAnalysis Toolkit'''
import wx
#import wx.lib.agw.flatnotebook as FNB
import External.wxPython.flatnotebook_fix as FNB
import wx.aui as aui


#Variables to configure GUI
FNB_STYLE = FNB.FNB_DEFAULT_STYLE|FNB.FNB_HIDE_ON_SINGLE_TAB|FNB.FNB_NO_X_BUTTON
NOTEBOOK_MOVEABLE = aui.AUI_NB_TOP | aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS
NOTEBOOK_SPLITABLE = aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | \
                    aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS
NOTEBOOK_FIXED = aui.AUI_NB_TOP | aui.AUI_NB_TAB_MOVE | \
                 aui.AUI_NB_SCROLL_BUTTONS

PHASE_LABEL_SIZE = 16
SUBMODULE_LABEL_SIZE = 15
LABEL_SIZE = 14
LABEL_FAMILY = wx.DEFAULT
LABEL_STYLE = wx.NORMAL
LABEL_WEIGHT = wx.NORMAL
LABEL_UNDERLINE = True

CURRENT_WORKSPACE = '../Current_Workspace'

#Menu Options
# removed to use built in id generator wx.ID_ANY

#Module Specific Variables
##Familiarization
##first n indexes need to align to TOKENIZER_APPROACH_LIST and must be 0 to n-1
TOKEN_TEXT_IDX = 0
TOKEN_NLTK_PORTERSTEM_IDX = 1
TOKEN_SPACY_LEMMA_IDX = 2
TOKEN_POS_IDX = 3
TOKEN_SPACY_STOPWORD_IDX = 4
TOKEN_TEXT_TFIDF_IDX = 5
TOKEN_STEM_TFIDF_IDX = 6
TOKEN_LEMMA_TFIDF_IDX = 7
TOKEN_ENTRIES = 'entries'
TOKEN_NUM_WORDS = 'num_of_words'
TOKEN_PER_WORDS = 'per_of_words'
TOKEN_NUM_DOCS = 'num_of_docs'
TOKEN_PER_DOCS = 'per_of_docs'
TOKEN_REMOVE_FLG = 'removed_flg'
TOKEN_TFIDF = 'tfidf'
FILTER_RULE_ANY = '<ANY>'
FILTER_RULE_REMOVE = 'remove'
FILTER_RULE_INCLUDE = 'include'
FILTER_RULE_REMOVE_SPACY_AUTO_STOPWORDS = 'remove spacy auto stopwords'
FILTER_TFIDF_REMOVE = 'remove tokens where their tfidf is '
FILTER_TFIDF_INCLUDE = 'include tokens where their tfidf is '
FILTER_TFIDF_LOWER = ' in the lower '
FILTER_TFIDF_UPPER = ' in the upper  '
###Token Filters
TOKENIZER_APPROACH_LISTS = {'eng-sm': ['raw text', 'nltk_PorterStemmer', 'spacy_lemmentizer'],
                            'eng-trf': ['raw text', 'nltk_PorterStemmer', 'spacy_lemmentizer'],
                            'fre-sm': ['raw text', '<no stemmer avaliable>', 'spacy_lemmentizer'],
                            'fre-trf': ['raw text', '<no stemmer avaliable>', 'spacy_lemmentizer'],
                            }
AVALIABLE_DATASET_LANGUAGES1 = ['eng-sm', 'eng-trf', 'fre-sm']
AVALIABLE_DATASET_LANGUAGES2 = ['English-Efficent', 'English-Accurate', 'French']

#definition of fields avaliable for use from the retrievers
avaliable_fields = {
    ('Reddit', 'submission',): {
        'author': {
            'desc': "the account name of the poster",
            'type': 'string',
            },
        'author_flair_css_class': {
            'desc': "the CSS class f the author's flair. subreddit specific",
            'type': 'string',
            },
        'author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string'
            },
        'created_utc': {
            'desc': "The UTC time stamp of when the submission was created",
            'type': 'UTC-timestamp'
            },
        'id': {
            'desc': "the unique Reddit Submission id (may not be unique across other sources/types",
            'type': 'string'
            },
        'num_comments': {
            'desc': "the number of comments made under this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'num_crossposts': {
            'desc': "the number of crossposts of this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'selftext': {
            'desc': "the raw text of the submission.",
            'type': 'string'
            },
        'score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string'
            },
        'subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string'
            },
        'title': {
            'desc': "the raw title of the submission.",
            'type': 'string'
            },
        },
    ('Reddit', 'comment',): {
        'author': {
            'desc': "the account name of the poster",
            'type': 'string'
            },
        'author_flair_css_class': {
            'desc': "the CSS class of the author's flair. subreddit specific",
            'type': 'string'
            },
        'author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string'
            },
        'body': {
            'desc': "the raw text of the comment.",
            'type': 'string'
            },
        'created_utc': {
            'desc': "The UTC time stamp of when the comment was created",
            'type': 'UTC-timestamp'
            },
        'id': {
            'desc': 'unique Reddit Comment id (may not be unique across other sources/types)',
            'type': 'string'
            },
        'link_id': {
            'desc': "A reference id that can link a comment to it's associated submission's id.",
            'type': 'string'
            },
        'parent_id': {
            'desc': "A reference id for the item (a comment or submission) that this comment is a reply to",
            'type': 'string'
            },
        'score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'submission_id':{
            'desc': 'the id of the submission that comment is a response to',
            'type': 'string'
            },
        'subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string'
            },
        'subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string'
            },
        },
    ('Reddit', 'discussion',): {
        'title': {
            'desc': "the raw title of the discussion.",
            'type': 'string'
            },
        'text': {
            'desc': "the raw text of the discussion.",
            'type': 'string'
            },
        'submission.author': {
            'desc': "the account name of the poster",
            'type': 'string',
            },
        'submission.author_flair_css_class': {
            'desc': "the CSS class f the author's flair. subreddit specific",
            'type': 'string',
            },
        'submission.author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string'
            },
        'submission.created_utc': {
            'desc': "The UTC time stamp of when the submission was created",
            'type': 'UTC-timestamp'
            },
        'submission.id': {
            'desc': "the unique Reddit Submission id (may not be unique across other sources/types",
            'type': 'string'
            },
        'submission.num_comments': {
            'desc': "the number of comments made under this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'submission.num_crossposts': {
            'desc': "the number of crossposts of this submission (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'submission.selftext': {
            'desc': "the raw text of the submission.",
            'type': 'string'
            },
        'submission.score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'submission.subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string'
            },
        'submission.subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string'
            },
        'submission.title': {
            'desc': "the raw title of the submission.",
            'type': 'string'
            },
        'comment.author': {
            'desc': "the account name of the poster",
            'type': 'string'
            },
        'comment.author_flair_css_class': {
            'desc': "the CSS class of the author's flair. subreddit specific",
            'type': 'string'
            },
        'comment.author_flair_text': {
            'desc': "the text of the author's flair. subreddit specific",
            'type': 'string'
            },
        'comment.body': {
            'desc': "the raw text of the comment.",
            'type': 'string'
            },
        'comment.created_utc': {
            'desc': "The UTC time stamp of when the comment was created",
            'type': 'UTC-timestamp'
            },
        'comment.id': {
            'desc': 'unique Reddit Comment id (may not be unique across other sources/types)',
            'type': 'string'
            },
        'comment.link_id': {
            'desc': "A reference id that can link a comment to it's associated submission's id.",
            'type': 'string'
            },
        'comment.parent_id': {
            'desc': "A reference id for the item (a comment or submission) that this comment is a reply to",
            'type': 'string'
            },
        'comment.score': {
            'desc': "the submission's score (may be out of date unless updated from Reddit API)",
            'type': 'integer'
            },
        'comment.subreddit': {
            'desc': "the subreddit the comment is from.",
            'type': 'string'
            },
        'comment.subreddit_id': {
            'desc': "The unique id of the subreddit the comment is from.",
            'type': 'string'
            },
        },
    }

#definition of default fields chosen for use from the retrievers
chosen_fields = {
    ('Reddit', 'submission',): {
        'selftext': {
            'desc': "the raw text of the submission.",
            'type': 'string'
            },
        'title': {
            'desc': "the raw title of the submission.",
            'type': 'string'
            },
        },
    ('Reddit', 'comment',): {
        'body': {
            'desc': "the raw text of the comment.",
            'type': 'string'
            },
        },
    ('Reddit', 'discussion',): {
        'title': {
            'desc': "the raw title of the discussion.",
            'type': 'string'
            },
        'text': {
            'desc': "the raw text of the discussion.",
            'type': 'string'
            },
        },
    }
