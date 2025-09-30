import os
import tksimple as tk

from core.jsonConfig import JsonConfig
from core.constants import STYLE_GROUP as SG, API, Path
from core.skyMisc import parsePrizeToStr
from core.skyMisc import (
    parseTimeFromSec,
    Sorter
)
from core.widgets import CustomPage


class ForgeProfitTrackerPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Forge Profit Tracker Page", buttonText="Forge Profit Tracker")

        self.forgeConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "forge_data.json"))

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("ItemID", "Ingredients", "Cost", "Profit", "ForgeTime")

        self.treeView.placeRelative(fixX=200)

        self.tooFrame = tk.LabelFrame(self.contentFrame, SG)
        self.tooFrame.setText("Tools")

        self.tooFrame.placeRelative(fixWidth=200)
    def updateTreeview(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None: return

        sorters = []

        for recipe in self.forgeConfig:
            itemIDOutput = recipe["output"]

            item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemIDOutput)
            if item is None:
                print("ERROR", itemIDOutput)
                continue
            itemSellPrice = item.getInstaBuyPrice()

            itemBuyPriceTotal = 0
            inputIDs = []

            for ingrediant in recipe["input"]:
                itemIDInput = ingrediant["type"]
                itemAmountInput = ingrediant["amount"]
                inputIDs.append((itemIDInput, itemAmountInput))

                item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemIDInput)
                if item is None:
                    print("ERROR", itemIDInput)
                    continue
                itemBuyPrice = [item.getInstaSellPrice() + .1] * itemAmountInput
                if len(itemBuyPrice) != itemAmountInput:
                    print(f"[BazaarFlipper]: Item {itemIDInput}. not enough in buy!")
                    continue

                itemBuyPriceTotal += sum(itemBuyPrice)
            sorters.append(
                Sorter(
                    sortKey="profit",
                    profit=itemSellPrice-itemBuyPriceTotal,
                    sellPrice=itemSellPrice,
                    buyPrice=itemBuyPriceTotal,
                    inputStr="".join([f"{ID}[{amount}], " for ID, amount in inputIDs])[:-2],
                    inputIDs=inputIDs,
                    outputID=itemIDOutput,
                    forgeTime=recipe["duration"]
                )
            )
        sorters.sort()
        for sorter in sorters:
            self.treeView.addEntry(
                sorter["outputID"],
                sorter["inputStr"],
                parsePrizeToStr(sorter["buyPrice"]),
                parsePrizeToStr(sorter["sellPrice"]),
                parseTimeFromSec(sorter["forgeTime"])
            )
    def onShow(self, **kwargs):
        self.placeRelative()
        self.placeContentFrame()
        self.master.updateCurrentPageHook = self.updateTreeview
        self.updateTreeview()