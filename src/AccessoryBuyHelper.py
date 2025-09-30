import os
from threading import Thread
from core.jsonConfig import JsonConfig
import tksimple as tk

from core.constants import STYLE_GROUP as SG, Color, API, Path, MAGIC_POWDER
from core.logger import MsgText
from core.settings import Config
from core.skyMisc import parsePrizeToStr, Sorter, requestProfilesHypixelAPI, requestProfileHypixelAPI, parsePriceFromStr
from core.widgets import CustomPage


class AccessoryBuyHelperAccount(tk.Dialog):
    def __init__(self, page, master, updHook, data=None):
        super().__init__(master, SG)
        self.page = page
        self.master = master
        self.updHook = updHook
        self.profile = {"uuid":"", "profile":""}
        self.accessories = [] if data is None else data["accessories"]
        self.inactive_accessories = [] if data is None else data["inactive_accessories"]
        self.setWindowSize(800, 800)
        self.setMinSize(500, 800)
        self.setCloseable(False)
        self.setTopmost(False)

        if data is None:
            self.edit = False
            self.setTitle("Account")
        else:
            self.edit = True
            self.setTitle(f"{data['name']}-Account")

        self.treeView = tk.TreeView(self, SG)
        self.treeView.setTableHeaders("Name", "Recomb", "Enrichment", "Rarity")
        self.treeView.placeRelative(fixX=200, changeHeight=-100)

        self.toolFrame = tk.LabelFrame(self, group=SG)
        self.toolFrame.setText("Account")
        self.toolFrame.placeRelative(fixWidth=200)

        self.nameEntry = tk.TextEntry(self.toolFrame, group=SG)
        self.nameEntry.setText("Name:")
        if data is not None:
            self.nameEntry.getEntry().setValue(data['name'])
            self.nameEntry.getEntry().setDisabled()

            self.profile = data["profile"]

        self.nameEntry.placeRelative(fixWidth=195, fixHeight=25)

        self.slotsFrame = tk.LabelFrame(self.toolFrame, SG)
        self.slotsFrame.setText("Slots [0]")
        self.slotsFrame.place(0, 25, 195, 95+27)

        tk.Label(self.slotsFrame, SG).setText("Redstone Collec:").place(0, 0, 106, 25)
        tk.Label(self.slotsFrame, SG).setText("Redstone Miner:").place(0, 25, 106, 25)
        tk.Label(self.slotsFrame, SG).setText("Community Shop:").place(0, 50, 106, 25)
        tk.Label(self.slotsFrame, SG).setText("Jacobus Slots:").place(0, 75, 106, 25)

        self.redsColDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 0, 86, 25).onSelectEvent(self.updateTreeView)
        self.redsMinerDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 25, 86, 25).onSelectEvent(self.updateTreeView)
        self.communityDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 50, 86, 25).onSelectEvent(self.updateTreeView)
        self.jacobusDrop = tk.DropdownMenu(self.slotsFrame, SG).place(106, 75, 86, 25).onSelectEvent(self.updateTreeView)

        self.redsColDrop.setOptionList([f"lvl{k} ({v} Slots)" for k, v in page.slotsConfig["redstone_collection"].items()])
        self.redsMinerDrop.setOptionList(["0", "1", "2", "3", "4"])
        self.communityDrop.setOptionList([f"lvl{k} ({v} Slots)" for k, v in page.slotsConfig["community_centre"].items()])
        self.jacobusDrop.setOptionList([f"{i} Slots" for i in range(0, 200, 2)])

        if data is not None:
            self.redsColDrop.setValueByIndex(data["redstone_collection"])
            self.redsMinerDrop.setValueByIndex(data["redstone_miner"])
            self.communityDrop.setValueByIndex(data["community_centre"])
            self.jacobusDrop.setValueByIndex(data["jacobus"])
            self.profile = data["profile"]
        else:
            self.redsColDrop.setValueByIndex(0)
            self.redsMinerDrop.setValueByIndex(0)
            self.communityDrop.setValueByIndex(0)
            self.jacobusDrop.setValueByIndex(0)

        self.accessoriesFrame = tk.LabelFrame(self.toolFrame, SG)
        self.accessoriesFrame.setText("Accessories")
        self.accessoriesFrame.place(0, 174, 195, 100+20)

        self.addBtn = tk.Button(self.accessoriesFrame, SG).setText("Add Accessory").place(0, 0, 192, 25).setCommand(self.openSearch)
        self.editBtn = tk.Button(self.accessoriesFrame, SG).setText("Edit Accessory").place(0, 25, 192, 25).setDisabled().setCommand(self.openEditDialog)
        self.delBtn = tk.Button(self.accessoriesFrame, SG).setText("Remove Accessory").place(0, 50, 192, 25).setDisabled()
        self.impBtn = tk.Button(self.accessoriesFrame, SG).setText("Import Accessories").place(0, 75, 192, 25).setCommand(self.importAccessories)

        if data is None: self.cancel = tk.Button(self.toolFrame, SG).setText("Cancel").placeRelative(fixHeight=25, changeWidth=-3, stickDown=True, changeY=-45).setCommand(self.destroy)
        self.close = tk.Button(self.toolFrame, SG).setText("Save & Close").placeRelative(fixHeight=25, changeWidth=-3, stickDown=True, changeY=-20).setCommand(self.close)

        if self.edit: self.updateTreeView()
        self.show()
    def openSearch(self):
        pass
    def openEditDialog(self):
        root = tk.Dialog(self)





        root.show()
    def importAccessories(self):
        def request():
            """ ### old ###

            url = f"https://sky.lea.moe/api/v2/talismans/{playerName}/{profileName.lower()}"
            try:
                val = getReq(url)
                val = val.json()
            except json.decoder.JSONDecodeError:
                tk.SimpleDialog.askError(self.master, f"{val.text}")
                return
            except ConnectionError:
                tk.SimpleDialog.askError(self.master, "An Exception occurred while connecting to API.\nCheck your internet connection.")
                return
            except ReadTimeout:
                tk.SimpleDialog.askError(self.master, "Timeout Exception occurred!")
                return
            if "error" in val.keys():
                tk.SimpleDialog.askError(self.master)
                return
            self.accessories.clear()"""

            profilesData = requestProfilesHypixelAPI(self.master, Config, uuid=self.profile["uuid"])
            if profilesData is None: return

            chooseData = tk.SimpleDialog.chooseFromList(self, values=[f"{i[0]} on {i[1]}" for i in zip(profilesData.getGameModes(), profilesData.getServerNames())], useIndexInstead=True, group=SG)
            if chooseData is None: return
            self.profile["account_id"] = profilesData.getProfileIDs()[chooseData]

            data = requestProfileHypixelAPI(self.master, Config, accUuid=self.profile["account_id"])
            if data is None: return
            accessories = data.decodeAccessoriesFromUUID(self.profile["uuid"])
            self.accessories = []
            self.inactive_accessories = []
            for acc in accessories:
                if acc["inactive"]:
                    self.inactive_accessories.append(acc)
                    continue
                self.accessories.append(acc)

            profile = profilesData.getProfiles()[chooseData]
            jacobusSlots = profile["members"][self.profile["uuid"]]["accessory_bag_storage"]["bag_upgrades_purchased"]
            self.jacobusDrop.setValue(f"{jacobusSlots*2} Slots")

            self.save()
            self.updateTreeView()
        if self.nameEntry.getValue() == "":
            tk.SimpleDialog.askError(self, "Please insert Player name!")
            return
        self.nameEntry.setDisabled()
        uuid = tk.SimpleDialog.askString(self, message="uuid:", initialValue=self.profile["uuid"])
        if uuid is None: return

        self.profile = {
            "uuid": uuid.replace("-", ""),
            "account_id": ""
        }
        Thread(target=request).start()
    def check(self):
        if self.nameEntry.getValue() == "":
            tk.SimpleDialog.askError(self.master, "Player name cannot be empty!")
            return False
        return True
    def updateTreeView(self):
        self.treeView.clear()
        self.slotsFrame.setText(f"Slots [{self.getTotalSlots()}]")
        for acc in Config.SETTINGS_CONFIG["accessories"][self.nameEntry.getValue()]["accessories"]:
            self.treeView.addEntry(acc["id"], acc["recomb"], acc["enrichment"], acc["rarity"].lower(), tag="none")
        for acc in Config.SETTINGS_CONFIG["accessories"][self.nameEntry.getValue()]["inactive_accessories"]:
            self.treeView.addEntry(acc["id"], acc["recomb"], acc["enrichment"], acc["rarity"].lower(), tag="inactive")
        self.treeView.setBgColorByTag("none", Color.COLOR_DARK)
        self.treeView.setBgColorByTag("inactive", tk.Color.RED)
    def close(self):
        if self.check():
            self.save()
            self.updHook(self.nameEntry.getValue())
            self.destroy()
    def save(self):
        Config.SETTINGS_CONFIG["accessories"][self.nameEntry.getValue()] = self.getData()
        Config.SETTINGS_CONFIG.save()
    def getData(self):
        return {
            "name":self.nameEntry.getValue(),
            "redstone_collection":self.redsColDrop.getSelectedIndex(),
            "redstone_miner":self.redsMinerDrop.getSelectedIndex(),
            "community_centre":self.communityDrop.getSelectedIndex(),
            "jacobus":self.jacobusDrop.getSelectedIndex(),
            "slots":self.getTotalSlots(),
            "powder":0,
            "profile":self.profile,
            "accessories":self.accessories,
            "inactive_accessories":self.inactive_accessories
        }
    def getTotalSlots(self):
        slots = self.redsMinerDrop.getSelectedIndex()
        slots += list(self.page.slotsConfig["redstone_collection"].values())[self.redsColDrop.getSelectedIndex()]
        slots += list(self.page.slotsConfig["community_centre"].values())[self.communityDrop.getSelectedIndex()]
        slots += self.jacobusDrop.getSelectedIndex() * 2
        return slots
class AccessoryBuyHelperPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Accessory Buy Helper Page", buttonText="Accessory Buy Helper")
        self.master = master

        self.conflictsConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "accessories_conflicts.json"))
        self.soulboundConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "accessories_soulbound.json"))
        self.ignoreConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "accessories_ignore.json"))
        self.slotsConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "accessories_buy_slots.json"))
        self.jacobusPricesConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "accessories_jacobus_prices.json"))
        self.cantRecomb = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "accessories_cannot_recomb.json"))

        self.toolFrame = tk.LabelFrame(self.contentFrame, group=SG)
        self.toolFrame.setText("Tools")
        self.toolFrame.placeRelative(fixWidth=200)

        self.treeView = tk.TreeView(self.contentFrame, group=SG)
        self.treeView.setTableHeaders("Name", "Action", "Price", "PricePerMp")
        self.treeView.placeRelative(fixX=200, changeHeight=-100)

        self.resFrame = tk.LabelFrame(self.contentFrame, group=SG)
        self.resFrame.setText("Result")
        self.resFrame.placeRelative(fixX=200, stickDown=True, fixHeight=100)

        self.statsFrame = tk.LabelFrame(self.resFrame, group=SG)
        self.statsFrame.setText("Stats")
        self.statsFrame.placeRelative(0, 0, 400, 80)

        self.powderPlusLabel = tk.Label(self.statsFrame, SG).setTextOrientation()
        self.powderPlusLabel.setText("Powder Gain: +0")
        self.powderPlusLabel.setFg(tk.Color.GREEN)
        self.powderPlusLabel.setFont(15)
        self.powderPlusLabel.place(0, 0, 390, 25)

        self.newTotalPowderLabel = tk.Label(self.statsFrame, SG).setTextOrientation()
        self.newTotalPowderLabel.setText("New Total Powder: 0")
        self.newTotalPowderLabel.setFg(tk.Color.GREEN)
        self.newTotalPowderLabel.setFont(15)
        self.newTotalPowderLabel.place(0, 25, 390, 25)

        self.buyFrame = tk.LabelFrame(self.resFrame, group=SG)
        self.buyFrame.setText("Cost")
        self.buyFrame.placeRelative(400, 0, 800, 80)

        self.recombLabel = tk.Label(self.buyFrame, SG).setTextOrientation()
        self.recombLabel.setText("Recombs: +0")
        self.recombLabel.setFont(15)
        self.recombLabel.place(0, 0, 400, 25)

        self.slotsLabel = tk.Label(self.buyFrame, SG).setTextOrientation()
        self.slotsLabel.setText("Slots: +0")
        self.slotsLabel.setFont(15)
        self.slotsLabel.place(0, 25, 400, 25)

        self.totalLabel = tk.Label(self.buyFrame, SG).setTextOrientation()
        self.totalLabel.setText("Total: 0 coins")
        self.totalLabel.setFont(15)
        self.totalLabel.place(400, 0, 395, 25)

        self.accFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.accFrame.setText("Account")
        self.accFrame.place(0, 0, 195, 69)

        self.accDrop = tk.DropdownMenu(self.accFrame, group=SG, readonly=True)
        self.accDrop.onSelectEvent(self.changeAccount)
        self.accDrop.place(0, 0, 192, 25)

        self.add = tk.Button(self.accFrame, group=SG)
        self.add.setText("Add")
        self.add.setCommand(self.addNewAccount)
        self.add.place(0, 25, 64, 25)

        self.edit = tk.Button(self.accFrame, group=SG)
        self.edit.setText("Edit")
        self.edit.setCommand(self.editAccount)
        self.edit.place(64, 25, 64, 25)

        self.rem = tk.Button(self.accFrame, group=SG)
        self.rem.setText("Remove")
        self.rem.setCommand(self.removeAccount)
        self.rem.place(64*2, 25, 64, 25)

        self.investFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.investFrame.setText("Invest")
        self.investFrame.place(0, 69, 195, 69)

        self.investEntry = tk.TextEntry(self.investFrame, group=SG)
        self.investEntry.setText("Invest (coins):")
        self.investEntry.getEntry().onUserInputEvent(self.updateHelper)
        self.investEntry.placeRelative(fixWidth=192, fixHeight=25)

        self.statsFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.statsFrame.setText("Stats")
        self.statsFrame.place(0, 138, 195, 200)

        self.statsText = tk.Text(self.statsFrame, SG, readOnly=True)
        self.statsText.placeRelative(changeHeight=-20, changeWidth=-5)

        self.filterFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.filterFrame.setText("Filter")
        self.filterFrame.place(0, 338, 195, 200)

        self.filterNotBuyableCheck = tk.Checkbutton(self.filterFrame, SG)
        self.filterNotBuyableCheck.setSelected()
        self.filterNotBuyableCheck.onSelectEvent(self.updateHelper)
        self.filterNotBuyableCheck.setText("Hide 'Not Buyable' Items")
        self.filterNotBuyableCheck.place(0, 0, 192, 25)

        self.compareFrame = tk.LabelFrame(self.toolFrame, group=SG)
        self.compareFrame.setText("Compare")
        self.compareFrame.place(0, 538, 192, 125)

        tk.Label(self.compareFrame, group=SG).setText("Compare Player:").place(0, 0, 192-5, 25)
        self.compPlay1 = tk.DropdownMenu(self.compareFrame).place(0, 25, 192-5, 25)
        tk.Label(self.compareFrame, group=SG).setText("With Player:").place(0, 50, 192-5, 25)
        self.compPlay2 = tk.DropdownMenu(self.compareFrame).place(0, 75, 192-5, 25)
        tk.Button(self.compareFrame, group=SG).setCommand(self.compare).setText("Compare ...").place(0, 100, 192-5, 25)

        self.updateAccounts(None)
        self.accessories = None
    def compare(self):
        pl1 = self.compPlay1.getValue()
        pl2 = self.compPlay2.getValue()
        if pl1 == "" or pl2 == "": return
        if pl1 == pl2: return
        root = tk.Toplevel(self.master, group=SG)
        tv = tk.TreeView(root, group=SG)
        tv.setTableHeaders("Name", pl1, pl2)
        p1Acc = {acc["id"]:acc for acc in Config.SETTINGS_CONFIG["accessories"][pl1]["accessories"]}
        p2Acc = {acc["id"]:acc for acc in Config.SETTINGS_CONFIG["accessories"][pl2]["accessories"]}
        for k, v in zip(p1Acc.keys(), p1Acc.values()):
            if k in p2Acc.keys():
                p1Str = "X"
                p2Str = "X"
                if v["recomb"] != p2Acc[k]["recomb"]:
                    p1Str += ("R" if v["recomb"] else "")
                    p2Str += ("R" if p2Acc[k]["recomb"] else "")
                if v["enrichment"] != p2Acc[k]["enrichment"]:
                    p1Str += ("R" if v["recomb"] else "")
                    p2Str += ("R" if p2Acc[k]["recomb"] else "")
                if v["recomb"] == p2Acc[k]["recomb"] and v["rarity"] != p2Acc[k]["rarity"]:
                    p1Str += f"({v['rarity']})"
                    p2Str += f"({p2Acc[k]['rarity']})"
                if p1Str+p2Str == "XX": continue
                tv.addEntry(k, p1Str, p2Str)
                continue
            tv.addEntry(k, f"X", "")
        for k, v in zip(p2Acc.keys(), p2Acc.values()):
            if k in p1Acc.keys():
                p1Str = "X"
                p2Str = "X"
                if v["recomb"] != p2Acc[k]["recomb"]:
                    p1Str += ("R" if p1Acc[k]["recomb"] else "")
                    p2Str += ("R" if v["recomb"] else "")
                if v["enrichment"] != p2Acc[k]["enrichment"]:
                    p1Str += ("R" if p1Acc[k]["recomb"] else "")
                    p2Str += ("R" if v["recomb"] else "")
                if v["recomb"] == p2Acc[k]["recomb"] and v["rarity"] != p2Acc[k]["rarity"]:
                    p1Str += f"({p1Acc[k]['rarity']})"
                    p2Str += f"({v['rarity']})"
                if p1Str + p2Str == "XX": continue
                tv.addEntry(k, p1Str, p2Str)
                continue
            tv.addEntry(k, f"", "X")
        tv.placeRelative()
        root.show()
    def removeAccount(self):
        name = self.accDrop.getValue()
        if name == "": return
        if tk.SimpleDialog.askOkayCancel(self.master, f"Delete data from player {name}?"):
            Config.SETTINGS_CONFIG["accessories"].pop(name)
            Config.SETTINGS_CONFIG.save()
            self.accDrop.clear()
            self.updateAccounts(None)
            self.updateHelper()
    def addNewAccount(self):
        account = AccessoryBuyHelperAccount(self, self.master, self.updateAccounts)
    def editAccount(self):
        name = self.accDrop.getValue()
        if name == "": return
        account = AccessoryBuyHelperAccount(self, self.master, self.updateAccounts, data=Config.SETTINGS_CONFIG["accessories"][name])
    def changeAccount(self):
        self.updateHelper()
    def getPowder(self, data):
        powder = 0
        for i in data:
            rarity = i["rarity"].upper() # {'id': 'PARTY_HAT_SLOTH', 'recomb': True, 'enrichment': True, 'rarity': 'VERY', 'inactive': False}
            if rarity not in MAGIC_POWDER.keys():
                MsgText.error(f"Could not parse Rarity: {i}")
                continue
            powder += MAGIC_POWDER[rarity]
        return powder
    def updateAccounts(self, name):
        accs = list(Config.SETTINGS_CONFIG["accessories"].keys())
        self.accDrop.setOptionList(accs)
        self.compPlay1.setOptionList(accs)
        self.compPlay2.setOptionList(accs)
        if name is not None:
            self.accDrop.setValue(name)
            self.updateHelper()
    def getMagicPoderDiffToNext(self, old):
        rarities = list(MAGIC_POWDER.keys())
        new = rarities[rarities.index(old) + 1]
        return MAGIC_POWDER[new] - MAGIC_POWDER[old]
    def getMagicPoderDiff(self, old, new):
        return MAGIC_POWDER[new] - MAGIC_POWDER[old]
    def updateHelper(self):
        self.accessories = [{"id":i.getID(), "rarity":(i.getRarity() if i.getRarity() is not None else "COMMON")} for i in API.SKYBLOCK_ITEM_API_PARSER.getItems() if i.getCategory() == "ACCESSORY"]
        self.treeView.clear()
        self.statsText.clear()
        name = self.accDrop.getValue()

        self.powderPlusLabel.setText(f"Powder Gain: +{0}")
        self.recombLabel.setText(f"Recombs: +{0} ({0} coins)")
        self.slotsLabel.setText(f"Slots: +{0} ()")
        self.totalLabel.setText(f"Total: {0} coins")
        self.newTotalPowderLabel.setText(f"New Total Powder: {0}")

        if name == "": return
        data = Config.SETTINGS_CONFIG["accessories"][name]
        slots = data["slots"]
        slotsUsed = len(data["accessories"])
        powderAllOld = self.getPowder(data["accessories"])
        ownedIDs = [i["id"] for i in data["accessories"]]
        notOwned = []
        notOwnedSoulbound = []
        piggies = [
            "BROKEN_PIGGY_BANK",
            "CRACKED_PIGGY_BANK",
            "PIGGY_BANK"
        ]
        isPiggyPreset = False
        budget = parsePriceFromStr(self.investEntry.getValue())
        filterNotBuyableCheck = self.filterNotBuyableCheck.getState()

        recomb = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("RECOMBOBULATOR_3000")
        if recomb is None:
            tk.SimpleDialog.askError(self.master, "Error getting 'RECOMBOBULATOR_3000' price from api!")
            return
        recombPrice = recomb.getInstaSellPrice() + .1
        if recombPrice == 0:
            tk.SimpleDialog.askError(self.master, "Error getting 'RECOMBOBULATOR_3000' price from api!")
            return

        self.statsText.addLine(f"Name: {name}")
        self.statsText.addLine(f"Slots used: [{slotsUsed}/{slots}]")
        self.statsText.addLine(f"Magic Powder: {powderAllOld}")

        sorters = []

        for acc in self.accessories:
            id_ = acc["id"]
            if id_ in piggies:
                isPiggyPreset = True
        # ignore acc
            if id_ in self.ignoreConfig: continue
        # remove soulbound
            if id_ not in ownedIDs:
                if id_ in self.soulboundConfig:
                    notOwnedSoulbound.append(acc)
                else:
                    notOwned.append(acc)
        # remove conflicts
        for acc in data["accessories"]:
            id_ = acc["id"]
            for conflict in self.conflictsConfig:
                if id_ in conflict:
                    for rem in conflict[:conflict.index(id_)]:
                        for i, val in enumerate(notOwned.copy()):
                            if val["id"] == rem:
                                notOwned.remove(val)
                                break
                    break
        ### NOT OWNED accessories ###
        for acc in notOwned:
            if isPiggyPreset and acc["id"] in piggies: continue
            price = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(acc["id"])
            price.sort()
            price = price[-1].getPrice() if len(price) > 0 else None
            rarity = acc["rarity"].upper()
            powder = MAGIC_POWDER[rarity]

            pricePerMP = None if price is None else (price/powder)

            recomb = False
            action = "buy"

            #check recomb
            if price is not None:
                price2 = price + recombPrice
                rarities = list(MAGIC_POWDER.keys())
                rarity2 = rarities[rarities.index(rarity) + 1]
                powder2 = MAGIC_POWDER[rarity2]

                pricePerMP2 = None if price2 is None else (price2/powder2)

                if pricePerMP2 < pricePerMP:
                    action = "buy & Recomb"
                    pricePerMP = pricePerMP2
                    price = price2
                    recomb = True
            if price is None:
                action = "Not buyable!"
                if filterNotBuyableCheck:
                    continue

            sorters.append(
                Sorter(
                    sortKey="pricePerMP",
                    id=acc["id"],
                    pricePerMP=pricePerMP,
                    price=price,
                    powder=powder,
                    rarity=rarity,
                    action=action,
                    slots=None,
                    recomb=recomb,
                )
            )
        sorters.sort()

        remaingSlots = slots - slotsUsed

        if remaingSlots <= 0:
            for i, sorter in enumerate(sorters[::-1][remaingSlots+1:]):
                jacobusSlotPrice = self.jacobusPricesConfig[data["jacobus"] + 1 + i//2] / 2
                sorter["price"] = sorter["price"]+jacobusSlotPrice
                sorter["action"] += f" & buy Slot ({parsePrizeToStr(jacobusSlotPrice)})"
                sorter["pricePerMP"] = sorter["price"] / sorter["powder"]
                sorter["slots"] = (1, jacobusSlotPrice)


        ### OWNED accessories ###
        for acc in data["accessories"]:

            price = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(acc["id"])
            price.sort()
            price = price[-1].getPrice() if len(price) > 0 else None
            rarity = acc["rarity"].upper()
            powder = MAGIC_POWDER[rarity]

            # check recomb

            if acc["recomb"] or acc["id"] in self.cantRecomb: continue
            rarities = list(MAGIC_POWDER.keys())
            rarity2 = rarities[rarities.index(rarity) + 1]
            powder2diff = MAGIC_POWDER[rarity2] - powder
            pricePerMP = recombPrice / powder2diff
            price2 = recombPrice
            action = "recomb"

            sorters.append(
                Sorter(
                    sortKey="pricePerMP",
                    id=acc["id"],
                    pricePerMP=pricePerMP,
                    price=price2,
                    powder=powder,
                    rarity=rarity2,
                    action=action,
                    slots=None,
                    recomb=True
                )
            )
            if isPiggyPreset and acc["id"] in piggies: continue
            # check upgrade
            id_ = acc["id"]
            for conflict in self.conflictsConfig:
                if id_ in conflict:
                    for i, upgradedacc in enumerate(conflict[conflict.index(id_)+1:]):
                        rarityNew = None

                        for acc2 in self.accessories:
                            if acc2["id"] == upgradedacc:
                                rarityNew = acc2["rarity"]
                                break
                        if rarityNew is None:
                            print("Not found!", upgradedacc)
                            continue
                        diff = self.getMagicPoderDiff(rarity, rarityNew)

                        upgradedPrice = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(upgradedacc)
                        upgradedPrice.sort()
                        upgradedPrice = upgradedPrice[-1].getPrice() if len(upgradedPrice) > 0 else None

                        if upgradedPrice is None: continue
                        if price is None: continue

                        priceDiff = upgradedPrice - price
                        if not diff:
                            print(id_, upgradedacc)
                            continue
                        pricePerMP = priceDiff / diff

                        sorters.append(
                            Sorter(
                                sortKey="pricePerMP",
                                id=acc["id"],
                                pricePerMP=pricePerMP,
                                price=priceDiff,
                                powder=diff,
                                rarity=rarityNew,
                                recomb=False,
                                slots=None,
                                action=f"upgrade -> {upgradedacc}",
                            )
                        )

        sorters.sort()

        costAll = 0
        powderAll = 0
        recombCount = 0
        slotCount = 0
        slotPrice = 0

        for acc in sorters[::-1]:
            costAll += 0 if acc["price"] is None else acc["price"]
            powderAll += acc["powder"]
            recombCount += 1 if acc["recomb"] and acc["id"] not in self.cantRecomb else 0
            if acc["slots"] is not None:
                slotCount += acc["slots"][0]
                slotPrice += acc["slots"][1]
            if budget is not None and costAll > budget: break # TODO recomb price not included

            self.treeView.addEntry(acc["id"], acc["action"], parsePrizeToStr(acc["price"]), parsePrizeToStr(acc["pricePerMP"]))

        if not powderAll:
            self.powderPlusLabel.setFg(Color.COLOR_WHITE)
        else:
            self.powderPlusLabel.setFg(tk.Color.GREEN)

        self.powderPlusLabel.setText(f"Powder Gain: +{powderAll}")
        self.recombLabel.setText(f"Recombs: +{recombCount} ({parsePrizeToStr(recombPrice * recombCount)})")
        self.slotsLabel.setText(f"Slots: +{slotCount} ({parsePrizeToStr(slotPrice)})")
        self.totalLabel.setText(f"Total: {parsePrizeToStr(costAll)}")
        self.newTotalPowderLabel.setText(f"New Total Powder: {powderAll+powderAllOld}")
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateHelper  # hook to update tv on new API-Data available
        self.placeRelative()
        self.placeContentFrame()
        self.updateHelper()