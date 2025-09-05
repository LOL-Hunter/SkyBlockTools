from typing import List, Dict, Tuple, Any
from pysettings import iterDict
from pysettings.jsonConfig import JsonConfig
from .constants import Config, Category
from datetime import datetime as dt, timedelta
from pytz import timezone
from base64 import b64decode
from nbt.nbt import NBTFile
from io import BytesIO


# TimeZone calculation
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
def getMayorTimezone(tz:str)->dt | None:
    if tz is None: return None
    time_zone = timezone("Europe/Berlin")
    tz = tz.replace(" +00:00", "")
    time = dt.strptime(tz, "%m/%d/%Y %H:%M:%S")
    return time_zone.localize(time) + timedelta(hours=2)
# id parsing
def convertAuctionNameToID(data:dict)->dict:
    check = lambda id_, def_: extra[id_].value if id_ in extra.keys() else def_
    isPresent = lambda id_: id_ in extra.keys()
    upr = lambda str_: str_.upper() if isinstance(str_, str) else str_

    dataB64 = data["item_bytes"]
    dataGZip = b64decode(dataB64)
    dataNBT = BytesIO(dataGZip)
    nbt = NBTFile(fileobj=dataNBT)["i"][0]

    itemID = str(nbt["tag"]["ExtraAttributes"]["id"])

    extra = nbt["tag"]["ExtraAttributes"]

    line = None
    hook = None
    sinker = None
    if "line" in extra.keys(): line = extra["line"]["part"].value.upper()
    if "hook" in extra.keys(): hook = extra["hook"]["part"].value.upper()
    if "sinker" in extra.keys(): sinker = extra["sinker"]["part"].value.upper()
    level = 0
    exp = 0.0
    rarity = None
    candyUsed = 0
    heldItem = None
    if "petInfo" in extra.keys(): # is Pet
        petData = str(extra["petInfo"])
        petData = JsonConfig.fromString(petData)
        candyUsed = petData["candyUsed"] if "candyUsed" in petData.keys() else None
        heldItem = petData["heldItem"] if "heldItem" in petData.keys() else None
        rarity = petData["tier"]
        exp = petData["exp"]
        itemID = f"PET_{petData['type']}"
        levelPart, *name = data["item_name"].split("]")
        level = levelPart.split(" ")[1]
    enchantments = []
    if "enchantments" in extra.keys():
        for ench in extra["enchantments"]:
            name, value = ench.upper(), extra["enchantments"][ench]
            enchantments.append(f"ENCHANTMENT_{name}_{value}")
    scrolls = []
    if "ability_scroll" in extra.keys():
        for i in extra["ability_scroll"]:
            scrolls.append(i.value)
    unlockedSlots = []
    appliedGemstones = []
    if "gems" in extra.keys():
        gemData = extra["gems"]
        if "unlocked_slots" in gemData.keys():
            for slot in gemData["unlocked_slots"]:
                unlockedSlots.append(slot.value)
        temp = {}
        for slot in gemData.keys(): # FINE_JASPER_GEM
            if slot == "unlocked_slots": continue
            fullName, value = gemData[slot].name, gemData[slot].value
            if value is None: continue # slot empty
            if fullName.endswith("_gem"):
                name, id_, _ = fullName.split("_")
                temp[name+"_"+id_] = value
        for slot in gemData.keys():
            if slot == "unlocked_slots": continue
            fullName, value = gemData[slot].name, gemData[slot].value
            if fullName.endswith("_gem"): continue
            if value is None: continue  # slot empty
            name, id_ = fullName.split("_")
            if fullName in temp.keys():
                appliedGemstones.append(f"{value}_{temp[fullName]}_GEM")
                continue
            appliedGemstones.append(f"{value}_{name}_GEM")
    runeType = None
    runeLvl = None
    if "runes" in extra.keys():  # has rune / is rune {TAG_Int('ZOMBIE_SLAYER'): 1}
        _rune = extra["runes"]
        _runeKeys = extra["runes"].keys()
        runeType = _runeKeys[0]
        runeLvl = int(str(_rune[_runeKeys[0]]))

    return {
        "count":nbt["Count"],
        "id": itemID,
        "name": data["item_name"],
        # upgrades
        "recomb": isPresent("rarity_upgrades"),
        "enchantments": enchantments,
        "stars": check("upgrade_level", 0),
        "reforge": upr(check("modifier", None)),
        "wooden_singularity_used": isPresent("wood_singularity_count"),
        "shiny": isPresent("is_shiny"),
        "hot_potato_count": check("hot_potato_count", 0),
        "polarvoid_count": check("polarvoid", 0),
        "farming_for_dummies_count": check("farming_for_dummies_count", 0),
        "tuned_transmission": check("tuned_transmission", 0),
        "etherwarp": isPresent("ethermerge"),
        "mana_disintegrator_count": check("mana_disintegrator_count", 0),
        "is_art_of_peace_applied": isPresent("artOfPeaceApplied"),
        "wet_book_count": check("wet_book_count", 0),
        "bookworm_books": check("bookworm_books", 0),
        "art_of_war_count": check("art_of_war_count", 0),
        "jalapeno_count": check("jalapeno_count", 0),
        "power_ability_scroll": check("power_ability_scroll", None),
        "ability_scroll": scrolls,
        # rune
        "rune_type": runeType,
        "rune_lvl": runeLvl,
        # potion
        "potion_level": check("potion_level", 0),
        # pets
        "pet_level": level,
        "pet_item":heldItem,
        "candy_used":candyUsed,
        "exp":exp,
        "pet_rarity": rarity,
        #stats
        "isStatsBook": isPresent("stats_book"),
        "kills": check("stats_book", 0),
        "sword_kills": check("sword_kills", 0),
        "zombie_kills": check("zombie_kills", 0),
        "eman_kills": check("eman_kills", 0),
        "spider_kills": check("spider_kills", 0),
        "runic_kills": check("runic_kills", 0),
        "expertise_kills": check("expertise_kills", 0),
        "champion_combat_xp": check("champion_combat_xp", 0.0),
        "toxophilite_combat_xp": check("toxophilite_combat_xp", 0.0),
        "collected_coins": check("collected_coins", 0),
        "drill_fuel": check("drill_fuel", 0),
        "compact_blocks": check("compact_blocks", 0),
        "farmed_cultivating": check("farmed_cultivating", 0),
        "mined_crops": check("mined_crops", 0),
        "thunder_charge": check("thunder_charge", 0),
        "logs_cut": check("logs_cut", 0),
        "boss_tier": check("boss_tier", None),
        # fishing
        "line": line,
        "hook": hook,
        "sinker": sinker,
        # talis
        "is_enriched": isPresent("talisman_enrichment"),
        "enrichment": check("talisman_enrichment", None),
        "blood_god_kills": check("blood_god_kills", 0),
        # dungeon
        "dungeon_skill_req": check("dungeon_skill_req", None),
        "hecatomb_s_runs": check("hecatomb_s_runs", None),
        "base_stat_boost_percentage": check("baseStatBoostPercentage", None),
        "item_tier": check("item_tier", None),
        "is_dungeonized": isPresent("dungeon_item"),
        # mining
        "drill_part_fuel_tank": check("drill_part_fuel_tank", None),
        "drill_part_upgrade_module": check("drill_part_upgrade_module", None),
        "drill_part_engine": check("drill_part_engine", None),
        "divan_powder_coating": check("divan_powder_coating", None),
        # skin
        "is_skin_applied": isPresent("skin"),
        "skin": check("skin", None),
        # gemstones
        "applied_gem_stones": appliedGemstones,
        "unlocked_slots":unlockedSlots,
        # midas
        "winning_bid": check("winning_bid", None),
        "additional_coins": check("additional_coins", None),
        # misc
        "year_obtained": check("yearObtained", None),
        "cake_year": check("new_years_cake", None),
        "dye": check("dye_item", None),
    }

# SkyCoflNet-History
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
class BazaarHistory:
    def __init__(self, data, _range):
        #if isinstance(data, Error):

        self._range = _range
        self._data = data
        self._slots = self._parseTimeSlots(data)
    def __getitem__(self, item):
        return self._slots[item]
    def _parseTimeSlots(self, dlist:list)->List[BazaarHistoryProduct]:
        return [BazaarHistoryProduct(i) for i in dlist]
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
    def __init__(self, data, _range):
        self._data = data
        self._range = _range
        self._slots = self._parseTimeSlots(data)
    def __getitem__(self, item):
        return self._slots[item]
    def _parseTimeSlots(self, l:list)->List[AuctionHistoryProduct]:
        return [AuctionHistoryProduct(i) for i in l]
    def getTimeSlots(self) -> List[AuctionHistoryProduct]:
        return self._slots
    def getTimeSlotAT(self, tstamp)->BazaarHistoryProduct:
        pass
# SkyCoflNet-MayorData
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
        return getMayorTimezone(self._data["start"])
    def getEndTimestamp(self)->dt:
        return getMayorTimezone(self._data["end"])
    def getID(self)->str:
        return self._data["id"]
    def getElectionCandidates(self)->List[Mayor]:
        return self._electionCandidates

    @staticmethod
    def fromData(i):
        if "winner" not in i.keys():
            return None
        if "perks" in i["winner"].keys():
            return MayorData(i)
        return None
class MayorHistory:
    def __init__(self, data):
        self._data = data

    def getData(self)->dict:
        return self._data
# Recipe-API
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
# hypixel (bazzar)
class BazaarOrder:
    def __init__(self, data):
        self._data = data
    def getAmount(self)->int:
        return self._data["amount"]
    def getPricePerUnit(self)->float:
        return self._data["pricePerUnit"]
    def getOrders(self)->int:
        return self._data["orders"]
class BazaarProduct:
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
    def getInstaBuyPrice(self):
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
    def getInstaSellPrice(self):
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
class BazaarProductWithOrders(BazaarProduct):
    def __init__(self, id_, data):
        super().__init__(id_, data)
        self._sellOrders = self._parseOrders(self._data["sell_summary"])
        self._buyOrders = self._parseOrders(self._data["buy_summary"])
    def _parseOrders(self, l:list)->List[BazaarOrder]:
        return [BazaarOrder(i) for i in l]
    def getSellOrders(self)->List[BazaarOrder]:
        return self._sellOrders#[::-1]
    def getBuyOrders(self)->List[BazaarOrder]:
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
# hypixel (auction)
class BaseAuctionProduct:
    def __init__(self, auctData:dict, itemData:dict):
        self._itemData = itemData
        self._auctData = auctData
    # Auction
    def getCreatorUUID(self):
        return self._auctData["auctioneer"]
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
    def isClaimed(self)->bool:
        return self._auctData["claimed"]
    # item
    def getID(self)->str:
        return self._itemData["id"]
    def getCount(self)->int:
        return self._itemData["count"]
    def getDisplayName(self)->str:
        return self._itemData["name"]
    def getRarity(self)->str:
        return self._auctData["tier"]
    def getLore(self)->str:
        return self._auctData["item_lore"]
    # upgrades
    def isRecombUsed(self)->bool:
        return self._itemData["recomb"]
    def getEnchantments(self)->List[str]:
        return self._itemData["enchantments"]
    def getStars(self)->int:
        return self._itemData["stars"]
    def isReforged(self)->bool:
        return self._itemData["reforge"] is not None
    def getReforge(self)->str:
        return self._itemData["reforge"]
    def isWoodenSingularityUsed(self)->bool:
        return self._itemData["wooden_singularity_used"]
    def isShiny(self)->bool:
        return self._itemData["shiny"]
    def getPotatoBookCount(self)->int:
        return self._itemData["hot_potato_count"]
    def getPolarvoidCount(self)->int:
        return self._itemData["polarvoid_count"]
    def getFarmingForDummiesCount(self)->int:
        return self._itemData["farming_for_dummies_count"]
    def getTransmissionTunedCount(self)->int:
        return self._itemData["tuned_transmission"]
    def isEtherwarpApplied(self)->bool:
        return self._itemData["etherwarp"]
    def getManaDisintegratorCount(self)->int:
        return self._itemData["mana_disintegrator_count"]
    def isArtOfPeaceApplied(self)->bool:
        return self._itemData["is_art_of_peace_applied"]
    def getWetBookCount(self)->int:
        return self._itemData["wet_book_count"]
    def getBookWormCount(self)->int:
        return self._itemData["bookworm_books"]
    def getArtOfWarCount(self)->int:
        return self._itemData["art_of_war_count"]
    def getJalapenoCount(self)->int:
        return self._itemData["jalapeno_count"]
    def getPowerAbilityScroll(self)->str | None:
        return self._itemData["power_ability_scroll"]
    def getAbilityScrolls(self)->List[str] | None:
        return self._itemData["ability_scroll"]
    # rune
    def hasRune(self) -> bool:
        return self._itemData["rune_lvl"] != 0
    def getRuneLevel(self) -> int:
        return self._itemData["rune_lvl"]
    def getRuneType(self) -> str:
        return self._itemData["runeType"]
    # potion
    def getPotionLvl(self)->int:
        return self._itemData["potion_level"]
    # pets
    def isPet(self)->bool:
        return self._itemData["pet_level"] != 0
    def getPetLevel(self)->int:
        return int(self._itemData["pet_level"])
    def getPetItem(self)->str | None:
        return self._itemData["pet_item"]
    def getCandyUsed(self)->int:
        return self._itemData["candy_used"]
    def getPetExp(self)->float:
        return self._itemData["exp"]
    def getPetRarity(self)->str:
        return self._itemData["pet_rarity"]
    # stats
    def isBookOfStatsApplied(self)->bool:
        return self._itemData["isStatsBook"]
    def getBookOfStatsKills(self)->int:
        return self._itemData["kills"]
    def getSwordKills(self)->int:
        return self._itemData["sword_kills"]
    def getZombieKills(self)->int:
        return self._itemData["zombie_kills"]
    def getEmanKills(self)->int:
        return self._itemData["eman_kills"]
    def getSpiderKills(self)->int:
        return self._itemData["spider_kills"]
    def getRunicKills(self)->int:
        return self._itemData["runic_kills"]
    def getExpertiseKills(self)->int:
        return self._itemData["expertise_kills"]
    def getChampionCombatExp(self)->float:
        return self._itemData["champion_combat_xp"]
    def getToxophiliteCombatExp(self)->float:
        return self._itemData["toxophilite_combat_xp"]
    def getCollectedCoins(self)->int:
        return self._itemData["collected_coins"]
    def getDrillFuel(self)->int:
        return self._itemData["drill_fuel"]
    def getCompactBlocks(self)->int:
        return self._itemData["compact_blocks"]
    def getFarmedCultivating(self)->int:
        return self._itemData["farmed_cultivating"]
    def getMinedCrops(self)->int:
        return self._itemData["mined_crops"]
    def getThunderCharge(self)->int:
        return self._itemData["thunder_charge"]
    def getLogsCut(self)->int:
        return self._itemData["logs_cut"]
    def getBossTier(self):
        return self._itemData["boss_tier"]
    # fishing
    def getLineAttached(self)-> str | None:
        return self._itemData["line"]
    def getHookAttached(self)->str | None:
        return self._itemData["hook"]
    def getSinkerAttached(self)->str | None:
        return self._itemData["sinker"]
    # talis
    def isEnriched(self)->bool:
        return self._itemData["is_enriched"]
    def getEnrichment(self)->str | None:
        return self._itemData["enrichment"]
    def getBloodGodKills(self)->int:
        return self._itemData["blood_god_kills"]
    # dungeon
    def getDungeonSkillReq(self)->int:
        return self._itemData["dungeon_skill_req"]
    def getHecatombSRuns(self)->int | None:
        return self._itemData["hecatomb_s_runs"]
    def getBaseStatBoostPerc(self)->int:
        return self._itemData["base_stat_boost_percentage"]
    def getItemTier(self)->int:
        return self._itemData["item_tier"]
    def isDungeonized(self)->bool:
        return self._itemData["is_dungeonized"]
    # mining
    def getDrillPartFuelTank(self)->str | None:
        return self._itemData["drill_part_fuel_tank"]
    def getDrillPartUpgradeModule(self)->str | None:
        return self._itemData["drill_part_upgrade_module"]
    def getDrillPartEngine(self)->str | None:
        return self._itemData["drill_part_engine"]
    def getDivanPowderCoatingCount(self)->int:
        return self._itemData["divan_powder_coating"]
    # skin
    def getSkin(self)->str | None:
        return self._itemData["skin"]
    # gemstones
    def getAppliedGemstones(self)->List[str]:
        return self._itemData["applied_gem_stones"]
    def getUnlockedSlots(self)->List[str]:
        return self._itemData["unlocked_slots"]
    # midas
    def getMidasWinningBid(self)->float | None:
        return self._itemData["winning_bid"]
    def getMidasPricePayed(self)->float | None:
        return self._itemData["additional_coins"]
    # misc
    def getYearObtained(self)->int | None:
        return self._itemData["year_obtained"]
    def getCakeYear(self)->int | None:
        return self._itemData["cake_year"]
    def getDye(self):
        return self._itemData["dye"]
    def getDyeDonated(self)->str | None:
        return self._itemData["dye_donated"]
    def getUUID(self):
        return self._auctData["uuid"]


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
# hypixel (item API)
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
    def getUpgradeCosts(self):
        return self._data.get("upgrade_costs", None)
    def getGemstoneSlots(self):
        return self._data.get("gemstone_slots", None)