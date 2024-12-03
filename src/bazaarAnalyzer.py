from hyPI.hypixelAPI.loader import HypixelBazaarParser
from hyPI._parsers import ProductWithOrders
from skyMath import applyBazaarTax
from constants import BazaarItemID, API, ConfigFile
from skyMisc import Sorter

from time import time
from typing import List, Tuple

"""
updates the Bazaar analyzer after new data is available from the api.
"""
def updateBazaarAnalyzer():
    if API.SKYBLOCK_BAZAAR_API_PARSER is None: return
    for itemID in BazaarItemID:
        itemClass = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemID)

        ## Sell price ##
        sellOrderPrice = applyBazaarTax(itemClass.getInstaBuyPrice())
        instaSellPrice = applyBazaarTax(itemClass.getInstaSellPrice())

        ## Buy price ##
        buyOrderPrice = itemClass.getInstaSellPrice() + .1
        instaBuyPrice = itemClass.getInstaBuyPriceList(1)
        if len(instaBuyPrice) > 0:
            instaBuyPrice = instaBuyPrice[0]
        else:
            instaBuyPrice = 0


        sellsPerHour = itemClass.getInstaSellWeek() / 168
        buysPerHour = itemClass.getInstaBuyWeek() / 168


        isManip = None
        isCrash = None
        avgPrDiff = ""
        avg = None
        if itemID in ConfigFile.AVERAGE_PRICE.keys():
            avg = ConfigFile.AVERAGE_PRICE[itemID]
            avgPrDiff = avg - buyOrderPrice

            if buyOrderPrice < (avg/4) and sellOrderPrice > 200:
                isCrash = True

            if sellOrderPrice > (avg*2) and sellOrderPrice > 200:
                isManip = True
        oldSorter = None
        prDiffChange = 0
        if itemID in BazaarAnalyzer.SORTER.keys():
            oldSorter = BazaarAnalyzer.SORTER[itemID]
            prDiffChange = oldSorter["priceDifference"] - (sellOrderPrice - buyOrderPrice)

        if itemID in BazaarAnalyzer.CRASHED_PRODUCTS.keys():
            cState = "old"
        else:
            cState = "new"

        if itemID in BazaarAnalyzer.MANIPULATED_PRODUCTS.keys():
            mState = "old"
        else:
            mState = "new"

        sorter = Sorter(
            sortKey="priceDifference",

            ## formal ##
            ID=itemID,
            itemClass=itemClass,

            ## price ##
            instaBuyPrice=instaBuyPrice,
            buyOrderPrice=buyOrderPrice,
            instaSellPrice=instaSellPrice,
            sellOrderPrice=sellOrderPrice,
            averagePriceToBuyDiff=avgPrDiff,
            priceDifference=sellOrderPrice - buyOrderPrice,
            averageBuyPrice=avg,

            ## traffic over time ##
            sellsPerWeek=itemClass.getInstaSellWeek(),
            buysPerWeek=itemClass.getInstaBuyWeek(),
            sellsPerHour=sellsPerHour,
            buysPerHour=buysPerHour,
            sellVolume=itemClass.getSellVolume(),
            sellOrders=itemClass.getSellOrdersTotal(),
            buyVolume=itemClass.getBuyVolume(),
            buyOrders=itemClass.getBuyOrdersTotal(),

            ## change ##
            priceDifferenceChance=prDiffChange,

            ## analyzes ##
            isManipulated=isManip,
            isCrashed=isCrash,
            crashedState=cState,
            manipulatedState=mState,
        )
        BazaarAnalyzer.SORTER[itemID] = sorter
        if isCrash:
            if itemID in BazaarAnalyzer.CRASHED_PRODUCTS.keys():
                BazaarAnalyzer.CRASHED_PRODUCTS[itemID] = (sorter, BazaarAnalyzer.CRASHED_PRODUCTS[itemID][1])
            else:
                BazaarAnalyzer.CRASHED_PRODUCTS[itemID] = (sorter, time())
        elif itemID in BazaarAnalyzer.CRASHED_PRODUCTS.keys():
            BazaarAnalyzer.CRASHED_PRODUCTS.pop(itemID)

        if isManip:
            if itemID in BazaarAnalyzer.MANIPULATED_PRODUCTS.keys():
                BazaarAnalyzer.MANIPULATED_PRODUCTS[itemID] = (sorter, BazaarAnalyzer.MANIPULATED_PRODUCTS[itemID][1])
            else:
                BazaarAnalyzer.MANIPULATED_PRODUCTS[itemID] = (sorter, time())
        elif itemID in BazaarAnalyzer.MANIPULATED_PRODUCTS.keys():
            BazaarAnalyzer.MANIPULATED_PRODUCTS.pop(itemID)

class BazaarAnalyzer:
    CRASHED_PRODUCTS = {}
    MANIPULATED_PRODUCTS = {}
    SORTER = {}

    @staticmethod
    def getManipulatedItems()->List[Tuple[Sorter, float]]:
        return list(BazaarAnalyzer.MANIPULATED_PRODUCTS.values())

    @staticmethod
    def getCrashedItems()->List[Tuple[Sorter, float]]:
        return list(BazaarAnalyzer.CRASHED_PRODUCTS.values())

    @staticmethod
    def _verifyProduct(prod):
        if isinstance(prod, str):
            return API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(prod)
        return prod