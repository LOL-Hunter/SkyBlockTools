from hyPI.APIError import APIConnectionError, NoAPIKeySetException
from hyPI.hypixelAPI import HypixelAPIURL, HypixelBazaarParser, APILoader, fileLoader
from hyPI.skyCoflnetAPI import SkyConflnetAPI
from hyPI.constants import ALL_ENCHANTMENT_IDS
from hyPI import getEnchantmentIDLvl
from pysettings import tk
from pysettings.text import TextColor
from traceback import format_exc
from datetime import datetime
from constants import INFO_LABEL_GROUP as ILG
from settings import Config
from skyMath import parseTimeDelta
from typing import List, Dict
from functools import total_ordering

def requestHypixelAPI(master, path=None):
    """

    @param master:
    @param path:
    @return:
    """
    try:
        if path is not None:
            try:
                data = fileLoader(path)
            except:
                tk.SimpleDialog.askError(master, f"Could not decode API-Config at:\n{path}", "SkyBlockTools")
                return None
        else:
            data = APILoader(HypixelAPIURL.BAZAAR_URL, Config.SETTINGS_CONFIG["api_key"], Config.SETTINGS_CONFIG["player_name"])
        parser = HypixelBazaarParser(data)
    except APIConnectionError as e:
        TextColor.print(format_exc(), "red")
        tk.SimpleDialog.askError(master, e.getMessage(), "SkyBlockTools")
        return None
    except NoAPIKeySetException as e:
        TextColor.print(format_exc(), "red")
        tk.SimpleDialog.askError(master, e.getMessage(), "SkyBlockTools")
        return None
    return parser
def updateInfoLabel(api:HypixelBazaarParser | None, loaded=False):
    if api is not None:
        ts:datetime = api.getLastUpdated()
        diff = parseTimeDelta(datetime.now()-ts)


        if any([diff.minute, diff.day, diff.hour]):
            ILG.setFg("orange")
        else:
            ILG.setFg("green")
        if loaded:
            ILG.setFg("cyan")

        _timeStr = parseTimeToStr(diff)
        if not loaded:
            ILG.setText(f"SkyBlock-API successful! Last request was [{_timeStr}] ago.")
        else:
            ILG.setText(f"SkyBlock-API was loaded from config! Request was [{_timeStr}] ago.")
    else:
        ILG.setFg("red")
        ILG.setText("SkyBlock-API request failed!")
def modeToBazaarAPIFunc(mode):
    match mode:
        case "hour":
            return SkyConflnetAPI.getBazaarHistoryHour
        case "day":
            return SkyConflnetAPI.getBazaarHistoryDay
        case "week":
            return SkyConflnetAPI.getBazaarHistoryWeek
        case "all":
            return SkyConflnetAPI.getBazaarHistoryComplete
def parseTimeToStr(d)->str:
    out = ""
    av = False
    for t, i in zip([d.day, d.hour, d.minute, d.second], ["d", "h", "m", "s"]):
        if t > 0 or av:
            out += f"{t}{i} "
            av = True
    return out
def prizeToStr(inputPrize:int | float | None, hideCoins=False)->str | None:
    if inputPrize is None: return None
    exponent = 0
    neg = inputPrize < 0
    if neg:
        inputPrize = abs(inputPrize)
    prefix = ["", "k", "m", "b", "Tr", "Q"]
    while inputPrize > 1000:
        inputPrize = inputPrize/1000
        exponent += 1
        if exponent > 5:
            return f"Overflow {inputPrize}"
    return ("-" if neg else "")+str(round(inputPrize, 1)) +" "+ prefix[exponent] + ("" if hideCoins else " coins")
def getDictEnchantmentIDToLevels()->Dict[str, List[str]]:
    """
    Returns a dictionary to access the valid enchantment levels from raw enchantmentID.

    format: {'ENCHANTMENT_TABASCO': ['ENCHANTMENT_TABASCO_1', 'ENCHANTMENT_TABASCO_2', 'ENCHANTMENT_TABASCO_3']}
    @return:
    """
    typeEnchantment = {}
    for singleEnchantment in ALL_ENCHANTMENT_IDS:
        enchantmentName, _ = getEnchantmentIDLvl(singleEnchantment)
        if enchantmentName in typeEnchantment:
            typeEnchantment[enchantmentName].append(singleEnchantment)
            typeEnchantment[enchantmentName].sort()
        else:
            typeEnchantment[enchantmentName] = [singleEnchantment]
    return typeEnchantment

def search(searchInput, value:str, minLength=0, printable=True):
    """
    inputList -> [BazaarItemID, AuctionItemID] # search bazaar and auction-house
    inputList -> {"ItemType":[IDS:str, ...]}

    @param printable:
    @param value:
    @param searchInput:
    @param minLength:
    @return:
    """
    def getType(_type) -> str:
        if "BazaarItemID" in str(_type):
            return "Bazaar Item"
        elif "AuctionItemID" in str(_type):
            return "Auction Item"
        else:
            return _type

    _searchInput = searchInput
    if isinstance(searchInput, dict):
        _searchInput = searchInput.values()

    suggestions = []
    if len(value) >= minLength:
        for i, searchList in enumerate(_searchInput):
            if isinstance(searchInput, dict):
                type_ = getType(list(searchInput.keys())[i])
            elif isinstance(searchInput, list) and len(searchInput) == 1:
                type_ = getType(_searchInput[0])
            else:
                raise Exception(f"Invalid search input! {searchInput}")
            for item in searchList:
                itemName = item.value if hasattr(item, "value") else item
                itemName = itemName.replace("_", " ")
                show = True
                for valPice in value.split(" "):
                    if valPice not in itemName.lower():
                        show = False
                if show:
                    if printable:
                        if type_ is None:
                            suggestions.append(f"{itemName.lower()}")
                        else:
                            suggestions.append(f"{itemName.lower()} - {type_}")
                    else:
                        suggestions.append(itemName.replace(" ", "_"))
    return suggestions









class BookCraft:
    def __init__(self, data, targetPrice):
        self._book_from_id = data["book_from_id"]
        self._book_to_id = data["book_to_id"]
        self._book_from_amount = data["book_from_amount"]
        self._anvil_operation_amount = data["anvil_operation_amount"]
        self._book_from_buy_price = data["book_from_buy_price"]
        self._book_from_sell_volume = data["book_from_sell_volume"]
        self._targetPrice = targetPrice

    def getShowAbleIDFrom(self):
        return self.getIDFrom().replace("ENCHANTMENT_", "").lower()
    def getShowAbleIDTo(self):
        return self.getIDTo().replace("ENCHANTMENT_", "").lower()
    def getIDFrom(self)->str:
        return self._book_from_id
    def getIDTo(self)->str:
        return self._book_to_id
    def getFromPrice(self):
        return self._book_from_buy_price
    def getFromPriceSingle(self, round_=2):
        if self._book_from_buy_price is None or self.getFromAmount() is None: return None
        return round(self._book_from_buy_price / self.getFromAmount(), round_)
    def getFromAmount(self):
        return self._book_from_amount
    def getSavedCoins(self):
        if self.getFromPrice() is None: return None
        return self._targetPrice - self.getFromPrice()
    def getFromSellVolume(self):
        return self._book_from_sell_volume
    def __lt__(self, other):
        if self.getSavedCoins() is None: return 0
        if other.getSavedCoins() is None: return 1
        return self.getSavedCoins() > other.getSavedCoins()
    #def __eq__(self, other):
    #    if self.getSavedCoins() is None or other.getSavedCoins() is None: return 0
    #    return self.getSavedCoins() == other.getSavedCoins()
    def __repr__(self):
        return f"{self.getSavedCoins()}"


class RecipeResult:
    def __init__(self, id_, profit, craftPrice, req):
        self._id = id_
        self._profit = profit
        self._craftPrice = craftPrice
        self.rq = req
    def getCraftPrice(self):
        return self._craftPrice
    def getRequired(self):
        return self.rq
    def getID(self):
        return self._id

    def getProfit(self):
        return self._profit



    def __lt__(self, other):
        return self.getProfit() > other.getProfit()


