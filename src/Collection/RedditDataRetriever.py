'''https://medium.com/@RareLoot/using-pushshifts-api-to-extract-reddit-submissions-fb517b286563
any class from this code must NEVER be run in multiple threads or processes to avoid flooding
the pushshift or reddit api and being blocked with an error'''
import logging
from collections import OrderedDict
import json
import datetime
import calendar
import time
import os
import requests
from dateutil.relativedelta import relativedelta

import Common.Constants as Constants

def DeleteFiles(sub):
    logger = logging.getLogger(__name__+".FilesAvailable["+sub+"]")
    logger.info("Starting")
    path = os.path.join(Constants.DATA_PATH, 'Reddit', sub)
    if os.path.exists(path):
        # r=root, d=directories, f = files
        for r, d, f in os.walk(path):
            for filename in f:
                os.remove(os.path.join(path, filename))
    logger.info("Finished")

def FilesAvailable(sub, start_date, end_date, prefix):
    logger = logging.getLogger(__name__+".FilesAvailable["+sub+"]["+str(start_date)+"]["+str(end_date)+"]["+prefix+"]")
    logger.info("Starting")
    start_month = start_date[0:7]
    end_month = end_date[0:7]

    dates = [start_month, end_month]
    start, end = [datetime.datetime.strptime(_, "%Y-%m") for _ in dates]

    months = list(OrderedDict(((start + datetime.timedelta(_)).strftime(r"%Y-%m"), None) for _ in range((end - start).days)).keys())
    months.append(end_month)

    files = []
    #data location
    path = os.path.join(Constants.DATA_PATH, 'Reddit')
    if not os.path.exists(path):
        os.makedirs(path)    
    path = os.path.join(Constants.DATA_PATH, 'Reddit', sub)
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

def RetrieveMonth(sub, month, prefix):
    logger = logging.getLogger(__name__+".RetrieveMonth["+sub+"]["+month+"]["+prefix+"]")
    logger.info("Starting")
    id_dict = {}
    data = []
    month_start = month
    start_dt = calendar.timegm(datetime.datetime.strptime(month_start, "%Y-%m").timetuple())
    month_end = (datetime.datetime.strptime(month, "%Y-%m")
                 + relativedelta(months=1)).strftime(r"%Y-%m")
    end_dt = calendar.timegm(datetime.datetime.strptime(month_end, "%Y-%m").timetuple())
    if prefix == "RS_":
        new_data, status = PushshiftRetriever.GetSubmissionData(start_dt, end_dt, sub)
    else:
        new_data, status = PushshiftRetriever.GetCommentData(start_dt, end_dt, sub)
    
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
        file_path = os.path.join(Constants.DATA_PATH, 'Reddit', sub, prefix+month+'.json')
        with open(file_path, 'w') as outfile:
            json.dump(data, outfile)
    if status != 0:
        logger.error("Retrieval of sub[%s], file[%s] was incomplete.", sub, month+prefix)
        raise RuntimeError("Incomplete Retrieval")
    logger.info("Finished")

def UpdateRetrievedMonth(sub, month, file, prefix):
    logger = logging.getLogger(__name__+".UpdateRetrievedMonth["+sub+"]["+month+"]["+prefix+"]")
    logger.info("Starting")
    data = []
    new_data = []
    with open(file, 'r') as infile:
        data = json.load(infile)
        id_dict = data.pop(0)
    if len(data) > 0:
        start_dt = data[len(data)-1]['created_utc']
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
    if prefix == "RS_":
        new_data, status = PushshiftRetriever.GetSubmissionData(start_dt, end_dt, sub)
    else:
        new_data, status = PushshiftRetriever.GetCommentData(start_dt, end_dt, sub)

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
                        if existing_entry['id'] == entry[id]:
                            data.remove(existing_entry)
                            del id_dict[entry['id']]
                            id_dict[entry['id']] = entry['retrieved_on']
                            data.append(entry)
                            break
        data.insert(0, id_dict)
        file_path = os.path.join(Constants.DATA_PATH, 'Reddit', sub, prefix+month+'.json')
        with open(file_path, 'w') as outfile:
            json.dump(data, outfile)
    if status != 0:
        logger.error("Retrieval of sub[%s], file[%s] was incomplete.", sub, month+prefix)
        raise RuntimeError("Incomplete Retrieval")
    logger.info("Finished")

class PushshiftRetriever():
    @staticmethod
    def SendDataRequest(url):
        logger = logging.getLogger(__name__+".PushshiftRetriever.SendDataRequest["+str(url)+"]")
        #used to throttle and avoid ddosing pushshift
        min_seconds_per_request = 1
        retry = 0
        try:
            while(retry < 3):
                req = requests.get(url)
                time.sleep(min_seconds_per_request)
                if req.status_code == 200:
                    data = json.loads(req.text)['data']
                    break
                else:
                    retry += 1
            if retry == 3:
                logger.error("unexpected status code returned[%s]", req.status_code)
                raise RuntimeError("Retrieval Failed")
        except requests.exceptions.ConnectionError:
            logger.error("Connection Failure")
            raise RuntimeError("Retrieval Failed")
        return data

    @staticmethod
    def GetSubmissionData(start_dt, end_dt, sub):
        logger = logging.getLogger(__name__+".PushshiftRetriever.GetSubmissionData["+str(start_dt)+"]["+str(end_dt)+"]["+sub+"]")
        logger.info("Starting")
        submissions = []
        start_dt = start_dt
        status = 0
        try:
            # Will run until all submissions have been gathered
            # from the 'after' date up until before date
            url = 'https://api.pushshift.io/reddit/search/submission/?size=500&after=' + str(start_dt) + '&before=' + str(end_dt) + '&subreddit=' + str(sub)
            submission_data = PushshiftRetriever.SendDataRequest(url)
            while len(submission_data) > 0:
                submissions = submissions+submission_data
                # Calls getPushshiftData() with the created date of the last submission
                start_dt = submission_data[-1]['created_utc']
                url = 'https://api.pushshift.io/reddit/search/submission/?size=500&after=' + str(start_dt) + '&before=' + str(end_dt) + '&subreddit=' + str(sub)
                submission_data = PushshiftRetriever.SendDataRequest(url)
            logger.info("Finished %s submissions have added to list", str(len(submissions)))
        except RuntimeError:
            status = 1
            logger.info("Due to Error canceled operation. only %s submissions have added to list", str(len(submissions)))
        return submissions, status

    @staticmethod
    def GetCommentData(start_dt, end_dt, sub):
        logger = logging.getLogger(__name__+".PushshiftRetriever.GetCommentData["+str(start_dt)+"]["+str(end_dt)+"]["+sub+"]")
        logger.info("Starting")
        comments = []
        start_dt = start_dt
        status = 0
        try:
            # Will run until all comments have been gathered
            # from the 'after' date up until before date
            url = 'https://api.pushshift.io/reddit/search/comment/?size=500&after=' + str(start_dt) + '&before=' + str(end_dt) + '&subreddit=' + str(sub)
            comment_data = PushshiftRetriever.SendDataRequest(url)
            while len(comment_data) > 0:
                comments = comments+comment_data
                # Calls getPushshiftData() with the created date of the last submission
                start_dt = comment_data[-1]['created_utc']
                url = 'https://api.pushshift.io/reddit/search/comment/?size=500&after=' + str(start_dt) + '&before=' + str(end_dt) + '&subreddit=' + str(sub)
                comment_data = PushshiftRetriever.SendDataRequest(url)
            logger.info("Finished %s comments have added to list", str(len(comments)))
        except RuntimeError:
            status = 1
            logger.info("Due to Error canceled operation. only %s comments have added to list", str(len(comments)))
        return comments, status

        
