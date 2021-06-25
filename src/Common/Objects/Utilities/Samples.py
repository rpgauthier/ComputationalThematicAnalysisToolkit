from datetime import datetime


from datetime import datetime

import Common.Objects.Samples as Samples
import Common.Objects.Datasets as Datasets

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