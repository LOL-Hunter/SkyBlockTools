import tksimple as tk
from pysettings.jsonConfig import AdvancedJsonConfig
from pysettings import iterDict
from pysettings.text import MsgText
from constants import STYLE_GROUP as SG
import os
from datetime import datetime
from threading import Thread
from webbrowser import open as openURL
from widgets import SettingValue
from skyMisc import parseTimeToStr, parseTimeDelta, requestItemHypixelAPI
from constants import API, Constants

APP_DATA = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
APP_DATA_SETTINGS = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".SkyBlockTools")
IMAGES = os.path.join(os.path.split(__file__)[0], "images")
CONFIG = os.path.join(os.path.split(__file__)[0], "config")
API_URL = "https://developer.hypixel.net/"

if not os.path.exists(APP_DATA_SETTINGS):
    os.mkdir(APP_DATA_SETTINGS)
    MsgText.warning("Settings Folder missing! Creating at: "+APP_DATA_SETTINGS)
def checkConfigForUpdates():
    for key in Config.SETTINGS_CONFIG.getDefault().keys():
        if key not in Config.SETTINGS_CONFIG.keys():
            MsgText.warning(f"Key '{key}' in settings config missing! Adding default...")
            if hasattr(Config.SETTINGS_CONFIG.getDefault()[key], "copy"):
                Config.SETTINGS_CONFIG[key] = Config.SETTINGS_CONFIG.getDefault()[key].copy()
            else:
                Config.SETTINGS_CONFIG[key] = Config.SETTINGS_CONFIG.getDefault()[key]

        if isinstance(Config.SETTINGS_CONFIG[key], dict):
            for key2 in Config.SETTINGS_CONFIG.getDefault()[key].keys():
                if key2 not in Config.SETTINGS_CONFIG[key].keys():
                    MsgText.warning(f"Key '{key}:{key2}' in settings config missing! Adding default...")
                    if hasattr(Config.SETTINGS_CONFIG.getDefault()[key][key2], "copy"):
                        Config.SETTINGS_CONFIG[key][key2] = Config.SETTINGS_CONFIG.getDefault()[key][key2].copy()
                    else:
                        Config.SETTINGS_CONFIG[key][key2] = Config.SETTINGS_CONFIG.getDefault()[key][key2]
    Config.SETTINGS_CONFIG.save()

class Config:
    AdvancedJsonConfig.setConfigFolderPath(APP_DATA_SETTINGS)

    SETTINGS_CONFIG = AdvancedJsonConfig("SettingsConfig")
    SETTINGS_CONFIG.setDefault({
        "player_name":"",
        "api_key":"",
        "notifications":{
            "tracker_manipulation":False,
            "tracker_custom":False,
            "tracker_crash":False,
            "tracker_flip":False,
        },
        "constants":{
            "bazaar_tax":1.25,
            "hypixel_bazaar_config_path":"",
            "hypixel_auction_config_path":"",
            "hypixel_item_config_path":"",
        },
        "pest_profit":{
            "farming_fortune":0,
            "crop_fortune":0,
            "pet_luck":0,
        },
        "magic_find":{
            "base_chance":1,
            "pet_luck":0,
            "magic_find":0,
            "magic_find_bestiary":0,
            "looting_lvl":0,
            "luck_lvl":0,
            "item_type":0
        },
        "wisdom":0,
        "auto_api_requests":{
            "bazaar_auto_request_off_on_load":True,
            "bazaar_auto_request":False,
            "bazaar_auto_request_interval": 60
        },
        "composter":{
            "speed":1,
            "multi_drop":1,
            "fuel_cap":1,
            "matter_cap":1,
            "cost_reduction":1
        },
        "auction_creator_uuids":{},
        "accessories":{}
    })
    SETTINGS_CONFIG.load("settings.json")
    SettingValue.CONFIG = SETTINGS_CONFIG
    Constants.BAZAAR_TAX = SETTINGS_CONFIG["constants"]["bazaar_tax"]
class ComposterSettings(tk.Frame):
    def __init__(self, master, onScrollHook=None):
        super().__init__(master)
        self.master = master
        self.onScrollHook = onScrollHook
        i=0
        for upgr, lvl in iterDict(Config.SETTINGS_CONFIG["composter"]):
            tk.Label(master, SG).setText(upgr).placeRelative(fixHeight=50, fixWidth=100, fixY=i*50)
            scale = tk.Scale(master, to=25)
            scale.onScroll(self.onChange, args=[upgr])
            scale.setValue(lvl)
            scale.placeRelative(fixHeight=50, fixX=100, fixY=i*50)
            i+=1

    def onChange(self, e):
        value = e.getWidget().getValue()
        Config.SETTINGS_CONFIG["composter"][e.getArgs(0)] = int(value)
        Config.SETTINGS_CONFIG.save()
        if self.onScrollHook is not None: self.onScrollHook()
class SettingsGUI(tk.Dialog):
    def __init__(self, master):
        super().__init__(master, SG, False)
        self.master = master
        self.setTitle("SkyBlockTools-Settings")
        self.setMinSize(410, 410)

        self.bind(self.close, tk.EventType.ESC)

        self.notebook = tk.Notebook(self, SG)
        self.generalTab = self.notebook.createNewTab("General", SG)
        self.notifyTab = self.notebook.createNewTab("Notifications", SG)
        self.constTab = self.notebook.createNewTab("Constants", SG)
        self.notebook.placeRelative()

        self.createGeneralTab(self.generalTab)
        self.createNotificationsTab(self.notifyTab)
        self.createConstantsTab(self.constTab)

        self.show()
        self.lift()
    def createGeneralTab(self, tab):
        self.keyLf = tk.LabelFrame(tab, SG)
        self.keyLf.setText("API-Authentication")
        self.apiUsernameTextE = tk.TextEntry(self.keyLf, SG)
        self.apiUsernameTextE.setValue(Config.SETTINGS_CONFIG["player_name"])
        self.apiUsernameTextE.setText("Username:")
        self.apiUsernameTextE.place(0, 0, 200, 25)
        self.apiUsernameTextE.getEntry().disable()
        self.apiKeyTextE = tk.TextEntry(self.keyLf, SG)
        self.apiKeyTextE.setValue("*" * 16 if Config.SETTINGS_CONFIG["api_key"] != "" else "No api key set!")
        self.apiKeyTextE.setText("API-Key:")
        self.apiKeyTextE.place(0, 25, 200, 25)
        self.apiKeyTextE.getEntry().disable()
        tk.Button(self.keyLf, SG).setText("Change...").setCommand(self._openChangeWindow).placeRelative(changeWidth=-5,  fixY=50, fixHeight=25)
        self.urlL = tk.Label(self.keyLf, SG).setText("Click to generate API-Key.").placeRelative(changeWidth=-5, fixY=75, fixHeight=25)
        self.urlL.bind(self._enter, tk.EventType.ENTER)
        self.urlL.bind(self._leave, tk.EventType.LEAVE)
        self.urlL.bind(self._click, tk.EventType.LEFT_CLICK)
        self.keyLf.place(0, 0, 205, 125)

        self.itemAPILf = tk.LabelFrame(tab, SG)
        self.itemAPILf.setText("Item-API")
        self.lastUpd = tk.Label(self.itemAPILf, SG).placeRelative(fixHeight=25, changeWidth=-5)
        self.regItems = tk.Label(self.itemAPILf, SG).placeRelative(fixHeight=25, changeWidth=-5, fixY=25)
        self.uptBtn = tk.Button(self.itemAPILf, SG).setText("Update Now").setCommand(self._updateItemAPI).placeRelative(fixHeight=25, changeWidth=-5, fixY=50)
        self.itemAPILf.place(205, 0, 205, 125)

        self.ownAuct = tk.LabelFrame(tab, SG)
        self.ownAuct.setText("Own-Auctions")

        self.players = tk.Listbox(self.ownAuct, SG)
        for uuid, player in iterDict(Config.SETTINGS_CONFIG["auction_creator_uuids"]):
            self.players.add(player+" : "+uuid)
        self.players.placeRelative(fixHeight=55, changeWidth=-5)
        self.uptBtn2 = tk.Button(self.ownAuct, SG).setText("Delete Selected Player").setCommand(self.deleteSelectedPlayer).placeRelative(fixHeight=25, changeWidth=-5, changeY=-45, stickDown=True)
        self.uptBtn3 = tk.Button(self.ownAuct, SG).setText("Add Player...").setCommand(self.addPlayer).placeRelative(fixHeight=25, changeWidth=-5, fixY=50, changeY=-20, stickDown=True)
        self.ownAuct.place(0, 125, 205, 125)

        self.autoRequests = tk.LabelFrame(tab, SG)
        self.autoRequests.setText("Auto-API-Requests")
        self.isAutoReq = tk.Checkbutton(self.autoRequests, SG)
        self.isAutoReq.onSelectEvent(self.writeAutoAPISettings)
        self.isAutoReq.setState(Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"])
        self.isAutoReq.setText("Bazaar-API-Auto-Request")
        self.isAutoReq.placeRelative(fixHeight=25, changeWidth=-5)
        self.isAutoReqOff = tk.Checkbutton(self.autoRequests, SG)
        self.isAutoReqOff.onSelectEvent(self.writeAutoAPISettings)
        self.isAutoReqOff.setText("Disable-Auto-Requests-Startup")
        self.isAutoReqOff.setState(Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_off_on_load"])
        self.isAutoReqOff.placeRelative(fixHeight=25, changeWidth=-5, fixY=50)
        self.reqInterval = tk.DropdownMenu(self.autoRequests, SG)

        options = {
            "300":"1 Request/5 Minutes (Slow)",
            "60":"1 Request/Minute (Normal)",
            "20":"3 Request/Minute (Fast)",
        }

        self.reqInterval.setOptionList(list(options.values()))
        self.reqInterval.onSelectEvent(self.writeAutoAPISettings)
        self.reqInterval.setValue(options[str(Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"])])
        self.reqInterval.placeRelative(fixHeight=25, fixY=25, changeWidth=-5)
        self.autoRequests.place(205, 125, 205, 125)

        self.updateItemAPIWidgets()
    def createNotificationsTab(self, tab):
        def change(e):
            Config.SETTINGS_CONFIG["notifications"][e.getArgs(0)] = (e.getValue() == "ON")
            Config.SETTINGS_CONFIG.save()
            self.master.mainMenuPage.getToolFromClassName("ItemPriceTrackerPage").updateNotificationFromSettings()

        for i, key in enumerate(Config.SETTINGS_CONFIG["notifications"].keys()):
            frame = tk.Frame(tab, SG)
            tk.Label(frame, SG).setText(key).placeRelative(fixWidth=200, changeHeight=-5)
            radio = tk.Radiobutton(frame, SG)
            radio.onSelectEvent(change, args=[key])
            offBtn = radio.createNewRadioButton(SG)
            onBtn = radio.createNewRadioButton(SG)
            onBtn.setText("ON")
            offBtn.setText("OFF")
            offBtn.placeRelative(changeHeight=-5, fixX=200, fixWidth=100)
            onBtn.placeRelative(changeHeight=-5, fixX=300, fixWidth=100)
            frame.placeRelative(fixY=25*i, fixHeight=25, changeWidth=-5)
            radio.setState(int(Config.SETTINGS_CONFIG["notifications"][key]))

    def writeAutoAPISettings(self):
        state = self.isAutoReq.getState()
        stateStartup = self.isAutoReqOff.getState()
        interval = self.reqInterval.getValue()
        transl = {
            "slow":300,
            "normal":60,
            "fast":20
        }
        for type_ in ["slow", "normal", "fast"]:
            if type_ in interval.lower():
                interval = transl[type_]
                break
        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = state
        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_off_on_load"] = stateStartup
        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"] = interval
        Config.SETTINGS_CONFIG.save()
        self.master.mainMenuPage.updateAutoRequestButton()

    def deleteSelectedPlayer(self):
        sel = self.players.getSelectedItem()
        if sel is not None:
            if tk.SimpleDialog.askOkayCancel(self, "Are you sure?", "Settings"):
                uuid = sel.split(":")[1].strip()
                Config.SETTINGS_CONFIG["auction_creator_uuids"].pop(uuid)
                Config.SETTINGS_CONFIG.save()
                self.players.clear()
                for uuid, player in iterDict(Config.SETTINGS_CONFIG["auction_creator_uuids"]):
                    self.players.add(player + " : " + uuid)
    def addPlayer(self):
        anw = tk.SimpleDialog.askUsernamePassword(self, unameString="Player Name: ", passwString="UUID: ", hidePassword=False)
        if anw is not None:
            pname, uuid = anw
            Config.SETTINGS_CONFIG["auction_creator_uuids"][uuid.replace("-", "")] = pname
            Config.SETTINGS_CONFIG.save()
            self.players.clear()
            for uuid, player in iterDict(Config.SETTINGS_CONFIG["auction_creator_uuids"]):
                self.players.add(player + " : " + uuid)
    def updateItemAPIWidgets(self):
        if API.SKYBLOCK_ITEM_API_PARSER is not None:
            amount = API.SKYBLOCK_ITEM_API_PARSER.getItemAmount()
            ts: datetime = API.SKYBLOCK_ITEM_API_PARSER.getLastUpdated()
            diff = parseTimeDelta(datetime.now() - ts)
            self.lastUpd.setText(f"Last-Updated: {parseTimeToStr(diff)} ago")
        else:
            amount = 0
            diff = "-1"
            self.lastUpd.setText(f"Error: could not request!")

        self.regItems.setText(f"Registered-Items: {amount}")
    def createConstantsTab(self, tab):

        self.valueLf = tk.LabelFrame(tab, SG)
        self.valueLf.setText("Constants:")
        tk.Text(tab, SG).setText("Ony change the Values if you\nreally know what you are doing!").setFg("red").place(0, 0, 305, 50).setFont(15).setDisabled()
        y = tk.Placer(ySpace=25)
        SettingValue(self.valueLf, name="Bazaar-Tax:", x=0, y=y.get(), key="bazaar_tax")
        SettingValue(self.valueLf, name="UseBazaarConfigAt:", x=0, y=y.get(), key="hypixel_bazaar_config_path")
        SettingValue(self.valueLf, name="UseAuctionConfigAt:", x=0, y=y.get(), key="hypixel_auction_config_path")

        self.valueLf.place(0, 50, 305, 300)
    def _requestItemAPI(self):
        Constants.WAITING_FOR_API_REQUEST = True

        API.SKYBLOCK_ITEM_API_PARSER = requestItemHypixelAPI(self, Config, saveTo=os.path.join(APP_DATA_SETTINGS, "skyblock_save", "hypixel_item_config.json"))
        if API.SKYBLOCK_AUCTION_API_PARSER is not None:
            API.SKYBLOCK_AUCTION_API_PARSER.changeItemParser(API.SKYBLOCK_ITEM_API_PARSER)
        Constants.WAITING_FOR_API_REQUEST = False
        self.uptBtn.setEnabled()
        self.updateItemAPIWidgets()
    def _updateItemAPI(self):
        if Constants.WAITING_FOR_API_REQUEST: return
        self.lastUpd.setText("Updating...")
        self.regItems.setText("")
        self.uptBtn.setDisabled()
        Thread(target=self._requestItemAPI).start()
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
    def openComposterSettings(master, finishHook=None, onScrollHook=None):
        dialog = tk.Dialog(master, SG)
        dialog.setWindowSize(400, 400)
        ComposterSettings(dialog, onScrollHook)
        if finishHook is not None: dialog.onCloseEvent(finishHook)
        dialog.show()
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
        if not master.loadingPage.loadingComplete: return
        SettingsGUI(master)
    @staticmethod
    def isAPIKeySet()->bool:
        return Config.SETTINGS_CONFIG["api_key"] != ""
    @staticmethod
    def checkItemConfigExist()->bool:
        path = os.path.join(APP_DATA_SETTINGS, "skyblock_save", "hypixel_item_config.json")
        if not os.path.exists(path):
            file = open(path, "w")
            file.write("{}")
            file.close()
            return False
        return True

