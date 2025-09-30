import tksimple as tk
from core.constants import STYLE_GROUP as SG, RARITY_COLOR_CODE
from core.settings import Config
from core.skyMisc import parsePrizeToStr
from core.widgets import CustomPage


class MagicFindCalculatorPage(CustomPage):
    def __init__(self, master):
        super().__init__(master, pageTitle="Magic Find Calculator", buttonText="Magic Find Calculator")

        self.LOOTING_CONST = .15
        self.LUCK_CONST = .05

        """{
            "base_chance":1,
            "pet_luck":0,
            "magic_find":0,
            "magic_find_bestiary":0,
            "looting_lvl":0,
            "luck_lvl":0,
            "item_type":0
        }"""

        mc = RARITY_COLOR_CODE["DIVINE"] # magic find color-code
        pc = RARITY_COLOR_CODE["MYTHIC"] # pet luck color-code
        ec = RARITY_COLOR_CODE["LEGENDARY"] # enchantment color-code
        placer = tk.Placer(25)
        self.baseChanceE = tk.TextEntry(self.contentFrame, SG).setText("Base Chance (1 in)").setFg(ec).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["base_chance"])
        self.petLuckE = tk.TextEntry(self.contentFrame, SG).setText("Pet Luck Stat(in %)").setFg(pc).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["pet_luck"])
        self.magicFindE = tk.TextEntry(self.contentFrame, SG).setText("Magic Find Stat").setFg(mc).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find"])
        self.magicFindBeE = tk.TextEntry(self.contentFrame, SG).setText("Magic Find Bestiary").setFg(mc).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"])
        self.lootingE = tk.TextEntry(self.contentFrame, SG).setText("Looting Enchantment:").setFg(ec).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"])
        self.luckE = tk.TextEntry(self.contentFrame, SG).setText("Luck Enchantment:").setFg(ec).placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25).setValue(Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"])
        tk.Label(self.contentFrame, SG).setText("Item Type:").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)
        self.rad = tk.Radiobutton(self.contentFrame, SG)
        norItem = self.rad.createNewRadioButton(SG).setText("Normal Item").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)
        armor = self.rad.createNewRadioButton(SG).setText("Armor Piece").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)
        pet = self.rad.createNewRadioButton(SG).setText("Pet").placeRelative(fixX=0, fixY=placer.get(), fixWidth=300, fixHeight=25)

        self.rad.setState(Config.SETTINGS_CONFIG["magic_find"]["item_type"])

        self.baseChanceE.getEntry().onUserInputEvent(self.onUpdate)
        self.petLuckE.getEntry().onUserInputEvent(self.onUpdate)
        self.magicFindE.getEntry().onUserInputEvent(self.onUpdate)
        self.magicFindBeE.getEntry().onUserInputEvent(self.onUpdate)
        self.lootingE.getEntry().onUserInputEvent(self.onUpdate)
        self.luckE.getEntry().onUserInputEvent(self.onUpdate)
        self.rad.onSelectEvent(self.onUpdate)

        self.toKillE = tk.Label(self.contentFrame, SG).setText("Actions till drop: ").placeRelative(fixX=300, fixY=0, fixWidth=300, fixHeight=30).setFont(15)
        self.chanceE = tk.Label(self.contentFrame, SG).setText("Chance: ").placeRelative(fixX=300, fixY=30, fixWidth=300, fixHeight=30).setFont(15)
    def onUpdate(self):
        self.toKillE.setText("Actions till drop: ")
        self.chanceE.setText("Chance: ")

        state = self.rad.getState()
        baseChance = self.baseChanceE.getValue()
        petLuck = self.petLuckE.getValue()
        magicFind = self.magicFindE.getValue()
        magicFindBe = self.magicFindBeE.getValue()
        luck = self.luckE.getValue()
        looting = self.lootingE.getValue()


        if baseChance.isnumeric():
            baseChance = int(baseChance)
            Config.SETTINGS_CONFIG["magic_find"]["base_chance"] = baseChance
            Config.SETTINGS_CONFIG.save()
        elif baseChance == "": baseChance = Config.SETTINGS_CONFIG["magic_find"]["base_chance"]
        else:
            self.baseChanceE.setValue(Config.SETTINGS_CONFIG["magic_find"]["base_chance"])
            tk.SimpleDialog.askError(self.master, f"Wrong base_chance value! Must be > 0.")
            return
        if petLuck.isnumeric():
            petLuck = int(petLuck)
            Config.SETTINGS_CONFIG["magic_find"]["pet_luck"] = petLuck
            Config.SETTINGS_CONFIG.save()
        elif petLuck == "": petLuck = Config.SETTINGS_CONFIG["magic_find"]["pet_luck"]
        elif state == 2: # pets
            self.petLuckE.setValue(Config.SETTINGS_CONFIG["magic_find"]["pet_luck"])
            tk.SimpleDialog.askError(self.master, f"Wrong pet_luck value! Must be > 0.")
            return
        if magicFind.isnumeric():
            magicFind = int(magicFind)
            Config.SETTINGS_CONFIG["magic_find"]["magic_find"] = magicFind
            Config.SETTINGS_CONFIG.save()
        elif magicFind == "": magicFind = Config.SETTINGS_CONFIG["magic_find"]["magic_find"]
        else:
            self.magicFindE.setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find"])
            tk.SimpleDialog.askError(self.master, f"Wrong magic_find value! Must be > 0.")
            return
        if magicFindBe.isnumeric():
            magicFindBe = int(magicFindBe)
            Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"] = magicFindBe
            Config.SETTINGS_CONFIG.save()
        elif magicFindBe == "": magicFindBe = Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"]
        else:
            self.magicFindBeE.setValue(Config.SETTINGS_CONFIG["magic_find"]["magic_find_bestiary"])
            tk.SimpleDialog.askError(self.master, f"Wrong magic_find_bestiary value! Must be > 0.")
            return
        if luck.isnumeric():
            luck = int(luck)
            Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"] = luck
            Config.SETTINGS_CONFIG.save()
        elif luck == "": luck = Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"]
        elif state == 1:
            self.luckE.setValue(Config.SETTINGS_CONFIG["magic_find"]["luck_lvl"])
            tk.SimpleDialog.askError(self.master, f"Wrong luck_lvl value! Must be > 0.")
            return
        if looting.isnumeric():
            looting = int(looting)
            Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"] = looting
            Config.SETTINGS_CONFIG.save()
        elif looting == "": looting = Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"]
        elif state == 0:
            self.lootingE.setValue(Config.SETTINGS_CONFIG["magic_find"]["looting_lvl"])
            tk.SimpleDialog.askError(self.master, f"Wrong looting_lvl value! Must be > 0.")
            return

        if state == 0: add = (looting*self.LOOTING_CONST) # item
        if state == 1: add = (luck*self.LUCK_CONST) # armor
        if state == 2: add = (petLuck/100) # pet

        magicFind += magicFindBe
        baseChance = 1/baseChance

        newChance = baseChance * (1+(magicFind/100)+add)

        self.toKillE.setText(f"Actions till drop: {parsePrizeToStr(round(1 / newChance, 2), True)}")
        self.chanceE.setText(f"Chance: {round(newChance*100, 5)}%")
    def onShow(self, **kwargs):
        self.master.updateCurrentPageHook = self.onUpdate  # hook to update tv on new API-Data available
        self.placeRelative()
        self.onUpdate()
        self.placeContentFrame()
        tk.SimpleDialog.askWarning(self.master, "This feature does not work properly at the moment, due a wrong and outdated magicfind formular.")