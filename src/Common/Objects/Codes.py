import logging
from datetime import datetime

from Common.Objects.Generic import GenericObject
import Common.Objects.Datasets as Datasets
import Common.Objects.Samples as Samples

class Code(GenericObject):

    def __init__(self, key):
        logger = logging.getLogger(__name__+".Code["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, name=key)

        self.connections = []

    def AddConnection(self, obj):
        obj_module = getattr(obj, '__module__', None)
        key_path = []
        key_path.append((type(obj), obj.key))
        while obj.parent != None:
            obj = obj.parent
            key_path.append((type(obj), obj.key))
        key_path.reverse()
        self.connections.append((obj_module, key_path))
        self.last_changed_dt = datetime.now()
    
    def RemoveConnection(self, obj):
        obj_module = getattr(obj, '__module__', None)
        key_path = []
        key_path.append((type(obj), obj.key))
        while obj.parent != None:
            obj = obj.parent
            key_path.append((type(obj), obj.key))
        key_path.reverse()
        self.connections.remove((obj_module, key_path))
        self.last_changed_dt = datetime.now()

    def GetConnections(self, datasets, samples):
        connection_objects = []
        for key_path in self.connections:
            if key_path[0] == Datasets.__name__:
                current_parent = datasets
                for key in key_path[1]:
                    if isinstance(current_parent, dict):
                        if key[1] in current_parent:
                            current_parent = current_parent[key[1]]
                        else:
                            current_parent = None
                            break
                    elif isinstance(current_parent, Datasets.GroupedDataset):
                        if key[0] ==  Datasets.Dataset:
                            if key[1] in current_parent.datasets:
                                current_parent = current_parent.datasets[key[1]]
                            else:
                                current_parent = None
                                break
                        elif key[0] ==  Datasets.MergedField:
                            if key[1] in current_parent.merged_fields:
                                current_parent = current_parent.merged_fields[key[1]]
                            else:
                                current_parent = None
                                break
                        elif key[0] ==  Datasets.GroupedDocuments:
                            if key[1] in current_parent.grouped_documents:
                                current_parent = current_parent.grouped_documents[key[1]]
                            else:
                                current_parent = None
                                break
                        else:
                            current_parent = None
                            break
                    elif isinstance(current_parent, Datasets.Dataset):
                        if key[0] ==  Datasets.Field:
                            if key[1] in current_parent.avaliable_fields:
                                current_parent = current_parent.avaliable_fields[key[1]]
                            else:
                                current_parent = None
                                break
                        elif key[0] ==  Datasets.Field:
                            if key[1] in current_parent.chosen_fields:
                                current_parent = current_parent.chosen_fields[key[1]]
                            else:
                                current_parent = None
                                break
                        elif key[0] ==  Datasets.MergedField:
                            if key[1] in current_parent.merged_fields:
                                current_parent = current_parent.merged_fields[key[1]]
                            else:
                                current_parent = None
                                break
                        elif key[0] ==  Datasets.Document:
                            if key[1] in current_parent.documents:
                                current_parent = current_parent.documents[key[1]]
                            else:
                                current_parent = None
                                break
                        else:
                            current_parent = None
                            break
                    elif isinstance(current_parent, Datasets.MergedField):
                        if key[0] ==  Datasets.Field:
                            if key[1] in current_parent.chosen_fields:
                                current_parent = current_parent.chosen_fields[key[1]]
                            else:
                                current_parent = None
                                break
                        else:
                            current_parent = None
                            break
                    elif isinstance(current_parent, Datasets.GroupedDocuments):
                        if key[0] ==  Datasets.Document:
                            if key[1] in current_parent.documents:
                                current_parent = current_parent.documents[key[1]]
                            else:
                                current_parent = None
                                break
                        else:
                            current_parent = None
                            break
                    else:
                        current_parent = None
                        break
                if current_parent is not None:
                    connection_objects.append(current_parent)
            elif key_path[0] == Samples.__name__:
                current_parent = samples
                for key in key_path[1]:
                    if isinstance(current_parent, dict):
                        if key in current_parent:
                            current_parent = current_parent[key[1]]
                        else:
                            current_parent = None
                            break
                    elif isinstance(current_parent, Samples.Sample):
                        if key[1] in current_parent.parts_dict:
                            current_parent = current_parent.parts_dict[key[1]]
                        else:
                            current_parent = None
                            break
                    elif isinstance(current_parent, Samples.MergedPart):
                        if key[1] in current_parent.parts_dict:
                            current_parent = current_parent.parts_dict[key[1]]
                        else:
                            current_parent = None
                            break
                    else:
                        current_parent = None
                        break
                if current_parent is not None:
                    connection_objects.append(current_parent)

        return connection_objects
