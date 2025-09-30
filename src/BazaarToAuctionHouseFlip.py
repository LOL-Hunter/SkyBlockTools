import tksimple as tk
from core.constants import API, BazaarItemID
from core.constants import STYLE_GROUP as SG, AuctionItemID
from core.hyPI.recipeAPI import RecipeAPI
from core.skyMisc import (Sorter)
from core.skyMisc import parsePrizeToStr, search
from core.widgets import CustomPage


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
            result = recipe.getID()

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
                if self.useBuyOffers.getState():  # use buy Offer ingredients
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
                parsePrizeToStr(rec.get()), # profit
                parsePrizeToStr(rec["craftCost"]),
                parsePrizeToStr(rec["lowestBin"]),
                rec["reqItemsStr"]
            )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView # hook to update tv on new API-Data available
        self.validRecipes = self._getValidRecipes()
        self.validBzItems = [i.getID() for i in self.validRecipes]
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()