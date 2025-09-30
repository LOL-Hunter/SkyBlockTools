import os

from core.jsonConfig import JsonConfig

import tksimple as tk

from core.constants import STYLE_GROUP as SG, Path, API, BazaarItemID
from core.logger import MsgText
from core.settings import Config
from core.skyMath import applyBazaarTax
from core.skyMisc import iterDict, Sorter
from core.skyMisc import parsePrizeToStr
from core.widgets import CustomPage


class PestProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Pest Profit Page", buttonText="Pest Profit")

        self.selectedPest = None
        self.pestNameMetaSorter = {}

        self.rarePestChances = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "garden_pest_chances_rare.json"))
        self.commonPestChances = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "garden_pest_chances_common.json"))

        self.treeView = tk.TreeView(self.contentFrame, SG)
        self.treeView.onSingleSelectEvent(self.onSelect)
        self.treeView.setTableHeaders("Pest-Name", "Average-Profit-Per-Pest")
        self.treeView.placeRelative(changeHeight=-25, changeWidth=-300)

        self.frame = tk.LabelFrame(self.contentFrame, SG)
        self.frame.setText("Pest-Details")
        self.frame.placeRelative(fixWidth=300, stickRight=True, changeHeight=-25)

        self.innerFrame1 = tk.LabelFrame(self.frame, SG)
        self.innerFrame1.setText("Common Loot")
        self.commonList = tk.Listbox(self.innerFrame1, SG)
        self.commonList.placeRelative(changeWidth=-5, changeHeight=-20)
        self.innerFrame1.placeRelative(fixY=25, fixHeight=100)

        self.innerFrame2 = tk.LabelFrame(self.frame, SG)
        self.innerFrame2.setText("Rare Loot")
        self.rareList = tk.Listbox(self.innerFrame2, SG)
        self.rareList.placeRelative(changeWidth=-5, changeHeight=-20)
        self.innerFrame2.placeRelative(fixY=125, fixHeight=200)

        self.fullProfit = tk.Label(self.frame, SG)
        self.fullProfit.setFont(15)
        self.fullProfit.placeRelative(fixY=325, fixHeight=25)

        self.pestName = tk.Label(self.frame, SG)
        self.pestName.setFont(19)
        self.pestName.placeRelative(fixHeight=25, changeWidth=-5)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG).setSelected()
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.onSelectEvent(self.updateTreeView)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=0)

        self.farmingFortune = tk.TextEntry(self.contentFrame, SG)
        self.farmingFortune.setText("Farming-Fortune:")
        self.farmingFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["farming_fortune"])
        self.farmingFortune.getEntry().onUserInputEvent(self.updateTreeView)
        self.farmingFortune.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.cropFortune = tk.TextEntry(self.contentFrame, SG)
        self.cropFortune.setText("Crop-Fortune:")
        self.cropFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["crop_fortune"])
        self.cropFortune.getEntry().onUserInputEvent(self.updateTreeView)
        self.cropFortune.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=300)

        self.petChance = tk.TextEntry(self.contentFrame, SG)
        self.petChance.setText("Pet-Luck:")
        self.petChance.setValue(Config.SETTINGS_CONFIG["pest_profit"]["pet_luck"])
        self.petChance.getEntry().onUserInputEvent(self.updateTreeView)
        self.petChance.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=450)

        self.pestsActive = tk.Checkbutton(self.contentFrame, SG)
        self.pestsActive.setText("Bonus-Farming-Fortune")
        self.pestsActive.onSelectEvent(self.onSelect)
        self.pestsActive.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=600)

        self.noneSelected = tk.Label(self.frame, SG)
        self.noneSelected.setText("No Pest Selected!")
    def onSelect(self):
        sel = self.treeView.getSelectedItem()
        if sel is not None:
            self.selectedPest = sel["Pest-Name"]
        elif self.selectedPest is None:
            return
        self.updateTreeView()
        sorter = self.pestNameMetaSorter[self.selectedPest]
        self.pestName.setText(self.selectedPest)

        self.commonList.clear()
        self.rareList.clear()

        self.commonList.add(f"{sorter['itemID']}")
        self.commonList.add(f"Amount-Per-Pest: {sorter['amount']}")
        self.commonList.add(f"Sell-Price: {parsePrizeToStr(sorter['profitCommonSingle'])}")
        self.commonList.add(f"Sell-Price-x{sorter['amount']}: {parsePrizeToStr(sorter['profitCommon'])}")

        self.fullProfit.setText(f"Profit per Pest: {parsePrizeToStr(sorter['profit'])}")

        for sorter in sorter["profitRareSorter"]:
            self.rareList.add(f"{sorter['itemID']}")
            self.rareList.add(f"Chance: {round(sorter['raw_chance'], 2)}% -> {round(sorter['chance'], 2)}%")
            self.rareList.add(f"Average-Pests: {round(sorter['rawAverageNeededPestsForARareDrop'], 2)} -> {round(sorter['averageNeededPestsForARareDrop'], 2)}")
            self.rareList.add(f"Sell-Price: {parsePrizeToStr(sorter['profit_full'])}")
            self.rareList.add(f"Sell-Price / Pest: {parsePrizeToStr(sorter['profit'])}")
            self.rareList.add(f"")
            self.rareList.add(f"")
    def updateTreeView(self):
        self.treeView.clear()
        if API.SKYBLOCK_BAZAAR_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        if API.SKYBLOCK_AUCTION_API_PARSER is None:
            tk.SimpleDialog.askError(self.master, "Cannot calculate! No API data available!")
            return
        isPestsActive = self.pestsActive.getState()
        if self.selectedPest is None:
            self.noneSelected.placeRelative(changeWidth=-5, changeHeight=-20)
        else:
            self.noneSelected.placeForget()
        farmingFortune = self.farmingFortune.getValue()
        if farmingFortune.isnumeric():
            farmingFortune = int(farmingFortune)
            Config.SETTINGS_CONFIG["pest_profit"]["farming_fortune"] = farmingFortune
            Config.SETTINGS_CONFIG.save()
        elif farmingFortune == "": farmingFortune = 0
        else:
            self.cropFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["farming_fortune"])
            tk.SimpleDialog.askError(self.master, f"Wrong Farming Fortune value! Must be > 0.")
        cropFortune = self.cropFortune.getValue()

        if cropFortune.isnumeric():
            cropFortune = int(cropFortune)
            Config.SETTINGS_CONFIG["pest_profit"]["crop_fortune"] = cropFortune
            Config.SETTINGS_CONFIG.save()
        elif cropFortune == "": cropFortune = 0
        else:
            self.cropFortune.setValue(Config.SETTINGS_CONFIG["pest_profit"]["crop_fortune"])
            tk.SimpleDialog.askError(self.master, f"Wrong Crop Fortune value! Must be > 0.")
        petLuck = self.petChance.getValue()

        if petLuck.isnumeric():
            petLuck = int(petLuck)
            Config.SETTINGS_CONFIG["pest_profit"]["pet_luck"] = petLuck
            Config.SETTINGS_CONFIG.save()
        elif petLuck == "": petLuck = 0
        else:
            self.petChance.setValue(Config.SETTINGS_CONFIG["pest_profit"]["pet_luck"])
            tk.SimpleDialog.askError(self.master, f"Wrong Pet Luck value! Must be > 0.")
        if isPestsActive: farmingFortune += 200
        """
        The Pest chances are given in percenteges.
        Rare Drops are drops with a basechance lower 5%
        Common Drops are drops with a basechance higher than 5%
        """

        metaSorters = []
        for pestName in self.rarePestChances.keys():
            sorters = []
            for singleDropItemID, dropChance in iterDict(self.rarePestChances[pestName]):
                dropChance, amount = dropChance

                if singleDropItemID in BazaarItemID: # Bazaar Item!
                    item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(singleDropItemID)

                    if self.useSellOffers.getState():  # use sell Offer
                        itemSellPrice = item.getInstaBuyPrice()
                    else:  # insta sell
                        itemSellPrice = item.getInstaSellPrice()
                    itemSellPrice = applyBazaarTax(itemSellPrice)
                else:
                    rarity = None
                    if singleDropItemID.endswith("epic"):
                        singleDropItemID = singleDropItemID.replace("_epic", "")
                        rarity = "EPIC"
                    if singleDropItemID.endswith("legendary"):
                        singleDropItemID = singleDropItemID.replace("_legendary", "")
                        rarity = "LEGENDARY"
                    active = API.SKYBLOCK_AUCTION_API_PARSER.getBINAuctionByID(singleDropItemID)

                    auctSorters = []
                    for auction in active:
                        if rarity is not None:
                            if rarity.lower() != auction.getRarity().lower():
                                continue
                        auctSorters.append(
                            Sorter(
                                sortKey="profit",
                                profit=auction.getPrice(),
                            )
                        )
                    auctSorters.sort()
                    if len(auctSorters) == 0:
                        itemSellPrice = 0
                        MsgText.error(f"Could not calculate price for {singleDropItemID}.")
                    else:
                        itemSellPrice = auctSorters[-1]["profit"]

                if "PET" in singleDropItemID:
                    rareDropChance = dropChance * (1 + (farmingFortune + cropFortune + petLuck) / 600)
                else:
                    rareDropChance = dropChance * (1 + (farmingFortune + cropFortune) / 600)
                averageNeededPestsForARareDrop = 1 / (rareDropChance / 100)
                rawAverageNeededPestsForARareDrop = 1 / (dropChance / 100)
                pestProfitRare = (rareDropChance / 100) * itemSellPrice * amount

                sorters.append(
                    Sorter(
                        sortKey="profit",

                        itemID=singleDropItemID,
                        pestName=pestName,
                        averageNeededPestsForARareDrop=averageNeededPestsForARareDrop,
                        rawAverageNeededPestsForARareDrop=rawAverageNeededPestsForARareDrop,
                        profit=pestProfitRare,
                        profit_full=itemSellPrice,
                        chance=rareDropChance,
                        raw_chance=dropChance,
                        amount=amount,
                    )
                )
            sorters.sort()
            product = self.commonPestChances[pestName]["id"]
            base_amount = self.commonPestChances[pestName]["base_amount"]
            gain_additional_ff = self.commonPestChances[pestName]["gain_additional_ff"]

            item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(product)

            if self.useSellOffers.getState():  # use sell Offer
                itemSellPrice = item.getInstaBuyPrice()
            else:  # insta sell
                itemSellPrice = item.getInstaSellPrice()
            itemSellPrice = applyBazaarTax(itemSellPrice)

            pestProfitCommon = itemSellPrice * (base_amount+farmingFortune/gain_additional_ff)

            metaSorters.append(
                Sorter(
                    sortKey="profit",
                    itemID=product,
                    amount=(base_amount+farmingFortune/gain_additional_ff),
                    pestName=pestName,
                    profitRareSorter=sorters,
                    profitCommon=pestProfitCommon,
                    profitCommonSingle=itemSellPrice,
                    profit=pestProfitCommon + sum([i["profit"] for i in sorters])
                )
            )
            self.pestNameMetaSorter[pestName] = metaSorters[-1]
        metaSorters.sort()
        for sorter in metaSorters:
            self.treeView.addEntry(
                sorter["pestName"],
                parsePrizeToStr(sorter["profit"])
            )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.onSelect  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()