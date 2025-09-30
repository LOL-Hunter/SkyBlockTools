from typing import List
from pyperclip import copy as copyStr
import tksimple as tk

from core.constants import STYLE_GROUP as SG, API, AuctionItemID, RARITY_COLOR_CODE
from core.settings import Config
from core.skyMisc import (
    parseTimeFromSec,
    parsePrizeToStr,
    search,
    parseTimeDelta,
    iterDict,
    getLBin,
    Sorter
)
from core.widgets import ItemToolTip
from core.analyzer import calculateEstimatedItemValue
from core.widgets import CustomPage
from core.hyPI.parser import BaseAuctionProduct, NORAuctionProduct, BINAuctionProduct

class AuctionHousePage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Auction House", buttonText="Auction House")
        self.selectedItem = None
        self.window = master
        self.shownAuctions = []
        self.showOwnAuctions = False
        self.isMenuShown = False
        self.menuMode = None # "pet"
        self.lastSelected = None
        self.itemToolTip = None
        self.colorMode = None

        self.tvScroll = tk.ScrollBar(self.contentFrame, SG)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.setSingleSelect()
        self.treeView.attachVerticalScrollBar(self.tvScroll)
        self.treeView.setTableHeaders("Name", "Lowest BIN")
        self.treeView.onDoubleSelectEvent(self.onDoubleClick)
        self.treeView.bind(self.onRClick, tk.EventType.RIGHT_CLICK)
        self.treeView.bind(self.onLClick, tk.EventType.LEFT_CLICK_RELEASE)
        self.treeView.bind(self.onBtn, tk.EventType.MOUSE_PREV)
        self.treeView.placeRelative(changeHeight=-25, changeWidth=-2)

        self.searchBtn = tk.Button(self.contentFrame, SG)
        self.searchBtn.setText("Show My Auctions")
        self.searchBtn.setCommand(self.onBtn)
        self.searchBtn.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.searchL = tk.Label(self.contentFrame, SG)
        self.searchL.setText("Search: ")

        self.searchE = tk.Entry(self.contentFrame, SG)
        self.searchE.bind(self._clearAndUpdate, tk.EventType.RIGHT_CLICK)
        self.searchE.onUserInputEvent(self.updateTreeView)

        self.ownContextM = tk.ContextMenu(self.treeView, group=SG, eventType=None)
        tk.Button(self.ownContextM).setText("View this Item in AH").setCommand(self.viewSelectedItem)
        self.ownContextM.create()

        self.itemContextM = tk.ContextMenu(self.treeView, group=SG, eventType=None)
        tk.Button(self.itemContextM).setText("copy in-game Command").setCommand(self.copyURL)
        self.itemContextM.create()

        self.auctionType = tk.DropdownMenu(self.contentFrame, SG, optionList=["BIN only", "Auctions only"])
        self.auctionType.setText("BIN only")
        self.auctionType.onSelectEvent(self.updateTreeView)
        self.auctionType.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=450)

        self.menuOpenCloseBtn = tk.Button(self.contentFrame, SG)
        self.menuOpenCloseBtn.setText("<")
        self.menuOpenCloseBtn.setCommand(self.toggleMenu)
        self.menuOpenCloseBtn.placeRelative(fixHeight=50, fixWidth=25, stickRight=True, changeX=-21, stickDown=True, changeY=-28-(400/2+50/2))

        self.settingsMenu = tk.LabelFrame(self.contentFrame, SG)

        tk.Label(self.settingsMenu, SG).setText("Rarity:").placeRelative(fixHeight=25, stickDown=True, xOffsetRight=50, changeHeight=-5, changeWidth=-5)
        self.raritySelectC = tk.DropdownMenu(self.settingsMenu, SG,optionList=["All", "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"], readonly=True)
        self.raritySelectC.setText("All")
        self.raritySelectC.onSelectEvent(self.updateTreeView)
        self.raritySelectC.placeRelative(fixHeight=25, stickDown=True, xOffsetLeft=50, changeHeight=-5, changeWidth=-5)

        self.colorL = tk.Label(self.settingsMenu, SG)
        self.colorL.setText("Color Mode:")
        self.colorL.placeRelative(fixHeight=25, stickDown=True, changeY=-25, changeHeight=-5, changeWidth=-5,fixX=0, fixWidth=(250 - 5) // 2)

        self.colorD = tk.DropdownMenu(self.settingsMenu, SG)
        self.colorD.setOptionList([
            "None",
            "Show Rarity",
            "Estimated Price"
        ])
        self.colorD.setValue("Show Rarity")
        self.colorD.onSelectEvent(self.updateTreeView)
        self.colorD.placeRelative(fixHeight=25, stickDown=True, changeY=-25, changeHeight=-5, changeWidth=-5,fixX=(250 - 5) // 2, fixWidth=(250 - 5) // 2)

        self.hideSkinsC = tk.Checkbutton(self.settingsMenu, SG)
        self.hideSkinsC.setText("Hide Skins").setSelected()
        self.hideSkinsC.onSelectEvent(self.updateTreeView)
        self.hideSkinsC.placeRelative(fixHeight=25, stickDown=True, changeY=-50, changeHeight=-5, changeWidth=-5, fixX=0, fixWidth=(250-5)//2)

        self.hideDyesC = tk.Checkbutton(self.settingsMenu, SG)
        self.hideDyesC.setText("Hide Dyes").setSelected()
        self.hideDyesC.onSelectEvent(self.updateTreeView)
        self.hideDyesC.placeRelative(fixHeight=25, stickDown=True, changeY=-50, changeHeight=-5, changeWidth=-5, fixX=(250-5)//2, fixWidth=(250-5)//2)

        self.estmUseOfferC = tk.Checkbutton(self.settingsMenu, SG)
        self.estmUseOfferC.setText("Use instaBuy for Estimated").setSelected()
        self.estmUseOfferC.onSelectEvent(self.updateTreeView)
        self.estmUseOfferC.placeRelative(fixHeight=25, stickDown=True, changeY=-75, changeHeight=-5, changeWidth=-5)

        self.petMenuF = tk.Frame(self.settingsMenu, SG)
        self.check_filterC = tk.Checkbutton(self.petMenuF, SG)
        self.check_filterC.setText("Filter Pet-Lvl")
        self.check_filterC.onSelectEvent(self.updateTreeView)
        self.check_filterC.placeRelative(fixHeight=25)

        self.ownAuctionF = tk.Frame(self.settingsMenu, SG)
        self.own_sumL2 = tk.Label(self.ownAuctionF, SG)
        self.own_sumL2.setFont(13)
        self.own_sumL2.setText("If all Sold: ")
        self.own_sumL2.placeRelative(xOffsetRight=50, fixHeight=25)
        self.own_sumL = tk.Label(self.ownAuctionF, SG)
        self.own_sumL.setFg("green")
        self.own_sumL.setFont(13)
        self.own_sumL.placeRelative(xOffsetLeft=50, fixHeight=25)
    def clearMenu(self):
        self.petMenuF.placeForget()
        self.check_filterC.setState(False)
        self.raritySelectC.setText("All")
        self.ownAuctionF.placeForget()
        self.menuMode = None
    def configureMenu(self, auctions:List[BaseAuctionProduct]):
        if self.showOwnAuctions:
            sum_ = 0
            for auc in auctions:
                if isinstance(auc, BINAuctionProduct):
                    sum_ += auc.getPrice()
                elif isinstance(auc, NORAuctionProduct):
                    sum_ += auc.getHighestBid()
            self.own_sumL.setText(f"+ {parsePrizeToStr(sum_)}")
            self.ownAuctionF.placeRelative(changeWidth=-5, changeHeight=-5-50)
        elif self.selectedItem is not None:
            if not len(auctions): return
            if auctions[0].isPet():
                self.menuMode = "pet"
                self.petMenuF.placeRelative(changeWidth=-5, changeHeight=-5-50)
    def toggleMenu(self):
        self.isMenuShown = not self.isMenuShown
        if self.isMenuShown:
            self.openMenu()
        else:
            self.closeMenu()
    def closeMenu(self):
        self.isMenuShown = False
        self.menuOpenCloseBtn.setText("<")
        self.settingsMenu.placeForget()
        self.menuOpenCloseBtn.placeRelative(fixHeight=50, fixWidth=25, stickRight=True, changeX=-21, stickDown=True, changeY=-28 - (400 / 2 + 50 / 2))
    def openMenu(self):
        self.isMenuShown = True
        self.menuOpenCloseBtn.setText(">")
        self.settingsMenu.placeRelative(fixWidth=250, fixHeight=400, stickDown=True, stickRight=True, changeY=-28,changeX=-21)
        self.menuOpenCloseBtn.placeRelative(fixHeight=50, fixWidth=25, stickRight=True, changeX=-21 - 250, stickDown=True, changeY=-28 - (400 / 2 + 50 / 2))
        self.master.updateDynamicWidgets()

    def _filterPets(self, auctions:List[Sorter])->List[Sorter]:
        if not len(auctions): return []
        if isinstance(auctions[0]["auctClass"], NORAuctionProduct): return auctions # not supported
        pet_lvl_set = {}
        for sorter in auctions:
            auction: BaseAuctionProduct = sorter["auctClass"]
            lvl = auction.getPetLevel()
            pet_lvl_set[lvl] = sorter
        sorted_ = list(pet_lvl_set.values())
        sorted_.sort()
        sorted_.reverse()
        currentLvl = 0
        out = []
        for sorter in sorted_:
            auction: BaseAuctionProduct = sorter["auctClass"]
            lvl = auction.getPetLevel()
            if lvl > currentLvl:
                out.append(sorter)
                currentLvl = lvl
        out.sort()
        return out
    def _filterRarities(self, auctions:List[Sorter])->List[Sorter]:
        if not len(auctions): return []
        if isinstance(auctions[0]["auctClass"], NORAuctionProduct): return auctions # not supported

        raritiy = self.raritySelectC.getValue()
        if raritiy.lower() == "all": return auctions
        out = []
        for sorter in auctions:
            auction: BaseAuctionProduct = sorter["auctClass"]
            rar = auction.getRarity()
            if rar.upper() == raritiy.upper():
                out.append(sorter)
        return out
    def filterAuctions(self, auctions:List[Sorter])->List[Sorter]:
        if not len(auctions): return []
        out = auctions.copy()
        out = self._filterRarities(out)
        if self.menuMode == "pet":
            if self.check_filterC.getState():
                out = self._filterPets(out)
        return out

    def viewSelectedItem(self):
        index = self.treeView.getSelectedIndex()
        if index is None: return
        self.clearMenu()
        auct = self.shownAuctions[index]
        self.selectedItem = auct.getID()
        print(self.selectedItem)
        self.showOwnAuctions = False
        self.updateTreeView()
    def copyURL(self):
        sel = self.treeView.getSelectedIndex()
        if sel is None: return
        auction = self.shownAuctions[sel]
        copyStr(f"/viewauction {auction.getAuctionID()}")
    def placeMainWidgets(self):
        self.searchL.placeRelative(fixHeight=25, stickDown=True, fixWidth=75, fixX=150)
        self.searchE.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=250)
    def removeWidgets(self):
        self.searchE.placeForget()
        self.searchL.placeForget()
    def _clearAndUpdate(self):
        self.searchE.clear()
        self.updateTreeView()
        self.searchE.setFocus()
    def filterView(self, itemID:str)->bool:
        if self.hideDyesC.getState() and itemID.startswith("DYE_"): return True
        if self.hideSkinsC.getState() and (itemID.startswith("PET_SKIN") or itemID.endswith("SKIN")): return True
        return False
    def getTags(self, rarity, type_, estimPrice):
        tags = [type_]
        if self.colorMode == "Show Rarity":
            tags.append(rarity)
        elif self.colorMode == "Estimated Price":
            tags.append(estimPrice)
        return tuple(tags)
    def renderOwnAuctions(self):
        ownAuctionUUIDs: dict = Config.SETTINGS_CONFIG["auction_creator_uuids"]
        self.searchBtn.setText("< Back")
        if self.auctionType.getValue() == "BIN only":
            self.treeView.setTableHeaders("Display-Name", "BIN-Price", "Ending-In")
            binAuctions = API.SKYBLOCK_AUCTION_API_PARSER.getBinAuctions()
            sorters = []
            for auct in binAuctions:
                if auct.getCreatorUUID() not in ownAuctionUUIDs.keys(): continue  # own Auction
                pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                sorters.append(
                    Sorter(
                        sortKey="bin_price",

                        display_name=auct.getDisplayName() + ("" if pName is None else f" ({pName})"),
                        bin_price=auct.getPrice(),
                        ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                        auctClass=auct,
                        isOwn=pName is not None
                    )
                )
            self.setPageTitle(f"Auction House [Your BIN-Auctions] ({len(sorters)} found)")
            sorters.sort()
            sorters = self.filterAuctions(sorters)
            for auct in sorters:
                self.shownAuctions.append(auct["auctClass"])
                self.treeView.addEntry(
                    auct["display_name"],
                    parsePrizeToStr(auct["bin_price"]),
                    "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                    tag=("own", auct['auctClass'].getRarity()) if auct["isOwn"] else (
                    "bin", auct['auctClass'].getRarity())
                )
            self.treeView.see(-1)
        if self.auctionType.getValue() == "Auctions only":
            self.treeView.setTableHeaders("Display-Name", "Price", "Ending-In", "Bids")
            auctions = API.SKYBLOCK_AUCTION_API_PARSER.getAuctionByID(self.selectedItem)
            sorters = []
            for auct in auctions:
                if auct.getCreatorUUID() not in ownAuctionUUIDs.keys(): continue  # own Auction
                pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                sorters.append(
                    Sorter(
                        sortKey="ending_in",

                        display_name=auct.getDisplayName() + ("" if pName is None else f" ({pName})"),
                        price=auct.getHighestBid(),
                        ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                        bids=auct.getBidAmount(),
                        auctClass=auct,
                        isOwn=pName is not None
                    )
                )
            self.setPageTitle(f"Auction House [Your Auctions] ({len(sorters)} found)")
            sorters.sort()
            sorters = self.filterAuctions(sorters)
            for auct in sorters:
                self.shownAuctions.append(auct["auctClass"])
                self.treeView.addEntry(
                    auct["display_name"],
                    parsePrizeToStr(auct["price"]),
                    "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                    parsePrizeToStr(auct["bids"], hideCoins=True),
                    tag=("own", auct['auctClass'].getRarity()) if auct["isOwn"] else (
                    "auc", auct['auctClass'].getRarity())
                )
            self.treeView.see(-1)
        self.configureMenu(self.shownAuctions)
    def renderAuctions(self):
        ownAuctionUUIDs: dict = Config.SETTINGS_CONFIG["auction_creator_uuids"]
        self.searchBtn.setText("Show My Auctions")
        self.placeMainWidgets()
        if self.searchE.getValue() == "":
            validItems = None
        else:
            validItems = search([AuctionItemID], self.searchE.getValue(), printable=False)

        if self.auctionType.getValue() == "BIN only":
            self.setPageTitle(f"Auction House [BIN]")
            metaSorters = []
            ownAuctionIDs = set()
            self.treeView.setTableHeaders("Name", "Lowest-BIN", "Highest-BIN", "Active-Auctions")
            for auct_ID, activeAucs in zip(*API.SKYBLOCK_AUCTION_API_PARSER.getBinTypeAndAuctions()):
                if auct_ID is None: continue  # auction Items that cannot be registered
                if validItems is not None and auct_ID not in validItems: continue
                sorters = []
                if not len(activeAucs): continue
                if self.filterView(activeAucs[0].getID()): continue
                for auction in activeAucs:
                    pName = None
                    if auction.getCreatorUUID() in ownAuctionUUIDs.keys():  # own Auction
                        pName = ownAuctionUUIDs[auction.getCreatorUUID()]
                        ownAuctionIDs.add(auction.getID())
                    sorters.append(
                        Sorter(
                            sortKey="price".lower(),

                            name=auction.getID() + ("" if pName is None else f" ({pName})"),
                            price=auction.getPrice(),
                            auctClass=auction,
                        )
                    )
                sorters.sort()
                metaSorters.append(
                    Sorter(
                        sortKey="lowest_bin".lower(),

                        name=sorters[0]["name"],
                        lowest_bin=sorters[-1]["price"],
                        highest_bin=sorters[0]["price"],
                        active_auctions=len(sorters),
                        auctClass=sorters[0]["auctClass"]
                    )
                )
            metaSorters.sort()
            metaSorters = self.filterAuctions(metaSorters)
            for metaSorter in metaSorters:
                self.shownAuctions.append(metaSorter["auctClass"])
                self.treeView.addEntry(
                    metaSorter["name"] + (f" (Contains active Auction)" if metaSorter['name'] in ownAuctionIDs else ""),
                    parsePrizeToStr(metaSorter["lowest_bin"]),
                    parsePrizeToStr(metaSorter["highest_bin"]),
                    parsePrizeToStr(metaSorter["active_auctions"], hideCoins=True),
                    tag=("own", metaSorter['auctClass'].getRarity()) if metaSorter['name'] in ownAuctionIDs else (
                    "bin", metaSorter['auctClass'].getRarity())
                )
        if self.auctionType.getValue() == "Auctions only":
            self.setPageTitle(f"Auction House [AUCTIONS]")
            metaSorters = []
            ownAuctionIDs = set()
            self.treeView.setTableHeaders("Name", "Lowest-Bid", "Ending-In", "Active-Auctions")
            for auct_ID, activeAucs in zip(*API.SKYBLOCK_AUCTION_API_PARSER.getAucTypeAndAuctions()):
                if auct_ID is None: continue  # auction Items that cannot be registered
                if validItems is not None and auct_ID not in validItems: continue
                sorters = []
                if not len(activeAucs): continue
                if self.filterView(activeAucs[0].getID()): continue
                for auction in activeAucs:
                    if auction.getCreatorUUID() in ownAuctionUUIDs.keys():  # own Auction
                        ownAuctionIDs.add(auction.getID())
                    sorters.append(
                        Sorter(
                            sortKey="price".lower(),

                            name=auction.getID(),
                            price=auction.getHighestBid(),
                            ending=parseTimeDelta(auction.getEndIn()).toSeconds(),
                            auctClass=auction,
                        )
                    )
                sorters.sort()
                metaSorters.append(
                    Sorter(
                        sortKey="lowest_bid".lower(),

                        name=sorters[0]["name"],
                        lowest_bid=sorters[-1]["price"],
                        ending=sorters[-1]["ending"],
                        active_auctions=len(sorters),
                        auctClass=sorters[0]["auctClass"]
                    )
                )
            metaSorters.sort()
            metaSorters = self.filterAuctions(metaSorters)
            for metaSorter in metaSorters:
                self.shownAuctions.append(metaSorter["auctClass"])
                self.treeView.addEntry(
                    metaSorter["name"] + (f" (Contains active Auction)" if metaSorter['name'] in ownAuctionIDs else ""),
                    parsePrizeToStr(metaSorter["lowest_bid"]),
                    "ENDED" if metaSorter["ending"] <= 0 else parseTimeFromSec(metaSorter["ending"]),
                    parsePrizeToStr(metaSorter["active_auctions"], hideCoins=True),
                    tag=("own", metaSorter['auctClass'].getRarity()) if metaSorter['name'] in ownAuctionIDs else (
                    "auc", metaSorter['auctClass'].getRarity())
                )
        self.configureMenu(self.shownAuctions)
    def renderSelectedAuctions(self):
        ownAuctionUUIDs: dict = Config.SETTINGS_CONFIG["auction_creator_uuids"]
        self.searchBtn.setText("< Back")
        self.removeWidgets()
        if self.auctionType.getValue() == "BIN only":
            lowestBin = getLBin(self.selectedItem)
            self.treeView.setTableHeaders("Display-Name", "BIN-Price", "Ending-In", "Estimated-Price")
            binAuctions = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(self.selectedItem)
            self.setPageTitle(f"Auction House [{self.selectedItem}] ({len(binAuctions)} found)")
            sorters = []
            for auct in binAuctions:
                pName = None
                if auct.getCreatorUUID() in ownAuctionUUIDs.keys():  # own Auction
                    pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                estimatedPrice, desc, data = calculateEstimatedItemValue(auct, not self.estmUseOfferC.getState(), lowestBin)
                estimatedPriceDiff = "Could not be calculated!"
                if estimatedPrice is not None:
                    estimatedPriceDiff = estimatedPrice - auct.getPrice()
                sorters.append(
                    Sorter(
                        sortKey="bin_price",

                        display_name=auct.getDisplayName() + ("" if pName is None else f" ({pName})"),
                        bin_price=auct.getPrice(),
                        ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                        auctClass=auct,
                        estimated_price=estimatedPrice,
                        estimated_price_diff=estimatedPriceDiff,
                        isOwn=pName is not None
                    )
                )
            sorters.sort()
            sorters = self.filterAuctions(sorters)
            for auct in sorters:
                self.shownAuctions.append(auct["auctClass"])

                type_ = "own" if auct["isOwn"] else "bin"
                estimatedPrice_ = None

                if type(auct["estimated_price_diff"]) is not str:
                    if auct["estimated_price_diff"] > 0: estimatedPrice_ = "good_price"
                    else: estimatedPrice_ = "bad_price"

                self.treeView.addEntry(
                    auct["display_name"],
                    parsePrizeToStr(auct["bin_price"]),
                    "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                    parsePrizeToStr(auct["estimated_price_diff"], forceSign=True),
                    tag=self.getTags(auct["auctClass"].getRarity(), type_, estimatedPrice_),
                )
            self.treeView.see(-1)
        if self.auctionType.getValue() == "Auctions only":
            self.treeView.setTableHeaders("Display-Name", "Price", "Ending-In", "Bids")
            auctions = API.SKYBLOCK_AUCTION_API_PARSER.getAuctionByID(self.selectedItem)
            self.setPageTitle(f"Auction House [{self.selectedItem}] ({len(auctions)} found)")
            sorters = []
            for auct in auctions:
                pName = None
                if auct.getCreatorUUID() in ownAuctionUUIDs.keys():  # own Auction
                    pName = ownAuctionUUIDs[auct.getCreatorUUID()]
                sorters.append(
                    Sorter(
                        sortKey="ending_in",

                        display_name=auct.getDisplayName() + ("" if pName is None else f" ({pName})"),
                        price=auct.getHighestBid(),
                        ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                        bids=auct.getBidAmount(),
                        auctClass=auct,
                        isOwn=pName is not None
                    )
                )
            sorters.sort()
            sorters = self.filterAuctions(sorters)
            for auct in sorters:
                self.shownAuctions.append(auct["auctClass"])
                self.treeView.addEntry(
                    auct["display_name"],
                    parsePrizeToStr(auct["price"]),
                    "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                    parsePrizeToStr(auct["bids"], hideCoins=True),
                    tag=("own", auct['auctClass'].getRarity()) if auct["isOwn"] else (
                    "auc", auct['auctClass'].getRarity())
                )
            self.treeView.see(-1)
        self.configureMenu(self.shownAuctions)
    def updateTreeView(self):
        self.treeView.clear()
        self.colorMode = self.colorD.getValue()
        if API.SKYBLOCK_AUCTION_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        self.shownAuctions = []
        if self.showOwnAuctions:
            self.renderOwnAuctions()
        elif self.selectedItem is None: # show all
            self.renderAuctions()
        else:
            self.renderSelectedAuctions()
        self.treeView.setBgColorByTag("own", tk.Color.rgb(26, 156, 17))
        for k, v in iterDict(RARITY_COLOR_CODE):
            self.treeView.setFgColorByTag(k, v)
        self.treeView.setFgColorByTag("good_price", "green")
        self.treeView.setFgColorByTag("bad_price", "red")
    def closeToolTip(self):
        if self.itemToolTip is not None:
            self.itemToolTip.close()
            self.itemToolTip = None
    def onBtn(self):
        self.closeToolTip()
        self.clearMenu()
        if self.selectedItem is not None:
            self.selectedItem = None
        elif self.showOwnAuctions:
            self.selectedItem = None
            self.showOwnAuctions = False
        else:
            self.showOwnAuctions = True
        self.updateTreeView()
    def onLClick(self, e:tk.Event):
        if self.selectedItem is None and not self.showOwnAuctions:
            return
        selectedItem = self.treeView.getSelectedIndex()
        if selectedItem is None: return
        if self.lastSelected == selectedItem:
            self.treeView.clearSelection()
            self.treeView.update()
            if self.itemToolTip is not None:
                self.itemToolTip.close()
                self.itemToolTip = None
            self.lastSelected = None
            return
        self.lastSelected = selectedItem
        if not len(self.shownAuctions): return
        self.closeToolTip()
        self.itemToolTip = ItemToolTip(self.master, self.shownAuctions[selectedItem])
        self.itemToolTip.open()
    def onRClick(self, e:tk.Event):
        if self.showOwnAuctions:
            self.ownContextM.open(e)
        elif self.selectedItem is not None:
            self.itemContextM.open(e)
    def onDoubleClick(self, e):
        sel = e.getValue()
        if sel is None: return
        if self.selectedItem is None and not self.showOwnAuctions:
            self.selectedItem = (sel["Name"] if "(" not in sel["Name"] else sel["Name"].split("(")[0]).strip()
            self.updateTreeView()
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
    def onHide(self):
        self.closeToolTip()