import json, os


class _JsonConfig:
    def __init__(self, data, path):
        self.data = data
        self.path = path
        self.save = self.saveConfig
    def __setitem__(self, key, value):
        self.data[key] = value
    def __getitem__(self, item):
        if type(self.data) is dict:
            if list(self.data.keys()).__contains__(item):
                return self.data[item]
            else:
                return None
        else:
            return self.data[item]
    def __repr__(self):
        return str(self.data)
    def keys(self):
        return list(self.data.keys())
    def values(self):
        return list(self.data.values())
    def get(self, key, std):
        if key in self.data.keys():
            return self[key]
        else:
            return std
    def clearData(self):
        self.data = {}
        return self
    def getData(self):
        return self.data
    def getPrettifyData(self):
        return json.dumps(self.data, indent=4)
    def setData(self, d):
        if isinstance(d, dict) or isinstance(d, list):
            self.data = d.copy()
        else:
            self.data = d.data
        return self
    def saveConfig(self, beauty=True):
        if beauty:
            con = json.dumps(self.data, indent=4)
        else:
            con = json.dumps(self.data)
        file = open(self.path, "w")
        file.write(con)
        file.close()
    def toString(self, beauty=False):
        if beauty:
            return json.dumps(self.data, indent=4)
        else:
            return json.dumps(self.data)
    def setPath(self, path:str):
        self.path = path
        return self
    def getPath(self):
        return self.path

class JsonConfig:
    @staticmethod
    def isConfigAvailable(path):
        return os.path.exists(path)
    @staticmethod
    def loadConfig(path, create=False, ignoreErrors=False)->_JsonConfig:
        if not os.path.exists(path):
            if create:
                file = open(path, "w")
                file.write("{}")
                file.close()
            else: raise FileExistsError("Config file does not exists.: "+path)
        file = open(path, "rb")
        text = file.read()
        file.close()
        data = JsonConfig._decode(path, text, ignoreErrors)
        if isinstance(data, list) or isinstance(data, dict):
            return _JsonConfig(data, path)
        return data
    @staticmethod
    def fromString(s:str, ignoreErrors=False):
        data = JsonConfig._decode("", s.encode(), ignoreErrors)
        return data

    @staticmethod
    def fromDict(d:dict):
        return _JsonConfig(d, None)
    @staticmethod
    def prettifyString(s:str, ignoreErrors=False):
        data = JsonConfig.fromString(s, True)
        if isinstance(data, dict) or isinstance(data, list):
            return str(json.dumps(data, indent=4))
        if ignoreErrors:
            return data
        raise Exception(data)
    @staticmethod
    def prettifyData(data: dict, ignoreErrors=False):
        if isinstance(data, dict) or isinstance(data, list):
            return str(json.dumps(data, indent=4))
        if ignoreErrors:
            return data
        raise Exception(data)
    @staticmethod
    def _decode(path, s:bytes, ignoreErrors):
        try:
            data = json.loads(s.replace(b"\n", b"").replace(b"(", b"[").replace(b")", b"]"))  # .replace(b"'", b"\""))
        except json.JSONDecodeError as e:
            line = e.lineno
            col = e.colno
            pos = e.pos
            textLine = s.split(b"\n")[line - 1]
            if len(textLine) - pos > 10:
                to_ = pos + 10
                dots = True
            else:
                to_ = len(textLine)
                dots = False
            if pos >= 10:
                _dots = True
                from_ = pos - 10
            else:
                _dots = False
                from_ = 0
            err = "\nThis ConfigFile is corrupted or not readable!\n\nFile: " + path + "\nLine: " + str(
                line - 1) + "\nchar: " + str(pos) + "\nException type: " + str(e.msg) + "\n\nInvalid Syntax Here:\n" + (
                      "..." if _dots > 0 else "") + textLine[from_:to_].decode() + ("...\n" if dots else "\n")
            err += " " * ((pos - from_) if not _dots else (pos - from_ + 3)) + "^"
            if not ignoreErrors:
                raise Exception(err)
            return err
        return data

class AdvancedJsonConfig:
    _FOLDER = None
    def __init__(self, name):
        self._isWanings = True
        self.data = None
        self._path = None
        self._name = name
        self._std = {}
    def setWarnings(self, b):
        self._isWanings = bool(b)
    @staticmethod
    def setConfigFolderPath(path):
        AdvancedJsonConfig._FOLDER = path

    def __getitem__(self, item):
        try:
            return self.data[item]
        except:
            print("ERROR Could not get value from key '" + item + "'!\nConfigFile: " + self._path)
            return None
    def __setitem__(self, key, value):
        self.data[key] = value

    def keys(self):
        return list(self.data.keys())
    def values(self):
        return list(self.data.values())
    def getPath(self):
        return self._path
    def save(self, beauty=True):
        file = open(self._path, "w")
        if beauty:
            file.write(json.dumps(self.data, indent=4))
        else:
            file.write(json.dumps(self.data))
        file.close()
    def get(self, key:str, std):
        if key in self.data.keys():
            return self[key]
        else:
            return std
    def setDefault(self, d):
        self._std = d
    def getDefault(self):
        return self._std
    def setDataToDefault(self):
        self.data = self._std.copy()
        return self
    def load(self, name):
        if AdvancedJsonConfig._FOLDER is not None: self._path = os.path.join(AdvancedJsonConfig._FOLDER, name)
        else: self._path = name
        if not JsonConfig.isConfigAvailable(self._path):
            print("Configfile is missing! Creating blank config at: " + self._path)
            config = JsonConfig.loadConfig(self._path, True)
            config.setData(self._std)
            config.saveConfig(True)
        else:
            config = JsonConfig.loadConfig(self._path, True)
        if type(config) == _JsonConfig:
            self._config = config
            self.data = self._config.getData()
        return self