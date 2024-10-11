# -*- coding: iso-8859-15 -*-
from hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException
from hyPI._parsers import MayorData, BazaarHistoryProduct, BaseAuctionProduct, BINAuctionProduct, NORAuctionProduct
from hyPI.hypixelAPI.loader import HypixelBazaarParser
from hyPI.recipeAPI import RecipeAPI
from hyPI.skyCoflnetAPI import SkyConflnetAPI
import tksimple as tk
from requests import get as getReq
from requests.exceptions import ConnectionError, ReadTimeout
from pysettings import iterDict
from pysettings.geometry import _map
from pysettings.jsonConfig import JsonConfig
from pysettings.text import MsgText
import os
from datetime import datetime, timedelta
from ctypes import windll
from threading import Thread
from time import time, sleep
from typing import List, Tuple
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pyperclip import copy as copyStr
from pytz import timezone

from widgets import CompleterEntry, CustomPage, CustomMenuPage, TrackerWidget, APIRequest
from bazaarAnalyzer import updateBazaarAnalyzer, BazaarAnalyzer
from analyzer import getPlotData, getCheapestEnchantmentData
from images import IconLoader
from settings import SettingsGUI, Config, checkConfigForUpdates
from constants import (
    VERSION,
    RARITY_COLOR_CODE,
    LOAD_STYLE,
    STYLE_GROUP as SG,
    BAZAAR_INFO_LABEL_GROUP as BILG,
    AUCT_INFO_LABEL_GROUP as AILG,
    API,
    Color,
    Constants,
    MAGIC_POWDER,
    BazaarItemID,
    AuctionItemID,
    ALL_ENCHANTMENT_IDS,
    ConfigFile
)
from skyMath import (
    getPlotTicksFromInterval,
    parsePrizeList,
    getMedianExponent,
    getFlattenList,
    getMedianFromList,
    applyBazaarTax
)
from skyMisc import (
    requestAuctionHypixelAPI,
    requestItemHypixelAPI,
    requestBazaarHypixelAPI,
    updateAuctionInfoLabel,
    updateBazaarInfoLabel,
    modeToBazaarAPIFunc,
    parseTimeDelta,
    parseTimeToStr,
    parseTimeFromSec,
    prizeToStr,
    parsePrice,
    search,
    Sorter,
    BookCraft,
    RecipeResult,
    getDictEnchantmentIDToLevels,
    checkWindows,
    updateItemLists,
    addPetsToAuctionHouse,
    playNotificationSound,
    throwNoAPIKeyException,
    throwAPIConnectionException,
    throwAPITimeoutException
)

APP_DATA = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".SkyBlockTools")
IMAGES = os.path.join(os.path.split(__file__)[0], "images")
CONFIG = os.path.join(os.path.split(__file__)[0], "config")

# Info/Content Pages
class MayorInfoPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Mayor Info Page", buttonText="Mayor Info")
        self.master: Window = master
        self.currentMayorEnd = None
        Thread(target=self.updateTimer).start()

        self.images = self.loadMayorImages()

        self.currentMayor:MayorData = None

        self.notebook = tk.Notebook(self.contentFrame, SG)
        self.tabMayorCur = self.notebook.createNewTab("Current Mayor", SG)
        self.tabMayorHist = self.notebook.createNewTab("Mayor History", SG)
        self.tabMayorRef = self.notebook.createNewTab("Mayor Reference", SG)
        self.notebook.placeRelative()

        self.createCurrentTab(self.tabMayorCur)
        self.createHistoryTab(self.tabMayorHist)
        self.createReferenceTab(self.tabMayorRef)

        self.api = APIRequest(self, self._getTkMaster())
        self.api.setRequestAPIHook(self.requestAPIHook)
    def createCurrentTab(self, tab):
        self.topFrameCurr = tk.Frame(tab, SG)
        self.timerLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.timerLf.setText("Time Remaining")

        self.timeLabel = tk.Label(self.timerLf, SG)
        self.timeLabel.setFg(tk.Color.rgb(227, 141, 30))
        self.timeLabel.setFont(20)
        self.timeLabel.placeRelative(changeWidth=-5, changeHeight=-20)

        self.timerLf.placeRelative(fixWidth=495, fixHeight=50, fixX=100)

        self.imageLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.imageLf.setText("Current Mayor")
        self.imageDisplay = tk.Label(self.imageLf, SG).setText("No Image!")
        self.imageDisplay.placeRelative(fixWidth=100, fixHeight=230, fixX=5, changeHeight=-15, changeWidth=-15)
        self.imageLf.placeRelative(fixWidth=100, fixHeight=240)

        self.dataLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.dataLf.setText("Data")
        self.dataText = tk.Text(self.dataLf, SG, readOnly=True)
        self.dataText.setFont(15)
        self.dataText.placeRelative(changeWidth=-5, changeHeight=-20)
        self.dataLf.placeRelative(fixX=100, fixY=50, fixWidth=495, fixHeight=140+50)

        self.dataLf = tk.LabelFrame(self.topFrameCurr, SG)
        self.dataLf.setText("Perks")
        self.dataTextPerks = tk.Text(self.dataLf, SG, readOnly=True, scrollAble=True)
        self.dataTextPerks.setFont(15)
        self.dataTextPerks.setWrapping(tk.Wrap.WORD)
        self.dataTextPerks.placeRelative(changeWidth=-5, changeHeight=-20)
        self.dataLf.placeRelative(fixX=0, fixY=240, fixWidth=595, fixHeight=250)

        self.topFrameCurr.placeRelative(fixWidth=600, centerX=True)
    def createReferenceTab(self, tab):

        self.topFrame = tk.Frame(tab, SG)
        self.menuFrame = tk.Frame(tab, SG)

        self.imageLf_hist = tk.LabelFrame(self.topFrame, SG)
        self.imageLf_hist.setText("Mayor")
        self.imageDisplay_ref = tk.Label(self.imageLf_hist, SG).setText("No Image!")
        self.imageDisplay_ref.placeRelative(fixWidth=100, fixHeight=230, fixX=5, changeHeight=-15, changeWidth=-15)
        self.imageLf_hist.placeRelative(fixWidth=100, fixHeight=240)

        self.dataLf = tk.LabelFrame(self.topFrame, SG)
        self.dataLf.setText("Data")
        self.dataText_ref = tk.Text(self.dataLf, SG, readOnly=True)
        self.dataText_ref.setFont(15)
        self.dataText_ref.placeRelative(changeWidth=-5, changeHeight=-20)
        self.dataLf.placeRelative(fixX=100, fixY=50, fixWidth=495, fixHeight=140 + 50)

        self.dataLf = tk.LabelFrame(self.topFrame, SG)
        self.dataLf.setText("Perks")
        self.dataTextPerks_ref = tk.Text(self.dataLf, SG, readOnly=True, scrollAble=True)
        self.dataTextPerks_ref.setFont(15)
        self.dataTextPerks_ref.setWrapping(tk.Wrap.WORD)
        self.dataTextPerks_ref.placeRelative(changeWidth=-5, changeHeight=-20)
        self.dataLf.placeRelative(fixX=0, fixY=240, fixWidth=595, fixHeight=250)

        tk.Button(self.topFrame, SG).setText("Back to Mayor Menu").setCommand(self.backToMenu).placeRelative(fixHeight=50, stickRight=True, fixWidth=200)

        self.regMayLf = tk.LabelFrame(self.menuFrame, SG).setText("Regular")
        self.specMayLf = tk.LabelFrame(self.menuFrame, SG).setText("Special")

        widthButton = 300
        heightButton = 35
        regIndex = 0
        specIndex = 0
        for name, data in iterDict(ConfigFile.MAYOR_DATA.getData()):
            if data["special"]:
                specIndex += 1
                index = specIndex
                _master = self.specMayLf
            else:
                regIndex += 1
                index = regIndex
                _master = self.regMayLf

            b = tk.Button(_master, SG)
            b.setText(name.capitalize() +f"\n({ConfigFile.MAYOR_DATA[name]['key']})")
            b.setCommand(self.showMayorInfo, args=[name])
            b.placeRelative(fixWidth=widthButton-5, fixHeight=heightButton, centerX=True, fixY=(index-1)*heightButton)

        self.regMayLf.placeRelative(centerX=True, fixHeight=regIndex * heightButton + 20, fixWidth=widthButton)
        self.specMayLf.placeRelative(centerX=True, fixY=regIndex * heightButton + 20, fixHeight=specIndex * heightButton + 20, fixWidth=widthButton)


        self.menuFrame.placeRelative()
    def showMayorInfo(self, e):
        name = e.getArgs(0)
        self.menuFrame.placeForget()
        self.topFrame.placeRelative(fixWidth=600, centerX=True)
        self._getTkMaster().updateDynamicWidgets()

        dataContent = {
            "Mayor Name:": name,
            "Profession:": ConfigFile.MAYOR_DATA[name]["key"],
            "Peaks:": f"[max {len(ConfigFile.MAYOR_DATA[name]['perks'])}]"
        }
        self.dataText_ref.setText(f"\n".join([f"{k} {v}" for k, v in iterDict(dataContent)]))

        out = ""
        for perk in ConfigFile.MAYOR_DATA[name]["perks"]:
            name_ = perk["name"]
            desc = perk["description"]
            out += f"§g== {name_} ==\n"
            out += f"§c{desc}\n"

        self.dataTextPerks_ref.clear()
        self.dataTextPerks_ref.addStrf(out)

        if name in self.images.keys():
            self.imageDisplay_ref.setImage(self.images[name])
        else:
            self.imageDisplay_ref.clearImage()
            self.imageDisplay_ref.setText("No Image Available")
    def backToMenu(self, e):
        self.topFrame.placeForget()
        self.menuFrame.placeRelative(fixWidth=600, centerX=True)
        self._getTkMaster().updateDynamicWidgets()
    def createHistoryTab(self, tab):
        pass
    def getPerkDescFromPerkName(self, mName, pName)->str:
        for perk in ConfigFile.MAYOR_DATA[mName]["perks"]:
            if perk["name"] == pName:
                return perk["description"]
    def configureContentFrame(self):
        mayorName = self.currentMayor.getName().lower()
        key = self.currentMayor.getKey()
        currYear = self.currentMayor.getYear()
        perks = self.currentMayor.getPerks()
        perkCount = self.currentMayor.getPerkAmount()
        self.currentMayorEnd = self.currentMayor.getEndTimestamp()

        delta:timedelta = self.currentMayorEnd - self.getLocalizedNow()
        self.timeLabel.setText(parseTimeToStr(parseTimeDelta(delta)))

        dataContent = {
            "Mayor Name:": mayorName,
            "Profession:": key,
            "Year:": currYear,
            "Perks:": f"[{perkCount}/{len(ConfigFile.MAYOR_DATA[mayorName]['perks'])}]"
        }
        self.dataText.setText(f"\n".join([f"{k} {v}" for k, v in iterDict(dataContent)]))

        out = ""
        activePerkNames = []
        for perk in perks:
            perkName = perk.getPerkName()
            activePerkNames.append(perkName)
            out += f"§g== {perkName} ==\n"
            out += f"§c{self.getPerkDescFromPerkName(mayorName, perkName)}\n"
        for perk in ConfigFile.MAYOR_DATA[mayorName]["perks"]:
            perkName = perk["name"]
            if perkName not in activePerkNames:
                out += f"§r== {perkName} ==\n"
                out += f"§c{self.getPerkDescFromPerkName(mayorName, perkName)}\n"

        self.dataTextPerks.clear()
        self.dataTextPerks.addStrf(out)

        if mayorName in self.images.keys():
            self.imageDisplay.setImage(self.images[mayorName])
        else:
            self.imageDisplay.clearImage()
            self.imageDisplay.setText("No Image Available")
    def getLocalizedNow(self)->datetime:
        return timezone("Europe/Berlin").localize(datetime.now())
    def updateTimer(self):
        while True:
            sleep(1)
            if self.currentMayorEnd is None: continue
            delta: timedelta = self.currentMayorEnd - self.getLocalizedNow()
            self.timeLabel.setText(parseTimeToStr(parseTimeDelta(delta)))
    def loadMayorImages(self):
        images = {}
        pathMayor = os.path.join(IMAGES, "mayors")
        for fName in os.listdir(pathMayor):
            path = os.path.join(pathMayor, fName)
            name = fName.split(".")[0]
            image = tk.PILImage.loadImage(path)
            image.resizeTo(500, 1080)
            image.resize(.2, useOriginal=False)
            image.preRender()
            images[name] = image
        return images
    def requestAPIHook(self):
        try:
            self.mayorHist = SkyConflnetAPI.getMayorData()
        except APIConnectionError as e:
            throwAPIConnectionException(
                source="Mayor",
                master=self.master,
                event=e
            )
            return None
        except NoAPIKeySetException as e:
            throwNoAPIKeyException(
                source="Mayor",
                master=self.master,
                event=e
            )
            return None
        except APITimeoutException as e:
            throwAPITimeoutException(
                source="Mayor",
                master=self.master,
                event=e
            )
            return None
        self.currentMayor = self.mayorHist.getCurrentMayor()
        self.configureContentFrame()
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = None  # hook to update tv on new API-Data available
        self.placeRelative()
        self.api.startAPIRequest()
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
        if self.filterManipulation.getValue():
            bp = self.currentHistoryData["past_flatten_buy_prices"]
            sp = self.currentHistoryData["past_flatten_sell_prices"]

        self.plot.clear()
        if self.plot2 is not None:
            self.plot2.clear()
            self.plot2.remove()
            self.plot2 = None
        if self.chBuy.getValue(): self.plot.plot(ts, bp, label="Buy Price", color="red")
        if self.chSell.getValue(): self.plot.plot(ts, sp, label="Sell Price", color="green")

        if not self.chSell.getValue() and not self.chBuy.getValue() and not self.chBuyV.getValue() and not self.chSellV.getValue():
            self.plot.clear()
            return

        self.plot.set_title("Price over all available Data." if self.selectedMode == "all" else f"Price over the last {self.selectedMode.capitalize()}")
        self.plot.set_xlabel("Time in h")
        self.plot.set_ylabel(f"Price in {pricePref} coins")

        if self.chBuyV.getValue() or self.chSellV.getValue():
            self.plot2:Axes = self.plot.twinx()
            self.plot2.set_ylabel(f"Volume in {volPref}")

            if self.chBuyV.getValue(): self.plot2.plot(ts, bv, label="Buy Volume", color="blue")
            if self.chSellV.getValue(): self.plot2.plot(ts, sv, label="Sell Volume", color="orange")

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
        if self.filterManipulation.getValue():
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
        out += f"§rInsta-Buy-Price:\n§r  {prizeToStr(bp * amount)}\n"
        out += f"§gInsta-Sell-Price:\n§g  {prizeToStr(sp * amount)}\n\n"
        out += f"§c== Average-Price ==\n(over last {self.selectedMode})\n"
        out += f"§rAverage-Buy-Price:\n§r  {str(round(bpm, 2))} {mPref} coins\n"
        out += f"§gAverage-Sell-Price:\n§g  {str(round(spm, 2))} {mPref} coins\n\n"
        out += f"§c== Volume ==\n"
        out += f"§rInsta-Buy-Volume:\n§r  {prizeToStr(bv)}\n"
        out += f"§gInsta-Sell-Volume:\n§g  {prizeToStr(sv)}\n"
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
class AlchemyXPCalculatorPage(CustomPage):
    def __init__(self, master):
        super().__init__(master,
                         pageTitle="Alchemy XP",
                         buttonText="Alchemy XP Calc")
        self.master: Window = master
        self.headerIndex = ""

        self.alchemyLvlConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "alchemy_lvl.json"))
        self.alchemyXPConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "alchemy_xp.json"))
        self.alchemyXPGoldGainConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "alchemy_lvl_gold.json"))
        self.alchemySellConfigDefault = JsonConfig.loadConfig(os.path.join(CONFIG, "alchemy_sell.json"))
        self.alchemySellConfigGlowstone = JsonConfig.loadConfig(os.path.join(CONFIG, "alchemy_sell_glowstone.json"))

        self.calcMode = tk.DropdownMenu(self.contentFrame, SG)
        self.calcMode.setText("Default (shown ingredient)")
        self.calcMode.setOptionList([
            "Default (shown ingredient)",
            "Default + 1 (shown ingredient + 1 glowstone)",
        ])
        self.calcMode.onSelectEvent(self.updateTreeView)
        self.calcMode.placeRelative(fixHeight=25, stickDown=True, fixWidth=250)

        self.wisdom = tk.TextEntry(self.contentFrame, SG)
        self.wisdom.setText("Wisdom: ")
        self.wisdom.setValue(Config.SETTINGS_CONFIG["alchemy_wisdom"])
        self.wisdom.getEntry().onUserInputEvent(self.updateTreeView)
        self.wisdom.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=250)

        self.fromTo = tk.TextEntry(self.contentFrame, SG)
        self.fromTo.setText("Level Range: ")
        self.fromTo.getEntry().onUserInputEvent(self.updateTreeView)
        self.fromTo.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=350)

        self.info = tk.Label(self.contentFrame, SG)
        self.info.placeRelative(fixHeight=25, stickDown=True, fixX=550)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        scrollbar = tk.ScrollBar(self.master)
        self.treeView.attachVerticalScrollBar(scrollbar)
        self.treeView.bind(self.onItemInfo, tk.EventType.DOUBBLE_LEFT)
        self.treeView.onSelectHeader(self.onHeaderClick)
        self.treeView.placeRelative(changeHeight=-25)
    def onItemInfo(self):
        sel = self.treeView.getSelectedItem()
        if sel is None: return
        self.master.showItemInfo(self, sel["Item"])
    def onHeaderClick(self, e:tk.Event):
        self.headerIndex:str = e.getValue()
        self.updateTreeView()
    def updateTreeView(self):
        self.treeView.clear()
        self.treeView.setTableHeaders("Item", "Cost", "Brews(3-Pots)")

        if API.SKYBLOCK_BAZAAR_API_PARSER is None:

            return


        wisdom = self.wisdom.getValue()
        if wisdom.isnumeric():
            wisdomFactor = int(wisdom)
            Config.SETTINGS_CONFIG["alchemy_wisdom"] = wisdomFactor
            Config.SETTINGS_CONFIG.save()
            wisdomFactor = 1+(wisdomFactor/100)
        else:
            self.info.setText(f"Wrong wisdom value! Must be > 0.")
            return


        content = self.fromTo.getValue()
        if content.count("-") == 1:
            fr, to = content.split("-")
            if fr == "":
                fr = 0
            elif not fr.isnumeric():
                self.info.setText(f"Error: 'from' in level range is nan. {fr}. ({-1} xp)")
                return
            fr = int(fr)
            if to == "":
                to = len(self.alchemyLvlConfig.getData())-1
            elif not to.isnumeric():
                self.info.setText(f"Error: 'to' in level range is nan. {to}. ({-1} xp)")
                return
            to = int(to)
            if not (0 < fr <= len(self.alchemyLvlConfig.getData())):
                self.info.setText(f"Error: 'from' in level range is not in range. {fr}. ({-1} xp)")
                return
            if not (0 < to <= len(self.alchemyLvlConfig.getData())):
                self.info.setText(f"Error: 'to' in level range is not in range. {to}. ({-1} xp)")
                return
            if fr >= to:
                self.info.setText(f"Error: 'to' cannot be less or equal to 'from'. {to}. ({-1} xp)")
                return

            _range = self.alchemyLvlConfig.getData()[fr-1:to]
            requiredXP = sum(_range)
            lvlEarn = sum(self.alchemyXPGoldGainConfig.getData()[fr-1:to])

            self.info.setText(f"Showing range of {len(_range)} Levels. ({requiredXP} xp)")


        elif content == "":
            self.info.setText(f"Showing all 50 Levels. ({sum(self.alchemyLvlConfig.getData())} xp)")
            requiredXP = sum(self.alchemyLvlConfig.getData())
            lvlEarn = sum(self.alchemyXPGoldGainConfig.getData())
        elif content.isnumeric():
            content = int(content)
            if content > 0 and content <= len(self.alchemyLvlConfig.getData()):
                requiredXP = self.alchemyLvlConfig.getData()[content-1]
                lvlEarn = self.alchemyXPGoldGainConfig.getData()[content-1]
                self.info.setText(f"Showing Level {content}. ({requiredXP} xp)")
            else:
                self.info.setText(f"Error: There is no Level {content}. ({-1} xp)")
                return
        else:
            self.info.setText(f"Error: Wrong range or Level {content}. ({-1} xp)")
            return



        if self.calcMode.getValue() == "Default (shown ingredient)":
            alchemySellConfig = self.alchemySellConfigDefault
        else:
            alchemySellConfig = self.alchemySellConfigGlowstone

        sorters = []
        for itemID in self.alchemyXPConfig.keys():
            item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemID)
            singleXp = self.alchemyXPConfig[itemID]
            npcSellPrice = alchemySellConfig[itemID]*3


            brews = int(requiredXP / (singleXp*wisdomFactor*3))+1

            ## Buy price ##

            itemBuyPrice = (item.getInstaSellPrice() + .1-npcSellPrice) * brews

            sorters.append(
                Sorter(
                    sortKey="cost",
                    itemID=itemID,
                    cost=itemBuyPrice-lvlEarn,
                    brews=brews
                )
            )
        sorters.sort()
        sorters.reverse()
        for s in sorters:
            self.treeView.addEntry(
                s["itemID"],
                prizeToStr(s["cost"]),
                s["brews"]
            )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
class EnchantingBookBazaarProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Book Combine Profit Page", buttonText="Book Combine Profit")

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("Name", "Buy-Price", "Sell-Price", "Profit", "Times-Combine", "Insta-Sell/Hour", "Insta-Buy/Hour")
        self.treeView.placeRelative(changeHeight=-25)

        self.eBookImage = tk.PILImage.loadImage(os.path.join(IMAGES, "enchanted_book.gif")).resizeToIcon().preRender()

        # only these enchantments are shown
        self.whiteList = None
        path = os.path.join(CONFIG, "enchantment_profit_whitelist.json")
        if not os.path.exists(path):
            tk.SimpleDialog.askError(master, "enchantment_profit_whitelist.json Path does not exist!")
        else:
            js = JsonConfig.loadConfig(path, ignoreErrors=True)
            if type(js) == str:
                tk.SimpleDialog.askError(master, js)
            else:
                self.whiteList = js.getData()


        self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useBuyOffers.setText("Use-Buy-Offers")
        self.useBuyOffers.onSelectEvent(self.updateTreeView)
        self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.onSelectEvent(self.updateTreeView)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.includeUltimate = tk.Checkbutton(self.contentFrame, SG)
        self.includeUltimate.setText("Include-Ultimate")
        self.includeUltimate.onSelectEvent(self.updateTreeView)
        self.includeUltimate.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=300)

        self.useWhiteList = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useWhiteList.setText("Use-Whitelist")
        self.useWhiteList.onSelectEvent(self.updateTreeView)
        self.useWhiteList.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=450)
    def updateTreeView(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return

        if not self.useBuyOffers.getValue():  # isInstaBuy?
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Profit")
        else:
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Profit", "Others-try-to-buy")
        if self.whiteList is None:
            tk.SimpleDialog.askError(self.master, "Could not load WhitelistFile! Showing All.")
        eDataComplete = []
        enchIDToLvl = getDictEnchantmentIDToLevels()
        for currentItem in enchIDToLvl.keys():
            if self.whiteList is not None and self.useWhiteList.getValue(): # whiteList Active
                if currentItem not in self.whiteList and not (self.includeUltimate.getValue() and currentItem.startswith("ENCHANTMENT_ULTIMATE")):
                    continue
            currentItem = enchIDToLvl[currentItem][-1] # get Highest Enchantment


            eData = getCheapestEnchantmentData(API.SKYBLOCK_BAZAAR_API_PARSER, currentItem, instaBuy=not self.useBuyOffers.getValue())
            if eData is not None:
                if self.useSellOffers.getValue(): # insta sell
                    targetBookInstaBuy = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(currentItem).getInstaBuyPrice()
                else:
                    targetBookInstaBuy = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(currentItem).getInstaSellPrice()

                targetBookInstaBuy = applyBazaarTax(targetBookInstaBuy) # apply Tax


                prods = [
                    API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("ENCHANTMENT_ULTIMATE_BANK_5"),
                    API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("ENCHANTMENT_ULTIMATE_BANK_4"),
                    API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("ENCHANTMENT_ULTIMATE_BANK_3"),
                    API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("ENCHANTMENT_ULTIMATE_BANK_2"),
                    API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("ENCHANTMENT_ULTIMATE_BANK_1"),
                ]

                # == For Test Reason ==

                """ for productFrom in prods:
                    print(f"== {productFrom.getID()} ==")
                    print(f"Volume:", productFrom.getBuyVolume(), "are Selling", )
                    print(f"Volume:", productFrom.getSellVolume(), "are Buying", )
                    targetBookInstaBuy__ = productFrom.getInstaBuyPrice()
                    targetBookInstaSell = productFrom.getInstaSellPrice()

                    print("Insta-Buy: ", round(targetBookInstaBuy__, 0))
                    print("Insta-Sell: ", round(targetBookInstaSell, 0))
                    if targetBookBuyOffer := productFrom.getSellOrders():
                        print("Buy-Order: ", round(targetBookBuyOffer[0].getPricePerUnit(), 0))
                    else:
                        print("Buy-Order: ", None)

                    if targetBookSellOrder := productFrom.getBuyOrders():
                        print("Sell-Offer: ", round(targetBookSellOrder[0].getPricePerUnit(), 0))
                    else:
                        print("Sell-Offer: ", None)

                    # print("InstaBuyTest",  productFrom.getInstaBuyPriceList(1)[0])
                    # print("InstaSellTest", productFrom.getInstaSellPriceList(1)[0])
                """

                eData = [BookCraft(d, targetBookInstaBuy) for d in eData]  # convert so sortable BookCraft instances
                eData.sort()
                eDataComplete.append(eData[0]) #get best BookCraft instance


        eDataComplete.sort()
        for bookCraft in eDataComplete:
            if not self.useBuyOffers.getValue():
                if bookCraft.getFromAmount() is None: continue
                self.treeView.addEntry(
                    f"{bookCraft.getShowAbleIDFrom()} [x{bookCraft.getFromAmount()}] -> {bookCraft.getShowAbleIDTo()}",
                    prizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                    prizeToStr(bookCraft.getFromPrice()),
                    prizeToStr(bookCraft.getSavedCoins()),
                    image=self.eBookImage
                )
            else:
                if bookCraft.getFromAmount() is None:
                    pass

                self.treeView.addEntry(
                    f"{bookCraft.getShowAbleIDFrom()} [x{bookCraft.getFromAmount()}] -> {bookCraft.getShowAbleIDTo()}",
                    prizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                    prizeToStr(bookCraft.getFromPrice()),
                    prizeToStr(bookCraft.getSavedCoins()),
                    prizeToStr(bookCraft.getFromSellVolume(), hideCoins=True),
                    image=self.eBookImage
                )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
class EnchantingBookBazaarCheapestPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Cheapest Book Craft Page", buttonText="Cheapest Book Craft")
        self.currentItem = None
        self.currentParser = None
        # mark best !!!
        self.eBookImage = tk.PILImage.loadImage(os.path.join(IMAGES, "enchanted_book.gif")).resizeToIcon().preRender()

        self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useBuyOffers.setText("Use-Buy-Order-Price")
        self.useBuyOffers.onSelectEvent(self.updateTreeView)
        self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Buy-Amount", "Total-Buy-Price", "Saved-Coins")
        self.treeView.placeRelative(changeHeight=-25)
    def updateTreeView(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return

        if not self.useBuyOffers.getValue(): # isInstaBuy?
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Saved-Coins")
        else:
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Saved-Coins", "Others-try-to-buy")

        eData = getCheapestEnchantmentData(API.SKYBLOCK_BAZAAR_API_PARSER, self.currentItem, instaBuy=not self.useBuyOffers.getValue())
        if eData is not None:
            targetBookInstaBuy = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(self.currentItem).getInstaBuyPrice()
            eData = [BookCraft(d, targetBookInstaBuy) for d in eData] # convert so sortable BookCraft instances
            eData.sort()
            for bookCraft in eData:
                if not self.useBuyOffers.getValue():
                    if bookCraft.getFromAmount() is None: continue
                    self.treeView.addEntry(
                        bookCraft.getShowAbleIDFrom()+f" [x{bookCraft.getFromAmount()}]",
                        prizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                        prizeToStr(bookCraft.getFromPrice()),
                        prizeToStr(bookCraft.getSavedCoins()),
                        image=self.eBookImage
                    )
                else:
                    if bookCraft.getFromAmount() is None:
                        pass

                    self.treeView.addEntry(
                        bookCraft.getShowAbleIDFrom() + f" [x{bookCraft.getFromAmount()}]",
                        prizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                        prizeToStr(bookCraft.getFromPrice()),
                        prizeToStr(bookCraft.getSavedCoins()),
                        prizeToStr(bookCraft.getFromSellVolume(), hideCoins=True),
                        image=self.eBookImage
                    )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.currentItem = kwargs["itemName"]
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
        self.setPageTitle(f"Cheapest Book Craft [{self.currentItem}]")
    def customShow(self, page):
        page.openNextMenuPage(self.master.searchPage,
                         input={"Enchantment":ALL_ENCHANTMENT_IDS},
                         msg="Search EnchantedBook in Bazaar: (At least tree characters)",
                         next_page=self)
class BazaarCraftProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Bazaar-Craft-Profit", buttonText="Bazaar Craft Profit")
        self.currentParser = None

        self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useBuyOffers.setText("Use-Buy-Offers")
        self.useBuyOffers.onSelectEvent(self.updateTreeView)
        self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.onSelectEvent(self.updateTreeView)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.showStackProfit = tk.Checkbutton(self.contentFrame, SG)
        self.showStackProfit.setText("Show-Profit-as-Stack[x64]")
        self.showStackProfit.onSelectEvent(self.updateTreeView)
        self.showStackProfit.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=300)

        tk.Label(self.contentFrame, SG).setText("Search:").placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=500)

        self.searchE = tk.Entry(self.contentFrame, SG)
        self.searchE.bind(self._clearAndUpdate, tk.EventType.RIGHT_CLICK)
        self.searchE.onUserInputEvent(self.updateTreeView)
        self.searchE.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=600)

        self.recursiveCraft = tk.Checkbutton(self.contentFrame, SG)
        self.recursiveCraft.setText("Add-Deep-Recipes")
        self.recursiveCraft.onSelectEvent(self.updateTreeView)
        self.recursiveCraft.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=700)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        #self.treeView.setNoSelectMode()
        self.treeView.setTableHeaders("Recipe", "Profit-Per-Item[x64]", "Ingredients-Buy-Price-Per-Item", "Needed-Item-To-Craft")
        self.treeView.placeRelative(changeHeight=-25)

        self.forceAdd = [
            "GRAND_EXP_BOTTLE",
            "TITANIC_EXP_BOTTLE",
            "ENCHANTED_GOLDEN_CARROT",
            "BUDGET_HOPPER",
            "ENCHANTED_HOPPER",
            "CORRUPT_SOIL",
            "HOT_POTATO_BOOK",
            "ENCHANTED_EYE_OF_ENDER",
            "ENCHANTED_COOKIE",
            "BLESSED_BAIT"
        ]
        self.validRecipes = self._getValidRecipes()
        self.validBzItems = [i.getID() for i in self.validRecipes]

        self.rMenu = tk.ContextMenu(self.treeView, SG)
        tk.Button(self.rMenu).setText("ItemInfo").setCommand(self.onItemInfo)
        self.rMenu.create()
    def onItemInfo(self):
        sel = self.treeView.getSelectedItem()
        if sel is None: return
        self.master.showItemInfo(self, sel["Recipe"])
    def _clearAndUpdate(self):
        self.searchE.clear()
        self.updateTreeView()
        self.searchE.setFocus()
    def _getValidRecipes(self):
        validRecipes = []
        for recipe in RecipeAPI.getRecipes():
            if not self.isBazaarItem(recipe.getID()): continue # filter Items to only take Bazaar Items
            validIngredient = True
            ingredients = recipe.getItemInputList()
            if ingredients is None: # no recipe available
                continue
            for ingredient in ingredients:
                indName = ingredient["name"]
                if not self.isBazaarItem(indName): # filter ingredients
                    if recipe.getID() not in self.forceAdd:
                        validIngredient = False
                        break
            if validIngredient:
                validRecipes.append(recipe)
        return validRecipes
    def isBazaarItem(self, item:str)->bool:
        return item in BazaarItemID
    def getIngredient(self, item)->Tuple[List[str], List[str]]:




        return
    def updateTreeView(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        if not self.showStackProfit.getValue():
            factor = 1
            headers = ["Recipe", "Profit-Per-Item", "Ingredients-Buy-Price-Per-Item", "Needed-Item-To-Craft"]
        else:
            factor = 64
            headers = ["Recipe", "Profit-Per-Stack[x64]", "Ingredients-Buy-Price-Per-Stack[x64]", "Needed-Item-To-Craft[x64]"]

        if self.recursiveCraft.getValue():
            headers.append("Craft-Depth")

        self.treeView.setTableHeaders(headers)

        validItems = search([self.validBzItems], self.searchE.getValue(), printable=False)

        recipeList = []
        for recipe in self.validRecipes:
            result = recipe.getID()
            if result in BazaarAnalyzer.getCrashedItems():
                tag = "crash"
            if result in BazaarAnalyzer.getManipulatedItems():
                tag = "manip"
            if self.searchE.getValue() != "":
                if recipe.getID() not in validItems: continue

            resultItem = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(result)
            ingredients = recipe.getItemInputList()
            craftPrice = 0
            requiredItemString = "("

            ## Result price ##
            if self.useSellOffers.getValue(): # use sell Offer
                resultPrice = resultItem.getInstaBuyPrice()
            else: # insta sell result
                resultPrice = resultItem.getInstaSellPrice()

            #apply bz tax
            resultPrice = applyBazaarTax(resultPrice)

            ## ingredients calc ##
            for ingredient in ingredients:
                name = ingredient["name"]
                amount = ingredient["amount"]
                requiredItemString+=f"{name}[{amount*factor}], "

                if name not in BazaarItemID: continue

                ingredientItem = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(name)

                ## ingredients price ##
                if self.useBuyOffers.getValue():  # use buy Offer ingredients
                    ingredientPrice = [ingredientItem.getInstaSellPrice()+.1] * amount
                else:  # insta buy ingredients
                    ingredientPrice = ingredientItem.getInstaBuyPriceList(amount)
                if len(ingredientPrice) != amount:
                    result+="*"
                    extentAm = amount - len(ingredientPrice)
                    average = sum(ingredientPrice)/amount
                    ingredientPrice.extend([average]*extentAm)
                craftPrice += sum(ingredientPrice)
            profitPerCraft = resultPrice - craftPrice # profit calculation
            requiredItemString = requiredItemString[:-2]+")"

            recipeList.append(RecipeResult(result, profitPerCraft*factor, craftPrice*factor, requiredItemString))
        recipeList.sort()
        for rec in recipeList:
            content = [
                rec.getID(),
                prizeToStr(rec.getProfit()),
                prizeToStr(rec.getCraftPrice()),
                rec.getRequired()
            ]
            if self.recursiveCraft.getValue():
                content.append(rec.getCraftDepth())
            self.treeView.addEntry(*content)
    def onShow(self, **kwargs):
        self.validRecipes = self._getValidRecipes()
        self.validBzItems = [i.getID() for i in self.validRecipes]
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
class BazaarFlipProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Bazaar-Flip-Profit", buttonText="Bazaar Flip Profit")

        self.currentParser = None
        self.perMode = None # "per_hour" / "per_week"
        self.headerIndex = "Flip-Rating"
        self.headerToKey = {
            "Item":"ID",
            "Profit-Per-Item":"profitPerFlip",
            "Profit-Per-Stack[x64]":"profitPerFlip",
            "Buy-Price":"buy",
            "Buy-Price[x64]":"buy",
            "Sell-Price":"sell",
            "Sell-Price[x64]":"sell",
            "Others-Try-To-Buy":"buyVolume",
            "Others-Try-To-Sell":"sellVolume",
            "Buy-Per-Hour":"buysPerHour",
            "Sell-Per-Hour":"sellsPerHour",
            "Buy-Per-Week":"buysPerWeek",
            "Sell-Per-Week":"sellsPerWeek",
            "Flip-Rating":"flipRating",
            "Average Buy Order":"averagePriceToBuyDiff"
        }

        self.settingsWindow = tk.Dialog(master, SG)
        self.settingsWindow.hide()
        self.settingsWindow.setTitle("Bazaar-Flip-Settings")
        self.settingsWindow.setCloseable(False)
        self.settingsWindow.setWindowSize(500, 500)
        self.settingsWindow.setResizeable(False)

        self.useBuyOffers = tk.Checkbutton(self.settingsWindow, SG).setSelected()
        self.useBuyOffers.setText("Use-Buy-Offers").setTextOrientation()
        self.useBuyOffers.placeRelative(fixHeight=25, fixWidth=120, fixY=0)

        self.useSellOffers = tk.Checkbutton(self.settingsWindow, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers").setTextOrientation()
        self.useSellOffers.placeRelative(fixHeight=25, fixWidth=120, fixY=25)

        self.includeEnchantments = tk.Checkbutton(self.settingsWindow, SG)
        self.includeEnchantments.setText("Include-Enchantments").setTextOrientation()
        self.includeEnchantments.placeRelative(fixHeight=25, fixWidth=200, fixY=75-25)

        self.showOthersTry = tk.Checkbutton(self.settingsWindow, SG)
        self.showOthersTry.setText("Show-other-Try-To-buy/sell").setTextOrientation()
        self.showOthersTry.placeRelative(fixHeight=25, fixWidth=200, fixY=100-25)

        self.perHour = tk.Button(self.settingsWindow, SG)
        self.perHour.setText("Sells/Buys-per-Hour: Hidden").setTextOrientation()
        self.perHour.setCommand(self.toggleSellsPer)
        self.perHour.placeRelative(fixHeight=25, fixWidth=200, fixY=125-25)

        self.hideLowInstaSell = tk.Checkbutton(self.settingsWindow, SG)
        self.hideLowInstaSell.setText("Hide Insta-Sells < 1/h").setTextOrientation()
        self.hideLowInstaSell.placeRelative(fixHeight=25, fixWidth=200, fixY=150-25)

        self.showFlipRatingHour = tk.Checkbutton(self.settingsWindow, SG).setSelected()
        self.showFlipRatingHour.setText("Show-Flip-Rating").setTextOrientation()
        self.showFlipRatingHour.placeRelative(fixHeight=25, fixWidth=200, fixY=175 - 25)

        self.saveAndClose = tk.Button(self.settingsWindow, SG)
        self.saveAndClose.setText("Save & Close")
        self.saveAndClose.setCommand(self.closeAndUpdate)
        self.saveAndClose.placeRelative(stickDown=True, fixWidth=100, fixHeight=25)

        tk.Label(self.contentFrame, SG).setText("Search:").placeRelative(fixHeight=25, stickDown=True, fixWidth=100)

        self.searchE = tk.Entry(self.contentFrame, SG)
        self.searchE.bind(self._clearAndUpdate, tk.EventType.RIGHT_CLICK)
        self.searchE.onUserInputEvent(self.updateTreeView)
        self.searchE.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=100)

        self.openSettings = tk.Button(self.contentFrame, SG)
        self.openSettings.setCommand(self.settingsWindow.show)
        self.openSettings.setText("Open Settings")
        self.openSettings.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=200)

        tk.Label(self.contentFrame, SG).setText("Show for amount:").placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=300)
        self.factorSelect = tk.DropdownMenu(self.contentFrame, SG)
        self.factorSelect.setText("1")
        self.factorSelect.setOptionList([1, 16, 32, 64, 160, 1024, 71680, "custom..."])
        self.factorSelect.onSelectEvent(self.updateTreeView)
        self.factorSelect.placeRelative(fixHeight=25, stickDown=True, fixWidth=50, fixX=400)

        self.flipRatingSelect = tk.DropdownMenu(self.contentFrame, SG)
        self.flipRatingSelect.setText("flipping")
        self.flipRatingSelect.setOptionList(["flipping"])
        self.flipRatingSelect.onSelectEvent(self.updateTreeView)
        self.flipRatingSelect.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=450)

        self.filterManip = tk.Checkbutton(self.contentFrame, SG)
        self.filterManip.setText("Filter Manipulated Data")
        self.filterManip.onSelectEvent(self.updateTreeView)
        self.filterManip.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=550)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        scrollbar = tk.ScrollBar(self.master)
        self.treeView.attachVerticalScrollBar(scrollbar)
        self.treeView.bind(self.onItemInfo, tk.EventType.DOUBBLE_LEFT)
        self.treeView.onSelectHeader(self.onHeaderClick)
        self.treeView.placeRelative(changeHeight=-25)

        # Test: request missing average values
        #tk.Button(self.contentFrame, SG).setCommand(self.test).place(0, 0, 50, 50)

        self.rMenu = tk.ContextMenu(self.treeView, SG)
        tk.Button(self.rMenu).setText("Request Average Price...").setCommand(self.requestAverage)
        self.rMenu.create()
    def saveAverage(self):
        ConfigFile.AVERAGE_PRICE.saveConfig()

    def test(self):
        def request(id_):
            try:
                self.currentHistoryData = getPlotData(id_, SkyConflnetAPI.getBazaarHistoryWeek)
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
            Constants.WAITING_FOR_API_REQUEST = False

            ConfigFile.AVERAGE_PRICE[id_] = getMedianFromList(self.currentHistoryData["past_raw_buy_prices"])
            self.master.runTask(self.updateTreeView).start()
            self.master.runTask(self.saveAverage).start()
        def _test():
            for i in BazaarItemID:
                if i not in ConfigFile.AVERAGE_PRICE.keys():
                    sleep(5)
                    request(i)
                    print("request", i)



        Thread(target=_test).start()
        print("return")

    def requestAverage(self):
        def request():
            try:
                self.currentHistoryData = getPlotData(id_, SkyConflnetAPI.getBazaarHistoryWeek)
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

            ConfigFile.AVERAGE_PRICE[id_] = getMedianFromList(self.currentHistoryData["past_raw_buy_prices"])
            self.master.runTask(self.updateTreeView).start()
            self.master.runTask(self.saveAverage).start()

        if not Constants.WAITING_FOR_API_REQUEST:
            selected = self.treeView.getSelectedItem()
            if selected is None: return
            id_ = selected["Item"]

            Constants.WAITING_FOR_API_REQUEST = True
            Thread(target=request).start()
    def onItemInfo(self):
        sel = self.treeView.getSelectedItem()
        if sel is None: return
        self.master.showItemInfo(self, sel["Item"])
    def onHeaderClick(self, e:tk.Event):
        self.headerIndex:str = e.getValue()
        self.updateTreeView()
    def closeAndUpdate(self):
        self.settingsWindow.hide()
        self.updateTreeView()
    def toggleSellsPer(self):
        match self.perMode:
            case None:
                self.perMode = "per_week"
            case "per_week":
                self.perMode = "per_hour"
            case "per_hour":
                self.perMode = None
        self.updateTreeView()
    def _clearAndUpdate(self):
        self.searchE.clear()
        self.updateTreeView()
        self.searchE.setFocus()
    def isBazaarItem(self, item:str)->bool:
        return item in BazaarItemID
    def updateTreeView(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return

        factor = self.factorSelect.getValue()
        if factor == "custom...":
            factor = tk.SimpleDialog.askInteger(self.master, "Custom Amount?")
            if factor is None:
                factor = 1
            self.factorSelect.setText(factor)
        factor = int(factor)
        if factor < 1: factor = 1

        if factor == 1:
            titles = ["Item", "Buy-Price", "Sell-Price", "Profit-Per-Item"]
        else:
            titles = ["Item", f"Buy-Price[x{factor}]", f"Sell-Price[x{factor}]", f"Profit-Per-Stack[x{factor}]"]
        if self.showOthersTry.getValue():
            titles.extend(["Others-Try-To-Buy", "Others-Try-To-Sell"])
        if self.perMode == "per_hour":
            titles.extend(["Buy-Per-Hour", "Sell-Per-Hour"])
        if self.perMode == "per_week":
            titles.extend(["Buy-Per-Week", "Sell-Per-Week"])
        if self.showFlipRatingHour.getValue():
            titles.append("Flip-Rating")
        titles.append("Average Buy Order")
        self.treeView.setTableHeaders(titles)

        validItems = search([BazaarItemID], self.searchE.getValue(), printable=False)

        itemList = []
        filterManip = self.filterManip.getState()
        manipulatedItemIDs = [i[0]["ID"] for i in BazaarAnalyzer.getManipulatedItems()]
        #print("=======================================================================================")
        for itemID in BazaarItemID:

            if itemID in manipulatedItemIDs and filterManip: continue

            if self.searchE.getValue() != "" and itemID not in validItems: continue

            if itemID.startswith("ENCHANTMENT") and not self.includeEnchantments.getValue(): continue

            item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemID)
            if item is None:
                print("ERROR", itemID)
                continue
            if self.hideLowInstaSell.getValue() and item.getInstaSellWeek() / 168 < 1: continue
            ## Sell price ##
            if self.useSellOffers.getValue(): # use sell Offer
                itemSellPrice = item.getInstaBuyPrice()
            else: # insta sell
                itemSellPrice = item.getInstaSellPrice()
            itemSellPrice = applyBazaarTax(itemSellPrice) * factor
            if not itemSellPrice: continue # sell is zero
            ## Buy price ##
            if self.useBuyOffers.getValue():
                itemBuyPrice = [item.getInstaSellPrice() + .1] * factor
            else:  # insta buy ingredients
                itemBuyPrice = item.getInstaBuyPriceList(factor)
            if len(itemBuyPrice) != factor:
                print(f"[BazaarFlipper]: Item {itemID}. not enough in buy!")
                continue

            averageBuyPrice = ""
            averagePriceToBuyDiff = ""

            itemBuyPrice = sum(itemBuyPrice)
            if itemID in ConfigFile.AVERAGE_PRICE.keys():
                averageBuyPrice = ConfigFile.AVERAGE_PRICE[itemID] * factor
                averagePriceToBuyDiff = averageBuyPrice - itemBuyPrice


            profitPerFlip = itemSellPrice - itemBuyPrice # profit calculation

            sellsPerHour = item.getInstaSellWeek() / 168
            buysPerHour = item.getInstaBuyWeek() / 168

            flipRating = -1
            if self.flipRatingSelect.getValue() == "flipping":
                minBuysSells = min([sellsPerHour, buysPerHour])
                flipRating = profitPerFlip * minBuysSells
                if minBuysSells > 1000:
                    flipRating*=10



                #flipRating = ((1-(1/min([sellsPerHour, buysPerHour])**(1/1000)))+(1-(1/profitPerFlip)))/2



            elif self.flipRatingSelect.getValue() == "profit per Hour":
                profitPerHour = profitPerFlip * min([sellsPerHour, buysPerHour])
                offerAmountFactor = 1-1/(min([sellsPerHour, buysPerHour])**(1/5)) # filter
                flipRating = profitPerHour*offerAmountFactor



            itemList.append(
                Sorter(
                    sortKey=self.headerToKey[self.headerIndex],

                    ID=itemID,
                    profitPerFlip=profitPerFlip,
                    buy=itemBuyPrice,
                    sell=itemSellPrice,
                    sellsPerWeek=item.getInstaSellWeek(),
                    buysPerWeek=item.getInstaBuyWeek(),
                    sellsPerHour=sellsPerHour,
                    buysPerHour=buysPerHour,
                    sellVolume=item.getSellVolume(),
                    sellOrders=item.getSellOrdersTotal(),
                    buyVolume=item.getBuyVolume(),
                    buyOrders=item.getBuyOrdersTotal(),
                    flipRating=flipRating,
                    averagePriceToBuyDiff=averagePriceToBuyDiff,
                    averageBuyPrice=averageBuyPrice,
                )
            )
        itemList.sort()
        for rec in itemList:
            input_ = [
                rec["ID"],
                prizeToStr(rec["buy"]),
                prizeToStr(rec["sell"]),
                prizeToStr(rec["profitPerFlip"]),
            ]
            if self.showOthersTry.getValue():
                input_.extend([f"{rec['buyVolume']} in {rec['buyOrders']} Orders", f"{rec['sellVolume']} in {rec['sellOrders']} Orders"])
            if self.perMode == "per_hour":
                input_.extend([f"{round(rec['buysPerHour'], 2)}", f"{round(rec['sellsPerHour'], 2)}"])
            if self.perMode == "per_week":
                input_.extend([f"{rec['buysPerWeek']}", f"{rec['sellsPerWeek']}"])
            if self.showFlipRatingHour.getValue():
                input_.append(f"{prizeToStr(rec['flipRating'], hideCoins=True)}")


            colorTag = "none"
            if rec["averageBuyPrice"] != "":
                price = prizeToStr(rec["averageBuyPrice"])
                diff = prizeToStr(rec["averagePriceToBuyDiff"])
                if rec["averagePriceToBuyDiff"] > 0:
                    colorTag = "good"
                    diff = "+" + diff

                    #crash detection
                    if rec["buy"] < (rec["averageBuyPrice"]/5)*3:
                        colorTag = "crash"

                else:
                    colorTag = "bad"
                input_.append(f"{price} ({diff})")
            else:
                input_.append("")

            self.treeView.addEntry(*input_, tag=colorTag)
        self.treeView.setBgColorByTag("none", Color.COLOR_DARK)
        self.treeView.setBgColorByTag("good", tk.Color.GREEN)
        self.treeView.setBgColorByTag("bad", tk.Color.RED)
        self.treeView.setBgColorByTag("crash", "#27a39f")
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
    def onHide(self):
        self.settingsWindow.hide()
class ComposterProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Composter-Profit", buttonText="Composter Profit")
        self.currentParser = None

        self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG)
        self.useBuyOffers.setText("Use-Buy-Offers")
        self.useBuyOffers.setSelected()
        self.useBuyOffers.onSelectEvent(self.updateTreeView)
        self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG)
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.setSelected()
        self.useSellOffers.onSelectEvent(self.updateTreeView)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.openSettings = tk.Button(self.contentFrame, SG)
        self.openSettings.setText("Composter-Settings")
        self.openSettings.setCommand(self.openComposterSettings)
        self.openSettings.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.matterLf = tk.LabelFrame(self.contentFrame, SG)
        self.matterLf.setText("Plant Matter [coins per matter]")
        self.matterLb = tk.Listbox(self.matterLf, SG)
        self.matterLb.onSelectEvent(self.onListboxSelect, args=["matter"])
        self.matterLb.placeRelative(changeWidth=-5, changeHeight=-25)
        self.matterLf.placeRelative(fixWidth=300, fixHeight=300, centerX=True, changeX=-150)

        self.fuelLf = tk.LabelFrame(self.contentFrame, SG)
        self.fuelLf.setText("Fuel [coins per fuel]")
        self.fuelLb = tk.Listbox(self.fuelLf, SG)
        self.fuelLb.onSelectEvent(self.onListboxSelect, args=["fuel"])
        self.fuelLb.placeRelative(changeWidth=-5, changeHeight=-25)
        self.fuelLf.placeRelative(fixWidth=300, fixHeight=300, centerX=True,changeX=+150)

        self.textLf = tk.LabelFrame(self.contentFrame, SG)
        self.textLf.setText("Info")
        self.textT = tk.Text(self.textLf, SG, readOnly=True)
        self.textT.placeRelative(changeWidth=-5, changeHeight=-25)
        self.textLf.placeRelative(fixY=300, fixWidth=600, changeHeight=-25, centerX=True)

        self.organic_matter_data = JsonConfig.loadConfig(os.path.join(CONFIG, "composter_organic_matter.json"), ignoreErrors=True)
        if type(self.organic_matter_data) == str:
            self.organic_matter_data = None
            tk.SimpleDialog.askError(self.master, self.organic_matter_data)

        self.fuel_data = JsonConfig.loadConfig(os.path.join(CONFIG, "composter_fuel.json"), ignoreErrors=True)
        if type(self.fuel_data) == str:
            self.fuel_data = None
            tk.SimpleDialog.askError(self.master, self.fuel_data)

        self.sortedFuel = []
        self.sortedMatter = []
        self.selectedMatter = None
        self.selectedFuel = None


        #self.showStackProfit = tk.Checkbutton(self.contentFrame, SG)
        #self.showStackProfit.setText("Show-Profit-as-Stack[x64]")
        #self.showStackProfit.onSelectEvent(self.updateTreeView)
        #self.showStackProfit.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=300)
    def openComposterSettings(self):
        SettingsGUI.openComposterSettings(self.master, onScrollHook=self.updateTreeView)
    def onListboxSelect(self, e):
        type_ = e.getArgs(0)
        if type_ == "matter":
            self.selectedMatter = self.matterLb.getSelectedIndex()
        else:
            self.selectedFuel = self.fuelLb.getSelectedIndex()
        self.updateTreeView()
    def parseData(self):

        if API.SKYBLOCK_BAZAAR_API_PARSER is None: return
        if self.fuel_data is None or self.organic_matter_data is None:
            self.sortedFuel = False
            self.sortedMatter = False
            return
        sortedFuel = []
        sortedMatter = []
        for name, value in iterDict(self.fuel_data.getData()):

            ingredientItem = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(name)

            ## ingredients price ##
            if self.useBuyOffers.getValue():  # use buy Offer ingredients
                # print(f"Offer one {name}:", ingredientItem.getInstaSellPrice()+.1)
                ingredientPrice = [ingredientItem.getInstaSellPrice() + .1]
            else:  # insta buy ingredients
                ingredientPrice = ingredientItem.getInstaBuyPriceList(1)

            pricePerFuel = ingredientPrice[0] / value

            sortedFuel.append(Sorter(pricePerFuel, name=name))
        sortedFuel.sort()
        self.sortedFuel = sortedFuel[::-1]
        if self.selectedFuel is None:
            self.selectedFuel = 0

        for name, value in iterDict(self.organic_matter_data.getData()):

            ingredientItem = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(name)

            ## ingredients price ##
            if self.useBuyOffers.getValue():  # use buy Offer ingredients
                # print(f"Offer one {name}:", ingredientItem.getInstaSellPrice()+.1)
                ingredientPrice = [ingredientItem.getInstaSellPrice() + .1]
            else:  # insta buy ingredients
                ingredientPrice = ingredientItem.getInstaBuyPriceList(1)

            pricePerMatter = ingredientPrice[0]/value

            sortedMatter.append(Sorter(pricePerMatter, name=name))
        sortedMatter.sort()
        self.sortedMatter = sortedMatter[::-1]
        if self.selectedMatter is None:
            self.selectedMatter = 0
    def calculateComposterUpgrades(self):
        data = Config.SETTINGS_CONFIG["composter"]

        # constants
        matterRequired = 4000
        fuelRequired = 2000
        durationSeconds = 600

        # upgrades
        speed = data["speed"]
        mulDrop = data["multi_drop"] * 3
        fuelCap = data["fuel_cap"] * 30_000 + 100_000
        matterCap = data["matter_cap"] * 20_000 + 40_000
        costReduct = data["cost_reduction"]

        # apply cost reduction
        matterRequired *= (100 - costReduct) / 100
        fuelRequired *= (100 - costReduct) / 100

        newDuration = 1/((6 + 6 * 0.2 * speed) / 3600) # new duration to produce one compost

        return {
            "multiple_drop_percentage": mulDrop,
            "matter_required": matterRequired,
            "fuel_required": fuelRequired,
            "matter_cap":matterCap,
            "fuel_cap":fuelCap,
            "duration_seconds":newDuration
        }
    def addMultipleChance(self, chance, amount):
        amount += amount*(chance/100)
        return amount
    def updateTreeView(self):
        if self.sortedFuel is None or self.sortedMatter is None: return
        if API.SKYBLOCK_BAZAAR_API_PARSER is None: return

        ## calculation ##
        self.parseData() # calculate current prices
        data = self.calculateComposterUpgrades() # calculate upgrades

        ## Listbox ##
        self.matterLb.clear()
        self.fuelLb.clear()
        for i, matter in enumerate(self.sortedMatter):
            self.matterLb.add(f"{matter['name']} [{round(matter.get(), 2)} coins]")
        for i, matter in enumerate(self.sortedFuel):
            self.fuelLb.add(f"{matter['name']} [{round(matter.get(), 2)} coins]")

        ## Result price ##
        compost = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("COMPOST")
        if self.useSellOffers.getValue():  # use sell Offer
            compostSellPrice = compost.getInstaBuyPrice()
        else:  # insta sell result
            compostSellPrice = compost.getInstaSellPrice()
        compostSellPrice = applyBazaarTax(compostSellPrice) # add tax

        compostE = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("ENCHANTED_COMPOST")
        if self.useSellOffers.getValue():  # use sell Offer
            compostESellPrice = compostE.getInstaBuyPrice()
        else:  # insta sell result
            compostESellPrice = compostE.getInstaSellPrice()
        compostESellPrice = applyBazaarTax(compostESellPrice)  # add tax

        matterType = self.sortedMatter[self.selectedMatter]
        fuelType = self.sortedFuel[self.selectedFuel]

        coinsPerMatter = self.sortedMatter[self.selectedMatter].get()
        coinsPerFuel = self.sortedFuel[self.selectedFuel].get()

        singleCost = (coinsPerMatter * data["matter_required"] + coinsPerFuel * data["fuel_required"])
        singleProfit = compostSellPrice - singleCost
        enchantedSingleCost = (compostESellPrice - (singleCost*160)) / 160
        #TODO test
        enchantedSingleCostA = (compostESellPrice - (singleCost*self.addMultipleChance(data['multiple_drop_percentage'], 160))) / 160 # with multiple_drop_percentage

        compostFullFuel = round(data['fuel_cap']/data['fuel_required'], 2)
        compostFullMatter = round(data['matter_cap']/data['matter_required'], 2)
        if compostFullFuel > compostFullMatter:
            upgrade = "matter"
            compostFull = compostFullMatter
        else:
            upgrade = "fuel"
            compostFull = compostFullFuel
        self.textT.clear()
        text = f"Matter-Type: {matterType['name']}\n"
        text += f"Matter-Required-Full-Tank: {int(data['matter_cap']/self.organic_matter_data[matterType['name']])}\n"
        text += f"Matter-Tank: {prizeToStr(data['matter_cap'], True)}\n"
        text += f"Fuel-Type: {fuelType['name']}\n"
        text += f"Fuel-Required-Full-Tank: {int(data['fuel_cap']/self.fuel_data[fuelType['name']])}\n"
        text += f"Fuel-Tank: {prizeToStr(data['fuel_cap'], True)}\n"
        text += f"Time-Per-Compost: {parseTimeFromSec(data['duration_seconds'])}\n\n"
        text += f"===== PROFIT =====\n"
        text += f"Single-Profit(no mul drop): {prizeToStr(singleProfit)}\n"
        text += f"Stack-Profit(x64): {prizeToStr(singleProfit*64)} (~{prizeToStr(singleProfit * self.addMultipleChance(data['multiple_drop_percentage'], 64))} per)\n"
        text += f"Profit-Enchanted-Compost(x1 compost): {prizeToStr(enchantedSingleCost)}\n"
        text += f"Profit-Enchanted-Compost(x160 compost): {prizeToStr(enchantedSingleCostA)}\n\n"
        text += f"== OFFLINE ==\n"
        text += f"Compost-With-Full-Tanks: {compostFull} (upgrade: {upgrade})\n"
        text += f"Duration-With-Full-Tanks: {parseTimeFromSec(data['duration_seconds'] * compostFull)}\n"
        text += f"Full-Composter-Profit: ~{prizeToStr(singleProfit*self.addMultipleChance(data['multiple_drop_percentage'], compostFull))}\n"
        self.textT.setStrf(text)
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
class BazaarToAuctionHouseFlipProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Bazaar-To-Auction-Flip-Profit", buttonText="Bazaar to Auction Flip Profit")
        self.currentParser = None

        self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG)
        self.useBuyOffers.setText("Use-Buy-Offers").setSelected()
        self.useBuyOffers.onSelectEvent(self.updateTreeView)
        self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        #self.showStackProfit = tk.Checkbutton(self.contentFrame, SG)
        #self.showStackProfit.setText("Show-Profit-as-Stack[x64]")
        #self.showStackProfit.onSelectEvent(self.updateTreeView)
        #self.showStackProfit.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=300)

        tk.Label(self.contentFrame, SG).setText("Search:").placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=500)

        self.searchE = tk.Entry(self.contentFrame, SG)
        self.searchE.bind(self._clearAndUpdate, tk.EventType.RIGHT_CLICK)
        self.searchE.onUserInputEvent(self.updateTreeView)
        self.searchE.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=600)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        #self.treeView.setNoSelectMode()
        self.treeView.setTableHeaders("Recipe", "Profit-Per-Item", "Ingredients-Buy-Price-Per-Item", "Needed-Item-To-Craft")
        self.treeView.placeRelative(changeHeight=-25)



        self.forceAdd = [
            "DAY_SAVER"
        ]
        self.validRecipes = self._getValidRecipes()
        #print("valid", [i.getID() for i in self.validRecipes])
        self.validBzItems = [i.getID() for i in self.validRecipes]
    def _clearAndUpdate(self):
        self.searchE.clear()
        self.updateTreeView()
        self.searchE.setFocus()
    def _getValidRecipes(self):
        validRecipes = []
        for recipe in RecipeAPI.getRecipes():

            #if recipe.getID() not in AuctionItemID and recipe.getID() not in self._ownBzItems:
            #    print(recipe.getID())

            if not self.isAuctionItem(recipe.getID()): continue # filter Items to only take Auction Items
            validIngredient = True
            ingredients = recipe.getItemInputList()
            if ingredients is None: # no recipe available
                continue
            for ingredient in ingredients:
                indName = ingredient["name"]
                if not self.isBazaarItem(indName): # filter ingredients
                    if recipe.getID() not in self.forceAdd:
                        validIngredient = False
                        break
            if validIngredient:
                validRecipes.append(recipe)
        return validRecipes
    def isAuctionItem(self, item:str)->bool:
        return item in AuctionItemID
    def isBazaarItem(self, item:str)->bool:
        return item in BazaarItemID
    def updateTreeView(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        if API.SKYBLOCK_AUCTION_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        self.treeView.setTableHeaders("Recipe", "Profit-Per-Item", "Ingredients-Buy-Price-Per-Item", "Lowest-Bin", "Needed-Item-To-Craft")
        validItems = search([self.validBzItems], self.searchE.getValue(), printable=False)

        recipeList = []
        #print("=======================================================================================")
        for recipe in self.validRecipes:
            #if recipe.getID().lower() != "compactor": continue
            result =recipe.getID()

            if self.searchE.getValue() != "":
                if recipe.getID() not in validItems: continue

            #if "ENCHANTED_SLIME_BLOCK" != result: continue
            #print("result", result)

            auct = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(result)
            if not len(auct):
                #print("No data found ", result)
                continue
            auct.sort()
            lowestBin = auct[-1].getPrice()

            #print(result, auct[0].getPrice(), auct[-1].getPrice(), len(auct))


            ingredients = recipe.getItemInputList()
            craftCost = 0
            requiredItemString = "("

            ## Result price ##
            #TODO get cheapest Auction house item price -> "resultItem"


            ## ingredients calc ##
            for ingredient in ingredients:
                name = ingredient["name"]
                amount = ingredient["amount"]
                requiredItemString+=f"{name}[{amount}], "

                if name not in BazaarItemID: continue

                ingredientItem = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(name)

                ## ingredients price ##
                if self.useBuyOffers.getValue():  # use buy Offer ingredients
                    ingredientPrice = [ingredientItem.getInstaSellPrice()+.1] * amount
                else:  # insta buy ingredients
                    ingredientPrice = ingredientItem.getInstaBuyPriceList(amount)
                if len(ingredientPrice) != amount:
                    result+="*"
                    extentAm = amount - len(ingredientPrice)
                    average = sum(ingredientPrice)/amount
                    ingredientPrice.extend([average]*extentAm)

                craftCost += sum(ingredientPrice)
            profitPerCraft = lowestBin - craftCost # profit calculation
            requiredItemString = requiredItemString[:-2]+")"

            recipeList.append(Sorter(profitPerCraft, reqItemsStr=requiredItemString, resultID=result, craftCost=craftCost, lowestBin=lowestBin))
        recipeList.sort()
        for rec in recipeList:
            self.treeView.addEntry(
                rec["resultID"],
                prizeToStr(rec.get()), # profit
                prizeToStr(rec["craftCost"]),
                prizeToStr(rec["lowestBin"]),
                rec["reqItemsStr"]
            )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView # hook to update tv on new API-Data available
        self.validRecipes = self._getValidRecipes()
        self.validBzItems = [i.getID() for i in self.validRecipes]
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
class LongTimeFlip(tk.Frame):
    def __init__(self, page, window, master, data):
        super().__init__(master, SG)
        self.isOrder = False
        self.data = data
        self.master:tk.Frame = master
        self.window:Window = window
        self.page = page
        self.bind(self.onEdit, tk.EventType.LEFT_CLICK)
        self.selectedItem = self.data["item_id"]
        self.setBg(Color.COLOR_GRAY)
        self.titleL = tk.Label(self, SG).setFont(13)
        self.titleL.bind(self.onEdit, tk.EventType.LEFT_CLICK)
        self.titleL.setBg(Color.COLOR_GRAY)
        self.titleL.setText(f"{self.selectedItem} [{1}]")
        self.titleL.placeRelative(fixHeight=25)
        self.spendL = tk.Label(self, SG)
        self.spendL.bind(self.onEdit, tk.EventType.LEFT_CLICK)
        self.spendL.setBg(Color.COLOR_GRAY)
        self.spendL.placeRelative(fixHeight=25, fixY=25)
        self.sellNowL = tk.Label(self, SG)
        self.sellNowL.bind(self.onEdit, tk.EventType.LEFT_CLICK)
        self.sellNowL.setBg(Color.COLOR_GRAY)
        self.sellNowL.placeRelative(fixHeight=25, fixY=50)
        self.profitL = tk.Label(self, SG).setFont(16)
        self.profitL.bind(self.onEdit, tk.EventType.LEFT_CLICK)
        self.profitL.setBg(Color.COLOR_GRAY)
        self.profitL.placeRelative(fixHeight=25, fixY=75)
        self.profitL2 = tk.Label(self, SG).setFont(16)
        self.profitL2.bind(self.onEdit, tk.EventType.LEFT_CLICK)
        self.profitL2.setBg(Color.COLOR_GRAY)
        self.profitL2.placeRelative(fixHeight=25, fixY=100)

        self.expectedSellPrice = tk.Label(self, SG)
        self.expectedSellPrice.setText("Expected Price: ")
        self.expectedSellPrice.placeRelative(stickDown=True, fixHeight=25)

        self.rMenu = tk.ContextMenu(self, SG)
        self.rMenu.bindToWidget(self.titleL)
        self.rMenu.bindToWidget(self.spendL)
        self.rMenu.bindToWidget(self.sellNowL)
        self.rMenu.bindToWidget(self.profitL)
        self.rMenu.bindToWidget(self.profitL2)
        tk.Button(self.rMenu).setText("ItemInfo").setCommand(self.onItemInfo)
        tk.Button(self.rMenu).setText("Request Average Price...").setCommand(self.requestAverage)
        self.rMenu.create()


    def saveAverage(self):
        ConfigFile.AVERAGE_PRICE.saveConfig()

    def requestAverage(self):
        def request():
            try:
                self.currentHistoryData = getPlotData(id_, SkyConflnetAPI.getBazaarHistoryWeek)
                Constants.WAITING_FOR_API_REQUEST = False
            except APIConnectionError as e:
                throwAPIConnectionException(
                    source="SkyCoflnet",
                    master=self.window,
                    event=e
                )
                return None
            except NoAPIKeySetException as e:
                throwNoAPIKeyException(
                    source="SkyCoflnet",
                    master=self.window,
                    event=e
                )
                return None
            except APITimeoutException as e:
                throwAPITimeoutException(
                    source="SkyCoflnet",
                    master=self.window,
                    event=e
                )
                return None

            ConfigFile.AVERAGE_PRICE[id_] = getMedianFromList(self.currentHistoryData['past_raw_buy_prices'])
            self.window.runTask(self.updateWidget).start()
            self.window.runTask(self.saveAverage).start()

        if not Constants.WAITING_FOR_API_REQUEST:
            id_ = self.selectedItem

            Constants.WAITING_FOR_API_REQUEST = True
            Thread(target=request).start()
    def onItemInfo(self):
        self.window.showItemInfo(self.page, self.selectedItem)

    def onEdit(self):
        NewFlipWindow(self, self.page, self.master._getTkMaster(), self.selectedItem, finish=self.page.finishEdit, data=self.data).show()
    def updateWidget(self, isOrder=None):
        if isOrder is None:
            isOrder = self.isOrder
        else:
            self.isOrder = isOrder

        _sum = 0
        for i in self.data["data"]:
            _sum += i["amount"]

        self.titleL.setText(f"{self.selectedItem} [{_sum}x]")

        sellPricePer = self.getSellSinglePrice(isOrder)
        sellPrice, exact = self.getSellPrice(isOrder)
        buyPrice = self.getPriceSpend()

        if self.selectedItem in ConfigFile.AVERAGE_PRICE.keys():

            averageBuyPrice = ConfigFile.AVERAGE_PRICE[self.selectedItem]
            averagePriceToBuyDiff = averageBuyPrice - sellPricePer
            if averagePriceToBuyDiff > 0:
                self.expectedSellPrice.setFg("red")
                self.expectedSellPrice.setText(f"Expected Price: +{prizeToStr(averagePriceToBuyDiff)}")
            else:
                self.expectedSellPrice.setFg("green")
                self.expectedSellPrice.setText(f"Expected Price: {prizeToStr(averagePriceToBuyDiff)}")
        else:
            self.expectedSellPrice.setFg("white")
            self.expectedSellPrice.setText("Expected Price: null")

        if buyPrice == 0:
            tk.SimpleDialog.askError(self.master, "BuyPrice cannot be zero!")
            return
        buyPricePer = buyPrice/self.getAmountBought()
        star = "*" if not exact else ""
        if self.data["items_bought"]:
            self._setBg(tk.Color.rgb(138, 90, 12))
            self.profitL2.setFg(Color.COLOR_WHITE)
            profit = sellPrice - buyPrice
            self.spendL.setText(f"Coins Spend: {prizeToStr(self.getPriceSpend())} (Price Per: ~{prizeToStr(buyPricePer)})")
            self.sellNowL.setText(f"Sell now{star}: {prizeToStr(sellPrice)} (Price Per: ~{prizeToStr(sellPricePer)})")
            self.profitL.setText(f"Profit: {prizeToStr(profit)}")
            self.profitL2.setText(f"Invest: {prizeToStr(buyPrice)}")
        else:
            self.profitL2.setFg("green")
            self._setBg(tk.Color.rgb(22, 51, 45))
            profit = sellPrice - buyPrice
            self.spendL.setText(f"Worth at Start: {prizeToStr(buyPrice)} (Price Per: ~{prizeToStr(buyPricePer)})")
            self.sellNowL.setText(f"Sell now{star}: {prizeToStr(sellPrice)} (Price Per: ~{prizeToStr(sellPricePer)})")
            self.profitL.setText(f"Profit: {prizeToStr(profit)}")
            self.profitL2.setText(f"Sell: {prizeToStr(sellPrice)}")
        if profit > 0:
            self.profitL.setFg("green")
        else:
            self.profitL.setFg("red")

        self._getTkMaster().updateDynamicWidgets()
    def _setBg(self, bg):
        self.setBg(bg)
        self.titleL.setBg(bg)
        self.spendL.setBg(bg)
        self.sellNowL.setBg(bg)
        self.profitL.setBg(bg)
        self.profitL2.setBg(bg)
        self.expectedSellPrice.setBg(bg)
    def isFlip(self):
        return self.data["items_bought"]
    def isFinished(self):
        return self.data["finished"]
    def setName(self, name:str):
        self.titleL.setText(name)
    def getPriceSpend(self) -> float:
        price = 0
        for item in self.data["data"]:
            price += item["price"] * item["amount"]
        return price
    def getAmountBought(self) -> int:
        amount = 0
        for item in self.data["data"]:
            amount += item["amount"]
        return amount
    def getSellSinglePrice(self, offer=False):
        item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(self.selectedItem)
        if offer:  # use sell Offer
            price = item.getInstaBuyPrice()
        else:  # insta sell result
            price = item.getInstaSellPrice()
        return applyBazaarTax(price)  # add tax
    def getSellPrice(self, offer) -> Tuple[float, bool]:
        amount = self.getAmountBought()
        item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(self.selectedItem)
        if offer:  # use sell Offer
            price = item.getInstaBuyPrice() * amount
        else:  # insta sell result
            price = item.getInstaSellPriceList(amount)
            if len(price) != amount:
                extentAm = amount - len(price)
                average = sum(price) / amount
                price.extend([average] * extentAm)
                return sum(price), False
            return sum(price), True
        return applyBazaarTax(price), True  # add tax
    def getPercentage(self):
        pass
    def setData(self, data):
        self.data = data
        self.updateWidget()
    def toData(self):
        return self.data
    def getProfit(self, isOrder):
        buyPrice = self.getPriceSpend()
        sellPrice, exact = self.getSellPrice(isOrder)
        if self.data["items_bought"]:
            return sellPrice - buyPrice, exact
        return sellPrice, exact
class NewFlipWindow(tk.Dialog):
    def __init__(self, widget, page, master, itemId, data=None, finish=None):
        super().__init__(master, SG)
        self._finishHook = finish
        self.master = master
        self.itemID = itemId
        self.data = data
        self.page = page
        self.widget = widget
        self.selectedItem = None

        self.setWindowSize(600, 600)
        self.setResizeable(False)
        self.onCloseEvent(self.finish)
        self.setTitle("Add New Flip")
        tk.Label(self, SG).setText(f"Selected-Item: {itemId}").setFont(16).placeRelative(fixHeight=30)

        self.priceE = tk.TextEntry(self, SG)
        self.priceE.setText("Price-Per-Item:")
        self.priceE.getEntry().bind(self.onChange, tk.EventType.RETURN)
        self.priceE.place(0, 30, 200, 25, entryStartX=105)

        self.takeOfferPrice = tk.Button(self, SG)
        self.takeOfferPrice.canTakeFocusByTab(False)
        self.takeOfferPrice.setText("Use buy Offer Price")
        self.takeOfferPrice.setCommand(self.takeOffer)
        self.takeOfferPrice.place(200, 30, 150, 25)

        self.setAmountE = tk.TextEntry(self, SG)
        self.setAmountE.getEntry().bind(self.onChange, tk.EventType.RETURN)
        self.setAmountE.setText("Set-Item-Amount:")
        self.setAmountE.place(0, 30+25, 200, 25, entryStartX=105)

        self.setAmountB = tk.Button(self, SG)
        self.setAmountB.canTakeFocusByTab(False)
        self.setAmountB.setText("Set Amount")
        self.setAmountB.setCommand(self.onChange)
        self.setAmountB.place(200, 30 + 25, 150, 25)

        self.addAmountE = tk.TextEntry(self, SG)
        self.addAmountE.setText("Add-Item-Amount:")
        self.addAmountE.getEntry().bind(self.onChange, tk.EventType.RETURN)
        self.addAmountE.place(0, 30 + 25*2, 200, 25, entryStartX=105)

        self.addAmountB = tk.Button(self, SG)
        self.addAmountB.canTakeFocusByTab(False)
        self.addAmountB.setText("Add-Amount")
        self.addAmountB.setCommand(self.onChange)
        self.addAmountB.place(200, 30 + 25*2, 150, 25)

        self.newEntryB = tk.Button(self, SG)
        self.newEntryB.canTakeFocusByTab(False)
        self.newEntryB.setText("New Flip Entry")
        self.newEntryB.setCommand(self.newFlip)
        self.newEntryB.place(0, 30+25*3, 350, 25)

        self.deleteEntryB = tk.Button(self, SG).setDisabled()
        self.deleteEntryB.canTakeFocusByTab(False)
        self.deleteEntryB.setText("Delete Flip Entry")
        self.deleteEntryB.setCommand(self.deleteSelectedFlip)
        self.deleteEntryB.place(0, 30 + 25 * 4, 350, 25)

        self.isFlipC = tk.Checkbutton(self, SG)
        self.isFlipC.canTakeFocusByTab(False)
        self.isFlipC.setText("0 -> Items bought for price|1-> Item are worth this Price")
        self.isFlipC.place(0, 30 + 25 * 5, 350, 25)

        self.isFinishedC = tk.Checkbutton(self, SG)
        self.isFinishedC.canTakeFocusByTab(False)
        self.isFinishedC.setText("Finished")
        self.isFinishedC.place(0, 30 + 25 * 6, 350, 25)

        self.deleteThis = tk.Button(self, SG)
        self.deleteThis.setText("Delete This Entry")
        self.deleteThis.setFg("red")
        self.deleteThis.setCommand(self.onDeleteThis)
        self.deleteThis.placeRelative(fixHeight=25, fixWidth=100, stickRight=True, fixY=30)

        self.disableWidgets()
        self.treeView = tk.TreeView(self, SG)
        self.treeView.onSingleSelectEvent(self.onSelect)
        self.treeView.setTableHeaders("Amount", "Price-Per-Item", "Price")
        self.treeView.placeRelative(fixY=200)
        if data is not None:
            self.isNew = False
            self.readData(data)
        else:
            self.isNew = True
            self.data = {
                "item_id":self.itemID,
                "finished":False,
                "sold_for":0,
                "items_bought":False,
                "data":[]
            }
    def onDeleteThis(self):
        if tk.SimpleDialog.askOkayCancel(self.master, "Are you sure?"):
            if not self.isNew:
                self.page.deleteEntry(self.widget)
            self.destroy()
            if self._finishHook is not None: self._finishHook()

    def takeOffer(self):
        item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(self.itemID)
        price = item.getInstaSellPrice()+.1
        self.priceE.setValue(str(price))
    def onChange(self):
        selectedIndex = self.treeView.getSelectedIndex()
        if selectedIndex is None: return
        if selectedIndex == -1: return
        add = self.addAmountE.getValue()
        amount = self.setAmountE.getValue()
        price = self.priceE.getValue()

        if not amount.isnumeric():
            tk.SimpleDialog.askError(self.master, "Amount is not Valid or Empty!")
            return

        if (not price.isnumeric() and "." not in price) or (not price.replace(".", "").isnumeric() and not price.count(".") == 1):
            tk.SimpleDialog.askError(self.master, "Price is not Valid or Empty!")
            return
        if add != "" and not add.isnumeric():
            tk.SimpleDialog.askError(self.master, "Add is not Valid!")
            return
        if add == "": add = 0
        amount = int(amount) + int(add)
        price = float(price)
        if amount == 0 or price == 0:
            tk.SimpleDialog.askError(self.master, "Price or Amount is Zero!")
            return

        self.addAmountE.clear()
        self.setAmountE.setValue(str(amount))

        data = self.data["data"][self.treeView.getSelectedIndex()]
        data["price"] = price
        data["amount"] = amount

        self.treeView.setEntry(prizeToStr(amount, True), prizeToStr(price), prizeToStr(amount*price), index=selectedIndex)
    def onSelect(self):
        self.enableWidgets()
        if self.treeView.getSelectedIndex() is None: return
        data = self.data["data"][self.treeView.getSelectedIndex()]
        self.priceE.setValue(data["price"])
        self.setAmountE.setValue(data["amount"])
        self.addAmountE.setValue("")
        if data["amount"] == "":
            self.addAmountE.setDisabled()
            self.addAmountB.setDisabled()
        else:
            self.addAmountE.setEnabled()
            self.addAmountB.setEnabled()
    def deleteSelectedFlip(self):
        selectedIndex = self.treeView.getSelectedIndex()[0]
        if selectedIndex == -1: return
        self.enableWidgets()
        self.clear()
        self.disableWidgets()
        self.data["data"].pop(selectedIndex)
        self.treeView.deleteItemByIndex(selectedIndex)
    def disableWidgets(self):
        self.priceE.setDisabled()
        self.setAmountE.setDisabled()
        self.setAmountB.setDisabled()
        self.addAmountE.setDisabled()
        self.addAmountB.setDisabled()
        self.takeOfferPrice.setDisabled()
        self.deleteEntryB.setDisabled()
    def enableWidgets(self):
        self.priceE.setEnabled()
        self.setAmountE.setEnabled()
        self.setAmountB.setEnabled()
        self.addAmountE.setEnabled()
        self.addAmountB.setEnabled()
        self.takeOfferPrice.setEnabled()
        self.deleteEntryB.setEnabled()
    def clear(self):
        self.setAmountE.clear()
        self.addAmountE.clear()
        self.priceE.clear()
    def newFlip(self):
        self.treeView.addEntry("", "", "")
        self.treeView.setItemSelectedByIndex(-1, clearFirst=True)
        self.data["data"].append(
            {
                "amount":0,
                "price":0
            }
        )
        self.enableWidgets()
        self.addAmountB.setDisabled()
        self.addAmountE.setDisabled()
        self.onSelect()
    def finish(self):
        if self.isNew: # create New or apply data
            self.page.flips.append(LongTimeFlip(self.page, self.master, self.page.contentFrame, self.data))
        self.data["items_bought"] = not self.isFlipC.getValue()
        self.data["finish"] = not self.isFinishedC.getValue()
        if self._finishHook is not None: self._finishHook()
    def readData(self, data):
        self.selectedItem = data["item_id"]
        self.isFinishedC.setValue(self.data["finished"])
        self.isFlipC.setValue(not self.data["items_bought"])
        self.treeView.clear()
        for dat in self.data["data"]:
            amount = dat["amount"]
            price = dat["price"]
            self.treeView.addEntry(prizeToStr(amount, True), prizeToStr(price), prizeToStr(amount*price))
class LongTimeFlipHelperPage(CustomPage):
    def __init__(self, master):
        super().__init__(master,
                         pageTitle="Active-Flips",
                         buttonText="Active Flips")

        self.flipGap = 5
        self.flipWidth = 300 - self.flipGap
        self.flipHeight = 150 - self.flipGap
        self.flipw = 0
        self.fliph = 0
        self.flips: List[LongTimeFlip] = []
        self.js = None

        self.master:Window = master
        self.master.onWindowResize(self.onResizeEvent)
        self.master.updateCurrentPageHook = self.updateView
        #self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        #self.useBuyOffers.setText("Use-Buy-Offers")
        #self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.onSelectEvent(self.updateView)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=0)

        self.newFlip = tk.Button(self.contentFrame, SG)
        self.newFlip.setText("New Flip")
        self.newFlip.setCommand(self.addNewFlip)
        self.newFlip.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.modeS = tk.DropdownMenu(self.contentFrame, SG, optionList=[
            "Show All Active",
            "Show All Flips",
            "Show All in Stock",
        ])
        self.modeS.setText("Show All Active")
        self.modeS.onSelectEvent(self.updateView)
        self.modeS.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=320)

        self.showFinished = tk.Checkbutton(self.contentFrame, SG)
        self.showFinished.setText("Show Finished")
        self.showFinished.onSelectEvent(self.updateView)
        self.showFinished.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=320+150)

        self.infoLf = tk.LabelFrame(self.contentFrame, SG)
        self.infoLf.setText("Info")
        self.fullProfitL = tk.Label(self.infoLf, SG)
        self.fullProfitL.setText("Profit: None")
        self.fullProfitL.setFont(16)
        self.fullProfitL.placeRelative(changeWidth=-5, fixHeight=25)
        self.totalValueL = tk.Label(self.infoLf, SG).setFg("green")
        self.totalValueL.setText("Total-Value: None")
        self.totalValueL.setFont(16)
        self.totalValueL.placeRelative(changeWidth=-5, fixHeight=25, fixY=25)

        self.infoLf.placeRelative(fixHeight=self.flipHeight, fixWidth=self.flipWidth, stickDown=True, stickRight=True, changeY=-30)

        self._decode()
    def _decode(self):
        path = os.path.join(APP_DATA, "active_flip_config.json")
        if not os.path.exists(path):
            MsgText.warning("active_flip_config.json dosent exist. Creating blank at: "+path)
            file = open(path, "w")
            file.write("[]")
            file.close()
        js = JsonConfig.loadConfig(path, ignoreErrors=True)
        if type(js) == str:
            tk.SimpleDialog.askError(self.master, js)
            return
        self.js = js
        for flipData in js.getData():
            self.flips.append(LongTimeFlip(self, self.master, self.contentFrame, flipData))
    def addNewFlip(self):
        self.openNextMenuPage(self.master.searchPage,
                              input=[BazaarItemID],
                              next_page=self
                              )
    def onResizeEvent(self, e):
        if self.master.getWidth() // (self.flipWidth + self.flipGap) != self.flipw or (self.master.getHeight()-200) // (self.flipHeight + self.flipGap) != self.fliph:
            self.placeWidgets()
    def placeWidgets(self)->List[LongTimeFlip]:
        if self.js is None: return []
        width = self.master.getWidth()
        height = self.master.getHeight()
        self.flipw = width // self.flipWidth # how many x elements fit
        self.fliph = (height-40) // self.flipHeight # how many y elements fit
        flipRow = 0
        flipCol = 0

        mode = self.modeS.getValue()
        showFin = self.showFinished.getValue()
        placedFlips = []
        for frame in self.flips:
            if showFin != frame.isFinished():
                frame.placeForget()
                continue

            if mode == "Show All Flips" and not frame.isFlip():
                frame.placeForget()
                continue
            elif mode == "Show All in Stock" and frame.isFlip():
                frame.placeForget()
                continue
            # else -> "Show All Active"
            if height - 105 <= (self.flipHeight + self.flipGap) * (flipCol+2) and flipRow+1 == self.flipw:
                frame.placeForget()
                placedFlips.append(frame)
                continue
            if height-105 <= (self.flipHeight + self.flipGap) * (flipCol+1):
                frame.placeForget()
                placedFlips.append(frame)
                continue
            placedFlips.append(frame)
            frame.place((self.flipWidth + self.flipGap) * flipRow, (self.flipHeight + self.flipGap) * flipCol, self.flipWidth, self.flipHeight)
            if flipRow+1 == self.flipw:
                flipRow = 0
                flipCol += 1
            else:
                flipRow += 1
        return placedFlips
    def deleteEntry(self, e:LongTimeFlip):
        self.flips.remove(e)
        e.destroy()
    def finishEdit(self):
        self.saveToFile()
        self.updateView()
    def saveToFile(self):
        if self.js is None:
            MsgText.warning("Could not save Data! 'active_flip_config.json' does not exist or not readable!")
            return
        self.js.setData([i.toData() for i in self.flips])
        self.js.saveConfig()
    def updateView(self):
        placedFlips = self.placeWidgets()
        fullProfit = 0
        totalValue = 0
        exact = True
        for flip in self.flips:
            flip.updateWidget(self.useSellOffers.getValue())

        for flip in placedFlips:
            value, _exact = flip.getProfit(self.useSellOffers.getValue())
            if not _exact: exact = False
            fullProfit += value

            value, _exact = flip.getSellPrice(self.useSellOffers.getValue())
            if not _exact: exact = False
            totalValue += value

        self.master.updateDynamicWidgets()
        star = "*" if not exact else ""
        self.fullProfitL.setText(f"Profit{star}: {prizeToStr(fullProfit)}")
        self.totalValueL.setText(f"Total-Value{star}: {prizeToStr(totalValue)}")
        if fullProfit > 0:
            self.fullProfitL.setFg("green")
        else:
            self.fullProfitL.setFg("red")
    def onShow(self, **kwargs):
        if "itemName" in kwargs: # search complete
            self._menuData["history"].pop(-2) # delete search Page and self
            self._menuData["history"].pop(-2) # workaround
            selected = kwargs["itemName"]
            NewFlipWindow(None, self, self.master, selected, finish=self.finishEdit).show()
        self.placeRelative()
        self.placeContentFrame()
        self.master.updateDynamicWidgets()
        self.updateView()
class AuctionHousePage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Auction House", buttonText="Auction House")
        self.selectedItem = None
        self.shownAuctions = []
        self.showOwnAuctions = False
        self.isMenuShown = False
        self.menuMode = None # "pet"

        self.tvScroll = tk.ScrollBar(master, SG)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setSingleSelect()
        self.treeView.attachVerticalScrollBar(self.tvScroll)
        self.treeView.setTableHeaders("Name", "Lowest BIN")
        self.treeView.onDoubleSelectEvent(self.onDoubleClick)
        self.treeView.bind(self.onRClick, tk.EventType.RIGHT_CLICK)
        self.treeView.bind(self.onBtn, tk.EventType.MOUSE_PREV)
        self.treeView.placeRelative(changeHeight=-25, changeWidth=-2)

        self.searchBtn = tk.Button(self.contentFrame, SG)
        self.searchBtn.setText("Show My Auctions")
        self.searchBtn.setCommand(self.onBtn)
        self.searchBtn.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.searchL = tk.Label(self.contentFrame, SG)
        self.searchL.setText("Search: ")

        self.searchE = tk.Entry(self.contentFrame, SG)
        self.searchE.bind(self._clearAndUpdate, tk.EventType.RIGHT_CLICK)
        self.searchE.onUserInputEvent(self.updateTreeView)

        self.ownContextM = tk.ContextMenu(self.treeView, group=SG, eventType=None)
        tk.Button(self.ownContextM).setText("View this Item in AH").setCommand(self.viewSelectedItem)
        self.ownContextM.create()

        self.itemContextM = tk.ContextMenu(self.treeView, group=SG, eventType=None)
        tk.Button(self.itemContextM).setText("copy in-game Command").setCommand(self.copyURL)
        self.itemContextM.create()

        self.auctionType = tk.DropdownMenu(self.contentFrame, SG, optionList=["BIN only", "Auctions only"])
        self.auctionType.setText("BIN only")
        self.auctionType.onSelectEvent(self.updateTreeView)
        self.auctionType.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=450)

        self.menuOpenCloseBtn = tk.Button(self.contentFrame, SG)
        self.menuOpenCloseBtn.setText("<")
        self.menuOpenCloseBtn.setCommand(self.toggleMenu)
        self.menuOpenCloseBtn.placeRelative(fixHeight=50, fixWidth=25, stickRight=True, changeX=-21, stickDown=True, changeY=-28-(400/2+50/2))

        self.settingsMenu = tk.LabelFrame(self.contentFrame, SG)

        tk.Label(self.settingsMenu, SG).setText("Rarity:").placeRelative(fixHeight=25, stickDown=True, xOffsetRight=50, changeHeight=-5, changeWidth=-5)
        self.raritySelectC = tk.DropdownMenu(self.settingsMenu, SG,optionList=["All", "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"], readonly=True)
        self.raritySelectC.setText("All")
        self.raritySelectC.onSelectEvent(self.updateTreeView)
        self.raritySelectC.placeRelative(fixHeight=25, stickDown=True, xOffsetLeft=50, changeHeight=-5, changeWidth=-5)

        self.showRarityC = tk.Checkbutton(self.settingsMenu, SG)
        self.showRarityC.setText("Show Rarity").setSelected()
        self.showRarityC.onSelectEvent(self.updateTreeView)
        self.showRarityC.placeRelative(fixHeight=25, stickDown=True, changeY=-25, changeHeight=-5, changeWidth=-5)


        self.petMenuF = tk.Frame(self.settingsMenu, SG)
        self.check_filterC = tk.Checkbutton(self.petMenuF, SG)
        self.check_filterC.setText("Filter Pet-Lvl")
        self.check_filterC.onSelectEvent(self.updateTreeView)
        self.check_filterC.placeRelative(fixHeight=25)


        self.ownAuctionF = tk.Frame(self.settingsMenu, SG)
        self.own_sumL2 = tk.Label(self.ownAuctionF, SG)
        self.own_sumL2.setFont(13)
        self.own_sumL2.setText("If all Sold: ")
        self.own_sumL2.placeRelative(xOffsetRight=50, fixHeight=25)
        self.own_sumL = tk.Label(self.ownAuctionF, SG)
        self.own_sumL.setFg("green")
        self.own_sumL.setFont(13)
        self.own_sumL.placeRelative(xOffsetLeft=50, fixHeight=25)
    def clearMenu(self):
        self.petMenuF.placeForget()
        self.check_filterC.setState(False)
        self.raritySelectC.setText("All")
        self.ownAuctionF.placeForget()
        self.menuMode = None
    def configureMenu(self, auctions:List[BaseAuctionProduct]):
        if self.showOwnAuctions:
            sum_ = 0
            for auc in auctions:
                if isinstance(auc, BINAuctionProduct):
                    sum_ += auc.getPrice()
                elif isinstance(auc, NORAuctionProduct):
                    sum_ += auc.getHighestBid()
            self.own_sumL.setText(f"+ {prizeToStr(sum_)}")
            self.ownAuctionF.placeRelative(changeWidth=-5, changeHeight=-5-50)
        elif self.selectedItem is not None:
            if not len(auctions): return
            if auctions[0].isPet():
                self.menuMode = "pet"
                self.petMenuF.placeRelative(changeWidth=-5, changeHeight=-5-50)
    def toggleMenu(self):
        self.isMenuShown = not self.isMenuShown
        if self.isMenuShown:
            self.openMenu()
        else:
            self.closeMenu()
    def closeMenu(self):
        self.isMenuShown = False
        self.menuOpenCloseBtn.setText("<")
        self.settingsMenu.placeForget()
        self.menuOpenCloseBtn.placeRelative(fixHeight=50, fixWidth=25, stickRight=True, changeX=-21, stickDown=True, changeY=-28 - (400 / 2 + 50 / 2))
    def openMenu(self):
        self.isMenuShown = True
        self.menuOpenCloseBtn.setText(">")
        self.settingsMenu.placeRelative(fixWidth=250, fixHeight=400, stickDown=True, stickRight=True, changeY=-28,changeX=-21)
        self.menuOpenCloseBtn.placeRelative(fixHeight=50, fixWidth=25, stickRight=True, changeX=-21 - 250, stickDown=True, changeY=-28 - (400 / 2 + 50 / 2))
        self.master.updateDynamicWidgets()

    def _filterPets(self, auctions:List[Sorter])->List[Sorter]:
        if not len(auctions): return []
        if isinstance(auctions[0]["auctClass"], NORAuctionProduct): return auctions # not supported
        pet_lvl_set = {}
        for sorter in auctions:
            auction: BaseAuctionProduct = sorter["auctClass"]
            lvl = auction.getPetLevel()
            pet_lvl_set[lvl] = sorter
        sorted_ = list(pet_lvl_set.values())
        sorted_.sort()
        sorted_.reverse()
        currentLvl = 0
        out = []
        for sorter in sorted_:
            auction: BaseAuctionProduct = sorter["auctClass"]
            lvl = auction.getPetLevel()
            if lvl > currentLvl:
                out.append(sorter)
                currentLvl = lvl
        out.sort()
        return out
    def _filterRarities(self, auctions:List[Sorter])->List[Sorter]:
        if not len(auctions): return []
        if isinstance(auctions[0]["auctClass"], NORAuctionProduct): return auctions # not supported

        raritiy = self.raritySelectC.getValue()
        if raritiy.lower() == "all": return auctions
        out = []
        for sorter in auctions:
            auction: BaseAuctionProduct = sorter["auctClass"]
            rar = auction.getRarity()
            if rar.upper() == raritiy.upper():
                out.append(sorter)
        return out
    def filterAuctions(self, auctions:List[Sorter])->List[Sorter]:
        if not len(auctions): return []
        out = auctions.copy()
        out = self._filterRarities(out)
        if self.menuMode == "pet":
            if self.check_filterC.getValue():
                out = self._filterPets(out)
        return out

    def viewSelectedItem(self):
        index = self.treeView.getSelectedIndex()
        if index is None: return
        self.clearMenu()
        auct = self.shownAuctions[index]
        self.selectedItem = auct.getID()
        self.showOwnAuctions = False
        self.updateTreeView()
    def copyURL(self):
        sel = self.treeView.getSelectedIndex()
        if not len(sel): return
        index = sel[0]
        auction = self.shownAuctions[index]
        copyStr(f"/viewauction {auction.getAuctionID()}")

    def placeMainWidgets(self):
        self.searchL.placeRelative(fixHeight=25, stickDown=True, fixWidth=75, fixX=150)
        self.searchE.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=250)
    def removeWidgets(self):
        self.searchE.placeForget()
        self.searchL.placeForget()
    def _clearAndUpdate(self):
        self.searchE.clear()
        self.updateTreeView()
        self.searchE.setFocus()
    def updateTreeView(self):
        ownAuctionUUIDs:dict = Config.SETTINGS_CONFIG["auction_creator_uuids"]
        self.treeView.clear()
        if API.SKYBLOCK_AUCTION_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        self.shownAuctions = []
        if self.showOwnAuctions:
            self.searchBtn.setText("< Back")
            if self.auctionType.getValue() == "BIN only":
                self.treeView.setTableHeaders("Display-Name", "BIN-Price", "Ending-In")
                binAuctions = API.SKYBLOCK_AUCTION_API_PARSER.getBinAuctions()
                sorters = []
                for auct in binAuctions:
                    if auct.getCreatorUUID() not in ownAuctionUUIDs.keys(): continue  # own Auction
                    pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                    sorters.append(
                        Sorter(
                            sortKey="bin_price",

                            display_name=auct.getDisplayName()+("" if pName is None else f" ({pName})"),
                            bin_price=auct.getPrice(),
                            ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                            auctClass=auct,
                            isOwn=pName is not None
                        )
                    )
                self.setPageTitle(f"Auction House [Your BIN-Auctions] ({len(sorters)} found)")
                sorters.sort()
                sorters = self.filterAuctions(sorters)
                for auct in sorters:
                    self.shownAuctions.append(auct["auctClass"])
                    self.treeView.addEntry(
                        auct["display_name"],
                        prizeToStr(auct["bin_price"]),
                        "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                        tag=("own", auct['auctClass'].getRarity()) if auct["isOwn"] else ("bin", auct['auctClass'].getRarity())
                    )
                self.treeView.see(-1)
            if self.auctionType.getValue() == "Auctions only":
                self.treeView.setTableHeaders("Display-Name", "Price", "Ending-In", "Bids")
                auctions = API.SKYBLOCK_AUCTION_API_PARSER.getAuctionByID(self.selectedItem)
                sorters = []
                for auct in auctions:
                    if auct.getCreatorUUID() not in ownAuctionUUIDs.keys(): continue # own Auction
                    pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                    sorters.append(
                        Sorter(
                            sortKey="ending_in",

                            display_name=auct.getDisplayName()+("" if pName is None else f" ({pName})"),
                            price=auct.getHighestBid(),
                            ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                            bids=auct.getBidAmount(),
                            auctClass=auct,
                            isOwn=pName is not None
                        )
                    )
                self.setPageTitle(f"Auction House [Your Auctions] ({len(sorters)} found)")
                sorters.sort()
                sorters = self.filterAuctions(sorters)
                for auct in sorters:
                    self.shownAuctions.append(auct["auctClass"])
                    self.treeView.addEntry(
                        auct["display_name"],
                        prizeToStr(auct["price"]),
                        "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                        prizeToStr(auct["bids"], hideCoins=True),
                        tag=("own", auct['auctClass'].getRarity()) if auct["isOwn"] else ("auc", auct['auctClass'].getRarity())
                    )
                self.treeView.see(-1)
            self.configureMenu(self.shownAuctions)
        elif self.selectedItem is None: # show all
            self.searchBtn.setText("Show My Auctions")
            self.placeMainWidgets()
            if self.searchE.getValue() == "":
                validItems = None
            else:
                validItems = search([AuctionItemID], self.searchE.getValue(), printable=False)

            if self.auctionType.getValue() == "BIN only":
                self.setPageTitle(f"Auction House [BIN]")
                metaSorters = []
                ownAuctionIDs = set()
                self.treeView.setTableHeaders("Name", "Lowest-BIN", "Highest-BIN", "Active-Auctions")
                for auct_ID, active in zip(*API.SKYBLOCK_AUCTION_API_PARSER.getBinTypeAndAuctions()):
                    if auct_ID is None: continue # auction Items that cannot be registered
                    if validItems is not None and auct_ID not in validItems: continue
                    sorters = []
                    if not len(active): continue
                    for auction in active:
                        pName = None
                        if auction.getCreatorUUID() in ownAuctionUUIDs.keys():  # own Auction
                            pName = ownAuctionUUIDs[auction.getCreatorUUID()]
                            ownAuctionIDs.add(auction.getID())
                        sorters.append(
                            Sorter(
                                sortKey="price".lower(),

                                name=auction.getID() + ("" if pName is None else f" ({pName})"),
                                price=auction.getPrice(),
                                auctClass=auction,
                            )
                        )
                    sorters.sort()
                    metaSorters.append(
                        Sorter(
                            sortKey="lowest_bin".lower(),

                            name=sorters[0]["name"],
                            lowest_bin=sorters[-1]["price"],
                            highest_bin=sorters[0]["price"],
                            active_auctions=len(sorters),
                            auctClass=sorters[0]["auctClass"]
                        )
                    )
                metaSorters.sort()
                metaSorters = self.filterAuctions(metaSorters)
                for metaSorter in metaSorters:
                    self.shownAuctions.append(metaSorter["auctClass"])
                    self.treeView.addEntry(
                        metaSorter["name"] + (f" (Contains active Auction)" if metaSorter['name'] in ownAuctionIDs else ""),
                        prizeToStr(metaSorter["lowest_bin"]),
                        prizeToStr(metaSorter["highest_bin"]),
                        prizeToStr(metaSorter["active_auctions"], hideCoins=True),
                        tag=("own", metaSorter['auctClass'].getRarity()) if metaSorter['name'] in ownAuctionIDs else ("bin", metaSorter['auctClass'].getRarity())
                    )
            if self.auctionType.getValue() == "Auctions only":
                self.setPageTitle(f"Auction House [AUCTIONS]")
                metaSorters = []
                ownAuctionIDs = set()
                self.treeView.setTableHeaders("Name", "Lowest-Bid", "Ending-In", "Active-Auctions")
                for auct_ID, active in zip(*API.SKYBLOCK_AUCTION_API_PARSER.getAucTypeAndAuctions()):
                    if auct_ID is None: continue  # auction Items that cannot be registered
                    if validItems is not None and auct_ID not in validItems: continue
                    sorters = []
                    if not len(active): continue
                    for auction in active:
                        if auction.getCreatorUUID() in ownAuctionUUIDs.keys():  # own Auction
                            ownAuctionIDs.add(auction.getID())
                        sorters.append(
                            Sorter(
                                sortKey="price".lower(),

                                name=auction.getID(),
                                price=auction.getHighestBid(),
                                ending=parseTimeDelta(auction.getEndIn()).toSeconds(),
                                auctClass=auction,
                            )
                        )
                    sorters.sort()
                    metaSorters.append(
                        Sorter(
                            sortKey="lowest_bid".lower(),

                            name=sorters[0]["name"],
                            lowest_bid=sorters[-1]["price"],
                            ending=sorters[-1]["ending"],
                            active_auctions=len(sorters),
                            auctClass=sorters[0]["auctClass"]
                        )
                    )
                metaSorters.sort()
                metaSorters = self.filterAuctions(metaSorters)
                for metaSorter in metaSorters:
                    self.shownAuctions.append(metaSorter["auctClass"])
                    self.treeView.addEntry(
                        metaSorter["name"] + (f" (Contains active Auction)" if metaSorter['name'] in ownAuctionIDs else ""),
                        prizeToStr(metaSorter["lowest_bid"]),
                        parseTimeFromSec(metaSorter["ending"]),
                        prizeToStr(metaSorter["active_auctions"], hideCoins=True),
                        tag=("own", metaSorter['auctClass'].getRarity()) if metaSorter['name'] in ownAuctionIDs else ("auc", metaSorter['auctClass'].getRarity())
                    )
            self.configureMenu(self.shownAuctions)
        else:
            self.searchBtn.setText("< Back")
            self.removeWidgets()
            if self.auctionType.getValue() == "BIN only":
                self.treeView.setTableHeaders("Display-Name", "BIN-Price", "Ending-In")
                binAuctions = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(self.selectedItem)
                self.setPageTitle(f"Auction House [{self.selectedItem}] ({len(binAuctions)} found)")
                sorters = []
                for auct in binAuctions:
                    pName = None
                    if auct.getCreatorUUID() in ownAuctionUUIDs.keys():  # own Auction
                        pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                    sorters.append(
                        Sorter(
                            sortKey="bin_price",

                            display_name=auct.getDisplayName()+("" if pName is None else f" ({pName})"),
                            bin_price=auct.getPrice(),
                            ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                            auctClass=auct,
                            isOwn=pName is not None
                        )
                    )
                sorters.sort()
                sorters = self.filterAuctions(sorters)
                for auct in sorters:
                    self.shownAuctions.append(auct["auctClass"])

                    self.treeView.addEntry(
                        auct["display_name"],
                        prizeToStr(auct["bin_price"]),
                        "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                        tag=("own", auct['auctClass'].getRarity()) if auct["isOwn"] else ("bin", auct['auctClass'].getRarity())
                    )
                self.treeView.see(-1)
            if self.auctionType.getValue() == "Auctions only":
                self.treeView.setTableHeaders("Display-Name", "Price", "Ending-In", "Bids")
                auctions = API.SKYBLOCK_AUCTION_API_PARSER.getAuctionByID(self.selectedItem)
                self.setPageTitle(f"Auction House [{self.selectedItem}] ({len(auctions)} found)")
                sorters = []
                for auct in auctions:
                    pName = None
                    if auct.getCreatorUUID() in ownAuctionUUIDs.keys(): # own Auction
                        pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                    sorters.append(
                        Sorter(
                            sortKey="ending_in",

                            display_name=auct.getDisplayName()+("" if pName is None else f" ({pName})"),
                            price=auct.getHighestBid(),
                            ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                            bids=auct.getBidAmount(),
                            auctClass=auct,
                            isOwn=pName is not None
                        )
                    )
                sorters.sort()
                sorters = self.filterAuctions(sorters)
                for auct in sorters:
                    self.shownAuctions.append(auct["auctClass"])
                    self.treeView.addEntry(
                        auct["display_name"],
                        prizeToStr(auct["price"]),
                        "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                        prizeToStr(auct["bids"], hideCoins=True),
                        tag=("own", auct['auctClass'].getRarity()) if auct["isOwn"] else ("auc", auct['auctClass'].getRarity())
                    )
                self.treeView.see(-1)
            self.configureMenu(self.shownAuctions)
        self.treeView.setBgColorByTag("bin", tk.Color.rgb(138, 90, 12))
        self.treeView.setBgColorByTag("auc", tk.Color.rgb(22, 51, 45))
        self.treeView.setBgColorByTag("own", tk.Color.rgb(26, 156, 17))
        if self.showRarityC.getValue():
            for k, v in iterDict(RARITY_COLOR_CODE):
                self.treeView.setFgColorByTag(k, v)
        else:
            for k, v in iterDict(RARITY_COLOR_CODE):
                self.treeView.setFgColorByTag(k, "white")

    def onBtn(self):
        self.clearMenu()
        if self.selectedItem is not None:
            self.selectedItem = None
        elif self.showOwnAuctions:
            self.selectedItem = None
            self.showOwnAuctions = False
        else:
            self.showOwnAuctions = True
        self.updateTreeView()
    def onRClick(self, e:tk.Event):
        if self.showOwnAuctions:
            self.ownContextM.open(e)
        elif self.selectedItem is not None:
            self.itemContextM.open(e)
    def onDoubleClick(self, e):
        sel = e.getValue()
        if sel is None: return
        if self.selectedItem is None and not self.showOwnAuctions:
            self.selectedItem = (sel["Name"] if "(" not in sel["Name"] else sel["Name"].split("(")[0]).strip()
            self.updateTreeView()
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
class PestProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Pest Profit Page", buttonText="Pest Profit")

        self.selectedPest = None
        self.pestNameMetaSorter = {}

        self.rarePestChances = JsonConfig.loadConfig(os.path.join(CONFIG, "garden_pest_chances_rare.json"))
        self.commonPestChances = JsonConfig.loadConfig(os.path.join(CONFIG, "garden_pest_chances_common.json"))

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.onSingleSelectEvent(self.onSelect)
        self.treeView.setTableHeaders("Pest-Name", "Average-Profit-Per-Pest")
        self.treeView.placeRelative(changeHeight=-25, changeWidth=-300)

        self.frame = tk.LabelFrame(self.contentFrame, SG)
        self.frame.setText("Pest-Details")
        self.frame.placeRelative(fixWidth=300, stickRight=True, changeHeight=-25)

        self.innerFrame1 = tk.LabelFrame(self.frame, SG)
        self.innerFrame1.setText("Common Loot")
        self.commonList = tk.Listbox(self.innerFrame1, SG)
        self.commonList.placeRelative(changeWidth=-5, changeHeight=-20)
        self.innerFrame1.placeRelative(fixY=25, fixHeight=100)

        self.innerFrame2 = tk.LabelFrame(self.frame, SG)
        self.innerFrame2.setText("Rare Loot")
        self.rareList = tk.Listbox(self.innerFrame2, SG)
        self.rareList.placeRelative(changeWidth=-5, changeHeight=-20)
        self.innerFrame2.placeRelative(fixY=125, fixHeight=200)

        self.fullProfit = tk.Label(self.frame, SG)
        self.fullProfit.setFont(15)
        self.fullProfit.placeRelative(fixY=325, fixHeight=25)

        self.pestName = tk.Label(self.frame, SG)
        self.pestName.setFont(19)
        self.pestName.placeRelative(fixHeight=25, changeWidth=-5)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.onSelectEvent(self.updateTreeView)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=0)

        self.farmingFortune = tk.TextEntry(self.contentFrame, SG)
        self.farmingFortune.setText("Farming-Fortune:")
        self.farmingFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["farming_fortune"])
        self.farmingFortune.getEntry().onUserInputEvent(self.updateTreeView)
        self.farmingFortune.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.cropFortune = tk.TextEntry(self.contentFrame, SG)
        self.cropFortune.setText("Crop-Fortune:")
        self.cropFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["crop_fortune"])
        self.cropFortune.getEntry().onUserInputEvent(self.updateTreeView)
        self.cropFortune.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=300)

        self.petChance = tk.TextEntry(self.contentFrame, SG)
        self.petChance.setText("Pet-Luck:")
        self.petChance.setValue(Config.SETTINGS_CONFIG["pest_profit"]["pet_luck"])
        self.petChance.getEntry().onUserInputEvent(self.updateTreeView)
        self.petChance.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=450)

        self.pestsActive = tk.Checkbutton(self.contentFrame, SG)
        self.pestsActive.setText("Bonus-Farming-Fortune")
        self.pestsActive.onSelectEvent(self.onSelect)
        self.pestsActive.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=600)

        self.noneSelected = tk.Label(self.frame, SG)
        self.noneSelected.setText("No Pest Selected!")
    def onSelect(self):
        sel = self.treeView.getSelectedItem()
        if sel is not None:
            self.selectedPest = sel["Pest-Name"]
        elif self.selectedPest is None:
            return
        self.updateTreeView()
        sorter = self.pestNameMetaSorter[self.selectedPest]
        self.pestName.setText(self.selectedPest)

        self.commonList.clear()
        self.rareList.clear()

        self.commonList.add(f"{sorter['itemID']}")
        self.commonList.add(f"Amount-Per-Pest: {sorter['amount']}")
        self.commonList.add(f"Sell-Price: {prizeToStr(sorter['profitCommonSingle'])}")
        self.commonList.add(f"Sell-Price-x{sorter['amount']}: {prizeToStr(sorter['profitCommon'])}")

        self.fullProfit.setText(f"Profit per Pest: {prizeToStr(sorter['profit'])}")

        for sorter in sorter["profitRareSorter"]:
            self.rareList.add(f"{sorter['itemID']}")
            self.rareList.add(f"Chance: {round(sorter['raw_chance'], 2)}% -> {round(sorter['chance'], 2)}%")
            self.rareList.add(f"Average-Pests: {round(sorter['rawAverageNeededPestsForARareDrop'], 2)} -> {round(sorter['averageNeededPestsForARareDrop'], 2)}")
            self.rareList.add(f"Sell-Price: {prizeToStr(sorter['profit_full'])}")
            self.rareList.add(f"Sell-Price / Pest: {prizeToStr(sorter['profit'])}")
            self.rareList.add(f"")
            self.rareList.add(f"")
    def updateTreeView(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        if API.SKYBLOCK_AUCTION_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        isPestsActive = self.pestsActive.getValue()
        if self.selectedPest is None:
            self.noneSelected.placeRelative(changeWidth=-5, changeHeight=-20)
        else:
            self.noneSelected.placeForget()
        farmingFortune = self.farmingFortune.getValue()
        if farmingFortune.isnumeric():
            farmingFortune = int(farmingFortune)
            Config.SETTINGS_CONFIG["pest_profit"]["farming_fortune"] = farmingFortune
            Config.SETTINGS_CONFIG.save()
        elif farmingFortune == "": farmingFortune = 0
        else:
            self.cropFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["farming_fortune"])
            tk.SimpleDialog.askError(self.master, f"Wrong Farming Fortune value! Must be > 0.")
        cropFortune = self.cropFortune.getValue()

        if cropFortune.isnumeric():
            cropFortune = int(cropFortune)
            Config.SETTINGS_CONFIG["pest_profit"]["crop_fortune"] = cropFortune
            Config.SETTINGS_CONFIG.save()
        elif cropFortune == "": cropFortune = 0
        else:
            self.cropFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["crop_fortune"])
            tk.SimpleDialog.askError(self.master, f"Wrong Crop Fortune value! Must be > 0.")
        petLuck = self.petChance.getValue()

        if petLuck.isnumeric():
            petLuck = int(petLuck)
            Config.SETTINGS_CONFIG["pest_profit"]["pet_luck"] = petLuck
            Config.SETTINGS_CONFIG.save()
        elif petLuck == "": petLuck = 0
        else:
            self.petChance.setValue(Config.SETTINGS_CONFIG["pest_profit"]["pet_luck"])
            tk.SimpleDialog.askError(self.master, f"Wrong Pet Luck value! Must be > 0.")
        if isPestsActive: farmingFortune += 200
        """
        The Pest chances are given in percenteges.
        Rare Drops are drops with a basechance lower 5%
        Common Drops are drops with a basechance higher than 5%
        """

        metaSorters = []
        for pestName in self.rarePestChances.keys():
            sorters = []
            for singleDropItemID, dropChance in iterDict(self.rarePestChances[pestName]):

                if singleDropItemID in BazaarItemID: # Bazaar Item!
                    item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(singleDropItemID)

                    if self.useSellOffers.getValue():  # use sell Offer
                        itemSellPrice = item.getInstaBuyPrice()
                    else:  # insta sell
                        itemSellPrice = item.getInstaSellPrice()
                    itemSellPrice = applyBazaarTax(itemSellPrice)
                else:
                    rarity = None
                    if singleDropItemID.endswith("epic"):
                        singleDropItemID = singleDropItemID.replace("_epic", "")
                        rarity = "EPIC"
                    if singleDropItemID.endswith("legendary"):
                        singleDropItemID = singleDropItemID.replace("_legendary", "")
                        rarity = "LEGENDARY"
                    active = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(singleDropItemID)

                    auctSorters = []
                    for auction in active:
                        if rarity is not None:
                            if rarity.lower() != auction.getRarity().lower():
                                continue
                        auctSorters.append(
                            Sorter(
                                sortKey="profit",
                                profit=auction.getPrice(),
                            )
                        )
                    auctSorters.sort()
                    if len(auctSorters) == 0:
                        itemSellPrice = 0
                        MsgText.error(f"Could not calculate price for {singleDropItemID}.")
                    else:
                        itemSellPrice = auctSorters[-1]["profit"]

                if "PET" in singleDropItemID:
                    rareDropChance = dropChance * (1 + (farmingFortune + cropFortune + petLuck) / 600)
                else:
                    rareDropChance = dropChance * (1 + (farmingFortune + cropFortune) / 600)
                averageNeededPestsForARareDrop = 1 / (rareDropChance / 100)
                rawAverageNeededPestsForARareDrop = 1 / (dropChance / 100)
                pestProfitRare = (rareDropChance / 100) * itemSellPrice

                sorters.append(
                    Sorter(
                        sortKey="profit",

                        itemID=singleDropItemID,
                        pestName=pestName,
                        averageNeededPestsForARareDrop=averageNeededPestsForARareDrop,
                        rawAverageNeededPestsForARareDrop=rawAverageNeededPestsForARareDrop,
                        profit=pestProfitRare,
                        profit_full=itemSellPrice,
                        chance=rareDropChance,
                        raw_chance=dropChance,
                    )
                )
            sorters.sort()

            item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(self.commonPestChances[pestName])

            if self.useSellOffers.getValue():  # use sell Offer
                itemSellPrice = item.getInstaBuyPrice()
            else:  # insta sell
                itemSellPrice = item.getInstaSellPrice()
            itemSellPrice = applyBazaarTax(itemSellPrice)

            pestProfitCommon = itemSellPrice * (1+farmingFortune/100)

            metaSorters.append(
                Sorter(
                    sortKey="profit",

                    itemID=self.commonPestChances[pestName],
                    amount=(1+farmingFortune/100),
                    pestName=pestName,
                    profitRareSorter=sorters,
                    profitCommon=pestProfitCommon,
                    profitCommonSingle=itemSellPrice,
                    profit=pestProfitCommon + sum([i["profit"] for i in sorters])
                )
            )
            self.pestNameMetaSorter[pestName] = metaSorters[-1]
        metaSorters.sort()
        for sorter in metaSorters:
            self.treeView.addEntry(
                sorter["pestName"],
                prizeToStr(sorter["profit"])
            )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.onSelect  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
class MagicFindCalculatorPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Magic Find Calculator", buttonText="Magic Find Calculator")

        self.LOOTING_CONST = .15
        self.LUCK_CONST = .05

        """{
            "base_chance":1,
            "pet_luck":0,
            "magic_find":0,
            "magic_find_bestiary":0,
            "looting_lvl":0,
            "luck_lvl":0,
            "item_type":0
        }"""

        mc = RARITY_COLOR_CODE["DIVINE"] # magic find color-code
        pc = RARITY_COLOR_CODE["MYTHIC"] # pet luck color-code
        ec = RARITY_COLOR_CODE["LEGENDARY"] # enchantment color-code
        placer = tk.Placer(25)
        self.baseChanceE = tk.TextEntry(self.contentFrame, SG).setText("Base Chance (1 in)").setFg(ec).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["base_chance"])
        self.petLuckE = tk.TextEntry(self.contentFrame, SG).setText("Pet Luck Stat(in %)").setFg(pc).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["pet_luck"])
        self.magicFindE = tk.TextEntry(self.contentFrame, SG).setText("Magic Find Stat").setFg(mc).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find"])
        self.magicFindBeE = tk.TextEntry(self.contentFrame, SG).setText("Magic Find Bestiary").setFg(mc).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"])
        self.lootingE = tk.TextEntry(self.contentFrame, SG).setText("Looting Enchantment:").setFg(ec).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"])
        self.luckE = tk.TextEntry(self.contentFrame, SG).setText("Luck Enchantment:").setFg(ec).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"])
        tk.Label(self.contentFrame, SG).setText("Item Type:").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)
        self.rad = tk.Radiobutton(self.contentFrame, SG)
        norItem = self.rad.createNewRadioButton(SG).setText("Normal Item").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)
        armor = self.rad.createNewRadioButton(SG).setText("Armor Piece").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)
        pet = self.rad.createNewRadioButton(SG).setText("Pet").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)

        self.rad.setState(Config.SETTINGS_CONFIG["magic_find"]["item_type"])

        self.baseChanceE.getEntry().onUserInputEvent(self.onUpdate)
        self.petLuckE.getEntry().onUserInputEvent(self.onUpdate)
        self.magicFindE.getEntry().onUserInputEvent(self.onUpdate)
        self.magicFindBeE.getEntry().onUserInputEvent(self.onUpdate)
        self.lootingE.getEntry().onUserInputEvent(self.onUpdate)
        self.luckE.getEntry().onUserInputEvent(self.onUpdate)
        self.rad.onSelectEvent(self.onUpdate)

        self.toKillE = tk.Label(self.contentFrame, SG).setText("Actions till drop: ").placeRelative(fixX=300, fixY=0, fixWidth=300, fixHeight=30).setFont(15)
        self.chanceE = tk.Label(self.contentFrame, SG).setText("Chance: ").placeRelative(fixX=300, fixY=30, fixWidth=300, fixHeight=30).setFont(15)
    def onUpdate(self):
        self.toKillE.setText("Actions till drop: ")
        self.chanceE.setText("Chance: ")

        state = self.rad.getState()
        baseChance = self.baseChanceE.getValue()
        petLuck = self.petLuckE.getValue()
        magicFind = self.magicFindE.getValue()
        magicFindBe = self.magicFindBeE.getValue()
        luck = self.luckE.getValue()
        looting = self.lootingE.getValue()


        if baseChance.isnumeric():
            baseChance = int(baseChance)
            Config.SETTINGS_CONFIG["magic_find"]["base_chance"] = baseChance
            Config.SETTINGS_CONFIG.save()
        elif baseChance == "": baseChance = Config.SETTINGS_CONFIG["magic_find"]["base_chance"]
        else:
            self.baseChanceE.setValue(Config.SETTINGS_CONFIG["magic_find"]["base_chance"])
            tk.SimpleDialog.askError(self.master, f"Wrong base_chance value! Must be > 0.")
            return
        if petLuck.isnumeric():
            petLuck = int(petLuck)
            Config.SETTINGS_CONFIG["magic_find"]["pet_luck"] = petLuck
            Config.SETTINGS_CONFIG.save()
        elif petLuck == "": petLuck = Config.SETTINGS_CONFIG["magic_find"]["pet_luck"]
        elif state == 2: # pets
            self.petLuckE.setValue(Config.SETTINGS_CONFIG["magic_find"]["pet_luck"])
            tk.SimpleDialog.askError(self.master, f"Wrong pet_luck value! Must be > 0.")
            return
        if magicFind.isnumeric():
            magicFind = int(magicFind)
            Config.SETTINGS_CONFIG["magic_find"]["magic_find"] = magicFind
            Config.SETTINGS_CONFIG.save()
        elif magicFind == "": magicFind = Config.SETTINGS_CONFIG["magic_find"]["magic_find"]
        else:
            self.magicFindE.setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find"])
            tk.SimpleDialog.askError(self.master, f"Wrong magic_find value! Must be > 0.")
            return
        if magicFindBe.isnumeric():
            magicFindBe = int(magicFindBe)
            Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"] = magicFindBe
            Config.SETTINGS_CONFIG.save()
        elif magicFindBe == "": magicFindBe = Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"]
        else:
            self.magicFindBeE.setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"])
            tk.SimpleDialog.askError(self.master, f"Wrong magic_find_bestiary value! Must be > 0.")
            return
        if luck.isnumeric():
            luck = int(luck)
            Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"] = luck
            Config.SETTINGS_CONFIG.save()
        elif luck == "": luck = Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"]
        elif state == 1:
            self.luckE.setValue(Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"])
            tk.SimpleDialog.askError(self.master, f"Wrong luck_lvl value! Must be > 0.")
            return
        if looting.isnumeric():
            looting = int(looting)
            Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"] = looting
            Config.SETTINGS_CONFIG.save()
        elif looting == "": looting = Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"]
        elif state == 0:
            self.lootingE.setValue(Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"])
            tk.SimpleDialog.askError(self.master, f"Wrong looting_lvl value! Must be > 0.")
            return

        if state == 0: add = (looting*self.LOOTING_CONST) # item
        if state == 1: add = (luck*self.LUCK_CONST) # armor
        if state == 2: add = (petLuck/100) # pet

        magicFind += magicFindBe
        baseChance = 1/baseChance

        newChance = baseChance * (1+(magicFind/100)+add)

        self.toKillE.setText(f"Actions till drop: {prizeToStr(round(1/newChance, 2), True)}")
        self.chanceE.setText(f"Chance: {round(newChance*100, 5)}%")
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.onUpdate  # hook to update tv on new API-Data available
        self.placeRelative()
        self.onUpdate()
        self.placeContentFrame()
        tk.SimpleDialog.askWarning(self.master, "This feature does not work properly at the moment, due a wrong and outdated magicfind formular.")
class ItemPriceTrackerPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Price Tracker", buttonText="Price Tracker")
        self._notificationsDisabled = False

        self.customTrackers = TrackerWidget(self.contentFrame, master, "Custom-Tracker")
        self.flipTrackers = TrackerWidget(self.contentFrame, master, "Flip-Tracker")
        self.crashTrackers = TrackerWidget(self.contentFrame, master, "Crash-Tracker")
        self.manipulationTrackers = TrackerWidget(self.contentFrame, master, "Manipulation-Tracker")

        self.customTrackers.setUpdateHook(self.onUpdate)
        self.flipTrackers.setUpdateHook(self.onUpdate)
        self.crashTrackers.setUpdateHook(self.onUpdate)
        self.manipulationTrackers.setUpdateHook(self.onUpdate)

        self.customTrackers.placeRelative(xOffsetRight=50, yOffsetDown=50)
        self.crashTrackers.placeRelative(xOffsetLeft=50, yOffsetDown=50)
        self.flipTrackers.placeRelative(xOffsetRight=50, yOffsetUp=50)
        self.manipulationTrackers.placeRelative(xOffsetLeft=50, yOffsetUp=50)

        self.customTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)
        self.crashTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)
        self.manipulationTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)
        self.flipTrackers.notify.onSelectEvent(self.updateNotificationFromCheck)

        self.updateNotificationFromSettings()
        self.customTrackers.showType.placeForget()
    def updateNotificationFromSettings(self):
        self.customTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_custom"])
        self.crashTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_crash"])
        self.flipTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_flip"])
        self.manipulationTrackers.notify.setState(Config.SETTINGS_CONFIG["notifications"]["tracker_manipulation"])
    def updateNotificationFromCheck(self):
        Config.SETTINGS_CONFIG["notifications"]["tracker_custom"] = self.customTrackers.notify.getValue()
        Config.SETTINGS_CONFIG["notifications"]["tracker_crash"] = self.crashTrackers.notify.getValue()
        Config.SETTINGS_CONFIG["notifications"]["tracker_flip"] = self.flipTrackers.notify.getValue()
        Config.SETTINGS_CONFIG["notifications"]["tracker_manipulation"] = self.manipulationTrackers.notify.getValue()
        Config.SETTINGS_CONFIG.save()
    def onUpdate(self):
        """
        Triggers update after new Average request!
        @return:
        """
        updateBazaarAnalyzer()
        self.updateTreeView()
    def addNewCustomItem(self):
        pass
    def updateTreeView(self):
        notify = False
        self.manipulationTrackers.treeView.clear()
        manipulated = BazaarAnalyzer.getManipulatedItems()
        containsNew = False
        filterEnchantments = self.manipulationTrackers.filterEnchantments.getState()
        for sorter, _time in manipulated:
            if sorter["ID"].startswith("ENCHANTMENT_") and filterEnchantments: continue
            self.manipulationTrackers.treeView.addEntry(
                sorter["ID"],
                prizeToStr(sorter["buyOrderPrice"], True),
                prizeToStr(sorter["sellOrderPrice"], True),
                prizeToStr(sorter["priceDifference"], True) + ("" if sorter["priceDifferenceChance"] == 0 else f" ({prizeToStr(sorter['priceDifferenceChance'], True, True)})"),
                parseTimeFromSec(time()-_time),

                tag=sorter["manipulatedState"]
            )
            if sorter["manipulatedState"] == "new":
                containsNew = True
        self.manipulationTrackers.setText(f"Manipulation-Tracker [{self.manipulationTrackers.treeView.getSize()}]")
        self.manipulationTrackers.treeView.setBgColorByTag("old", Color.COLOR_DARK)
        self.manipulationTrackers.treeView.setBgColorByTag("new", "green")
        if self.manipulationTrackers.notify.getState():
            if containsNew: notify = True
        containsNew = False


        self.crashTrackers.treeView.clear()
        crashed = BazaarAnalyzer.getCrashedItems()
        crashed.sort()
        filterEnchantments = self.crashTrackers.filterEnchantments.getState()
        for sorter, _time in crashed:
            if sorter["ID"].startswith("ENCHANTMENT_") and filterEnchantments: continue
            self.crashTrackers.treeView.addEntry(
                sorter["ID"],
                prizeToStr(sorter["buyOrderPrice"], True),
                prizeToStr(sorter["sellOrderPrice"], True),
                prizeToStr(sorter["priceDifference"], True) + ("" if sorter["priceDifferenceChance"] == 0 else f" ({prizeToStr(sorter['priceDifferenceChance'], True, True)})"),
                parseTimeFromSec(time() - _time),
                tag=sorter["crashedState"]
            )
            if sorter["crashedState"] == "new":
                containsNew = True
        self.crashTrackers.setText(f"Crash-Tracker [{self.crashTrackers.treeView.getSize()}]")
        if self.crashTrackers.notify.getState():
            if containsNew: notify = True
        self.crashTrackers.treeView.setBgColorByTag("old", Color.COLOR_DARK)
        self.crashTrackers.treeView.setBgColorByTag("new", "green")

        if notify and not self._notificationsDisabled:
            playNotificationSound()
        self._notificationsDisabled = False
    def disableNotifications(self):
        self._notificationsDisabled = True
        return self
    def onAPIUpdate(self):
        self.updateTreeView()
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = None # hook to update tv on new API-Data available
        self.placeRelative()
        self.disableNotifications()
        self.updateTreeView()
        self.placeContentFrame()
        if not Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"]: tk.SimpleDialog.askWarning(self.master, "This feature requires 'auto_api_requests' feature to be active!\nTurn on In Settings or in the opper left corner in MainMenu!")
class AccessoryBuyHelperAccount(tk.Dialog):
    def __init__(self, page, master, updHook, data=None):
        super().__init__(master, SG)
        self.page = page
        self.master = master
        self.updHook = updHook
        self.accessories = [] if data is None else data["accessories"]
        self.setWindowSize(800, 800)
        self.setMinSize(500, 800)
        self.setCloseable(False)

        if data is None:
            self.edit = False
            self.setTitle("Account")
        else:
            self.edit = True
            self.setTitle(f"{data['name']}-Account")

        self.treeView = tk.TreeView(self, SG)
        self.treeView.setTableHeaders("Name", "Recomb", "Enrichment", "Rarity")
        self.treeView.placeRelative(fixX=200, changeHeight=-100)

        self.toolFrame = tk.LabelFrame(self, group=SG)
        self.toolFrame.setText("Account")
        self.toolFrame.placeRelative(fixWidth=200)

        self.nameEntry = tk.TextEntry(self.toolFrame, group=SG)
        self.nameEntry.setText("Name:")
        if data is not None:
            self.nameEntry.getEntry().setValue(data['name'])
            self.nameEntry.getEntry().disable()
        self.nameEntry.placeRelative(fixWidth=195, fixHeight=25)

        self.slotsFrame = tk.LabelFrame(self.toolFrame, SG)
        self.slotsFrame.setText("Slots [0]")
        self.slotsFrame.place(0, 25, 195, 95+27)

        tk.Label(self.slotsFrame, SG).setText("Redstone Collec:").place(0, 0, 106, 25)
        tk.Label(self.slotsFrame, SG).setText("Redstone Miner:").place(0, 25, 106, 25)
        tk.Label(self.slotsFrame, SG).setText("Community Shop:").place(0, 50, 106, 25)
        tk.Label(self.slotsFrame, SG).setText("Jacobus Slots:").place(0, 75, 106, 25)

        self.redsColDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 0, 86, 25).onSelectEvent(self.select)
        self.redsMinerDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 25, 86, 25).onSelectEvent(self.select)
        self.communityDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 50, 86, 25).onSelectEvent(self.select)
        self.jacobusDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 75, 86, 25).onSelectEvent(self.select)

        self.redsColDrop.setOptionList([f"lvl{k} ({v} Slots)" for k, v in page.slotsConfig["redstone_collection"].items()])
        self.redsMinerDrop.setOptionList(["0", "1", "2", "3", "4"])
        self.communityDrop.setOptionList([f"lvl{k} ({v} Slots)" for k, v in page.slotsConfig["community_centre"].items()])
        self.jacobusDrop.setOptionList([f"{i} Slots" for i in range(0, 200, 2)])

        if data is not None:
            self.redsColDrop.setValueByIndex(data["redstone_collection"])
            self.redsMinerDrop.setValueByIndex(data["redstone_miner"])
            self.communityDrop.setValueByIndex(data["community_centre"])
            self.jacobusDrop.setValueByIndex(data["jacobus"])
            self.select()
        else:
            self.redsColDrop.setValueByIndex(0)
            self.redsMinerDrop.setValueByIndex(0)
            self.communityDrop.setValueByIndex(0)
            self.jacobusDrop.setValueByIndex(0)

        self.accessoriesFrame = tk.LabelFrame(self.toolFrame, SG)
        self.accessoriesFrame.setText("Accessories")
        self.accessoriesFrame.place(0, 174, 195, 100+20)

        tk.Button(self.accessoriesFrame, SG).setText("Add Accessory").place(0, 0, 192, 25).setDisabled()
        tk.Button(self.accessoriesFrame, SG).setText("Edit Accessory").place(0, 25, 192, 25).setDisabled()
        tk.Button(self.accessoriesFrame, SG).setText("Remove Accessory").place(0, 50, 192, 25).setDisabled()
        tk.Button(self.accessoriesFrame, SG).setText("Import Accessories").place(0, 75, 192, 25).setCommand(self.importAccessories)


        if data is None: self.cancel = tk.Button(self.toolFrame, SG).setText("Cancel").placeRelative(fixHeight=25, changeWidth=-3, stickDown=True, changeY=-45).setCommand(self.destroy)
        self.close = tk.Button(self.toolFrame, SG).setText("Save & Close").placeRelative(fixHeight=25, changeWidth=-3, stickDown=True, changeY=-20).setCommand(self.close)

        if self.edit: self.updateTreeView()
        self.show()
    def importAccessories(self):
        def request(playerName, profileName):
            url = f"https://sky.shiiyu.moe/api/v2/talismans/{playerName}/{profileName.lower()}"
            try:
                val =  getReq(url).json()
            except ConnectionError:
                tk.SimpleDialog.askError(self.master, "An Exception occurred while connecting to API.\nCheck your internet connection.")
                return
            except ReadTimeout:
                tk.SimpleDialog.askError(self.master, "Timeout Exception occurred!")
                return
            self.accessories.clear()
            for acc in val["accessories"]["accessories"]:
                if acc["isInactive"]:
                    continue
                accData = {
                    "id": acc["tag"]["ExtraAttributes"]["id"],
                    "recomb": acc["recombobulated"],
                    "enrichment": True if "enrichment" in acc.keys() else False,
                    "rarity": acc["rarity"].upper(),
                }
                self.accessories.append(accData)
            self.save()
            self.updateTreeView()
        data = tk.SimpleDialog.askUsernamePassword(self.master,
                                                   initialUname=self.nameEntry.getValue(),
                                                   unameString="Player Name",
                                                   passwString="Profile",
                                                   hidePassword=False
                                                   )
        if data is None: return
        Thread(target=request, args=data).start()
    def select(self):
        self.slotsFrame.setText(f"Slots [{self.getTotalSlots()}]")
    def check(self):
        if self.nameEntry.getValue() == "":
            tk.SimpleDialog.askError(self.master, "Player name cannot be empty!")
            return False
        return True
    def updateTreeView(self):
        self.treeView.clear()
        for acc in Config.SETTINGS_CONFIG["accessories"][self.nameEntry.getValue()]["accessories"]:
            self.treeView.addEntry(acc["id"], acc["recomb"], acc["enrichment"], acc["rarity"].lower())
    def close(self):
        if self.check():
            self.save()
            self.updHook(self.nameEntry.getValue())
            self.destroy()
    def save(self):
        Config.SETTINGS_CONFIG["accessories"][self.nameEntry.getValue()] = self.getData()
        Config.SETTINGS_CONFIG.save()
    def getData(self):
        return {
            "name":self.nameEntry.getValue(),
            "redstone_collection":self.redsColDrop.getSelectedIndex(),
            "redstone_miner":self.redsMinerDrop.getSelectedIndex(),
            "community_centre":self.communityDrop.getSelectedIndex(),
            "jacobus":self.jacobusDrop.getSelectedIndex(),
            "slots":self.getTotalSlots(),
            "powder":0,
            "accessories":self.accessories
        }
    def getTotalSlots(self):
        slots = self.redsMinerDrop.getSelectedIndex()
        slots += list(self.page.slotsConfig["redstone_collection"].values())[self.redsColDrop.getSelectedIndex()]
        slots += list(self.page.slotsConfig["community_centre"].values())[self.communityDrop.getSelectedIndex()]
        slots += self.jacobusDrop.getSelectedIndex() * 2
        return slots
class AccessoryBuyHelperPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Accessory Buy Helper Page", buttonText="Accessory Buy Helper")
        self.master: Window = master

        self.conflictsConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "accessories_conflicts.json"))
        self.soulboundConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "accessories_soulbound.json"))
        self.ignoreConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "accessories_ignore.json"))
        self.slotsConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "accessories_buy_slots.json"))
        self.jacobusPricesConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "accessories_jacobus_prices.json"))

        self.toolFrame = tk.LabelFrame(self.contentFrame, group=SG)
        self.toolFrame.setText("Tools")
        self.toolFrame.placeRelative(fixWidth=200)

        self.treeView = tk.TreeView(self.contentFrame, group=SG)
        self.treeView.setTableHeaders("Name", "Action", "Price", "PricePerMp")
        self.treeView.placeRelative(fixX=200, changeHeight=-100)

        self.resFrame = tk.LabelFrame(self.contentFrame, group=SG)
        self.resFrame.setText("Result")
        self.resFrame.placeRelative(fixX=200, stickDown=True, fixHeight=100)

        self.statsFrame = tk.LabelFrame(self.resFrame, group=SG)
        self.statsFrame.setText("Stats")
        self.statsFrame.placeRelative(0, 0, 400, 80)

        self.powderPlusLabel = tk.Label(self.statsFrame, SG).setTextOrientation()
        self.powderPlusLabel.setText("Powder Gain: +0")
        self.powderPlusLabel.setFg(tk.Color.GREEN)
        self.powderPlusLabel.setFont(15)
        self.powderPlusLabel.place(0, 0, 390, 25)

        self.newTotalPowderLabel = tk.Label(self.statsFrame, SG).setTextOrientation()
        self.newTotalPowderLabel.setText("New Total Powder: 0")
        self.newTotalPowderLabel.setFg(tk.Color.GREEN)
        self.newTotalPowderLabel.setFont(15)
        self.newTotalPowderLabel.place(0, 25, 390, 25)

        self.buyFrame = tk.LabelFrame(self.resFrame, group=SG)
        self.buyFrame.setText("Cost")
        self.buyFrame.placeRelative(400, 0, 800, 80)

        self.recombLabel = tk.Label(self.buyFrame, SG).setTextOrientation()
        self.recombLabel.setText("Recombs: +0")
        self.recombLabel.setFont(15)
        self.recombLabel.place(0, 0, 400, 25)

        self.slotsLabel = tk.Label(self.buyFrame, SG).setTextOrientation()
        self.slotsLabel.setText("Slots: +0")
        self.slotsLabel.setFont(15)
        self.slotsLabel.place(0, 25, 400, 25)

        self.totalLabel = tk.Label(self.buyFrame, SG).setTextOrientation()
        self.totalLabel.setText("Total: 0 coins")
        self.totalLabel.setFont(15)
        self.totalLabel.place(400, 0, 395, 25)

        self.accFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.accFrame.setText("Account")
        self.accFrame.place(0, 0, 195, 69)

        self.accDrop = tk.DropdownMenu(self.accFrame, group=SG, readonly=True)
        self.accDrop.onSelectEvent(self.changeAccount)
        self.accDrop.place(0, 0, 192, 25)

        self.add = tk.Button(self.accFrame, group=SG)
        self.add.setText("Add")
        self.add.setCommand(self.addNewAccount)
        self.add.place(0, 25, 64, 25)

        self.edit = tk.Button(self.accFrame, group=SG)
        self.edit.setText("Edit")
        self.edit.setCommand(self.editAccount)
        self.edit.place(64, 25, 64, 25)

        self.rem = tk.Button(self.accFrame, group=SG)
        self.rem.setText("Remove")
        self.rem.setCommand(self.removeAccount)
        self.rem.place(64*2, 25, 64, 25)

        self.investFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.investFrame.setText("Invest")
        self.investFrame.place(0, 69, 195, 69)

        self.investEntry = tk.TextEntry(self.investFrame, group=SG)
        self.investEntry.setText("Invest (coins):")
        self.investEntry.getEntry().onUserInputEvent(self.updateHelper)
        self.investEntry.placeRelative(fixWidth=192, fixHeight=25)

        self.statsFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.statsFrame.setText("Stats")
        self.statsFrame.place(0, 138, 195, 200)

        self.statsText = tk.Text(self.statsFrame, SG, readOnly=True)
        self.statsText.placeRelative(changeHeight=-20, changeWidth=-5)

        self.filterFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.filterFrame.setText("Filter")
        self.filterFrame.place(0, 338, 195, 200)

        self.filterNotBuyableCheck = tk.Checkbutton(self.filterFrame, SG)
        self.filterNotBuyableCheck.setSelected()
        self.filterNotBuyableCheck.onSelectEvent(self.updateHelper)
        self.filterNotBuyableCheck.setText("Hide 'Not Buyable' Items")
        self.filterNotBuyableCheck.place(0, 0, 192, 25)

        self.updateAccounts(None)
        self.accessories = None
    def removeAccount(self):
        name = self.accDrop.getValue()
        if name == "": return
        if tk.SimpleDialog.askOkayCancel(self.master, f"Delete data from player {name}?"):
            Config.SETTINGS_CONFIG["accessories"].pop(name)
            Config.SETTINGS_CONFIG.save()
            self.accDrop.clear()
            self.updateAccounts(None)
            self.updateHelper()
    def addNewAccount(self):
        account = AccessoryBuyHelperAccount(self, self.master, self.updateAccounts)
    def editAccount(self):
        name = self.accDrop.getValue()
        if name == "": return
        account = AccessoryBuyHelperAccount(self, self.master, self.updateAccounts, data=Config.SETTINGS_CONFIG["accessories"][name])
    def changeAccount(self):
        self.updateHelper()
    def getPowder(self, data):
        powder = 0
        for i in data:
            powder += MAGIC_POWDER[i["rarity"].upper()]
        return powder
    def updateAccounts(self, name):
        self.accDrop.setOptionList(list(Config.SETTINGS_CONFIG["accessories"].keys()))
        if name is not None:
            self.accDrop.setValue(name)
            self.updateHelper()
    def getMagicPoderDiffToNext(self, old):
        rarities = list(MAGIC_POWDER.keys())
        new = rarities[rarities.index(old) + 1]
        return MAGIC_POWDER[new] - MAGIC_POWDER[old]
    def getMagicPoderDiff(self, old, new):
        return MAGIC_POWDER[new] - MAGIC_POWDER[old]
    def updateHelper(self):
        self.accessories = [{"id":i.getID(), "rarity":(i.getRarity() if i.getRarity() is not None else "COMMON")} for i in API.SKYBLOCK_ITEM_API_PARSER.getItems() if i.getCategory() == "ACCESSORY"]
        self.treeView.clear()
        self.statsText.clear()
        name = self.accDrop.getValue()

        self.powderPlusLabel.setText(f"Powder Gain: +{0}")
        self.recombLabel.setText(f"Recombs: +{0} ({0} coins)")
        self.slotsLabel.setText(f"Slots: +{0} ()")
        self.totalLabel.setText(f"Total: {0} coins")
        self.newTotalPowderLabel.setText(f"New Total Powder: {0}")

        if name == "": return
        data = Config.SETTINGS_CONFIG["accessories"][name]
        slots = data["slots"]
        slotsUsed = len(data["accessories"])
        powderAllOld = self.getPowder(data["accessories"])
        ownedIDs = [i["id"] for i in data["accessories"]]
        notOwned = []
        notOwnedSoulbound = []
        piggies = [
            "BROKEN_PIGGY_BANK",
            "CRACKED_PIGGY_BANK",
            "PIGGY_BANK"
        ]
        isPiggyPreset = False
        budget = parsePrice(self.investEntry.getValue())
        filterNotBuyableCheck = self.filterNotBuyableCheck.getValue()

        recomb = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("RECOMBOBULATOR_3000")
        if recomb is None:
            tk.SimpleDialog.askError(self.master, "Error getting 'RECOMBOBULATOR_3000' price from api!")
            return
        recombPrice = recomb.getInstaSellPrice() + .1
        if recombPrice == 0:
            tk.SimpleDialog.askError(self.master, "Error getting 'RECOMBOBULATOR_3000' price from api!")
            return

        self.statsText.addLine(f"Name: {name}")
        self.statsText.addLine(f"Slots used: [{slotsUsed}/{slots}]")
        self.statsText.addLine(f"Magic Powder: {powderAllOld}")

        sorters = []

        for acc in self.accessories:
            id_ = acc["id"]
            if id_ in piggies:
                isPiggyPreset = True
        # ignore acc
            if id_ in self.ignoreConfig: continue
        # remove soulbound
            if id_ not in ownedIDs:
                if id_ in self.soulboundConfig:
                    notOwnedSoulbound.append(acc)
                else:
                    notOwned.append(acc)
        # remove conflicts
        for acc in data["accessories"]:
            id_ = acc["id"]
            for conflict in self.conflictsConfig:
                if id_ in conflict:
                    for rem in conflict[:conflict.index(id_)]:
                        for i, val in enumerate(notOwned.copy()):
                            if val["id"] == rem:
                                notOwned.remove(val)
                                break
                    break
        ### NOT OWNED accessories ###
        for acc in notOwned:
            if isPiggyPreset and acc["id"] in piggies: continue
            price = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(acc["id"])
            price.sort()
            price = price[-1].getPrice() if len(price) > 0 else None
            rarity = acc["rarity"].upper()
            powder = MAGIC_POWDER[rarity]
            pricePerMP = None if price is None else (price/powder)

            recomb = False
            action = "buy"



            #check recomb
            if price is not None:
                price2 = price + recombPrice
                rarities = list(MAGIC_POWDER.keys())
                rarity2 = rarities[rarities.index(rarity) + 1]
                powder2 = MAGIC_POWDER[rarity2]

                pricePerMP2 = None if price2 is None else (price2/powder2)

                if pricePerMP2 < pricePerMP:
                    action = "buy & Recomb"
                    pricePerMP = pricePerMP2
                    price = price2
                    recomb = True
            if price is None:
                action = "Not buyable!"
                if filterNotBuyableCheck:
                    continue

            sorters.append(
                Sorter(
                    sortKey="pricePerMP",
                    id=acc["id"],
                    pricePerMP=pricePerMP,
                    price=price,
                    powder=powder,
                    rarity=rarity,
                    action=action,
                    slots=None,
                    recomb=recomb,
                )
            )
        sorters.sort()

        remaingSlots = slots - slotsUsed

        if remaingSlots > 0:
            for i, sorter in enumerate(sorters[::-1][remaingSlots+1:]):
                jacobusSlotPrice = self.jacobusPricesConfig[data["jacobus"] + 1 + i//2] / 2
                sorter["price"] = sorter["price"]+jacobusSlotPrice
                sorter["action"] += f" & buy Slot ({prizeToStr(jacobusSlotPrice)})"
                sorter["pricePerMP"] = sorter["price"] / sorter["powder"]
                sorter["slots"] = (1, jacobusSlotPrice)


        ### OWNED accessories ###
        for acc in data["accessories"]:

            price = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(acc["id"])
            price.sort()
            price = price[-1].getPrice() if len(price) > 0 else None
            rarity = acc["rarity"].upper()
            powder = MAGIC_POWDER[rarity]

            # check recomb

            if acc["recomb"]: continue
            rarities = list(MAGIC_POWDER.keys())
            rarity2 = rarities[rarities.index(rarity) + 1]
            powder2diff = MAGIC_POWDER[rarity2] - powder
            pricePerMP = recombPrice / powder2diff
            price2 = recombPrice
            action = "recomb"

            sorters.append(
                Sorter(
                    sortKey="pricePerMP",
                    id=acc["id"],
                    pricePerMP=pricePerMP,
                    price=price2,
                    powder=powder,
                    rarity=rarity2,
                    action=action,
                    slots=None,
                    recomb=True
                )
            )
            if isPiggyPreset and acc["id"] in piggies: continue
            # check upgrade
            id_ = acc["id"]
            for conflict in self.conflictsConfig:
                if id_ in conflict:
                    for i, upgradedacc in enumerate(conflict[conflict.index(id_)+1:]):
                        rarityNew = None

                        for acc2 in self.accessories:
                            if acc2["id"] == upgradedacc:
                                rarityNew = acc2["rarity"]
                                break
                        if rarityNew is None:
                            print("Not found!", upgradedacc)
                            continue
                        diff = self.getMagicPoderDiff(rarity, rarityNew)

                        upgradedPrice = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(upgradedacc)
                        upgradedPrice.sort()
                        upgradedPrice = upgradedPrice[-1].getPrice() if len(upgradedPrice) > 0 else None

                        if upgradedPrice is None: continue
                        if price is None: continue

                        priceDiff = upgradedPrice - price
                        if not diff:
                            print(id_, upgradedacc)
                            continue
                        pricePerMP = priceDiff / diff

                        sorters.append(
                            Sorter(
                                sortKey="pricePerMP",
                                id=acc["id"],
                                pricePerMP=pricePerMP,
                                price=priceDiff,
                                powder=diff,
                                rarity=rarityNew,
                                recomb=False,
                                slots=None,
                                action=f"upgrade -> {upgradedacc}",
                            )
                        )

        sorters.sort()

        costAll = 0
        powderAll = 0
        recombCount = 0
        slotCount = 0
        slotPrice = 0

        for acc in sorters[::-1]:
            costAll += acc["price"]
            powderAll += acc["powder"]
            recombCount += 1 if acc["recomb"] else 0
            if acc["slots"] is not None:
                slotCount += acc["slots"][0]
                slotPrice += acc["slots"][1]
            if budget is not None and costAll > budget: break

            self.treeView.addEntry(acc["id"], acc["action"], prizeToStr(acc["price"]), prizeToStr(acc["pricePerMP"]))

        if not powderAll:
            self.powderPlusLabel.setFg(Color.COLOR_WHITE)
        else:
            self.powderPlusLabel.setFg(tk.Color.GREEN)

        self.powderPlusLabel.setText(f"Powder Gain: +{powderAll}")
        self.recombLabel.setText(f"Recombs: +{recombCount} ({prizeToStr(recombPrice*recombCount)})")
        self.slotsLabel.setText(f"Slots: +{slotCount} ({prizeToStr(slotPrice)})")
        self.totalLabel.setText(f"Total: {prizeToStr(costAll)}")
        self.newTotalPowderLabel.setText(f"New Total Powder: {powderAll+powderAllOld}")
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateHelper  # hook to update tv on new API-Data available
        self.placeRelative()
        self.placeContentFrame()
        self.updateHelper()
class MedalTransferProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Medal Transfer Profit Page", buttonText="Medal Transfer Profit")
        self.master: Window = master

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("ID", "Medal-Price", "Profit", "ProfitPerMedal", "ItemLowestBinPrice")
        self.treeView.placeRelative(fixX=200)

        self.medalConfig = JsonConfig.loadConfig(os.path.join(CONFIG, "garden_medal_cost.json"))

        tk.Label(self.contentFrame, SG).setText("Jacobs Ticket Price:").setFont(16).placeRelative(fixWidth=200, fixHeight=25).setTextOrientation()
        self.ticketLabel = tk.Label(self.contentFrame, SG).setTextOrientation()
        self.ticketLabel.setFont(16)
        self.ticketLabel.setFg("green")
        self.ticketLabel.placeRelative(fixWidth=200, fixHeight=25, fixY=25)

        tk.Label(self.contentFrame, SG).setText("Average Price (7d):").setFont(16).placeRelative(fixWidth=200, fixHeight=25, fixY=50).setTextOrientation()
        self.ticketAvgLabel = tk.Label(self.contentFrame, SG).setTextOrientation()
        self.ticketAvgLabel.setFont(16)
        if "JACOBS_TICKET" in ConfigFile.AVERAGE_PRICE.keys():
            self.ticketAvgLabel.setText(prizeToStr(ConfigFile.AVERAGE_PRICE["JACOBS_TICKET"]))
        else:
            self.ticketAvgLabel.setText("None")
        self.ticketAvgLabel.placeRelative(fixWidth=200, fixHeight=25, fixY=75)

        self.openGraph = tk.Button(self.contentFrame, SG)
        self.openGraph.setCommand(self.openGraphGUI)
        self.openGraph.setText("Open Jacobs Ticket Graph")
        self.openGraph.placeRelative(fixWidth=200, fixHeight=25, fixY=125)

        self.updateAverage = tk.Button(self.contentFrame, SG)
        self.updateAverage.setCommand(self.requestAverage)
        self.updateAverage.setText("Update Jacobs Ticket Avg")
        self.updateAverage.placeRelative(fixWidth=200, fixHeight=25, fixY=100)

    def saveAverage(self):
        ConfigFile.AVERAGE_PRICE.saveConfig()

    def requestAverage(self):
        def request():
            try:
                self.currentHistoryData = getPlotData("JACOBS_TICKET", SkyConflnetAPI.getBazaarHistoryWeek)
                Constants.WAITING_FOR_API_REQUEST = False
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

            ConfigFile.AVERAGE_PRICE["JACOBS_TICKET"] = getMedianFromList(self.currentHistoryData['past_raw_buy_prices'])
            self.master.runTask(self.updatePrice).start()
            self.master.runTask(self.saveAverage).start()
            self.updateAverage.setText("Update Jacobs Ticket Avg")
            self.updateAverage.setEnabled()

        if not Constants.WAITING_FOR_API_REQUEST:
            self.updateAverage.setText("Updating ...")
            self.updateAverage.setDisabled()
            Constants.WAITING_FOR_API_REQUEST = True
            Thread(target=request).start()
        else:
            tk.SimpleDialog.askError(self.master, "Another API-Request is still running!")

    def updatePrice(self):
        if "JACOBS_TICKET" in ConfigFile.AVERAGE_PRICE.keys():
            self.ticketAvgLabel.setText(prizeToStr(ConfigFile.AVERAGE_PRICE["JACOBS_TICKET"]))
        else:
            self.ticketAvgLabel.setText("None")
        self.updateTreeView()

    def openGraphGUI(self):
        self.master.showItemInfo(self, "JACOBS_TICKET")
    def updateTreeView(self):
        self.treeView.clear()

        ticket = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("JACOBS_TICKET")
        if ticket is None:
            self.ticketLabel.setText("None")
            tk.SimpleDialog.askError(self.master, "Could not parse Ticket Prices!")
            return
        ticketPrice = ticket.getInstaSellPrice() + .1
        self.ticketLabel.setText(prizeToStr(ticketPrice))
        if "JACOBS_TICKET" in ConfigFile.AVERAGE_PRICE.keys():
            if ConfigFile.AVERAGE_PRICE["JACOBS_TICKET"] > ticketPrice:
                self.ticketLabel.setFg("green")
            else:
                self.ticketLabel.setFg("red")

        sorters = []
        for itemID, itemData in self.medalConfig.data.items():
            ticketAmount = itemData["tickets"]

            totalBronzeMedals = 0

            strPrice = ""
            if type(itemData["medal"]) is list:
                for data in itemData["medal"]:
                    medalType = data["type"]
                    medalAmount = data["amount"]
                    strPrice += f"{medalType}({medalAmount}), "
                    if medalType == "GOLD":
                        totalBronzeMedals += medalAmount * 8
                    if medalType == "SILVER":
                        totalBronzeMedals += medalAmount * 2
                    if medalType == "BRONZE":
                        totalBronzeMedals += medalAmount
                strPrice = strPrice[:-2]
            else:
                medalType = itemData["medal"]["type"]
                medalAmount = itemData["medal"]["amount"]
                if medalType == "GOLD":
                    totalBronzeMedals += medalAmount*8
                if medalType == "SILVER":
                    totalBronzeMedals += medalAmount*2
                if medalType == "BRONZE":
                    totalBronzeMedals += medalAmount
                strPrice = f"{medalType}({medalAmount})"

            ticketPriceFull = ticketPrice*ticketAmount

            itemPrice = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(itemID)
            itemPrice.sort()
            itemPrice = itemPrice[-1].getPrice() if len(itemPrice) > 0 else None


            if itemPrice is None: # try Bazaar
                item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemID)
                if item is not None:
                    itemPrice = item.getInstaBuyPrice()
            sorters.append(
                Sorter(
                    sortKey="profitPerMedal",
                    profitPerMedal=None if itemPrice is None else (itemPrice-ticketPriceFull)/(totalBronzeMedals/8),
                    itemSellPrice=itemPrice,
                    ticketAmount=ticketAmount,
                    strPrice=strPrice,
                    lbPrice=itemPrice,
                    id=itemID,
                    profit=None if itemPrice is None else (itemPrice-ticketPriceFull)
                )
            )
        sorters.sort()
        for sorter in sorters:
            self.treeView.addEntry(sorter["id"], sorter["strPrice"], prizeToStr(sorter["profit"]), prizeToStr(sorter["profitPerMedal"]), prizeToStr(sorter["lbPrice"]))
    def onShow(self, **kwargs):
        self.placeRelative()
        self.placeContentFrame()
        self.updatePrice() # and Treeview
        self.master.updateCurrentPageHook = self.updateTreeView

# Menu Pages
class MainMenuPage(CustomMenuPage):
    def __init__(self, master, tools:List[CustomMenuPage | CustomPage]):
        super().__init__(master, showBackButton=False, showTitle=False, homeScreen=True, showHomeButton=False)
        self.tools = tools
        self.toolsDict = {tool.__class__.__name__:tool for tool in tools}
        self.scrollFramePosY = 0
        self.activeButtons = []
        self.image = tk.PILImage.loadImage(os.path.join(IMAGES, "logo.png"))
        self.image.resize(.55)
        self.image.preRender()
        self.title = tk.Label(self, SG).setImage(self.image).placeRelative(centerX=True, fixHeight=self.image.getHeight(), fixWidth=self.image.getWidth(), fixY=50)

        self.playerHead1 = tk.PILImage.loadImage(os.path.join(IMAGES, "lol_hunter.png")).resizeTo(32, 32).preRender()
        self.playerHead2 = tk.PILImage.loadImage(os.path.join(IMAGES, "glaciodraco.png")).resizeTo(32, 32).preRender()

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

        self.autoUpdateActive = tk.Button(self, SG)
        self.autoUpdateActive.attachToolTip(
            "Bazaar Data Auto Request:\n\nUse this option to toggle automatic requests.\nRequest interval can be changed in Settings.\nThis is required to track item prices\nin real time.",
            group=SG
        )
        self.autoUpdateActive.setStyle(tk.Style.FLAT)
        self.autoUpdateActive.setFont(15)
        self.autoUpdateActive.setCommand(self.toggleAutoRequest)
        self.autoUpdateActive.setFg("green" if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] else "red")
        self.autoUpdateActive.setText("\u27F3")
        self.autoUpdateActive.placeRelative(fixHeight=25, fixWidth=25)

        self.scrollFrame = tk.Frame(self, SG)
        self.scrollFrame.bind(self.onPlaceRelative, tk.EventType.CUSTOM_RELATIVE_UPDATE)
        self.buttonFrame = tk.Frame(self.scrollFrame, SG)
        self.scrollFrame.placeRelative(fixY=250, fixWidth=300, centerX=True, fixHeight=300)

        self.scrollBarFrame = tk.Frame(self, SG).setBg(Color.COLOR_WHITE)
        self.scrollLabel = tk.Label(self.scrollBarFrame, SG)
    def getToolFromClassName(self, n:str):
        return self.toolsDict[n]
    def toggleAutoRequest(self):
        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = not Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"]
        Config.SETTINGS_CONFIG.save()
        self.updateAutoRequestButton()
    def updateAutoRequestButton(self):
        self.autoUpdateActive.setFg("green" if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] else "red")
    def onSearchClick(self):
        self.noSearchInput.placeForget()
    def clearSearch(self):
        self.search.clear()
        self.noSearchInput.placeRelative(fixY=200 + 12, fixWidth=295, fixHeight=25, centerX=True)
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
    def onPlaceRelative(self, e):
        if not hasattr(self, "scrollBarFrame"): return
        x, y, width, height = e.getValue()
        self.scrollBarFrame.place(x+width+3, y, 20, height)
    def onScroll(self, e:tk.Event):
        if not self.isActive(): return # if this page is not visible
        if self.buttonFrame.getHeight() < self.scrollFrame.getHeight(): return
        speed = 10
        delta = e.getScrollDelta()
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
            self.noSearchInput.placeRelative(fixY=200+12, fixWidth=295, fixHeight=25, centerX=True)
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
        self.image = tk.PILImage.loadImage(os.path.join(IMAGES, "logo.png"))
        self.image.resize(.89)
        self.image.preRender()
        self.title = tk.Label(self, SG).setImage(self.image).placeRelative(centerX=True, fixHeight=self.image.getHeight(), fixWidth=self.image.getWidth(), fixY=50)

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
                bazaarConfPath = os.path.join(APP_DATA, "skyblock_save", "bazaar.json")

                if not os.path.exists(path) and path != "":
                    tk.SimpleDialog.askWarning(self.master, "Could not read data from API-Config.\nConfig does not exist!\nSending request to Hypixel-API...")
                    path = None
                if path == "" or None: # load last config
                    path = None
                    if os.path.exists(bazaarConfPath):
                        path = bazaarConfPath
                t = time()
                API.SKYBLOCK_BAZAAR_API_PARSER = requestBazaarHypixelAPI(self.master, Config, path=path, saveTo=bazaarConfPath)
                MsgText.info(f"Loading HypixelBazaarConfig too {round(time()-t, 2)} Seconds!")
                if API.SKYBLOCK_BAZAAR_API_PARSER is not None: bazaarAPISuccessful = True

                updateBazaarInfoLabel(API.SKYBLOCK_BAZAAR_API_PARSER, path is not None)
                self.master.isConfigLoadedFromFile = path is not None


                self.processBar.setNormalMode()
                self.processBar.setValue(i+1)
            elif i == 1: # check/fetch Item API
                self.info.setText(msg)

                path = os.path.join(APP_DATA, "skyblock_save", "hypixel_item_config.json")

                if not SettingsGUI.checkItemConfigExist():
                    tk.SimpleDialog.askWarning(self.master, "Could not read data from Item-API-Config.\nConfig does not exist!\nCreating new...")
                    API.SKYBLOCK_ITEM_API_PARSER = requestItemHypixelAPI(self.master, Config, saveTo=path)
                else:
                    t = time()
                    API.SKYBLOCK_ITEM_API_PARSER = requestItemHypixelAPI(self.master, Config, path=path)
                    MsgText.info(f"Loading HypixelItemConfig took {round(time()-t, 2)} Seconds!")
                if API.SKYBLOCK_ITEM_API_PARSER is not None: itemAPISuccessful = True
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
                auctConfPath = os.path.join(APP_DATA, "skyblock_save", "auctionhouse")

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
                                                                           saveTo=os.path.join(APP_DATA, "skyblock_save", "auctionhouse"))
                pages = len(os.listdir(os.path.join(APP_DATA, "skyblock_save", "auctionhouse")))
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
        checkWindows() # ensures saved files
        checkConfigForUpdates()
        if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_off_on_load"]:
            Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = False
            Config.SETTINGS_CONFIG.save()
        MsgText.info("Creating GUI...")
        super().__init__(group=SG)
        MsgText.info("Loading Style...")
        if not os.path.exists(os.path.join(APP_DATA)):
            os.mkdir(APP_DATA)
            MsgText.warning("Folder does not exist! Creating folder: " + os.path.join(APP_DATA))
        if not os.path.exists(os.path.join(APP_DATA, "skyblock_save")):
            os.mkdir(os.path.join(APP_DATA, "skyblock_save"))
            MsgText.warning("Folder does not exist! Creating folder: "+os.path.join(APP_DATA, "skyblock_save"))
        if not os.path.exists(os.path.join(APP_DATA, "skyblock_save", "auctionhouse")):
            os.mkdir(os.path.join(APP_DATA, "skyblock_save", "auctionhouse"))
            MsgText.warning("Folder does not exist! Creating folder: " + os.path.join(APP_DATA, "skyblock_save", "auctionhouse"))
        # load average_price_save.json
        ConfigFile.AVERAGE_PRICE = JsonConfig.loadConfig(os.path.join(APP_DATA, "skyblock_save", "average_price_save.json"), create=True)
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

        ## REGISTER FEATURES ##
        self.mainMenuPage = MainMenuPage(self, [
                LongTimeFlipHelperPage(self),
                ItemPriceTrackerPage(self),
                MayorInfoPage(self),
                BazaarFlipProfitPage(self),
                BazaarCraftProfitPage(self),
                AuctionHousePage(self),
                AccessoryBuyHelperPage(self),
                MedalTransferProfitPage(self),
                MagicFindCalculatorPage(self),
                PestProfitPage(self),
                AlchemyXPCalculatorPage(self),
                ItemInfoPage(self),
                BazaarToAuctionHouseFlipProfitPage(self),
                ComposterProfitPage(self),
                EnchantingBookBazaarCheapestPage(self),
                EnchantingBookBazaarProfitPage(self),
        ])

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
        self.configureWindows()
    def _autoRequestAPI(self):
        started = False
        timer = time()
        while True:
            sleep(.1)
            if self.loadingPage.loadingComplete and not started:
                started = True
                sleep(5)
            if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"]:
                if Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"] < 20:
                    tk.SimpleDialog.askError("Request interval cannot be smaller than 20s!")
                    return
                if time()-timer >= Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request_interval"]:
                    self.refreshAPIRequest("bazaar")
                    timer = time()
                    if API.SKYBLOCK_BAZAAR_API_PARSER is None: # if request fails -> auto request disabled
                        Config.SETTINGS_CONFIG["auto_api_requests"]["bazaar_auto_request"] = False
                        self.mainMenuPage.updateAutoRequestButton()
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

        self.bind(self.mainMenuPage.onScroll, tk.EventType.WHEEL_MOTION)
    def configureWindows(self):
        self.updateIdleTasks()
        self.withdraw()
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        hwnd = windll.user32.GetParent(self._get().winfo_id())
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        self.withdraw()
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
        conf = JsonConfig.loadConfig(os.path.join(APP_DATA, "skyblock_save", "bazaar.json"), create=True)
        conf.setData(data)
        conf.save()
        API.SKYBLOCK_BAZAAR_API_PARSER = HypixelBazaarParser(data.getData())
        self.isConfigLoadedFromFile = True
        updateBazaarInfoLabel(API.SKYBLOCK_BAZAAR_API_PARSER, self.isConfigLoadedFromFile)
    def refreshAPIRequest(self, e):
        if Constants.WAITING_FOR_API_REQUEST:
            tk.SimpleDialog.askError(self, "Another api request is still running!\nTry again later.")
            return
        if not self.loadingPage.loadingComplete:
            tk.SimpleDialog.askError(self, "Software is not fully initialized yet!\nTry again later.")
            return
        self.lockInfoLabel = True
        Constants.WAITING_FOR_API_REQUEST = True
        self.isConfigLoadedFromFile = False

        sleep(.3)
        if e == "all" or e == "bazaar":
            BILG.setFg("white")
            BILG.setText("Requesting Hypixel-API...")
            API.SKYBLOCK_BAZAAR_API_PARSER = requestBazaarHypixelAPI(self,
                                                                     Config,
                                                                     saveTo=os.path.join(APP_DATA, "skyblock_save", "bazaar.json"))
            updateBazaarInfoLabel(API.SKYBLOCK_BAZAAR_API_PARSER, self.isConfigLoadedFromFile)
        if e == "all" or e == "auction":
            AILG.setFg("white")
            AILG.setText("Requesting Hypixel-API...")
            API.SKYBLOCK_AUCTION_API_PARSER = requestAuctionHypixelAPI(self,
                                                                       Config,
                                                                       infoLabel=AILG,
                                                                       saveTo=os.path.join(APP_DATA, "skyblock_save", "auctionhouse"))
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
