import logging

import spacy
import nltk
from math import log

import wx

import Common.CustomEvents as CustomEvents
import Common.Objects.Datasets as Datasets
import Common.Database as Database
from Common.GUIText import Datasets as GUIText

def CreateDataset(dataset_key, retrieval_details, data, avaliable_fields_list, metadata_fields_list, included_fields_list, main_frame):
    dataset = Datasets.Dataset(dataset_key,
                               dataset_key[0],
                               dataset_key[1],
                               dataset_key[2],
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
    for field_name, field_info in avaliable_fields_list:
        new_field = Datasets.Field(dataset,
                                   field_name,
                                   dataset,
                                   field_info['desc'],
                                   field_info['type'])
        dataset.avaliable_fields[field_name] = new_field
    for field_name, field_info in included_fields_list:
        new_field = Datasets.Field(dataset,
                                   field_name,
                                   dataset,
                                   field_info['desc'],
                                   field_info['type'])
        dataset.chosen_fields[field_name] = new_field
    return dataset

def TokenizeDataset(dataset, notify_window, main_frame, rerun=False):
    logger = logging.getLogger(__name__+".TokenizeDataset")
    logger.info("Starting")
    main_frame = main_frame
    db_conn = Database.DatabaseConnection(main_frame.current_workspace.name)

    def TokenizationController(field, field_data):
        logger.info("Preparing Processes for dataset[%s], field[%s], for %s documents", str(dataset.key), str(field.key), str(len(field_data)))
        wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_STARTING_FIELD_MSG+str(field.key)))
        results = []

        total = len(field_data)
        nonlocal main_frame
        
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
        wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
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
            wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
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
    for chosen_field_key in dataset.chosen_fields:
        has_data = False
        if dataset.chosen_fields[chosen_field_key].fieldtype == 'string':
            if rerun:
                db_conn.DeleteField(dataset.key, chosen_field_key)
            else:
                has_data = db_conn.CheckIfFieldExists(dataset.key, chosen_field_key)
            if not has_data:
                FieldTokenizer(dataset.chosen_fields[chosen_field_key])
                stringfield_count = stringfield_count + 1
        elif dataset.chosen_fields[chosen_field_key].tokenset == None or rerun:
            FieldTokenizer(dataset.chosen_fields[chosen_field_key])

    #calculate tfidf scores for all stored string tokens if any changes occured
    if stringfield_count > 0:
        wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_STARTING_TFIDF_MSG))
        db_conn.UpdateStringTokensTFIDF(dataset.key)
        counts = db_conn.GetStringTokensCounts(dataset.key)
        dataset.total_docs = counts['documents']
        dataset.total_tokens = counts['tokens']
        dataset.total_uniquetokens = counts['unique_tokens']
        wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_TFIDF_MSG))
            
    logger.info("Finished")

def TokenizationWorker(data_list, field_key, label, language):
    logger = logging.getLogger(__name__+".TokenizationWorker["+str(field_key)+"]["+str(label)+"]")
    logger.info("Starting")

    package_versions = []

    spacy.prefer_gpu()
    if language == 'fre-trf':
        # tried to updated to use more accurate model
        # but not able to install on python 3.9 on Feb 23 2021
        nlp = spacy.load("fr_dep_news_trf")
        stemmer = nltk.stem.snowball.FrenchStemmer()
        package_versions.append(spacy.__name__+" "+spacy.__version__+" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
        package_versions.append(nltk.__name__ +" "+nltk.__version__+" snowball.FrenchStemmer")
        package_versions.append(spacy.__name__ +" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
    elif language == 'fre-sm':
        #less accurate but faster model
        nlp = spacy.load('fr_core_news_sm')
        stemmer = nltk.stem.snowball.FrenchStemmer()
        package_versions.append(spacy.__name__+" "+spacy.__version__+" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
        package_versions.append(nltk.__name__ +" "+nltk.__version__+" snowball.FrenchStemmer")
        package_versions.append(spacy.__name__ +" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
    elif language == 'eng-trf':
        #more accurate but slower model
        nlp = spacy.load("en_core_web_trf")
        stemmer = nltk.stem.snowball.EnglishStemmer()
        package_versions.append(spacy.__name__+" "+spacy.__version__+" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
        package_versions.append(nltk.__name__ +" "+nltk.__version__+" snowball.EnglishStemmer")
        package_versions.append(spacy.__name__ +" "+nlp.meta['lang']+"_"+nlp.meta['name']+" "+nlp.meta['version'])
    elif language == 'eng-sm':
        #less accurate but faster model
        nlp = spacy.load('en_core_web_sm')
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
