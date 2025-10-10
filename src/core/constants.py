import os
import tksimple as tk
from tkinter import ttk

from .hyPI.hypixelAPI.loader import HypixelBazaarParser, HypixelAuctionParser, HypixelItemParser

VERSION = "v2.3.0"
APP_DATA = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")

class Path:
    INTERNAL_CONFIG = ""
    IMAGES = ""
    APP_DATA = ""
class Color:
    COLOR_WHITE = tk.Color.rgb(255, 255, 255)
    COLOR_DARK = tk.Color.rgb(50, 50, 50)
    COLOR_GRAY = tk.Color.rgb(160, 160, 160)
class ConfigFile:
    AVERAGE_PRICE = None
    ATTR_SHARD_DATA = None
class API:
    SKYBLOCK_BAZAAR_API_PARSER: HypixelBazaarParser = None
    SKYBLOCK_AUCTION_API_PARSER: HypixelAuctionParser = None
    SKYBLOCK_ITEM_API_PARSER: HypixelItemParser = None
class System:
    CONFIG_PATH = ""
    SYSTEM_TYPE = ""
class ClipBoard:
    COPY = None
    PASTE = None
BazaarItemID: [str] = [] # creation on runtime
AuctionItemID: [str] = [] # creation on runtime
MASTER_STARS = [
    "FIRST_MASTER_STAR",
    "SECOND_MASTER_STAR",
    "THIRD_MASTER_STAR",
    "FOURTH_MASTER_STAR",
    "FIFTH_MASTER_STAR",
]
ALL_ENCHANTMENT_IDS = [] # generated at runtime
BITS_ENCHANTS = [
    "ENCHANTMENT_CHAMPION",
    "ENCHANTMENT_EXPERTISE",
    "ENCHANTMENT_COMPACT",
    "ENCHANTMENT_TOXOPHILITE",
    "ENCHANTMENT_CULTIVATING",
    "ENCHANTMENT_HECATOMB",
]
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
    "SUPREME":"#AA0000"
}
RARITIES = [
    "COMMON",
    "UNCOMMON",
    "RARE",
    "EPIC",
    "LEGENDARY",
    "MYTHIC",
    "DIVINE",
    "SPECIAL",
    "VERY_SPECIAL",
    "ULTIMATE",
    "SUPREME"
]
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
DUNGEON_ITEMS = [
	"SKELETON_LORD_CHESTPLATE",
	"SKELETON_MASTER_CHESTPLATE",
	"HEAVY_HELMET",
	"SKELETON_MASTER_BOOTS",
	"THORNS_BOOTS",
	"ZOMBIE_COMMANDER_WHIP",
	"SKELETON_GRUNT_BOOTS",
	"SKELETON_SOLDIER_LEGGINGS",
	"SUPER_HEAVY_BOOTS",
	"BOUNCY_CHESTPLATE",
    "CRYPT_BOW",
    "CRYPT_DREADLORD_SWORD",
	"SKELETON_MASTER_LEGGINGS",
	"SKELETON_GRUNT_CHESTPLATE",
	"CONJURING_SWORD",
	"SILENT_DEATH",
	"SKELETOR_CHESTPLATE",
	"ZOMBIE_KNIGHT_BOOTS",
	"ZOMBIE_KNIGHT_HELMET",
	"SKELETON_SOLDIER_HELMET",
	"SKELETOR_LEGGINGS",
	"ZOMBIE_SOLDIER_LEGGINGS",
	"ZOMBIE_LORD_LEGGINGS",
	"SKELETON_LORD_LEGGINGS",
	"ZOMBIE_COMMANDER_CHESTPLATE",
	"BOUNCY_LEGGINGS",
	"ROTTEN_HELMET",
	"SUPER_UNDEAD_BOW",
	"FEL_SWORD",
	"ZOMBIE_COMMANDER_BOOTS",
	"SKELETOR_BOOTS",
	"ZOMBIE_KNIGHT_CHESTPLATE",
	"ROTTEN_LEGGINGS",
	"SKELETON_SOLDIER_BOOTS",
	"ZOMBIE_SOLDIER_HELMET",
	"ZOMBIE_SOLDIER_BOOTS",
	"SKELETON_SOLDIER_CHESTPLATE",
	"SKELETON_MASTER_HELMET",
	"ROTTEN_BOOTS",
	"HEAVY_CHESTPLATE",
	"SKELETOR_HELMET",
	"BOUNCY_HELMET",
	"ZOMBIE_KNIGHT_SWORD",
	"SUPER_HEAVY_CHESTPLATE",
	"BOUNCY_BOOTS",
	"SKELETON_LORD_BOOTS",
	"ROTTEN_CHESTPLATE",
	"SUPER_HEAVY_HELMET",
	"HEAVY_LEGGINGS",
	"SKELETON_GRUNT_HELMET",
	"ZOMBIE_COMMANDER_LEGGINGS",
	"ZOMBIE_LORD_HELMET",
	"ZOMBIE_SOLDIER_CUTLASS",
	"SUPER_HEAVY_LEGGINGS",
	"EARTH_SHARD",
	"SKELETON_GRUNT_LEGGINGS",
	"ZOMBIE_KNIGHT_LEGGINGS",
	"ZOMBIE_LORD_CHESTPLATE",
	"ZOMBIE_COMMANDER_HELMET",
	"SKELETON_LORD_HELMET",
	"HEAVY_BOOTS",
	"ZOMBIE_LORD_BOOTS",
	"ZOMBIE_SOLDIER_CHESTPLATE",
]
FURNITURE_ITEMS = [] # generated at runtime
AUTO_RECOMBED_ITEMS = [
    *DUNGEON_ITEMS,
    "SLUG_BOOTS",
    "MOOGMA_LEGGINGS",
    "FLAMING_CHESTPLATE",
    "TAURUS_HELMET",
    "BLADE_OF_THE_VOLCANO",
    "FAIRY_HELMET",
    "FAIRY_CHESTPLATE",
    "FAIRY_BOOTS",
    "FAIRY_LEGGINGS",
    "GHOST_BOOTS",
    "SQUID_BOOTS",
    "RABBIT_HAT",
    "SNOW_HOWITZER",
    "GLACITE_HELMET",
    "GLACITE_CHESTPLATE",
    "GLACITE_LEGGINGS",
    "GLACITE_BOOTS",
    "TANK_MINER_HELMET",
    "TANK_MINER_CHESTPLATE",
    "TANK_MINER_LEGGINGS",
    "TANK_MINER_BOOTS",
    "GOBLIN_HELMET",
    "GOBLIN_CHESTPLATE",
    "GOBLIN_LEGGINGS",
    "GOBLIN_BOOTS",
    "LAPIS_ARMOR_HELMET",
    "LAPIS_ARMOR_CHESTPLATE",
    "LAPIS_ARMOR_LEGGINGS",
    "LAPIS_ARMOR_BOOTS",
]
ATTR_SHARD_CATEGORY = [
    "FOREST",
    "WATER",
    "COMBAT",
]
ATTR_SHARD_FAMILY = [
    "ELEMENTAL",
    "SERPENT",
    "NONE",
    "TROPICAL_FISH",
    "BIRD",
    "EEL",
    "FROG",
    "DROWNED",
    "CROCO",
    "TURTLE",
    "SCALED",
    "CAVE_DWELLER",
    "LIZARD",
    "SPIDER",
    "DRAGON",
    "PHANTOM",
    "REPTILE",
    "TREASURE_FISH",
    "SQUID",
    "AMPHIBIAN",
    "BUG",
    "SHULKER",
    "LAPIS",
    "PANDA",
    "DEMON",
    "AXOLOTL"
]
ATTR_SHARDS_REQ = {
    "COMMON": [1, 3, 5, 6, 7, 8, 10, 14, 18, 24],
    "UNCOMMON": [1, 2, 3, 4, 5, 6, 7, 8, 12, 16],
    "RARE": [1, 2, 3, 3, 4, 4, 5, 6, 8, 12],
    "EPIC": [1, 1, 2, 2, 3, 3, 4, 4, 5, 7],
    "LEGENDARY": [1, 1, 1, 2, 2, 2, 3, 3, 4, 5],
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