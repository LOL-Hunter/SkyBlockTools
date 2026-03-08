# -*- coding: iso-8859-15 -*-
import os
from threading import Thread
from time import time, sleep

import tksimple as tk

from core.bazaarAnalyzer import updateBazaarAnalyzer
from core.constants import (
    VERSION,
    System,
    LOAD_STYLE,
    STYLE_GROUP as SG,
    BAZAAR_INFO_LABEL_GROUP as BILG,
    AUCT_INFO_LABEL_GROUP as AILG,
    API,
    Constants,
)
from core.hyPI.hypixelAPI.loader import HypixelBazaarParser
from core.customPage import SearchPage, MainMenuPage, LoadingPage
from core.image import IconLoader
from core.jsonConfig import JsonConfig
from core.logger import MsgText, Title
from core.settings import SettingsGUI, Config, checkConfigForUpdates, testForConfigFolder
from core.skyMisc import (
    requestAuctionHypixelAPI,
    requestBazaarHypixelAPI,
    updateAuctionInfoLabel,
    updateBazaarInfoLabel,
    determineSystem,
    registerPath,
    loadConfigs,
    initClipBoard
)
from core.widgets import CustomPage
from core.featureLoader import FeatureLoader
from ItemInfo import ItemInfoPage

# Window class
class Window(tk.Tk):
    def __init__(self):
        checkConfigForUpdates()
        #tk.enableRelativePlaceOptimization()
        if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_off_on_load"] or Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_off_on_load"]:
            if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_off_on_load"]: Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = False
            if Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_off_on_load"]: Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] = False
            Config.SETTINGS_CONFIG.save()
        MsgText.info("Creating GUI...")
        super().__init__(group=SG)
        MsgText.info("Loading Style...")
        if not os.path.exists(os.path.join(System.CONFIG_PATH)):
            os.mkdir(System.CONFIG_PATH)
            MsgText.warning("Folder does not exist! Creating folder: " + System.CONFIG_PATH)
        if not os.path.exists(os.path.join(System.CONFIG_PATH, "skyblock_save")):
            os.mkdir(os.path.join(System.CONFIG_PATH, "skyblock_save"))
            MsgText.warning("Folder does not exist! Creating folder: "+os.path.join(System.CONFIG_PATH, "skyblock_save"))
        if not os.path.exists(os.path.join(System.CONFIG_PATH, "skyblock_save", "auctionhouse")):
            os.mkdir(os.path.join(System.CONFIG_PATH, "skyblock_save", "auctionhouse"))
            MsgText.warning("Folder does not exist! Creating folder: " + os.path.join(System.CONFIG_PATH, "skyblock_save", "auctionhouse"))
        # load average_price_save.json
        LOAD_STYLE() # load DarkMode!
        IconLoader.loadIcons()
        self.requestedOnlyPage = None
        self.isShiftPressed = False
        self.isControlPressed = False
        self.isAltPressed = False
        self.lockInfoLabel = False
        self.isConfigLoadedFromFile = False
        self.keyPressHooks = []
        self.updateCurrentPageHook = None
        self.additionalItemInfoPage = ItemInfoPage(self)
        ## instantiate Pages ##
        MsgText.info("Creating MenuPages...")
        FeatureLoader.getInstance().loadFeatures(self)
        self.searchPage = SearchPage(self)
        self.loadingPage = LoadingPage(self)
        self.mainMenuPage = MainMenuPage(self)
        ## REGISTER FEATURES ##
        self.infoTopLevel = tk.Toplevel(self, SG)
        self.infoTopLevel.setTitle("Price Graph")
        self.infoTopLevel.setWindowSize(600, 600, True)
        self.infoPage = ItemInfoPage(self, self.infoTopLevel)
        def _onclose(e):
            e.setCanceled(True)
            self.infoTopLevel.hide()
        self.infoTopLevel.onCloseEvent(_onclose)
        self.infoTopLevel.hide()

        self.configureWindow()
        self.createGUI()
        self.loadingPage.openMenuPage()
        Thread(target=self._autoRequestAPI).start()
        Thread(target=self._updateInfoLabel).start()
        Thread(target=self.loadingPage.preLoad).start()
        if System.SYSTEM_TYPE == "WINDOWS": self.configureWindows()
    def _autoRequestAPI(self):
        started = False
        nextPage = 0
        timerBaz = time()
        timerAuc = time()
        diffTimer = time()
        MIN_DIFF = 1.5 #sek
        while True:
            sleep(.1)
            if self.loadingPage.loadingComplete and not started:
                started = True
                sleep(5)

            if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"]:
                if time()-timerBaz >= Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"]:
                    if time()-diffTimer < MIN_DIFF: continue
                    self.refreshAPIRequest("bazaar", force=True)
                    diffTimer = time()
                    timerBaz = time()
                    if API.SKYBLOCK_BAZAAR_API_PARSER is None: # if request fails -> auto request disabled
                        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = False
                        self.mainMenuPage.updateAutoRequestButton()

            if Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] and API.SKYBLOCK_AUCTION_API_PARSER is not None:
                if time() - timerAuc >= Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request_interval"]:
                    if time() - diffTimer < MIN_DIFF: continue
                    self.refreshAPIRequest("auction",
                                           fileNr=nextPage,
                                           force=True,
                                           useParser=API.SKYBLOCK_AUCTION_API_PARSER
                                           )
                    diffTimer = time()
                    timerAuc = time()
                    if API.SKYBLOCK_AUCTION_API_PARSER is None:  # if request fails -> auto request disabled
                        Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] = False
                        self.mainMenuPage.updateAutoRequestButton()
                    else:
                        pages:int = API.SKYBLOCK_AUCTION_API_PARSER.getPages()
                        if nextPage == pages:
                            nextPage = 0
                        else:
                            nextPage += 1
    def configureWindow(self):
        self.setMinSize(600, 600)
        self.setTitle("SkyBlockTools "+VERSION)
        self.setIcon(IconLoader.ICONS["icon"])
        self.bind(self.onKeyPress, tk.EventType.SHIFT_LEFT_DOWN, args=["isShiftPressed", True])
        self.bind(self.onKeyPress, tk.EventType.SHIFT_LEFT_UP, args=["isShiftPressed", False])

        self.bind(self.onKeyPress, tk.EventType.ALT_LEFT_DOWN, args=["isAltPressed", True])
        self.bind(self.onKeyPress, tk.EventType.ALT_LEFT_UP, args=["isAltPressed", False])

        self.bind(self.onKeyPress, tk.EventType.STRG_LEFT_DOWN, args=["isControlPressed", True])
        self.bind(self.onKeyPress, tk.EventType.STRG_LEFT_UP, args=["isControlPressed", False])

        self.bind(lambda:Thread(target=self.refreshAPIRequest, args=("all",)).start(), tk.EventType.hotKey(tk.FunctionKey.ALT, "F5"))
        self.bind(lambda:SettingsGUI.openSettings(self), tk.EventType.hotKey(tk.FunctionKey.ALT, "s"))

        self.bind(self.mainMenuPage.onScrollUp, tk.EventType.ARROW_UP)
        self.bind(self.mainMenuPage.onScrollDown, tk.EventType.ARROW_DOWN)
        self.bind(self.mainMenuPage.onScroll, tk.EventType.WHEEL_MOTION)
    def configureWindows(self):
        self.updateIdleTasks()
        self.hide()
        from ctypes import windll
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        hwnd = windll.user32.GetParent(self._get().winfo_id())
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self.hide()
        self._get().after(10, lambda:self._get().wm_deiconify())
        windll.shell32.SetCurrentProcessExplicitAppUserModelID('mycompany.myproduct.subproduct.version')
    def onKeyPress(self, e):
        setattr(self, e.getArgs(0), e.getArgs(1))
        for hook in self.keyPressHooks:
            hook()
    def createGUI(self):
        self.taskBar = tk.TaskBar(self, SG)
        self.taskBar_file = self.taskBar.createSubMenu("File")
        self.taskBar_api = self.taskBar.createSubMenu("API")

        tk.Button(self.taskBar_file, SG).setText("Save current Bazaar API-Data...").setCommand(self.saveAPIData)
        tk.Button(self.taskBar_file, SG).setText("Open Bazaar API-Data...").setCommand(self.openAPIData)
        self.taskBar_file.addSeparator()
        tk.Button(self.taskBar_file, SG).setText("Settings (Alt+s)").setCommand(lambda:SettingsGUI.openSettings(self))

        tk.Button(self.taskBar_api, SG).setText("Refresh all API Data...(Alt+F5)").setCommand(lambda:Thread(target=self.refreshAPIRequest, args=("all",)).start())
        self.taskBar_api.addSeparator()
        tk.Button(self.taskBar_api, SG).setText("Refresh Bazaar API Data...(Alt+F5)").setCommand(lambda:Thread(target=self.refreshAPIRequest, args=("bazaar",)).start())
        tk.Button(self.taskBar_api, SG).setText("Refresh Auction API Data...(Alt+F5)").setCommand(lambda:Thread(target=self.refreshAPIRequest, args=("auction",)).start())

        self.taskBar.create()
    def _updateInfoLabel(self):
        while True:
            sleep(5)
            if self.lockInfoLabel: continue
            updateBazaarInfoLabel(API.SKYBLOCK_BAZAAR_API_PARSER, self.isConfigLoadedFromFile)
            updateAuctionInfoLabel(API.SKYBLOCK_AUCTION_API_PARSER, self.isConfigLoadedFromFile)
    def saveAPIData(self):
        if API.SKYBLOCK_BAZAAR_API_PARSER is not None:
            path = tk.FileDialog.saveFile(self, "SkyBlockTools", types=[".json"])
            if not path.endswith(".json"): path += ".json"
            if os.path.exists(path):
                if not tk.SimpleDialog.askOkayCancel(self, "Are you sure you want to overwrite the file?", "SkyBlockTools"):
                    return
            js = JsonConfig.fromDict(API.SKYBLOCK_BAZAAR_API_PARSER.getRawData())
            js.path = path
            js.save()
    def openAPIData(self):
        path = tk.FileDialog.openFile(self, "SkyBlockTools", types=[".json"])
        if path is None:
            tk.SimpleDialog.askError(self, "Could not read config!")
            return
        if not os.path.exists(path):
            tk.SimpleDialog.askError(self, "Config file does not exist!")
            return
        data = JsonConfig.loadConfig(path, ignoreErrors=True)
        if type(data) == str:
            tk.SimpleDialog.askError(self, data)
            return
        conf = JsonConfig.loadConfig(os.path.join(System.CONFIG_PATH, "skyblock_save", "bazaar.json"), create=True)
        conf.setData(data)
        conf.save()
        API.SKYBLOCK_BAZAAR_API_PARSER = HypixelBazaarParser(data.getData())
        self.isConfigLoadedFromFile = True
        updateBazaarInfoLabel(API.SKYBLOCK_BAZAAR_API_PARSER, self.isConfigLoadedFromFile)
    def refreshAPIRequest(self, e, force=False, fileNr=None, useParser=None):
        self.requestedOnlyPage = fileNr
        if Constants.WAITING_FOR_API_REQUEST:
            tk.SimpleDialog.askError(self, "Another api request is still running!\nTry again later.")
            return
        if not self.loadingPage.loadingComplete:
            tk.SimpleDialog.askError(self, "Software is not fully initialized yet!\nTry again later.")
            return
        if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] and not force:
            tk.SimpleDialog.askError(self, "Could not request!\nDisable auto request first!")
            return
        if Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] and not force:
            tk.SimpleDialog.askError(self, "Could not request!\nDisable auto request first!")
            return
        self.lockInfoLabel = True
        Constants.WAITING_FOR_API_REQUEST = True
        self.isConfigLoadedFromFile = False

        sleep(.3)
        if e == "all" or e == "bazaar":
            BILG.executeCommand("setFg", "white")
            BILG.executeCommand("setText", "Requesting Hypixel-API...")
            API.SKYBLOCK_BAZAAR_API_PARSER = requestBazaarHypixelAPI(self,
                                                                     Config,
                                                                     saveTo=os.path.join(System.CONFIG_PATH, "skyblock_save", "bazaar.json"))
            updateBazaarInfoLabel(API.SKYBLOCK_BAZAAR_API_PARSER, self.isConfigLoadedFromFile)
        if e == "all" or e == "auction":
            AILG.executeCommand("setFg", "white")
            AILG.executeCommand("setText", "Requesting Hypixel-API...")
            API.SKYBLOCK_AUCTION_API_PARSER = requestAuctionHypixelAPI(self,
                                                                       Config,
                                                                       infoLabel=AILG,
                                                                       saveTo=os.path.join(System.CONFIG_PATH, "skyblock_save", "auctionhouse"),
                                                                       fileNr=fileNr,
                                                                       useParser=useParser)
            updateAuctionInfoLabel(API.SKYBLOCK_AUCTION_API_PARSER, self.isConfigLoadedFromFile)
        updateBazaarAnalyzer()
        Constants.WAITING_FOR_API_REQUEST = False
        self.lockInfoLabel = False
        if self.updateCurrentPageHook is not None:
            self.runTask(self.updateCurrentPageHook).start()
        self.runTask(self.mainMenuPage.getToolFromClassName("ItemPriceTrackerPage").onAPIUpdate).start()
    def showItemInfo(self, page:CustomPage, itemID:str):
        self.infoPage.onShow(itemName=itemID, selectMode="hour", ignoreHook=True)
        self.infoTopLevel.show()


        # old version:      page.openNextMenuPage(self.additionalItemInfoPage, itemName=itemID)

if __name__ == '__main__':
    registerPath(__file__)
    determineSystem()
    testForConfigFolder()
    Config.load() # load Settings
    initClipBoard()
    loadConfigs()

    Title().print("Sky Block Tools", "green")
    window = Window()
    MsgText.info("GUI opened successfully!")
    window.mainloop()
    os._exit(0)