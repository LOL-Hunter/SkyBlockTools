from hyPI.hypixelAPI import fileLoader, APILoader, HypixelBazaarParser
from hyPI.constants import BazaarItemID, AuctionItemID, HypixelAPIURL
from hyPI import setAPIKey, setPlayerName
from hyPI.skyCoflnetAPI import SkyConflnetAPI
from typing import Tuple, List

from skyMath import getMedianExponent, parsePrizeList

def getPlotData(ItemId:BazaarItemID | AuctionItemID | str, func):
    hist = func(ItemId)
    pastBuyPrizes = []
    pastSellPrizes = []
    pastBuyVolume = []
    pastSellVolume = []
    timestamps = []
    for single in hist.getTimeSlots()[::-1]:
        buyPrice = single.getBuyPrice()
        sellPrice = single.getSellPrice()
        buyVolume = single.getBuyVolume()
        sellVolume = single.getSellVolume()
        pastBuyPrizes.append(0 if buyPrice is None else buyPrice)
        pastSellPrizes.append(0 if sellPrice is None else sellPrice)
        pastBuyVolume.append(0 if buyVolume is None else buyVolume)
        pastSellVolume.append(0 if sellVolume is None else sellVolume)
        ts = single.getTimestamp()
        time = ts.strftime('%d-%m-%Y-(%H:%M:%S)')
        timestamps.append(time)
    #price
    exp, pricePref = getMedianExponent(pastSellPrizes + pastBuyPrizes)
    pastBuyPrizes = parsePrizeList(pastBuyPrizes, exp)
    pastSellPrizes = parsePrizeList(pastSellPrizes, exp)

    #volume
    exp, volumePref = getMedianExponent(pastBuyVolume + pastSellVolume)
    pastBuyVolume = parsePrizeList(pastBuyVolume, exp)
    pastSellVolume = parsePrizeList(pastSellVolume, exp)

    return {
        "time_stamps":timestamps,
        "past_buy_prices":pastBuyPrizes,
        "past_sell_prices":pastSellPrizes,
        "past_buy_volume":pastBuyVolume,
        "past_sell_volume":pastSellVolume,
        "history_object":hist,
        "price_prefix":pricePref,
        "volume_prefix":volumePref,
    }




