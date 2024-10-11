from pysettings import iterDict
from pysettings.text import MsgText
from typing import Dict, List, Tuple, Any
from datetime import datetime
from hyPI.APIError import *
from hyPI._parsers import ProductWithOrders, BINAuctionProduct, NORAuctionProduct, convertAuctionNameToID, Item
from traceback import format_exc
from time import time

def getTimezone(tz)->datetime:
    unixTime = tz/1000
    return datetime.fromtimestamp(unixTime)

class HypixelBazaarParser:
    def __init__(self, rawData:dict):
        if not rawData["success"]: raise CouldNotReadDataPackageException(rawData, success=False)
        self._data = rawData
        self._product_IDs = []
        self._products:Dict[str, ProductWithOrders] = {} # id<str> : product <Product>
        self._parseProducts()

    def getRawData(self):
        return self._data

    def _parseProducts(self):
        for product_ID, product_data in iterDict(self._data["products"]):
            if ":" in product_ID: product_ID = product_ID.replace(":", "-")
            self._product_IDs.append(product_ID)
            self._products[product_ID] = ProductWithOrders(product_ID, product_data)

    def getProducts(self)->List[ProductWithOrders]:
        return list(self._products.values())

    def getProductByID(self, id_:str)->ProductWithOrders | None:
        id_ = id_.value if hasattr(id_, "value") else id_
        if id_ not in self._products.keys():
            return None
        return self._products[id_]

    def getProductIDs(self)->List[str]:
        return self._product_IDs

    def getLastUpdated(self)->datetime:
        return getTimezone(self._data["lastUpdated"])

class HypixelItemParser:
    def __init__(self, rawData:dict):
        self._data = rawData
        self._items = []
        self._byID = {}
        self._byName = {}
        self._decode()
    def _decode(self):
        for data in self._data["items"]:
            ins = Item(data)
            self._byName[data["name"].upper().replace(" ", "_")] = ins
            self._byID[data["id"]] = ins
            self._items.append(ins)

    def getLastUpdated(self)->datetime:
        return getTimezone(self._data["lastUpdated"])

    def getItemAmount(self):
        return len(self._data["items"])
    def getItems(self)->List[Item]:
        return self._items
    def getItemByID(self, id_:str)->Item | None:
        if id_ in self._byID.keys():
            return self._byID[id_]
        return None
    def getItemByName(self, name:str)->Item | None:
        name = name.strip().upper().replace(" ", "_")
        if name in self._byName.keys():
            return self._byName[name]
        return None

class HypixelAuctionParser:
    def __init__(self, rawData:dict, itemParser:HypixelItemParser, auctionIDs:[str]):
        self._data = rawData
        self._binAucts = []
        self._binByID = {}
        self._norAucts = []
        self._norByID = {}
        self._auctionIDs = auctionIDs
        self._itemParser:HypixelItemParser = itemParser
        self._decode(rawData["auctions"])
        #print(ascii(self._binByID.keys()))
    def changeItemParser(self, parser:HypixelItemParser):
        self._itemParser._data = parser._data
    def _decode(self, data:list):
        for auctData in data:
            if auctData["bin"]:
                try:
                    itemData = convertAuctionNameToID(auctData, self._itemParser, self._auctionIDs)
                except:
                    MsgText.warning(f"Could not parse Item name: {ascii(auctData['item_name'])}")
                    continue
                #if "PET" in itemData["id"]: print(ascii(itemData["id"]))
                #if itemData["id"] is None: print(ascii(itemData["name"]))
                _bin = BINAuctionProduct(auctData, itemData)
                if itemData["id"] in self._binByID.keys():
                    self._binByID[itemData["id"]].append(_bin)
                else:
                    self._binByID[itemData["id"]] = [_bin]
                self._binAucts.append(_bin)
            else:
                try:
                    itemData = convertAuctionNameToID(auctData, self._itemParser, self._auctionIDs)
                except:
                    MsgText.error(format_exc(), True)
                    MsgText.warning(f"Could not parse Item name: {ascii(auctData['item_name'])}")
                    continue
                _auc = NORAuctionProduct(auctData, itemData)
                if itemData["id"] in self._norByID.keys():
                    self._norByID[itemData["id"]].append(_auc)
                else:
                    self._norByID[itemData["id"]] = [_auc]
                self._norAucts.append(_auc)
    def addPage(self, rawData:dict):
        if "auctions" in rawData.keys():
            self._decode(rawData["auctions"])
            return
        MsgText.warning(f"Auction House page: \"{rawData['cause']}\"")
    def getBinAuctions(self)->List[BINAuctionProduct]:
        return self._binAucts
    def getAuctions(self)->List[NORAuctionProduct]:
        return self._norAucts
    def getBINAuctionByID(self, id_:str)->List[BINAuctionProduct]:
        id_ = id_.value if hasattr(id_, "value") else id_
        if id_ in self._binByID:
            return self._binByID[id_]
        return []
    def getAuctionByID(self, id_:str)->List[NORAuctionProduct]:
        id_ = id_.value if hasattr(id_, "value") else id_
        if id_ in self._norByID:
            return self._norByID[id_]
        return []
    def getBinTypeAndAuctions(self)-> tuple[list[str], list[BINAuctionProduct]]:
        return list(self._binByID.keys()), list(self._binByID.values())
    def getAucTypeAndAuctions(self)-> tuple[list[str], list[NORAuctionProduct]]:
        return list(self._norByID.keys()), list(self._norByID.values())
    def getPages(self)->int:
        return self._data["totalPages"]
    def getTotalAuctions(self)->int:
        return self._data["totalAuctions"]
    def getLastUpdated(self)->datetime:
        return getTimezone(self._data["lastUpdated"])



