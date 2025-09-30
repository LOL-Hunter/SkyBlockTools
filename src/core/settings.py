import tksimple as tk
import os
from datetime import datetime
from threading import Thread

from .constants import STYLE_GROUP as SG
from .logger import MsgText
from .jsonConfig import AdvancedJsonConfig
from .widgets import SettingValue, APILoginWidget
from .skyMisc import iterDict, parseTimeToStr, parseTimeDelta, requestItemHypixelAPI
from .constants import API, Constants, System

def testForConfigFolder():
    if not os.path.exists(System.CONFIG_PATH):
        os.mkdir(System.CONFIG_PATH)
        MsgText.warning("Settings Folder missing! Creating at: "+System.CONFIG_PATH)

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
    AdvancedJsonConfig.setConfigFolderPath(System.CONFIG_PATH)

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
        "alchemy_wisdom":0,
        "auto_api_requests":{
            "bazaar_auto_request_off_on_load":True,
            "bazaar_auto_request":False,
            "bazaar_auto_request_interval": 60,
            "auction_auto_request_off_on_load": True,
            "auction_auto_request": False,
            "auction_auto_request_interval": 60
        },
        "composter":{
            "speed":1,
            "multi_drop":1,
            "fuel_cap":1,
            "matter_cap":1,
            "cost_reduction":1
        },
        "auction_creator_uuids":{},
        "accessories":{},
        "player_rank": "New_Player",
        "bin_sniper_blacklist":[]
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
    def __init__(self, master, hook=None):
        super().__init__(master, SG, False)
        self.master = master
        self.hook = None
        self.setTitle("SkyBlockTools-Settings")
        self.setMinSize(410, 410)

        self.bind(self.close, tk.EventType.ESC)
        self.onCloseEvent(self.close)

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
    def close(self):
        if self.hook is not None:
            self.hook()
    def createGeneralTab(self, tab):
        self.apiWidg = APILoginWidget(tab, self, Config.SETTINGS_CONFIG)
        self.apiWidg.place(0, 0, 205, 125)

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
        # Auto Req Bazaar
        self.autoRequestsBazaar = tk.LabelFrame(tab, SG)
        self.autoRequestsBazaar.setText("Auto-API-Requests-Bazaar")
        self.isAutoReqBazaar = tk.Checkbutton(self.autoRequestsBazaar, SG)
        self.isAutoReqBazaar.onSelectEvent(self.writeAutoAPISettings)
        self.isAutoReqBazaar.setState(Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"])
        self.isAutoReqBazaar.setText("Bazaar-API-Auto-Request")
        self.isAutoReqBazaar.placeRelative(fixHeight=25, changeWidth=-5)
        self.isAutoReqOffBazaar = tk.Checkbutton(self.autoRequestsBazaar, SG)
        self.isAutoReqOffBazaar.onSelectEvent(self.writeAutoAPISettings)
        self.isAutoReqOffBazaar.setText("Disable-Auto-Requests-Startup")
        self.isAutoReqOffBazaar.setState(Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_off_on_load"])
        self.isAutoReqOffBazaar.placeRelative(fixHeight=25, changeWidth=-5, fixY=50)
        self.reqIntervalBazaar = tk.DropdownMenu(self.autoRequestsBazaar, SG)

        options = {
            "60": "1 Request/Minute (Slow)",
            "30": "2 Request/Minute (Normal)",
            "10": "6 Request/Minute (Fast)",
        }

        self.reqIntervalBazaar.setOptionList(list(options.values()))
        self.reqIntervalBazaar.onSelectEvent(self.writeAutoAPISettings)
        if str(Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"]) in options.keys():
            self.reqIntervalBazaar.setValue(options[str(Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"])])
        self.reqIntervalBazaar.placeRelative(fixHeight=25, fixY=25, changeWidth=-5)
        self.autoRequestsBazaar.place(205, 125, 205, 125)
        
        # Auto Req Auc
        self.autoRequestsAuct = tk.LabelFrame(tab, SG)
        self.autoRequestsAuct.setText("Auto-API-Requests-Auction")
        self.isAutoReqAuct = tk.Checkbutton(self.autoRequestsAuct, SG)
        self.isAutoReqAuct.onSelectEvent(self.writeAutoAPISettings)
        self.isAutoReqAuct.setState(Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"])
        self.isAutoReqAuct.setText("Auction-API-Auto-Request")
        self.isAutoReqAuct.placeRelative(fixHeight=25, changeWidth=-5)
        self.isAutoReqOffAuct = tk.Checkbutton(self.autoRequestsAuct, SG)
        self.isAutoReqOffAuct.onSelectEvent(self.writeAutoAPISettings)
        self.isAutoReqOffAuct.setText("Disable-Auto-Requests-Startup")
        self.isAutoReqOffAuct.setState(Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_off_on_load"])
        self.isAutoReqOffAuct.placeRelative(fixHeight=25, changeWidth=-5, fixY=50)
        self.reqIntervalAuct = tk.DropdownMenu(self.autoRequestsAuct, SG)

        options = {
            "30": "2 Request/Minute (Slow)",
            "10": "6 Request/Minute (Normal)",
            "2": "30 Request/Minute (Fast)",
        }

        self.reqIntervalAuct.setOptionList(list(options.values()))
        self.reqIntervalAuct.onSelectEvent(self.writeAutoAPISettings)
        if str(Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_interval"]) in options.keys():
            self.reqIntervalAuct.setValue(options[str(Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_interval"])])
        self.reqIntervalAuct.placeRelative(fixHeight=25, fixY=25, changeWidth=-5)
        self.autoRequestsAuct.place(205, 125+125, 205, 125)


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
        def _translate(inv:str, data:dict):
            for type_ in ["slow", "normal", "fast"]:
                if type_ in inv.lower():
                    return data[type_]
            return 10_000 # failsafe

        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = self.isAutoReqBazaar.getState()
        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_off_on_load"] = self.isAutoReqOffBazaar.getState()
        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"] = _translate(
            self.reqIntervalBazaar.getValue(),
            {
                "slow": 60,
                "normal": 30,
                "fast": 10
            }
        )

        Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] = self.isAutoReqAuct.getState()
        Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_off_on_load"] = self.isAutoReqOffAuct.getState()
        Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_interval"] = _translate(
            self.reqIntervalAuct.getValue(),
        {
                "slow": 30,
                "normal": 10,
                "fast": 2
            }
        )
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
        API.SKYBLOCK_ITEM_API_PARSER = requestItemHypixelAPI(self, Config, saveTo=os.path.join(System.CONFIG_PATH, "skyblock_save", "hypixel_item_config.json"))
        Constants.WAITING_FOR_API_REQUEST = False
        self.uptBtn.setEnabled()
        self.updateItemAPIWidgets()
    def _updateItemAPI(self):
        if Constants.WAITING_FOR_API_REQUEST: return
        self.lastUpd.setText("Updating...")
        self.regItems.setText("")
        self.uptBtn.setDisabled()
        Thread(target=self._requestItemAPI).start()

    @staticmethod
    def openComposterSettings(master, finishHook=None, onScrollHook=None):
        dialog = tk.Dialog(master, SG)
        dialog.setWindowSize(400, 400)
        ComposterSettings(dialog, onScrollHook)
        if finishHook is not None: dialog.onCloseEvent(finishHook)
        dialog.show()
    @staticmethod
    def openSettings(master, hook=None):
        if not master.loadingPage.loadingComplete: return
        SettingsGUI(master, hook)
    @staticmethod
    def isAPIKeySet()->bool:
        return Config.SETTINGS_CONFIG["api_key"] != ""
    @staticmethod
    def checkItemConfigExist()->bool:
        path = os.path.join(System.CONFIG_PATH, "skyblock_save", "hypixel_item_config.json")
        if not os.path.exists(path):
            file = open(path, "w")
            file.write("{}")
            file.close()
            return False
        return True
    @staticmethod
    def checkAPIKeySet(master, hook):
        def load():
            root.destroy()
            hook()

        if Config.SETTINGS_CONFIG["api_key"] == "":
            tk.SimpleDialog.askInfo(master, "Hypixel-API-Key not set yet.\nSet API-Key in Settings to continue.")

            root = tk.Dialog(master, SG)
            root.setCloseable(False)
            root.setResizeable(False)
            root.setWindowSize(205, 125)

            apiWidg = APILoginWidget(root,
                                     root,
                                     Config.SETTINGS_CONFIG,
                                     continueAt=load,
                                     canCancel=False)
            apiWidg.placeRelative()
            root.show()
            return True
        return False




