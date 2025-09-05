import tksimple as tk
from tkinter import ttk
from hyPI.hypixelAPI.loader import HypixelBazaarParser, HypixelAuctionParser, HypixelItemParser
import os

VERSION = "v2.3.0"
APP_DATA = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
CONFIG = os.path.join(os.path.split(__file__)[0], "config")

class Color:
    COLOR_WHITE = tk.Color.rgb(255, 255, 255)
    COLOR_DARK = tk.Color.rgb(50, 50, 50)
    COLOR_GRAY = tk.Color.rgb(160, 160, 160)

class ConfigFile:
    AVERAGE_PRICE = None

class API:
    SKYBLOCK_BAZAAR_API_PARSER: HypixelBazaarParser = None
    SKYBLOCK_AUCTION_API_PARSER: HypixelAuctionParser = None
    SKYBLOCK_ITEM_API_PARSER: HypixelItemParser = None

class System:
    CONFIG_PATH = ""
    SYSTEM_TYPE = ""

BazaarItemID: [str] = [] # creation on runtime
AuctionItemID: [str] = [] # creation on runtime

MASTER_STARS = [
    "FIRST_MASTER_STAR",
    "SECOND_MASTER_STAR",
    "THIRD_MASTER_STAR",
    "FOURTH_MASTER_STAR",
    "FIFTH_MASTER_STAR",
]

ALL_ENCHANTMENT_IDS = []

MAGIC_POWDER = {
    "COMMON": 3,
    "UNCOMMON": 5,
    "RARE": 8,
    "EPIC": 12,
    "LEGENDARY": 16,
    "MYTHIC": 22,
    "SPECIAL": 3,
    "VERY_SPECIAL": 5,
    "SUPREME": 0 # crux tier7 (dont care)
}
ENCHANTMENT_UPGRADES = {
    "ENCHANTMENT_SCAVENGER_6": "GOLDEN_BOUNTY",
    "ENCHANTMENT_LUCK_OF_THE_SEA_7": "GOLD_BOTTLE_CAP",
    "ENCHANTMENT_PESTERMINATOR_6": "PESTHUNTING_GUIDE",
    "ENCHANTMENT_SMITE_7": "SEVERED_HAND",
    "ENCHANTMENT_PISCARY_7": "TROUBLED_BUBBLE",
    "ENCHANTMENT_SPIKED_HOOK_7": "OCTOPUS_TENDRIL",
    "ENCHANTMENT_BANE_OF_ARTHROPODS_7": "ENSNARED_SNAIL",
    "ENCHANTMENT_CHARM_7": "CHAIN_END_TIMES",
    "ENCHANTMENT_FRAIL_7": "SEVERED_PINCER",
    "ENCHANTMENT_ENDER_SLAYER_7": "ENDSTONE_IDOL",
}
RARITY_COLOR_CODE = {
    "COMMON":"white",
    "UNCOMMON":"#55FF55",
    "RARE":"#5555FF",
    "EPIC":"#AA00AA",
    "LEGENDARY":"#FFAA00",
    "MYTHIC":"#FF55FF",
    "DIVINE":"#55FFFF",
    "SPECIAL":"#AA0000",
    "VERY_SPECIAL":"#AA0000",
    "ULTIMATE":"#AA0000",
    "SUPREME":"#AA0000",
}
NPC_BUYABLE_PET_ITEMS = {
    "PET_ITEM_COMBAT_SKILL_BOOST_COMMON": 60_000,
    "PET_ITEM_FORAGING_SKILL_BOOST_COMMON": 60_000,
    "PET_ITEM_MINING_SKILL_BOOST_COMMON": 60_000,
    "PET_ITEM_MINING_SKILL_BOOST_UNCOMMON": 250_000,
    "PET_ITEM_FARMING_SKILL_BOOST_COMMON": 60_000,
    "PET_ITEM_FARMING_SKILL_BOOST_RARE": 500_000,
    "PET_ITEM_FISHING_SKILL_BOOST_COMMON": 60_000,
    "PET_ITEM_ALL_SKILLS_BOOST_COMMON": 50_000,
    "PET_ITEM_BIG_TEETH_COMMON": 750_000,
    "PET_ITEM_IRON_CLAWS_COMMON": 750_000,
    "PET_ITEM_HARDENED_SCALES_UNCOMMON": 1_000_000,
    "PET_ITEM_SHARPENED_CLAWS_UNCOMMON": 1_000_000,
    "PET_ITEM_BUBBLEGUM": 5_000_000,
    "REAPER_GEM": 20_000_000
}
CUSTOM_PET_XP_MAX = {
    "PET_GOLDEN_DRAGON": 210_255_385,
    "PET_JADE_DRAGON": 210_255_385
}
PET_XP_MAX = {
    "COMMON": 5_624_785,
    "UNCOMMON": 8_644_220,
    "RARE": 12_626_665,
    "EPIC": 18_608_500,
    "LEGENDARY": 25_353_230,
    "MYTHIC": 25_353_230,
}
MAYOR_NORMAL = [
    "Diana",
    "Paul",
    "Finnegan",
    "Marina",
    "Cole",
    "Diaz",
    "Foxy",
    "Aatrox"
]
MAYOR_SPEC = [
    "Jerry",
    "Scorpius",
    "Derpy",
]
COLOR_CODE_MAP = {
    "0": "#000000",
    "1": "#0000AA",
    "2": "#00AA00",
    "3": "#00AAAA",
    "4": "#AA0000",
    "5": "#AA00AA",
    "6": "#FFAA00",
    "7": "#AAAAAA",
    "8": "#555555",
    "9": "#5555FF",
    "a": "#55FF55",
    "b": "#55FFFF",
    "c": "#FF5555",
    "d": "#FF55FF",
    "e": "#FFFF55",
    "f": "#FFFFFF",
    "l": ("Arial", 10, "bold"),
    "m": ("Arial", 10, "overstrike")
}
MAYOR_PERK_AMOUNT = {
    "Diana": 4,
    "Paul": 3,
    "Finnegan": 4,
    "Marina": 4,
    "Cole": 4,
    "Diaz": 4,
    "Foxy": 4,
    "Aatrox": 3,
    "Jerry": 3,
    "Scorpius": 2,
    "Derpy": 4,
}

STYLE_GROUP = tk.WidgetGroup()
STYLE_GROUP.addCommand("setBg", Color.COLOR_DARK, ignoreErrors=True)
STYLE_GROUP.addCommand("setFg", Color.COLOR_WHITE, ignoreErrors=True)
STYLE_GROUP.addCommand("setActiveBg", Color.COLOR_GRAY, ignoreErrors=True)
STYLE_GROUP.addCommand("setSlotBgDefault", Color.COLOR_DARK, ignoreErrors=True)
STYLE_GROUP.addCommand("setSelectBackGroundColor", Color.COLOR_GRAY, ignoreErrors=True)
STYLE_GROUP.addCommand("setSelectColor", Color.COLOR_GRAY, ignoreErrors=True)
STYLE_GROUP.addCommand("setSlotBgAll", Color.COLOR_GRAY, ignoreErrors=True)

BAZAAR_INFO_LABEL_GROUP = tk.WidgetGroup(instantiate=STYLE_GROUP)
AUCT_INFO_LABEL_GROUP = tk.WidgetGroup(instantiate=STYLE_GROUP)


def LOAD_STYLE():
    style = ttk.Style()
    style.theme_create("custom_theme", parent="alt", settings={
        "TNotebook":{
            "configure":{
                "tabmargins":[2, 5, 2, 0],
                "background": Color.COLOR_DARK,
            }
        },
        "TNotebook.Tab":{
            "configure":{
                "padding":[5, 1],
                "background":Color.COLOR_DARK,
                "foreground":Color.COLOR_WHITE,
            }
        },
        "Treeview": {
            "configure": {
                "background": Color.COLOR_DARK,
                "foreground": Color.COLOR_WHITE,
                "fieldbackground":Color.COLOR_DARK
            },
            "map":{
                "background": [('selected', Color.COLOR_GRAY)]
            }
        },
        "Treeview.Heading":{
            "configure": {
                "background": Color.COLOR_DARK,
                "foreground": Color.COLOR_WHITE
            }
        },
        "TProgressbar": {
            "configure": {
                "background": "green",
                "troughcolor": Color.COLOR_DARK,
            }
        },
        "TCombobox": {
            "configure": {
                "background": Color.COLOR_DARK,
                "foreground": Color.COLOR_WHITE,
                "fieldbackground": Color.COLOR_DARK,
                "selectbackground":Color.COLOR_DARK,
                "selectcolor":Color.COLOR_DARK,
            }
        },
        "Vertical.TScrollbar": {
            "configure": {
                "background": Color.COLOR_DARK,
                "foreground": Color.COLOR_WHITE,
                "fieldbackground": Color.COLOR_DARK,
                "selectbackground": Color.COLOR_DARK,
                "selectcolor": Color.COLOR_DARK,
                "arrowsize": 17
            }
        }
    }
                       )
    style.theme_use("custom_theme")


def CONFIGURE_NOTEBOOK_STYLE(style):
    style.configure(
        "CustomNotebook",
        background=Color.COLOR_DARK,
        foreground=Color.COLOR_WHITE
    )
    style.configure(
        "CustomNotebook.Tab",
        background=Color.COLOR_DARK,
        foreground=Color.COLOR_WHITE
    )


class Constants:
    BAZAAR_TAX = None
    WAITING_FOR_API_REQUEST = False