import os

from sympy.logic.inference import valid

import tksimple as tk
from functools import cache
from itertools import product

from core.logger import MsgText
from core.widgets import CustomPage
from core.constants import API, STYLE_GROUP as SG, ConfigFile
from core.skyMisc import iterDict, Sorter, parsePrizeToStr, getShardsNeeded, isRarityGreater
from core.skyMath import applyBazaarTax


"""
save calculated shards look if this shard is req take cheapest path
look at start shard price and stop calc if shards are more exp than start


"""


class AttrHelper:
    @staticmethod
    def getShard(shard:str)->dict:
        if shard in ConfigFile.ATTR_SHARD_DATA.keys():
            return ConfigFile.ATTR_SHARD_DATA[shard]
        MsgText.error(f"Could not find shardID {shard}")

    @staticmethod
    def getCheapestShard(*shards:str, isOrder:bool):
        cheapestPrice = None
        cheapestID = None
        for _id in shards:
            product = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(_id)
            if product is None:
                #MsgText.error(f"getShardsPrices() -> cannot get price of shard {_id}!")
                continue
            if isOrder:
                price = product.getInstaSellPrice()
            else:
                price = product.getInstaBuyPrice()
            price =  applyBazaarTax(price)
            if cheapestID is None or cheapestPrice > price:
                cheapestID = _id
                cheapestPrice = price
        return cheapestID, cheapestPrice

    @staticmethod
    def getShardsPrices(*IDs:str, isOrder:bool)->float:
        temp = 0
        for _id in IDs:
            product = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(_id)
            if product is None:
                #MsgText.error(f"getShardsPrices() -> cannot get price of shard {_id}!")
                continue
            if isOrder:
                price = product.getInstaSellPrice()
            else:
                price = product.getInstaBuyPrice()
            temp += applyBazaarTax(price)
        return temp

    @staticmethod
    @cache
    def getValidShards(rarity=None, or_higher=None, family=None, category=None, shard=None)->list:
        if shard is not None: return [shard]
        valid = []
        for shID, data in iterDict(ConfigFile.ATTR_SHARD_DATA):
            if rarity is not None and rarity != data["rarity"]: continue
            if or_higher is not None and not isRarityGreater(rarity, data["rarity"]): continue
            if family is not None and family not in data["family"]: continue
            if category is not None and category not in data["category"]: continue
            valid.append(shID)
        return valid

    @staticmethod
    def getFusionPossib(shardID:str, isOrder:bool, price:float, data:dict, depth=0, visited=None):
        input_1 = data["input_1"]
        input_2 = data["input_2"]
        visited = [] if visited is None else visited
        if shardID in visited: return None
        price_calc = AttrHelper.getShardsPrices(*visited[1:], isOrder=isOrder)
        if price_calc > price + 1000:
            # print(f"Price of shard {shardID} is too high! ({price_calc} > {price})  {len(visited)}")
            return None
        visited.append(shardID)
        fuseList = {}
        for inpt in [input_1, input_2]:
            if not inpt: continue
            if "data" in inpt.keys():
                if inpt["type"] == "and":
                    validShards = AttrHelper.getValidShards(**inpt["data"][0], **inpt["data"][1])
                else:
                    v1 = AttrHelper.getValidShards(**inpt["data"][0])
                    v2 = AttrHelper.getValidShards(**inpt["data"][1])
                    v1.extend(v2)
                    validShards = list(set(v1))
            else:
                validShards = AttrHelper.getValidShards(**inpt)
                if "shard" in inpt.keys():
                    validShards = AttrHelper.getFusionPossib(inpt["shard"], isOrder, price, AttrHelper.getShard(inpt["shard"])["fusion"],  depth=depth+1, visited=visited.copy())

            if not validShards:
                MsgText.warning(f"ValidShards are empty! {inpt}")
                continue
            cheapest = AttrHelper.getCheapestShard(*validShards, isOrder=isOrder)
            fuseList[shardID] = cheapest
        return validShardList

class AttrBuyHelperPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Attr-Buy-Helper", buttonText="Attr Buy Helper")

        self.treeview = tk.TreeView(self.contentFrame, SG)
        self.treeview.setTableHeaders("ID", "Amount-Max", "Price/Shard", "price-Max", "Instruction", "Buff-Info")
        self.treeview.placeRelative(changeHeight=-25)

        self.isOrderCheck = tk.Checkbutton(self.contentFrame, SG)
        self.isOrderCheck.onSelectEvent(self.updateTreeView)
        self.isOrderCheck.setText("Is Order: ")
        self.isOrderCheck.placeRelative(stickDown=True, fixHeight=25, fixWidth=200)
    def updateTreeView(self):
        self.treeview.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            return
        sorters = []
        isOrder = self.isOrderCheck.getState()
        for name, data in iterDict(ConfigFile.ATTR_SHARD_DATA):
            price = None
            inst = None
            product = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(name)
            if product is not None:
                if isOrder:
                    price = product.getInstaSellPrice()
                else:
                    price = product.getInstaBuyPrice()
                price = applyBazaarTax(price)

                inst = "Buy from Bazaar"

            if name != "SHARD_LAPIS_CREEPER": continue
            valid = []
            AttrHelper.getFusionPossib(name, isOrder, price, data["fusion"], valid)
            print(len(valid))
            print(valid)

            #if price is None or (fusePrice is not None and fusePrice < price):
            #    MsgText.info(f"Fuse price is smaller: {price} -> {fusePrice}, {types}")
            #    price = fusePrice
            #    inst = f"Fuse: {types}"


            sorters.append(
                Sorter(
                    sortKey="price",

                    inst=inst,
                    needed=getShardsNeeded(data["rarity"]),
                    id=name,
                    price=price,
                    buff=data["effect"],
                )
            )

        sorters.sort()

        for sorter in sorters:
            self.treeview.addEntry(
                sorter["id"],
                sorter["needed"],
                parsePrizeToStr(sorter["price"]),
                None if sorter["price"] is None else parsePrizeToStr(sorter["price"]*sorter["needed"]),
                sorter["inst"],
                sorter["buff"]
            )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()
