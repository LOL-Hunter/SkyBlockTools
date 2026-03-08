import os
from time import time

import tksimple as tk

from .bazaarAnalyzer import updateBazaarAnalyzer
from .constants import (
    Path,
    System,
    FURNITURE_ITEMS,
    STYLE_GROUP as SG,
    API,
    Color,
    BazaarItemID,
    AuctionItemID,
)
from .image import IconLoader
from .logger import MsgText
from .settings import SettingsGUI, Config
from .skyMisc import (
    requestAuctionHypixelAPI,
    requestItemHypixelAPI,
    requestBazaarHypixelAPI,
    updateAuctionInfoLabel,
    updateBazaarInfoLabel,
    search,
    _map,
    updateItemLists,
    addPetsToAuctionHouse
)
from .widgets import CompleterEntry, CustomPage, CustomMenuPage
from .featureLoader import FeatureLoader

# Info/Content Pages
class SearchPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, SG)
        self.master = master

        ## run properties ##
        self.searchInput = [BazaarItemID, AuctionItemID]
        self.msg = "Search: (At least tree characters)"
        self.nextPage = None
        self.forceType = ""
        ####################
        self.setPageTitle(self.msg)

        self.entry = CompleterEntry(self)
        self.entry.bind(self.clear, tk.EventType.RIGHT_CLICK)
        self.entry.onSelectEvent(self.onSelectEvent)
        self.entry.onUserInputEvent(self.onUserInputEvent)
        self.entry.placeRelative(centerX=True, fixHeight=30, fixWidth=300, fixY=40)
    def clear(self):
        self.entry.closeListbox()
        self.entry.clear()
    def onUserInputEvent(self, e):
        value = self.entry.getValue()
        _searchInput = self.searchInput
        return search(self.searchInput, value, minLength=3)
    def onSelectEvent(self, e):
        value = e.getValue()
        if value is not None and value != "None":
            value = value.split(" - ")[0]
            value = value.replace(" ", "_")
            self.openNextMenuPage(self.nextPage, itemName=value.upper())
    def onShow(self, **kwargs):
        if "next_page" in kwargs.keys() and kwargs["next_page"] != self.nextPage:
            self.entry.clear()
        self.nextPage = kwargs["next_page"] if "next_page" in kwargs.keys() else self.nextPage
        self.searchInput = kwargs["input"] if "input" in kwargs.keys() else self.searchInput
        self.msg = kwargs["msg"] if "msg" in kwargs.keys() else self.msg
        self.forceType = kwargs["forceType"] if "forceType" in kwargs.keys() else self.forceType
        self.setPageTitle(self.msg)
        self.placeRelative()
        self.entry.setFocus()
# Menu Pages
class MainMenuPage(CustomMenuPage):
    def __init__(self, master):
        super().__init__(master, showBackButton=False, showTitle=False, homeScreen=True, showHomeButton=False)
        self.tools = FeatureLoader.getInstance().getTools()
        self.toolsDict = {tool.__class__.__name__:tool for tool in self.tools}
        self.visibleTools = []
        self.scrollFramePosY = 0
        self.activeButtons = []
        self.image = tk.PILImage.loadImage(os.path.join(Path.IMAGES, "logo.png"))
        self.image.resize(.2)
        self.image.preRender()
        self.title = tk.Label(self, SG).setImage(self.image).placeRelative(centerX=True, fixHeight=self.image.getHeight(), fixWidth=self.image.getWidth(), fixY=20)

        self.playerHead1 = tk.PILImage.loadImage(os.path.join(Path.IMAGES, "lol_hunter.png")).resizeTo(32, 32).preRender()
        self.playerHead2 = tk.PILImage.loadImage(os.path.join(Path.IMAGES, "glaciodraco.png")).resizeTo(32, 32).preRender()

        tk.Label(self, SG).setText("Made by").placeRelative(stickRight=True, stickDown=True, fixHeight=25, fixWidth=100, changeY=-40, changeX=-25)
        def _openSettings():
            SettingsGUI.openSettings(self.master)
        tk.Button(self, SG).setImage(IconLoader.ICONS["settings"]).setCommand(_openSettings).placeRelative(stickDown=True, fixWidth=40, fixHeight=40).setStyle(tk.Style.FLAT)

        self.pl1L = tk.Label(self, SG).setImage(self.playerHead1)
        self.pl2L = tk.Label(self, SG).setImage(self.playerHead2)
        self.pl1L.attachToolTip("LOL_Hunter", waitBeforeShow=0, group=SG)
        self.pl2L.attachToolTip("glaciodraco", waitBeforeShow=0, group=SG)
        self.pl1L.placeRelative(stickRight=True, stickDown=True, fixHeight=self.playerHead1.getHeight(), fixWidth=self.playerHead1.getHeight(), changeY=-10, changeX=-10)
        self.pl2L.placeRelative(stickRight=True, stickDown=True, changeY=-self.playerHead1.getWidth()-10*2, fixHeight=self.playerHead1.getHeight(), fixWidth=self.playerHead1.getHeight(), changeX=-10)

        self.search = tk.Entry(self, SG)
        self.search.setFont(16)
        self.search.setFocus()
        self.search.onUserInputEvent(self.onSearch)
        self.search.setBorderWidth(3)
        self.search.bind(self.onSearchClick, tk.EventType.LEFT_CLICK)
        self.search.bind(self.search.clear, tk.EventType.LEFT_CLICK)
        self.search.bind(self.onReturn, tk.EventType.RETURN)
        self.search.setStyle(tk.Style.RIDGE)
        self.search.placeRelative(fixY=200, fixWidth=300, fixHeight=50, centerX=True)

        self.noSearchInput = tk.Label(self, SG)
        self.noSearchInput.setText("Type here to search")
        self.noSearchInput.setFg(tk.Color.rgb(69, 67, 67))
        self.noSearchInput.setFont(16)
        self.noSearchInput.bind(self.onSearchClick, tk.EventType.LEFT_CLICK)
        self.noSearchInput.setTextOrientation(tk.Anchor.LEFT)
        self.noSearchInput.placeRelative(fixY=200+12, fixWidth=290, fixHeight=25, centerX=True)

        self.autoUpdateBazzarActive = tk.Button(self, SG)
        self.autoUpdateBazzarActive.attachToolTip(
            "Bazaar Data Auto Request:\n\nUse this option to toggle automatic requests.\nRequest interval can be changed in Settings.\nThis is required to track item prices\nin real time.",
            group=SG
        )
        self.autoUpdateBazzarActive.setStyle(tk.Style.FLAT)
        self.autoUpdateBazzarActive.setFont(15)
        self.autoUpdateBazzarActive.setCommand(self.toggleAutoBazzarRequest)
        self.autoUpdateBazzarActive.setFg("green" if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] else "red")
        self.autoUpdateBazzarActive.setText("\u27F3 Bazzar")
        self.autoUpdateBazzarActive.placeRelative(fixHeight=25, fixWidth=100)

        self.autoUpdateAuctActive = tk.Button(self, SG)
        self.autoUpdateAuctActive.attachToolTip(
            "Auction Data Auto Request:\n\nUse this option to toggle automatic requests.\nRequest interval can be changed in Settings.\nThis is required to track item prices\nin real time.",
            group=SG
        )
        self.autoUpdateAuctActive.setStyle(tk.Style.FLAT)
        self.autoUpdateAuctActive.setFont(15)
        self.autoUpdateAuctActive.setCommand(self.toggleAutoAuctRequest)
        self.autoUpdateAuctActive.setFg("green" if Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] else "red")
        self.autoUpdateAuctActive.setText("\u27F3 Auction")
        self.autoUpdateAuctActive.placeRelative(fixHeight=25, fixWidth=100, changeY=25)

        self.scrollFrame = tk.Frame(self, SG)
        self.scrollFrame.bind(self.onPlaceRelative, tk.EventType.CUSTOM_RELATIVE_UPDATE)
        self.buttonFrame = tk.Frame(self.scrollFrame, SG)
        self.scrollFrame.placeRelative(fixY=250, fixWidth=300, centerX=True, fixHeight=300)

        self.scrollBarFrame = tk.Frame(self, SG).setBg(Color.COLOR_WHITE)
        self.scrollLabel = tk.Label(self.scrollBarFrame, SG)
    def getToolFromClassName(self, n:str):
        if n in self.toolsDict.keys():
            return self.toolsDict[n]
    def toggleAutoBazzarRequest(self):
        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = not Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"]
        Config.SETTINGS_CONFIG.save()
        self.updateAutoRequestButton()
    def toggleAutoAuctRequest(self):
        Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] = not Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"]
        Config.SETTINGS_CONFIG.save()
        self.updateAutoRequestButton()
    def updateAutoRequestButton(self):
        self.autoUpdateBazzarActive.setFg("green" if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] else "red")
        self.autoUpdateAuctActive.setFg("green" if Config.SETTINGS_CONFIG["auto_api_requests"]["auction_auto_request"] else "red")
    def onSearchClick(self):
        self.noSearchInput.placeForget()
    def clearSearch(self):
        self.search.clear()
        self.noSearchInput.placeRelative(fixY=200 + 12, fixWidth=290, fixHeight=25, centerX=True)
        self.placeButtons(self.tools)
    def placeButtons(self, tools):
        if tools == self.visibleTools: return
        self.visibleTools = tools.copy()
        for i in self.activeButtons:
            i.destroy()
        self.activeButtons.clear()
        for i, tool in enumerate(tools):
            self.activeButtons.append(tk.Button(self.buttonFrame, SG).setFont(16).setText(tool.getButtonText()).setCommand(self._run, args=[tool]).placeRelative(centerX=True, fixY=50 * i, fixWidth=300, fixHeight=50))
        if not len(tools):
            i = 0
            self.activeButtons.append(tk.Label(self.buttonFrame, SG).setFont(16).setText("There is no tool with this Name!").placeRelative(centerX=True, fixY=50 * i, fixWidth=300, fixHeight=50))
        self.buttonFrame.place(0, 0, 300, 50 * (i+1))

        if self.buttonFrame.getHeight() < self.scrollFrame.getHeight():
            self.scrollLabel.place(2, 2, 20-4, self.scrollFrame.getHeight()-4)
        else:
            self.scrollLabel.place(2, 2, 20 - 4, 50)
    @tk.runWatcherDec
    def onPlaceRelative(self, e):
        if not hasattr(self, "scrollBarFrame"): return
        x, y, width, height = e.getValue()
        self.scrollBarFrame.place(x+width+3, y, 20, height)
    def onScrollUp(self):
        self.onScroll(1)
    def onScrollDown(self):
        self.onScroll(-1)
    def onScroll(self, e:tk.Event|int, speed=10):
        if not self.isActive(): return # if this page is not visible
        if self.buttonFrame.getHeight() < self.scrollFrame.getHeight(): return
        delta = e.getScrollDelta() if isinstance(e, tk.Event) else e
        if delta < 0: # down
            if not self.scrollFrame.getHeight() >= self.buttonFrame.getHeight()-abs(self.scrollFramePosY):
                self.scrollFramePosY -= speed
        else: # up
            if not self.buttonFrame.getPosition().getY() >= 0:
                self.scrollFramePosY += speed

        scrollYRange = self.scrollFrame.getHeight() - 50 - 4

        scrollY = _map(abs(self.scrollFramePosY),
                       0,
                       self.buttonFrame.getHeight()-self.scrollFrame.getHeight(),
                       0,
                       scrollYRange)

        self.scrollLabel.place(2, scrollY+2, 20 - 4, 50)
        self.buttonFrame.place(0, self.scrollFramePosY, 300, 50*len(self.tools))
    def onReturn(self):
        if len(self.visibleTools) == 1:
            self.openNextMenuPage(self.visibleTools[0])
    def onSearch(self):
        if self.search.getValue() == "":
            self.noSearchInput.placeRelative(fixY=200+12, fixWidth=290, fixHeight=25, centerX=True)
        else:
            self.onSearchClick()
        tools = []
        for tool in self.tools:
            name = tool._buttonText.lower()
            searchValue = self.search.getValue().lower()
            if searchValue in name:
                tools.append(tool)
        self.placeButtons(tools)
    def onShow(self):
        self.scrollFramePosY = 0 # reset scroll position
        self.placeRelative()
        self.clearSearch()
        self.search.setFocus()
class LoadingPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, showTitle=False, showHomeButton=False, showBackButton=False, showInfoLabel=False)
        self.loadingComplete = False
        self.master = master
        self.image = tk.PILImage.loadImage(os.path.join(Path.IMAGES, "logo.png"))
        self.image.resize(.3)
        self.image.preRender()
        self.title = tk.Label(self, SG).setImage(self.image).placeRelative(centerX=True, fixHeight=self.image.getHeight(), fixWidth=self.image.getWidth(), fixY=40)

        self.processBar = tk.Progressbar(self, SG)
        self.processBar.placeRelative(fixHeight=25, fixY=300, changeX=+50, changeWidth=-100)

        self.info = tk.Label(self, SG).setFont(16)
        self.info.placeRelative(fixHeight=25, fixY=340, changeX=+50, changeWidth=-100)
    def preLoad(self):
        if SettingsGUI.checkAPIKeySet(self.master, self.load): return
        self.load()
    def load(self):
        itemAPISuccessful = False
        bazaarAPISuccessful = False
        actionAPISuccessful = False
        msgs = ["Applying Settings...", "Fetching Hypixel Bazaar API...", "Checking Hypixel Item API...", "Creating Dynamic Item lists...", "Fetching Hypixel Auction API...", "Finishing Up..."]
        self.processBar.setValues(len(msgs))
        for i, msg in enumerate(msgs):
            self.processBar.addValue()
            if i == 0: # fetch Bazaar API
                self.info.setText(msg)
                self.processBar.setAutomaticMode()

                path = Config.SETTINGS_CONFIG["constants"]["hypixel_bazaar_config_path"]
                bazaarConfPath = os.path.join(System.CONFIG_PATH, "skyblock_save", "bazaar.json")

                if not os.path.exists(path) and path != "":
                    tk.SimpleDialog.askWarning(self.master, "Could not read data from API-Config.\nConfig does not exist!\nSending request to Hypixel-API...")
                    path = None
                if path == "" or None: # load last config
                    path = None
                    if os.path.exists(bazaarConfPath):
                        path = bazaarConfPath
                t = time()
                API.SKYBLOCK_BAZAAR_API_PARSER = requestBazaarHypixelAPI(self.master, Config, path=path, saveTo=bazaarConfPath)
                MsgText.info(f"Loading HypixelBazaarConfig took {round(time()-t, 2)} Seconds!")
                if API.SKYBLOCK_BAZAAR_API_PARSER is not None: bazaarAPISuccessful = True

                updateBazaarInfoLabel(API.SKYBLOCK_BAZAAR_API_PARSER, path is not None)
                self.master.isConfigLoadedFromFile = path is not None


                self.processBar.setNormalMode()
                self.processBar.setValue(i+1)
            elif i == 1: # check/fetch Item API
                self.info.setText(msg)

                path = os.path.join(System.CONFIG_PATH, "skyblock_save", "hypixel_item_config.json")

                if not SettingsGUI.checkItemConfigExist():
                    tk.SimpleDialog.askWarning(self.master, "Could not read data from Item-API-Config.\nConfig does not exist!\nCreating new...")
                    API.SKYBLOCK_ITEM_API_PARSER = requestItemHypixelAPI(self.master, Config, saveTo=path)
                else:
                    t = time()
                    API.SKYBLOCK_ITEM_API_PARSER = requestItemHypixelAPI(self.master, Config, path=path)
                    MsgText.info(f"Loading HypixelItemConfig took {round(time()-t, 2)} Seconds!")
                if API.SKYBLOCK_ITEM_API_PARSER is not None:
                    FURNITURE_ITEMS.clear()
                    for item in API.SKYBLOCK_ITEM_API_PARSER.getItems():
                        if item.isFurniture():
                            FURNITURE_ITEMS.append(item.getID())
                    itemAPISuccessful = True
                self.master.isConfigLoadedFromFile = path is not None

                self.processBar.setValues(len(msgs))
                self.processBar.setNormalMode()
                self.processBar.setValue(i + 1)
            elif i == 2: # build item lists
                if not itemAPISuccessful or not bazaarAPISuccessful:
                    MsgText.error("Could not parse Items!")
                    continue
                self.info.setText(msg)
                t = time()
                updateItemLists()
                MsgText.info(f"Building ItemList took {round(time()-t, 2)} Seconds!")

                self.master.runTask(updateBazaarAnalyzer).start()

                itemTracker = self.master.mainMenuPage.getToolFromClassName("ItemPriceTrackerPage")
                if itemTracker is not None:
                    itemTracker.disableNotifications()
                    self.master.runTask(itemTracker.onAPIUpdate).start()

                self.processBar.setValues(len(msgs))
                self.processBar.setNormalMode()
                self.processBar.setValue(i + 1)
            elif i == 3: # fetch Auction API
                self.info.setText(msg)

                path = Config.SETTINGS_CONFIG["constants"]["hypixel_auction_config_path"]
                auctConfPath = os.path.join(System.CONFIG_PATH, "skyblock_save", "auctionhouse")

                if not os.path.exists(path) and path != "":
                    tk.SimpleDialog.askWarning(self.master,"Could not read data from API-Config.\nConfig does not exist!\nSending request to Hypixel-API...")
                    path = None
                if path == "":
                    path = None
                    if os.path.exists(auctConfPath):
                        path = auctConfPath
                t = time()
                API.SKYBLOCK_AUCTION_API_PARSER = requestAuctionHypixelAPI(self.master,
                                                                           Config,
                                                                           path=path,
                                                                           progBar=self.processBar,
                                                                           infoLabel=self.info,
                                                                           saveTo=os.path.join(System.CONFIG_PATH, "skyblock_save", "auctionhouse"))
                pages = len(os.listdir(os.path.join(System.CONFIG_PATH, "skyblock_save", "auctionhouse")))
                MsgText.info(f"Loading {pages} Auction-Pages took {round(time()-t, 2)} Seconds!")
                if API.SKYBLOCK_AUCTION_API_PARSER is not None: actionAPISuccessful = True
                updateAuctionInfoLabel(API.SKYBLOCK_AUCTION_API_PARSER, path is not None)
                self.master.isConfigLoadedFromFile = path is not None

                self.processBar.setValues(len(msgs))
                self.processBar.setNormalMode()
                self.processBar.setValue(i + 1)
            elif i == 4:
                self.info.setText(msg)
                if actionAPISuccessful:
                    t = time()
                    amount = addPetsToAuctionHouse()
                    MsgText.info(f"Registering {amount} Pets in ItemList took {round(time()-t, 2)} Seconds!")
                else:
                    MsgText.warning("Could not register Pets in ItemList!")
                self.processBar.setValues(len(msgs))
                self.processBar.setNormalMode()
                self.processBar.setValue(i + 1)
            else:
                self.info.setText(msg)
                #sleep(.2)
        self.placeForget()
        self.master.mainMenuPage.openMenuPage()
        self.loadingComplete = True
    def onShow(self, **kwargs):
        self.placeRelative()
        #self.api.startAPIRequest()