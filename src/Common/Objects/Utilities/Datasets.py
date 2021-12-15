import logging
from datetime import datetime, timedelta

import spacy
import en_core_web_sm
import fr_core_news_sm
import nltk

import wx

import Common.Constants as Constants
import Common.CustomEvents as CustomEvents
import Common.Objects.Datasets as Datasets
import Common.Database as Database
from Common.GUIText import Datasets as GUIText
from Common.GUIText import Filtering as GUITextFiltering

def CreateDataset(dataset_name, dataset_source, dataset_type, language, retrieval_details, data, available_fields_list, label_fields, computational_fields, main_frame):
    dataset = Datasets.Dataset(name=dataset_name,
                               dataset_source=dataset_source,
                               dataset_type=dataset_type,
                               language=language,
                               retrieval_details=retrieval_details)

    db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
    
    db_conn.InsertDataset(dataset.key, 'text')

    dataset.data = data
    
    db_conn.InsertDocuments(dataset.key, dataset.data.keys())
    
    for field_name, field_info in available_fields_list:
        new_field = Datasets.Field(dataset,
                                   field_name,
                                   dataset,
                                   field_info['desc'],
                                   field_info['type'])
        dataset.available_fields[new_field.key] = new_field
    for field_name, field_info in label_fields:
        for field in dataset.available_fields.values():
            if field.name == field_name:
                found_field = field
                break
        dataset.label_fields[found_field.key] = found_field
    for field_name, field_info in computational_fields:
        for field in dataset.available_fields.values():
            if field.name == field_name:
                found_field = field
                break
        dataset.computational_fields[found_field.key] = found_field
    return dataset

def TokenizeDataset(dataset, notify_window, main_frame, rerun=False, tfidf_update=False):
    logger = logging.getLogger(__name__+".TokenizeDataset")
    logger.info("Starting")
    main_frame = main_frame
    db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)

    def TokenizationController(field, field_data):
        logger.info("Preparing Processes for %s, %s, for %s documents", repr(dataset), repr(field), str(len(field_data)))
        nonlocal main_frame
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'msg':GUIText.TOKENIZING_BUSY_STARTING_FIELD_MSG+str(field.name)}))
        results = []

        total = len(field_data)
        full_data_list = list(field_data.items())
        split_data_lists = []
        if total > main_frame.pool_num*2:
            increment = int(total/(main_frame.pool_num*2))
            start = 0
            end = increment
            for i in range(main_frame.pool_num*2-1):
                split_data_lists.append(full_data_list[start:end])
                start = end
                end = end+increment
            split_data_lists.append(full_data_list[start:])
        else:
            split_data_lists.append(full_data_list)
        
        count = 0
        for data_list in split_data_lists:
            logger.info("Creating TokenizationWorker for Documents %s - %s", str(count+1), str(count+len(data_list)))
            res = main_frame.pool.apply_async(TokenizationWorker, (data_list, 
                                                                   repr(field),
                                                                   str(count+1)+"-"+str(count+len(data_list)-1),
                                                                   field.parent.language))
            results.append(res)
            count = count+len(data_list)
        
        completed = 0
        start_time = datetime.now()
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'msg':GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
                                                               +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG2+str(len(results))\
                                                               +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG3+str(field.name)}))
        if not db_conn.CheckIfFieldExists(dataset.key, field.key):
            db_conn.InsertField(dataset.key, field.key)
        res_count = 0
        for res in results:
            res_count += 1
            new_tokensets = res.get()[0]
            package_versions = res.get()[1]
            #insert documents' tokens into database
            db_conn.InsertStringTokens(dataset.key, field.key, new_tokensets)
            completed += 1
            logger.info("%s %s", repr(field), completed)
            wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'msg':GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
                                                                   +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG2+str(len(results))\
                                                                   +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG3+str(field.name)}))

            current_time = datetime.now()
            if res_count < len(results)/2:
                new_estimated_loop_time = (current_time - start_time)*2
            else:
                new_estimated_loop_time = (current_time - start_time)
            nonlocal estimated_loop_time, field_count, remaining_field_count
            if estimated_loop_time < new_estimated_loop_time:
                estimated_loop_time = new_estimated_loop_time
                elapsed_time = current_time - start_time
                if res_count < len(results)/2:
                    estimated_remaining_sec = estimated_loop_time.total_seconds() * (remaining_field_count-0.5)
                else:
                    estimated_remaining_sec = estimated_loop_time.total_seconds() * (remaining_field_count-1)
                estimated_remaining_time = timedelta(seconds=estimated_remaining_sec)
                wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'estimated_time':elapsed_time + estimated_remaining_time}))
        dataset.tokenization_package_versions = package_versions

    def FieldTokenizer(field):
        loop_start_time = datetime.now()
        id_key_fields = ["data_source", "data_type", "id"]
        field_data = {}
        for data in field.dataset.data.values():
            id_key = tuple(data[id_key_field] for id_key_field in id_key_fields)
            if id_key not in field_data:
                if field.name in data:
                    if isinstance(data[field.name], str):
                        field_data[id_key] = [data[field.name]]
                    else:
                        field_data[id_key] = data[field.name]
                else:
                    field_data[id_key] = [""]
            else:
                if field.name in data:
                    if isinstance(data[field.name], str):
                        field_data[id_key].append(data[field.name])
                    else:
                        field_data[id_key].extend(data[field.name])
                else:
                    field_data[id_key].append("")
        if field.fieldtype == "string":
            TokenizationController(field, field_data)
        else:
            field.tokenset = field_data
        new_estimated_loop_time = (datetime.now() - loop_start_time)
        nonlocal estimated_loop_time, field_count, remaining_field_count, start_time
        remaining_field_count -= 1
        if estimated_loop_time == None or estimated_loop_time < new_estimated_loop_time:
            estimated_loop_time = new_estimated_loop_time
        elapsed_time = datetime.now() - start_time
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'estimated_time':elapsed_time + (estimated_loop_time * remaining_field_count)}))

    wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'step':GUIText.TOKENIZING_BUSY_STEP}))
    field_count = len(dataset.computational_fields)
    remaining_field_count = field_count
    start_time = datetime.now()
    estimated_loop_time = timedelta()
    stringfield_count = 0
    for computational_field_key in dataset.computational_fields:
        has_data = False
        if dataset.computational_fields[computational_field_key].fieldtype == 'string':
            if rerun:
                db_conn.DeleteField(dataset.key, computational_field_key)
            else:
                has_data = db_conn.CheckIfFieldExists(dataset.key, computational_field_key)
            if not has_data:
                FieldTokenizer(dataset.computational_fields[computational_field_key])
                stringfield_count += 1
        elif dataset.computational_fields[computational_field_key].tokenset == None or rerun:
            FieldTokenizer(dataset.computational_fields[computational_field_key])

    #calculate tfidf scores for all stored string tokens if any changes occured
    if stringfield_count > 0 or tfidf_update:
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'step':GUIText.TOKENIZING_BUSY_STEP_TFIDF_STEP}))
        db_conn.UpdateStringTokensTFIDF(dataset.key)
        counts = db_conn.GetStringTokensCounts(dataset.key)
        dataset.total_docs = counts['documents']
        dataset.total_tokens = counts['tokens']
        dataset.total_uniquetokens = counts['unique_tokens']
        ApplyFilterAllRules(dataset, main_frame)
            
    logger.info("Finished")

def TokenizationWorker(data_list, field_repr, label, language):
    logger = logging.getLogger(__name__+".TokenizationWorker["+field_repr+"]["+str(label)+"]")
    logger.info("Starting")

    package_versions = []

    spacy.prefer_gpu()
    if language == 'fre-sm':
        #less accurate but faster model
        nlp = fr_core_news_sm.load()
        stemmer = nltk.stem.snowball.FrenchStemmer()
        package_versions.append(spacy.__name__+" "+spacy.__version__+" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
        package_versions.append(nltk.__name__ +" "+nltk.__version__+" snowball.FrenchStemmer")
        package_versions.append(spacy.__name__ +" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
    elif language == 'eng-sm':
        #less accurate but faster model
        nlp = en_core_web_sm.load()
        stemmer = nltk.stem.snowball.EnglishStemmer()
        package_versions.append(spacy.__name__+" "+spacy.__version__+" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
        package_versions.append(nltk.__name__ +" "+nltk.__version__+" snowball.EnglishStemmer")
        package_versions.append(spacy.__name__ +" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
    
    tokensets = {}
    for key, data in data_list:
        tokenset = []
        position = 0
        for tmp_tokens in nlp.pipe(data):
            for token in tmp_tokens:
                text = token.text.strip().lower()
                stem = stemmer.stem(token.text).strip().lower()
                lemma = token.lemma_.strip().lower()
                tokenset.append((position,
                                     text,
                                     stem,
                                     lemma,
                                     token.pos_,
                                     token.is_stop))
                position = position + 1
        tokensets[key] = tokenset

    logger.info("Finished")
    #return tokensets, rawtext_tokens_df, stem_tokens_df, lemma_tokens_df, package_versions
    return tokensets, package_versions

def ApplyFilterAllRules(dataset, main_frame):
    logger = logging.getLogger(__name__+".ApplyFilterAllRules")
    logger.info("Starting")
    db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
    wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'step':GUITextFiltering.FILTERS_APPLYING_RULES_STEP}))
    mapped_rules = []
    for field_name, word, pos, action in dataset.filter_rules:
        include = False
        if field_name != Constants.FILTER_RULE_ANY:
            for field in dataset.computational_fields.values():
                if field.name == field_name:
                    field_name = field.key
                    include = True
                    break
        else:
            include = True
        if include:
            mapped_rules.append((field_name, word, pos, action))
    db_conn.ApplyAllDatasetRules(dataset.key, mapped_rules)
    wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'step':GUITextFiltering.FILTERS_UPDATING_COUNTS_STEP}))
    db_conn.RefreshStringTokensIncluded(dataset.key)
    db_conn.RefreshStringTokensRemoved(dataset.key)
    included_counts = db_conn.GetIncludedStringTokensCounts(dataset.key)
    dataset.total_docs_remaining = included_counts['documents']
    dataset.total_tokens_remaining = included_counts['tokens']
    dataset.total_uniquetokens_remaining = included_counts['unique_tokens']
    logger.info("Finished")

def ApplyFilterNewRules(dataset, main_frame, new_rules):
    logger = logging.getLogger(__name__+".ApplyFilterNewRules")
    logger.info("Starting")
    if len(new_rules) > 0:
        db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'step': GUITextFiltering.FILTERS_APPLYING_RULES_STEP}))
        mapped_rules = []
        for field_name, word, pos, action in new_rules:
            include = False
            if field_name != Constants.FILTER_RULE_ANY:
                for field in dataset.computational_fields.values():
                    if field.name == field_name:
                        field_name = field.key
                        include = True
                        break
            else:
                include = True
            if include:
                mapped_rules.append((field_name, word, pos, action))
        db_conn.ApplyNewDatasetRules(dataset.key, mapped_rules)
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent({'step': GUITextFiltering.FILTERS_UPDATING_COUNTS_STEP}))
        db_conn.RefreshStringTokensIncluded(dataset.key)
        db_conn.RefreshStringTokensRemoved(dataset.key)
        included_counts = db_conn.GetIncludedStringTokensCounts(dataset.key)
        dataset.total_docs_remaining = included_counts['documents']
        dataset.total_tokens_remaining = included_counts['tokens']
        dataset.total_uniquetokens_remaining = included_counts['unique_tokens']
    logger.info("Finished")

def DatasetTypeLabel(dataset):
    if dataset.dataset_source == 'Reddit':
        if dataset.dataset_type == 'discussion':
            dataset_type = GUIText.REDDIT_DISCUSSIONS
        elif dataset.dataset_type == 'submission':
            dataset_type = GUIText.REDDIT_SUBMISSIONS
        elif dataset.dataset_type == 'comment':
            dataset_type = GUIText.REDDIT_COMMENTS
        else:
            dataset_type = dataset.dataset_type
    elif dataset.dataset_source == 'Twitter':
        if dataset.dataset_type == 'tweet':
            dataset_type = GUIText.TWITTER_TWEETS
        else:
            dataset_type = dataset.dataset_type
    else:
        dataset_type = dataset.dataset_type
    return dataset_type