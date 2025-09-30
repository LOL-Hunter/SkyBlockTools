# -*- coding: iso-8859-15 -*-
import os
from threading import Thread
from time import time, sleep
from typing import List
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import tksimple as tk

from core.analyzer import getPlotData
from core.bazaarAnalyzer import updateBazaarAnalyzer
from core.constants import (
    VERSION,
    Path,
    System,
    FURNITURE_ITEMS,
    LOAD_STYLE,
    STYLE_GROUP as SG,
    BAZAAR_INFO_LABEL_GROUP as BILG,
    AUCT_INFO_LABEL_GROUP as AILG,
    API,
    Color,
    Constants,
    BazaarItemID,
    AuctionItemID,
    ConfigFile
)
from core.hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException
from core.hyPI.hypixelAPI.loader import HypixelBazaarParser
from core.hyPI.parser import BazaarHistoryProduct
from core.widgets import CompleterEntry, CustomPage, CustomMenuPage, APIRequest
from core.image import IconLoader
from core.jsonConfig import JsonConfig
from core.logger import MsgText, Title
from core.settings import SettingsGUI, Config, checkConfigForUpdates, testForConfigFolder
from core.skyMath import (
    getPlotTicksFromInterval,
    parsePrizeList,
    getMedianExponent,
    getFlattenList,
    getMedianFromList
)
from core.skyMisc import (
    requestAuctionHypixelAPI,
    requestItemHypixelAPI,
    requestBazaarHypixelAPI,
    updateAuctionInfoLabel,
    updateBazaarInfoLabel,
    modeToBazaarAPIFunc,
    parsePrizeToStr,
    determineSystem,
    registerPath,
    search,
    _map,
    updateItemLists,
    addPetsToAuctionHouse,
    throwNoAPIKeyException,
    throwAPIConnectionException,
    throwAPITimeoutException
)

from MayorInfo import MayorInfoPage
from LongTimeFlipHelper import LongTimeFlipHelperPage
from ItemPriceTracker import ItemPriceTrackerPage
from PestProfit import PestProfitPage
from BinSniper import BinSniperPage
from BazaarFlipProfit import BazaarFlipProfitPage
from AlchemyXPCalculator import AlchemyXPCalculatorPage
from BazaarCraftProfit import BazaarCraftProfitPage
from AuctionHouse import AuctionHousePage
from ForgeProfit import ForgeProfitTrackerPage
from AccessoryBuyHelper import AccessoryBuyHelperPage
from MedalProfit import MedalTransferProfitPage
from MagicFindCalculator import MagicFindCalculatorPage
from BazaarToAuctionHouseFlip import BazaarToAuctionHouseFlipProfitPage
from ComposterProfit import ComposterProfitPage
from BoosterCookieBitsProfit import BoosterCookieBitsProfit
from EnchantingBookBazaarProfit import EnchantingBookBazaarProfitPage
from EnchantingBookBazaarCheapest import EnchantingBookBazaarCheapestPage

# Info/Content Pages
class ItemInfoPage(CustomPage):
    def __init__(self, master, tkMaster=None):
        showAddBtns = True if tkMaster is None else False
        super().__init__(master if tkMaster is None else tkMaster, pageTitle="Info of Item: []", buttonText="Bazaar Item Info", showBackButton=showAddBtns, showHomeButton=showAddBtns)
        self.master: Window = master
        self.selectedMode = "hour"
        self.selectedItem = None
        self.plot2 = None
        self.currentHistoryData = None
        self.latestHistoryDataHour = None
        self.master.keyPressHooks.append(self.onKeyPressed)  # register keyPressHook

        self.lf = tk.LabelFrame(self.contentFrame, SG)
        self.lf.setText("Plot:")
        self.timeRangeBtns = [
            tk.Button(self.lf, SG).setCommand(self.changePlotType, args=["hour"]).setText("Last hour").placeRelative(fixWidth=150, changeHeight=-20).setStyle(tk.Style.SUNKEN),
            tk.Button(self.lf, SG).setCommand(self.changePlotType, args=["day"]).setText("Last day").placeRelative(fixWidth=150, changeHeight=-20, fixX=150),
            tk.Button(self.lf, SG).setCommand(self.changePlotType, args=["week"]).setText("Last Week").placeRelative(fixWidth=150, changeHeight=-20, fixX=300),
            tk.Button(self.lf, SG).setCommand(self.changePlotType, args=["all"]).setText("All").placeRelative(fixWidth=150, changeHeight=-20, fixX=450, changeWidth=-5)
        ]
        self.lf.placeRelative(centerX=True, fixY=0, fixHeight=40, fixWidth=600)

        self.toolLf = tk.LabelFrame(self.contentFrame, SG).setText("Tools")

        self.dataText = tk.Text(self.toolLf, SG, readOnly=True).placeRelative(changeHeight=-115, changeWidth=-5, fixY=0)

        self.optionLf = tk.LabelFrame(self.toolLf, SG)
        self.chSell = tk.Checkbutton(self.optionLf, SG).setText("Sell-Price").setSelected().placeRelative(changeWidth=-5, fixHeight=23, xOffsetRight=50, fixY=0).setTextOrientation().onSelectEvent(self.onPlotSettingsChanged)
        self.chBuy = tk.Checkbutton(self.optionLf, SG).setText("Buy-Price").setSelected().placeRelative(changeWidth=-5, xOffsetLeft=50,  fixHeight=23, fixY=0).setTextOrientation().onSelectEvent(self.onPlotSettingsChanged)
        self.chSellV = tk.Checkbutton(self.optionLf, SG).setText("Sell-Volume").placeRelative(changeWidth=-5, fixHeight=23, xOffsetRight=50, fixY=23).setTextOrientation().onSelectEvent(self.onPlotSettingsChanged)
        self.chBuyV = tk.Checkbutton(self.optionLf, SG).setText("Buy-Volume").placeRelative(changeWidth=-5, fixHeight=23, xOffsetLeft=50, fixY=23).setTextOrientation().onSelectEvent(self.onPlotSettingsChanged)
        self.filterManipulation = tk.Checkbutton(self.optionLf, SG).setText("Filter-Manipulation").placeRelative(changeWidth=-5, fixHeight=23, fixY=23*2).setTextOrientation().onSelectEvent(self.onPlotSettingsChanged)

        self.optionLf.placeRelative(stickDown=True, fixHeight=105, changeWidth=-5, changeY=-20)

        self.toolLf.placeRelative(fixY=50, stickRight=True, fixWidth=200, fixX=40)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.plot:Axes = self.figure.add_subplot(111)

        self.plotWidget = tk.MatPlotLibFigure(self.contentFrame, self.figure, toolBar=True)

        self.plotWidget.placeRelative(fixY=50, centerX=True, changeWidth=-200)

        self.api = APIRequest(self, self._getTkMaster())
        self.api.setRequestAPIHook(self.requestAPIHook)
    def updatePlot(self):
        ts = self.currentHistoryData["time_stamps"]
        bp = self.currentHistoryData["past_buy_prices"]
        sp = self.currentHistoryData["past_sell_prices"]
        bv = self.currentHistoryData["past_buy_volume"]
        sv = self.currentHistoryData["past_sell_volume"]
        if ts is None: return #no data available
        pricePref = self.currentHistoryData["price_prefix"]
        volPref = self.currentHistoryData["volume_prefix"]

        # if flatten is selected -> take flatten prices
        if self.filterManipulation.getState():
            bp = self.currentHistoryData["past_flatten_buy_prices"]
            sp = self.currentHistoryData["past_flatten_sell_prices"]

        self.plot.clear()
        if self.plot2 is not None:
            self.plot2.clear()
            self.plot2.remove()
            self.plot2 = None
        if self.chBuy.getState(): self.plot.plot(ts, bp, label="Buy Price", color="red")
        if self.chSell.getState(): self.plot.plot(ts, sp, label="Sell Price", color="green")

        if not self.chSell.getState() and not self.chBuy.getState() and not self.chBuyV.getState() and not self.chSellV.getState():
            self.plot.clear()
            return

        self.plot.set_title("Price over all available Data." if self.selectedMode == "all" else f"Price over the last {self.selectedMode.capitalize()}")
        self.plot.set_xlabel("Time in h")
        self.plot.set_ylabel(f"Price in {pricePref} coins")

        if self.chBuyV.getState() or self.chSellV.getState():
            self.plot2:Axes = self.plot.twinx()
            self.plot2.set_ylabel(f"Volume in {volPref}")

            if self.chBuyV.getState(): self.plot2.plot(ts, bv, label="Buy Volume", color="blue")
            if self.chSellV.getState(): self.plot2.plot(ts, sv, label="Sell Volume", color="orange")

            self.plot2.legend()

        self.plot.tick_params(axis='x', labelrotation=90)
        self.plot.set_xticks(getPlotTicksFromInterval(ts, 10))
        self.plot.legend()
        self.figure.canvas.draw_idle()  # update Widget!
    def updateInfoList(self):
        if self.latestHistoryDataHour is None: return

        if self.master.isShiftPressed:
            amount = 64
        else:
            amount = 1

        latestBazaarHistObj:BazaarHistoryProduct = self.latestHistoryDataHour["history_object"].getTimeSlots()[0]
        latestTimestamp:str = self.latestHistoryDataHour['time_stamps'][-1] # format -> '%d-%m-%Y-(%H:%M:%S)'

        bp = latestBazaarHistObj.getBuyPrice()
        sp = latestBazaarHistObj.getSellPrice()
        bv = latestBazaarHistObj.getBuyVolume()
        sv = latestBazaarHistObj.getSellVolume()

        bp = bp if bp is not None else 0
        sp = sp if sp is not None else 0
        bv = bv if bv is not None else 0
        sv = sv if sv is not None else 0

        # if the manipulation filter is active that values are used
        if self.filterManipulation.getState():
            bpm = getMedianFromList(self.currentHistoryData['past_flatten_buy_prices'])
            spm = getMedianFromList(self.currentHistoryData['past_flatten_sell_prices'])
            mPref = self.currentHistoryData["flatten_price_prefix"] # get median prefix for flatten mode
        else:
            bpm = getMedianFromList(self.currentHistoryData['past_buy_prices'])
            spm = getMedianFromList(self.currentHistoryData['past_sell_prices'])
            mPref = self.currentHistoryData["price_prefix"]

        out = f"§c== Info ==\n"
        out += f"§yMeasured-At:\n  §y{latestTimestamp.split('-')[-1].replace('(', '').replace(')', '')}\n\n"
        out += f"§c== Price x{amount}==\n"
        out += f"§rInsta-Buy-Price:\n§r  {parsePrizeToStr(bp * amount)}\n"
        out += f"§gInsta-Sell-Price:\n§g  {parsePrizeToStr(sp * amount)}\n\n"
        out += f"§c== Average-Price ==\n(over last {self.selectedMode})\n"
        out += f"§rAverage-Buy-Price:\n§r  {str(round(bpm, 2))} {mPref} coins\n"
        out += f"§gAverage-Sell-Price:\n§g  {str(round(spm, 2))} {mPref} coins\n\n"
        out += f"§c== Volume ==\n"
        out += f"§rInsta-Buy-Volume:\n§r  {parsePrizeToStr(bv)}\n"
        out += f"§gInsta-Sell-Volume:\n§g  {parsePrizeToStr(sv)}\n"
        self.dataText.setStrf(out)
    def _flattenPrices(self, bp, sp):
        bp = getFlattenList(bp)
        sp = getFlattenList(sp)

        # recalculate buy/sell price Prefix from flatten List
        exp, flatPref = getMedianExponent(bp + sp)
        fbp = parsePrizeList(bp, exp)
        fsp = parsePrizeList(sp, exp)
        return fbp, fsp, flatPref
    def requestAPIHook(self):
        # api request
        try:
            self.currentHistoryData = getPlotData(self.selectedItem, modeToBazaarAPIFunc(self.selectedMode))
        except APIConnectionError as e:
            throwAPIConnectionException(
                source="SkyCoflnet",
                master=self.master,
                event=e
            )
            return None
        except NoAPIKeySetException as e:
            throwNoAPIKeyException(
                source="SkyCoflnet",
                master=self.master,
                event=e
            )
            return None
        except APITimeoutException as e:
            throwAPITimeoutException(
                source="SkyCoflnet",
                master=self.master,
                event=e
            )
            return None

        #flatten prices
        fbp, fsp, flatPref = self._flattenPrices(self.currentHistoryData["past_raw_buy_prices"], self.currentHistoryData["past_raw_sell_prices"])
        self.currentHistoryData["past_flatten_buy_prices"] = fbp
        self.currentHistoryData["past_flatten_sell_prices"] = fsp
        self.currentHistoryData["flatten_price_prefix"] = flatPref

        # if mode == "hour" take newest as "latestHistory"
        if self.selectedMode == "hour": self.latestHistoryDataHour = self.currentHistoryData

        #update values on widgets
        self.updatePlot()
        self.updateInfoList()
    def onKeyPressed(self):
        self.updateInfoList()
    def onPlotSettingsChanged(self):
        self.updatePlot()
        self.updateInfoList()
    def changePlotType(self, e:tk.Event):
        for i in self.timeRangeBtns:
            i.setStyle(tk.Style.RAISED)
        e.getWidget().setStyle(tk.Style.SUNKEN)
        self.selectedMode = e.getArgs(0)
        self.api.startAPIRequest()
    def onShow(self, **kwargs):
        if "ignoreHook" not in kwargs.keys() or not kwargs["ignoreHook"]:
            self.master.updateCurrentPageHook = None  # hook to update tv on new API-Data available
        for i in self.timeRangeBtns:
            i.setStyle(tk.Style.RAISED)
        self.timeRangeBtns[0].setStyle(tk.Style.SUNKEN)
        if "selectMode" in kwargs.keys():
            self.selectedMode = kwargs["selectMode"]
        else:
            self.selectedMode = "hour"
        self.setPageTitle(f"Info of Item: [{kwargs['itemName']}]")
        self.selectedItem = kwargs['itemName']
        self.placeRelative()
        self.api.startAPIRequest()
    # custom! with search
    def customShow(self, page):
        page.openNextMenuPage(self.master.searchPage,
                         input=[BazaarItemID],
                         msg="Search in Bazaar: (At least tree characters)",
                         next_page=self)
class SearchPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, SG)
        self.master:Window = master

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
    def __init__(self, master, tools:List[CustomMenuPage | CustomPage]):
        super().__init__(master, showBackButton=False, showTitle=False, homeScreen=True, showHomeButton=False)
        self.tools = tools
        self.toolsDict = {tool.__class__.__name__:tool for tool in tools}
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
        self.search.setStyle(tk.Style.RIDGE)
        self.search.bind(self.search.clear, tk.EventType.LEFT_CLICK)
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
        self.master:Window = master
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
                self.master.runTask(self.master.mainMenuPage.getToolFromClassName("ItemPriceTrackerPage").disableNotifications().onAPIUpdate).start()

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
        ConfigFile.AVERAGE_PRICE = JsonConfig.loadConfig(os.path.join(System.CONFIG_PATH, "skyblock_save", "average_price_save.json"), create=True)
        LOAD_STYLE() # load DarkMode!
        IconLoader.loadIcons()
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
        self.searchPage = SearchPage(self)
        self.loadingPage = LoadingPage(self)

        self.mainMenuPage = MainMenuPage(self, [
                LongTimeFlipHelperPage(self),
                ItemPriceTrackerPage(self),
                PestProfitPage(self),
                MayorInfoPage(self),
                BinSniperPage(self),
                BazaarFlipProfitPage(self),
                AlchemyXPCalculatorPage(self),
                BazaarCraftProfitPage(self),
                AuctionHousePage(self),
                AccessoryBuyHelperPage(self),
                ForgeProfitTrackerPage(self),
                MedalTransferProfitPage(self),
                MagicFindCalculatorPage(self),
                ItemInfoPage(self),
                BazaarToAuctionHouseFlipProfitPage(self),
                ComposterProfitPage(self),
                BoosterCookieBitsProfit(self),
                EnchantingBookBazaarCheapestPage(self),
                EnchantingBookBazaarProfitPage(self),
        ])
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

    Title().print("Sky Block Tools", "green")
    window = Window()
    MsgText.info("GUI opened successfully!")
    window.mainloop()
    os._exit(0)