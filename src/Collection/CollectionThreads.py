import logging
import json
import csv
import calendar
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import dateparser
from threading import Thread
import tweepy

import wx

from Common.GUIText import Datasets as GUIText
import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
import Common.Objects.Datasets as Datasets
import Common.Objects.Utilities.Datasets as DatasetsUtilities
import Collection.RedditDataRetriever as rdr
import Collection.TwitterDataRetriever as twr

class RetrieveRedditDatasetThread(Thread):
    """Retrieve Reddit Dataset Thread Class."""
    def __init__(self, notify_window, main_frame, dataset_name, subreddit, start_date, end_date, replace_archive_flg, pushshift_flg, redditapi_flg, dataset_type, avaliable_fields_list, metadata_fields_list, included_fields_list):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.main_frame = main_frame
        self.dataset_name = dataset_name
        self.dataset_type = dataset_type
        self.replace_archive_flg = replace_archive_flg
        self.pushshift_flg = pushshift_flg
        self.redditapi_flg = redditapi_flg
        self.subreddit = subreddit
        self.start_date = start_date
        self.end_date = end_date
        self.avaliable_fields_list = avaliable_fields_list
        self.metadata_fields_list = metadata_fields_list
        self.included_fields_list = included_fields_list
        self.start()
    
    def run(self):
        logger = logging.getLogger(__name__+".RetrieveRedditDatasetThread.run")
        logger.info("Starting")
        status_flag = True
        dataset_key = (self.dataset_name, "Reddit", self.dataset_type)
        retrieval_details = {
                'subreddit': self.subreddit,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'replace_archive_flg': self.replace_archive_flg,
                'pushshift_flg': self.pushshift_flg,
                'redditapi_flg': self.redditapi_flg
                }
        data = {}
        dataset = None
        error_msg = ""
        if self.replace_archive_flg:
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_REMOVE_SUBREDDIT_ARCHIVE_MSG + self.subreddit))
            rdr.DeleteFiles(self.subreddit)
        if self.dataset_type == "discussion":
            if self.pushshift_flg:
                try:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_SUBMISSIONS_MSG))
                    self.UpdateDataFiles(self.subreddit, self.start_date, self.end_date, "RS_")
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_COMMENTS_MSG))
                    self.UpdateDataFiles(self.subreddit, self.start_date, self.end_date, "RC_")
                except RuntimeError:
                    status_flag = False
                    error_msg = GUIText.RETRIEVAL_FAILED_ERROR
            if status_flag:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_SUBMISSION_MSG))
                submission_data = self.ImportDataFiles(self.subreddit, self.start_date, self.end_date, "RS_")
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_COMMENT_MSG))
                comment_data = self.ImportDataFiles(self.subreddit, self.start_date, self.end_date, "RC_")
                #convert data to discussion
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_PREPARING_DISCUSSION_MSG))
                discussion_data = {}
                for submission in submission_data:
                    key = ("Reddit", "discussion", submission['id'])
                    discussion_data[key] = {}
                    discussion_data[key]['data_source'] = "Reddit"
                    discussion_data[key]['data_type'] = "discussion"
                    discussion_data[key]['id'] = submission['id']
                    discussion_data[key]["url"] = "https://www.reddit.com/"+submission['id']
                    discussion_data[key]['created_utc'] = submission['created_utc']
                    if 'title' in submission:
                        discussion_data[key]['title'] = submission['title']
                    else:
                        discussion_data[key]['title'] = ""
                    if 'selftext' in submission:
                        discussion_data[key]['text'] = [submission['selftext']]
                    else:
                        discussion_data[key]['text'] = [""]
                    for field in submission:
                        discussion_data[key]["submission."+field] = submission[field]
                for comment in comment_data:
                    submission_id = comment['link_id'].split('_')[1]
                    key = ("Reddit", "discussion", submission_id)
                    if key in discussion_data:
                        if 'body' in comment:
                            discussion_data[key]['text'].append(comment['body'])
                        for field in comment:
                            if "comment."+field in discussion_data[key]:
                                discussion_data[key]["comment."+field].append(comment[field])
                            else:
                                discussion_data[key]["comment."+field] = [comment[field]]
                #save as a discussion dataset
                data = discussion_data
        elif self.dataset_type == "submission":
            if self.pushshift_flg:
                try:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_SUBMISSIONS_MSG))
                    self.UpdateDataFiles(self.subreddit, self.start_date, self.end_date, "RS_")
                except RuntimeError:
                    status_flag = False
                    error_msg = GUIText.RETRIEVAL_FAILED_ERROR
            if status_flag:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_SUBMISSION_MSG))
                raw_submission_data = self.ImportDataFiles(self.subreddit, self.start_date, self.end_date, "RS_")
                submission_data = {}
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_PREPARING_SUBMISSION_MSG))
                for submission in raw_submission_data:
                    key = ("Reddit", "submission", submission["id"])
                    submission_data[key] = submission
                    submission_data[key]["data_source"] = "Reddit"
                    submission_data[key]["data_type"] = "submission"
                    submission_data[key]["url"] = "https://www.reddit.com/"+submission['id']
                data = submission_data
        elif self.dataset_type == "comment":
            if self.pushshift_flg:
                try:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_COMMENTS_MSG))
                    self.UpdateDataFiles(self.subreddit, self.start_date, self.end_date, "RC_")
                except RuntimeError:
                    status_flag = False
                    error_msg = GUIText.RETRIEVAL_FAILED_ERROR
            if status_flag:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_COMMENT_MSG))
                raw_comment_data = self.ImportDataFiles(self.subreddit, self.start_date, self.end_date, "RC_")
                comment_data = {}
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_PREPARING_COMMENT_MSG))
                for comment in raw_comment_data:
                    key = ("Reddit", "comment", comment["id"])
                    comment_data[key] = comment
                    comment_data[key]["data_source"] = "Reddit"
                    comment_data[key]["data_type"] = "comment"
                    link_id = comment['link_id'].split('_')
                    comment_data[key]["submission_id"] = link_id[1]
                    comment_data[key]["url"] = "https://www.reddit.com/"+link_id[1]+"/_/"+comment['id']+"/"
                data = comment_data
        if status_flag:
            if len(data) > 0:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_CONSTRUCTING_MSG))
                dataset = DatasetsUtilities.CreateDataset(dataset_key, retrieval_details, data, self.avaliable_fields_list, self.metadata_fields_list, self.included_fields_list)
                DatasetsUtilities.TokenizeDatasetObjects([dataset], self._notify_window, self.main_frame)
            else:
                status_flag = False
                error_msg = GUIText.NO_DATA_AVALIABLE_ERROR

        #return dataset and associated information
        result = {}
        result['status_flag'] = status_flag
        result['dataset_key'] = dataset_key
        result['dataset'] = dataset
        result['error_msg'] = error_msg
        wx.PostEvent(self._notify_window, CustomEvents.RetrieveResultEvent(result))
        logger.info("Finished")

    def UpdateDataFiles(self, subreddit, start_date, end_date, prefix):
        logger = logging.getLogger(__name__+".RedditRetrieverDialog.UpdateDataFiles["+subreddit+"]["+str(start_date)+"]["+str(end_date)+"]["+prefix+"]")
        logger.info("Starting")
        #check which months of the range are already downloaded
        #data archives are by month so need which months have no data and which months are before months which have no data
        dict_monthfiles = rdr.FilesAvaliable(subreddit, start_date, end_date, prefix)
        months_notfound = []
        months_tocheck = []
        errors = []
        for month, filename in dict_monthfiles.items():
            if filename == "":
                months_notfound.append(month)
            else:
                months_tocheck.append(month)
        #retireve data of months that have not been downloaded
        for month in months_notfound:
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_ALL_MSG+str(month)))
            try:
                rdr.RetrieveMonth(subreddit, month, prefix)
            except RuntimeError as error:
                errors.append(error)
        #check the exiting months of data for any missing data
        for month in months_tocheck:
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_NEW_MSG+str(month)))
            try:
                rdr.UpdateRetrievedMonth(subreddit, month, dict_monthfiles[month], prefix)
            except RuntimeError as error:
                errors.append(error)
        if len(errors) != 0:
            raise RuntimeError(str(len(errors)) + " Retrievals Failed")
        logger.info("Finished")

    def ImportDataFiles(self, subreddit, start_date, end_date, prefix):
        logger = logging.getLogger(__name__+".RedditRetrieverDialog.ImportDataFiles["+subreddit+"]["+str(start_date)+"]["+str(end_date)+"]["+prefix+"]")
        logger.info("Starting")
        #get names of files where data is to be loaded from
        dict_monthfiles = rdr.FilesAvaliable(subreddit, start_date, end_date, prefix)
        files = []
        for filename in dict_monthfiles.values():
            if filename != "":
                files.append(filename)
        data = []
        if len(files) != 0:
            if len(files) > 1:
                #retrieve only needed data from first file
                with open(files[0], 'r') as infile:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(files[0])))
                    temp_data = json.load(infile)
                    temp_data.pop(0)
                    for entry in temp_data:
                        if entry['created_utc'] >= calendar.timegm((datetime.strptime(start_date,
                                                                    "%Y-%m-%d")).timetuple()):
                            data.append(entry)
                if len(files) > 2:
                    #retrieve all data from middle files
                    for filename in files[1:(len(files)-2)]:
                        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(filename)))
                        with open(filename, 'r') as infile:
                            new_data = json.load(infile)
                            new_data.pop(0)
                            data = data + new_data

                #retrieve only needed data from last file
                with open(files[(len(files)-1)], 'r') as infile:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(files[(len(files)-1)])))
                    temp_data = json.load(infile)
                    temp_data.pop(0)
                    for entry in temp_data:
                        if entry['created_utc'] < calendar.timegm((datetime.strptime(end_date,
                                                                   "%Y-%m-%d") + relativedelta(days=1)).timetuple()):
                            data.append(entry)
            else:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(files[0])))
                with open(files[0], 'r') as infile:
                    temp_data = json.load(infile)
                    temp_data.pop(0)
                    for entry in temp_data:
                        if entry['created_utc'] >= calendar.timegm((datetime.strptime(start_date,
                                                                    "%Y-%m-%d")).timetuple()):
                            if entry['created_utc'] < calendar.timegm((datetime.strptime(end_date,
                                                                       "%Y-%m-%d") + relativedelta(days=1)).timetuple()):
                                data.append(entry)
        logger.info("Finished")
        return data

class RetrieveTwitterDatasetThread(Thread):
    """Retrieve Reddit Dataset Thread Class."""
    def __init__(self, notify_window, main_frame, dataset_name, keys, query, start_date, end_date, dataset_type, avaliable_fields_list, metadata_fields_list, included_fields_list):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self.main_frame = main_frame
        self.dataset_name = dataset_name
        self.consumer_key = keys['consumer_key']
        self.consumer_secret = keys['consumer_secret']
        self.query = query
        self.start_date = start_date
        self.end_date = end_date
        self.dataset_type = dataset_type
        self.avaliable_fields_list = avaliable_fields_list
        self.metadata_fields_list = metadata_fields_list
        self.included_fields_list = included_fields_list
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()
    
    def run(self):
        logger = logging.getLogger(__name__+".RetrieveTwitterDatasetThread.run")
        logger.info("Starting")
        status_flag = True
        dataset_key = (self.dataset_name, "Twitter", self.dataset_type)
        retrieval_details = {
                'query': self.query,
                'start_date': self.start_date,
                'end_date': self.end_date,
                }
        data = {}
        dataset = None
        error_msg = ""

        # tweepy auth
        # TODO: user-level auth
        consumer_key = self.consumer_key
        consumer_secret = self.consumer_secret
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        api = tweepy.API(auth) # TODO: create auth object in dialog and just pass in auth object

        if self.dataset_type == "tweet":
            # TODO: only update if called with twitter api flag? otherwise just import instead (like with reddit)
            if True: # twitter_api_flag
                try:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_TWITTER_TWEETS_MSG))
                    self.UpdateDataFiles(auth, self.dataset_name, self.query, self.start_date, self.end_date, "TW_") #TODO: TW == twitter, maybe TD? Twitter Document?
                except RuntimeError:
                    status_flag = False
                    error_msg = GUIText.RETRIEVAL_FAILED_ERROR
            if status_flag:
                # wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BEGINNING_MSG))

                # # TODO: get data from files?
                # tweets = tweepy.Cursor(api.search, self.query).items(10)

                # wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_PREPARING_TWITTER_MSG))

                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_TWITTER_TWEET_MSG))
                tweets = self.ImportDataFiles(self.dataset_name, self.query, self.start_date, self.end_date, "TW_")
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_PREPARING_TWITTER_MSG))
                
                tweets_data = {}
                for tweet in tweets:
                    key = ("Twitter", "tweet", tweet['id'])
                    tweets_data[key] = {}
                    tweets_data[key]['data_source'] = "Twitter"
                    tweets_data[key]['data_type'] = "tweet"
                    tweets_data[key]['id'] = tweet['id']
                    tweets_data[key]["url"] = "https://twitter.com/" + tweet['user']['screen_name'] + "/status/" + tweet['id_str']
                    tweets_data[key]['created_utc'] = tweet['created_utc']
                    # TODO: is 'title' needed if tweets don't have titles?
                    if 'title' in tweet:
                        tweets_data[key]['title'] = tweet['title']
                    else:
                        tweets_data[key]['title'] = ""
                    if 'text' in tweet:
                        tweets_data[key]['text'] = [tweet['text']]
                    else:
                        tweets_data[key]['text'] = [""]

                    # tweet always has shortened 'text', but we should use 'full_text' if possible
                    status = None
                    try:
                        status_attempt = api.get_status(tweet['id'], tweet_mode="extended")
                        status = status_attempt
                    except tweepy.error.TweepError: # Could not retrieve status for this tweet id, so use shortened 'text'(?) TODO
                        tweets_data[key]['full_text'] = [tweet['text']]
                    if status is not None:
                        try: 
                            tweets_data[key]['full_text'] = [status.retweeted_status.full_text]
                        except AttributeError:  # Not a Retweet (no 'retweeted_status' field)
                            tweets_data[key]['full_text'] = [status.full_text]
                    
                    for field in tweet:
                        tweets_data[key]["tweet."+field] = tweet[field]
                #save as a document dataset
                data = tweets_data           
        
        if status_flag:
            if len(data) > 0:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_CONSTRUCTING_MSG))
                dataset = DatasetsUtilities.CreateDataset(dataset_key, retrieval_details, data, self.avaliable_fields_list, self.metadata_fields_list, self.included_fields_list)
                DatasetsUtilities.TokenizeDatasetObjects([dataset], self._notify_window, self.main_frame)
            else:
                status_flag = False
                error_msg = GUIText.NO_DATA_AVALIABLE_ERROR

        #return dataset and associated information
        result = {}
        result['status_flag'] = status_flag
        result['dataset_key'] = dataset_key
        result['dataset'] = dataset
        result['error_msg'] = error_msg
        wx.PostEvent(self._notify_window, CustomEvents.RetrieveResultEvent(result))
        logger.info("Finished")

    def UpdateDataFiles(self, auth, name, query, start_date, end_date, prefix):
        logger = logging.getLogger(__name__+".TwitterRetrieverDialog.UpdateDataFiles["+name+"]["+str(start_date)+"]["+str(end_date)+"]["+prefix+"]")
        logger.info("Starting")
        #check which months of the range are already downloaded
        #data archives are by month so need which months have no data and which months are before months which have no data
        dict_monthfiles = twr.FilesAvaliable(name, start_date, end_date, prefix)
        months_notfound = []
        months_tocheck = []
        errors = []
        for month, filename in dict_monthfiles.items():
            if filename == "":
                months_notfound.append(month)
            else:
                months_tocheck.append(month)
        
        rate_limit_reached = False
        #retireve data of months that have not been downloaded
        for month in months_notfound:
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_ALL_MSG+str(month)))
            try:
                rate_limit_reached = twr.RetrieveMonth(auth, name, query, month, end_date, prefix)
                if rate_limit_reached:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.TWITTER_RATE_LIMIT_REACHED_MSG))
                    break
            except RuntimeError as error:
                errors.append(error)
        #check the exiting months of data for any missing data
        for month in months_tocheck:
            wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_DOWNLOADING_NEW_MSG+str(month)))
            try:
                rate_limit_reached = twr.UpdateRetrievedMonth(auth, name, query, month, end_date, dict_monthfiles[month], prefix)
                if rate_limit_reached:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.TWITTER_RATE_LIMIT_REACHED_MSG))
                    break
            except RuntimeError as error:
                errors.append(error)
        if len(errors) != 0:
            raise RuntimeError(str(len(errors)) + " Retrievals Failed")
        logger.info("Finished")

    def ImportDataFiles(self, name, query, start_date, end_date, prefix):
        logger = logging.getLogger(__name__+".TwitterRetrieverDialog.ImportDataFiles["+name+"]["+str(start_date)+"]["+str(end_date)+"]["+prefix+"]")
        logger.info("Starting")
        #get names of files where data is to be loaded from
        dict_monthfiles = twr.FilesAvaliable(name, start_date, end_date, prefix)
        files = []
        for filename in dict_monthfiles.values():
            if filename != "":
                files.append(filename)
        data = []
        if len(files) != 0:
            if len(files) > 1:
                #retrieve only needed data from first file
                with open(files[0], 'r') as infile:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(files[0])))
                    temp_data = json.load(infile)
                    temp_data.pop(0)
                    for entry in temp_data:
                        if entry['created_utc'] >= calendar.timegm((datetime.strptime(start_date, "%Y-%m-%d")).timetuple()):
                                data.append(entry)
                if len(files) > 2:
                    #retrieve all data from middle files
                    for filename in files[1:(len(files)-2)]:
                        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(filename)))
                        with open(filename, 'r') as infile:
                            new_data = json.load(infile)
                            new_data.pop(0)
                            data = data + new_data

                #retrieve only needed data from last file
                with open(files[(len(files)-1)], 'r') as infile:
                    wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(files[(len(files)-1)])))
                    temp_data = json.load(infile)
                    temp_data.pop(0)
                    for entry in temp_data:
                        if entry['created_utc'] < calendar.timegm((datetime.strptime(end_date, "%Y-%m-%d") + relativedelta(days=1)).timetuple()):
                            data.append(entry)
            else:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG+str(files[0])))
                with open(files[0], 'r') as infile:
                    temp_data = json.load(infile)
                    temp_data.pop(0)
                    for entry in temp_data:
                        if entry['created_utc'] >= calendar.timegm((datetime.strptime(start_date, "%Y-%m-%d")).timetuple()):
                            if (entry['created_utc'] < calendar.timegm((datetime.strptime(end_date,"%Y-%m-%d") + relativedelta(days=1)).timetuple())):
                                data.append(entry)
        logger.info("Finished")
        return data

class RetrieveCSVDatasetThread(Thread):
    """Retrieve CSV Dataset Thread Class."""
    def __init__(self, notify_window, main_frame, dataset_name, dataset_field, dataset_type, id_field, url_field, datetime_field, datetime_tz, avaliable_fields_list, metadata_fields_list, included_fields_list, combined_fields_list, filename):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.daemon = True
        self._notify_window = notify_window
        self.main_frame = main_frame
        self.dataset_name = dataset_name
        self.dataset_field = dataset_field
        self.dataset_type = dataset_type
        self.id_field = id_field
        self.url_field = url_field
        self.datetime_field = datetime_field
        self.datetime_tz = datetime_tz
        self.avaliable_fields_list = avaliable_fields_list
        self.metadata_fields_list = metadata_fields_list
        self.included_fields_list = included_fields_list
        self.combined_fields_list = combined_fields_list

        self.filename = filename
        self.start()
    
    def run(self):
        logger = logging.getLogger(__name__+".RetrieveCSVDatasetThread.run")
        logger.info("Starting")
        retrieval_details = {
                'filename': self.filename
                }
        data = {}
        dataset = None
        datasets = {}
        error_msg = ""
        status_flag = True
        
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_IMPORTING_FILE_MSG + self.filename))
        file_data = self.ImportDataFiles(self.filename)
        #convert the data into toolkit's dataset format
        wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_PREPARING_CSV_MSG))

        if self.dataset_field == "":
            dataset_key = (self.dataset_name, "CSV", self.dataset_type)
            
            row_num = 1
            for row in file_data:
                if self.id_field in row:
                    document_id = row[self.id_field]
                else:
                    document_id = row_num
                key = ("CSV", "document", document_id)
                if key not in data:
                    data[key] = {}
                    data[key]['data_source'] = 'CSV'
                    data[key]['data_type'] = 'document'
                    data[key]['id'] = document_id
                    if self.url_field == "":
                        data[key]['url'] = ""
                    else:
                        data[key]['url'] = row[self.url_field]
                    if self.datetime_field == "":
                        data[key]['created_utc'] = 0
                    else:
                        datetime_value = row[self.datetime_field]
                        if datetime_value != '':
                            datetime_obj = dateparser.parse(datetime_value, settings={'TIMEZONE': self.datetime_tz})
                            if datetime_obj != None:
                                datetime_obj = datetime_obj.astimezone(timezone.utc)
                                datetime_utc = datetime_obj.replace(tzinfo=timezone.utc).timestamp()
                                data[key]['created_utc'] = datetime_utc
                            else:
                                data[key]['created_utc'] = 0
                        else:
                            data[key]['created_utc'] = 0
                for field in row:
                    field_name = "csv."+field
                    if field_name in data[key]:
                        if field_name in self.combined_fields_list:
                            data[key][field_name].append(row[field])
                    else:
                        if field_name in self.combined_fields_list:
                            data[key][field_name] = [row[field]]
                        else:
                            data[key][field_name] = row[field]
                row_num = row_num + 1
            #save as a document dataset
            if len(data) > 0:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_CONSTRUCTING_MSG))
                dataset = DatasetsUtilities.CreateDataset(dataset_key, retrieval_details, data, self.avaliable_fields_list, self.metadata_fields_list, self.included_fields_list)
                DatasetsUtilities.TokenizeDatasetObjects([dataset], self._notify_window, self.main_frame)
            else:
                status_flag = False
                error_msg = GUIText.NO_DATA_AVALIABLE_ERROR
        else:
            new_dataset_key = []
            row_num = 1 
            for row in file_data:
                new_dataset_key = (self.dataset_name, "CSV", row[self.dataset_field])
                if new_dataset_key not in data:
                    data[new_dataset_key] = {}

                if self.id_field in row:
                    document_id = row[self.id_field]
                else:
                    document_id = row_num
                key = ("CSV", row[self.dataset_field], document_id)
                if key not in data[new_dataset_key]:
                    data[new_dataset_key][key] = {}
                    data[new_dataset_key][key]['data_source'] = 'CSV'
                    data[new_dataset_key][key]['data_type'] = row[self.dataset_field]
                    data[new_dataset_key][key]['id'] = document_id
                    if self.url_field == "":
                        data[new_dataset_key][key]['url'] = ""
                    else:
                        data[new_dataset_key][key]['url'] = row[self.url_field]
                    if self.datetime_field == "":
                        data[new_dataset_key][key]['created_utc'] = 0
                    else:
                        datetime_value = row[self.datetime_field]
                        if datetime_value != '':
                            datetime_obj = dateparser.parse(datetime_value, settings={'TIMEZONE': self.datetime_tz})
                            if datetime_obj != None:
                                datetime_obj = datetime_obj.astimezone(timezone.utc)
                                datetime_utc = datetime_obj.replace(tzinfo=timezone.utc).timestamp()
                                data[new_dataset_key][key]['created_utc'] = datetime_utc
                            else:
                                data[new_dataset_key][key]['created_utc'] = 0
                        else:
                            data[new_dataset_key][key]['created_utc'] = 0
                    for field in row:
                        data[new_dataset_key][key]["csv."+field] = [row[field]]
                else:
                    for field in row:
                        if "csv."+field in data[new_dataset_key][key]:
                            data[new_dataset_key][key]["csv."+field].append(row[field])
                        else:
                            data[new_dataset_key][key]["csv."+field] = [row[field]]
                row_num = row_num + 1
            #save as a document dataset
            if len(data) > 0:
                wx.PostEvent(self._notify_window, CustomEvents.ProgressEvent(GUIText.RETRIEVING_BUSY_CONSTRUCTING_MSG))
                for new_dataset_key in data:
                    datasets[new_dataset_key] = DatasetsUtilities.CreateDataset(new_dataset_key, retrieval_details, data[new_dataset_key], self.avaliable_fields_list, self.metadata_fields_list, self.included_fields_list)
                    DatasetsUtilities.TokenizeDatasetObjects([datasets[new_dataset_key]], self._notify_window, self.main_frame)
            else:
                status_flag = False
                error_msg = GUIText.NO_DATA_AVALIABLE_ERROR

        #return dataset and associated information
        result = {}
        result['status_flag'] = status_flag
        if dataset is not None:
            result['dataset_key'] = dataset_key
            result['dataset'] = dataset
        else:
            result['datasets'] = datasets
        result['error_msg'] = error_msg
        wx.PostEvent(self._notify_window, CustomEvents.RetrieveResultEvent(result))
        logger.info("Finished")

    def ImportDataFiles(self, filename):
        logger = logging.getLogger(__name__+".RetrieveCSVDatasetThread.ImportDataFiles["+filename+"]")
        logger.info("Starting")

        file_data = []
        with open(filename, mode='r') as infile:
            reader = csv.reader(infile)
            header_row = next(reader)
            for row in reader:
                data_row = {header_row[i]: row[i] for i in range(len(header_row))}
                file_data.append(data_row)

        logger.info("Finished")
        return file_data