import logging
import csv
import os.path
import tweepy
import json

import wx
import wx.adv
import wx.grid
import wx.dataview as dv

from Common.GUIText import Collection as GUIText
import Common.CustomEvents as CustomEvents
import Collection.CollectionThreads as CollectionThreads

class AbstractRetrieverDialog(wx.Dialog):
    def OnRetrieveEnd(self, event):
        logger = logging.getLogger(__name__+".AbstractRetrieverDialog.OnRetrieveEnd")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if event.data['status_flag']:
            if 'dataset' in event.data:
                dataset_key = event.data['dataset_key']
                if dataset_key in main_frame.datasets:
                    main_frame.datasets[dataset_key].DestroyObject()
                main_frame.datasets[dataset_key] = event.data['dataset']
            elif 'datasets' in event.data:
                for dataset_key in event.data['datasets']:
                    i = 0
                    new_dataset_key = dataset_key
                    while new_dataset_key in main_frame.datasets:
                        i += 1
                        new_dataset_key = (dataset_key[0]+"_"+str(i), dataset_key[1], dataset_key[2])
                    main_frame.datasets[new_dataset_key] = event.data['datasets'][dataset_key]
            main_frame.DatasetsUpdated()
            #code to automatically change view to familiarization module
            main_frame.toggle_familiarization_menuitem.Check(True)
            main_frame.OnToggleFamiliarization(None)
            self.Destroy()
        else:
            wx.MessageBox(event.data['error_msg'],
                          GUIText.ERROR,
                          wx.OK | wx.ICON_ERROR)
            self.Thaw()
            self.Enable()
            self.SetFocus()
        self.retrieval_thread = None
        main_frame.CloseProgressDialog(thaw=True)
        logger.info("Finished")

    def OnProgress(self, event):
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(event.data)

class RedditDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".RedditRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_REDDIT_LABEL)
        self.retrieval_thread = None
        
        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multipledatasets_mode:
            name_label = wx.StaticText(self, label=GUIText.NAME + ": ")
            self.name_ctrl = wx.TextCtrl(self)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_sizer.Add(name_label)
            name_sizer.Add(self.name_ctrl)

        subreddit_label = wx.StaticText(self, label=GUIText.REDDIT_SUBREDDIT+": ")
        self.subreddit_ctrl = wx.TextCtrl(self)
        self.subreddit_ctrl.SetToolTip(GUIText.REDDIT_SUBREDDIT_TOOLTIP)
        subreddit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        subreddit_sizer.Add(subreddit_label)
        subreddit_sizer.Add(self.subreddit_ctrl)

        self.ethics_community1_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION+GUIText.ETHICS_COMMUNITY1)
        self.ethics_community2_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION+GUIText.ETHICS_COMMUNITY2)
        self.ethics_research_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION+GUIText.ETHICS_RESEARCH)
        self.ethics_institution_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION+GUIText.ETHICS_INSTITUTION)
        self.ethics_reddit_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION+GUIText.ETHICS_REDDIT)
        ethics_reddit_url = wx.adv.HyperlinkCtrl(self, label="1", url=GUIText.ETHICS_REDDIT_URL)
        ethics_redditapi_url = wx.adv.HyperlinkCtrl(self, label="2", url=GUIText.ETHICS_REDDITAPI_URL)
        self.ethics_pushshift_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION+GUIText.ETHICS_PUSHSHIFT)
        ethics_sizer = wx.BoxSizer(wx.VERTICAL)
        ethics_sizer.Add(self.ethics_community1_ctrl)
        ethics_sizer.Add(self.ethics_community2_ctrl)
        ethics_sizer.Add(self.ethics_research_ctrl)
        ethics_sizer.Add(self.ethics_institution_ctrl)
        ethics_reddit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ethics_reddit_sizer.Add(self.ethics_reddit_ctrl)
        ethics_reddit_sizer.Add(ethics_reddit_url)
        ethics_reddit_sizer.AddSpacer(5)
        ethics_reddit_sizer.Add(ethics_redditapi_url)
        ethics_sizer.Add(ethics_reddit_sizer)
        ethics_sizer.Add(self.ethics_pushshift_ctrl)

        #choose type of dataset to retrieve
        dataset_type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dataset_type_label = wx.StaticText(self, label=GUIText.TYPE+": ")
        self.dataset_type_choice = wx.Choice(self, choices=[GUIText.REDDIT_DISCUSSIONS, GUIText.REDDIT_SUBMISSIONS, GUIText.REDDIT_COMMENTS])
        dataset_type_sizer.Add(dataset_type_label)
        dataset_type_sizer.Add(self.dataset_type_choice)

        #control the subsource of where data is retrieved from
        self.archived_radioctrl = wx.RadioButton(self, label=GUIText.REDDIT_ARCHIVED, style=wx.RB_GROUP)
        self.archived_radioctrl.SetToolTip(GUIText.REDDIT_ARCHIVED_TOOLTIP)
        self.archived_radioctrl.SetValue(True)
        self.update_pushshift_radioctrl = wx.RadioButton(self, label=GUIText.REDDIT_UPDATE_PUSHSHIFT)
        self.update_pushshift_radioctrl.SetToolTip(GUIText.REDDIT_UPDATE_PUSHSHIFT_TOOLTIP)
        self.full_pushshift_radioctrl = wx.RadioButton(self, label=GUIText.REDDIT_FULL_PUSHSHIFT)
        self.full_pushshift_radioctrl.SetToolTip(GUIText.REDDIT_FULL_PUSHSHIFT_TOOLTIP)
        #TODO add ability to dynamically update from reddit information like Score
        #self.update_redditapi_radioctrl = wx.RadioButton(self, label=GUIText.REDDIT_API)
        #self.update_redditapi_radioctrl.SetToolTipString(GUIText.REDDIT_UPDATE_REDDITAPI_TOOLTIP)
        #self.full_redditapi_radioctrl = wx.RadioButton(self, label=GUIText.REDDIT_API)
        #self.full_redditapi_radioctrl.SetToolTipString(GUIText.REDDIT_FULL_REDDITAPI_TOOLTIP)
        source_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=GUIText.SOURCE+": ")
        source_sizer.Add(self.archived_radioctrl)
        source_sizer.Add(self.update_pushshift_radioctrl)
        source_sizer.Add(self.full_pushshift_radioctrl)
        #source_sizer.Add(self.update_redditapi_radioctrl)
        #source_sizer.Add(self.full_redditapi_radioctrl)

        start_date_label = wx.StaticText(self, label=GUIText.START_DATE+": ")
        self.start_date_ctrl = wx.adv.DatePickerCtrl(self, name="startDate",
                                                style=wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY)
        self.start_date_ctrl.SetToolTip(GUIText.START_DATE_TOOLTIP)
        end_date_label = wx.StaticText(self, label=GUIText.END_DATE+": ")
        self.end_date_ctrl = wx.adv.DatePickerCtrl(self, name="endDate",
                                              style=wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY)
        self.end_date_ctrl.SetToolTip(GUIText.END_DATE_TOOLTIP)
        date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        date_sizer.Add(start_date_label)
        date_sizer.Add(self.start_date_ctrl)
        date_sizer.AddSpacer(10)
        date_sizer.Add(end_date_label)
        date_sizer.Add(self.end_date_ctrl)

        

        #Retriever button to collect the requested data
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label=GUIText.OK)
        button_sizer.Add(ok_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label=GUIText.CANCEL)
        button_sizer.Add(cancel_button)

        retriever_sizer = wx.BoxSizer(wx.VERTICAL)
        if main_frame.multipledatasets_mode:
            retriever_sizer.Add(name_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(subreddit_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(ethics_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(dataset_type_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(source_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(date_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(retriever_sizer)
        self.Layout()
        self.Fit()

        ok_button.Bind(wx.EVT_BUTTON, self.OnRetrieveStart)
        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
        CustomEvents.RETRIEVE_EVT_RESULT(self, self.OnRetrieveEnd)

        logger.info("Finished")

    def OnRetrieveStart(self, event):
        logger = logging.getLogger(__name__+".RedditRetrieverDialog.OnRetrieveStart")
        logger.info("Starting")

        status_flag = True
        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multipledatasets_mode:
            name = self.name_ctrl.GetValue()
            if name == "":
                wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                            GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('No name entered')
                status_flag = False
        else:
            name = self.subreddit_ctrl.GetValue() 
        subreddit = self.subreddit_ctrl.GetValue()
        if subreddit == "":
            wx.MessageBox(GUIText.REDDIT_SUBREDDIT_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No subreddit entered')
            status_flag = False
        if not self.ethics_community1_ctrl.IsChecked():
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR+GUIText.ETHICS_COMMUNITY1,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('Ethics not checked')
            status_flag = False
        if not self.ethics_community2_ctrl.IsChecked():
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR+GUIText.ETHICS_COMMUNITY2,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('Ethics not checked')
            status_flag = False
        if not self.ethics_research_ctrl.IsChecked():
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR+GUIText.ETHICS_RESEARCH,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('Ethics not checked')
            status_flag = False
        if not self.ethics_institution_ctrl.IsChecked():
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR+GUIText.ETHICS_INSTITUTION,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('Ethics not checked')
            status_flag = False
        if not self.ethics_reddit_ctrl.IsChecked():
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR+GUIText.ETHICS_REDDIT,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('Ethics not checked')
            status_flag = False
        if not self.ethics_pushshift_ctrl.IsChecked():
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR+GUIText.ETHICS_PUSHSHIFT,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('Ethics not checked')
            status_flag = False
        
        start_date = str(self.start_date_ctrl.GetValue().Format("%Y-%m-%d"))
        end_date = str(self.end_date_ctrl.GetValue().Format("%Y-%m-%d"))
        if start_date > end_date:
            wx.MessageBox(GUIText.DATE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning("Start Date[%s] not before End Date[%s]",
                           str(start_date), str(end_date))
            status_flag = False
        
        #determine what type of retrieval is to be performed
        replace_archive_flg = self.full_pushshift_radioctrl.GetValue() #or  self.full_redditapi_radioctrl.GetValue()
        pushshift_flg = self.full_pushshift_radioctrl.GetValue() or self.update_pushshift_radioctrl.GetValue()
        redditapi_flg = False
        #redditapi_flg = self.update_redditapi_radioctrl.GetValue() or self.full_redditapi_radioctrl.GetValue()

        dataset_type_id = self.dataset_type_choice.GetSelection()
        dataset_type = ""
        if dataset_type_id is wx.NOT_FOUND:
            wx.MessageBox(GUIText.TYPE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning("No Data type was selected for retrieval")
            status_flag = False
        else:
            dataset_type = self.dataset_type_choice.GetString(dataset_type_id)
        if dataset_type == GUIText.REDDIT_DISCUSSIONS:
            dataset_type = 'discussion'
        elif dataset_type == GUIText.REDDIT_SUBMISSIONS:
            dataset_type = 'submission'
        elif dataset_type == GUIText.REDDIT_COMMENTS:
            dataset_type = 'comment'

        dataset_source = "Reddit"

        dataset_key = (name, dataset_source, dataset_type)
        if dataset_key in main_frame.datasets:
            wx.MessageBox(GUIText.NAME_EXISTS_ERROR,
                          GUIText.ERROR,
                          wx.OK | wx.ICON_ERROR)
            logger.warning("Data with same name[%s] already exists", name)
            status_flag = False

        if status_flag:
            main_frame.CreateProgressDialog(title=GUIText.RETRIEVING_LABEL+name,
                                            warning=GUIText.SIZE_WARNING_MSG,
                                            freeze=True)
            self.Disable()
            self.Freeze()
            main_frame.PulseProgressDialog(GUIText.RETRIEVING_BEGINNING_MSG)
            self.retrieval_thread = CollectionThreads.RetrieveRedditDatasetThread(self, main_frame, name, subreddit, start_date, end_date, replace_archive_flg, pushshift_flg, redditapi_flg, dataset_type)
        logger.info("Finished")

class TwitterDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".TwitterRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_TWITTER_LABEL)
        self.retrieval_thread = None
        self.keys_filename = "../keys.json"
        self.keys = {}
        # get saved keys, if any
        if os.path.isfile(self.keys_filename):
            with open(self.keys_filename, mode='r') as infile:
                self.keys = json.load(infile)

        name_label = wx.StaticText(self, label=GUIText.NAME+": ")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label)
        name_sizer.Add(self.name_ctrl, wx.EXPAND)

        consumer_key_label = wx.StaticText(self, label=GUIText.CONSUMER_KEY + ": ")
        self.consumer_key_ctrl = wx.TextCtrl(self)
        if 'consumer_key' in self.keys:
            self.consumer_key_ctrl.SetValue(self.keys['consumer_key'])
        self.consumer_key_ctrl.SetToolTip(GUIText.CONSUMER_KEY_TOOLTIP)
        consumer_key_sizer = wx.BoxSizer(wx.HORIZONTAL)
        consumer_key_sizer.Add(consumer_key_label)
        consumer_key_sizer.Add(self.consumer_key_ctrl, wx.EXPAND)
    
        consumer_secret_label = wx.StaticText(self, label=GUIText.CONSUMER_SECRET + ": ")
        self.consumer_secret_ctrl = wx.TextCtrl(self)
        if 'consumer_secret' in self.keys:
            self.consumer_secret_ctrl.SetValue(self.keys['consumer_secret'])
        self.consumer_secret_ctrl.SetToolTip(GUIText.CONSUMER_SECRET_TOOLTIP)
        consumer_secret_sizer = wx.BoxSizer(wx.HORIZONTAL)
        consumer_secret_sizer.Add(consumer_secret_label)
        consumer_secret_sizer.Add(self.consumer_secret_ctrl, wx.EXPAND)

        # search by query
        self.query_radioctrl = wx.RadioButton(self, label=GUIText.TWITTER_QUERY+": ", style=wx.RB_GROUP)
        self.query_radioctrl.SetToolTip(GUIText.TWITTER_QUERY_RADIOBUTTON_TOOLTIP)
        self.query_radioctrl.SetValue(True)

        self.query_hyperlink_ctrl = wx.adv.HyperlinkCtrl(self, label="[⬈]", url=GUIText.TWITTER_QUERY_HYPERLINK)
        self.query_hyperlink_ctrl.SetNormalColour(wx.Colour(255, 255, 255))
        self.query_hyperlink_ctrl.SetHoverColour(wx.Colour(127, 127, 127))
        self.query_hyperlink_ctrl.SetVisitedColour(wx.Colour(255, 255, 255))

        self.query_ctrl = wx.TextCtrl(self)
        self.query_ctrl.SetHint(GUIText.TWITTER_QUERY_PLACEHOLDER)
        self.query_ctrl.SetToolTip(GUIText.TWITTER_QUERY_TOOLTIP)

        query_sizer = wx.BoxSizer(wx.HORIZONTAL)
        query_sizer.Add(self.query_radioctrl)
        query_sizer.Add(self.query_hyperlink_ctrl)
        query_sizer.AddSpacer(10)
        query_sizer.Add(self.query_ctrl, wx.EXPAND)

        # search by tweet attributes
        self.attributes_radioctrl = wx.RadioButton(self, label=GUIText.TWITTER_TWEET_ATTRIBUTES+": ")
        self.attributes_radioctrl.SetToolTip(GUIText.TWITTER_TWEET_ATTRIBUTES_RADIOBUTTON_TOOLTIP)

        self.keywords_checkbox_ctrl = wx.CheckBox(self, label=GUIText.KEYWORDS+": ")
        self.keywords_ctrl = wx.TextCtrl(self)
        self.keywords_ctrl.SetHint(GUIText.TWITTER_KEYWORDS_PLACEHOLDER)
        keywords_sizer = wx.BoxSizer(wx.HORIZONTAL)
        keywords_sizer.AddSpacer(20)
        keywords_sizer.Add(self.keywords_checkbox_ctrl)
        keywords_sizer.Add(self.keywords_ctrl, wx.EXPAND)

        self.hashtags_checkbox_ctrl = wx.CheckBox(self, label=GUIText.HASHTAGS+": ")
        self.hashtags_ctrl = wx.TextCtrl(self)
        self.hashtags_ctrl.SetHint(GUIText.TWITTER_HASHTAGS_PLACEHOLDER)
        hashtags_sizer = wx.BoxSizer(wx.HORIZONTAL)
        hashtags_sizer.AddSpacer(20)
        hashtags_sizer.Add(self.hashtags_checkbox_ctrl)
        hashtags_sizer.Add(self.hashtags_ctrl, wx.EXPAND)

        self.account_checkbox_ctrl = wx.CheckBox(self, label=GUIText.TWITTER_LABEL+" "+GUIText.ACCOUNT+": ")
        self.account_ctrl = wx.TextCtrl(self)
        self.account_ctrl.SetHint(GUIText.TWITTER_ACCOUNT_PLACEHOLDER)
        account_sizer = wx.BoxSizer(wx.HORIZONTAL)
        account_sizer.AddSpacer(20)
        account_sizer.Add(self.account_checkbox_ctrl)
        account_sizer.Add(self.account_ctrl, wx.EXPAND)

        attributes_options_sizer = wx.BoxSizer(wx.VERTICAL)
        attributes_options_sizer.Add(keywords_sizer, 0, wx.EXPAND)
        attributes_options_sizer.Add(hashtags_sizer, 0, wx.EXPAND)
        attributes_options_sizer.Add(account_sizer, 0, wx.EXPAND)
        
        attributes_sizer = wx.BoxSizer(wx.VERTICAL)
        attributes_sizer.Add(self.attributes_radioctrl)
        attributes_sizer.Add(attributes_options_sizer, 0, wx.EXPAND)

        # add elements to 'search by' box
        search_by_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=GUIText.SEARCH_BY+": ")
        search_by_sizer.Add(query_sizer, 0, wx.EXPAND)
        search_by_sizer.Add(attributes_sizer, 0, wx.EXPAND)

        start_date_label = wx.StaticText(self, label=GUIText.START_DATE+": ")
        self.start_date_ctrl = wx.adv.DatePickerCtrl(self, name="startDate",
                                                style=wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY)
        self.start_date_ctrl.SetToolTip(GUIText.START_DATE_TOOLTIP)
        start_date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        start_date_sizer.Add(start_date_label)
        start_date_sizer.Add(self.start_date_ctrl)

        end_date_label = wx.StaticText(self, label=GUIText.END_DATE+": ")
        self.end_date_ctrl = wx.adv.DatePickerCtrl(self, name="endDate",
                                              style=wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY)
        self.end_date_ctrl.SetToolTip(GUIText.END_DATE_TOOLTIP)
        end_date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        end_date_sizer.Add(end_date_label)
        end_date_sizer.Add(self.end_date_ctrl)

        #Retriever button to collect the requested data
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label=GUIText.OK)
        button_sizer.Add(ok_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label=GUIText.CANCEL)
        button_sizer.Add(cancel_button)

        retriever_sizer = wx.BoxSizer(wx.VERTICAL)
        retriever_sizer.SetMinSize(350, -1)
        retriever_sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)
        retriever_sizer.Add(consumer_key_sizer, 0, wx.EXPAND | wx.ALL, 5)
        retriever_sizer.Add(consumer_secret_sizer, 0, wx.EXPAND | wx.ALL, 5)
        retriever_sizer.Add(search_by_sizer, 0, wx.EXPAND | wx.ALL, 5)
        retriever_sizer.Add(start_date_sizer, 0, wx.EXPAND | wx.ALL, 5)
        retriever_sizer.Add(end_date_sizer, 0, wx.EXPAND | wx.ALL, 5)
        retriever_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(retriever_sizer)
        self.Layout()
        self.Fit()

        ok_button.Bind(wx.EVT_BUTTON, self.OnRetrieveStart)
        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
        CustomEvents.RETRIEVE_EVT_RESULT(self, self.OnRetrieveEnd)

        logger.info("Finished")

    def OnRetrieveStart(self, event):
        logger = logging.getLogger(__name__+".TwitterRetrieverDialog.OnRetrieveStart")
        logger.info("Starting")

        status_flag = True
        main_frame = wx.GetApp().GetTopWindow()
        keys = {}
        
        name = self.name_ctrl.GetValue()
        if name == "":
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No name entered')
            status_flag = False
        keys['consumer_key'] = self.consumer_key_ctrl.GetValue()
        if keys['consumer_key'] == "":
            wx.MessageBox(GUIText.CONSUMER_KEY_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No consumer key entered')
            status_flag = False
        keys['consumer_secret'] = self.consumer_secret_ctrl.GetValue()
        if keys['consumer_secret'] == "":
            wx.MessageBox(GUIText.CONSUMER_SECRET_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No consumer secret entered')
            status_flag = False

        auth = tweepy.OAuthHandler(keys['consumer_key'], keys['consumer_secret'])
        api = tweepy.API(auth)
        valid_credentials = False
        try:
            valid_credentials = api.verify_credentials() # throws an error if user credentials are insufficient
            if not valid_credentials:
                wx.MessageBox(GUIText.INVALID_CREDENTIALS_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('Invalid credentials')
                status_flag = False 
        except tweepy.error.TweepError as e:
            if e.api_code == 220:
                # TODO: once user auth is implemented, verify user credentials are sufficient (input for valid user credentials still need to be added)
                pass
                # wx.MessageBox(GUIText.INSUFFICIENT_CREDENTIALS_ERROR,
                #             GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                # logger.warning('User credentials do not allow access to this resource.')
                # status_flag = False         

        query = self.query_ctrl.GetValue()
        if query == "":
            wx.MessageBox(GUIText.TWITTER_QUERY_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No query entered')
            status_flag = False
        start_date = str(self.start_date_ctrl.GetValue().Format("%Y-%m-%d"))
        end_date = str(self.end_date_ctrl.GetValue().Format("%Y-%m-%d"))
        if start_date > end_date:
            wx.MessageBox(GUIText.DATE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning("Start Date[%s] not before End Date[%s]",
                           str(start_date), str(end_date))
            status_flag = False

        dataset_source = "Twitter"
        # TODO: is document type ok for tweets?
        dataset_type = "document"

        dataset_key = (name, dataset_source, dataset_type)
        if dataset_key in main_frame.datasets:
            wx.MessageBox(GUIText.NAME_EXISTS_ERROR,
                          GUIText.ERROR,
                          wx.OK | wx.ICON_ERROR)
            logger.warning("Data with same name[%s] already exists", name)
            status_flag = False

        if status_flag:
            # save keys
            with open(self.keys_filename, mode='w') as outfile:
                json.dump(keys, outfile)

            main_frame.CreateProgressDialog(title=GUIText.RETRIEVING_LABEL+name,
                                            warning=GUIText.SIZE_WARNING_MSG,
                                            freeze=True)
            self.Disable()
            self.Freeze()
            main_frame.PulseProgressDialog(GUIText.RETRIEVING_BEGINNING_MSG)
            self.retrieval_thread = CollectionThreads.RetrieveTwitterDatasetThread(self, main_frame, name, keys, query, start_date, end_date, dataset_type)
        logger.info("Finished")

class CSVDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".CSVRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_CSV_LABEL)
        self.retrieval_thread = None
        self.avaliable_fields = {}

        name_label = wx.StaticText(self, label=GUIText.NAME + ": ")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label)
        name_sizer.Add(self.name_ctrl)

        filename_label = wx.StaticText(self, label=GUIText.FILENAME + ": ")
        self.filename_ctrl = wx.FilePickerCtrl(self, wildcard="CSV files (*.csv)|*.csv")
        self.filename_ctrl.SetInitialDirectory('../Data/CSV')
        filename_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filename_sizer.Add(filename_label)
        filename_sizer.Add(self.filename_ctrl)
        self.filename_ctrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnFilenameChosen)

        dataset_field_label = wx.StaticText(self, label=GUIText.CSV_DATASETFIELD+": ")
        self.dataset_field_ctrl = wx.Choice(self, choices=[])
        self.dataset_field_ctrl.SetToolTip(GUIText.CSV_DATASETFIELD_TOOLTIP)
        dataset_field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dataset_field_sizer.Add(dataset_field_label)
        dataset_field_sizer.Add(self.dataset_field_ctrl)
        
        id_field_label = wx.StaticText(self, label=GUIText.CSV_IDFIELD+": ")
        self.id_field_ctrl = wx.Choice(self, choices=[GUIText.CSV_IDFIELD_DEFAULT])
        self.id_field_ctrl.SetToolTip(GUIText.CSV_IDFIELD_TOOLTIP)
        id_field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        id_field_sizer.Add(id_field_label)
        id_field_sizer.Add(self.id_field_ctrl)

        included_fields_label = wx.StaticText(self, label=GUIText.CSV_INCLUDEDFIELDS+": ")
        self.included_fields_ctrl = wx.ListBox(self, style=wx.LB_MULTIPLE)
        self.included_fields_ctrl.SetToolTip(GUIText.CSV_INCLUDEDFIELDS_TOOLTIP)
        included_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        included_fields_sizer.Add(included_fields_label)
        included_fields_sizer.Add(self.included_fields_ctrl)

        #Retriever button to collect the requested data
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label=GUIText.OK)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label=GUIText.CANCEL)
        button_sizer.Add(ok_button)
        button_sizer.Add(cancel_button)

        retriever_sizer = wx.BoxSizer(wx.VERTICAL)
        retriever_sizer.Add(name_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(filename_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(dataset_field_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(id_field_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(included_fields_sizer, 0, wx.ALL, 5)
        retriever_sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(retriever_sizer)
        self.Layout()
        self.Fit()

        ok_button.Bind(wx.EVT_BUTTON, self.OnRetrieveStart)
        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
        CustomEvents.RETRIEVE_EVT_RESULT(self, self.OnRetrieveEnd)

        logger.info("Finished")
    
    def OnFilenameChosen(self, event):
        logger = logging.getLogger(__name__+".CSVRetrieverDialog.OnFilenameChosen")
        logger.info("Starting")
        filename = self.filename_ctrl.GetPath()

        if os.path.isfile(filename):
            with open(filename, mode='r') as infile:
                reader = csv.reader(infile)
                header_row = next(reader)
                self.dataset_field_ctrl.Clear()
                self.id_field_ctrl.Clear()
                self.included_fields_ctrl.Clear()
                self.avaliable_fields.clear()
                self.dataset_field_ctrl.Append("")
                self.id_field_ctrl.Append(GUIText.CSV_IDFIELD_DEFAULT)
                for column_name in header_row:
                    self.dataset_field_ctrl.Append(column_name)
                    self.id_field_ctrl.Append(column_name)
                    self.included_fields_ctrl.Append("csv."+column_name)
                    self.avaliable_fields["csv."+column_name] = {"desc":"CSV Field", "type":"string"}
                self.Layout()
                self.Fit()
        logger.info("Finished")

    def OnRetrieveStart(self, event):
        logger = logging.getLogger(__name__+".CSVRetrieverDialog.OnRetrieveStart")
        logger.info("Starting")

        status_flag = True
        main_frame = wx.GetApp().GetTopWindow()
        
        name = self.name_ctrl.GetValue()
        if name == "":
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No name entered')
            status_flag = False

        filename = self.filename_ctrl.GetPath()
        if filename == "":
            wx.MessageBox(GUIText.FILENAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No filename entered')
            status_flag = False
        
        dataset_field = self.dataset_field_ctrl.GetStringSelection()

        id_field = self.id_field_ctrl.GetStringSelection()
        if id_field == "":
            wx.MessageBox(GUIText.CSV_IDFIELD_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No id field chosen')
            status_flag = False
        
        included_fields = {}
        for index in self.included_fields_ctrl.GetSelections():
            field_name = self.included_fields_ctrl.GetString(index)
            included_fields[field_name] = self.avaliable_fields[field_name]
        
        
        dataset_source = "CSV"
        dataset_field = self.dataset_field_ctrl.GetStringSelection()
        dataset_type = ""
        if dataset_field == "":
            dataset_type = "document"
            
            dataset_key = (name, dataset_source, dataset_type)
            if dataset_key in main_frame.datasets:
                wx.MessageBox(GUIText.NAME_EXISTS_ERROR,
                            GUIText.ERROR,
                            wx.OK | wx.ICON_ERROR)
                logger.warning("Data with same name[%s] already exists", name)
                status_flag = False

        if status_flag:
            main_frame.CreateProgressDialog(title=GUIText.RETRIEVING_LABEL+name,
                                            warning=GUIText.SIZE_WARNING_MSG,
                                            freeze=True)
            self.Disable()
            self.Freeze()
            main_frame.PulseProgressDialog(GUIText.RETRIEVING_BEGINNING_MSG)
            self.retrieval_thread = CollectionThreads.RetrieveCSVDatasetThread(self, main_frame, name, dataset_field, dataset_type, id_field, self.avaliable_fields, included_fields, filename)
        logger.info("Finished")

class GroupingFieldDialog(wx.Dialog):
    '''dialog for choosing field to group on'''
    def __init__(self, parent, node):
        logger = logging.getLogger(__name__+".GroupingFieldDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.GROUP_REQUEST+str(node.key))

        class FieldTreeListCtrl(dv.TreeListCtrl):
            '''Lists of Fields'''
            def __init__(self, parent):
                logger = logging.getLogger(__name__+".GroupingFieldDialog.FieldTreeListCtrl.__init__")
                logger.info("Starting")
                dv.TreeListCtrl.__init__(self, parent, style=dv.TL_MULTIPLE)
                self.AppendColumn('Source', align=wx.ALIGN_LEFT, flags=wx.COL_SORTABLE|wx.COL_RESIZABLE)
                self.AppendColumn('Type', align=wx.ALIGN_LEFT, flags=wx.COL_SORTABLE|wx.COL_RESIZABLE)
                self.AppendColumn('Field', align=wx.ALIGN_LEFT, flags=wx.COL_SORTABLE|wx.COL_RESIZABLE)
                self.AppendColumn('Example', align=wx.ALIGN_LEFT, flags=wx.COL_SORTABLE|wx.COL_RESIZABLE)
                logger.info("Finished")

        self.node = node

        self.fields_listctrl = FieldTreeListCtrl(self)
        self.fields_listctrl.SetWindowStyle(dv.TL_SINGLE)

        for field_name in self.node.avaliable_fields:
            field = self.node.avaliable_fields[field_name]
            item = self.fields_listctrl.AppendItem(self.fields_listctrl.GetRootItem(), str(self.node.dataset_source))
            self.fields_listctrl.SetItemText(item, 1, str(self.node.dataset_type))
            self.fields_listctrl.SetItemText(item, 2, str(field.key))
            self.fields_listctrl.SetItemText(item, 3, str(field.desc))

        ok_btn = wx.Button(self, wx.ID_OK, label=GUIText.OK)
        skip_btn = wx.Button(self, wx.ID_CANCEL, label=GUIText.SKIP)

        hz_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hz_sizer1.Add(self.fields_listctrl, 1, wx.EXPAND)

        hz_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hz_sizer2.Add(ok_btn)
        hz_sizer2.Add(skip_btn)

        vt_sizer = wx.BoxSizer(wx.VERTICAL)
        vt_sizer.Add(hz_sizer1, 1, wx.ALL|wx.EXPAND)
        vt_sizer.Add(hz_sizer2)
        self.SetSizer(vt_sizer)

        ok_btn.Bind(wx.EVT_BUTTON, self.OnOk)
        
        self.Layout()
        self.Fit()
        logger.info("Finished")

    def OnOk(self, event):
        logger = logging.getLogger(__name__+".GroupingFieldDialog.OnOk")
        logger.info("Starting")
        item = self.fields_listctrl.GetSelection()
        if item.IsOk():
            field_selected = self.fields_listctrl.GetItemText(item, 2)
            for field_name in self.node.avaliable_fields:
                if field_name == field_selected:
                    self.node.grouping_field = self.node.avaliable_fields[field_name]
                    break
            logger.info("Finished")
            self.EndModal(wx.ID_OK)
        else:
            #display error message
            wx.MessageBox(GUIText.GROUP_REQUEST_ERROR,
                          GUIText.ERROR,
                          wx.OK | wx.ICON_ERROR)
            logger.warning('User did not select a field to group with')
            logger.info("Finished")