from hyPI.constants import BazaarItemID, AuctionItemID, ALL_ENCHANTMENT_IDS
from hyPI.hypixelAPI.loader import HypixelBazaarParser
from hyPI import getEnchantmentIDLvl

from skyMath import getMedianExponent, parsePrizeList
from skyMisc import getDictEnchantmentIDToLevels

def getPlotData(itemId:BazaarItemID | AuctionItemID | str, func):
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


def getCheapestEnchantmentData(parser:HypixelBazaarParser, inputEnchantment: BazaarItemID | str, instaBuy=False) -> list | None:
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
