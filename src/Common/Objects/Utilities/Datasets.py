import logging

import spacy
import en_core_web_sm
import fr_core_news_sm
import nltk

import wx

import Common.CustomEvents as CustomEvents
import Common.Objects.Datasets as Datasets
import Common.Database as Database
from Common.GUIText import Datasets as GUIText
from Common.GUIText import Filtering as GUITextFiltering

def CreateDataset(dataset_key, language, retrieval_details, data, available_fields_list, metadata_fields_list, included_fields_list, main_frame):
    dataset = Datasets.Dataset(dataset_key,
                               dataset_key[0],
                               dataset_key[1],
                               dataset_key[2],
                               language,
                               retrieval_details)

    db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)
    
    db_conn.InsertDataset(dataset_key, 'text')

    dataset.data = data
    
    db_conn.InsertDocuments(dataset_key, dataset.data.keys())
    
    for field_name, field_info in metadata_fields_list:
        new_field = Datasets.Field(dataset,
                                   field_name,
                                   dataset,
                                   field_info['desc'],
                                   field_info['type'])
        dataset.metadata_fields[field_name] = new_field
    for field_name, field_info in available_fields_list:
        new_field = Datasets.Field(dataset,
                                   field_name,
                                   dataset,
                                   field_info['desc'],
                                   field_info['type'])
        dataset.available_fields[field_name] = new_field
    for field_name, field_info in included_fields_list:
        new_field = Datasets.Field(dataset,
                                   field_name,
                                   dataset,
                                   field_info['desc'],
                                   field_info['type'])
        dataset.included_fields[field_name] = new_field
    return dataset

def TokenizeDataset(dataset, notify_window, main_frame, rerun=False):
    logger = logging.getLogger(__name__+".TokenizeDataset")
    logger.info("Starting")
    main_frame = main_frame
    db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)

    def TokenizationController(field, field_data):
        logger.info("Preparing Processes for dataset[%s], field[%s], for %s documents", str(dataset.key), str(field.key), str(len(field_data)))
        nonlocal main_frame
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_STARTING_FIELD_MSG+str(field.key)))
        results = []

        total = len(field_data)
        full_data_list = list(field_data.items())
        split_data_lists = []
        if total > main_frame.pool_num:
            increment = int(total/main_frame.pool_num)
            start = 0
            end = increment
            for i in range(main_frame.pool_num-1):
                split_data_lists.append(full_data_list[start:end])
                start = end
                end = end+increment
            split_data_lists.append(full_data_list[start:])
        else:
            for i in range(total):
                split_data_lists.append(full_data_list[i:i+1])
        
        count = 0
        for data_list in split_data_lists:
            logger.info("Creating TokenizationWorker for Documents %s - %s", str(count+1), str(count+len(data_list)))
            res = main_frame.pool.apply_async(TokenizationWorker, (data_list, 
                                                                   str(field.key),
                                                                   str(count+1)+"-"+str(count+len(data_list)-1),
                                                                   field.parent.language))
            results.append(res)
            count = count+len(data_list)
        
        completed = 0
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
                                                               +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG2+str(len(results))\
                                                               +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG3+str(field.key)))
        if not db_conn.CheckIfFieldExists(dataset.key, field.key):
            db_conn.InsertField(dataset.key, field.key)
        for res in results:
            new_tokensets = res.get()[0]
            package_versions = res.get()[1]

            #insert documents' tokens into database
            db_conn.InsertStringTokens(dataset.key, field.key, new_tokensets)
            completed += 1
            logger.info("%s %s", str(field.key), completed)
            wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
                                                                   +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG2+str(len(results))\
                                                                   +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG3+str(field.key)))

        dataset.tokenization_package_versions = package_versions

    def FieldTokenizer(field):
        id_key_fields = ["data_source", "data_type", "id"]
        field_data = {}
        for data in field.dataset.data.values():
            id_key = tuple(data[id_key_field] for id_key_field in id_key_fields)
            if id_key not in field_data:
                if field.key in data:
                    if isinstance(data[field.key], str):
                        field_data[id_key] = [data[field.key]]
                    else:
                        field_data[id_key] = data[field.key]
                else:
                    field_data[id_key] = [""]
            else:
                if field.key in data:
                    if isinstance(data[field.key], str):
                        field_data[id_key].append(data[field.key])
                    else:
                        field_data[id_key].extend(data[field.key])
                else:
                    field_data[id_key].append("")
        if field.fieldtype == "string":
            TokenizationController(field, field_data)
        else:
            field.tokenset = field_data

    stringfield_count = 0
    for included_field_key in dataset.included_fields:
        has_data = False
        if dataset.included_fields[included_field_key].fieldtype == 'string':
            if rerun:
                db_conn.DeleteField(dataset.key, included_field_key)
            else:
                has_data = db_conn.CheckIfFieldExists(dataset.key, included_field_key)
            if not has_data:
                FieldTokenizer(dataset.included_fields[included_field_key])
                stringfield_count = stringfield_count + 1
        elif dataset.included_fields[included_field_key].tokenset == None or rerun:
            FieldTokenizer(dataset.included_fields[included_field_key])

    #calculate tfidf scores for all stored string tokens if any changes occured
    if stringfield_count > 0:
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_STARTING_TFIDF_MSG))
        db_conn.UpdateStringTokensTFIDF(dataset.key)
        counts = db_conn.GetStringTokensCounts(dataset.key)
        dataset.total_docs = counts['documents']
        dataset.total_tokens = counts['tokens']
        dataset.total_uniquetokens = counts['unique_tokens']
        wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_TFIDF_MSG))
        ApplyFilterAllRules(dataset, main_frame)
            
    logger.info("Finished")

def TokenizationWorker(data_list, field_key, label, language):
    logger = logging.getLogger(__name__+".TokenizationWorker["+str(field_key)+"]["+str(label)+"]")
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
    wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUITextFiltering.FILTERS_APPLYING_RULES_BUSY_MSG))
    db_conn.ApplyAllDatasetRules(dataset.key, dataset.filter_rules)
    db_conn.RefreshStringTokensIncluded(dataset.key)
    db_conn.RefreshStringTokensRemoved(dataset.key)
    wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUITextFiltering.FILTERS_UPDATING_COUNTS))
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
            wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUITextFiltering.FILTERS_APPLYING_RULES_BUSY_MSG))
            db_conn.ApplyNewDatasetRules(dataset.key, new_rules)
            db_conn.RefreshStringTokensIncluded(dataset.key)
            db_conn.RefreshStringTokensRemoved(dataset.key)
            wx.PostEvent(main_frame, CustomEvents.ProgressEvent(GUITextFiltering.FILTERS_UPDATING_COUNTS))
            included_counts = db_conn.GetIncludedStringTokensCounts(dataset.key)
            dataset.total_docs_remaining = included_counts['documents']
            dataset.total_tokens_remaining = included_counts['tokens']
            dataset.total_uniquetokens_remaining = included_counts['unique_tokens']
    logger.info("Finished")