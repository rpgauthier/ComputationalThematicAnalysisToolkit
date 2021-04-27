from datetime import datetime

import Common.Objects.Datasets as Datasets

def CreateMetadata(dataset):
    def DatasetMetadata(dataset):
        id_keys = ["data_source", "data_type", "id"]
        metadata = {}
        for data_row in dataset.data.values():
            data_id = []
            for key in id_keys:
                data_id.append(data_row[key])
            metadata[tuple(data_id)] = {}
            if dataset.grouping_field is not None:
                grouping_key = data_row[dataset.grouping_field.key]
                metadata[tuple(data_id)]["grouping_key"] = grouping_key
            url = data_row["url"]
            metadata[tuple(data_id)]['dataset'] = dataset.key
            metadata[tuple(data_id)]["url"] = url
        dataset.metadata = metadata

    def GroupedDatasetMetadata(grouped_dataset):
        metadata = {}
        for dataset in grouped_dataset.datasets:
            DatasetMetadata(grouped_dataset.datasets[dataset])
            for data_id in grouped_dataset.datasets[dataset].metadata:
                grouping_key = grouped_dataset.datasets[dataset].metadata[data_id]["grouping_key"]
                if grouping_key not in metadata:
                    metadata[grouping_key] = {}
                    metadata[grouping_key]['submetadata'] = {}
                submetadata = grouped_dataset.datasets[dataset].metadata[data_id]
                metadata[grouping_key]['submetadata'][data_id] = submetadata
        grouped_dataset.metadata = metadata

    if isinstance(dataset, Datasets.Dataset):
        DatasetMetadata(dataset)
    elif isinstance(dataset, Datasets.GroupedDataset):
        GroupedDatasetMetadata(dataset)