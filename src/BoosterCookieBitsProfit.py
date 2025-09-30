import os

from core.jsonConfig import JsonConfig

import tksimple as tk
from core.constants import STYLE_GROUP as SG, Path, API
from core.settings import Config
from core.skyMath import applyBazaarTax
from core.skyMisc import iterDict, Sorter, parsePrizeToStr
from core.widgets import CustomPage
from core.logger import MsgText


class BoosterCookieBitsProfit(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Booster Cookie Bits Profit", buttonText="Bits Profit")
        self.bitsConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "bit_shop.json"))
        self.multipliers = [1, 1.1, 1.2, 1.3, 1.4, 1.6, 1.8, 1.9, 2.0, 2.04, 2.08, 2.12, 2.16, 2.2, 2.22, 2.24, 2.26, 2.28, 2.3, 2.32, 2.34, 2.36, 2.38, 2.4]

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setTableHeaders("ItemID", "CoinsPerBit", "CookieProfit", "ItemCost", "SellAmount")
        self.treeView.placeRelative(changeHeight=-25)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.onSelectEvent(self.updateTreeview)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=0)

        self.rankSelect = tk.DropdownMenu(self.contentFrame, SG)
        self.rankSelect.setOptionList(["New_Player", "Settler", "Citizen", "Contributor", "Philanthropist", "Patron", "Famous_Player", "Attache", "Ambassador", "Statesperson", "Senator", "Dignitary", "Councilor", "Minister", "Premier", "Chancellor", "Supreme", "Overseer", "Regent", "Viceroy", "Sovereign", "Archon", "Imperator", "Paragon"])
        self.rankSelect.setValue(Config.SETTINGS_CONFIG["player_rank"])
        self.rankSelect.onSelectEvent(self.updateTreeview)
        self.rankSelect.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)
    def updateTreeview(self):
        BITS_BASE = 4800
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        if API.SKYBLOCK_AUCTION_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        BITS = self.multipliers[self.rankSelect.getSelectedIndex()] * BITS_BASE

        Config.SETTINGS_CONFIG["player_rank"] = self.rankSelect.getValue()
        Config.SETTINGS_CONFIG.save()

        cookie = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("BOOSTER_COOKIE")
        if cookie is None:
            tk.SimpleDialog.askError(self.master, "Error getting 'BOOSTER_COOKIE' price from api!")
            return
        cookiePrice = cookie.getInstaSellPrice() + .1
        if cookiePrice == 0:
            tk.SimpleDialog.askError(self.master, "Error getting 'BOOSTER_COOKIE' price from api!")
            return

        sorters = []
        for itemID, bitCost in iterDict(self.bitsConfig.getData()):

            bzProduct = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemID)
            if bzProduct is not None:
                if self.useSellOffers.getState():  # use sell Offer
                    itemSellPrice = bzProduct.getInstaBuyPrice()
                else:  # insta sell
                    itemSellPrice = bzProduct.getInstaSellPrice()
                itemSellPrice = applyBazaarTax(itemSellPrice)
                shopType="BAZAAR"
            else:
                ahProduct = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(itemID)
                if ahProduct is None:
                    MsgText.error(f"Could not find Item in AH: {itemID}")
                    continue
                if not len(ahProduct):
                    MsgText.error(f"Could not find Auction data for item: {itemID}")
                    continue
                ahProduct.sort()
                itemSellPrice = ahProduct[-1].getPrice()
                shopType = "AUCTION"

            if itemSellPrice is None:
                MsgText.error(f"Could not get SellPrice of item ID: {itemID}")
                continue

            sorters.append(Sorter(
                sortKey="COOKIE_PROFIT",
                ID=itemID,
                BITS_COST=bitCost,
                SELL_PRICE=itemSellPrice,
                COINS_PER_BIT=itemSellPrice / bitCost,
                COOKIE_PROFIT=((BITS / bitCost)*itemSellPrice) - cookiePrice,
                SELL_AMOUNT=(BITS / bitCost),
                SHOP_TYPE=shopType,
            ))

        sorters.sort()

        for sorter in sorters:
            self.treeView.addEntry(
                sorter["ID"],
                parsePrizeToStr(sorter["COINS_PER_BIT"]),
                parsePrizeToStr(sorter["COOKIE_PROFIT"]),
                parsePrizeToStr(sorter["SELL_PRICE"]),
                str(round(sorter["SELL_AMOUNT"], 1)),
                tag=sorter["SHOP_TYPE"],
            )
        self.treeView.setBgColorByTag("AUCTION", tk.Color.rgb(138, 90, 12))
        self.treeView.setBgColorByTag("BAZAAR", tk.Color.rgb(22, 51, 45))
    def onShow(self, **kwargs):
        self.placeRelative()
        self.placeContentFrame()
        self.master.updateCurrentPageHook = self.updateTreeview
        self.updateTreeview()