import os

import tksimple as tk
from core.analyzer import getCheapestEnchantmentData
from core.constants import Path, ALL_ENCHANTMENT_IDS
from core.constants import STYLE_GROUP as SG, API
from core.skyMisc import parsePrizeToStr, BookCraft
from core.widgets import CustomPage


class EnchantingBookBazaarCheapestPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Cheapest Book Craft Page", buttonText="Cheapest Book Craft")
        self.currentItem = None
        self.currentParser = None
        # mark best !!!
        self.eBookImage = tk.PILImage.loadImage(os.path.join(Path.IMAGES, "enchanted_book.gif")).resizeToIcon().preRender()

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

        if not self.useBuyOffers.getState(): # isInstaBuy?
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Saved-Coins")
        else:
            self.treeView.setTableHeaders("Using-Book", "Buy-Price-Per-Item", "Total-Buy-Price", "Saved-Coins", "Others-try-to-buy")

        eData = getCheapestEnchantmentData(API.SKYBLOCK_BAZAAR_API_PARSER, self.currentItem, instaBuy=not self.useBuyOffers.getState())
        if eData is not None:
            targetBookInstaBuy = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(self.currentItem).getInstaBuyPrice()
            eData = [BookCraft(d, targetBookInstaBuy) for d in eData] # convert so sortable BookCraft instances
            eData.sort()
            for bookCraft in eData:
                if not self.useBuyOffers.getState():
                    if bookCraft.getFromAmount() is None: continue
                    self.treeView.addEntry(
                        bookCraft.getShowAbleIDFrom()+f" [x{bookCraft.getFromAmount()}]",
                        parsePrizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                        parsePrizeToStr(bookCraft.getFromPrice()),
                        parsePrizeToStr(bookCraft.getSavedCoins()),
                        image=self.eBookImage
                    )
                else:
                    if bookCraft.getFromAmount() is None:
                        pass

                    self.treeView.addEntry(
                        bookCraft.getShowAbleIDFrom() + f" [x{bookCraft.getFromAmount()}]",
                        parsePrizeToStr(bookCraft.getFromPriceSingle(round_=2)),
                        parsePrizeToStr(bookCraft.getFromPrice()),
                        parsePrizeToStr(bookCraft.getSavedCoins()),
                        parsePrizeToStr(bookCraft.getFromSellVolume(), hideCoins=True),
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