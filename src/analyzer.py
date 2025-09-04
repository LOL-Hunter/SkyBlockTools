from typing import Tuple, Union

from hyPI.hypixelAPI.loader import HypixelBazaarParser
from hyPI.parser import BaseAuctionProduct, BINAuctionProduct
from hyPI.constants import MODIFIER
from hyPI import getEnchantmentIDLvl

from random import randint
from skyMath import getMedianExponent, parsePrizeList, applyBazaarTax
from skyMisc import getDictEnchantmentIDToLevels, prizeToStr, getLBin, enchBookConvert
from constants import MAYOR_NORMAL, MAYOR_SPEC, MAYOR_PERK_AMOUNT, API, ConfigFile, MASTER_STARS
from logger import MsgText


def getPlotData(itemId:str, func):
    hist = func(itemId)
    pastRawBuyPrizes = []
    pastRawSellPrizes = []
    pastBuyVolume = []
    pastSellVolume = []
    timestamps = []
    for single in hist.getTimeSlots()[::-1]:
        buyPrice = single.getBuyPrice()
        sellPrice = single.getSellPrice()
        buyVolume = single.getBuyVolume()
        sellVolume = single.getSellVolume()
        pastRawBuyPrizes.append(0 if buyPrice is None else buyPrice)
        pastRawSellPrizes.append(0 if sellPrice is None else sellPrice)
        pastBuyVolume.append(0 if buyVolume is None else buyVolume)
        pastSellVolume.append(0 if sellVolume is None else sellVolume)
        ts = single.getTimestamp()
        time = ts.strftime('%d-%m-%Y-(%H:%M:%S)')
        timestamps.append(time)

    #price
    exp, pricePref = getMedianExponent(pastRawSellPrizes + pastRawBuyPrizes)
    pastBuyPrizes = parsePrizeList(pastRawBuyPrizes, exp)
    pastSellPrizes = parsePrizeList(pastRawSellPrizes, exp)

    #volume
    exp, volumePref = getMedianExponent(pastBuyVolume + pastSellVolume)
    pastBuyVolume = parsePrizeList(pastBuyVolume, exp)
    pastSellVolume = parsePrizeList(pastSellVolume, exp)

    return {
        "time_stamps":timestamps,
        "past_buy_prices":pastBuyPrizes,
        "past_sell_prices":pastSellPrizes,
        "past_raw_buy_prices": pastRawBuyPrizes,
        "past_raw_sell_prices": pastRawSellPrizes,
        "past_buy_volume":pastBuyVolume,
        "past_sell_volume":pastSellVolume,
        "history_object":hist,
        "price_prefix":pricePref,
        "volume_prefix":volumePref,
    }
def getCheapestEnchantmentData(parser:HypixelBazaarParser, inputEnchantment:str, instaBuy=False) -> list | None:
    inputEnchantment = inputEnchantment.name if hasattr(inputEnchantment, "value") else inputEnchantment

    # getting the prizes of all Enchantments
    allEnchantments = getDictEnchantmentIDToLevels()
    # test if the input is an Enchantment to avoid Errors
    if "ENCHANTMENT" not in inputEnchantment:
        return None

    # get Name and Level of 'inputEnchantment'.
    nameEnchantment, heightEnchantment = getEnchantmentIDLvl(inputEnchantment)

    # Calculate the Prize of a single book in compared to the others

    rawDict = {
        "book_to_id": inputEnchantment,
        "book_from_id": "",
        "book_from_amount": None,
        "anvil_operation_amount": None,
        "book_from_buy_price": None,
        "book_from_sell_volume": None,
        "book_from_sells_per_hour": None,
    }
    returnList = []
    prizeList = {}
    endPriceAllBooks = {}

    for single in allEnchantments[nameEnchantment]:
        heightOfPossible = int(single.split('_')[-1])
        if heightOfPossible > heightEnchantment:
            continue
        if instaBuy:
            prizeList[single] = parser.getProductByID(single).getInstaBuyPriceList(2 ** heightEnchantment)
        else:
            prizeList[single] = parser.getProductByID(single).getInstaSellPriceList(2 ** heightEnchantment)
        neededHeight = 0
        amountOfBooks = 0
        endPriceAllBooks[single] = 0

        for prizeSingleEnchantment in prizeList[single]:
            if 2 ** heightEnchantment <= neededHeight:
                break

            neededHeight += 2 ** heightOfPossible
            endPriceAllBooks[single] += prizeSingleEnchantment
            amountOfBooks += 1

            singleDict = {
                "book_to_id":inputEnchantment,
                "book_from_id": single,
                "book_from_amount": amountOfBooks, # not always correct !
                "anvil_operation_amount": amountOfBooks - 1, # not always correct !
                "book_from_buy_price": endPriceAllBooks[single],
                "book_from_sell_volume": parser.getProductByID(single).getSellVolume(),
                "book_from_sells_per_hour": None
            }
        if not len(prizeList[single]): #  No Data found for this craft
            singleDict = rawDict.copy()
            singleDict["book_from_id"] = single
        returnList.append(singleDict)
    return returnList
def simulateElections(data:dict, n=100_000):
    mayorPool = list(data["next_perks"].keys())
    _data = {}
    for mayor in mayorPool:
        _data[mayor] = {}
        numOfPerks = data["next_perks"][mayor]["perks"]
        maxAmountOfPerks = MAYOR_PERK_AMOUNT[mayor]
        numOfDraws = data["next_perks"][mayor]["cycles_without_selected"] + 1
        _data[mayor]["chances"] = []
        if data["next_perks"][mayor]["available_perks"][0]["name"] == "<Random_Perk>": continue # mayor came back after one election cycle -> ignore (must have exact one perk)
        if numOfPerks == maxAmountOfPerks: continue # skip if already have all perks (from diaz)
        drawData = [0, 0, 0, 0] # [zero, one, two, three] times perks gained
        for _ in range(n):
            newNumOfPerks = numOfPerks
            for draw in range(numOfDraws):
                if newNumOfPerks == maxAmountOfPerks: break
                if newNumOfPerks < 3 and randint(0, 1) == 1:
                    newNumOfPerks += 1
                elif newNumOfPerks >= 3 and randint(1, 100) <= 8:
                    newNumOfPerks += 1
            gained = newNumOfPerks - numOfPerks
            drawData[gained] += 1
        for i, times in enumerate(drawData):
            if times <= 0: break
            _data[mayor]["chances"].append(times / n)
    return _data
def analyzeMayors(data:list, currentMinister:str, ministerHasLTI, yearOffset:int=0):
    if not len(data): return None
    lastSpecialName = None
    lastSpecialYear = None
    currentMinister = currentMinister.lower().capitalize() if currentMinister is not None else None
    currentYear = data[-1]["year"] - yearOffset
    currentMayor = data[-1]["winner"]["name"]
    currentPerks = data[-1]["winner"]["perks"]
    perkData = {}
    oldWinner = [None, None]
    for election in data:
        candidates = []
        for candidate in election["candidates"]:
            name = candidate["name"]
            perks = len(candidate["perks"])
            if name not in perkData.keys() and name not in MAYOR_SPEC:
                perkData[name] = {
                    "perks":0,
                    "available_perks": [],
                    "cycles_without_selected":0,
                    "is_special": False,
                    "has_full_perks": False
                }
            if name not in MAYOR_SPEC:
                perkData[name]["perks"] = perks
                perkData[name]["available_perks"] = candidate["perks"].copy()
                perkData[name]["cycles_without_selected"] = 0
            if name in MAYOR_SPEC:
                lastSpecialYear = election["year"]
                lastSpecialName = name
            candidates.append(name)
        for may in MAYOR_NORMAL:
            if may not in candidates and may in perkData.keys():
                perkData[may]["cycles_without_selected"] += 1
        if election["winner"]["name"] in MAYOR_NORMAL: perkData.pop(election["winner"]["name"])
        oldWinner[0] = oldWinner[1]
        oldWinner[1] = {
            "name": election["winner"]["name"],
            "can_participate_again": election["year"]+2
        }
        if oldWinner[0] is not None:
            if oldWinner[0]["name"] in MAYOR_NORMAL:
                perkData[oldWinner[0]["name"]] = {
                    "perks": 1,
                    "available_perks": [{"name":"<Random_Perk>", "description":"<Random_Perk>"}],
                    "cycles_without_selected": 0,
                    "is_special": False,
                    "has_full_perks": False
                }

    # Diaz is Minister with "Long Term Investment"-Perk -> Diaz will appear as Mayor in next Cycle with FULL perks
    if currentMinister == "Diaz" and ministerHasLTI:
        perkData["Diaz"]["perks"] = 4
        perkData["Diaz"]["available_perks"].append({"name":"<Full_Perk>", "description":"<Full_Perk>"})
        perkData["Diaz"]["has_full_perks"] = True
    # Diaz is Main with "Long Term Investment"-Perk Current Minister will appear with FULL perks
    elif currentMayor == "Diaz" and any([i["name"] == "Long Term Investment" for i in currentPerks]):
        perkData[currentMinister]["perks"] = MAYOR_PERK_AMOUNT[currentMinister]
        perkData[currentMinister]["available_perks"].append({"name":"<Full_Perk>", "description":"<Full_Perk>"})
        perkData[currentMinister]["has_full_perks"] = True
    else:
        if currentMinister is not None: perkData.pop(currentMinister)

    for may in perkData.keys():
        mayorData = perkData[may]
        if mayorData["available_perks"] == MAYOR_PERK_AMOUNT[may]:
            mayorData["has_full_perks"] = True
    NEXT_SPEC_NAME = MAYOR_SPEC[(MAYOR_SPEC.index(lastSpecialName)+1) % len(MAYOR_SPEC)]
    if lastSpecialYear+8-currentYear == 0:
        perkData[NEXT_SPEC_NAME] = {
            "perks": MAYOR_PERK_AMOUNT[NEXT_SPEC_NAME],
            "cycles_without_selected": 0,
            "available_perks": [{"name":"<Full_Perk>", "description":"<Full_Perk>"}],
            "is_special": True,
            "has_full_perks": True
        }

    return {
        "next_special_name":NEXT_SPEC_NAME,
        "next_special_year":lastSpecialYear+8,
        "next_special_in_years":lastSpecialYear+8-currentYear,
        "next_perks":perkData,
    }
def calculateUpgradesPrice(item: BaseAuctionProduct, isOrder: bool) -> tuple[float, str]:
    desc = ""
    def getPrice(id_: str | int, amount: int=1, ignore=False, addStr=""):
        nonlocal desc
        price = None
        if not amount: return 0
        if type(id_) is str:
            bzProduct = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(id_)
            if bzProduct is not None:
                if isOrder:  # use buy Offer
                    itemSellPrice = bzProduct.getInstaSellPrice()
                else:  # insta buy
                    itemSellPrice = bzProduct.getInstaBuyPrice()
                price = applyBazaarTax(itemSellPrice) * amount
        else: price = id_

        if price is None:
            if not ignore: desc += f"{addStr}{id_}(x{amount}): 0 (ERROR)\n"
            return 0.0
        desc += f"{addStr}{id_}(x{amount}): {prizeToStr(price)}\n"
        return price

    upgradePrice = 0.0
    if item.isRecombUsed(): upgradePrice += getPrice("RECOMBOBULATOR_3000")
    enchPrice = 0
    for ench in item.getEnchantments():
        if not ench.startswith("ENCHANTMENT_ULTIMATE"):
            c = getPrice(ench, ignore=False, addStr="\t")
            upgradePrice += c
            enchPrice += c
            continue

        *name, ultLvl = ench.split("_")

        name = "_".join(name)
        lowestUltLvl = int(ultLvl)
        while True:
            if API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(f"{name}_{lowestUltLvl-1}") is None:
                break
            lowestUltLvl -= 1
        amount = enchBookConvert(lowestUltLvl, int(ultLvl))
        id_ = f"{name}_{lowestUltLvl}"
        bzProduct = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(id_)
        if bzProduct is not None:
            if isOrder:  # use buy Offer
                itemSellPrice = bzProduct.getInstaSellPrice()
            else:  # insta buy
                itemSellPrice = bzProduct.getInstaBuyPrice()
            price = applyBazaarTax(itemSellPrice) * amount
            desc += f"\t{id_}: {prizeToStr(price)}(x{amount})\n"
            upgradePrice += price
    desc += f"Enchantments: {prizeToStr(enchPrice)}\n"

    if item.getStars() > 0:
        itemConf = API.SKYBLOCK_ITEM_API_PARSER.getItemByID(item.getID())
        if itemConf is None or itemConf.getUpgradeCosts() is None:
            desc += f"Stars: Could not Calculate! (ItemAPI missing)\n"
        else:
            stars = item.getStars()
            for upgrades in itemConf.getUpgradeCosts():
                if not stars: break
                for upgrade in upgrades:
                    amount = 0
                    if "amount" in upgrade.keys():
                        amount = upgrade["amount"]
                    upgItemID = None
                    if upgrade["type"] == "ITEM":
                        upgItemID = upgrade["item_id"]
                    elif upgrade["type"] == "ESSENCE":
                        upgItemID = "ESSENCE_"+upgrade["essence_type"]
                    if upgItemID is None:
                        MsgText.error(f"Could not calculate StarPrice: ItemAPI[unknown type {upgrade['type']}]")
                    else:
                        upgradePrice += getPrice(upgItemID, amount=amount, ignore=False)
                stars -= 1
            if stars > 0:
                for i in range(stars):
                    upgradePrice += getPrice(MASTER_STARS[i], ignore=False)

    for gem in item.getAppliedGemstones():
        upgradePrice += getPrice(gem, ignore=False)
    if item.getStars() > 0:
        itemConf = API.SKYBLOCK_ITEM_API_PARSER.getItemByID(item.getID())
        if itemConf is None or itemConf.getGemstoneSlots() is None:
            desc += f"Gem-Unlocks: Could not Calculate! (ItemAPI missing)\n"
        else:
            gemstoneUnlockCost = 0
            unlockedGemstoneSlots = item.getUnlockedSlots()
            for slot in itemConf.getGemstoneSlots():
                slotType = slot["slot_type"]

                for unlSlot in unlockedGemstoneSlots:
                    if unlSlot.split("_")[0] == slotType:

                        for cost in slot["costs"]:
                            if cost["type"] == "COINS":
                                gemstoneUnlockCost += getPrice(cost["coins"], addStr="\t")
                            elif cost["type"] == "ITEM":
                                gemstoneUnlockCost += getPrice(cost["item_id"], amount=cost["amount"], addStr="\t")
                            else:
                                MsgText.error(f"Could not calculate GemstoneUnlock Price: ItemAPI[unknown type {cost['type']}]")
                        break
            desc += f"Gemstone Unlock: {prizeToStr(gemstoneUnlockCost)}\n"
            upgradePrice += gemstoneUnlockCost
    if item.isReforged():
        reforge = item.getReforge()
        if reforge in MODIFIER.keys():
            reforgeStone = MODIFIER[reforge]
            if reforgeStone != "BLACKSMITH":
                upgradePrice += getPrice(reforgeStone, ignore=False)
        else:
            MsgText.warning(f"calculateUpgradesPrice() -> Reforge {reforge} not found!")
    if item.isWoodenSingularityUsed(): upgradePrice += getPrice("WOOD_SINGULARITY", ignore=False)
    if item.isShiny(): upgradePrice += getPrice(100_000_000, ignore=False)
    potatoAmount = item.getPotatoBookCount()
    if potatoAmount > 10:
        upgradePrice += getPrice("FUMING_POTATO_BOOK", amount=potatoAmount-10, ignore=False)
        potatoAmount = 10
    upgradePrice += getPrice("HOT_POTATO_BOOK", amount=potatoAmount, ignore=False)
    upgradePrice += getPrice("POLARVOID_BOOK", amount=item.getPolarvoidCount(), ignore=False)
    upgradePrice += getPrice("FARMING_FOR_DUMMIES", amount=item.getFarmingForDummiesCount(), ignore=False)
    upgradePrice += getPrice("TRANSMISSION_TUNER", amount=item.getTransmissionTunedCount(), ignore=False)
    if item.isEtherwarpApplied():
        #TODO impl
        pass
    upgradePrice += getPrice("MANA_DISINTEGRATOR", amount=item.getManaDisintegratorCount(), ignore=False)
    if item.isArtOfPeaceApplied(): upgradePrice += getPrice("THE_ART_OF_PEACE", ignore=False)
    upgradePrice += getPrice("WET_BOOK", amount=item.getWetBookCount(), ignore=False)
    upgradePrice += getPrice("BOOKWORM_BOOK", amount=item.getBookWormCount(), ignore=False)
    upgradePrice += getPrice("THE_ART_OF_WAR", amount=item.getArtOfWarCount(), ignore=False)
    upgradePrice += getPrice("JALAPENO_BOOK", amount=item.getJalapenoCount(), ignore=False)
    if item.getPowerAbilityScroll() is not None:
        upgradePrice += getPrice(item.getPowerAbilityScroll(), ignore=False)
    for scroll in item.getAbilityScrolls():
        upgradePrice += getPrice(scroll, ignore=False)
    if item.isBookOfStatsApplied():
        upgradePrice += getPrice("BOOK_OF_STATS", amount=item.getJalapenoCount(), ignore=False)
    return upgradePrice, desc
def calculateEstimatedItemValue(item: BaseAuctionProduct, isOrder: bool, lowestBinPrice:float=None)->Tuple[Union[float, None], str]:
    itemID = item.getID()
    basePrice = None
    mode = ""
    remTxt = ""
    # get average price from Config
    if ConfigFile.AVERAGE_PRICE is not None:
        if itemID in ConfigFile.AVERAGE_PRICE.keys():
            mode = "avg"
            basePrice = ConfigFile.AVERAGE_PRICE[itemID]
    # else take LBin
    if basePrice is None:
        if lowestBinPrice is None:
            lowestBin = getLBin(itemID)
        else:
            lowestBin = lowestBinPrice
        if lowestBin is None: return None, "LowestBin is None"
        if not isinstance(lowestBin, BINAuctionProduct): return None, "lowestBin is not instance BINAuctionProduct!"
        basePrice = lowestBin.getPrice()
        upgradesPriceLBIN, _ = calculateUpgradesPrice(lowestBin, isOrder)
        if upgradesPriceLBIN:
            remTxt = f"\t(-{prizeToStr(upgradesPriceLBIN)})\n"
            basePrice -= upgradesPriceLBIN
        mode = "lbin"
    desc = f"BasePrice({mode}): {prizeToStr(basePrice)}\n{remTxt}"
    upgradesPrice, desc2 = calculateUpgradesPrice(item, isOrder)
    desc += desc2

    basePrice += upgradesPrice

    desc += f"\nEstimatedTotal: {prizeToStr(basePrice)}"

    return basePrice, desc
