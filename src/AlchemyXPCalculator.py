import os
from core.jsonConfig import JsonConfig
import tksimple as tk
from core.constants import STYLE_GROUP as SG, Path, API
from core.settings import Config
from core.skyMisc import Sorter, parsePrizeToStr
from core.widgets import CustomPage


class AlchemyXPCalculatorPage(CustomPage):
    def __init__(self, master):
        super().__init__(master,
                         pageTitle="Alchemy XP",
                         buttonText="Alchemy XP Calc")
        self.master = master
        self.headerIndex = ""

        self.alchemyLvlConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "alchemy_lvl.json"))
        self.alchemyXPConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "alchemy_xp.json"))
        self.alchemyXPGoldGainConfig = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "alchemy_lvl_gold.json"))
        self.alchemySellConfigDefault = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "alchemy_sell.json"))
        self.alchemySellConfigGlowstone = JsonConfig.loadConfig(os.path.join(Path.INTERNAL_CONFIG, "alchemy_sell_glowstone.json"))

        self.calcMode = tk.DropdownMenu(self.contentFrame, SG)
        self.calcMode.setText("Default (shown ingredient)")
        self.calcMode.setOptionList([
            "Default (shown ingredient)",
            "Default + 1 (shown ingredient + 1 glowstone)",
        ])
        self.calcMode.onSelectEvent(self.updateTreeView)
        self.calcMode.placeRelative(fixHeight=25, stickDown=True, fixWidth=250)

        self.wisdom = tk.TextEntry(self.contentFrame, SG)
        self.wisdom.setText("Wisdom: ")
        self.wisdom.setValue(Config.SETTINGS_CONFIG["alchemy_wisdom"])
        self.wisdom.getEntry().onUserInputEvent(self.updateTreeView)
        self.wisdom.placeRelative(fixHeight=25, stickDown=True, fixWidth=100, fixX=250)

        self.fromTo = tk.TextEntry(self.contentFrame, SG)
        self.fromTo.setText("Level Range: ")
        self.fromTo.getEntry().onUserInputEvent(self.updateTreeView)
        self.fromTo.placeRelative(fixHeight=25, stickDown=True, fixWidth=200, fixX=350)

        self.info = tk.Label(self.contentFrame, SG)
        self.info.placeRelative(fixHeight=25, stickDown=True, fixX=550)

        self.treeView = tk.TreeView(self.contentFrame, SG)
        scrollbar = tk.ScrollBar(self.master)
        self.treeView.attachVerticalScrollBar(scrollbar)
        self.treeView.bind(self.onItemInfo, tk.EventType.DOUBBLE_LEFT)
        self.treeView.onSelectHeader(self.onHeaderClick)
        self.treeView.placeRelative(changeHeight=-25)
    def onItemInfo(self):
        sel = self.treeView.getSelectedItem()
        if sel is None: return
        self.master.showItemInfo(self, sel["Item"])
    def onHeaderClick(self, e:tk.Event):
        self.headerIndex:str = e.getValue()
        self.updateTreeView()
    def updateTreeView(self):
        self.treeView.clear()
        self.treeView.setTableHeaders("Item", "Cost", "Brews(3-Pots)")

        if API.SKYBLOCK_BAZAAR_API_PARSER is None:

            return


        wisdom = self.wisdom.getValue()
        if wisdom.isnumeric():
            wisdomFactor = int(wisdom)
            Config.SETTINGS_CONFIG["alchemy_wisdom"] = wisdomFactor
            Config.SETTINGS_CONFIG.save()
            wisdomFactor = 1+(wisdomFactor/100)
        else:
            self.info.setText(f"Wrong wisdom value! Must be > 0.")
            return


        content = self.fromTo.getValue()
        if content.count("-") == 1:
            fr, to = content.split("-")
            if fr == "":
                fr = 0
            elif not fr.isnumeric():
                self.info.setText(f"Error: 'from' in level range is nan. {fr}. ({-1} xp)")
                return
            fr = int(fr)
            if to == "":
                to = len(self.alchemyLvlConfig.getData())-1
            elif not to.isnumeric():
                self.info.setText(f"Error: 'to' in level range is nan. {to}. ({-1} xp)")
                return
            to = int(to)
            if not (0 < fr <= len(self.alchemyLvlConfig.getData())):
                self.info.setText(f"Error: 'from' in level range is not in range. {fr}. ({-1} xp)")
                return
            if not (0 < to <= len(self.alchemyLvlConfig.getData())):
                self.info.setText(f"Error: 'to' in level range is not in range. {to}. ({-1} xp)")
                return
            if fr >= to:
                self.info.setText(f"Error: 'to' cannot be less or equal to 'from'. {to}. ({-1} xp)")
                return

            _range = self.alchemyLvlConfig.getData()[fr-1:to]
            requiredXP = sum(_range)
            lvlEarn = sum(self.alchemyXPGoldGainConfig.getData()[fr-1:to])

            self.info.setText(f"Showing range of {len(_range)} Levels. ({requiredXP} xp)")


        elif content == "":
            self.info.setText(f"Showing all 50 Levels. ({sum(self.alchemyLvlConfig.getData())} xp)")
            requiredXP = sum(self.alchemyLvlConfig.getData())
            lvlEarn = sum(self.alchemyXPGoldGainConfig.getData())
        elif content.isnumeric():
            content = int(content)
            if content > 0 and content <= len(self.alchemyLvlConfig.getData()):
                requiredXP = self.alchemyLvlConfig.getData()[content-1]
                lvlEarn = self.alchemyXPGoldGainConfig.getData()[content-1]
                self.info.setText(f"Showing Level {content}. ({requiredXP} xp)")
            else:
                self.info.setText(f"Error: There is no Level {content}. ({-1} xp)")
                return
        else:
            self.info.setText(f"Error: Wrong range or Level {content}. ({-1} xp)")
            return



        if self.calcMode.getValue() == "Default (shown ingredient)":
            alchemySellConfig = self.alchemySellConfigDefault
        else:
            alchemySellConfig = self.alchemySellConfigGlowstone

        sorters = []
        for itemID in self.alchemyXPConfig.keys():
            item = API.SKYBLOCK_BAZAAR_API_PARSER.getProductByID(itemID)
            singleXp = self.alchemyXPConfig[itemID]
            npcSellPrice = alchemySellConfig[itemID]*3


            brews = int(requiredXP / (singleXp*wisdomFactor*3))+1

            ## Buy price ##

            itemBuyPrice = (item.getInstaSellPrice() + .1-npcSellPrice) * brews

            sorters.append(
                Sorter(
                    sortKey="cost",
                    itemID=itemID,
                    cost=itemBuyPrice-lvlEarn,
                    brews=brews
                )
            )
        sorters.sort()
        sorters.reverse()
        for s in sorters:
            self.treeView.addEntry(
                s["itemID"],
                parsePrizeToStr(s["cost"]),
                s["brews"]
            )
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.updateTreeView  # hook to update tv on new API-Data available
        self.placeRelative()
        self.updateTreeView()
        self.placeContentFrame()