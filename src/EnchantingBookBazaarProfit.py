import os

from core.jsonConfig import JsonConfig

import tksimple as tk
from core.constants import STYLE_GROUP as SG, Path, API
from core.skyMisc import parsePrizeToStr, BookCraft
from core.skyMath import applyBazaarTax
from core.analyzer import getDictEnchantmentIDToLevels, getCheapestEnchantmentData
from core.widgets import CustomPage


class EnchantingBookBazaarProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Book Combine Profit Page", buttonText="Book Combine Profit")

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("Name", "Buy-Price", "Sell-Price", "Profit", "Times-Combine", "Insta-Sell/Hour", "Insta-Buy/Hour")
        self.treeView.placeRelative(changeHeight=-25)

        self.eBookImage = tk.PILImage.loadImage(os.path.join(Path.IMAGES, "enchanted_book.gif")).resizeToIcon().preRender()

        # only these enchantments are shown
        self.whiteList = None
        path = os.path.join(Path.INTERNAL_CONFIG, "enchantment_profit_whitelist.json")
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

        if not self.useBuyOffers.getState():  # isInstaBuy?
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Profit")
        else:
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Profit", "Others-try-to-buy")
        if self.whiteList is None:
            tk.SimpleDialog.askError(self.master, "Could not load WhitelistFile! Showing All.")
        eDataComplete = []
        enchIDToLvl = getDictEnchantmentIDToLevels()
        for currentItem in enchIDToLvl.keys():
            if self.whiteList is not None and self.useWhiteList.getState(): # whiteList Active
                if currentItem not in self.whiteList and not (self.includeUltimate.getState() and currentItem.startswith("ENCHANTMENT_ULTIMATE")):
                    continue
            currentItem = enchIDToLvl[currentItem][-1] # get Highest Enchantment


            eData = getCheapestEnchantmentData(API.SKYBLOCK_BAZAAR_API_PARSER, currentItem, instaBuy=not self.useBuyOffers.getState())
            if eData is not None:
                if self.useSellOffers.getState(): # insta sell
                    targetBookInstaBuy = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(currentItem).getInstaBuyPrice()
                else:
                    targetBookInstaBuy = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(currentItem).getInstaSellPrice()

                targetBookInstaBuy = applyBazaarTax(targetBookInstaBuy) # apply Tax

                eData = [BookCraft(d, targetBookInstaBuy) for d in eData]  # convert so sortable BookCraft instances
                eData.sort()
                eDataComplete.append(eData[0]) #get best BookCraft instance


        eDataComplete.sort()
        for bookCraft in eDataComplete:
            if not self.useBuyOffers.getState():
                if bookCraft.getFromAmount() is None: continue
                self.treeView.addEntry(
                    f"{bookCraft.getShowAbleIDFrom()} [x{bookCraft.getFromAmount()}] -> {bookCraft.getShowAbleIDTo()}",
                    parsePrizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                    parsePrizeToStr(bookCraft.getFromPrice()),
                    parsePrizeToStr(bookCraft.getSavedCoins()),
                    image=self.eBookImage
                )
            else:
                if bookCraft.getFromAmount() is None:
                    pass

                self.treeView.addEntry(
                    f"{bookCraft.getShowAbleIDFrom()} [x{bookCraft.getFromAmount()}] -> {bookCraft.getShowAbleIDTo()}",
                    parsePrizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                    parsePrizeToStr(bookCraft.getFromPrice()),
                    parsePrizeToStr(bookCraft.getSavedCoins()),
                    parsePrizeToStr(bookCraft.getFromSellVolume(), hideCoins=True),
                    image=self.eBookImage
                )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()