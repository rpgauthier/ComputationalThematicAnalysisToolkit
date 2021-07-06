import logging

import spacy
import nltk
from math import log

import wx

import Common.CustomEvents as CustomEvents
import Common.Objects.Datasets as Datasets
from Common.GUIText import Datasets as GUIText

def CreateDataset(dataset_key, retrieval_details, data, avaliable_fields_list, metadata_fields_list, included_fields_list):
    dataset = Datasets.Dataset(dataset_key,
                               dataset_key[0],
                               dataset_key[1],
                               dataset_key[2],
                               retrieval_details)
    dataset.metadata_fields_list = metadata_fields_list
    dataset.data = data
    
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

def CreateDatasetObjectsMetadata(dataset):
    id_keys = ["data_source", "data_type", "id"]
    metadata = {}
    for data_row in dataset.data.values():
        data_id = []
        for key in id_keys:
            data_id.append(data_row[key])
        metadata[tuple(data_id)] = {}
        metadata[tuple(data_id)]['dataset'] = dataset.key
        if hasattr(dataset, 'metadata_fields_list'):
            for field in dataset.metadata_fields_list:
                metadata[tuple(data_id)][field[0]] = data_row[field[0]]
        else:    
            url = data_row["url"]
            if url != '':
                metadata[tuple(data_id)]["url"] = url
            else:
                metadata[tuple(data_id)]["id"] = data_row['id']
            metadata[tuple(data_id)]["created_utc"] = data_row['created_utc']
    dataset.metadata = metadata

def TokenizeDatasetObjects(dataset_objects, notify_window, main_frame):
    logger = logging.getLogger(__name__+".TokenizeDatasetObjects")
    logger.info("Starting")
    fields = {}
    results = {}
    main_frame = main_frame

    def FindDatasetIdFields(dataset):
        id_key_fields = ["data_source", "data_type", "id"]
        return id_key_fields

    def TokenizationController(key, field, field_data):
        logger.info("Preparing Processes for dataset[%s], field[%s], for %s documents", str(key), str(field.key), str(len(field_data)))
        wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_STARTING_FIELD_MSG+str(key)))
        nonlocal fields
        fields[(key, field.key)] = field
        nonlocal results
        results[(key, field.key)] = []

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
                                                                   str((key, field.key)),
                                                                   str(count+1)+"-"+str(count+len(data_list)-1),
                                                                   field.parent.language))
            results[(key, field.key)].append(res)
            count = count+len(data_list)
            

    def FieldTokenizer(field, merged=False):
        id_key_fields = FindDatasetIdFields(field.dataset)
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
        if not merged:
            TokenizationController(field.dataset.key, field, field_data)
            return
        else:
            return field_data

    def DatasetTokenizer(dataset):
        for chosen_field_key in dataset.chosen_fields:
            FieldTokenizer(dataset.chosen_fields[chosen_field_key])

    for node in dataset_objects:
        if isinstance(node, Datasets.Dataset):
            DatasetTokenizer(node)
        elif isinstance(node, Datasets.Field):
            FieldTokenizer(node)

    if len(results) > 0:
        for key in results:
            completed = 0
            wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
                                                                   +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG2+str(len(results[key]))\
                                                                   +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG3+str(key)))
            tmp_tokensets = {}
            rawtext_df = {}
            stem_df = {}
            lemma_df = {}
            for res in results[key]:
                new_tokensets = res.get()[0]
                new_rawtext_df = res.get()[1]
                for rawtext in new_rawtext_df:
                    if rawtext in rawtext_df:
                        rawtext_df[rawtext] = rawtext_df[rawtext] + new_rawtext_df[rawtext]
                    else:
                        rawtext_df[rawtext] = new_rawtext_df[rawtext]
                new_stem_df = res.get()[2]
                for stem in new_stem_df:
                    if stem in stem_df:
                        stem_df[stem] = stem_df[stem] + new_stem_df[stem]
                    else:
                        stem_df[stem] = new_stem_df[stem]
                new_lemma_df = res.get()[3]
                for lemma in new_lemma_df:
                    if lemma in lemma_df:
                        lemma_df[lemma] = lemma_df[lemma] + new_lemma_df[lemma]
                    else:
                        lemma_df[lemma] = new_lemma_df[lemma]
                completed += 1
                package_versions = res.get()[4]
                tmp_tokensets.update(new_tokensets)
                logger.info("%s %s", str(key), len(tmp_tokensets))
                wx.PostEvent(notify_window, CustomEvents.ProgressEvent(GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG1+str(completed)\
                                                                       +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG2+str(len(results[key]))\
                                                                       +GUIText.TOKENIZING_BUSY_COMPLETED_FIELD_MSG3+str(key)))
            #convert df to idf
            doc_num = len(tmp_tokensets)
            rawtext_idf = {}
            for rawtext in rawtext_df:
                rawtext_idf[rawtext] = log(doc_num/rawtext_df[rawtext])
            stem_idf = {}
            for stem in stem_df:
                stem_idf[stem] = log(doc_num/stem_df[stem])
            lemma_idf = {}
            for lemma in lemma_df:
                lemma_idf[lemma] = log(doc_num/lemma_df[lemma])

            #combine with tf with idf for all tokens in tokensets
            tokensets = {}
            for toksenset_key in tmp_tokensets:
                tokenset = []
                order = 0
                for tmp_token in tmp_tokensets[toksenset_key]:
                    token = (order,
                             tmp_token[0], tmp_token[1], tmp_token[2],
                             tmp_token[3], tmp_token[4],
                             tmp_token[5]*rawtext_idf[tmp_token[0]],
                             tmp_token[6]*stem_idf[tmp_token[1]],
                             tmp_token[7]*lemma_idf[tmp_token[2]])
                    tokenset.append(token)
                    order = order + 1
                tokensets[toksenset_key] = tokenset

            fields[key].tokenset = tokensets
            fields[key].dataset.tokenization_package_versions = package_versions
    logger.info("Finished")

def TokenizationWorker(data_list, field, label, language):
    logger = logging.getLogger(__name__+".TokenizationWorker["+str(field)+"]["+str(label)+"]")
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
    #document frequency
    rawtext_tokens_df = {}
    stem_tokens_df = {}
    lemma_tokens_df = {}
    
    for key, data in data_list:
        tmp_tokenset = []
        rawtext_tf = {}
        stem_tf = {}
        lemma_tf = {}
        for tmp_tokens in nlp.pipe(data):
            for token in tmp_tokens:
                #order must align to Common.Constants.tokenization.tokenset_indexes
                rawtext = token.text.strip().lower()
                stem = stemmer.stem(token.text).strip().lower()
                lemma = token.lemma_.strip().lower()
                tmp_tokenset.append((rawtext,
                                     stem,
                                     lemma,
                                     token.pos_,
                                     token.is_stop))
                if rawtext in rawtext_tf:
                    rawtext_tf[rawtext] = rawtext_tf[rawtext] + 1
                else:
                    rawtext_tf[rawtext] = 1
                if stem in stem_tf:
                    stem_tf[stem] = stem_tf[stem] + 1
                else:
                    stem_tf[stem] = 1
                if lemma in lemma_tf:
                    lemma_tf[lemma] = lemma_tf[lemma] + 1
                else:
                    lemma_tf[lemma] = 1

        tokenset = []
        for tmp_token in tmp_tokenset:
            tokenset.append((tmp_token[0], tmp_token[1], tmp_token[2],
                            tmp_token[3], tmp_token[4],
                            rawtext_tf[tmp_token[0]], stem_tf[tmp_token[1]], lemma_tf[tmp_token[2]]))
        tokensets[key] = tokenset        

        for rawtext in rawtext_tf:
            if rawtext in rawtext_tokens_df:
                rawtext_tokens_df[rawtext] = rawtext_tokens_df[rawtext] + 1
            else:
                rawtext_tokens_df[rawtext] = 1
        for stem in stem_tf:
            if stem in stem_tokens_df:
                stem_tokens_df[stem] = stem_tokens_df[stem] + 1
            else:
                stem_tokens_df[stem] = 1
        for lemma in lemma_tf:
            if lemma in lemma_tokens_df:
                lemma_tokens_df[lemma] = lemma_tokens_df[lemma] + 1
            else:
                lemma_tokens_df[lemma] = 1

    logger.info("Finished")
    return tokensets, rawtext_tokens_df, stem_tokens_df, lemma_tokens_df, package_versions
