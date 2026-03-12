import tksimple as tk
from typing import Tuple, List

from core.constants import STYLE_GROUP as SG, BazaarItemID
from core.skyMisc import parsePrizeToStr, search, RecipeResult, ItemPrice
from core.widgets import CustomPage
from core.bazaarAnalyzer import BazaarAnalyzer
from core.hyPI.recipeAPI import RecipeAPI
from core.featureLoader import loadableFeature
from src.core.logger import MsgText


@loadableFeature
class BazaarCraftProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(
            master,
            pageTitle="Bazaar-Craft-Profit",
            buttonText="Bazaar Craft Profit"
        )
        self.currentParser = None

        self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useBuyOffers.setText("Use-Buy-Offers")
        self.useBuyOffers.onSelectEvent(self.onUpdate)
        self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.onSelectEvent(self.onUpdate)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.showStackProfit = tk.Checkbutton(self.contentFrame, SG)
        self.showStackProfit.setText("Show-Profit-as-Stack[x64]")
        self.showStackProfit.onSelectEvent(self.onUpdate)
        self.showStackProfit.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=300)

        tk.Label(self.contentFrame, SG).setText("Search:").placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=500)

        self.searchE = tk.Entry(self.contentFrame, SG)
        self.searchE.bind(self._clearAndUpdate, tk.EventType.RIGHT_CLICK)
        self.searchE.onUserInputEvent(self.onUpdate)
        self.searchE.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=600)

        self.recursiveCraft = tk.Checkbutton(self.contentFrame, SG)
        self.recursiveCraft.setText("Add-Deep-Recipes")
        self.recursiveCraft.onSelectEvent(self.onUpdate)
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
            "ENCHANTED_CAKE"
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
        self.onUpdate()
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
    def onUpdate(self):
        self.treeView.clear()
        if not self.showStackProfit.getState():
            factor = 1
            headers = ["Recipe", "Profit-Per-Item", "Ingredients-Buy-Price-Per-Item", "Needed-Item-To-Craft"]
        else:
            factor = 64
            headers = ["Recipe", "Profit-Per-Stack[x64]", "Ingredients-Buy-Price-Per-Stack[x64]", "Needed-Item-To-Craft[x64]"]

        if self.recursiveCraft.getState():
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

            itemPrice = ItemPrice.getBazaarItemSellPrice(result, useSellOffer=self.useSellOffers.getState())

            if itemPrice.failed():
                MsgText.error(itemPrice.getError())
                continue

            resultPrice = itemPrice.getPrice()
            ingredients = recipe.getItemInputList()
            craftPrice = 0
            requiredItemString = "("

            ## ingredients calc ##
            for ingredient in ingredients:
                name = ingredient["name"]
                amount = ingredient["amount"]
                requiredItemString+=f"{name}[{amount*factor}], "

                if name not in BazaarItemID: continue

                ingredientItem = ItemPrice.getBazaarItemBuyPrice(name, useBuyOrder=self.useBuyOffers.getState())
                if ingredientItem.failed():
                    MsgText.error(ingredientItem.getError())
                craftPrice += ingredientItem.getPrice()
            profitPerCraft = resultPrice - craftPrice # profit calculation
            requiredItemString = requiredItemString[:-2]+")"

            recipeList.append(RecipeResult(result, profitPerCraft*factor, craftPrice*factor, requiredItemString))
        recipeList.sort()
        for rec in recipeList:
            content = [
                rec.getID(),
                parsePrizeToStr(rec.getProfit()),
                parsePrizeToStr(rec.getCraftPrice()),
                rec.getRequired()
            ]
            if self.recursiveCraft.getState():
                content.append(rec.getCraftDepth())
            self.treeView.addEntry(*content)
    def onShow(self, **kwargs):
        self.validRecipes = self._getValidRecipes()
        self.validBzItems = [i.getID() for i in self.validRecipes]
        super().onShow()