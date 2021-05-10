'''https://docs.tweepy.org/en/latest/'''
import logging
from collections import OrderedDict
import json
import datetime
import calendar
import time
import os
import tweepy

import requests

from dateutil.relativedelta import relativedelta

def DeleteFiles(query):
    logger = logging.getLogger(__name__+".FilesAvaliable["+query+"]")
    logger.info("Starting")
    path = '../Data/Twitter/'+query+'/'
    if os.path.exists(path):
        # r=root, d=directories, f = files
        for r, d, f in os.walk(path):
            for filename in f:
                os.remove(os.path.join(path+filename))
    logger.info("Finished")

def FilesAvaliable(query, start_date, end_date, prefix):
    logger = logging.getLogger(__name__+".FilesAvaliable["+query+"]["+str(start_date)+"]["+str(end_date)+"]["+prefix+"]")
    logger.info("Starting")
    start_month = start_date[0:7]
    end_month = end_date[0:7]

    dates = [start_month, end_month]
    start, end = [datetime.datetime.strptime(_, "%Y-%m") for _ in dates]

    months = list(OrderedDict(((start + datetime.timedelta(_)).strftime(r"%Y-%m"), None) for _ in range((end - start).days)).keys())
    months.append(end_month)

    files = []
    #data location
    if not os.path.exists('../Data'):
        os.makedirs('../Data')
    if not os.path.exists('../Data/Twitter'):
        os.makedirs('../Data/Twitter')    
    path = '../Data/Twitter/'+query+'/'
    if not os.path.exists(path):
        os.makedirs(path)
    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for filename in f:
            if '.json' in filename:
                files.append(os.path.join(r, filename))

    dict_monthfiles = OrderedDict()
    for month in months:
        found = False
        for f in files:
            if  prefix+month in f:
                dict_monthfiles[month] = f
                found = True
                break
        if not found:
            dict_monthfiles[month] = ""

    logger.info("Finished")
    return dict_monthfiles

def RetrieveMonth(auth, query, month, prefix):
    logger = logging.getLogger(__name__+".RetrieveMonth["+query+"]["+month+"]["+prefix+"]")
    logger.info("Starting")
    id_dict = {}
    data = []
    month_start = month
    start_dt = calendar.timegm(datetime.datetime.strptime(month_start, "%Y-%m").timetuple())
    month_end = (datetime.datetime.strptime(month, "%Y-%m")
                 + relativedelta(months=1)).strftime(r"%Y-%m")
    end_dt = calendar.timegm(datetime.datetime.strptime(month_end, "%Y-%m").timetuple())
    
    new_data = TweepyRetriever.GetTweetData(auth, start_dt, end_dt, query)
    
    if len(new_data) > 0:
        for entry in new_data:
            if entry['id'] not in id_dict:
                if 'retrieved_utc' in entry:
                    id_dict[entry['id']] = entry['retrieved_utc']
                elif 'retrieved_on' in entry:
                    id_dict[entry['id']] = entry['retrieved_on']
                else:
                    id_dict[entry['id']] = 0
                data.append(entry)
            else:
                logger.warning("Duplicate Entry found for month[%s] id[%s] old_retrieved_on[%s] new_retrieved_on[%s] keeping newest entry",
                             str(month), str(entry['id']), str(id_dict[entry['id']]), str(entry['retrieved_on']))
                if str(id_dict[entry['id']]) <= str(entry['retrieved_on']):
                    for existing_entry in data:
                        if existing_entry['id'] == entry['id']:
                            data.remove(existing_entry)
                            del id_dict[entry['id']]
                            id_dict[entry['id']] = entry['retrieved_on']
                            data.append(entry)
                            break
        data.insert(0, id_dict)
        with open('../Data/Twitter/'+query+'/'+prefix+month+'.json', 'w') as outfile:
            json.dump(data, outfile)
    logger.info("Finished")

def UpdateRetrievedMonth(auth, query, month, file, prefix):
    logger = logging.getLogger(__name__+".UpdateRetrievedMonth["+query+"]["+month+"]["+prefix+"]")
    logger.info("Starting")
    data = []
    new_data = []
    with open(file, 'r') as infile:
        data = json.load(infile)
        id_dict = data.pop(0)
    if len(data) > 0:
        start_dt = data[len(data)-1]['created_utc'] # TODO: created_utc?
        month_end = (datetime.datetime.strptime(month, "%Y-%m")
                     + relativedelta(months=1)).strftime(r"%Y-%m") + "-01"
        end_dt = calendar.timegm(datetime.datetime.strptime(month_end, "%Y-%m-%d").timetuple())
    else:
        last_id = None
        month_start = (datetime.datetime.strptime(month, "%Y-%m")).strftime(r"%Y-%m") + "-01"
        start_dt = calendar.timegm(datetime.datetime.strptime(month_start, "%Y-%m-%d").timetuple())
        month_end = (datetime.datetime.strptime(month, "%Y-%m")
                     + relativedelta(months=1)).strftime(r"%Y-%m") + "-01"
        end_dt = calendar.timegm(datetime.datetime.strptime(month_end, "%Y-%m-%d").timetuple())

    new_data = TweepyRetriever.GetTweetData(auth, start_dt, end_dt, query)

    if len(new_data) > 0:
        for entry in new_data:
            if entry['id'] not in id_dict:
                if 'retrieved_utc' in entry:
                    id_dict[entry['id']] = entry['retrieved_utc']
                elif 'retrieved_on' in entry:
                    id_dict[entry['id']] = entry['retrieved_on']
                else:
                    id_dict[entry['id']] = 0
                data.append(entry)
            else:
                logger.warning("Duplicate Entry found for month[%s] id[%s] old_retrieved_on[%s] new_retrieved_on[%s] keeping newest entry",
                             str(month), str(entry['id']), str(id_dict[entry['id']]), str(entry['retrieved_on']))
                if str(id_dict[entry['id']]) <= str(entry['retrieved_on']):
                    for existing_entry in data:
                        if existing_entry['id'] == entry['id']:
                            data.remove(existing_entry)
                            del id_dict[entry['id']]
                            id_dict[entry['id']] = entry['retrieved_on']
                            data.append(entry)
                            break
        data.insert(0, id_dict)
        with open('../Data/Twitter/'+query+'/'+prefix+month+'.json', 'w') as outfile:
            json.dump(data, outfile)
    logger.info("Finished")

class TweepyRetriever():
    @staticmethod
    def GetTweetData(auth, start_dt, end_dt, query):
        logger = logging.getLogger(__name__+".TwitterRetriever.GetTweetData["+str(start_dt)+"]["+str(end_dt)+"]["+query+"]")
        logger.info("Starting")
        
        api = tweepy.API(auth)
        start_dt = start_dt
        tweets = []

        # TODO: v1.1 search only goes back 7 days back from the end_dt
        # need to loop end_dt until we reach start date + account for the few days before the start_dt included in the earliest 7-day interval
        # 450 requests/15 mins == 64 weeks of data/15 mins, not ideal?
        start = start_dt
        end = end_dt

        while (start < end):
            tweets_data = tweepy.Cursor(api.search, query, until=end).items()
            for tweet in tweets_data:
                tweet._json['created_utc'] = calendar.timegm(datetime.datetime.strptime(tweet._json['created_at'], "%a %b %d %H:%M:%S +0000 %Y").timetuple()) # TODO: is making a created_utc field like this ok
                tweet._json['retrieved_on'] = calendar.timegm(datetime.datetime.now().timetuple())
                if (tweet._json['created_utc'] >= start and tweet._json['created_utc'] < end):
                    tweets.append(tweet._json)
                    #print(tweet._json) #TODO: remove

            # TODO: remove
            #print(datetime.datetime.utcfromtimestamp(start))
            #print(datetime.datetime.utcfromtimestamp(end))
            end = calendar.timegm((datetime.datetime.utcfromtimestamp(end) - relativedelta(weeks=1)).timetuple())

        logger.info("Finished %s tweets have added to list", str(len(tweets)))
        return tweets

        
