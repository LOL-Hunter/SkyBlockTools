import tksimple as tk
from core.constants import API, BazaarItemID
from core.constants import STYLE_GROUP as SG, AuctionItemID
from core.hyPI.recipeAPI import RecipeAPI
from core.skyMisc import (Sorter)
from core.skyMisc import parsePrizeToStr, search
from core.widgets import CustomPage
from core.featureLoader import loadableFeature
from core.logger import MsgText
from core.skyMisc import ItemPrice


@loadableFeature
class BazaarToAuctionHouseFlipProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(
            master, 
            pageTitle="Bazaar-To-Auction-Flip-Profit", 
            buttonText="Bazaar to Auction Flip Profit"
        )
        self.currentParser = None

        self.useBuyOrder = tk.Checkbutton(self.contentFrame, SG)
        self.useBuyOrder.setText("Use-Buy-Offers").setSelected()
        self.useBuyOrder.onSelectEvent(self.onUpdate)
        self.useBuyOrder.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        tk.Label(self.contentFrame, SG).setText("Search:").placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=500)

        self.searchE = tk.Entry(self.contentFrame, SG)
        self.searchE.bind(self._clearAndUpdate, tk.EventType.RIGHT_CLICK)
        self.searchE.onUserInputEvent(self.onUpdate)
        self.searchE.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=600)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("Recipe", "Profit-Per-Item", "Ingredients-Buy-Price-Per-Item", "Needed-Item-To-Craft")
        self.treeView.placeRelative(changeHeight=-25)

        self.forceAdd = [
            "DAY_SAVER"
        ]
        self.validRecipes = self._getValidRecipes()
        self.validBzItems = [i.getID() for i in self.validRecipes]
    def _clearAndUpdate(self):
        self.searchE.clear()
        self.onUpdate()
        self.searchE.setFocus()
    def _getValidRecipes(self):
        validRecipes = []
        for recipe in RecipeAPI.getRecipes():
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
    def onUpdate(self):
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
        for recipe in self.validRecipes:
            result = recipe.getID()
            if self.searchE.getValue() != "" and recipe.getID() not in validItems:
                continue

            itemPrice = ItemPrice.getAuctLBinPrice(result)

            if itemPrice.failed():
                MsgText.error(itemPrice.getError())

            lowestBin = itemPrice.getPrice()

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

                itemPrice = ItemPrice.getBazaarItemBuyPrice(name, useBuyOrder=self.useBuyOrder.getState())

                if itemPrice.failed():
                    MsgText.error(itemPrice.getError())

                craftCost += itemPrice.getPrice()
            profitPerCraft = lowestBin - craftCost # profit calculation
            requiredItemString = requiredItemString[:-2]+")"

            recipeList.append(Sorter(profitPerCraft, reqItemsStr=requiredItemString, resultID=result, craftCost=craftCost, lowestBin=lowestBin))
        recipeList.sort()
        for rec in recipeList:
            self.treeView.addEntry(
                rec["resultID"],
                parsePrizeToStr(rec.get()), # profit
                parsePrizeToStr(rec["craftCost"]),
                parsePrizeToStr(rec["lowestBin"]),
                rec["reqItemsStr"]
            )
    def onShow(self, **kwargs):
        self.validRecipes = self._getValidRecipes()
        self.validBzItems = [i.getID() for i in self.validRecipes]
        super().onShow()
