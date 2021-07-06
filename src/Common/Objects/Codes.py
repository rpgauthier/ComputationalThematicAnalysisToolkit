import logging
from datetime import date, datetime

from Common.Objects.Generic import GenericObject
import Common.Objects.Datasets as Datasets
import Common.Objects.Samples as Samples

class Code(GenericObject):
    def __init__(self, key):
        logger = logging.getLogger(__name__+".Code["+str(key)+"].__init__")
        logger.info("Starting")
        GenericObject.__init__(self, key, name=key)

        self.subcodes = {}
        self.connections = []
        self.quotations = []
    
    @property
    def key(self):
        return self._key
    @key.setter
    def key(self, value):
        self._name = value
        self._key = value
        self._last_changed_dt = datetime.now()

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = value
        self._key = value
        self._last_changed_dt = datetime.now()

    @property
    def last_changed_dt(self):
        for subcode_key in self.subcodes:
            tmp_last_changed_dt = self.subcodes[subcode_key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        for quotation_key in self.quotations:
            tmp_last_changed_dt = self.quotations[quotation_key].last_changed_dt
            if tmp_last_changed_dt > self._last_changed_dt:
                self._last_changed_dt = tmp_last_changed_dt
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value

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
        if (obj_module, key_path) in self.connections:
            self.connections.remove((obj_module, key_path))
            self.last_changed_dt = datetime.now()

    def GetConnections(self, datasets, samples):
        connection_objects = []
        for key_path in reversed(self.connections):
            current_parent = None
            if key_path[0] == Datasets.__name__:
                current_parent = datasets
                for key in key_path[1]:
                    if isinstance(current_parent, dict):
                        if key[1] in current_parent:
                            current_parent = current_parent[key[1]]
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
                        elif key[0] ==  Datasets.Document:
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
            else:
                #remove keypaths that dont exist to cleanup from name changes
                self.connections.remove(key_path)
        return list(reversed(connection_objects))
    
    def DestroyObject(self):
        #any childrens
        for code_key in list(self.subcodes.keys()):
            self.subcodes[code_key].DestroyObject()
        for quotation in reversed(self.quotations):
            quotation.DestroyObject()
        #remove self from parent if any
        if self.parent is not None:
            if self.key in self.parent.subcodes:
                if self.parent.subcodes[self.key] == self:
                    del self.parent.subcodes[self.key]
            self.parent.last_changed_dt = datetime.now()
            self.parent = None

class Quotation(GenericObject):
    def __init__(self, key, parent):
        GenericObject.__init__(self, key=key, parent=parent, name=key)
        #key needs to be a tuple made up of the dataset_key and a document_key from that dataset allowing for lookup of the document
        self._original_data = None
        self._paraphrased_data = None

    @property
    def original_data(self):
        return self._original_data
    @original_data.setter
    def original_data(self, value):
        self._original_data = value
        self.last_changed_dt = datetime.now()
    
    @property
    def paraphrased_data(self):
        return self._paraphrased_data
    @paraphrased_data.setter
    def paraphrased_data(self, value):
        self._paraphrased_data = value
        self.last_changed_dt = datetime.now()
    
    def DestroyObject(self):
        #remove self from parent if any
        if self.parent is not None:
            if self in self.parent.quotations:
                self.parent.quotations.remove(self)
            self.parent.last_changed_dt = datetime.now()
            self.parent = None
