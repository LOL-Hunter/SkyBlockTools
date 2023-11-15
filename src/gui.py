# -*- coding: iso-8859-15 -*-
import os
from datetime import datetime, timedelta
from hyPI._parsers import MayorData, BazaarHistory
from hyPI.constants import BazaarItemID, AuctionItemID
from hyPI.skyCoflnetAPI import SkyConflnetAPI
from pysettings import tk, iterDict
from pysettings.jsonConfig import JsonConfig
from threading import Thread
from time import sleep, time
from typing import List

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from pytz import timezone

from analyzer import getPlotData
from constants import STYLE_GROUP as SG, LOAD_STYLE
from skyMath import getPlotTicksFromInterval, parseTimeDelta
from skyMisc import modeToBazaarAPIFunc, prizeToStr
from widgets import CompleterEntry, CustomPage, CustomMenuPage

IMAGES = os.path.join(os.path.split(__file__)[0], "images")
CONFIG = os.path.join(os.path.split(__file__)[0], "config")

class APIRequest:
    """
    This class handles the threaded API requests.
    Showing "Waiting for API response..." while waiting for response.

    Perform API Request in API-hook-method -> set 'setRequestAPIHook'
    start the API request by using 'startAPIRequest'

    """
    def __init__(self, page, tkMaster:tk.Tk | tk.Toplevel):
        self._tkMaster = tkMaster
        self._page = page
        self._dots = 0
        self._dataAvailable = False
        self._hook = None
        self._waitingLabel = tk.Label(self._page, SG).setText("Waiting for API response").setFont(16).placeRelative(fixY=100, centerX=True, changeHeight=-40, changeWidth=-40, fixX=40)
    def startAPIRequest(self):
        """
        starts the API request and run threaded API-hook-method.

        @return:
        """
        assert self._hook is not None, "REQUEST HOOK IS NONE!"
        self._dataAvailable = False
        self._page.hideContentFrame()
        self._waitingLabel.placeRelative(fixY=100, centerX=True, changeHeight=-40)
        self._waitingLabel.update()
        Thread(target=self._updateWaitingForAPI).start()
        Thread(target=self._requestAPI).start()
    def setRequestAPIHook(self, hook):
        """
        set Function.
        Perform API-request in bound method.

        @param hook:
        @return:
        """
        self._hook = hook
    def _updateWaitingForAPI(self):
        timer = time()
        self._dots = 0
        while True:
            if self._dataAvailable: break
            sleep(.2)
            if time()-timer >= 1:
                if self._dots >= 3:
                    self._dots = 0
                else:
                    self._dots += 1
                self._waitingLabel.setText("Waiting for API response"+"."*self._dots)
            self._tkMaster.update()
    def _requestAPI(self):
        self._hook() # request API
        self._dataAvailable = True
        self._finishAPIRequest()
    def _finishAPIRequest(self):
        self._waitingLabel.placeForget()
        self._page.placeContentFrame()
        self._tkMaster.updateDynamicWidgets()
        self._tkMaster.update()

# Info/Content Pages
class MayorInfoPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Mayor Info Page", buttonText="Mayor Info")
        self.master: Window = master
        self.currentMayorEnd = None
        Thread(target=self.updateTimer).start()

        self.images = self.loadMayorImages()
        self.mayorData = JsonConfig.loadConfig(os.path.join(CONFIG, "mayor.json"))

        self.currentMayor:MayorData = None

        self.notebook = tk.Notebook(self.contentFrame, SG)
        self.tabMayorCur = self.notebook.createNewTab("Current Mayor", SG)
        self.tabMayorHist = self.notebook.createNewTab("Mayor History", SG)
        self.tabMayorRef = self.notebook.createNewTab("Mayor Reference", SG)
        self.notebook.placeRelative()

        self.createCurrentTab(self.tabMayorCur)
        self.createHistoryTab(self.tabMayorHist)
        self.createReferenceTab(self.tabMayorRef)

        self.api = APIRequest(self, self.getTkMaster())
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
        for name, data in iterDict(self.mayorData.getData()):
            if data["special"]:
                specIndex += 1
                index = specIndex
                _master = self.specMayLf
            else:
                regIndex += 1
                index = regIndex
                _master = self.regMayLf

            b = tk.Button(_master, SG)
            b.setText(name.capitalize() +f"\n({self.mayorData[name]['key']})")
            b.setCommand(self.showMayorInfo, args=[name])
            b.placeRelative(fixWidth=widthButton-5, fixHeight=heightButton, centerX=True, fixY=(index-1)*heightButton)

        self.regMayLf.placeRelative(centerX=True, fixHeight=regIndex * heightButton + 20, fixWidth=widthButton)
        self.specMayLf.placeRelative(centerX=True, fixY=regIndex * heightButton + 20, fixHeight=specIndex * heightButton + 20, fixWidth=widthButton)


        self.menuFrame.placeRelative()
    def showMayorInfo(self, e):
        name = e.getArgs(0)
        self.menuFrame.placeForget()
        self.topFrame.placeRelative(fixWidth=600, centerX=True)
        self.getTkMaster().updateDynamicWidgets()

        dataContent = {
            "Mayor Name:": name,
            "Profession:": self.mayorData[name]["key"],
            "Peaks:": f"[max {len(self.mayorData[name]['perks'])}]"
        }
        self.dataText_ref.setText(f"\n".join([f"{k} {v}" for k, v in iterDict(dataContent)]))

        out = ""
        for perk in self.mayorData[name]["perks"]:
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
        self.getTkMaster().updateDynamicWidgets()
    def createHistoryTab(self, tab):
        pass
    def parseTime(self, d):
        out = ""
        for t, i in zip([d.day, d.hour, d.minute, d.second], ["d", "h", "m", "s"]):
            if t > 0:
                out += f"{t}{i} "
        return out
    def configureContentFrame(self):
        name = self.currentMayor.getName().lower()
        key = self.currentMayor.getKey()
        currYear = self.currentMayor.getYear()
        perks = self.currentMayor.getPerks()
        perkCount = self.currentMayor.getPerkAmount()
        self.currentMayorEnd = self.currentMayor.getEndTimestamp()

        delta:timedelta = self.currentMayorEnd - self.getNow()
        self.timeLabel.setText(self.parseTime(parseTimeDelta(delta)))

        dataContent = {
            "Mayor Name:": name,
            "Profession:": key,
            "Year:": currYear,
            "Peaks:": f"[{perkCount}/{len(self.mayorData[name]['perks'])}]"
        }
        self.dataText.setText(f"\n".join([f"{k} {v}" for k, v in iterDict(dataContent)]))

        out = ""
        activePerkNames = []
        for perk in perks:
            name_ = perk.getPerkName()
            activePerkNames.append(name_)
            desc = perk.getDescription()
            out += f"§g== {name_} ==\n"
            out += f"§c{desc}\n"
        for perk in self.mayorData[name]["perks"]:
            name_ = perk["name"]
            desc = perk["description"]
            if name_ not in activePerkNames:
                out += f"§r== {name_} ==\n"
                out += f"§c{desc}\n"

        self.dataTextPerks.clear()
        self.dataTextPerks.addStrf(out)

        if name in self.images.keys():
            self.imageDisplay.setImage(self.images[name])
        else:
            self.imageDisplay.clearImage()
            self.imageDisplay.setText("No Image Available")
    def getNow(self):
        return timezone("Europe/Berlin").localize(datetime.now())
    def updateTimer(self):
        while True:
            sleep(1)
            if self.currentMayorEnd is None: continue
            delta: timedelta = self.currentMayorEnd - self.getNow()
            self.timeLabel.setText(self.parseTime(parseTimeDelta(delta)))
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
        self.mayorHist = SkyConflnetAPI.getMayorData()
        self.currentMayor = self.mayorHist.getCurrentMayor()
        self.configureContentFrame()
    def onShow(self, **kwargs):
        self.placeRelative()
        self.api.startAPIRequest()
class ItemInfoPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Info of Item: []", buttonText="Bazaar Item Info")
        self.master: Window = master
        self.selectedMode = "hour"
        self.selectedItem = None
        self.plot2 = None
        self.currentHistoryData = None

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

        #tk.Label(self.toolLf, SG).setText("Latest Item:").placeRelative(changeWidth=-5, fixHeight=10)

        self.dataText = tk.Text(self.toolLf, SG, readOnly=True).placeRelative(fixHeight=345, changeWidth=-5, fixY=0)

        self.optionLf = tk.LabelFrame(self.toolLf, SG)
        self.chSell = tk.Checkbutton(self.optionLf, SG).setText("Sell-Price").setSelected().placeRelative(changeWidth=-5, fixHeight=23, fixY=0).setTextOrientation().onSelectEvent(self.updatePlot)
        self.chBuy = tk.Checkbutton(self.optionLf, SG).setText("Buy-Price").setSelected().placeRelative(changeWidth=-5, fixHeight=23, fixY=23*1).setTextOrientation().onSelectEvent(self.updatePlot)
        self.chSellV = tk.Checkbutton(self.optionLf, SG).setText("Sell-Volume").placeRelative(changeWidth=-5, fixHeight=23, fixY=23*2).setTextOrientation().onSelectEvent(self.updatePlot)
        self.chBuyV = tk.Checkbutton(self.optionLf, SG).setText("Buy-Volume").placeRelative(changeWidth=-5, fixHeight=23, fixY=23*3).setTextOrientation().onSelectEvent(self.updatePlot)

        self.optionLf.placeRelative(fixY=345, fixHeight=105, changeWidth=-5)

        self.toolLf.placeRelative(fixY=50, stickRight=True, fixWidth=200, fixX=40)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.plot:Axes = self.figure.add_subplot(111)

        self.plotWidget = tk.MatPlotLibFigure(self.contentFrame, self.figure, toolBar=True)

        self.plotWidget.placeRelative(fixY=50, centerX=True, changeWidth=-200)

        self.api = APIRequest(self, self.getTkMaster())
        self.api.setRequestAPIHook(self.requestAPIHook)
    def updatePlot(self):
        ts = self.currentHistoryData["time_stamps"]
        bp = self.currentHistoryData["past_buy_prices"]
        sp = self.currentHistoryData["past_sell_prices"]
        bv = self.currentHistoryData["past_buy_volume"]
        sv = self.currentHistoryData["past_sell_volume"]
        pricePref = self.currentHistoryData["price_prefix"]
        volPref = self.currentHistoryData["volume_prefix"]

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
    def requestAPIHook(self):
        self.currentHistoryData = getPlotData(self.selectedItem, modeToBazaarAPIFunc(self.selectedMode))
        histObj:BazaarHistory = self.currentHistoryData["history_object"]

        self.updatePlot()

        if self.selectedMode == "hour":
            latest = histObj.getTimeSlots()[0]
            out =  f"§c== Info ==\n"
            out += f"§yMeasured-At:\n  §y{self.currentHistoryData['time_stamps'][-1].split('-')[-1].replace('(', '').replace(')', '')}\n\n"
            out += f"§c== Price Info ==\n"
            out += f"§rInsta-Buy-Price:\n§r  {prizeToStr(latest.getBuyPrice())}\n"
            out += f"§gInsta-Sell-Price:\n§g  {prizeToStr(latest.getSellPrice())}\n\n"
            out += f"§c== Price Info x64 ==\n"
            out += f"§rInsta-Buy-Price:\n§r  {prizeToStr(latest.getBuyPrice()*64)}\n"
            out += f"§gInsta-Sell-Price:\n§g  {prizeToStr(latest.getSellPrice()*64)}\n\n"
            out += f"§c== Volume-Info ==\n"
            out += f"§rInsta-Sell-Volume:\n§r  {prizeToStr(latest.getSellVolume())}\n"
            out += f"§gInsta-Buy-Volume:\n§g  {prizeToStr(latest.getBuyVolume())}\n"
            self.dataText.setStrf(out)
    def changePlotType(self, e:tk.Event):
        for i in self.timeRangeBtns:
            i.setStyle(tk.Style.RAISED)
        e.getWidget().setStyle(tk.Style.SUNKEN)
        self.selectedMode = e.getArgs(0)
        self.api.startAPIRequest()
    def onShow(self, **kwargs):
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
        def getType(_type)->str:
            if "BazaarItemID" in str(_type):
                return "Bazaar Item"
            elif "AuctionItemID" in str(_type):
                return "Auction Item"
            else: return _type
        value = self.entry.getValue()
        suggestions = []
        _searchInput = self.searchInput
        if isinstance(self.searchInput, dict):
            _searchInput = self.searchInput.values()

        if len(value) >= 3:
            for i, searchList in enumerate(_searchInput):
                if isinstance(self.searchInput, dict):
                    type_ = getType(list(self.searchInput.keys())[i])
                elif isinstance(self.searchInput, list) and len(self.searchInput) == 1:
                    type_ = getType(_searchInput[0])
                else:
                    raise Exception(f"Invalid search input! {self.searchInput}")
                for item in searchList:
                    itemName = item.value if hasattr(item, "value") else item
                    itemName = itemName.replace("_", " ")
                    show=True
                    for valPice in value.split(" "):
                        if valPice not in itemName.lower():
                            show = False
                    if show:
                        if type_ is None: suggestions.append(f"{itemName.lower()}")
                        else: suggestions.append(f"{itemName.lower()} - {type_}")

        return suggestions
    def onSelectEvent(self, e):
        value = e.getValue()
        if value is not None and value != "None":
            value = value.split(" - ")[0]
            value = value.replace(" ", "_")
            self.openNextMenuPage(self.nextPage, itemName=value.upper())
    def onShow(self, **kwargs):
        if kwargs["next_page"] != self.nextPage:
            self.entry.clear()
        self.nextPage = kwargs["next_page"] if "next_page" in kwargs.keys() else self.nextPage
        self.searchInput = kwargs["input"] if "input" in kwargs.keys() else self.searchInput
        self.msg = kwargs["msg"] if "msg" in kwargs.keys() else self.msg
        self.forceType = kwargs["forceType"] if "forceType" in kwargs.keys() else self.forceType
        self.setPageTitle(self.msg)
        self.placeRelative()
        self.entry.setFocus()
class EnchantingBookBazaarProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Book Combine Profit Page", buttonText="Book Combine Profit")

        self.api = APIRequest(self, self.getTkMaster())
        self.api.setRequestAPIHook(self.requestAPIHook)
    def requestAPIHook(self):

        return
    def onShow(self, **kwargs):
        self.placeRelative()
        self.api.startAPIRequest()
class EnchantingBookBazaarCheapestPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Cheapest Book Craft Page", buttonText="Cheapest Book Craft")

        self.enchantments = [i for i in BazaarItemID if i.value.startswith("enchantment".upper())]

        self.api = APIRequest(self, self.getTkMaster())
        self.api.setRequestAPIHook(self.requestAPIHook)
    def requestAPIHook(self):
        return
    def onShow(self, **kwargs):
        self.placeRelative()
        self.api.startAPIRequest()
    def customShow(self, page):
        page.openNextMenuPage(self.master.searchPage,
                         input={"Enchantment":self.enchantments},
                         msg="Search EnchantedBook in Bazaar: (At least tree characters)",
                         next_page=self)

# Menu Pages
class MainMenuPage(CustomMenuPage):
    def __init__(self, master, tools:List[CustomMenuPage | CustomPage]):
        super().__init__(master, showBackButton=False, showTitle=False, homeScreen=True, showHomeButton=False)
        self.image = tk.PILImage.loadImage(os.path.join(IMAGES, "logo.png"))
        self.image.preRender()
        self.title = tk.Label(self, SG).setImage(self.image).placeRelative(centerX=True, fixHeight=self.image.getHeight(), fixWidth=self.image.getWidth(), fixY=25)

        self.playerHead1 = tk.PILImage.loadImage(os.path.join(IMAGES, "lol_hunter.png"))
        self.playerHead2 = tk.PILImage.loadImage(os.path.join(IMAGES, "glaciodraco.png"))

        self.playerHead1.resizeTo(32, 32)
        self.playerHead2.resizeTo(32, 32)

        self.playerHead1.preRender()
        self.playerHead2.preRender()

        tk.Label(self, SG).setText("Made by").placeRelative(stickRight=True, stickDown=True, fixHeight=25, fixWidth=100, changeY=-40, changeX=-25)
        
        self.pl1L = tk.Label(self, SG).setImage(self.playerHead1)
        self.pl2L = tk.Label(self, SG).setImage(self.playerHead2)
        self.pl1L.attachToolTip("LOL_Hunter", waitBeforeShow=0, group=SG)
        self.pl2L.attachToolTip("glaciodraco", waitBeforeShow=0, group=SG)
        self.pl1L.placeRelative(stickRight=True, stickDown=True, fixHeight=self.playerHead1.getHeight(), fixWidth=self.playerHead1.getHeight(), changeY=-10, changeX=-10)
        self.pl2L.placeRelative(stickRight=True, stickDown=True, changeY=-self.playerHead1.getWidth()-10*2, fixHeight=self.playerHead1.getHeight(), fixWidth=self.playerHead1.getHeight(), changeX=-10)
        

        for i, tool in enumerate(tools):
            tk.Button(self, SG).setFont(16).setText(tool.getButtonText()).setCommand(self._run, args=[tool]).placeRelative(centerX=True, fixY=50 * i + 300, fixWidth=300, fixHeight=50)
class EnchantingMenuPage(CustomMenuPage):
    def __init__(self, master, tools: List[CustomMenuPage | CustomPage]):
        super().__init__(master, pageTitle="Enchanting Menu", buttonText="Enchanting Menu", showTitle=True)

        for i, tool in enumerate(tools):
            tk.Button(self, SG).setFont(16).setText(tool.getButtonText()).setCommand(self._run, args=[tool]).placeRelative(centerX=True, fixY=50 * i + 50, fixWidth=300, fixHeight=50)
class InfoMenuPage(CustomMenuPage):
    def __init__(self, master, tools: List[CustomMenuPage | CustomPage]):
        super().__init__(master, pageTitle="Information Menu", buttonText="Information Menu", showTitle=True)

        for i, tool in enumerate(tools):
            tk.Button(self, SG).setFont(16).setText(tool.getButtonText()).setCommand(self._run, args=[tool]).placeRelative(centerX=True, fixY=50 * i + 50, fixWidth=300, fixHeight=50)

class Window(tk.Toplevel):
    def __init__(self):
        super().__init__("Tk", SG, False)
        LOAD_STYLE() # load DarkMode!

        ## instantiate Pages ##
        self.searchPage = SearchPage(self)

        self.mainMenuPage = MainMenuPage(self, [
            InfoMenuPage(self, [
                ItemInfoPage(self),
                MayorInfoPage(self),
            ]),
            EnchantingMenuPage(self, [
                EnchantingBookBazaarCheapestPage(self),
                EnchantingBookBazaarProfitPage(self),
            ])
        ])

        self.configureWindow()
        self.createGUI()
        self.mainMenuPage.openMenuPage()
    def configureWindow(self):
        self.setMinSize(600, 600)
        self.setTitle("SkyblockTools")
    def createGUI(self):
        self.taskBar = tk.TaskBar(self, SG)
        self.taskBar_file = self.taskBar.createSubMenu("File")
        tk.Button(self.taskBar_file, SG).setText("Save...")

        self.taskBar_tools = self.taskBar.createSubMenu("Tools")
        tk.Button(self.taskBar_tools, SG).setText("Bazaar Item Info")


        self.taskBar.create()
