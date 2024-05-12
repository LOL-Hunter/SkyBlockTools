from requests import get as getReq
from requests.exceptions import ConnectionError
from hyPI.APIError import APIConnectionError

from hyPI.constants import SkyCoflnetAPIURL, BazaarItemID, AuctionItemID, Error
from hyPI._parsers import BazaarHistory, BazaarProduct, AuctionHistory, AuctionProduct, Recipe, MayorHistory

def _request(url) ->dict | str | Error:
    try:
        return getReq(url).json()
    except ConnectionError:
        raise APIConnectionError(url)


class SkyConflnetAPI:
    @staticmethod
    def getBazaarHistoryHour(item: BazaarItemID | str) -> BazaarHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_BAZAAR_HIST_HOUR(item))
        return BazaarHistory(packet, range_="hour")

    @staticmethod
    def getBazaarHistoryDay(item: BazaarItemID | str) -> BazaarHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_BAZAAR_HIST_DAY(item))
        return BazaarHistory(packet, range_="day")

    @staticmethod
    def getBazaarHistoryWeek(item: BazaarItemID | str) -> BazaarHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_BAZAAR_HIST_WEEK(item))
        return BazaarHistory(packet, range_="week")

    @staticmethod
    def getBazaarHistoryComplete(item: BazaarItemID | str) -> BazaarHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_BAZAAR_HIST_COMPLETE(item))
        return BazaarHistory(packet, range_="complete")

    @staticmethod
    def getBazaarItemPrice(item: BazaarItemID | str) -> BazaarProduct:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_ITEM_PRICE(item))
        return BazaarProduct(packet)




    @staticmethod
    def getAuctionHistoryDay(item: AuctionItemID | str) -> AuctionHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_ITEM_HIST_DAY(item))
        return AuctionHistory(packet, range_="day")

    @staticmethod
    def getAuctionHistoryWeek(item: AuctionItemID | str) -> AuctionHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_ITEM_HIST_WEEK(item))
        return AuctionHistory(packet, range_="week")

    @staticmethod
    def getAuctionHistoryMonth(item: AuctionItemID | str) -> AuctionHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_ITEM_HIST_MONTH(item))
        return AuctionHistory(packet, range_="month")

    @staticmethod
    def getAuctionHistoryComplete(item: AuctionItemID | str) -> AuctionHistory:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_ITEM_HIST_COMPLETE(item))
        return AuctionHistory(packet, range_="complete")


    @staticmethod
    def getAuctionItemPrice(item: AuctionItemID | str) -> AuctionProduct:
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_ITEM_PRICE(item))
        return AuctionProduct(packet)

    @DeprecationWarning
    @staticmethod
    def getCraftingRecipe(item: AuctionItemID | str) -> Recipe:
        raise DeprecationWarning()
        item = item.value if hasattr(item, "value") else item
        packet = _request(SkyCoflnetAPIURL.GET_URL_CRAFT_RECIPE(item))
        return Recipe(packet)

    @staticmethod
    def getMayorData() -> MayorHistory:
        packet = _request(SkyCoflnetAPIURL.GET_URL_MAJOR_ACTIVE())
        return MayorHistory(packet)

if __name__ == '__main__':
    print(ascii(_request("https://sky.coflnet.com/api/items")))