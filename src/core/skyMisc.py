# -*- coding: iso-8859-15 -*-
import tksimple as tk
from platform import system
from datetime import datetime
from typing import List, Dict
import os

from .hyPI.APIError import APIConnectionError, NoAPIKeySetException, APITimeoutException, CouldNotReadDataPackageException
from .hyPI.hypixelAPI import HypixelAPIURL, APILoader, fileLoader
from .hyPI.hypixelAPI.loader import HypixelBazaarParser, HypixelAuctionParser, HypixelItemParser, HypixelProfileParser, HypixelProfilesParser, HypixelMayorParser
from .hyPI.skyCoflnetAPI import SkyConflnetAPI
from .hyPI.parser import BINAuctionProduct
from .hyPI import getEnchantmentIDLvl
from .jsonConfig import JsonConfig
from .logger import TextColor, MsgText
from .constants import BAZAAR_INFO_LABEL_GROUP as BILG, AUCT_INFO_LABEL_GROUP as AILG, Path, API, ALL_ENCHANTMENT_IDS, AuctionItemID, BazaarItemID, System, Constants
from .skyMath import parseTimeDelta

def requestMayorHypixelAPI(master, config)->HypixelMayorParser | None:
    """
    @param uuid:
    @param config:
    @param master:
    @return:
    """
    try:
        TextColor.printStrf("§INFO§cRequesting 'MAYOR_DATA' from Hypixel-API")
        data = APILoader(HypixelAPIURL.MAYOR_URL, config.SETTINGS_CONFIG["api_key"])

        parser = HypixelMayorParser(data)
    except APIConnectionError as e:
        throwAPIConnectionException(
            source="Hypixel Mayor API",
            master=master,
            event=e
        )
        return None
    except NoAPIKeySetException as e:
        throwNoAPIKeyException(
            source="Hypixel Mayor API",
            master=master,
            event=e
        )
        return None
    except APITimeoutException as e:
        throwAPITimeoutException(
            source="Hypixel Mayor API",
            master=master,
            event=e
        )
        return None
    except CouldNotReadDataPackageException as e:
        throwCouldNotReadDataPackageException(
            source="Hypixel Mayor API",
            master=master,
            event=e
        )
        return None
    return parser
def requestProfilesHypixelAPI(master, config, uuid:str)->HypixelProfilesParser | None:
    """
    @param uuid:
    @param config:
    @param master:
    @return:
    """
    try: # config.SETTINGS_CONFIG["player_name"]
        TextColor.printStrf("§INFO§cRequesting 'PROFILES_DATA' from Hypixel-API")
        data = APILoader(HypixelAPIURL.PROFILES_URL, config.SETTINGS_CONFIG["api_key"], uuid=uuid)

        parser = HypixelProfilesParser(data)
    except APIConnectionError as e:
        throwAPIConnectionException(
            source="Hypixel Profiles API",
            master=master,
            event=e
        )
        return None
    except NoAPIKeySetException as e:
        throwNoAPIKeyException(
            source="Hypixel Profiles API",
            master=master,
            event=e
        )
        return None
    except APITimeoutException as e:
        throwAPITimeoutException(
            source="Hypixel Profiles API",
            master=master,
            event=e
        )
        return None
    except CouldNotReadDataPackageException as e:
        throwCouldNotReadDataPackageException(
            source="Hypixel Profiles API",
            master=master,
            event=e
        )
        return None
    return parser
def requestProfileHypixelAPI(master, config, accUuid:str)->HypixelProfileParser | None:
    """
    @param accUuid:
    @param config:
    @param master:
    @return:
    """
    try: # config.SETTINGS_CONFIG["player_name"]
        TextColor.printStrf(f"§INFO§cRequesting 'PROFILE_DATA_[{accUuid}]' from Hypixel-API")
        data = APILoader(HypixelAPIURL.PROFILE_URL, config.SETTINGS_CONFIG["api_key"], profile=accUuid)

        parser = HypixelProfileParser(data)
    except APIConnectionError as e:
        throwAPIConnectionException(
            source="Hypixel Profile API",
            master=master,
            event=e
        )
        return None
    except NoAPIKeySetException as e:
        throwNoAPIKeyException(
            source="Hypixel Profile API",
            master=master,
            event=e
        )
        return None
    except APITimeoutException as e:
        throwAPITimeoutException(
            source="Hypixel Profile API",
            master=master,
            event=e
        )
        return None
    except CouldNotReadDataPackageException as e:
        throwCouldNotReadDataPackageException(
            source="Hypixel Profile API",
            master=master,
            event=e
        )
        return None
    return parser
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
            data = APILoader(HypixelAPIURL.BAZAAR_URL, config.SETTINGS_CONFIG["api_key"], name=config.SETTINGS_CONFIG["player_name"])

            if saveTo is not None and data is not None:
                conf = JsonConfig.loadConfig(saveTo, create=True)
                conf.setData(data)
                conf.save()

        parser = HypixelBazaarParser(data)
    except APIConnectionError as e:
        throwAPIConnectionException(
            source="Hypixel Bazaar API",
            master=master,
            event=e
        )
        return None
    except NoAPIKeySetException as e:
        throwNoAPIKeyException(
            source="Hypixel Bazaar API",
            master=master,
            event=e
        )
        return None
    except APITimeoutException as e:
        throwAPITimeoutException(
            source="Hypixel Bazaar API",
            master=master,
            event=e
        )
        return None
    except CouldNotReadDataPackageException as e:
        throwCouldNotReadDataPackageException(
            source="Hypixel Bazaar API",
            master=master,
            event=e
        )
        return None
    return parser
def requestAuctionHypixelAPI(master, config, path=None, progBar:tk.Progressbar=None, infoLabel:tk.WidgetGroup | tk.Label=None, saveTo:str=None, fileNr:int=None, useParser=None)->HypixelAuctionParser | None:
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
            parser = HypixelAuctionParser()
            for i, fileName in enumerate(fileList):
                if progBar is not None: progBar.addValue()
                if infoLabel is not None:
                    if isinstance(infoLabel, tk.Label):
                        infoLabel.setText(f"Fetching Hypixel Auction API... [{i}/{len(fileList)}]")
                    else:
                        infoLabel.executeCommand("setText", f"Fetching Hypixel Auction API... [{i}/{len(fileList)}]")
                loader = fileLoader(os.path.join(path, fileName))
                parser.addPage(loader, 0 if "page" not in loader.keys() else loader["page"])
        else:
            if saveTo is not None and fileNr is None:
                TextColor.printStrf("§INFO§gDeleting old Auction-House config files...")
                for file in os.listdir(saveTo):
                    delPath = os.path.join(saveTo, file)
                    os.remove(delPath)
            if useParser is None:
                assert fileNr is None, "Using New Parser and requesting only one page!"
                parser = HypixelAuctionParser()
            else:
                parser = useParser
            if fileNr is None or fileNr == 0:
                TextColor.printStrf("§INFO§cRequesting 'AUCTION_DATA' from Hypixel-API [page=0]")
                data = APILoader(HypixelAPIURL.AUCTION_URL,
                                 config.SETTINGS_CONFIG["api_key"],
                                 name=config.SETTINGS_CONFIG["player_name"])
                data = parser.addPage(data, 0) # return decoded Data

                if saveTo is not None:
                    file = JsonConfig.fromDict(data)
                    file.setPath(os.path.join(saveTo, "file000.json"))
                    file.save()

            pages = parser.getPages()
            if progBar is not None: progBar.setValues(pages)
            if fileNr == 0: return parser
            for page in rangeIfSinleNone(1, pages, fileNr):
                Constants.WAITING_FOR_API_REQUEST = True
                TextColor.printStrf(f"§INFO§cRequesting 'AUCTION_DATA' from Hypixel-API [page={page}]")
                data = APILoader(HypixelAPIURL.AUCTION_URL,
                                 config.SETTINGS_CONFIG["api_key"],
                                 name=config.SETTINGS_CONFIG["player_name"],
                                 page=page)
                data = parser.addPage(data, page)  # return decoded Data
                if saveTo is not None:
                    file = JsonConfig.fromDict(data)
                    file.setPath(os.path.join(saveTo, f"file{str(page).rjust(3, '0')}.json"))
                    file.save()
                if infoLabel is not None:
                    if infoLabel is not None:
                        if isinstance(infoLabel, tk.Label):
                            infoLabel.setText(f"Fetching Hypixel Auction API... [{page}/{pages}]")
                        else:
                            infoLabel.executeCommand("setText",f"Fetching Hypixel Auction API... [{page+1}/{pages}]")
                if progBar is not None: progBar.setValue(page+1)
    except APIConnectionError as e:
        throwAPIConnectionException(
            source="Hypixel Auction API",
            master=master,
            event=e
        )
        return None
    except NoAPIKeySetException as e:
        throwNoAPIKeyException(
            source="Hypixel Auction API",
            master=master,
            event=e
        )
        return None
    except APITimeoutException as e:
        throwAPITimeoutException(
            source="Hypixel Auction API",
            master=master,
            event=e
        )
        return None
    except CouldNotReadDataPackageException as e:
        throwCouldNotReadDataPackageException(
            source="Hypixel Auction API",
            master=master,
            event=e
        )
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
            data = APILoader(HypixelAPIURL.ITEM_URL, config.SETTINGS_CONFIG["api_key"], name=config.SETTINGS_CONFIG["player_name"])
        if not data:
            return
        if saveTo is not None:
            conf = JsonConfig.loadConfig(saveTo)
            conf.setData(data)
            conf.save()
            MsgText.info(f"Saved Item-API-Data at: {saveTo}")

        parser = HypixelItemParser(data)
    except APIConnectionError as e:
        throwAPIConnectionException(
            source="Hypixel Item API",
            master=master,
            event=e
        )
        return None
    except NoAPIKeySetException as e:
        throwNoAPIKeyException(
            source="Hypixel Item API",
            master=master,
            event=e
        )
        return None
    except APITimeoutException as e:
        throwAPITimeoutException(
            source="Hypixel Item API",
            master=master,
            event=e
        )
        return None
    except CouldNotReadDataPackageException as e:
        throwCouldNotReadDataPackageException(
            source="Hypixel Item API",
            master=master,
            event=e
        )
        return None
    return parser

def throwAPIConnectionException(source:str, master:tk.Tk, event:APIConnectionError):
    MsgText.error(f"{source} request failed! Check your internet connection!")
    Constants.WAITING_FOR_API_REQUEST = False
    tk.SimpleDialog.askError(master, event.getMessage(), "SkyBlockTools")
def throwNoAPIKeyException(source:str, master:tk.Tk, event:NoAPIKeySetException):
    MsgText.error(f"{source} request failed! No API-key set.")
    Constants.WAITING_FOR_API_REQUEST = False
    tk.SimpleDialog.askError(master, event.getMessage(), "SkyBlockTools")
def throwAPITimeoutException(source:str, master:tk.Tk, event:APITimeoutException):
    MsgText.error(f"{source} request failed! Timeout Exception.")
    Constants.WAITING_FOR_API_REQUEST = False
    tk.SimpleDialog.askError(master, event.getMessage(), "SkyBlockTools")
def throwCouldNotReadDataPackageException(source:str, master:tk.Tk, event:CouldNotReadDataPackageException):
    MsgText.error(f"{source} request failed! Timeout Exception.")
    Constants.WAITING_FOR_API_REQUEST = False
    tk.SimpleDialog.askError(master, event.getMessage(), "SkyBlockTools")

def updateBazaarInfoLabel(api:HypixelBazaarParser | None, loaded=False):
    if api is not None:
        ts:datetime = api.getLastUpdated()
        diff = parseTimeDelta(datetime.now()-ts)

        if any([diff.minute, diff.day, diff.hour]):
            BILG.executeCommand("setFg", "orange")
        else:
            BILG.executeCommand("setFg", "green")
        if loaded:
            BILG.executeCommand("setFg", "cyan")

        _timeStr = parseTimeToStr(diff)
        if not loaded:
            BILG.executeCommand("setText", f"SkyBlock-Bazaar-API successful! Last request was [{_timeStr}] ago.")
        else:
            BILG.executeCommand("setText", f"SkyBlock-Bazaar-API was loaded from config! Request was [{_timeStr}] ago.")
    else:
        BILG.executeCommand("setFg", "red")
        BILG.executeCommand("setText", "SkyBlock-Bazaar-API request failed!")
def updateAuctionInfoLabel(api:HypixelAuctionParser | None, loaded=False):
    if api is not None:
        ts:datetime = api.getLastUpdated()
        diff = parseTimeDelta(datetime.now()-ts)

        if any([diff.minute, diff.day, diff.hour]):
            AILG.executeCommand("setFg", "orange")
        else:
            AILG.executeCommand("setFg", "green")
        if loaded:
            AILG.executeCommand("setFg", "cyan")

        _timeStr = parseTimeToStr(diff)
        if not loaded:
            AILG.executeCommand("setText", f"SkyBlock-Auction-API successful! Last request was [{_timeStr}] ago.")
        else:
            AILG.executeCommand("setText", f"SkyBlock-Auction-API was loaded from config! Request was [{_timeStr}] ago.")
    else:
        AILG.executeCommand("setFg", "red")
        AILG.executeCommand("setText", "SkyBlock-Auction-API request failed!")
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
def parsePriceFromStr(raw:str)-> float | None:
    if raw == "" or raw.count(".") > 1:
        return None # type: ignore
    raw = raw.replace(" ", "")
    if raw[-1].isdigit():
        return float(raw)
    allKeys = {"k":3,"m":6,"b":9,"t":12,"q":15}
    if (not raw[-1].lower() in allKeys.keys())or not raw[:-1].replace(".","").isdigit() or raw[0].lower() in allKeys.keys():
        return None # type: ignore
    return 10**allKeys[raw[-1].lower()]*float(raw[:-1])
def parsePrizeToStr(inputPrize: int | float | None, hideCoins=False, forceSign=False)-> str | None:
    if inputPrize is None: return None
    exponent = 0
    neg = inputPrize < 0
    if neg:
        inputPrize = abs(inputPrize)
    prefix = ["", "k", "m", "b", "Tr", "Q"]
    while round(inputPrize, 1) >= 1000:
        inputPrize /= 1000
        exponent += 1
        if exponent > 5:
            return f"Overflow {inputPrize}"
    return ("-" if neg else ("+" if forceSign else ""))+str(round(inputPrize, 1)) +" "+ prefix[exponent] + ("" if hideCoins else " coins")
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
            for item in searchList:
                itemName = item.value if hasattr(item, "value") else item
                itemName = itemName.replace("_", " ")
                show = True
                for valPice in value.split(" "):
                    if valPice not in itemName.lower():
                        show = False
                if show:
                    if printable:
                        suggestions.append(f"{itemName.lower()}")
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
    out += f"{round(sec, 3)}s"
    return out.strip()
def playNotificationSound():
    if System.SYSTEM_TYPE == "WINDOWS":
        from winsound import Beep
        Beep(800, 300)
    else:
        MsgText.warning("Beep on this System is not yet Implemented!")
def updateItemLists():
    BazaarItemID.clear()
    AuctionItemID.clear()
    ALL_ENCHANTMENT_IDS.clear()

    BazaarItemID.extend(API.SKYBLOCK_BAZAAR_API_PARSER.getProductIDs())

    for itemID in API.SKYBLOCK_ITEM_API_PARSER.getItems():
        id_ = itemID.getID()
        if id_ in BazaarItemID or id_ in AuctionItemID: continue
        AuctionItemID.append(id_)
def addPetsToAuctionHouse():
    i = 0
    for item in [*API.SKYBLOCK_AUCTION_API_PARSER.getAuctions(), *API.SKYBLOCK_AUCTION_API_PARSER.getBinAuctions()]:
        id_ = item.getID()
        if id_ is None: continue
        if id_.startswith("PET_") and id_ not in AuctionItemID:
            i += 1
            AuctionItemID.append(id_)
    ALL_ENCHANTMENT_IDS.clear()
    ALL_ENCHANTMENT_IDS.extend([i for i in BazaarItemID if i.startswith("enchantment".upper())])
    return i
def getLBin(itemID:str)->BINAuctionProduct | None:
    binAuctions = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(itemID)
    if binAuctions is None: return None
    if not len(binAuctions): return None
    sorters = []
    for auct in binAuctions:
        sorters.append(
            Sorter(
                sortKey="bin_price",

                bin_price=auct.getPrice(),
                auctClass=auct,
            )
        )
    sorters.sort()
    return sorters[-1]["auctClass"]
def getLBinList(itemID: str) -> list | None:
    binAuctions = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(itemID)
    if binAuctions is None: return None
    sorters = []
    for auct in binAuctions:
        sorters.append(
            Sorter(
                sortKey="bin_price",

                bin_price=auct.getPrice(),
                auctClass=auct,
            )
        )
    sorters.sort()
    return sorters
def enchBookConvert(from_:int, to:int)->int:
    if from_ == to: return 1
    if from_ > to: return 0
    return 2**(to - from_)
def rangeIfSinleNone(from_:int, to_:int, single: int | None):
    if single is None:
        return range(from_, to_)
    return [single]

class Sorter:
    def __init__(self, sort=None, sortKey=None, **kwargs):
        self._sort = sort if sort is not None else kwargs[sortKey]
        self._data = kwargs

    def __lt__(self, other):
        if self._sort is None: return False
        if other._sort is None: return True
        if type(self._sort) == str: return False
        if type(other._sort) == str: return True
        return self._sort > other._sort

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __repr__(self):
        return str(self._data)

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

def iterDict(__iterable:dict):
    return zip(__iterable.keys(), __iterable.values())
def _map(value, iMin, iMax, oMin=None, oMax=None):
    if oMin is None and oMax is None:
        oMax = iMax
        iMax = iMin
        iMin = 0
        oMin = 0
    return int((value-iMin) * (oMax-oMin) / (iMax-iMin) + oMin)
def determineSystem():
    match (system()):
        case "Windows":
            System.CONFIG_PATH = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".SkyBlockTools")
            System.SYSTEM_TYPE = "WINDOWS"
        case "Linux":
            System.CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", ".SkyBlockTools")
            System.SYSTEM_TYPE = "LINUX"
def registerPath(_file):
    Path.IMAGES = os.path.join(os.path.split(_file)[0], "images")
    Path.INTERNAL_CONFIG = os.path.join(os.path.split(_file)[0], "config")
def remEnum(val):
    return val.value if hasattr(val, "value") else val

