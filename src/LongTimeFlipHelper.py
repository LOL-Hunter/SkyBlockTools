from threading import Thread
import os
from typing import Tuple, List

from core.jsonConfig import JsonConfig

import tksimple as tk
from core.analyzer import getPlotData
from core.constants import API, BazaarItemID
from core.constants import STYLE_GROUP as SG, Color, ConfigFile, Constants, System
from core.hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException
from core.hyPI.skyCoflnetAPI import SkyConflnetAPI
from core.logger import MsgText
from core.skyMath import applyBazaarTax
from core.skyMath import getMedianFromList
from core.skyMisc import parsePrizeToStr
from core.skyMisc import (
    throwAPITimeoutException,
    throwNoAPIKeyException,
    throwAPIConnectionException
)
from core.widgets import CustomPage


class LongTimeFlip(tk.Frame):
    def __init__(self, page, window, master, data):
        super().__init__(master, SG)
        self.isOrder = False
        self.data = data
        self.master:tk.Frame = master
        self.window = window
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
        NewFlipWindow(self, self.page, self.window, self.selectedItem, finish=self.page.finishEdit, data=self.data).show()
    def updateWidget(self, isOrder=None):
        if API.SKYBLOCK_BAZAAR_API_PARSER is None: return
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
                self.expectedSellPrice.setText(f"Expected Price: +{parsePrizeToStr(averagePriceToBuyDiff)}")
            else:
                self.expectedSellPrice.setFg("green")
                self.expectedSellPrice.setText(f"Expected Price: {parsePrizeToStr(averagePriceToBuyDiff)}")
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
            self.spendL.setText(f"Coins Spend: {parsePrizeToStr(self.getPriceSpend())} (Price Per: ~{parsePrizeToStr(buyPricePer)})")
            self.sellNowL.setText(f"Sell now{star}: {parsePrizeToStr(sellPrice)} (Price Per: ~{parsePrizeToStr(sellPricePer)})")
            self.profitL.setText(f"Profit: {parsePrizeToStr(profit)}")
            self.profitL2.setText(f"Invest: {parsePrizeToStr(buyPrice)}")
        else:
            self.profitL2.setFg("green")
            self._setBg(tk.Color.rgb(22, 51, 45))
            profit = sellPrice - buyPrice
            self.spendL.setText(f"Worth at Start: {parsePrizeToStr(buyPrice)} (Price Per: ~{parsePrizeToStr(buyPricePer)})")
            self.sellNowL.setText(f"Sell now{star}: {parsePrizeToStr(sellPrice)} (Price Per: ~{parsePrizeToStr(sellPricePer)})")
            self.profitL.setText(f"Profit: {parsePrizeToStr(profit)}")
            self.profitL2.setText(f"Sell: {parsePrizeToStr(sellPrice)}")
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
        self.treeView.setSingleSelect()
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

        self.treeView.setEntry(parsePrizeToStr(amount, True), parsePrizeToStr(price), parsePrizeToStr(amount * price), index=selectedIndex)
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
        selectedIndex = self.treeView.getSelectedIndex()
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
        self.treeView.addEntry("0", "0", "0")
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
        self.data["items_bought"] = not self.isFlipC.getState()
        self.data["finish"] = not self.isFinishedC.getState()
        if self._finishHook is not None: self._finishHook()
    def readData(self, data):
        self.selectedItem = data["item_id"]
        self.isFinishedC.setState(self.data["finished"])
        self.isFlipC.setState(not self.data["items_bought"])
        self.treeView.clear()
        for dat in self.data["data"]:
            amount = dat["amount"]
            price = dat["price"]
            self.treeView.addEntry(parsePrizeToStr(amount, True), parsePrizeToStr(price), parsePrizeToStr(amount * price))
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

        self.master = master
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
        path = os.path.join(System.CONFIG_PATH, "active_flip_config.json")
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
    @tk.runWatcherDec
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
        showFin = self.showFinished.getState()
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
        self.updateView()
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
            flip.updateWidget(self.useSellOffers.getState())

        for flip in placedFlips:
            value, _exact = flip.getProfit(self.useSellOffers.getState())
            if not _exact: exact = False
            fullProfit += value

            value, _exact = flip.getSellPrice(self.useSellOffers.getState())
            if not _exact: exact = False
            totalValue += value

        self.master.updateDynamicWidgets()
        star = "*" if not exact else ""
        self.fullProfitL.setText(f"Profit{star}: {parsePrizeToStr(fullProfit)}")
        self.totalValueL.setText(f"Total-Value{star}: {parsePrizeToStr(totalValue)}")
        if fullProfit > 0:
            self.fullProfitL.setFg("green")
        else:
            self.fullProfitL.setFg("red")
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateView  # hook to update tv on new API-Data available
        if "itemName" in kwargs: # search complete
            self._history.pop(-2) # delete search Page and self
            self._history.pop(-2) # workaround
            selected = kwargs["itemName"]
            NewFlipWindow(None, self, self.master, selected, finish=self.finishEdit).show()
        self.placeRelative()
        self.placeContentFrame()
        self.master.updateDynamicWidgets()
        self.updateView()