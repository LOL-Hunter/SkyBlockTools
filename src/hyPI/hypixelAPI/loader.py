from pysettings import iterDict
from pysettings.text import MsgText
from typing import Dict, List
from datetime import datetime
from ..APIError import *
from ..parser import BazaarProductWithOrders, BINAuctionProduct, NORAuctionProduct, convertAuctionNameToID, Item
from base64 import b64decode
from nbt.nbt import NBTFile
from io import BytesIO
from string import digits, ascii_lowercase


def getTimezone(tz)->datetime:
    unixTime = tz/1000
    return datetime.fromtimestamp(unixTime)

class HypixelMayorParser:
    def __init__(self, rawData: dict):
        if not rawData["success"]: raise CouldNotReadDataPackageException(rawData)
        self._data = rawData

    def getCurrentYear(self)->int:
        return self._data["mayor"]["election"]["year"]

    def getMainMayorName(self)->str:
        return self._data["mayor"]["name"]

    def getMainMayorPerksAmount(self)->int:
        return len(self._data["mayor"]["perks"])

    def getMainMayorPerks(self)->list:
        return self._data["mayor"]["perks"]

    def getMinisterName(self)->str | None:
        if "minister" in self._data["mayor"].keys():
            return self._data["mayor"]["minister"]["name"]
        return None

    def getMinisterPerk(self)->dict | None:
        if "minister" in self._data["mayor"].keys():
            return self._data["mayor"]["minister"]["perk"]
        return None

    def getMinisterPerkName(self)->str | None:
        if "minister" in self._data["mayor"].keys():
            return self._data["mayor"]["minister"]["perk"]["name"]
        return None

    def hasElectionStarted(self)->bool:
        return "current" in self._data.keys()

    def getCurrentCandidates(self)->list:
        return self._data["current"]["candidates"]
class HypixelProfilesParser:
    def __init__(self, rawData: dict):
        if not rawData["success"]: raise CouldNotReadDataPackageException(rawData)
        if rawData["profiles"] is None: raise CouldNotReadDataPackageException({"cause":"No Profile found at given UUID."})
        self._data = rawData

        self._profileIDs = [i["profile_id"] for i in self._data["profiles"]]
        self._serverNames = [i["cute_name"] for i in self._data["profiles"]]
        self._gameModes = [("normal" if "game_mode" not in i.keys() else i["game_mode"]) for i in self._data["profiles"]]

    def getProfileIDs(self)->List[str]:
        return self._profileIDs
    def getProfiles(self):
        return self._data["profiles"]
    def getServerNames(self)->List[str]:
        return self._serverNames
    def getGameModes(self)->List[str]:
        return self._gameModes
class HypixelProfileParser:
    def __init__(self, rawData:dict):
        if not rawData["success"]: raise CouldNotReadDataPackageException(rawData)
        self._data = rawData

    def decodeAccessoriesFromUUID(self, uuid:str)->List[Dict]:
        _accData = []
        dataB64 = self._data["profile"]["members"][uuid]["inventory"]["bag_contents"]["talisman_bag"]["data"]

        dataGZip = b64decode(dataB64)

        dataNBT = BytesIO(dataGZip)

        nbt = NBTFile(fileobj=dataNBT)

        temp = {}

        for tag_compound in nbt['i']:
            if 'tag' in tag_compound:
                accID = str(tag_compound['tag']['ExtraAttributes']['id'])
                recom = False if "rarity_upgrades" not in tag_compound['tag']['ExtraAttributes'].keys() else bool(tag_compound['tag']['ExtraAttributes']['rarity_upgrades'])
                enrich = False if "talisman_enrichment" not in tag_compound['tag']['ExtraAttributes'].keys() else bool(tag_compound['tag']['ExtraAttributes']['talisman_enrichment'])
                loreLastTag = str(tag_compound['tag']["display"]["Lore"][-1])

                # remove unicode Chrs
                loreLastTag = loreLastTag.encode('ascii','ignore').decode()
                # remove numbers and lowercase
                table = str.maketrans('', '', ascii_lowercase + digits)
                loreLastTag = loreLastTag.translate(table)
                # get first Word as Rarity
                #print(loreLastTag)
                loreLastTag = loreLastTag.replace("DUNGEON ", "")
                rarity = "_".join(loreLastTag.strip().split(" ")[0:-1])

                data = {
                    "id":accID,
                    "recomb":recom,
                    "enrichment":enrich,
                    "rarity":rarity,
                }

                RARITIES = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC", "SPECIAL", "VERY_SPECIAL", "SUPREME"]

                if accID in temp.keys(): # already in bag -> look for best
                    otherData = temp[accID]
                    if RARITIES.index(rarity) > RARITIES.index(otherData["rarity"]): # this acc is rarer
                        otherData["inactive"] = True
                        data["inactive"] = False
                    else: # registered is rarer
                        data["inactive"] = True
                else: # new unique
                    data["inactive"] = False
                    temp[accID] = data
                _accData.append(data)
        return _accData
class HypixelBazaarParser:
    def __init__(self, rawData:dict):
        if not rawData["success"]: raise CouldNotReadDataPackageException(rawData)
        self._data = rawData
        self._product_IDs = []
        self._products:Dict[str, BazaarProductWithOrders] = {} # id<str> : product <Product>
        self._parseProducts()

    def getRawData(self):
        return self._data

    def _parseProducts(self):
        for product_ID, product_data in iterDict(self._data["products"]):
            if ":" in product_ID: product_ID = product_ID.replace(":", "-")
            self._product_IDs.append(product_ID)
            self._products[product_ID] = BazaarProductWithOrders(product_ID, product_data)

    def getProducts(self)->List[BazaarProductWithOrders]:
        return list(self._products.values())

    def getProductByID(self, id_:str)-> BazaarProductWithOrders | None:
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
class HypixelAuctionPage:
    def __init__(self, rawData:dict, page:int):
        self._data = rawData
        self._page = page
        self._binAucts = []
        self._binByID = {}
        self._norAucts = []
        self._norByID = {}
        self._decode(rawData["auctions"])

    def _decode(self, data:list):
        for auctData in data:
            try:
                itemData = convertAuctionNameToID(auctData)
            except Exception as e:
                MsgText.warning(f"Could not parse Item name: {ascii(auctData['item_name'])} | ERR: ({e.__class__.__name__}: {e})")
                continue
            if auctData["bin"]:
                _bin = BINAuctionProduct(auctData, itemData)
                if itemData["id"] in self._binByID.keys():
                    self._binByID[itemData["id"]].append(_bin)
                else:
                    self._binByID[itemData["id"]] = [_bin]
                self._binAucts.append(_bin)
            else:
                _auc = NORAuctionProduct(auctData, itemData)
                if itemData["id"] in self._norByID.keys():
                    self._norByID[itemData["id"]].append(_auc)
                else:
                    self._norByID[itemData["id"]] = [_auc]
                self._norAucts.append(_auc)

    def getBINAuctionByID(self, id_: str) -> List[BINAuctionProduct]:
        if id_ in self._binByID:
            return self._binByID[id_]
        return []
    def getAuctionByID(self, id_: str) -> List[BINAuctionProduct]:
        if id_ in self._norByID:
            return self._norByID[id_]
        return []
class HypixelAuctionParser:
    def __init__(self):
        self._data = None
        self._pages = {}
    def addPage(self, rawData:dict, page:int):
        if "auctions" in rawData.keys():
            self._pages[page] = HypixelAuctionPage(rawData, page)
            self._data = {
                "page": rawData["page"],
                "totalPages": rawData["totalPages"],
                "totalAuctions": rawData["totalAuctions"],
                "lastUpdated": rawData["lastUpdated"],
            }
            return
        MsgText.warning(f"Auction House page: \"{rawData['cause']}\"")
    def getBinAuctions(self)->List[BINAuctionProduct]:
        temp = []
        for page in self._pages.values():
            temp.extend(page._binAucts)
        return temp
    def getAuctions(self)->List[NORAuctionProduct]:
        temp = []
        for page in self._pages.values():
            temp.extend(page._norAucts)
        return temp
    def getBINAuctionByID(self, id_:str)->List[BINAuctionProduct]:
        temp = []
        for i, page in zip(list(self._pages.keys())[1:], list(self._pages.values())[1:]):
            aucts = page.getBINAuctionByID(id_)
            temp.extend(aucts)
        return temp
    def getAuctionByID(self, id_:str)->List[NORAuctionProduct]:
        temp = []
        for page in self._pages.values():
            temp.extend(page.getAuctionByID(id_))
        return temp
    def getBinTypeAndAuctions(self)-> tuple[list[str], list[BINAuctionProduct]]:
        temp = {}
        for page in self._pages.values():
            for id_ in page._binByID.keys():
                aucts = page._binByID[id_]
                if id_ in temp.keys():
                    temp[id_].extend(aucts)
                    continue
                temp[id_] = aucts.copy()
        return list(temp.keys()), list(temp.values())
    def getAucTypeAndAuctions(self)-> tuple[list[str], list[NORAuctionProduct]]:
        temp = {}
        for page in self._pages.values():
            for id_ in page._norByID.keys():
                aucts = page._norByID[id_]
                if id_ in temp.keys():
                    temp[id_].extend(aucts)
                    continue
                temp[id_] = aucts.copy()
        return list(temp.keys()), list(temp.values())
    def getPages(self)->int:
        return self._data["totalPages"]
    def getTotalAuctions(self)->int:
        return self._data["totalAuctions"]
    def getLastUpdated(self)->datetime:
        return getTimezone(self._data["lastUpdated"])
