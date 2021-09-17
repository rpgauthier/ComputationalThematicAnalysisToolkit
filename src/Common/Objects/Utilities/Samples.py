import logging
from datetime import datetime

import wx

import Common.Objects.Samples as Samples
import Common.Objects.Datasets as Datasets
from Common.GUIText import Samples as GUIText
import Common.Database as Database
import Common.Constants as Constants


#get a moment in time snap shot of the token set that includes each specified field
#snapshot is needed to generate ml samples
def CaptureTokens(dataset_key, main_frame):
    logger = logging.getLogger(__name__+".CaptureTokens")
    logger.info("Starting")
    token_dict = {}
    main_frame.PulseProgressDialog(GUIText.GENERATING_PREPARING_MSG)
    
    dataset = main_frame.datasets[dataset_key]

    #strings are from database table due to needing to handle memory constraints caused by number of NLP variables
    token_dict = Database.DatabaseConnection(main_frame.current_workspace.name).GetDocumentsTokensFromStringTokens(dataset.key)

    #Non-strings are stored in field objects
    field_list = list(main_frame.datasets[dataset_key].included_fields.keys())
    for field_key in main_frame.datasets[dataset_key].included_fields:
        if main_frame.datasets[dataset_key].included_fields[field_key].fieldtype != 'string':
            for doc_key in main_frame.datasets[dataset_key].included_fields[field_key].tokenset:
                if isinstance(main_frame.datasets[dataset_key].included_fields[field_key].tokenset[doc_key], list) and not isinstance(main_frame.datasets[dataset_key].included_fields[field_key].tokenset[doc_key], str):
                    for token in main_frame.datasets[dataset_key].included_fields[field_key].tokenset[doc_key]:
                        if main_frame.datasets[dataset_key].included_fields[field_key].fieldtype == 'UTC-timestamp' and token != '':
                            token_dict[doc_key].append(str(field_key) + "-" + str(datetime.utcfromtimestamp(token).strftime(Constants.DATETIME_FORMAT))+'UTC')
                        else:
                            token_dict[doc_key].append(str(field_key) + "-" + str(token))
                else:
                    if main_frame.datasets[dataset_key].included_fields[field_key].fieldtype == 'UTC-timestamp':
                            token_dict[doc_key].append(str(field_key) + "-" + str(datetime.utcfromtimestamp(main_frame.datasets[dataset_key].included_fields[field_key].tokenset[doc_key]).strftime(Constants.DATETIME_FORMAT))+'UTC')
                    else:
                        token_dict[doc_key].append(str(field_key) + "-" + str(main_frame.datasets[dataset_key].included_fields[field_key].tokenset[doc_key]))


    main_frame.PulseProgressDialog(GUIText.AFTERFILTERING_LABEL1+str(dataset.total_docs_remaining)+GUIText.AFTERFILTERING_LABEL2+str(dataset.total_docs)+GUIText.AFTERFILTERING_LABEL3)
    logger.info("Finished")
    return token_dict, field_list

def SamplesSelected(sample, dataset, obj, value):
    if isinstance(obj, Samples.Sample):
        for parts_key in obj.parts_dict:
            SamplesSelected(sample, dataset, obj.parts_dict[parts_key], value)
        obj.selected = value
    elif isinstance(obj, Samples.MergedPart):
        for parts_key in obj.parts_dict:
            SamplesSelected(sample, dataset, obj.parts_dict[parts_key], value)
        obj.selected = value
    elif isinstance(obj, Samples.Part):
        for doc_key in obj.documents:
            SamplesSelected(sample, dataset, dataset.documents[doc_key], value)
        obj.selected = value
    elif isinstance(obj, Datasets.Document):
        if value:
            sample.selected_documents.append(obj.key)
            sample.last_changed_dt = datetime.now()
        else:
            if obj.key in sample.selected_documents:
                sample.selected_documents.remove(obj.key)
                sample.last_changed_dt = datetime.now()
                
def dummy(x):
    return x