import logging
import csv
import os.path
import tweepy
import json
from numpy import source
import pytz

import wx
import wx.adv
from wx.core import DropTarget
import wx.grid
import wx.dataview as dv

import Common.Constants as Constants
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

    # given a sizer, disables all child elements
    def DisableSizer(self, parent_sizer):
        for child_sizer in parent_sizer.GetChildren():
            elem = child_sizer.GetWindow()
            if not elem:
                try:
                    # elem is a sizer
                    sizer = child_sizer.GetSizer()
                    self.DisableSizer(sizer)
                except:
                    # elem is something else, not a widget
                    pass
            else:
                # elem is a widget
                # disable all widgets
                if isinstance(elem, wx.adv.HyperlinkCtrl):
                    elem.SetNormalColour(wx.Colour(127, 127, 127))
                elem.Disable()

    # given a sizer, enables all child elements
    def EnableSizer(self, parent_sizer):
        for child_sizer in parent_sizer.GetChildren():
            elem = child_sizer.GetWindow()
            if not elem:
                try:
                    # elem is a sizer
                    sizer = child_sizer.GetSizer()
                    self.EnableSizer(sizer)
                except:
                    # elem is something else, not a widget
                    pass
            else:
                # elem is a widget
                # enable all widgets
                if isinstance(elem, wx.adv.HyperlinkCtrl):
                    elem.SetNormalColour(wx.Colour(wx.BLUE))
                elem.Enable()
    
    # given an options_list_sizer, where each immediate child is an option sizer,
    # and each option sizer contains a radio button and a corresponding sizer,
    # returns an array of tuples (radio button + corresponding sizer)
    def GetOptionsInRadioGroup(self, options_list_sizer):
        options = []
        for option in options_list_sizer.GetChildren(): 
            tuple = []
            option_sizer = option.GetSizer() # should have 2 elements: a radiobutton and its corresponding sizer
            tuple.append(option_sizer.GetChildren()[0].GetWindow())
            tuple.append(option_sizer.GetChildren()[1].GetSizer())
            options.append(tuple)
        return options

    # given a sizer containing a list of option sizers
    # enables option corresponding to selected radiobutton,
    # and disables the rest of the options            
    def EnableOnlySelected(self, options_list_sizer):
        options = self.GetOptionsInRadioGroup(options_list_sizer)
        for option in options:
            if option[0].GetValue():
                self.EnableSizer(option[1])
            else:
                self.DisableSizer(option[1])

class RedditDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".RedditRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_REDDIT_LABEL, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.retrieval_thread = None
        self.avaliable_fields = {}

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multipledatasets_mode:
            name_label = wx.StaticText(self, label=GUIText.NAME + ": ")
            self.name_ctrl = wx.TextCtrl(self)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_sizer.Add(name_label)
            name_sizer.Add(self.name_ctrl)
            sizer.Add(name_sizer, 0, wx.ALL, 5)

        subreddit_label = wx.StaticText(self, label=GUIText.REDDIT_SUBREDDIT+": ")
        self.subreddit_ctrl = wx.TextCtrl(self)
        self.subreddit_ctrl.SetToolTip(GUIText.REDDIT_SUBREDDIT_TOOLTIP)
        subreddit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        subreddit_sizer.Add(subreddit_label)
        subreddit_sizer.Add(self.subreddit_ctrl)
        sizer.Add(subreddit_sizer, 0, wx.ALL, 5)

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
        sizer.Add(ethics_sizer, 0, wx.ALL, 5)

        #choose type of dataset to retrieve
        dataset_type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dataset_type_label = wx.StaticText(self, label=GUIText.TYPE+": ")
        self.dataset_type_choice = wx.Choice(self, choices=[GUIText.REDDIT_DISCUSSIONS, GUIText.REDDIT_SUBMISSIONS, GUIText.REDDIT_COMMENTS])
        self.dataset_type_choice.Bind(wx.EVT_CHOICE, self.OnDatasetTypeChosen)
        dataset_type_sizer.Add(dataset_type_label)
        dataset_type_sizer.Add(self.dataset_type_choice)
        sizer.Add(dataset_type_sizer, 0, wx.ALL, 5)

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
        sizer.Add(source_sizer, 0, wx.ALL, 5)

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
        sizer.Add(date_sizer, 0, wx.ALL, 5)

        metadata_fields_label = wx.StaticText(self, label=GUIText.METADATAFIELDS)
        self.metadata_fields_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.metadata_fields_ctrl.AppendColumn(GUIText.FIELD)
        self.metadata_fields_ctrl.AppendColumn(GUIText.DESCRIPTION)
        self.metadata_fields_ctrl.AppendColumn(GUIText.TYPE)
        self.metadata_fields_ctrl.SetToolTip(GUIText.METADATAFIELDS_TOOLTIP)
        self.metadata_fields_ctrl.EnableCheckBoxes()
        metadata_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        metadata_fields_sizer.Add(metadata_fields_label, 0, wx.ALL)
        metadata_fields_sizer.Add(self.metadata_fields_ctrl, 1, wx.EXPAND)
        if main_frame.adjustable_metadata_mode:
            sizer.Add(metadata_fields_sizer, 0, wx.ALL|wx.EXPAND, 5)
        else:
            metadata_fields_sizer.ShowItems(False)

        included_fields_label = wx.StaticText(self, label=GUIText.INCLUDEDFIELDS)
        self.included_fields_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.included_fields_ctrl.AppendColumn(GUIText.FIELD)
        self.included_fields_ctrl.AppendColumn(GUIText.DESCRIPTION)
        self.included_fields_ctrl.AppendColumn(GUIText.TYPE)
        self.included_fields_ctrl.SetToolTip(GUIText.INCLUDEDFIELDS_TOOLTIP)
        self.included_fields_ctrl.EnableCheckBoxes()
        included_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        included_fields_sizer.Add(included_fields_label, 0, wx.ALL)
        included_fields_sizer.Add(self.included_fields_ctrl, 1, wx.EXPAND)
        if main_frame.adjustable_includedfields_mode:
            sizer.Add(included_fields_sizer, 0, wx.ALL|wx.EXPAND, 5)
        else:
            included_fields_sizer.ShowItems(False)

        #Retriever button to collect the requested data
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label=GUIText.OK)
        button_sizer.Add(ok_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label=GUIText.CANCEL)
        button_sizer.Add(cancel_button)
        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

        #fix since some operatign systems default to first element of the list instead of blank like windows
        if self.dataset_type_choice.GetStringSelection() != '':
            self.OnDatasetTypeChosen(None)

        ok_button.Bind(wx.EVT_BUTTON, self.OnRetrieveStart)
        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
        CustomEvents.RETRIEVE_EVT_RESULT(self, self.OnRetrieveEnd)

        logger.info("Finished")

    def OnDatasetTypeChosen(self, event):
        logger = logging.getLogger(__name__+".RedditRetrieverDialog.OnDatasetTypeChosen")
        logger.info("Starting")
        dataset_type = self.dataset_type_choice.GetStringSelection()
        if dataset_type == GUIText.REDDIT_DISCUSSIONS:
            dataset_type = 'discussion'
        elif dataset_type == GUIText.REDDIT_SUBMISSIONS:
            dataset_type = 'submission'
        elif dataset_type == GUIText.REDDIT_COMMENTS:
            dataset_type = 'comment'

        self.avaliable_fields = Constants.avaliable_fields[('Reddit', dataset_type,)]

        self.metadata_fields_ctrl.DeleteAllItems()
        self.included_fields_ctrl.DeleteAllItems()
        idx = 0
        for key in self.avaliable_fields:
            self.metadata_fields_ctrl.Append([key, self.avaliable_fields[key]['desc'], self.avaliable_fields[key]['type']])
            if self.avaliable_fields[key]['metadata_default']:
                self.metadata_fields_ctrl.CheckItem(idx)
            self.included_fields_ctrl.Append([key, self.avaliable_fields[key]['desc'], self.avaliable_fields[key]['type']])
            if self.avaliable_fields[key]['included_default']:
                self.included_fields_ctrl.CheckItem(idx)
            idx = idx+1

        self.Layout()
        self.Fit()
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
        
        metadata_fields_list = []
        item = self.metadata_fields_ctrl.GetNextItem(-1)
        while item != -1:
            if self.metadata_fields_ctrl.IsItemChecked(item):
                field_name = self.metadata_fields_ctrl.GetItemText(item, 0)
                metadata_fields_list.append((field_name, self.avaliable_fields[field_name],))
            item = self.metadata_fields_ctrl.GetNextItem(item)
        
        included_fields_list = []
        item = self.included_fields_ctrl.GetNextItem(-1)
        while item != -1:
            if self.included_fields_ctrl.IsItemChecked(item):
                field_name = self.included_fields_ctrl.GetItemText(item, 0)
                included_fields_list.append((field_name, self.avaliable_fields[field_name],))
            item = self.included_fields_ctrl.GetNextItem(item)

        if status_flag:
            main_frame.CreateProgressDialog(title=GUIText.RETRIEVING_LABEL+name,
                                            warning=GUIText.SIZE_WARNING_MSG,
                                            freeze=True)
            self.Disable()
            self.Freeze()
            main_frame.PulseProgressDialog(GUIText.RETRIEVING_BEGINNING_MSG)
            self.retrieval_thread = CollectionThreads.RetrieveRedditDatasetThread(self, main_frame, name, subreddit, start_date, end_date,
                                                                                  replace_archive_flg, pushshift_flg, redditapi_flg, dataset_type,
                                                                                  list(self.avaliable_fields.items()), metadata_fields_list, included_fields_list)
        logger.info("Finished")

class TwitterDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".TwitterRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_TWITTER_LABEL)
        self.retrieval_thread = None
        self.keys_filename = "../keys.json"
        self.keys = {}
        self.avaliable_fields = {}
        self.dataset_type = "tweet"

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.SetMinSize(350, -1)
        
        main_frame = wx.GetApp().GetTopWindow()

        # get saved keys, if any
        if os.path.isfile(self.keys_filename):
            with open(self.keys_filename, mode='r') as infile:
                self.keys = json.load(infile)

        # ethics/terms of use
        self.ethics_checkbox_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION+GUIText.ETHICS_TWITTER)
        self.ethics_hyperlink_ctrl = wx.adv.HyperlinkCtrl(self, label="1", url=GUIText.ETHICS_TWITTER_URL)

        ethics_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ethics_sizer.Add(self.ethics_checkbox_ctrl)
        ethics_sizer.Add(self.ethics_hyperlink_ctrl)
        sizer.Add(ethics_sizer, 0, wx.EXPAND | wx.ALL, 5)

        consumer_key_label = wx.StaticText(self, label=GUIText.CONSUMER_KEY + ": ")
        self.consumer_key_ctrl = wx.TextCtrl(self)
        if 'consumer_key' in self.keys:
            self.consumer_key_ctrl.SetValue(self.keys['consumer_key'])
        self.consumer_key_ctrl.SetToolTip(GUIText.CONSUMER_KEY_TOOLTIP)
        consumer_key_sizer = wx.BoxSizer(wx.HORIZONTAL)
        consumer_key_sizer.Add(consumer_key_label)
        consumer_key_sizer.Add(self.consumer_key_ctrl, wx.EXPAND)
        sizer.Add(consumer_key_sizer, 0, wx.EXPAND | wx.ALL, 5)
    
        consumer_secret_label = wx.StaticText(self, label=GUIText.CONSUMER_SECRET + ": ")
        self.consumer_secret_ctrl = wx.TextCtrl(self)
        if 'consumer_secret' in self.keys:
            self.consumer_secret_ctrl.SetValue(self.keys['consumer_secret'])
        self.consumer_secret_ctrl.SetToolTip(GUIText.CONSUMER_SECRET_TOOLTIP)
        consumer_secret_sizer = wx.BoxSizer(wx.HORIZONTAL)
        consumer_secret_sizer.Add(consumer_secret_label)
        consumer_secret_sizer.Add(self.consumer_secret_ctrl, wx.EXPAND)
        sizer.Add(consumer_secret_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # search by query
        self.query_radioctrl = wx.RadioButton(self, label=GUIText.QUERY+": ", style=wx.RB_GROUP)
        self.query_radioctrl.SetToolTip(GUIText.TWITTER_QUERY_RADIOBUTTON_TOOLTIP)
        self.query_radioctrl.SetValue(True)

        self.query_hyperlink_ctrl = wx.adv.HyperlinkCtrl(self, label="2", url=GUIText.TWITTER_QUERY_HYPERLINK)

        self.query_ctrl = wx.TextCtrl(self)
        self.query_ctrl.SetHint(GUIText.TWITTER_QUERY_PLACEHOLDER)
        self.query_ctrl.SetToolTip(GUIText.TWITTER_QUERY_TOOLTIP)

        query_items_sizer = wx.BoxSizer(wx.HORIZONTAL)
        query_items_sizer.Add(self.query_hyperlink_ctrl)
        query_items_sizer.AddSpacer(10)
        query_items_sizer.Add(self.query_ctrl, wx.EXPAND)

        query_sizer = wx.BoxSizer(wx.HORIZONTAL)
        query_sizer.Add(self.query_radioctrl)
        query_sizer.Add(query_items_sizer, wx.EXPAND)

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

        self.account_checkbox_ctrl = wx.CheckBox(self, label=GUIText.TWITTER_LABEL+" "+GUIText.ACCOUNTS+": ")
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

        # add 'search by' elements to box
        self.search_by_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=GUIText.SEARCH_BY+": ")
        self.search_by_sizer.Add(query_sizer, 0, wx.EXPAND)
        self.search_by_sizer.Add(attributes_sizer, 0, wx.EXPAND)

        # enable only the selected 'search by' option
        self.EnableOnlySelected(self.search_by_sizer)
        for search_by_option in self.search_by_sizer:
            option_sizer = search_by_option.GetSizer()
            # bind to each radiobutton
            option_sizer.GetChildren()[0].GetWindow().Bind(wx.EVT_RADIOBUTTON, lambda event: self.EnableOnlySelected(self.search_by_sizer))
        sizer.Add(self.search_by_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # retweets checkbox
        self.include_retweets_ctrl = wx.CheckBox(self, label=GUIText.INCLUDE_RETWEETS)
        sizer.Add(self.include_retweets_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        # dates
        date_sizer = wx.BoxSizer(wx.HORIZONTAL)

        start_date_label = wx.StaticText(self, label=GUIText.START_DATE+" ("+GUIText.UTC+")"+": ")
        self.start_date_ctrl = wx.adv.DatePickerCtrl(self, name="startDate",
                                                style=wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY)
        self.start_date_ctrl.SetToolTip(GUIText.START_DATE_TOOLTIP)
        start_date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        start_date_sizer.Add(start_date_label)
        start_date_sizer.Add(self.start_date_ctrl)

        end_date_label = wx.StaticText(self, label=GUIText.END_DATE+" ("+GUIText.UTC+")"+": ")
        self.end_date_ctrl = wx.adv.DatePickerCtrl(self, name="endDate",
                                              style=wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY)
        self.end_date_ctrl.SetToolTip(GUIText.END_DATE_TOOLTIP)
        end_date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        end_date_sizer.Add(end_date_label)
        end_date_sizer.Add(self.end_date_ctrl)

        date_sizer.Add(start_date_sizer, 0, wx.EXPAND, 5)
        date_sizer.AddSpacer(10)
        date_sizer.Add(end_date_sizer, 0, wx.EXPAND, 5)
        sizer.Add(date_sizer, 0, wx.ALL, 5)

        # warning/notice
        notice = wx.StaticText(self, label=GUIText.RETRIEVAL_NOTICE_TWITTER)
        sizer.Add(notice, 0, wx.EXPAND | wx.ALL, 5)
        
        metadata_fields_label = wx.StaticText(self, label=GUIText.METADATAFIELDS)
        self.metadata_fields_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.metadata_fields_ctrl.AppendColumn(GUIText.FIELD)
        self.metadata_fields_ctrl.AppendColumn(GUIText.DESCRIPTION)
        self.metadata_fields_ctrl.AppendColumn(GUIText.TYPE)
        self.metadata_fields_ctrl.SetToolTip(GUIText.METADATAFIELDS_TOOLTIP)
        self.metadata_fields_ctrl.EnableCheckBoxes()
        metadata_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        metadata_fields_sizer.Add(metadata_fields_label, 0, wx.ALL)
        metadata_fields_sizer.Add(self.metadata_fields_ctrl, 1, wx.EXPAND)
        if main_frame.adjustable_metadata_mode:
            sizer.Add(metadata_fields_sizer, 0, wx.ALL|wx.EXPAND, 5)
        else:
            metadata_fields_sizer.ShowItems(False)

        included_fields_label = wx.StaticText(self, label=GUIText.INCLUDEDFIELDS)
        self.included_fields_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.included_fields_ctrl.AppendColumn(GUIText.FIELD)
        self.included_fields_ctrl.AppendColumn(GUIText.DESCRIPTION)
        self.included_fields_ctrl.AppendColumn(GUIText.TYPE)
        self.included_fields_ctrl.SetToolTip(GUIText.INCLUDEDFIELDS_TOOLTIP)
        self.included_fields_ctrl.EnableCheckBoxes()
        included_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        included_fields_sizer.Add(included_fields_label, 0, wx.ALL)
        included_fields_sizer.Add(self.included_fields_ctrl, 1, wx.EXPAND)
        if main_frame.adjustable_includedfields_mode:
            sizer.Add(included_fields_sizer, 0, wx.ALL|wx.EXPAND, 5)
        else:
            included_fields_sizer.ShowItems(False)

        # TODO: defaults to tweet type for now, could add more (like with reddit) if needed
        self.OnDatasetTypeChosen(None)

        #Retriever button to collect the requested data
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label=GUIText.OK)
        button_sizer.Add(ok_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label=GUIText.CANCEL)
        button_sizer.Add(cancel_button)
        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()
        self.Fit()

        ok_button.Bind(wx.EVT_BUTTON, self.OnRetrieveStart)
        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
        CustomEvents.RETRIEVE_EVT_RESULT(self, self.OnRetrieveEnd)

        logger.info("Finished")

    def OnDatasetTypeChosen(self, event):
        logger = logging.getLogger(__name__+".TwitterRetrieverDialog.OnDatasetTypeChosen")
        logger.info("Starting")
        dataset_type = self.dataset_type

        self.avaliable_fields = Constants.avaliable_fields[('Twitter', dataset_type,)]

        self.metadata_fields_ctrl.DeleteAllItems()
        self.included_fields_ctrl.DeleteAllItems()
        idx = 0
        for key in self.avaliable_fields:
            self.metadata_fields_ctrl.Append([key, self.avaliable_fields[key]['desc'], self.avaliable_fields[key]['type']])
            if self.avaliable_fields[key]['metadata_default']:
                self.metadata_fields_ctrl.CheckItem(idx)
            self.included_fields_ctrl.Append([key, self.avaliable_fields[key]['desc'], self.avaliable_fields[key]['type']])
            if self.avaliable_fields[key]['included_default']:
                self.included_fields_ctrl.CheckItem(idx)
            idx = idx+1

        self.Layout()
        self.Fit()
        logger.info("Finished")

    def OnRetrieveStart(self, event):
        logger = logging.getLogger(__name__+".TwitterRetrieverDialog.OnRetrieveStart")
        logger.info("Starting")

        status_flag = True
        main_frame = wx.GetApp().GetTopWindow()
        keys = {}
        
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
        if not self.ethics_checkbox_ctrl.IsChecked():
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR+GUIText.ETHICS_TWITTER,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('Ethics not checked')
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

        search_by_options = self.GetOptionsInRadioGroup(self.search_by_sizer)
        selected_option = None
        for option in search_by_options:
            if option[0].GetValue():
                selected_option = option
                break
        
        # generate query
        query = ""
        if selected_option[0].GetLabel() == GUIText.QUERY+": ":
            query = self.query_ctrl.GetValue().strip()
        elif selected_option[0].GetLabel() == GUIText.TWITTER_TWEET_ATTRIBUTES+": ":
            query_items = [] # individual sub-queries, which are joined by UNION (OR) to form the overall query
            attributes_list_sizer = selected_option[1]
            for attribute_sizer in attributes_list_sizer.GetChildren():
                sizer = attribute_sizer.GetSizer()
                checkbox = sizer.GetChildren()[1].GetWindow()
                text_field = sizer.GetChildren()[2].GetWindow()
                if checkbox.GetValue() and text_field.GetValue() != "":
                    text = text_field.GetValue()
                    if checkbox.GetLabel() == GUIText.KEYWORDS+": ":
                        keywords = text.split(",")
                        for phrase in keywords:
                            phrase = phrase.strip()
                            if " " in phrase: # multi-word keyword
                                phrase = "\""+phrase+"\""
                            query_items.append(phrase)
                    elif checkbox.GetLabel() == GUIText.HASHTAGS+": ":
                        text = text.replace(",", " ")
                        hashtags = text.split()
                        for hashtag in hashtags:
                            hashtag = hashtag.strip()
                            if hashtag[0] != "#": # hashtags must start with '#' symbol
                                hashtag = "#"+hashtag
                            query_items.append(hashtag)
                    elif checkbox.GetLabel() == GUIText.TWITTER_LABEL+" "+GUIText.ACCOUNTS+": ":
                        text = text.replace(",", " ")
                        accounts = text.split()
                        for account in accounts:
                            account = account.strip()
                            if not account.startswith("from:"):
                                account = "from:"+account
                            query_items.append(account)
            for i in range(len(query_items)):
                query += query_items[i]
                if i < len(query_items)-1:
                    query += " OR "
        
        if query == "":
            wx.MessageBox(GUIText.TWITTER_QUERY_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No query entered')
            status_flag = False
        else:
            # retweets flag
            if not self.include_retweets_ctrl.GetValue():
                query += " -filter:retweets "
        query = query.strip() # trim whitespace
        print("QUERY: " + query) # TODO remove
        logger.info("Query: "+query)

        name = query

        start_date = str(self.start_date_ctrl.GetValue().Format("%Y-%m-%d"))
        end_date = str(self.end_date_ctrl.GetValue().Format("%Y-%m-%d"))
        if start_date > end_date:
            wx.MessageBox(GUIText.DATE_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning("Start Date[%s] not before End Date[%s]",
                           str(start_date), str(end_date))
            status_flag = False

        dataset_source = "Twitter"
        
        dataset_key = (query, dataset_source, self.dataset_type)
        if dataset_key in main_frame.datasets:
            wx.MessageBox(GUIText.NAME_EXISTS_ERROR,
                          GUIText.ERROR,
                          wx.OK | wx.ICON_ERROR)
            logger.warning("Data with same name[%s] already exists", query)
            status_flag = False

        metadata_fields_list = []
        item = self.metadata_fields_ctrl.GetNextItem(-1)
        while item != -1:
            if self.metadata_fields_ctrl.IsItemChecked(item):
                field_name = self.metadata_fields_ctrl.GetItemText(item, 0)
                metadata_fields_list.append((field_name, self.avaliable_fields[field_name],))
            item = self.metadata_fields_ctrl.GetNextItem(item)
        
        included_fields_list = []
        item = self.included_fields_ctrl.GetNextItem(-1)
        while item != -1:
            if self.included_fields_ctrl.IsItemChecked(item):
                field_name = self.included_fields_ctrl.GetItemText(item, 0)
                included_fields_list.append((field_name, self.avaliable_fields[field_name],))
            item = self.included_fields_ctrl.GetNextItem(item)

        if status_flag:
            # save keys
            with open(self.keys_filename, mode='w') as outfile:
                json.dump(keys, outfile)

            main_frame.CreateProgressDialog(title=GUIText.RETRIEVING_LABEL+query,
                                            warning=GUIText.SIZE_WARNING_MSG,
                                            freeze=True)
            self.Disable()
            self.Freeze()
            main_frame.PulseProgressDialog(GUIText.RETRIEVING_BEGINNING_MSG)
            self.retrieval_thread = CollectionThreads.RetrieveTwitterDatasetThread(self, main_frame, name, keys, query, start_date, end_date, self.dataset_type,
                                                                                    list(self.avaliable_fields.items()), metadata_fields_list, included_fields_list)
        logger.info("Finished")

class CSVDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".CSVRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_CSV_LABEL, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.retrieval_thread = None
        self.avaliable_fields = {}

        sizer = wx.BoxSizer(wx.VERTICAL)

        name_label = wx.StaticText(self, label=GUIText.NAME + ": ")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label)
        name_sizer.Add(self.name_ctrl)
        sizer.Add(name_sizer, 0, wx.ALL, 5)
        

        filename_label = wx.StaticText(self, label=GUIText.FILENAME + ": ")
        self.filename_ctrl = wx.FilePickerCtrl(self, wildcard="CSV files (*.csv)|*.csv")
        self.filename_ctrl.SetInitialDirectory('../Data/CSV')
        filename_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filename_sizer.Add(filename_label)
        filename_sizer.Add(self.filename_ctrl)
        self.filename_ctrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnFilenameChosen)
        sizer.Add(filename_sizer, 0, wx.ALL, 5)

        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.multipledatasets_mode:
            dataset_field_label = wx.StaticText(self, label=GUIText.CSV_DATASETFIELD)
            self.dataset_field_ctrl = wx.Choice(self, choices=[])
            self.dataset_field_ctrl.SetToolTip(GUIText.CSV_DATASETFIELD_TOOLTIP)
            dataset_field_sizer = wx.BoxSizer(wx.HORIZONTAL)
            dataset_field_sizer.Add(dataset_field_label)
            dataset_field_sizer.Add(self.dataset_field_ctrl)
            sizer.Add(dataset_field_sizer, 0, wx.ALL, 5)
        
        id_field_label = wx.StaticText(self, label=GUIText.CSV_IDFIELD)
        self.id_field_ctrl = wx.Choice(self, choices=[GUIText.CSV_IDFIELD_DEFAULT])
        self.id_field_ctrl.SetToolTip(GUIText.CSV_IDFIELD_TOOLTIP)
        id_field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        id_field_sizer.Add(id_field_label)
        id_field_sizer.Add(self.id_field_ctrl)
        sizer.Add(id_field_sizer, 0, wx.ALL, 5)

        url_field_label = wx.StaticText(self, label=GUIText.CSV_URLFIELD)
        self.url_field_ctrl = wx.Choice(self, choices=[""])
        self.url_field_ctrl.SetToolTip(GUIText.CSV_URLFIELD_TOOLTIP)
        url_field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        url_field_sizer.Add(url_field_label)
        url_field_sizer.Add(self.url_field_ctrl)
        sizer.Add(url_field_sizer, 0, wx.ALL, 5)

        datetime_field_label = wx.StaticText(self, label=GUIText.CSV_DATETIMEFIELD)
        self.datetime_field_ctrl = wx.Choice(self, choices=[""])
        self.datetime_field_ctrl.SetToolTip(GUIText.CSV_DATETIMEFIELD_TOOLTIP)
        self.datetime_tz_ctrl = wx.Choice(self, choices=pytz.all_timezones)
        datetime_field_sizer = wx.BoxSizer(wx.HORIZONTAL)
        datetime_field_sizer.Add(datetime_field_label)
        datetime_field_sizer.Add(self.datetime_field_ctrl)
        datetime_field_sizer.Add(self.datetime_tz_ctrl)
        sizer.Add(datetime_field_sizer, 0, wx.ALL, 5)

        metadata_first_label = wx.StaticText(self, label=GUIText.METADATAFIELDS)
        self.metadata_first_ctrl = wx.ListCtrl(self, style=wx.LC_LIST|wx.LC_NO_HEADER)
        self.metadata_first_ctrl.SetToolTip(GUIText.METADATAFIELDS_TOOLTIP)
        self.metadata_first_ctrl.EnableCheckBoxes()
        metadata_first_sizer = wx.BoxSizer(wx.VERTICAL)
        metadata_first_sizer.Add(metadata_first_label)
        metadata_first_sizer.Add(self.metadata_first_ctrl, 1, wx.EXPAND)
        metadata_combined_label = wx.StaticText(self, label=GUIText.COMBINED_METADATAFIELDS)
        self.metadata_combined_ctrl = wx.ListCtrl(self, style=wx.LC_LIST|wx.LC_NO_HEADER)
        self.metadata_combined_ctrl.SetToolTip(GUIText.COMBINED_METADATAFIELDS_TOOLTIP)
        self.metadata_combined_ctrl.EnableCheckBoxes()
        metadata_combined_sizer = wx.BoxSizer(wx.VERTICAL)
        metadata_combined_sizer.Add(metadata_combined_label)
        metadata_combined_sizer.Add(self.metadata_combined_ctrl, 1, wx.EXPAND)
        metadata_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        metadata_fields_sizer.Add(metadata_first_sizer, 1, wx.EXPAND)
        metadata_fields_sizer.Add(metadata_combined_sizer, 1, wx.EXPAND)
        if main_frame.adjustable_metadata_mode:
            sizer.Add(metadata_fields_sizer, 1, wx.EXPAND|wx.ALL, 5)
        else:
            metadata_fields_sizer.ShowItems(False)

        included_first_label = wx.StaticText(self, label=GUIText.INCLUDEDFIELDS)
        self.included_first_ctrl = wx.ListCtrl(self, style=wx.LC_LIST|wx.LC_NO_HEADER)
        self.included_first_ctrl.SetToolTip(GUIText.INCLUDEDFIELDS_TOOLTIP)
        self.included_first_ctrl.EnableCheckBoxes()
        included_first_sizer = wx.BoxSizer(wx.VERTICAL)
        included_first_sizer.Add(included_first_label)
        included_first_sizer.Add(self.included_first_ctrl, 1, wx.EXPAND)
        included_combined_label = wx.StaticText(self, label=GUIText.COMBINED_INCLUDEDFIELDS)
        self.included_combined_ctrl = wx.ListCtrl(self, style=wx.LC_LIST|wx.LC_NO_HEADER)
        self.included_combined_ctrl.SetToolTip(GUIText.COMBINED_INCLUDEDFIELDS_TOOLTIP)
        self.included_combined_ctrl.EnableCheckBoxes()
        included_combined_sizer = wx.BoxSizer(wx.VERTICAL)
        included_combined_sizer.Add(included_combined_label)
        included_combined_sizer.Add(self.included_combined_ctrl, 1, wx.EXPAND)
        included_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        included_fields_sizer.Add(included_first_sizer, 1, wx.EXPAND)
        included_fields_sizer.Add(included_combined_sizer, 1, wx.EXPAND)
        sizer.Add(included_fields_sizer, 1, wx.EXPAND|wx.ALL, 5)
        
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnDragInit, self.included_first_ctrl)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnDragInit, self.included_combined_ctrl)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnDragInit, self.metadata_first_ctrl)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.OnDragInit, self.metadata_combined_ctrl)
        metadata_first_dt = FieldDropTarget(self.included_first_ctrl, self.metadata_first_ctrl, self.included_combined_ctrl, self.metadata_combined_ctrl)
        self.metadata_first_ctrl.SetDropTarget(metadata_first_dt)
        metadata_combined_dt = FieldDropTarget(self.included_combined_ctrl, self.metadata_combined_ctrl, self.included_first_ctrl, self.metadata_first_ctrl)
        self.metadata_combined_ctrl.SetDropTarget(metadata_combined_dt)
        include_first_dt = FieldDropTarget(self.included_first_ctrl, self.metadata_first_ctrl, self.included_combined_ctrl, self.metadata_combined_ctrl)
        self.included_first_ctrl.SetDropTarget(include_first_dt)
        include_combined_dt = FieldDropTarget(self.included_combined_ctrl, self.metadata_combined_ctrl, self.included_first_ctrl, self.metadata_first_ctrl)
        self.included_combined_ctrl.SetDropTarget(include_combined_dt)

        #Retriever button to collect the requested data
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label=GUIText.OK)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label=GUIText.CANCEL)
        button_sizer.Add(ok_button)
        button_sizer.Add(cancel_button)
        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
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
                self.id_field_ctrl.Clear()
                self.id_field_ctrl.Append(GUIText.CSV_IDFIELD_DEFAULT)
                self.url_field_ctrl.Clear()
                self.url_field_ctrl.Append("")
                self.datetime_field_ctrl.Clear()
                self.datetime_field_ctrl.Append("")
                self.metadata_first_ctrl.DeleteAllItems()
                self.metadata_combined_ctrl.DeleteAllItems()
                self.included_first_ctrl.DeleteAllItems()
                self.included_combined_ctrl.DeleteAllItems()
                self.avaliable_fields.clear()
                main_frame = wx.GetApp().GetTopWindow()
                if main_frame.multipledatasets_mode:
                    self.dataset_field_ctrl.Clear()
                    self.dataset_field_ctrl.Append("")
                idx = 0
                for field_name in Constants.avaliable_fields[('CSV', 'documents',)]:
                    self.avaliable_fields[field_name] = Constants.avaliable_fields[('CSV', 'documents',)][field_name]
                    self.metadata_first_ctrl.Append([field_name])
                    if self.avaliable_fields[field_name]['metadata_default']:
                        self.metadata_first_ctrl.CheckItem(idx)
                    idx = idx+1
                for column_name in header_row:
                    if main_frame.multipledatasets_mode:
                        self.dataset_field_ctrl.Append(column_name)
                    self.id_field_ctrl.Append(column_name)
                    self.url_field_ctrl.Append(column_name)
                    self.datetime_field_ctrl.Append(column_name)
                    self.metadata_first_ctrl.Append(["csv."+column_name])
                    self.included_first_ctrl.Append(["csv."+column_name])
                    self.avaliable_fields["csv."+column_name] = {"desc":"CSV Field", "type":"string"}
                self.Layout()
                self.Fit()
        logger.info("Finished")

    def OnDragInit(self, event):
        text = event.GetEventObject().GetItemText(event.GetIndex())
        tobj = wx.TextDataObject(text)
        src = wx.DropSource(event.GetEventObject())
        src.SetData(tobj)
        src.DoDragDrop(True)

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
        
        id_field = self.id_field_ctrl.GetStringSelection()
        if id_field == "":
            wx.MessageBox(GUIText.CSV_IDFIELD_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No id field chosen')
            status_flag = False
        
        datetime_field = self.datetime_field_ctrl.GetStringSelection()
        datetime_tz = self.datetime_tz_ctrl.GetStringSelection()
        if datetime_field != '':
            if datetime_tz not in pytz.all_timezones:
                wx.MessageBox(GUIText.CSV_DATETIMETZ_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                logger.warning('No datetime tz chosen')
                status_flag = False
            if not main_frame.adjustable_metadata_mode:
                idx = self.metadata_first_ctrl.FindItem(-1, "created_utc")
                self.metadata_first_ctrl.CheckItem(idx, True)

        url_field = self.url_field_ctrl.GetStringSelection()
        if url_field != "" and not main_frame.adjustable_metadata_mode:
            idx = self.metadata_first_ctrl.FindItem(-1, "id")
            self.metadata_first_ctrl.CheckItem(idx, False)
            idx = self.metadata_first_ctrl.FindItem(-1, "url")
            self.metadata_first_ctrl.CheckItem(idx, True)

        metadata_field_list = []
        included_field_list = []
        combined_list = []
        item_idx = -1
        while 1:
            item_idx = self.metadata_first_ctrl.GetNextItem(item_idx)
            if item_idx == -1:
                break
            else:
                if self.metadata_first_ctrl.IsItemChecked(item_idx):
                    field_name = self.metadata_first_ctrl.GetItemText(item_idx)
                    metadata_field_list.append((field_name, self.avaliable_fields[field_name],))
        
        item_idx = -1
        while 1:
            item_idx = self.metadata_combined_ctrl.GetNextItem(item_idx)
            if item_idx == -1:
                break
            else:
                field_name = self.metadata_combined_ctrl.GetItemText(item_idx)    
                if (field_name, self.avaliable_fields[field_name],) not in combined_list:
                    combined_list.append(field_name)
                if self.metadata_combined_ctrl.IsItemChecked(item_idx):
                    metadata_field_list.append((field_name, self.avaliable_fields[field_name],))
        
        item_idx = -1
        while 1:
            item_idx = self.included_first_ctrl.GetNextItem(item_idx)
            if item_idx == -1:
                break
            else:
                if self.included_first_ctrl.IsItemChecked(item_idx):
                    field_name = self.included_first_ctrl.GetItemText(item_idx)
                    included_field_list.append((field_name, self.avaliable_fields[field_name],))
                    if not main_frame.adjustable_metadata_mode:
                        if (field_name, self.avaliable_fields[field_name],) not in metadata_field_list:
                            included_field_list.append((field_name, self.avaliable_fields[field_name],))
        
        item_idx = -1
        while 1:
            item_idx = self.included_combined_ctrl.GetNextItem(item_idx)
            if item_idx == -1:
                break
            else:
                field_name = self.included_combined_ctrl.GetItemText(item_idx)
                if (field_name, self.avaliable_fields[field_name],) not in combined_list:
                    combined_list.append(field_name)
                if self.included_combined_ctrl.IsItemChecked(item_idx):
                    included_field_list.append((field_name, self.avaliable_fields[field_name],))
                    if not main_frame.adjustable_metadata_mode:
                        if (field_name, self.avaliable_fields[field_name],) not in metadata_field_list:
                            metadata_field_list.append((field_name, self.avaliable_fields[field_name],))

        dataset_source = "CSV"
        if main_frame.multipledatasets_mode:
            dataset_field = self.dataset_field_ctrl.GetStringSelection()
        else:
            dataset_field = ""
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
            self.retrieval_thread = CollectionThreads.RetrieveCSVDatasetThread(self, main_frame, name, dataset_field, dataset_type,
                                                                               id_field, url_field, datetime_field, datetime_tz,
                                                                               list(self.avaliable_fields.items()), metadata_field_list, included_field_list, combined_list, filename)
        logger.info("Finished")
    
class FieldDropTarget(wx.TextDropTarget):
    def __init__(self, dest1, dest2, source1, source2):
        wx.TextDropTarget.__init__(self)
        self.dest1 = dest1
        self.dest2 = dest2
        self.source1 = source1
        self.source2 = source2
    def OnDropText(self, x, y, data):
        idx = self.source1.FindItem(-1, data)
        if idx is not wx.NOT_FOUND:
            self.source1.DeleteItem(idx)
        idx = self.source2.FindItem(-1, data)
        if idx is not wx.NOT_FOUND:
            self.source2.DeleteItem(idx)
        if self.dest1.FindItem(-1, data) is wx.NOT_FOUND:
            self.dest1.InsertItem(0, data)
        if self.dest2.FindItem(-1, data) is wx.NOT_FOUND:
            self.dest2.InsertItem(0, data)
        return True