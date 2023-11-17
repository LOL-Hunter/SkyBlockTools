from pysettings import tk
from pysettings.jsonConfig import AdvancedJsonConfig
from constants import STYLE_GROUP as SG
import os
from webbrowser import open as openURL
from widgets import SettingValue
IMAGES = os.path.join(os.path.split(__file__)[0], "images")
CONFIG = os.path.join(os.path.split(__file__)[0], "config")
API_URL = "https://developer.hypixel.net/"





class Config:
    AdvancedJsonConfig.setConfigFolderPath(CONFIG)

    SETTINGS_CONFIG = AdvancedJsonConfig("SettingsConfig")
    SETTINGS_CONFIG.setDefault({
        "player_name":"",
        "api_key":"",
        "constants":{
            "bazaar_tax":1.25
        }
    })
    SETTINGS_CONFIG.load("settings.json")
    SettingValue.CONFIG = SETTINGS_CONFIG


class SettingsGUI(tk.Dialog):
    def __init__(self, master):
        super().__init__(master, SG, False)
        self.master = master
        self.setTitle("SkyBlockTools-Settings")
        self.setMinSize(400, 400)

        self.notebook = tk.Notebook(self, SG)
        self.generalTab = self.notebook.createNewTab("General", SG)
        self.constTab = self.notebook.createNewTab("Constants", SG)
        self.notebook.placeRelative()

        self.createGeneralTab(self.generalTab)
        self.createConstantsTab(self.constTab)


        self.show()
        self.lift()

    def createGeneralTab(self, tab):
        self.keyLf = tk.LabelFrame(tab, SG)
        self.keyLf.setText("API-Authentication")
        self.apiUsernameTextE = tk.TextEntry(self.keyLf, SG)
        self.apiUsernameTextE.setValue(Config.SETTINGS_CONFIG["player_name"])
        self.apiUsernameTextE.setText("Username:")
        self.apiUsernameTextE.getEntry().disable()
        self.apiUsernameTextE.place(0, 0, 200, 25)
        self.apiKeyTextE = tk.TextEntry(self.keyLf, SG)
        self.apiKeyTextE.setValue("*" * 16 if Config.SETTINGS_CONFIG["api_key"] != "" else "No api key set!")
        self.apiKeyTextE.setText("API-Key:")
        self.apiKeyTextE.getEntry().disable()
        self.apiKeyTextE.place(0, 25, 200, 25)
        tk.Button(self.keyLf, SG).setText("Change...").setCommand(self._openChangeWindow).placeRelative(changeWidth=-5,
                                                                                                        fixY=50,
                                                                                                        fixHeight=25)
        self.urlL = tk.Label(self.keyLf, SG).setText("Click to generate API-Key.").placeRelative(changeWidth=-5,
                                                                                                 fixY=75, fixHeight=25)
        self.urlL.bind(self._enter, tk.EventType.ENTER)
        self.urlL.bind(self._leave, tk.EventType.LEAVE)
        self.urlL.bind(self._click, tk.EventType.LEFT_CLICK)
        self.keyLf.place(0, 0, 205, 125)

    def createConstantsTab(self, tab):

        self.valueLf = tk.LabelFrame(tab, SG)
        self.valueLf.setText("Constants:")
        tk.Text(tab, SG).setText("Ony change the Values if you\nreally know what you are doing!").setFg("red").place(0, 0, 305, 50).setFont(15).setDisabled()
        heightW = 10

        SettingValue(self.valueLf, name="Bazaar-Tax:", x=0, y=0, key="bazaar_tax")

        self.valueLf.place(0, 50, 305, 300)




    def _enter(self):
        self.urlL.setText(API_URL)
    def _leave(self):
        self.urlL.setText("Click to generate API-Key.")
    def _click(self):
        openURL(API_URL)
        self.urlL.setText("Click to generate API-Key.")

    def _openChangeWindow(self):
        SettingsGUI.openAPIKeyChange(self)

    @staticmethod
    def openAPIKeyChange(master, continueAt=None):
        def setData():
            _apiKey = apiKeyTextE.getValue()
            _userName = apiUsernameTextE.getValue()
            if _apiKey == "" or _userName == "":
                tk.SimpleDialog.askError(master, "'API-Key' or 'Username' is empty!")
                return
            Config.SETTINGS_CONFIG["api_key"] = _apiKey
            Config.SETTINGS_CONFIG["player_name"] = _userName
            Config.SETTINGS_CONFIG.save()
            if isinstance(_master, SettingsGUI):
                _master.apiKeyTextE.enable()
                _master.apiUsernameTextE.enable()
                _master.apiKeyTextE.setValue("*" * 16 if Config.SETTINGS_CONFIG["api_key"] != "" else "No api key set!")
                _master.apiUsernameTextE.setValue(Config.SETTINGS_CONFIG["player_name"])
                _master.apiKeyTextE.disable()
                _master.apiUsernameTextE.disable()
                _master.update()

            master.destroy()
            if continueAt is not None:
                continueAt()

        def cancel():
            master.destroy()
            if continueAt is not None:
                continueAt()

        _master = master
        if isinstance(master, tk.Event):
            master = master.getArgs(0)
            if len(master.getArgs()) > 1:
                continueAt = master.getArgs(1)
        master = tk.Dialog(master, SG)
        master.setTitle("Set API-Key")
        master.setCloseable(False)
        master.setResizeable(False)
        master.setWindowSize(200, 75)
        apiUsernameTextE = tk.TextEntry(master, SG)
        apiUsernameTextE.setText("Username:")
        apiUsernameTextE.place(0, 0, 200, 25)
        apiKeyTextE = tk.TextEntry(master, SG)
        apiKeyTextE.setText("API-Key:")
        apiKeyTextE.place(0, 25, 200, 25)

        tk.Button(master, SG).setText("OK").place(0, 50, 100, 25).setCommand(setData)
        tk.Button(master, SG).setText("Cancel").place(100, 50, 100, 25).setCommand(cancel)

        apiUsernameTextE.getEntry().setFocus()
        master.show()
    @staticmethod
    def openSettings(master):
        SettingsGUI(master)
    @staticmethod
    def isAPIKeySet()->bool:
        return Config.SETTINGS_CONFIG["api_key"] != ""

