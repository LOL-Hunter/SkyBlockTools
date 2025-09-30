import tksimple as tk
from time import sleep
from threading import Thread

from core.bazaarAnalyzer import BazaarAnalyzer
from core.constants import STYLE_GROUP as SG, API, BazaarItemID, ConfigFile, Constants, Color
from core.skyMath import applyBazaarTax, getMedianFromList
from core.skyMisc import (
    parsePrizeToStr,
    search,
    Sorter,
    throwAPIConnectionException,
    throwNoAPIKeyException,
    throwAPITimeoutException
)
from core.analyzer import getPlotData
from core.widgets import CustomPage
from core.hyPI.skyCoflnetAPI import SkyConflnetAPI
from core.hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException


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
        if self.showOthersTry.getState():
            titles.extend(["Others-Try-To-Buy", "Others-Try-To-Sell"])
        if self.perMode == "per_hour":
            titles.extend(["Buy-Per-Hour", "Sell-Per-Hour"])
        if self.perMode == "per_week":
            titles.extend(["Buy-Per-Week", "Sell-Per-Week"])
        if self.showFlipRatingHour.getState():
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

            if itemID.startswith("ENCHANTMENT") and not self.includeEnchantments.getState(): continue

            item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemID)
            if item is None:
                print("ERROR", itemID)
                continue
            if self.hideLowInstaSell.getState() and item.getInstaSellWeek() / 168 < 1: continue
            ## Sell price ##
            if self.useSellOffers.getState(): # use sell Offer
                itemSellPrice = item.getInstaBuyPrice()
            else: # insta sell
                itemSellPrice = item.getInstaSellPrice()
            itemSellPrice = applyBazaarTax(itemSellPrice) * factor
            if not itemSellPrice: continue # sell is zero
            ## Buy price ##
            if self.useBuyOffers.getState():
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
                parsePrizeToStr(rec["buy"]),
                parsePrizeToStr(rec["sell"]),
                parsePrizeToStr(rec["profitPerFlip"]),
            ]
            if self.showOthersTry.getState():
                input_.extend([f"{rec['buyVolume']} in {rec['buyOrders']} Orders", f"{rec['sellVolume']} in {rec['sellOrders']} Orders"])
            if self.perMode == "per_hour":
                input_.extend([f"{round(rec['buysPerHour'], 2)}", f"{round(rec['sellsPerHour'], 2)}"])
            if self.perMode == "per_week":
                input_.extend([f"{rec['buysPerWeek']}", f"{rec['sellsPerWeek']}"])
            if self.showFlipRatingHour.getState():
                input_.append(f"{parsePrizeToStr(rec['flipRating'], hideCoins=True)}")


            colorTag = "none"
            if rec["averageBuyPrice"] != "":
                price = parsePrizeToStr(rec["averageBuyPrice"])
                diff = parsePrizeToStr(rec["averagePriceToBuyDiff"])
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