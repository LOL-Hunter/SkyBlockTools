import os

from core.jsonConfig import JsonConfig

import tksimple as tk
from core.constants import STYLE_GROUP as SG, Path, API
from core.settings import Config
from core.settings import SettingsGUI
from core.skyMath import applyBazaarTax
from core.skyMisc import (
    parsePrizeToStr,
    parseTimeFromSec,
    iterDict,
    Sorter
)
from core.widgets import CustomPage


class ComposterProfitPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Composter-Profit", buttonText="Composter Profit")
        self.currentParser = None

        self.useBuyOffers = tk.Checkbutton(self.contentFrame, SG)
        self.useBuyOffers.setText("Use-Buy-Offers")
        self.useBuyOffers.setSelected()
        self.useBuyOffers.onSelectEvent(self.updateTreeView)
        self.useBuyOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150)

        self.useSellOffers = tk.Checkbutton(self.contentFrame, SG)
        self.useSellOffers.setText("Use-Sell-Offers")
        self.useSellOffers.setSelected()
        self.useSellOffers.onSelectEvent(self.updateTreeView)
        self.useSellOffers.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.openSettings = tk.Button(self.contentFrame, SG)
        self.openSettings.setText("Composter-Settings")
        self.openSettings.setCommand(self.openComposterSettings)
        self.openSettings.placeRelative(fixHeight=25, stickDown=True, fixWidth=150, fixX=150)

        self.matterLf = tk.LabelFrame(self.contentFrame, SG)
        self.matterLf.setText("Plant Matter [coins per matter]")
        self.matterLb = tk.Listbox(self.matterLf, SG)
        self.matterLb.onSelectEvent(self.onListboxSelect, args=["matter"])
        self.matterLb.placeRelative(changeWidth=-5, changeHeight=-25)
        self.matterLf.placeRelative(fixWidth=300, fixHeight=300, centerX=True, changeX=-150)

        self.fuelLf = tk.LabelFrame(self.contentFrame, SG)
        self.fuelLf.setText("Fuel [coins per fuel]")
        self.fuelLb = tk.Listbox(self.fuelLf, SG)
        self.fuelLb.onSelectEvent(self.onListboxSelect, args=["fuel"])
        self.fuelLb.placeRelative(changeWidth=-5, changeHeight=-25)
        self.fuelLf.placeRelative(fixWidth=300, fixHeight=300, centerX=True,changeX=+150)

        self.textLf = tk.LabelFrame(self.contentFrame, SG)
        self.textLf.setText("Info")
        self.textT = tk.Text(self.textLf, SG, readOnly=True)
        self.textT.placeRelative(changeWidth=-5, changeHeight=-25)
        self.textLf.placeRelative(fixY=300, fixWidth=600, changeHeight=-25, centerX=True)

        self.organic_matter_data = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "composter_organic_matter.json"), ignoreErrors=True)
        if type(self.organic_matter_data) == str:
            self.organic_matter_data = None
            tk.SimpleDialog.askError(self.master, self.organic_matter_data)

        self.fuel_data = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "composter_fuel.json"), ignoreErrors=True)
        if type(self.fuel_data) == str:
            self.fuel_data = None
            tk.SimpleDialog.askError(self.master, self.fuel_data)

        self.sortedFuel = []
        self.sortedMatter = []
        self.selectedMatter = None
        self.selectedFuel = None


        #self.showStackProfit = tk.Checkbutton(self.contentFrame, SG)
        #self.showStackProfit.setText("Show-Profit-as-Stack[x64]")
        #self.showStackProfit.onSelectEvent(self.updateTreeView)
        #self.showStackProfit.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=300)
    def openComposterSettings(self):
        SettingsGUI.openComposterSettings(self.master, onScrollHook=self.updateTreeView)
    def onListboxSelect(self, e):
        type_ = e.getArgs(0)
        if type_ == "matter":
            self.selectedMatter = self.matterLb.getSelectedIndex()
        else:
            self.selectedFuel = self.fuelLb.getSelectedIndex()
        self.updateTreeView()
    def parseData(self):

        if API.SKYBLOCK_BAZAAR_API_PARSER is None: return
        if self.fuel_data is None or self.organic_matter_data is None:
            self.sortedFuel = False
            self.sortedMatter = False
            return
        sortedFuel = []
        sortedMatter = []
        for name, value in iterDict(self.fuel_data.getData()):

            ingredientItem = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(name)

            ## ingredients price ##
            if self.useBuyOffers.getState():  # use buy Offer ingredients
                # print(f"Offer one {name}:", ingredientItem.getInstaSellPrice()+.1)
                ingredientPrice = [ingredientItem.getInstaSellPrice() + .1]
            else:  # insta buy ingredients
                ingredientPrice = ingredientItem.getInstaBuyPriceList(1)

            pricePerFuel = ingredientPrice[0] / value

            sortedFuel.append(Sorter(pricePerFuel, name=name))
        sortedFuel.sort()
        self.sortedFuel = sortedFuel[::-1]
        if self.selectedFuel is None:
            self.selectedFuel = 0

        for name, value in iterDict(self.organic_matter_data.getData()):

            ingredientItem = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(name)

            ## ingredients price ##
            if self.useBuyOffers.getState():  # use buy Offer ingredients
                # print(f"Offer one {name}:", ingredientItem.getInstaSellPrice()+.1)
                ingredientPrice = [ingredientItem.getInstaSellPrice() + .1]
            else:  # insta buy ingredients
                ingredientPrice = ingredientItem.getInstaBuyPriceList(1)

            pricePerMatter = ingredientPrice[0]/value

            sortedMatter.append(Sorter(pricePerMatter, name=name))
        sortedMatter.sort()
        self.sortedMatter = sortedMatter[::-1]
        if self.selectedMatter is None:
            self.selectedMatter = 0
    def calculateComposterUpgrades(self):
        data = Config.SETTINGS_CONFIG["composter"]

        # constants
        matterRequired = 4000
        fuelRequired = 2000
        durationSeconds = 600

        # upgrades
        speed = data["speed"]
        mulDrop = data["multi_drop"] * 3
        fuelCap = data["fuel_cap"] * 30_000 + 100_000
        matterCap = data["matter_cap"] * 20_000 + 40_000
        costReduct = data["cost_reduction"]

        # apply cost reduction
        matterRequired *= (100 - costReduct) / 100
        fuelRequired *= (100 - costReduct) / 100

        newDuration = 1/((6 + 6 * 0.2 * speed) / 3600) # new duration to produce one compost

        return {
            "multiple_drop_percentage": mulDrop,
            "matter_required": matterRequired,
            "fuel_required": fuelRequired,
            "matter_cap":matterCap,
            "fuel_cap":fuelCap,
            "duration_seconds":newDuration
        }
    def addMultipleChance(self, chance, amount):
        amount += amount*(chance/100)
        return amount
    def updateTreeView(self):
        if self.sortedFuel is None or self.sortedMatter is None: return
        if API.SKYBLOCK_BAZAAR_API_PARSER is None: return

        ## calculation ##
        self.parseData() # calculate current prices
        data = self.calculateComposterUpgrades() # calculate upgrades

        ## Listbox ##
        self.matterLb.clear()
        self.fuelLb.clear()
        for i, matter in enumerate(self.sortedMatter):
            self.matterLb.add(f"{matter['name']} [{round(matter.get(), 2)} coins]")
        for i, matter in enumerate(self.sortedFuel):
            self.fuelLb.add(f"{matter['name']} [{round(matter.get(), 2)} coins]")

        ## Result price ##
        compost = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("COMPOST")
        if self.useSellOffers.getState():  # use sell Offer
            compostSellPrice = compost.getInstaBuyPrice()
        else:  # insta sell result
            compostSellPrice = compost.getInstaSellPrice()
        compostSellPrice = applyBazaarTax(compostSellPrice) # add tax

        compostE = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID("ENCHANTED_COMPOST")
        if self.useSellOffers.getState():  # use sell Offer
            compostESellPrice = compostE.getInstaBuyPrice()
        else:  # insta sell result
            compostESellPrice = compostE.getInstaSellPrice()
        compostESellPrice = applyBazaarTax(compostESellPrice)  # add tax

        matterType = self.sortedMatter[self.selectedMatter]
        fuelType = self.sortedFuel[self.selectedFuel]

        coinsPerMatter = self.sortedMatter[self.selectedMatter].get()
        coinsPerFuel = self.sortedFuel[self.selectedFuel].get()

        singleCost = (coinsPerMatter * data["matter_required"] + coinsPerFuel * data["fuel_required"])
        singleProfit = compostSellPrice - singleCost
        enchantedSingleCost = (compostESellPrice - (singleCost*160)) / 160
        #TODO test
        enchantedSingleCostA = (compostESellPrice - (singleCost*self.addMultipleChance(data['multiple_drop_percentage'], 160))) / 160 # with multiple_drop_percentage

        compostFullFuel = round(data['fuel_cap']/data['fuel_required'], 2)
        compostFullMatter = round(data['matter_cap']/data['matter_required'], 2)
        if compostFullFuel > compostFullMatter:
            upgrade = "matter"
            compostFull = compostFullMatter
        else:
            upgrade = "fuel"
            compostFull = compostFullFuel
        self.textT.clear()
        text = f"Matter-Type: {matterType['name']}\n"
        text += f"Matter-Required-Full-Tank: {int(data['matter_cap']/self.organic_matter_data[matterType['name']])}\n"
        text += f"Matter-Tank: {parsePrizeToStr(data['matter_cap'], True)}\n"
        text += f"Fuel-Type: {fuelType['name']}\n"
        text += f"Fuel-Required-Full-Tank: {int(data['fuel_cap']/self.fuel_data[fuelType['name']])}\n"
        text += f"Fuel-Tank: {parsePrizeToStr(data['fuel_cap'], True)}\n"
        text += f"Time-Per-Compost: {parseTimeFromSec(data['duration_seconds'])}\n\n"
        text += f"===== PROFIT =====\n"
        text += f"Single-Profit(no mul drop): {parsePrizeToStr(singleProfit)}\n"
        text += f"Stack-Profit(x64): {parsePrizeToStr(singleProfit * 64)} (~{parsePrizeToStr(singleProfit * self.addMultipleChance(data['multiple_drop_percentage'], 64))} per)\n"
        text += f"Profit-Enchanted-Compost(x1 compost): {parsePrizeToStr(enchantedSingleCost)}\n"
        text += f"Profit-Enchanted-Compost(x160 compost): {parsePrizeToStr(enchantedSingleCostA)}\n\n"
        text += f"== OFFLINE ==\n"
        text += f"Compost-With-Full-Tanks: {compostFull} (upgrade: {upgrade})\n"
        text += f"Duration-With-Full-Tanks: {parseTimeFromSec(data['duration_seconds'] * compostFull)}\n"
        text += f"Full-Composter-Profit: ~{parsePrizeToStr(singleProfit * self.addMultipleChance(data['multiple_drop_percentage'], compostFull))}\n"
        self.textT.setStrf(text)
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()