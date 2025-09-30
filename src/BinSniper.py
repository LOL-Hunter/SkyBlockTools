from threading import Thread
from time import sleep, time
from typing import List, Tuple

import tksimple as tk
from core.constants import (
    STYLE_GROUP as SG,
    CUSTOM_PET_XP_MAX,
    PET_XP_MAX,
    ConfigFile,
    Constants,
    NPC_BUYABLE_PET_ITEMS,
    RARITY_COLOR_CODE,
    API,
    DUNGEON_ITEMS,
    FURNITURE_ITEMS
)
from core.hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException
from core.hyPI.skyCoflnetAPI import SkyConflnetAPI
from core.logger import MsgText
from core.settings import Config
from core.skyMath import parseTimeDelta, getMedianFromList
from core.skyMisc import (
    _map,
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

class BinSniperPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Bin-Sniper", buttonText="Bin Sniper")
        self.sorters = None
        self.buyCap = None
        self.displayedIds = []
        self.isSideBarOpen = False
        self.analyzedPetsSet = set()
        self.flaggedLbinItems = []
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
                self.flaggedFrame.setText(f"Flagged-Items [{len(self.flaggedLbinItems)}] ({i + 1}/{len(items)})")
                self.requestAverage(itemID=item, updAfter=False)
            self.master.runTask(self.updateTreeview).start()

        max_ = 25
        items = self.flaggedLbinItems if len(self.flaggedLbinItems) <= max_ else self.flaggedLbinItems[:25]
        Thread(target=run).start()
    def addSelectedToBlacklist(self):
        sel = self.treeview.getSelectedIndex()
        if sel is None: return
        sorter = self.sorters[sel]
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
    def analyzePets(self, id_:str, force:bool = False, petItemsCache:dict = None) -> List[Sorter]:
        if petItemsCache is None: petItemsCache = {}

        def getPetItemPrice(itemID: str | None) -> float:
            if itemID is None: return 0
            if itemID in petItemsCache.keys():
                return petItemsCache[itemID]
            if itemID in NPC_BUYABLE_PET_ITEMS:
                return NPC_BUYABLE_PET_ITEMS[itemID]
            lbin = getLBin(itemID)
            if lbin is None:
                # MsgText.warning(f"Could not get PetItem price {itemID}. Using Zero.")
                return 0
            price = lbin.getPrice()
            petItemsCache[itemID] = price
            return price

        def capPetXP(xp: float, itemID: str, rarity: str) -> float:
            if itemID in CUSTOM_PET_XP_MAX.keys():
                maxXP = CUSTOM_PET_XP_MAX[itemID]
            else:
                maxXP = PET_XP_MAX[rarity]
            if xp < maxXP:
                return xp
            return maxXP

        if id_ in self.analyzedPetsSet and not force:
            return []
        self.analyzedPetsSet.add(id_)

        rarityToPetMap = {}
        for auction in API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(id_):
            rarity = auction.getPetRarity()
            if rarity not in rarityToPetMap.keys():
                rarityToPetMap[rarity] = []
            rarityToPetMap[rarity].append(
                Sorter(
                    sortKey="pet_lvl",

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
    def getCustomLbinPrice(self, itemID: str, isOrder: bool) -> Tuple[BINAuctionProduct, float] | Tuple[None, None]:
        # get average from file if available
        if itemID in ConfigFile.AVERAGE_PRICE.keys():
            return None, ConfigFile.AVERAGE_PRICE[itemID]

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
            self.flaggedLbinItems.append(itemID)
            return None, None

        return lBinList[-1]["auctClass"], lowestBin1
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
                id_ = self.sorters[selected]["clazz"].getID()
            else:
                id_ = itemID
            Constants.WAITING_FOR_API_REQUEST = True
            Thread(target=request).start()
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
    def updateTreeview(self):
        timer = time()
        petTime = 0
        tempIDs = []
        self.otherAucTreeView.clear()
        self.toolTipText.clear()
        self.estmPriceText.clear()
        self.treeview.clear()
        self.flaggedLbinItems = []
        petItemCache = {}
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
        hideAutoRecomb = not self.filterAutoRecomb.getState()
        isBlacklist = self.blacklistEn.getState()
        isHideDungeonItems = self.hideDungeonItems.getState()
        isHideFurnitureItems = self.hideFurnitureItems.getState()
        if isOrder:
            recombPrice = recombPrice.getInstaSellPrice()
        else:
            recombPrice = recombPrice.getInstaBuyPrice()

        sorters = []
        typeAndAuc = API.SKYBLOCK_AUCTION_API_PARSER.getBinTypeAndAuctions()
        self.showLoadingFrame(len(typeAndAuc[0]))
        for id_, aucts in zip(*typeAndAuc):
            self.loadingBar.addValue()
            self.master.update()
            if len(aucts) < 5: continue

            if isBlacklist and id_ in Config.SETTINGS_CONFIG["bin_sniper_blacklist"]: continue

            lbin, lbinPrice = self.getCustomLbinPrice(id_, isOrder)
            if lbinPrice is None: continue
            for auction in aucts:
                if auction.isPet():
                    _petTimer = time()
                    sorters.extend(self.analyzePets(auction.getID(), False, petItemCache))  # add force later
                    petTime += (time() - _petTimer)
                    continue

                estimPrice, desc, data = calculateEstimatedItemValue(auction, isOrder, lbinPrice)
                price = auction.getPrice()
                if estimPrice is None:
                    MsgText.warning(f"Estim Price for {auction.getID()} is None[{desc}]. Skip, {type(lbin)}")
                    continue
                if estimPrice - price < 0: continue

                if self.buyCap is not None and price > self.buyCap: continue

                autoRecomb = "auto_recombed" in data.keys()
                if autoRecomb and price + recombPrice + 200_000 < estimPrice:
                    autoRecomb = False
                if autoRecomb and hideAutoRecomb:
                    continue
                if isHideDungeonItems and auction.getID() in DUNGEON_ITEMS: continue
                if isHideFurnitureItems and auction.getID() in FURNITURE_ITEMS: continue
                sorters.append(
                    Sorter(
                        sortKey=self.sortKey,

                        lowestBin=lbinPrice,
                        desc=desc,
                        id=auction.getID(),
                        estim=estimPrice,
                        price=price,
                        diff=estimPrice - price,
                        diffPerc=round((estimPrice / price) * 100, 1),
                        clazz=auction,
                        auctions=len(aucts),

                        autoRecombed=autoRecomb
                    )
                )
            self.loadingBar.addValue()
            self.master.update()
        sorters.sort()
        if self.sortDirec:
            sorters.reverse()
        self.sorters = sorters
        self.flaggedFrame.setText(f"Flagged-Items [{len(self.flaggedLbinItems)}]")
        self.flaggedList.clear()
        self.flaggedList.addAll(self.flaggedLbinItems)

        def getTags(sorter):
            temp = []
            if sorter["clazz"].getUUID() not in self.displayedIds and self.displayedIds:
                temp.append("new_id")
            return tuple(temp)

        for sorter in sorters:
            tempIDs.append(sorter["clazz"].getUUID())
            self.treeview.addEntry(
                sorter["clazz"].getDisplayName(),
                sorter["auctions"],
                parsePrizeToStr(sorter["price"]),
                parsePrizeToStr(sorter["estim"]),
                parsePrizeToStr(sorter["diff"], forceSign=True),
                str(sorter["diffPerc"]) + " %",
                tag=getTags(sorter)
            )
        self.hideLoadingFrame()
        self.treeview.setBgColorByTag("new_id", tk.Color.rgb(52, 125, 128))
        self.displayedIds = tempIDs
        MsgText.info(f"Updating Treeview took {round(time()-timer, 2)}s!")
        MsgText.info(f"\t-Pets took {round(petTime, 2)}s!")
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
        sorter = self.sorters[sel]
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
            self.updateTreeview()
    def onShow(self, **kwargs):
        self.placeRelative()
        self.placeContentFrame()
        self.master.updateCurrentPageHook = self.onAPIUpdate
        self.updateTreeview()