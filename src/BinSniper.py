from threading import Thread
from time import sleep, time
from typing import List, Tuple
from enum import Enum

import tksimple as tk
from core.constants import (
    STYLE_GROUP as SG,
    ConfigFile,
    Constants,
    NPC_BUYABLE_PET_ITEMS,
    RARITY_COLOR_CODE,
    AUTO_RECOMBED_ITEMS,
    API,
    DUNGEON_ITEMS,
    FURNITURE_ITEMS
)
from core.hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException
from core.hyPI.skyCoflnetAPI import SkyConflnetAPI
from core.logger import MsgText
from core.settings import Config
from core.skyMath import parseTimeDelta, getMedianFromList, capPetXP, applyBazaarTax
from core.skyMisc import (
    _map,
    remEnum,
    getLBinList,
    getLBin,
    parseTimeFromSec,
    parsePrizeToStr,
    parsePriceFromStr,
    iterDict,
    throwAPITimeoutException,
    throwNoAPIKeyException,
    throwAPIConnectionException,
    Sorter
)
from core.analyzer import calculateUpgradesPrice, calculateEstimatedItemValue
from core.widgets import CustomPage, TipText, fillToolTipText
from core.hyPI.parser import BINAuctionProduct

class SortKey(Enum):
    ESTIMATED_PRICE = "estim"
    AUCTION_PRICE = "price"
    DIFF = "diff"
    DIFF_PERC = "diffPerc"
class BinSniperAnalyzer:
    SORTER = []
    FLAGGED_ITEMS = []
    # cache
    PET_ITEM_CACHE = {}
    ANALYZED_PET_SET = set()
    LBIN_CACHE = {}

    @staticmethod
    def reset():
        BinSniperAnalyzer.SORTER = []
        BinSniperAnalyzer.PET_ITEM_CACHE = {}
        BinSniperAnalyzer.LBIN_CACHE = {}
        BinSniperAnalyzer.FLAGGED_ITEMS = []
        BinSniperAnalyzer.ANALYZED_PET_SET = set()

    @staticmethod
    def updateSniper(isOrder:bool, sortKey:SortKey | str, filterType=None, filterPrice=None):
        BinSniperAnalyzer.reset()

        typeAndAuc = API.SKYBLOCK_AUCTION_API_PARSER.getBinTypeAndAuctions()

        for id_, aucts in zip(*typeAndAuc):

            if filterType is not None and not filterType(id_, len(aucts)): continue
            lbin, lbinPrice = BinSniperAnalyzer.getCustomLbinPrice(id_, isOrder)
            if lbinPrice is None: continue

            for auction in aucts:
                if auction.isPet():
                    BinSniperAnalyzer.SORTER.extend(
                        BinSniperAnalyzer.analyzePets(auction.getID(), False)
                    )
                    continue
                estimPrice, desc, data = calculateEstimatedItemValue(auction, isOrder, lbinPrice)
                price = auction.getPrice()
                if estimPrice is None:
                    MsgText.warning(f"Estim Price for {auction.getID()} is None[{desc}]. Skip, {type(lbin)}")
                    continue
                if filterPrice is not None and not filterPrice(price, estimPrice, lbinPrice, auction.getID(), auction.getUUID()): continue
                BinSniperAnalyzer.addItemToSorter(
                    sortKey,
                    lbinPrice,
                    price,
                    estimPrice,
                    desc,
                    auction,
                    len(aucts)
                )
            BinSniperAnalyzer.SORTER.sort()


    @staticmethod
    def updateSniperPage(page:int, isOrder:bool, sortKey:SortKey | str, filterType=None, filterPrice=None):
        # remove old
        for sorter in BinSniperAnalyzer.SORTER.copy():
            if sorter["page"] == page:
                BinSniperAnalyzer.SORTER.remove(sorter)
        pageAucts = API.SKYBLOCK_AUCTION_API_PARSER.getPageByID(page)._binAucts
        for auction in pageAucts:
            auctions = len(API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(auction.getID()))
            if filterType is not None and not filterType(auction.getID(), auctions): continue
            lbin, lbinPrice = BinSniperAnalyzer.getCustomLbinPrice(auction.getID(), isOrder)
            if lbinPrice is None: continue
            if auction.isPet():
                BinSniperAnalyzer.SORTER.extend(
                    BinSniperAnalyzer.analyzePets(auction.getID(), False)
                )
                continue
            estimPrice, desc, data = calculateEstimatedItemValue(auction, isOrder, lbinPrice)
            price = auction.getPrice()
            if estimPrice is None:
                MsgText.warning(f"Estim Price for {auction.getID()} is None[{desc}]. Skip, {type(lbin)}")
                continue
            if filterPrice is not None and not filterPrice(price, estimPrice, lbinPrice, auction.getID(), auction.getUUID()): continue

            BinSniperAnalyzer.addItemToSorter(
                sortKey,
                lbinPrice,
                price,
                estimPrice,
                desc,
                auction,
                auctions
            )
        BinSniperAnalyzer.SORTER.sort()


    @staticmethod
    def addItemToSorter(sortKey:SortKey, lbinPrice:float, price:float, estimPrice:float, desc:str, auction:BINAuctionProduct, numAucts:int):
        BinSniperAnalyzer.SORTER.append(
            Sorter(
                sortKey=remEnum(sortKey),

                page=auction.getPageID(),
                lowestBin=lbinPrice,
                desc=desc,
                id=auction.getID(),
                estim=estimPrice,
                price=price,
                diff=estimPrice - price,
                diffPerc=round((estimPrice / price) * 100, 1),
                clazz=auction,
                auctions=numAucts,
            )
        )

    @staticmethod
    def getCustomLbinPrice(itemID: str, isOrder: bool)->Tuple[BINAuctionProduct, float] | Tuple[None, None]:
        # get average from file if available
        if itemID in ConfigFile.AVERAGE_PRICE.keys():
            return None, ConfigFile.AVERAGE_PRICE[itemID]

        if itemID in BinSniperAnalyzer.LBIN_CACHE.keys():
            a, b, _isOrder = BinSniperAnalyzer.LBIN_CACHE[itemID]
            if _isOrder == isOrder: return a, b

        lBinList = getLBinList(itemID)

        if len(lBinList) < 5:
            # MsgText.warning(f"LBIN from {itemID} cannot be calculated! Too few Data! Skipping.")
            return None, None

        lowestBin1 = lBinList[-1]["bin_price"] - calculateUpgradesPrice(lBinList[-1]["auctClass"], isOrder)[0]
        lowestBin2 = lBinList[-2]["bin_price"] - calculateUpgradesPrice(lBinList[-2]["auctClass"], isOrder)[0]
        lowestBin3 = lBinList[-3]["bin_price"] - calculateUpgradesPrice(lBinList[-3]["auctClass"], isOrder)[0]
        # if negative ignore upgrades
        if lowestBin1 < 0 or lowestBin2 < 0 or lowestBin3 < 0:
            lowestBin1 = lBinList[-1]["bin_price"]
            lowestBin2 = lBinList[-2]["bin_price"]
            lowestBin3 = lBinList[-3]["bin_price"]
        # flag if cannot determine which price
        if lowestBin1 * 1.5 < lowestBin2 or lowestBin2 * 1.5 < lowestBin3:
            BinSniperAnalyzer.FLAGGED_ITEMS.append(itemID)
            return None, None
        BinSniperAnalyzer.LBIN_CACHE[itemID] = (lBinList[-1]["auctClass"], lowestBin1, isOrder)
        return lBinList[-1]["auctClass"], lowestBin1
    @staticmethod
    def analyzePets(id_:str, force:bool = False) -> List[Sorter]:
        def getPetItemPrice(itemID: str | None) -> float:
            if itemID is None: return 0
            if itemID in BinSniperAnalyzer.PET_ITEM_CACHE.keys():
                return BinSniperAnalyzer.PET_ITEM_CACHE[itemID]
            if itemID in NPC_BUYABLE_PET_ITEMS:
                return NPC_BUYABLE_PET_ITEMS[itemID]
            lbin = getLBin(itemID)
            if lbin is None:
                # MsgText.warning(f"Could not get PetItem price {itemID}. Using Zero.")
                return 0
            price = lbin.getPrice()
            BinSniperAnalyzer.PET_ITEM_CACHE[itemID] = price
            return price

        if id_ in BinSniperAnalyzer.ANALYZED_PET_SET and not force:
            return []
        BinSniperAnalyzer.ANALYZED_PET_SET.add(id_)

        rarityToPetMap = {}
        for auction in API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(id_):
            rarity = auction.getPetRarity()
            if rarity not in rarityToPetMap.keys():
                rarityToPetMap[rarity] = []
            rarityToPetMap[rarity].append(
                Sorter(
                    sortKey="pet_lvl",

                    page=auction.getPageID(),
                    lowestBin=None,
                    desc="",
                    id=auction.getID(),
                    price=auction.getPrice(),
                    estim=None,
                    diff=None,  # estimPrice - price
                    diffPerc=None,  # round((estimPrice / price) * 100, 1)
                    clazz=auction,
                    auctions=None,

                    pet_lvl=auction.getPetLevel(),

                    autoRecombed=False,
                )
            )
        for pets in rarityToPetMap.values():
            pets.sort()
        for rarity, pets in iterDict(rarityToPetMap):
            if len(pets) < 3:
                # MsgText.warning(f"Cannot calc Estm Value from pet {id_} with rarity {rarity} only [{len(pets)}] active Auctions. Skip.")
                continue
            smallestLvl = None
            biggestLvl = None
            for pet in pets:
                pet["auctions"] = len(pets)
                if biggestLvl is None or pet["clazz"].getPetLevel() > biggestLvl["clazz"].getPetLevel():
                    biggestLvl = pet
                if smallestLvl is None or pet["clazz"].getPetLevel() < smallestLvl["clazz"].getPetLevel():
                    smallestLvl = pet

            smallestPrice = smallestLvl["clazz"].getPrice() - getPetItemPrice(smallestLvl["clazz"].getPetItem())
            biggestPrice = biggestLvl["clazz"].getPrice() - getPetItemPrice(biggestLvl["clazz"].getPetItem())
            smallestLvlXP = capPetXP(smallestLvl["clazz"].getPetExp(), id_, rarity)
            biggestLvlXP = capPetXP(biggestLvl["clazz"].getPetExp(), id_, rarity)
            for pet in pets:
                if biggestLvl != smallestLvl:
                    estimCost = _map(
                        capPetXP(pet["clazz"].getPetExp(), id_, rarity),
                        smallestLvlXP,
                        biggestLvlXP,
                        smallestPrice,
                        biggestPrice
                    )
                else:
                    estimCost = smallestPrice
                petItemPrice = getPetItemPrice(pet["clazz"].getPetItem())
                estimCost += petItemPrice

                pet[
                    "desc"] = f"{pet['id']} [{pet['clazz'].getPetLevel()}] ({pet['clazz'].getPetRarity()})\n\nBase-Pet: {smallestLvl['clazz'].getID()}[{smallestLvl['clazz'].getPetLevel()}]"
                pet["desc"] += f"\t{parsePrizeToStr(smallestLvl['clazz'].getPrice())}\n"
                if smallestLvl['clazz'].getPetItem() is not None:
                    pet["desc"] += f"PetItem: {smallestLvl['clazz'].getPetItem()}"
                    pet["desc"] += f"\t{parsePrizeToStr(getPetItemPrice(smallestLvl['clazz'].getPetItem()))}\n"
                pet["desc"] += f"Base-Total: {parsePrizeToStr(smallestPrice)}\n\n"

                pet["desc"] += f"Highest-Pet: {biggestLvl['clazz'].getID()} [{biggestLvl['clazz'].getPetLevel()}]"
                pet["desc"] += f"\t{parsePrizeToStr(biggestLvl['clazz'].getPrice())}\n"
                if biggestLvl['clazz'].getPetItem() is not None:
                    pet["desc"] += f"PetItem: {biggestLvl['clazz'].getPetItem()}"
                    pet["desc"] += f"\t{parsePrizeToStr(getPetItemPrice(biggestLvl['clazz'].getPetItem()))}\n"
                pet["desc"] += f"Base-Total: {parsePrizeToStr(biggestPrice)}\n\n\n"

                pet["desc"] += f"This-Pet: {pet['clazz'].getID()} [{pet['clazz'].getPetLevel()}]"
                pet["desc"] += f"\t{parsePrizeToStr(estimCost - petItemPrice)}\n"
                if pet['clazz'].getPetItem() is not None:
                    pet["desc"] += f"PetItem: {pet['clazz'].getPetItem()}"
                    prize = getPetItemPrice(pet['clazz'].getPetItem())
                    if prize > 0:
                        pet["desc"] += f"\t+{parsePrizeToStr(prize)}\n"
                    else:
                        pet["desc"] += f"\tCOULD NOT CALC USING ZERO!\n"
                pet["desc"] += f"Total: {parsePrizeToStr(estimCost)}\n\n"

                pet["estim"] = estimCost
                pet["diff"] = estimCost - pet["price"]
                pet["diffPerc"] = round((estimCost / pet["price"]) * 100, 1)
        temp = []
        for pets in rarityToPetMap.values():
            temp.extend(pets)
        return temp
class BinSniperPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Bin-Sniper", buttonText="Bin Sniper")
        self.buyCap = None
        self.displayedIds = []
        self.isSideBarOpen = False
        self.analyzedPetsSet = set()
        self.isLoading = False
        self.cheapFactorValue = 1.5

        self.sortKey = "diffPerc"
        self.sortDirec = False

        self.treeview = tk.TreeView(self.contentFrame, SG)
        self.treeview.setSingleSelect()
        self.treeview.onSelectHeader(self.onHeaderSelectEvent)
        self.treeview.onSingleSelectEvent(self.onSelectEvent)
        self.treeview.onDoubleSelectEvent(self.onDoubleSelectEvent)
        self.treeview.setTableHeaders("Item-ID", "Auctions", "Price", "Estim-Price", "Diff", "Diff-%")

        self.loadingFrame = tk.Frame(self.contentFrame, SG)
        self.loadingBar = tk.Progressbar(self.loadingFrame, SG)
        self.loadingBarLabel = tk.Label(self.loadingFrame, SG)
        self.loadingBarLabel.setText("Loading Data...")
        self.loadingBar.placeRelative(fixHeight=25, center=True, xOffset=5)
        self.loadingBarLabel.placeRelative(fixHeight=25, center=True, changeY=-25)

        self.tvRClickMenu = tk.ContextMenu(self.treeview, SG)
        tk.Button(self.tvRClickMenu).setText("Request Average Price").setCommand(self.requestAverage)
        tk.Button(self.tvRClickMenu).setText("Copy ID").setCommand(self.copyID)
        self.tvRClickMenu.create()

        self.sideBarFrame = tk.Frame(self.contentFrame, SG)

        self.tabContr = tk.Notebook(self.sideBarFrame, SG)
        self.infoFrame = self.tabContr.createNewTab("Item-Info")
        self.estimFrame = self.tabContr.createNewTab("Estim-Price-Info")
        self.otherAucFrame = self.tabContr.createNewTab("Other-Auctions")
        self.settingsFrame = self.tabContr.createNewTab("Settings")
        self.tabContr.placeRelative()
        # item Info
        self.toolTipText = TipText(self.infoFrame, SG, readOnly=True)
        self.toolTipText.placeRelative()
        # estm Price
        self.estmPriceText = tk.Text(self.estimFrame, SG, readOnly=True)
        self.estmPriceText.placeRelative()

        self.infoOpenBtn = tk.Button(self.contentFrame, SG)
        self.infoOpenBtn.setCommand(self.toggleSideBarFrame)

        self.closeSideBarBtn = tk.Button(self.sideBarFrame, SG)
        self.closeSideBarBtn.setCommand(self.closeSideBarFrame)
        self.closeSideBarBtn.setText("X")
        self.closeSideBarBtn.setFg("red")
        self.closeSideBarBtn.placeRelative(stickRight=True, fixWidth=25, fixHeight=25)
        # other auc
        self.otherAucTreeView = tk.TreeView(self.otherAucFrame, SG)
        self.otherAucTreeView.setTableHeaders("Display-Name", "BIN-Price", "Ending-In", "Estimated-Price")
        self.otherAucTreeView.placeRelative()

        # settings
        self.isInstaBuySelect = tk.Checkbutton(self.settingsFrame, SG)
        self.isInstaBuySelect.setText("Use Insta Buy")
        self.isInstaBuySelect.onSelectEvent(self.updateTreeview)
        self.isInstaBuySelect.place(0, 0, 250, 25)

        self.filterAutoRecomb = tk.Checkbutton(self.settingsFrame, SG)
        self.filterAutoRecomb.setSelected()
        self.filterAutoRecomb.setText("Filter Auto Recomb")
        self.filterAutoRecomb.onSelectEvent(self.updateTreeview)
        self.filterAutoRecomb.place(250, 0, 250, 25)

        self.capBuyPrice = tk.TextEntry(self.settingsFrame, SG)
        self.capBuyPrice.setText("Cap Buy-Price:")
        self.capBuyPrice.place(0, 25, 200, 25)

        self.capBuySet = tk.Button(self.settingsFrame, SG)
        self.capBuySet.setText("Set")
        self.capBuySet.setCommand(self.buyCapSet)
        self.capBuySet.place(200, 25, 50, 25)

        self.hideDungeonItems = tk.Checkbutton(self.settingsFrame, SG)
        self.hideDungeonItems.onSelectEvent(self.updateTreeview)
        self.hideDungeonItems.setText("Hide Dungeon Items").setSelected()
        self.hideDungeonItems.place(0, 50, 250, 25)

        self.hideFurnitureItems = tk.Checkbutton(self.settingsFrame, SG)
        self.hideFurnitureItems.onSelectEvent(self.updateTreeview)
        self.hideFurnitureItems.setText("Hide Furniture Items").setSelected()
        self.hideFurnitureItems.place(0, 75, 250, 25)

        self.viewMode = tk.TextDropdownMenu(self.settingsFrame, SG)
        self.viewMode.getDropdownMenu().onSelectEvent(self.updateTreeview)
        self.viewMode.getDropdownMenu().setOptionList([
            "View All",
            "Could be very Cheap"
        ])
        self.viewMode.setValue("View All")
        self.viewMode.setText("View Mode: ")
        self.viewMode.place(250, 25, 250, 25)

        self.updateTVonAPIUpd = tk.Checkbutton(self.settingsFrame, SG)
        self.updateTVonAPIUpd.setSelected()
        self.updateTVonAPIUpd.setText("Update On new Data Recive")
        self.updateTVonAPIUpd.place(250, 50, 250, 25)

        # Blacklist
        self.blacklistFrame = tk.LabelFrame(self.settingsFrame, SG)
        self.blacklistFrame.setText("Blacklist [0]")
        self.blacklistFrame.place(0, 150, 500, 225 + 25)

        self.blacklistList = tk.Listbox(self.blacklistFrame, SG)
        self.blacklistList.place(0, 0, 495, 200)
        self.updateBlacklistBox()

        self.blacklistAdd = tk.Button(self.blacklistFrame, SG)
        self.blacklistAdd.setCommand(self.addSelectedToBlacklist)
        self.blacklistAdd.setText("Add Selected")
        self.blacklistAdd.place(0, 200, 163, 25)

        self.blacklistRem = tk.Button(self.blacklistFrame, SG)
        self.blacklistRem.setCommand(self.removeSelectedFromBlacklist)
        self.blacklistRem.setText("Remove Selected")
        self.blacklistRem.place(163, 200, 163, 25)

        self.blacklistEn = tk.Checkbutton(self.blacklistFrame, SG)
        self.blacklistEn.setText("Enable")
        self.blacklistEn.onSelectEvent(self.updateTreeview)
        self.blacklistEn.setSelected()
        self.blacklistEn.place(163 * 2, 200, 163, 25)
        # Flagged
        self.flaggedFrame = tk.LabelFrame(self.settingsFrame, SG)
        self.flaggedFrame.setText("Flagged-Items [0]")
        self.flaggedFrame.place(0, 150 + 225 + 25, 500, 225 + 25)

        self.flaggedList = tk.Listbox(self.flaggedFrame, SG)
        self.flaggedList.place(0, 0, 495, 200)

        self.flaggedAdd = tk.Button(self.flaggedFrame, SG)
        self.flaggedAdd.setCommand(self.requestSelected)
        self.flaggedAdd.setText("Request Selected")
        self.flaggedAdd.place(0, 200, 163, 25)

        self.flaggedRem = tk.Button(self.flaggedFrame, SG)
        self.flaggedRem.setCommand(self.requestAll)
        self.flaggedRem.setText("Request All")
        self.flaggedRem.place(163, 200, 163, 25)

        self.flaggedAddBkList = tk.Button(self.flaggedFrame, SG)
        self.flaggedAddBkList.setCommand(self.addToBlackListFromFlagged)
        self.flaggedAddBkList.setText("Add To Blacklist")
        self.flaggedAddBkList.place(163 * 2, 200, 163, 25)

        self.closeSideBarFrame()
    def addToBlackListFromFlagged(self):
        sel = self.flaggedList.getSelectedItem()
        if sel is None: return
        if sel in Config.SETTINGS_CONFIG["bin_sniper_blacklist"]:
            return
        self.blacklistEn.setState(False)
        Config.SETTINGS_CONFIG["bin_sniper_blacklist"].append(sel)
        Config.SETTINGS_CONFIG.save()
        self.updateBlacklistBox()
    def requestSelected(self):
        sel = self.flaggedList.getSelectedItem()
        if sel is None: return
        self.requestAverage(itemID=sel, updAfter=False)
    def requestAll(self):
        def run():
            for i, item in enumerate(items):
                while Constants.WAITING_FOR_API_REQUEST:
                    sleep(.5)
                self.flaggedFrame.setText(f"Flagged-Items [{len(BinSniperAnalyzer.FLAGGED_ITEMS)}] ({i + 1}/{len(items)})")
                self.requestAverage(itemID=item, updAfter=False)
            self.master.runTask(self.updateTreeview).start()

        max_ = 25
        items = BinSniperAnalyzer.FLAGGED_ITEMS if len(BinSniperAnalyzer.FLAGGED_ITEMS) <= max_ else BinSniperAnalyzer.FLAGGED_ITEMS[:25]
        Thread(target=run).start()
    def addSelectedToBlacklist(self):
        sel = self.treeview.getSelectedIndex()
        if sel is None: return
        sorter = BinSniperAnalyzer.SORTER[sel]
        id_ = sorter["id"]
        if id_ in Config.SETTINGS_CONFIG["bin_sniper_blacklist"]:
            return
        self.blacklistEn.setState(False)
        Config.SETTINGS_CONFIG["bin_sniper_blacklist"].append(id_)
        Config.SETTINGS_CONFIG.save()
        self.updateBlacklistBox()
    def removeSelectedFromBlacklist(self):
        sel = self.blacklistList.getSelectedItem()
        if sel is None: return
        self.blacklistEn.setState(False)
        if sel not in Config.SETTINGS_CONFIG["bin_sniper_blacklist"]:
            return
        self.blacklistEn.setState(False)
        Config.SETTINGS_CONFIG["bin_sniper_blacklist"].remove(sel)
        self.blacklistFrame.setText(f"Blacklist [{len(Config.SETTINGS_CONFIG['bin_sniper_blacklist'])}]")
        Config.SETTINGS_CONFIG.save()
        self.updateBlacklistBox()
    def updateBlacklistBox(self):
        self.blacklistList.clear()
        self.blacklistFrame.setText(f"Blacklist [{len(Config.SETTINGS_CONFIG['bin_sniper_blacklist'])}]")
        self.blacklistList.addAll(Config.SETTINGS_CONFIG["bin_sniper_blacklist"])
    def buyCapSet(self):
        self.buyCap = None
        value = self.capBuyPrice.getValue()
        if value == "": return
        price = parsePriceFromStr(value)
        if price is None: return
        self.buyCap = price
        self.updateTreeview()
    def toggleSideBarFrame(self):
        self.isSideBarOpen = not self.isSideBarOpen
        if not self.isSideBarOpen:
            self.closeSideBarFrame()
            return
        self.openSideBarFrame()
    def openSideBarFrame(self):
        self.sideBarFrame.placeRelative(fixWidth=500, stickRight=True)
        self.infoOpenBtn.setText(">")
        self.infoOpenBtn.placeRelative(stickRight=True, fixHeight=50, fixWidth=25, changeX=-500, centerY=True)

        if not self.isLoading:
            self.loadingFrame.placeForget()
            self.treeview.placeRelative(changeWidth=-500)
        else:
            self.treeview.placeForget()
            self.loadingFrame.placeRelative(changeWidth=-500)
    def closeSideBarFrame(self):
        self.sideBarFrame.placeForget()
        self.infoOpenBtn.setText("<")
        self.infoOpenBtn.placeRelative(stickRight=True, fixHeight=50, fixWidth=25, centerY=True)
        if not self.isLoading:
            self.loadingFrame.placeForget()
            self.treeview.placeRelative()
        else:
            self.treeview.placeForget()
            self.loadingFrame.placeRelative()
    def requestAverage(self, e: tk.Event = None, itemID=None, updAfter=True):
        def request():
            try:
                MsgText.info(f"request average Price from {itemID}...")
                historyData = SkyConflnetAPI.getAuctionHistoryWeek(id_)._data
                Constants.WAITING_FOR_API_REQUEST = False
            except APIConnectionError as e:
                throwAPIConnectionException(
                    source="SkyCoflnet",
                    master=self.master,
                    event=e
                )
                Constants.WAITING_FOR_API_REQUEST = False
                return None
            except NoAPIKeySetException as e:
                throwNoAPIKeyException(
                    source="SkyCoflnet",
                    master=self.master,
                    event=e
                )
                Constants.WAITING_FOR_API_REQUEST = False
                return None
            except APITimeoutException as e:
                throwAPITimeoutException(
                    source="SkyCoflnet",
                    master=self.master,
                    event=e
                )
                Constants.WAITING_FOR_API_REQUEST = False
                return None
            temp = []
            for entry in historyData:
                temp.append(entry["min"])
            temp.sort()
            if not temp:
                MsgText.error(f"Could not request {itemID}! invalid Data!")
                return
            ConfigFile.AVERAGE_PRICE[id_] = getMedianFromList(temp)
            if updAfter: self.master.runTask(self.updateTreeview).start()
            self.master.runTask(self.saveAverage).start()

        if not Constants.WAITING_FOR_API_REQUEST:
            if itemID is None:
                selected = self.treeview.getSelectedIndex()
                if selected is None: return
                id_ = BinSniperAnalyzer.SORTER[selected]["clazz"].getID()
            else:
                id_ = itemID
            Constants.WAITING_FOR_API_REQUEST = True
            Thread(target=request).start()

    def copyID(self):
        selected = self.treeview.getSelectedIndex()
        if selected is None: return
        id_ = BinSniperAnalyzer.SORTER[selected]["clazz"].getUUID()
        import os
        os.system(f"wl-copy {id_}")

    def saveAverage(self):
        ConfigFile.AVERAGE_PRICE.saveConfig()
    def showLoadingFrame(self, len_):
        self.isLoading = True
        self.loadingBar.setValues(len_)
        self.loadingBar.setValue(0)
        if self.isSideBarOpen:
            self.openSideBarFrame()
            return
        self.closeSideBarFrame()
    def hideLoadingFrame(self):
        self.isLoading = False
        self.loadingFrame.placeForget()
        if self.isSideBarOpen:
            self.openSideBarFrame()
            return
        self.closeSideBarFrame()
    # update Treeview
    def updateTreeview(self, e=None, onlyPage=None):
        timer = time()
        TEMP_AUTORECOMB_IDS = []
        barCounter = 0
        tempIDs = []
        self.otherAucTreeView.clear()
        self.toolTipText.clear()
        self.estmPriceText.clear()
        self.treeview.clear()
        BinSniperAnalyzer.FLAGGED_ITEMS = []
        if API.SKYBLOCK_AUCTION_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        recombPrice = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("RECOMBOBULATOR_3000")
        if recombPrice is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! Recomb-Price is None")
            return
        isOrder = not self.isInstaBuySelect.getState()
        hideAutoRecomb = self.filterAutoRecomb.getState()
        isBlacklist = self.blacklistEn.getState()
        isHideDungeonItems = self.hideDungeonItems.getState()
        isHideFurnitureItems = self.hideFurnitureItems.getState()
        if isOrder: recombPrice = recombPrice.getInstaSellPrice()
        else: recombPrice = recombPrice.getInstaBuyPrice()
        recombPrice = applyBazaarTax(recombPrice)

        def filterType(itemID:str, auctAmount:int)->bool:
            nonlocal barCounter
            barCounter += 1
            if barCounter % 10 == 0:
                barCounter = 0
                self.loadingBar.addValue()
                self.master.update()
            if auctAmount < 5: return False
            if isBlacklist and itemID in Config.SETTINGS_CONFIG["bin_sniper_blacklist"]: return False
            if isHideDungeonItems and itemID in DUNGEON_ITEMS: return False
            if isHideFurnitureItems and itemID in FURNITURE_ITEMS: return False
            return True
        def filterPrice(price:float, estim:float, lBin:float, itemID:str, uuid:str)->bool:
            if self.buyCap is not None and price > self.buyCap: return False
            if estim - price < 0: return False
            if hideAutoRecomb and abs((estim - lBin) - recombPrice) < 500 and itemID in AUTO_RECOMBED_ITEMS:
                return False
            return True

        if onlyPage is None:
            self.showLoadingFrame(
                len(API.SKYBLOCK_AUCTION_API_PARSER.getBinTypeAndAuctions()[0]) // 10
            )
            BinSniperAnalyzer.updateSniper(
                sortKey=self.sortKey,
                isOrder=isOrder,
                filterType=filterType,
                filterPrice=filterPrice,
            )
        else:
            self.showLoadingFrame(
                len(API.SKYBLOCK_AUCTION_API_PARSER.getPageByID(onlyPage)._binAucts) // 10
            )
            BinSniperAnalyzer.updateSniperPage(
                page=onlyPage,
                sortKey=self.sortKey,
                isOrder=isOrder,
                filterType=filterType,
                filterPrice=filterPrice,
            )
        
        if self.sortDirec: BinSniperAnalyzer.SORTER.reverse()
        self.flaggedFrame.setText(f"Flagged-Items [{len(BinSniperAnalyzer.FLAGGED_ITEMS)}]")
        self.flaggedList.clear()
        self.flaggedList.addAll(BinSniperAnalyzer.FLAGGED_ITEMS)

        def getTags(sorter):
            temp = []

            if sorter["clazz"].getUUID() in TEMP_AUTORECOMB_IDS:
                return ["recomb"]

            if sorter["clazz"].getUUID() not in self.displayedIds and self.displayedIds:
                temp.append("new_id")
            return tuple(temp)
        for sorter in BinSniperAnalyzer.SORTER[:200]:
            tempIDs.append(sorter["clazz"].getUUID())
            self.treeview.addEntry(
                sorter["clazz"].getDisplayName(),
                sorter["auctions"],
                parsePrizeToStr(sorter["price"]),
                parsePrizeToStr(sorter["estim"]),
                parsePrizeToStr(sorter["diff"], forceSign=True),
                str(sorter["diffPerc"]) + "%",
                tag=getTags(sorter)
            )
        self.hideLoadingFrame()
        self.treeview.setBgColorByTag("new_id", tk.Color.rgb(52, 125, 128))
        self.treeview.setBgColorByTag("recomb", tk.Color.rgb(255, 125, 128))
        self.displayedIds = tempIDs
        MsgText.info(f"Updating Treeview took {round(time()-timer, 2)}s!")

    # events
    def onDoubleSelectEvent(self):
        if not self.isSideBarOpen:
            self.isSideBarOpen = True
            self.openSideBarFrame()
        self.tabContr.getTabByName("Other-Auctions").setSelected()
    def onSelectEvent(self, e: tk.Event):
        self.otherAucTreeView.clear()
        sel = self.treeview.getSelectedIndex()
        if sel is None: return
        sorter = BinSniperAnalyzer.SORTER[sel]
        self.toolTipText.clear()
        fillToolTipText(self.toolTipText, sorter["clazz"])
        self.estmPriceText.clear()
        self.estmPriceText.addText(sorter["desc"])

        lowestBin = sorter["lowestBin"]
        binAuctions = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(sorter["id"])

        sorters = []
        for auct in binAuctions:
            estimatedPrice, desc, data = calculateEstimatedItemValue(auct, not self.isInstaBuySelect.getState(),
                                                                     lowestBin)
            estimatedPriceDiff = "Could not be calculated!"
            if estimatedPrice is not None:
                estimatedPriceDiff = estimatedPrice - auct.getPrice()
            sorters.append(
                Sorter(
                    sortKey="bin_price",

                    display_name=auct.getDisplayName(),
                    bin_price=auct.getPrice(),
                    ending_in=parseTimeDelta(auct.getEndIn()).toSeconds(),
                    auctClass=auct,
                    estimated_price=estimatedPrice,
                    estimated_price_diff=estimatedPriceDiff,
                    uuid=auct.getUUID(),
                )
            )

        sorters.sort()

        for auct in sorters:

            tags = [auct["auctClass"].getRarity()]
            if auct["uuid"] == sorter["clazz"].getUUID():
                tags.append("this")

            self.otherAucTreeView.addEntry(
                auct["display_name"],
                parsePrizeToStr(auct["bin_price"]),
                "ENDED" if auct["ending_in"] <= 0 else parseTimeFromSec(auct["ending_in"]),
                parsePrizeToStr(auct["estimated_price_diff"], forceSign=True),
                tag=tuple(tags),
            )
        for k, v in iterDict(RARITY_COLOR_CODE):
            self.otherAucTreeView.setFgColorByTag(k, v)
        self.otherAucTreeView.setBgColorByTag("this", "green")
    def onHeaderSelectEvent(self, e):
        value = e.getValue()
        newSortKey = self.sortKey
        if value == newSortKey:
            self.sortDirec = not self.sortDirec
            self.updateTreeview()
            return
        if value == "Auctions":
            newSortKey = "auctions"
        elif value == "Price":
            newSortKey = "price"
        elif value == "Estim-Price":
            newSortKey = "estim"
        elif value == "Diff":
            newSortKey = "diff"
        elif value == "Diff-%":
            newSortKey = "diffPerc"
        if newSortKey != self.sortKey:
            self.sortKey = newSortKey
            self.updateTreeview()
    def onAPIUpdate(self):
        if self.updateTVonAPIUpd.getState():
            self.updateTreeview(onlyPage=self.master.requestedOnlyPage)
    def onShow(self, **kwargs):
        self.placeRelative()
        self.placeContentFrame()
        self.master.updateCurrentPageHook = self.onAPIUpdate
        if not BinSniperAnalyzer.SORTER:
            self.updateTreeview()
