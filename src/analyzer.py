from hyPI.hypixelAPI.loader import HypixelBazaarParser
from hyPI import getEnchantmentIDLvl
from random import randint
from skyMath import getMedianExponent, parsePrizeList
from skyMisc import getDictEnchantmentIDToLevels
from constants import MAYOR_NORMAL, MAYOR_SPEC, MAYOR_PERK_AMOUNT

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
    currentMinister = currentMinister.lower().capitalize()
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
                    "cycles_without_selected":0
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
                    "cycles_without_selected": 0
                }

    # Diaz is Minister with "Long Term Investment"-Perk -> Diaz will appear as Mayor in next Cycle with FULL perks
    if currentMinister == "Diaz" and ministerHasLTI:
        perkData["Diaz"]["perks"] = 4
    # Diaz is Main with "Long Term Investment"-Perk Current Minister will appear with FULL perks
    elif currentMayor == "Diaz" and any([i["name"] == "Long Term Investment" for i in currentPerks]):
        perkData[currentMinister]["perks"] = MAYOR_PERK_AMOUNT[currentMinister]
    else:
        perkData.pop(currentMinister)
    return {
        "next_special_name":MAYOR_SPEC[(MAYOR_SPEC.index(lastSpecialName)+1) % len(MAYOR_SPEC)],
        "next_special_year":lastSpecialYear+8,
        "next_special_in_years":lastSpecialYear+8-currentYear,
        "next_perks":perkData,
    }