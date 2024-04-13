# -*- coding: iso-8859-15 -*-
import os
from hyPI.APIError import APIConnectionError, NoAPIKeySetException
from hyPI.hypixelAPI import HypixelAPIURL, APILoader, fileLoader
from hyPI.hypixelAPI.loader import HypixelBazaarParser, HypixelAuctionParser, HypixelItemParser
from hyPI.skyCoflnetAPI import SkyConflnetAPI
from hyPI.constants import ALL_ENCHANTMENT_IDS
from hyPI import getEnchantmentIDLvl
from pysettings import tk
from pysettings.jsonConfig import JsonConfig
from pysettings.text import TextColor, MsgText
from traceback import format_exc
from datetime import datetime
from constants import BAZAAR_INFO_LABEL_GROUP as BILG, AUCT_INFO_LABEL_GROUP as AILG
from skyMath import parseTimeDelta
from typing import List, Dict
from constants import API

def requestBazaarHypixelAPI(master, config, path=None, saveTo=None)->HypixelBazaarParser | None:
    """

    @param saveTo:
    @param config:
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
            TextColor.printStrf("§INFO§cRequesting 'BAZAAR_DATA' from Hypixel-API")
            data = APILoader(HypixelAPIURL.BAZAAR_URL, config.SETTINGS_CONFIG["api_key"], config.SETTINGS_CONFIG["player_name"])

            if saveTo is not None:
                conf = JsonConfig.loadConfig(saveTo, create=True)
                conf.setData(data)
                conf.save()

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
def requestAuctionHypixelAPI(master, config, path=None, progBar:tk.Progressbar=None, infoLabel:tk.Label=None, saveTo:str=None)->HypixelAuctionParser | None:
    """

    @param saveTo:
    @param infoLabel:
    @param progBar:
    @param config:
    @param master:
    @param path:
    @return:
    """
    try:
        if path is not None:
            fileList = os.listdir(path)
            if not len(fileList):
                tk.SimpleDialog.askError(master, "Could not Load Auction Data!\nRequesting api...")
                return requestAuctionHypixelAPI(master, config, None, progBar, infoLabel, saveTo)
            if progBar is not None:
                progBar.setValue(0)
                progBar.setValues(len(fileList))
            parser = HypixelAuctionParser(
                fileLoader(os.path.join(path, fileList[0])),
                API.SKYBLOCK_ITEM_API_PARSER
            )
            for i, fileName in enumerate(fileList[1:]):
                if progBar is not None: progBar.addValue()
                if infoLabel is not None: infoLabel.setText(f"Fetching Hypixel Auction API... [{i+1}/{len(fileList)}]")
                parser.addPage(fileLoader(os.path.join(path, fileName)))
        else:
            if saveTo is not None:
                TextColor.printStrf("§INFO§gDeleting old Auction-House config files...")
                for file in os.listdir(saveTo):
                    delPath = os.path.join(saveTo, file)
                    os.remove(delPath)
            TextColor.printStrf("§INFO§cRequesting 'AUCTION_DATA' from Hypixel-API")
            parser = HypixelAuctionParser(
                APILoader(HypixelAPIURL.AUCTION_URL,
                          config.SETTINGS_CONFIG["api_key"],
                          config.SETTINGS_CONFIG["player_name"]),
                API.SKYBLOCK_ITEM_API_PARSER
            )
            if saveTo is not None:
                file = JsonConfig.fromDict(parser._data)
                file.setPath(os.path.join(saveTo, "file000.json"))
                file.save()

            pages = parser.getPages()
            if progBar is not None: progBar.setValues(pages)
            for page in range(1, pages):
                TextColor.printStrf(f"§INFO§cRequesting 'AUCTION_DATA' from Hypixel-API [{page+1}]")
                data = APILoader(HypixelAPIURL.AUCTION_URL,
                                 config.SETTINGS_CONFIG["api_key"],
                                 config.SETTINGS_CONFIG["player_name"],
                                 page=page)
                if saveTo is not None:
                    file = JsonConfig.fromDict(data)
                    file.setPath(os.path.join(saveTo, f"file{str(page).rjust(3, '0')}.json"))
                    file.save()
                if infoLabel is not None: infoLabel.setText(f"Fetching Hypixel Auction API... [{page+1}/{pages}]")
                if progBar is not None: progBar.setValue(page+1)
                parser.addPage(data)
    except APIConnectionError as e:
        TextColor.print(format_exc(), "red")
        tk.SimpleDialog.askError(master, e.getMessage(), "SkyBlockTools")
        return None
    except NoAPIKeySetException as e:
        TextColor.print(format_exc(), "red")
        tk.SimpleDialog.askError(master, e.getMessage(), "SkyBlockTools")
        return None
    return parser
def requestItemHypixelAPI(master, config, path=None, saveTo=None)->HypixelItemParser | None:
    """

    @param saveTo:
    @param config:
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
            TextColor.printStrf("§INFO§cRequesting 'ITEM_DATA' from Hypixel-API")
            data = APILoader(HypixelAPIURL.ITEM_URL, config.SETTINGS_CONFIG["api_key"], config.SETTINGS_CONFIG["player_name"])

        if saveTo is not None:
            conf = JsonConfig.loadConfig(saveTo)
            conf.setData(data)
            conf.save()
            MsgText.info(f"Saved Item-API-Data at: {saveTo}")

        parser = HypixelItemParser(data)
    except APIConnectionError as e:
        TextColor.print(format_exc(), "red")
        tk.SimpleDialog.askError(master, e.getMessage(), "SkyBlockTools")
        return None
    except NoAPIKeySetException as e:
        TextColor.print(format_exc(), "red")
        tk.SimpleDialog.askError(master, e.getMessage(), "SkyBlockTools")
        return None
    return parser

def updateBazaarInfoLabel(api:HypixelBazaarParser | None, loaded=False):
    if api is not None:
        ts:datetime = api.getLastUpdated()
        diff = parseTimeDelta(datetime.now()-ts)

        if any([diff.minute, diff.day, diff.hour]):
            BILG.setFg("orange")
        else:
            BILG.setFg("green")
        if loaded:
            BILG.setFg("cyan")

        _timeStr = parseTimeToStr(diff)
        if not loaded:
            BILG.setText(f"SkyBlock-Bazaar-API successful! Last request was [{_timeStr}] ago.")
        else:
            BILG.setText(f"SkyBlock-Bazaar-API was loaded from config! Request was [{_timeStr}] ago.")
    else:
        BILG.setFg("red")
        BILG.setText("SkyBlock-Bazaar-API request failed!")
def updateAuctionInfoLabel(api:HypixelAuctionParser | None, loaded=False):
    if api is not None:
        ts:datetime = api.getLastUpdated()
        diff = parseTimeDelta(datetime.now()-ts)

        if any([diff.minute, diff.day, diff.hour]):
            AILG.setFg("orange")
        else:
            AILG.setFg("green")
        if loaded:
            AILG.setFg("cyan")

        _timeStr = parseTimeToStr(diff)
        if not loaded:
            AILG.setText(f"SkyBlock-Auction-API successful! Last request was [{_timeStr}] ago.")
        else:
            AILG.setText(f"SkyBlock-Auction-API was loaded from config! Request was [{_timeStr}] ago.")
    else:
        AILG.setFg("red")
        AILG.setText("SkyBlock-Auction-API request failed!")
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
    while inputPrize >= 1000:
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
def parseTimeFromSec(sec)->str:
    minutes = 0
    hour = 0
    day = 0
    year = 0

    out = ""
    if sec / 60 >= 1:
        minutes += int(sec / 60)
        sec %= 60
        if minutes / 60 >= 1:
            hour += int(minutes / 60)
            minutes %= 60
            if hour / 24 >= 1:
                day += int(hour/24)
                hour %= 24
                if day / 365 >= 1:
                    year += int(day / 365)
                    hour %= 365
    out += f"{year}y " if year > 0 else ""
    out += f"{day}d " if day > 0 else ""
    out += f"{hour}h " if hour > 0 else ""
    out += f"{minutes}m " if minutes > 0 else ""
    out += f"{sec}s"
    return out.strip()


class Sorter:
    def __init__(self, sort=None, sortKey=None, **kwargs):
        self._sort = sort if sort is not None else kwargs[sortKey]
        self._data = kwargs

    def __lt__(self, other):
        if type(self._sort) == str: return False
        if type(other._sort) == str: return True
        return self._sort > other._sort

    def __getitem__(self, item):
        return self._data[item]

    def get(self):
        return self._sort
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
    def __init__(self, id_, profit, craftPrice, req, depth=1):
        self._id = id_
        self._profit = profit
        self._craftPrice = craftPrice
        self.rq = req
        self._depth = depth
    def getCraftDepth(self):
        return self._depth
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


