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

def DeleteFiles(name):
    logger = logging.getLogger(__name__+".FilesAvaliable["+name+"]")
    logger.info("Starting")
    path = '../Data/Twitter/'+name+'/'
    if os.path.exists(path):
        # r=root, d=directories, f = files
        for r, d, f in os.walk(path):
            for filename in f:
                os.remove(os.path.join(path+filename))
    logger.info("Finished")

def FilesAvaliable(name, start_date, end_date, prefix):
    logger = logging.getLogger(__name__+".FilesAvaliable["+name+"]["+str(start_date)+"]["+str(end_date)+"]["+prefix+"]")
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
    path = '../Data/Twitter/'+name+'/'
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

def RetrieveMonth(auth, name, query, month, end_date, prefix):
    logger = logging.getLogger(__name__+".RetrieveMonth["+query+"]["+month+"]["+prefix+"]")
    logger.info("Starting")
    id_dict = {}
    data = []
    month_start = month
    start_dt = calendar.timegm(datetime.datetime.strptime(month_start, "%Y-%m").timetuple())
    month_end = (datetime.datetime.strptime(month, "%Y-%m")
                 + relativedelta(months=1)).strftime(r"%Y-%m")
    end_dt = calendar.timegm(datetime.datetime.strptime(month_end, "%Y-%m").timetuple())

    end_date = calendar.timegm((datetime.datetime.strptime(end_date, "%Y-%m-%d") + relativedelta(days=1)).timetuple())
    if end_date < end_dt:
        # twitter data gets cut off after a limit is hit
        # so we don't want to hit this limit while retrieving unecessary tweets past the specified time interval
        # because a "no data available" error would come up (even though data is available)
        end_dt = end_date 
    
    tweepy_data = TweepyRetriever.GetTweetData(auth, start_dt, end_dt, query)
    new_data = tweepy_data['tweets']
    rate_limit_reached = tweepy_data['rate_limit_reached']
    
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
        with open('../Data/Twitter/'+name+'/'+prefix+month+'.json', 'w') as outfile:
            json.dump(data, outfile)
    logger.info("Finished")
    return rate_limit_reached

def UpdateRetrievedMonth(auth, name, query, month, end_date, file, prefix):
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
    
    end_date = calendar.timegm((datetime.datetime.strptime(end_date, "%Y-%m-%d") + relativedelta(days=1)).timetuple())
    if end_date < end_dt:
        # twitter data gets cut off after a limit is hit
        # so we don't want to hit this limit while retrieving unecessary tweets past the specified time interval
        # because a "no data available" error would come up (even though data is available)
        end_dt = end_date 

    tweepy_data = TweepyRetriever.GetTweetData(auth, start_dt, end_dt, query)
    new_data = tweepy_data['tweets']
    rate_limit_reached = tweepy_data['rate_limit_reached']

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
        with open('../Data/Twitter/'+name+'/'+prefix+month+'.json', 'w') as outfile:
            json.dump(data, outfile)
    logger.info("Finished")
    return rate_limit_reached

class TweepyRetriever():
    @staticmethod
    def GetTweetData(auth, start_dt, end_dt, query): # where end_dt is 12 am the day after the specified end date
        logger = logging.getLogger(__name__+".TwitterRetriever.GetTweetData["+str(start_dt)+"]["+str(end_dt)+"]["+query+"]")
        logger.info("Starting")
        
        api = tweepy.API(auth)
        start_dt = start_dt
        tweets = []

        # TODO: v1.1 search only goes back 7 days back from current day
        start = start_dt
        end = end_dt

        last_retrieved_id = None
        tweets_retrieved = True
        rate_limit_reached = False

        while (start < end):
            # 100 tweets per API request, and 450 requests/15 mins (usually only hits < 300 requests before reaching API limit though)
            if last_retrieved_id == None:
                tweets_data = tweepy.Cursor(api.search, query, lang="en", until=end).items(100)
            else:
                tweets_data = tweepy.Cursor(api.search, query, lang="en", until=end, max_id=last_retrieved_id-1).items(100)
            # send requests for tweets while the rate limit has not been exceeded
            while (tweets_retrieved):
                tweets_retrieved = False
                try:
                    for tweet in tweets_data:
                        print(len(tweets)) # TODO remove
                        tweet._json['created_utc'] = calendar.timegm(datetime.datetime.strptime(tweet._json['created_at'], "%a %b %d %H:%M:%S +0000 %Y").timetuple()) # TODO: is making a created_utc field like this ok
                        tweet._json['retrieved_on'] = calendar.timegm(datetime.datetime.now().timetuple())
                        if (tweet._json['created_utc'] >= start and tweet._json['created_utc'] < end):
                            tweets.append(tweet._json)
                        last_retrieved_id = tweet._json['id']
                        tweets_retrieved = True

                    if last_retrieved_id == None:
                        tweets_data = tweepy.Cursor(api.search, query, lang="en", until=end).items(100)
                    else:
                        tweets_data = tweepy.Cursor(api.search, query, lang="en", until=end, max_id=last_retrieved_id-1).items(100)
                except tweepy.error.TweepError as e:
                    if e.response.status_code == 429:
                        print("Twitter API rate limit reached.") # TODO: remove
                        rate_limit_reached = True
                    tweets_retrieved=False
                    break

            end = calendar.timegm((datetime.datetime.utcfromtimestamp(end) - relativedelta(weeks=1)).timetuple())

        logger.info("%s tweets were retrieved.", str(len(tweets)))
        return {
            'rate_limit_reached': rate_limit_reached,
            'tweets': tweets,
        }

        
