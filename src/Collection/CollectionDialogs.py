import logging
import csv
import os.path
import pytz

import wx
import wx.adv
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

class RedditDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".RedditRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_REDDIT_LABEL)
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

class CSVDatasetRetrieverDialog(AbstractRetrieverDialog):
    def __init__(self, parent):
        logger = logging.getLogger(__name__+".CSVRetrieverDialog.__init__")
        logger.info("Starting")
        wx.Dialog.__init__(self, parent, title=GUIText.RETRIEVE_CSV_LABEL)
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

        metadata_fields_label = wx.StaticText(self, label=GUIText.METADATAFIELDS)
        self.metadata_fields_ctrl = wx.CheckListBox(self, style=wx.LB_MULTIPLE)
        self.metadata_fields_ctrl.SetToolTip(GUIText.METADATAFIELDS_TOOLTIP)
        metadata_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        metadata_fields_sizer.Add(metadata_fields_label)
        metadata_fields_sizer.Add(self.metadata_fields_ctrl)
        if main_frame.adjustable_metadata_mode:
            sizer.Add(metadata_fields_sizer, 0, wx.ALL, 5)
        else:
            metadata_fields_sizer.ShowItems(False)

        included_fields_label = wx.StaticText(self, label=GUIText.INCLUDEDFIELDS)
        self.included_fields_ctrl = wx.CheckListBox(self, style=wx.LB_MULTIPLE)
        self.included_fields_ctrl.SetToolTip(GUIText.INCLUDEDFIELDS_TOOLTIP)
        included_fields_sizer = wx.BoxSizer(wx.HORIZONTAL)
        included_fields_sizer.Add(included_fields_label)
        included_fields_sizer.Add(self.included_fields_ctrl)
        sizer.Add(included_fields_sizer, 0, wx.ALL, 5)

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
                self.metadata_fields_ctrl.Clear()
                self.included_fields_ctrl.Clear()
                self.avaliable_fields.clear()
                main_frame = wx.GetApp().GetTopWindow()
                if main_frame.multipledatasets_mode:
                    self.dataset_field_ctrl.Clear()
                    self.dataset_field_ctrl.Append("")
                idx = 0
                for field_name in Constants.avaliable_fields[('CSV', 'documents',)]:
                    self.avaliable_fields[field_name] = Constants.avaliable_fields[('CSV', 'documents',)][field_name]
                    self.metadata_fields_ctrl.Append(field_name)
                    if self.avaliable_fields[field_name]['metadata_default']:
                        self.metadata_fields_ctrl.Check(idx)
                    idx = idx+1
                for column_name in header_row:
                    if main_frame.multipledatasets_mode:
                        self.dataset_field_ctrl.Append(column_name)
                    self.id_field_ctrl.Append(column_name)
                    self.url_field_ctrl.Append(column_name)
                    self.datetime_field_ctrl.Append(column_name)
                    self.metadata_fields_ctrl.Append("csv."+column_name)
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
                idx = self.metadata_fields_ctrl.FindString("created_utc")
                self.metadata_fields_ctrl.Check(idx, True)

        url_field = self.url_field_ctrl.GetStringSelection()
        if url_field != "" and not main_frame.adjustable_metadata_mode:
            idx = self.metadata_fields_ctrl.FindString("id")
            self.metadata_fields_ctrl.Check(idx, False)
            idx = self.metadata_fields_ctrl.FindString("url")
            self.metadata_fields_ctrl.Check(idx, True)

        metadata_fields_list = []
        for index in self.metadata_fields_ctrl.GetCheckedItems():
            field_name = self.metadata_fields_ctrl.GetString(index)
            metadata_fields_list.append((field_name, self.avaliable_fields[field_name],))

        included_fields_list = []
        for index in self.included_fields_ctrl.GetCheckedItems():
            field_name = self.included_fields_ctrl.GetString(index)
            included_fields_list.append((field_name, self.avaliable_fields[field_name],))
            if not main_frame.adjustable_metadata_mode:
                if (field_name, self.avaliable_fields[field_name],) not in metadata_fields_list:
                    metadata_fields_list.append((field_name, self.avaliable_fields[field_name],))

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
                                                                               list(self.avaliable_fields.items()), metadata_fields_list, included_fields_list, filename)
        logger.info("Finished")