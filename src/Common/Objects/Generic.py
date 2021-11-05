from datetime import datetime
import uuid

class GenericObject(object):
    def __init__(self, key=None, parent=None, name=None):
        #properties that automatically update last_changed_dt
        if key != None:
            self._uuid = str(uuid.uuid4())
            self._key = key
        else:
            self._uuid = str(uuid.uuid4())
            self._key = self._uuid
        self._parent = parent
        self._name = name
        self._label = ""
        self._notes = ""
        self._usefulness_flag = None

        #objects that have their own last_changed_dt and thus need to be checked dynamically

        #object ids that cross-reference ids from other repo's controlled by the app
        self._codes = []

        #properties that track datetime of creation and change
        self._created_dt = datetime.now()
        self._last_changed_dt = datetime.now()

    @property
    def key(self):
        return self._key
    @key.setter
    def key(self, value):
        self._key = value
        self.last_changed_dt = datetime.now()

    @property
    def parent(self):
        return self._parent
    @parent.setter
    def parent(self, value):
        self._parent = value
        self.last_changed_dt = datetime.now()

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = value
        self.last_changed_dt = datetime.now()

    @property
    def label(self):
        return self._label
    @label.setter
    def label(self, value):
        self._label = value
        self.last_changed_dt = datetime.now()

    @property
    def notes(self):
        return self._notes
    @notes.setter
    def notes(self, value):
        self._notes = value
        self.last_changed_dt = datetime.now()

    @property
    def usefulness_flag(self):
        return self._usefulness_flag
    @usefulness_flag.setter
    def usefulness_flag(self, value):
        self._usefulness_flag = value
        self.last_changed_dt = datetime.now()

    @property
    def codes(self):
        return self._codes
    def AppendCode(self, value):
        self._codes.append(value)
        self.last_changed_dt = datetime.now()
    def RemoveCode(self, value):
        self._codes.remove(value)
        self.last_changed_dt = datetime.now()
    def RemoveAllCodes(self):
        self._codes.clear()
        self.last_changed_dt = datetime.now()

    @property
    def created_dt(self):
        return self._created_dt
    @created_dt.setter
    def created_dt(self, value):
        self._created_dt = value

    @property
    def last_changed_dt(self):
        return self._last_changed_dt
    @last_changed_dt.setter
    def last_changed_dt(self, value):
        self._last_changed_dt = value

    def GetCodeConnections(self, codes):
        code_objs = []
        for code_key in codes:
            if code_key in self.codes:
                code_objs.append(codes[code_key])
            code_objs.extend(self.GetCodeConnections(codes[code_key].subcodes))
        return code_objs