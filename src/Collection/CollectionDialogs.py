import logging
import json
import csv
import os.path
import calendar
import tweepy
from datetime import datetime
from dateutil.relativedelta import relativedelta

import wx
import wx.grid
import wx.dataview as dv

from Common import Constants as Constants
from Common.GUIText import Collection as GUIText
import Common.Objects.Datasets as Datasets
import Common.CustomEvents as CustomEvents
import Collection.CollectionThreads as CollectionThreads
import Collection.SubModuleDatasets as SubModuleDatasets
import Collection.DataTokenizer as DataTokenizer

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

        self.ethics_ctrl = wx.CheckBox(self, label=GUIText.ETHICS_CONFIRMATION)
        self.ethics_ctrl.SetToolTip(GUIText.ETHICS_CONFIRMATION_TOOLTIP)

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

        #control where data is retrieved from
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

        #choose type of dataset to retrieve
        self.dataset_type_choice = wx.Choice(self, choices=[GUIText.REDDIT_DISCUSSIONS, GUIText.REDDIT_SUBMISSIONS, GUIText.REDDIT_COMMENTS])

        #Retriever button to collect the requested data
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label=GUIText.OK)
        button_sizer.Add(ok_button)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label=GUIText.CANCEL)
        button_sizer.Add(cancel_button)

        retriever_sizer = wx.BoxSizer(wx.VERTICAL)
        retriever_sizer.Add(name_sizer)
        retriever_sizer.Add(subreddit_sizer)
        retriever_sizer.Add(self.ethics_ctrl)
        retriever_sizer.Add(start_date_sizer)
        retriever_sizer.Add(end_date_sizer)
        retriever_sizer.Add(self.archived_radioctrl)
        retriever_sizer.Add(self.update_pushshift_radioctrl)
        retriever_sizer.Add(self.full_pushshift_radioctrl)
        #retriever_sizer.Add(self.update_redditapi_radioctrl)
        #retriever_sizer.Add(self.full_redditapi_radioctrl)
        retriever_sizer.Add(self.dataset_type_choice)
        retriever_sizer.Add(button_sizer)

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
        
        name = self.name_ctrl.GetValue()
        if name == "":
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No name entered')
            status_flag = False
        subreddit = self.subreddit_ctrl.GetValue()
        if subreddit == "":
            wx.MessageBox(GUIText.REDDIT_SUBREDDIT_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No subreddit entered')
            status_flag = False
        ethics_flg = self.ethics_ctrl.IsChecked()
        if not ethics_flg:
            wx.MessageBox(GUIText.ETHICS_CONFIRMATION_MISSING_ERROR,
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

        name_label = wx.StaticText(self, label=GUIText.NAME+": ")
        self.name_ctrl = wx.TextCtrl(self)
        self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(name_label)
        name_sizer.Add(self.name_ctrl)

        consumer_key_label = wx.StaticText(self, label=GUIText.CONSUMER_KEY + ": ")
        self.consumer_key_ctrl = wx.TextCtrl(self)
        self.consumer_key_ctrl.SetToolTip(GUIText.CONSUMER_KEY_TOOLTIP)
        consumer_key_sizer = wx.BoxSizer(wx.HORIZONTAL)
        consumer_key_sizer.Add(consumer_key_label)
        consumer_key_sizer.Add(self.consumer_key_ctrl)
    
        consumer_secret_label = wx.StaticText(self, label=GUIText.CONSUMER_SECRET + ": ")
        self.consumer_secret_ctrl = wx.TextCtrl(self)
        self.consumer_secret_ctrl.SetToolTip(GUIText.CONSUMER_SECRET_TOOLTIP)
        consumer_secret_sizer = wx.BoxSizer(wx.HORIZONTAL)
        consumer_secret_sizer.Add(consumer_secret_label)
        consumer_secret_sizer.Add(self.consumer_secret_ctrl)

        query_label = wx.StaticText(self, label=GUIText.TWITTER_QUERY+": ")
        self.query_ctrl = wx.TextCtrl(self)
        self.query_ctrl.SetToolTip(GUIText.TWITTER_QUERY_TOOLTIP)
        query_sizer = wx.BoxSizer(wx.HORIZONTAL)
        query_sizer.Add(query_label)
        query_sizer.Add(self.query_ctrl)

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
        retriever_sizer.Add(name_sizer)
        retriever_sizer.Add(consumer_key_sizer)
        retriever_sizer.Add(consumer_secret_sizer)
        retriever_sizer.Add(query_sizer)
        retriever_sizer.Add(start_date_sizer)
        retriever_sizer.Add(end_date_sizer)
        retriever_sizer.Add(button_sizer)

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
        
        name = self.name_ctrl.GetValue()
        if name == "":
            wx.MessageBox(GUIText.NAME_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No name entered')
            status_flag = False
        consumer_key = self.consumer_key_ctrl.GetValue()
        if consumer_key == "":
            wx.MessageBox(GUIText.CONSUMER_KEY_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No consumer key entered')
            status_flag = False
        consumer_secret = self.consumer_secret_ctrl.GetValue()
        if consumer_secret == "":
            wx.MessageBox(GUIText.CONSUMER_SECRET_MISSING_ERROR,
                          GUIText.ERROR, wx.OK | wx.ICON_ERROR)
            logger.warning('No consumer secret entered')
            status_flag = False

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
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
            main_frame.CreateProgressDialog(title=GUIText.RETRIEVING_LABEL+name,
                                            warning=GUIText.SIZE_WARNING_MSG,
                                            freeze=True)
            self.Disable()
            self.Freeze()
            main_frame.PulseProgressDialog(GUIText.RETRIEVING_BEGINNING_MSG)
            self.retrieval_thread = CollectionThreads.RetrieveTwitterDatasetThread(self, main_frame, name, consumer_key, consumer_secret, query, start_date, end_date, dataset_type)
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
        retriever_sizer.Add(name_sizer)
        retriever_sizer.Add(filename_sizer)
        retriever_sizer.Add(dataset_field_sizer)
        retriever_sizer.Add(id_field_sizer)
        retriever_sizer.Add(included_fields_sizer)
        retriever_sizer.Add(button_sizer)

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

class DatasetDetailsDialog(wx.Dialog):
    def __init__(self, parent, dataset):
        logger = logging.getLogger(__name__+".DatasetDetailsDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.GROUPED_DATASET_LABEL, style=wx.CAPTION|wx.RESIZE_BORDER)

        self.dataset = dataset
        self.tokenization_thread = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        if isinstance(dataset, Datasets.GroupedDataset):
            name_label = wx.StaticText(self, label=GUIText.NAME + ":")
            self.name_ctrl = wx.TextCtrl(self, value=self.dataset.name, style=wx.TE_PROCESS_ENTER)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            self.name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDatasetKey)
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_sizer.Add(name_label)
            name_sizer.Add(self.name_ctrl)
            self.sizer.Add(name_sizer)

            created_date_label = wx.StaticText(self, label=GUIText.CREATED_ON + ": "
                                               +self.dataset.created_dt.strftime("%Y-%m-%d, %H:%M:%S"))
            self.sizer.Add(created_date_label)

            selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(dataset.language)
            language_label = wx.StaticText(self, label=GUIText.LANGUAGE + ": ")
            self.language_ctrl = wx.Choice(self, choices=Constants.AVALIABLE_DATASET_LANGUAGES2)
            self.language_ctrl.Select(selected_lang)
            language_sizer = wx.BoxSizer(wx.HORIZONTAL)
            language_sizer.Add(language_label)
            language_sizer.Add(self.language_ctrl)
            self.sizer.Add(language_sizer, 0, wx.ALL, 5)

        elif isinstance(dataset, Datasets.Dataset) and dataset.dataset_source == 'Reddit':
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_label = wx.StaticText(self, label=GUIText.NAME + ":")
            name_sizer.Add(name_label)
            self.name_ctrl = wx.TextCtrl(self, value=dataset.name, style=wx.TE_PROCESS_ENTER)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            self.name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDatasetKey)
            name_sizer.Add(self.name_ctrl)
            self.sizer.Add(name_sizer, 0, wx.ALL, 5)

            retrieved_date_label = wx.StaticText(self, label=GUIText.RETRIEVED_ON + ": "
                                                +dataset.created_dt.strftime("%Y-%m-%d, %H:%M:%S"))
            self.sizer.Add(retrieved_date_label, 0, wx.ALL, 5)

            if dataset.parent is None:
                selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(dataset.language)
                language_label = wx.StaticText(self, label=GUIText.LANGUAGE + ": ")
                self.language_ctrl = wx.Choice(self, choices=Constants.AVALIABLE_DATASET_LANGUAGES2)
                self.language_ctrl.Select(selected_lang)
                language_sizer = wx.BoxSizer(wx.HORIZONTAL)
                language_sizer.Add(language_label)
                language_sizer.Add(self.language_ctrl)
                self.sizer.Add(language_sizer, 0, wx.ALL, 5)
            else:
                selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(dataset.language)
                language_label = wx.StaticText(self, label=GUIText.LANGUAGE + ": " + Constants.AVALIABLE_DATASET_LANGUAGES2[selected_lang])
                self.sizer.Add(language_label, 0, wx.ALL, 5)

            subreddit_label = wx.StaticText(self, label=GUIText.REDDIT_SUBREDDIT + ": "
                                            +dataset.retrieval_details['subreddit'])
            self.sizer.Add(subreddit_label, 0, wx.ALL, 5)

            start_date_label = wx.StaticText(self, label=GUIText.START_DATE + ": "
                                            +dataset.retrieval_details['start_date'])
            self.sizer.Add(start_date_label, 0, wx.ALL, 5)

            end_date_label = wx.StaticText(self, label=GUIText.END_DATE + ": "
                                        +dataset.retrieval_details['end_date'])
            self.sizer.Add(end_date_label, 0, wx.ALL, 5)

            if dataset.retrieval_details['pushshift_flg']:
                if dataset.retrieval_details['replace_archive_flg']:
                    if dataset.retrieval_details['redditapi_flg']:
                        retrieveonline_label = wx.StaticText(self, label=u'\u2611' + " " + GUIText.REDDIT_FULL_REDDITAPI)
                    else:
                        retrieveonline_label = wx.StaticText(self, label=u'\u2611' + " " + GUIText.REDDIT_FULL_PUSHSHIFT)
                else:
                    if dataset.retrieval_details['redditapi_flg']:
                        retrieveonline_label = wx.StaticText(self, label=u'\u2611' + " " + GUIText.REDDIT_UPDATE_REDDITAPI)
                    else:
                        retrieveonline_label = wx.StaticText(self, label=u'\u2611' + " " + GUIText.REDDIT_UPDATE_PUSHSHIFT)
            else:
                retrieveonline_label = wx.StaticText(self, label=u'\u2611' + " " + GUIText.REDDIT_ARCHIVED)
            self.sizer.Add(retrieveonline_label, 0, wx.ALL, 5)

            document_num_label = wx.StaticText(self, label=GUIText.DOCUMENT_NUM+": " + str(len(self.dataset.data)))
            self.sizer.Add(document_num_label)

        elif isinstance(dataset, Datasets.Dataset) and dataset.dataset_source == 'CSV':
            name_sizer = wx.BoxSizer(wx.HORIZONTAL)
            name_label = wx.StaticText(self, label=GUIText.NAME + ":")
            name_sizer.Add(name_label)
            self.name_ctrl = wx.TextCtrl(self, value=dataset.name, style=wx.TE_PROCESS_ENTER)
            self.name_ctrl.SetToolTip(GUIText.NAME_TOOLTIP)
            self.name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDatasetKey)
            name_sizer.Add(self.name_ctrl)
            self.sizer.Add(name_sizer, 0, wx.ALL, 5)

            retrieved_date_label = wx.StaticText(self, label=GUIText.RETRIEVED_ON + ": "
                                                +dataset.created_dt.strftime("%Y-%m-%d, %H:%M:%S"))
            self.sizer.Add(retrieved_date_label, 0, wx.ALL, 5)

            if dataset.parent is None:
                selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(dataset.language)
                language_label = wx.StaticText(self, label=GUIText.LANGUAGE + ": ")
                self.language_ctrl = wx.Choice(self, choices=Constants.AVALIABLE_DATASET_LANGUAGES2)
                self.language_ctrl.Select(selected_lang)
                language_sizer = wx.BoxSizer(wx.HORIZONTAL)
                language_sizer.Add(language_label)
                language_sizer.Add(self.language_ctrl)
                self.sizer.Add(language_sizer, 0, wx.ALL, 5)
            else:
                selected_lang = Constants.AVALIABLE_DATASET_LANGUAGES1.index(dataset.language)
                language_label = wx.StaticText(self, label=GUIText.LANGUAGE + ": " + Constants.AVALIABLE_DATASET_LANGUAGES2[selected_lang])
                self.sizer.Add(language_label, 0, wx.ALL, 5)

            document_num_label = wx.StaticText(self, label=GUIText.DOCUMENT_NUM+": " + str(len(self.dataset.data)))
            self.sizer.Add(document_num_label)

        #Close button to collect the requested data
        ok_button = wx.Button(self, id=wx.ID_OK, label=GUIText.OK)
        cancel_button = wx.Button(self, id=wx.ID_CANCEL, label=GUIText.CANCEL)
        ok_button.Bind(wx.EVT_BUTTON, self.OnChangeDatasetKey)
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        controls_sizer.Add(ok_button)
        controls_sizer.Add(cancel_button)
        self.sizer.Add(controls_sizer)

        self.SetSizer(self.sizer)
        self.Layout()

        CustomEvents.EVT_PROGRESS(self, self.OnProgress)
        CustomEvents.TOKENIZER_EVT_RESULT(self, self.OnTokenizerEnd)

        logger.info("Finished")
    
    def OnChangeDatasetKey(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsDialog.OnChangeDatasetKey")
        logger.info("Starting")
        main_frame = wx.GetApp().GetTopWindow()
        if main_frame.threaded_inprogress_flag == True:
            wx.MessageBox("A memory intensive operation is currently in progress."\
                          "\n Please try current action again after this operation has completed",
                          GUIText.WARNING, wx.OK | wx.ICON_WARNING)
            return

        main_frame.CreateProgressDialog(GUIText.CHANGING_NAME_BUSY_LABEL,
                                        freeze=True)
        updated_flag = False
        tokenizing_flag = False
        try:
            main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_PREPARING_MSG)
            node = self.dataset
            if isinstance(node, Datasets.Dataset) or isinstance(node, Datasets.GroupedDataset):
                new_name = self.name_ctrl.GetValue()
                
                if node.name != new_name:
                    old_key = node.key
                    if isinstance(node, Datasets.GroupedDataset):
                        new_key = (new_name, 'group')
                    elif isinstance(node, Datasets.Dataset):
                        new_key = (new_name, node.dataset_source, node.dataset_type,)
                    if new_key in main_frame.datasets:
                        wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                                        GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                        logger.error("Duplicate name[%s] entered by user", str(new_key))
                    else:
                        continue_flag = True
                        for key in main_frame.datasets:
                            if isinstance(main_frame.datasets[key], Datasets.GroupedDataset):
                                if new_key in main_frame.datasets[key].datasets:
                                    continue_flag = False
                                    wx.MessageBox(GUIText.NAME_DUPLICATE_ERROR,
                                        GUIText.ERROR, wx.OK | wx.ICON_ERROR)
                                    logger.error("Duplicate name[%s] entered by user", str(new_key))
                                    break
                        if continue_flag:
                            main_frame.PulseProgressDialog(GUIText.CHANGING_NAME_BUSY_MSG1+str(node.key)\
                                                  +GUIText.CHANGING_NAME_BUSY_MSG2+str(new_key))

                            node.key = new_key
                            node.name = new_name
                            if old_key in main_frame.datasets:
                                main_frame.datasets[new_key] = main_frame.datasets[old_key]
                                del main_frame.datasets[old_key]
                            elif node.parent is not None:
                                node.parent.datasets[new_key] = node
                                del node.parent.datasets[old_key]
                            main_frame.DatasetKeyChange(old_key, new_key)
                            updated_flag = True
                language_index = self.language_ctrl.GetSelection()
                if node.language != Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]:
                    main_frame.PulseProgressDialog(GUIText.CHANGING_LANGUAGE_BUSY_PREPARING_MSG)
                    node.language = Constants.AVALIABLE_DATASET_LANGUAGES1[language_index]
                    main_frame.threaded_inprogress_flag = True
                    self.tokenization_thread = CollectionThreads.TokenizerThread(self, main_frame, [node])
                    tokenizing_flag = True
        finally:
            if not tokenizing_flag:
                if updated_flag:
                    main_frame.DatasetsUpdated()
                main_frame.CloseProgressDialog(thaw=True)
                self.Close()
        logger.info("Finished")

    def OnTokenizerEnd(self, event):
        logger = logging.getLogger(__name__+".DatasetDetailsDialog.OnTokenizerEnd")
        logger.info("Starting")
        self.tokenization_thread = None
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.DatasetsUpdated()
        main_frame.CloseProgressDialog(thaw=True)
        main_frame.threaded_inprogress_flag = False
        self.Close()
        logger.info("Finished")
    
    def OnProgress(self, event):
        main_frame = wx.GetApp().GetTopWindow()
        main_frame.PulseProgressDialog(event.data)

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