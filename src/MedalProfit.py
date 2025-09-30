import os
from threading import Thread

import tksimple as tk
from core.analyzer import getPlotData
from core.constants import STYLE_GROUP as SG, ConfigFile, Constants, Path, API
from core.hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException
from core.hyPI.skyCoflnetAPI import SkyConflnetAPI
from core.skyMath import getMedianFromList
from core.jsonConfig import JsonConfig
from core.skyMisc import (
    parsePrizeToStr,
    throwAPITimeoutException,
    throwNoAPIKeyException,
    throwAPIConnectionException,
    Sorter
)
from core.widgets import CustomPage


class MedalTransferProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Medal Transfer Profit Page", buttonText="Medal Transfer Profit")
        self.master = master

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("ID", "Medal-Price", "Profit", "ProfitPerMedal", "ItemLowestBinPrice")
        self.treeView.placeRelative(fixX=200)

        self.medalConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "garden_medal_cost.json"))

        tk.Label(self.contentFrame, SG).setText("Jacobs Ticket Price:").setFont(16).placeRelative(fixWidth=200, fixHeight=25).setTextOrientation()
        self.ticketLabel = tk.Label(self.contentFrame, SG).setTextOrientation()
        self.ticketLabel.setFont(16)
        self.ticketLabel.setFg("green")
        self.ticketLabel.placeRelative(fixWidth=200, fixHeight=25, fixY=25)

        tk.Label(self.contentFrame, SG).setText("Average Price (7d):").setFont(16).placeRelative(fixWidth=200, fixHeight=25, fixY=50).setTextOrientation()
        self.ticketAvgLabel = tk.Label(self.contentFrame, SG).setTextOrientation()
        self.ticketAvgLabel.setFont(16)
        if "JACOBS_TICKET" in ConfigFile.AVERAGE_PRICE.keys():
            self.ticketAvgLabel.setText(parsePrizeToStr(ConfigFile.AVERAGE_PRICE["JACOBS_TICKET"]))
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
            self.ticketAvgLabel.setText(parsePrizeToStr(ConfigFile.AVERAGE_PRICE["JACOBS_TICKET"]))
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
        self.ticketLabel.setText(parsePrizeToStr(ticketPrice))
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
            self.treeView.addEntry(sorter["id"], sorter["strPrice"], parsePrizeToStr(sorter["profit"]), parsePrizeToStr(sorter["profitPerMedal"]), parsePrizeToStr(sorter["lbPrice"]))
    def onShow(self, **kwargs):
        self.placeRelative()
        self.placeContentFrame()
        self.updatePrice() # and Treeview
        self.master.updateCurrentPageHook = self.updateTreeView