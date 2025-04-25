from typing import List, Dict, Tuple, Any
from pysettings import iterDict

from hyPI.constants import Config, Category, MODIFIER, _RUNE_CONVERT, ROMIC_NUMBERS
from hyPI.APIError import YearNotAvailableInData
from datetime import datetime as dt, timedelta
from pytz import timezone

def getHypTimezone(tz)->dt:
    unixTime = tz/1000
    time_zone = timezone(Config.TARGET_TIME_ZONE)
    time = dt.fromtimestamp(unixTime)
    return time_zone.localize(time) + timedelta(hours=2)

def getTimezone(tz:str)->dt | None:
    if tz is None: return None
    time_zone = timezone(Config.TARGET_TIME_ZONE)
    if len(tz.split(".")[-1]) < 3: tz = tz+"0"
    if len(tz.split(".")[-1]) < 3: tz = tz+"0"
    if tz.endswith("Z"): # Z -> Zero
        tz = tz[:-1] + ".000"
    time = dt.fromisoformat(tz)
    return time_zone.localize(time) + timedelta(hours=2)

def convertAuctionNameToID(data:dict, itemParser, auctionIDs:[str])->dict:
    displayName = name = data["item_name"]
    categories = data["categories"]
    name = name.upper().replace(" ", "_")
    level = 0
    potion_level = 0
    reforge = None
    reforgeStone = None

    masterStar = -1
    stars = name.count("\u272a")
    name = name.replace("\u272a", "") # star

    for i, ms in enumerate(["\u278a", "\u278b", "\u278c", "\u278d", "\u278e"]): # master stars
        if ms in name: masterStar = i+1
        name = name.replace(ms, "")

    isUpgraded = name.startswith("\u269a") # upgraded symbol
    name = name.replace("\u269a", "")

    name = name.replace("\u2726", "") # weird star symbol
    name = name.replace("\u273f", "") # weird flower symbol
    #name = name.replace("\u2122", "") # weird tm symbol
    name = name.replace("\xa9", "")   # weird copyright symbol
    name = name.replace("\u0f15", "") # weird century cake symbol
    name = name.replace("\xae", "")   # weird registered symbol

    name = name.replace("\u25c6", "") # rune
    name = name.strip("_")

    #remove wooden singularity
    woodenSingUsed = False
    if "THICK" in name:
        name = name.replace("THICK", "").replace("__", "_")
        woodenSingUsed = True
    name = name.strip("_")
    #remove shiny
    shiny=False
    if "SHINY" in name and ("armor" in categories or "weapon" in categories):
        name = name.replace("SHINY", "").replace("__", "_")
        shiny = True
    #handle pet
    if name.startswith("["): # pet
        levelPart, *name = name.split("]")
        level = levelPart.split("_")[1]
        name = "PET_"+name[-1].strip("_")
    # handle rune
    runeLvl = 0
    if "RUNE" in name and not name == "RUNEBOOK":
        *runeID, _, lvl = name.strip().split("_")
        runeID = "_".join(runeID)
        name = f"RUNE_{runeID.upper()}"
        if name in _RUNE_CONVERT.keys():
            name = _RUNE_CONVERT[name]  # convert to custom name
        runeLvl = ROMIC_NUMBERS[lvl]
    # handle potions
    if name.endswith("POTION") and "GOD" not in name and "RECALL" not in name and name != "AWKWARD_POTION":
        name = name.replace("SPLASH_POTION", "POTION")
        *nameStuff, lvl, potion = name.split("_")
        potion_level = ROMIC_NUMBERS[lvl]
    if name == "TASTY_CAT_FOOD":
        name = "DEAD_CAT_FOOD"
    if name.endswith("REPELLING_CANDLE"):
        name = "REPELLING_CANDLE"

    name = name.strip("_")

    if not level: # no pet
        id_ = itemParser.getItemByName(displayName)
        if id_ is None: # not in hypixel-item-data
            if name in auctionIDs or name.startswith("PET_"): # in Auction IDs
                id_ = name
            elif "SKIN" in name:
                id_ = "SKIN"
            elif "NEW_YEAR_CAKE" in name:
                id_ = "NEW_YEAR_CAKE"
            elif name.startswith("GREATER_SPOOK"):
                id_ = "GREAT"+"_".join(name.split("_")[1:])
                reforgeStone = "BOO_STONE"
            elif "HAT_OF_CELEBRATION" in name:
                id_ = "HAT_OF_CELEBRATION"
            elif "ABICASE" in name:
                id_ = "ABICASE"
            elif name.endswith("POTION"):
                id_ = "POTION"
            else:
                if name.startswith("GREEN_THUMB"): # special
                    reforge = "GREEN_THUMB"
                    reforgeStone = "BLACKSMITH"
                    name = name.replace("GREEN_THUMB", "").strip("_")
                elif name.startswith("NOT_SO"):
                    reforge = "LIGHT"
                    reforgeStone = "BLACKSMITH"
                    name = name.replace("NOT_SO", "").strip("_")
                elif name.startswith("EVEN_MORE"):
                    reforge = "REFINED"
                    reforgeStone = "BLACKSMITH"
                    name = name.replace("EVEN_MORE", "").strip("_")
                else:
                    # remove reforge
                    reforge = None
                    reforgeStone = None
                    _reforge = name.split("_")[0]
                    if _reforge.upper() in MODIFIER.keys() and "RUNE" not in name:
                        reforge = _reforge.upper()
                        reforgeStone = MODIFIER[reforge]
                        name = "_".join(name.split("_")[1:])
                    name = name.strip("_")
                id_ = itemParser.getItemByName(name)
                if id_ is None:  # not in hypixel-item-data
                    if name in auctionIDs or name.startswith("PET_"):  # in Auction IDs
                        id_ = name
                else:
                    id_ = id_.getID()
        else:
            id_ = id_.getID()
    else:
        id_ = name # pet

    return {
        "id":id_,
        "name":displayName,
        "potion_level":potion_level,
        "stars":stars,
        "master_star":masterStar,
        "pet_level":level,
        "isUpgraded":isUpgraded,
        "reforge":reforge,
        "rune_level":runeLvl,
        "upgrade_stone":reforgeStone,
        "wooden_singularity_used":woodenSingUsed,
        "shiny":shiny,
    }


#sky coflnet
class BazaarHistoryProduct:
    def __init__(self, data):
        self._data = data
        if not isinstance(data, dict):
            print(ascii(data))
            self._data = {}

    def getMaxBuyPrice(self): return self._data.get("maxBuy", None)
    def getMinBuyPrice(self): return self._data.get("minBuy", None)
    def getMaxSellPrice(self): return self._data.get("maxSell", None)
    def getMinSellPrice(self): return self._data.get("minSell", None)

    def getBuyPrice(self): return self._data.get("buy", None)
    def getSellPrice(self): return self._data.get("sell", None)

    def getSellVolume(self): return self._data.get("sellVolume", None)
    def getBuyVolume(self): return self._data.get("buyVolume", None)

    def getBuyMovingWeek(self): return self._data.get("buyMovingWeek", None)
    def getSellMovingWeek(self): return self._data.get("sellMovingWeek", None)

    def getTimestamp(self)->dt: return getTimezone(self._data.get("timestamp", None))
class BazaarProduct:
    def __init__(self, data):
        self._data = data
    def getBuyPrice(self): return self._data["buy"]
    def getSellPrice(self): return self._data["sell"]
    def getAvailableItems(self): return self._data["available"]
    def getTimestamp(self)->dt: return getTimezone(self._data["updatedAt"])
class BazaarHistory:
    def __init__(self, data, range_):
        #if isinstance(data, Error):

        self._range = range_
        self._data = data
        self._slots = self._parseTimeSlots(data)

    def __getitem__(self, item):
        return self._slots[item]

    def _parseTimeSlots(self, l:list)->List[BazaarHistoryProduct]:
        return [BazaarHistoryProduct(i) for i in l]

    def getTimeSlots(self)->List[BazaarHistoryProduct]:
        return self._slots

    def getTimeSlotAT(self, tstamp)->BazaarHistoryProduct:
        pass
class AuctionHistoryProduct:
    def __init__(self, data):
        self._data = data
    def getMinPrice(self): return self._data["min"]
    def getMaxPrice(self): return self._data["max"]
    def getAveragePrice(self): return self._data["avg"]
    def getVolume(self): return self._data["volume"]
    def getTimestamp(self)->dt: return getTimezone(self._data["time"])
class AuctionHistory:
    def __init__(self, data, range_):
        self._data = data
        self._range = range_
        self._slots = self._parseTimeSlots(data)

    def __getitem__(self, item):
        return self._slots[item]

    def _parseTimeSlots(self, l:list)->List[AuctionHistoryProduct]:
        return [AuctionHistoryProduct(i) for i in l]

    def getTimeSlots(self) -> List[AuctionHistoryProduct]:
        return self._slots

    def getTimeSlotAT(self, tstamp)->BazaarHistoryProduct:
        pass
class AuctionProduct:
    def __init__(self, data):
        self._data = data
    def getBuyPrice(self): return self._data["buy"]
    def getSellPrice(self): return self._data["sell"]
    def getAvailableItems(self): return self._data["available"]
    def getTimestamp(self)->dt: return getTimezone(self._data["updatedAt"])

class MayorPerk:
    def __init__(self, data):
        self._data = data
    def getDescription(self):
        return self._data["description"]
    def getPerkName(self):
        return self._data["name"]
class Mayor:
    def __init__(self, data):
        self._data = data
        self._majorPerks = [MayorPerk(i) for i in data["perks"]]
    def getName(self):
        return self._data["name"]
    def getKey(self):
        return self._data["key"]
    def getPerks(self)->List[MayorPerk]:
        return self._majorPerks
class MayorData:
    def __init__(self, data):
        self._data = data
        self._majorPerks = [MayorPerk(i) for i in data["winner"]["perks"]]
        self._electionCandidates = [Mayor(i) for i in data["candidates"]]
    def getName(self)->str:
        return self._data["winner"]["name"]
    def getKey(self)->str:
        return self._data["winner"]["key"]
    def getPerks(self)->List[MayorPerk]:
        return self._majorPerks
    def getPerkAmount(self)->int:
        return len(self._majorPerks)
    def getYear(self)->int:
        return self._data["year"]
    def getStartTimestamp(self)->dt:
        return getTimezone(self._data["start"])
    def getEndTimestamp(self)->dt:
        return getTimezone(self._data["end"])
    def getID(self)->str:
        return self._data["id"]
    def getElectionCandidates(self)->List[Mayor]:
        return self._electionCandidates

    @staticmethod
    def fromData(i):
        if "winner" not in i.keys():
            #print("\n*\n*\n", ascii(i))
            return None


        if "perks" in i["winner"].keys():
            return MayorData(i)
        return None

class MayorHistory:
    def __init__(self, data):
        self._data = data[1:] # first data is corrupted (-> ~2019)
        #print(ascii(self._data))
        self._mayorYear = {}
        self._mayors = self._parse(self._data)

    def _parse(self, data):
        d = []
        for i in data:
            if "candidates" in i.keys():
                mdata = MayorData.fromData(i)
                if mdata is None: continue
                d.append(mdata)
                self._mayorYear[mdata.getYear()] = mdata
        return d

    def getCurrentMayor(self)->MayorData:
        return MayorData(self._data[-1])

    def getMayors(self)->List[MayorData]:
        return self._mayors

    def getMayorAtYear(self, year: int):
        if year in self._mayorYear.keys():
            return self._mayorYear[year]
        else:
            raise YearNotAvailableInData(year)

class Recipe:
    """
    A1 A2 A3
    B1 B2 B3
    C1 C2 C3
    """
    def __init__(self, data:dict, ID):
        self._data = data

        if ":" in ID:
            self.ID = ID.split(":")[0]
        else:
            self.ID = ID

        self.count = 1
        if "recipe" in self._data.keys():
            pattern = self._data["recipe"].copy()
            self.pattern = self._parsePattern(pattern)
        else:
            self.pattern = None

    def _parsePattern(self, data)-> dict[str, dict[str, int | Any] | dict[str, int | None]]:
        d = {}
        for k, v in iterDict(data):
            if k == "count":
                self.count = v
                continue
            if v != "":
                item, amount = v.split(":")
                d[k] = {"name":item, "amount":int(amount)}
            else:
                d[k] = {"name":None, "amount":int(0)}
        return d
    def getResultAmount(self):
        raise self.count
    def getPattern(self)->Dict[str, Tuple[str, int]]:
        return self.pattern
    def getItemInputList(self):
        if self.pattern is None: return None
        out = []
        p = {}
        for ind in self.getPattern().values():
            if ind["name"] is not None:
                if ind["name"] in p.keys():
                    p[ind["name"]] += ind["amount"]
                else:
                    p[ind["name"]] = ind["amount"]
        for k, v in iterDict(p):
            out.append({"name":k, "amount":v})
        return out

    def getBaseRarity(self):
        return self._data.get("base_rarity", None)
    def getDisplayName(self):
        return self._data.get("name", None)
    def getID(self):
        return self.ID
    def getWikiUrl(self):
        return self._data.get("wiki", None)

# hypixel
class Order:
    def __init__(self, data):
        self._data = data
    def getAmount(self)->int:
        return self._data["amount"]
    def getPricePerUnit(self)->float:
        return self._data["pricePerUnit"]
    def getOrders(self)->int:
        return self._data["orders"]
class Product:
    def __init__(self, id_, data):
        self._id = id_
        self._data = data
    def getID(self)->str:
        return self._id
    def getBuyVolume(self)->int:
        """
        How many buy orders are set.
        @return:
        """
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["buyVolume"]
    def getInstaBuyPrice(self)->float:
        return None
    def getWeightedBuyPrice(self)->float:
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["buyPrice"]
    def getBuyOrdersTotal(self)->int:
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["buyOrders"]
    def getSellVolume(self) -> int:
        """
        How many can I sell?
        """
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["sellVolume"]
    def getInstaSellPrice(self) -> float:
        return None
    def getWeightedSellPrice(self) -> float:
        #the weighted average of the top 2% of orders by volume.
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["sellPrice"]
    def getSellOrdersTotal(self) -> int:
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["sellOrders"]
    def getInstaBuyWeek(self) -> int:
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["buyMovingWeek"]
    def getInstaSellWeek(self) -> int:
        if "quick_status" in self._data.keys(): return self._data["quick_status"]["sellMovingWeek"]
class ProductWithOrders(Product):
    def __init__(self, id_, data):
        super().__init__(id_, data)
        self._sellOrders = self._parseOrders(self._data["sell_summary"])
        self._buyOrders = self._parseOrders(self._data["buy_summary"])
    def _parseOrders(self, l:list)->List[Order]:
        return [Order(i) for i in l]
    def getSellOrders(self)->List[Order]:
        return self._sellOrders#[::-1]
    def getBuyOrders(self)->List[Order]:
        return self._buyOrders#[::-1]
    def getInstaSellPrice(self) -> float:
        price = self.getInstaSellPriceList(1)
        if len(price):
            return price[0]
        return 0
    def getInstaBuyPrice(self)->float:
        price = self.getInstaBuyPriceList(1)
        if len(price):
            return price[0]
        return 0
    def getInstaSellPriceList(self, i:int)->List[float]:
        sellOffers = self.getSellOrders() # get who wants to sell the Items.
        remaining = i
        _list = []
        for offer in sellOffers:
            price = offer.getPricePerUnit()
            offers = offer.getAmount()
            if remaining > offers:
                _list.extend([price] * offers)
                remaining -= offers
            else: # remaining < offers
                _list.extend([price] * remaining)
                break
        return _list
    def getInstaBuyPriceList(self, i:int)->List[float]:
        buyOffers = self.getBuyOrders()
        remaining = i
        _list = []
        for offer in buyOffers:
            price = offer.getPricePerUnit()
            offers = offer.getAmount()
            if remaining > offers:
                _list.extend([price] * offers)
                remaining -= offers
            else:  # remaining < offers
                _list.extend([price] * remaining)
                break
        return _list
class AuctionBid:
    def __init__(self, data):
        self._data = data
    def getPrice(self):
        return self._data["amount"]
class BaseAuctionProduct:
    def __init__(self, auctData:dict, itemData:dict):
        self._itemData = itemData
        self._auctData = auctData
    def getCreatorUUID(self):
        return self._auctData["auctioneer"]
    def getID(self)->str:
        return self._itemData["id"]
    def getDisplayName(self)->str:
        return self._itemData["name"]
    def getAuctionID(self)->str:
        return self._auctData["uuid"]
    def getStartedAt(self)->dt:
        return getHypTimezone(self._auctData["start"])
    def getEndAt(self)->dt:
        return getHypTimezone(self._auctData["end"])
    def getEndIn(self)->timedelta:
        now = timezone(Config.TARGET_TIME_ZONE).localize(dt.now())
        return self.getEndAt() - now
    def getItemCategory(self)->str:
        return self._auctData["category"].upper()
    def isCategory(self, c:Category | str)->bool:
        c = c.value if hasattr(c, "value") else c
        return self.getItemCategory() == c
    def isRune(self)->bool:
        return self._itemData["rune_level"] != 0
    def getRuneLevel(self)->int:
        return self._itemData["rune_level"]
    def isReforged(self)->bool:
        return self._itemData["reforge"] is not None
    def getReforge(self)->str:
        return self._itemData["reforge"]
    def getReforgeStone(self)->str:
        return self._itemData["upgrade_stone"]
    def getRarity(self)->str:
        return self._auctData["tier"]
    def isClaimed(self)->bool:
        return self._auctData["claimed"]
    def getStars(self)->int:
        return self._itemData["stars"]
    def getMasterStar(self)->int:
        return self._itemData["master_star"]
    def isPet(self)->bool:
        return self._itemData["pet_level"] != 0
    def getPetLevel(self)->int:
        return int(self._itemData["pet_level"])
    def isWoodenSingUsed(self)->bool:
        return self._itemData["wooden_singularity_used"]
    def isShiny(self)->bool:
        return self._itemData["shiny"]
    def isRecombobulated(self)->bool:
        raise NotImplemented()

    def getPrice(self)->float:
        pass
    def getHighestBid(self)->float:
        pass
    def getBidAmount(self)->int:
        pass

class BINAuctionProduct(BaseAuctionProduct):
    def __init__(self, auctData:dict, itemData:dict):
        super().__init__(auctData, itemData)
    def __lt__(self, other):
        return self.getPrice() > other.getPrice()
    def getPrice(self):
        return self._auctData["starting_bid"]
class NORAuctionProduct(BaseAuctionProduct):
    def __init__(self, auctData: dict, itemData: dict):
        super().__init__(auctData, itemData)
    def __lt__(self, other):
        return self.getHighestBid() < other.getHighestBid()
    def getHighestBid(self):
        return self._auctData["highest_bid_amount"]
    def getBidAmount(self):
        return len(self._auctData["bids"])
class Item: # Hypixel ItemInstance
    def __init__(self, data:dict):
        self._data = data
    def getDisplayName(self)-> str | None:
        return self._data.get("name", None)
    def getID(self)-> str | None:
        return self._data.get("id", None)
    def getNPCSellPrice(self)->float | None:
        return self._data.get("npc_sell_price", None)
    def getRarity(self)-> str | None:
        return self._data.get("tier", None)
    def getCategory(self)->str | None:
        return self._data.get("category", None)
