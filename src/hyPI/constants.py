from enum import Enum
from pysettings import iterDict



UNICODE = {
    "rune":u"\u25c6",
    "star":"\u272a",

}


SPECIAL_MODIFIER = {
    "GREATER_SPOOK":("BOO_STONE", "GREAT_SPOOK")
}
MODIFIER = {
    "VERY":"BLACKSMITH",
    "HIGHLY":"BLACKSMITH",
    "EXTREMELY":"BLACKSMITH",
    "NOT_SO":"BLACKSMITH",
    "THICC":"BLACKSMITH",
    "ABSOLUTELY":"BLACKSMITH",
    "EVEN_MORE":"BLACKSMITH",

    "BUZZING":"CLIPPED_WINGS",
    "BEADY":"BEADY_EYES",

    "EPIC":"BLACKSMITH",
    "FAIR":"BLACKSMITH",
    "FAST":"BLACKSMITH",
    "GENTLE":"BLACKSMITH",
    "HEROIC":"BLACKSMITH",
    "LEGENDARY":"BLACKSMITH",
    "ODD":"BLACKSMITH",
    "SHARP":"BLACKSMITH",
    "SPICY":"BLACKSMITH",
    "COLDFUSED":"ENTROPY_SUPPRESSOR",
    "DIRTY":"DIRT_BOTTLE",
    "FABLED":"DRAGON_CLAW",
    "GILDED":"MIDAS_JEWEL",
    "SUSPICIOUS":"SUSPICIOUS_VIAL",
    "WARPED":"WARPED_STONE",
    "WITHERED":"WITHER_BLOOD",
    "BULKY":"BULKY_STONE",
    "JERRY'S":"JERRY_STONE",
    "FANGED":"FULL-JAW_FANGING_KIT",
    "AWKWARD":"BLACKSMITH",
    "DEADLY":"BLACKSMITH",
    "FINE":"BLACKSMITH",
    "GRAND":"BLACKSMITH",
    "HASTY":"BLACKSMITH",
    "NEAT":"BLACKSMITH",
    "RAPID":"BLACKSMITH",
    "RICH":"BLACKSMITH",
    "UNREAL":"BLACKSMITH",
    "PRECISE":"OPTICAL_LENS",
    "SPIRITUAL":"SPIRIT_STONE",
    "HEADSTRONG":"SALMON_OPAL",
    "CLEAN":"BLACKSMITH",
    "FIERCE":"BLACKSMITH",
    "HEAVY":"BLACKSMITH",
    "LIGHT":"BLACKSMITH",
    "MYTHIC":"BLACKSMITH",
    "PURE":"BLACKSMITH",
    "TITANIC":"BLACKSMITH",
    "SMART":"BLACKSMITH",
    "WISE":"BLACKSMITH",
    "CANDIED":"CANDY_CORN",
    "REINFORCED":"NECROMANCER'S_BROOCH",
    "SUBMERGED":"DEEP_SEA_ORB",
    "PERFECT":"DIAMOND_ATOM",
    "RENOWNED":"DRAGON_HORN",
    "SPIKED":"DRAGON_SCALE",
    "HYPER":"END_STONE_GEODE",
    "GIANT":"GIANT_TOOTH",
    "JADED":"JADERALD",
    "CUBIC":"MOLTEN_CUBE",
    "NECROTIC":"NECROMANCER'S_BROOCH",
    "EMPOWERED":"SADAN'S_BROOCH",
    "ANCIENT":"PRECURSOR_GEAR",
    "UNDEAD":"PREMIUM_FLESH",
    "LOVING":"RED_SCARF",
    "RIDICULOUS":"RED_NOSE",
    "BUSTLING":"SKYMART_BROCHURE",
    "MOSSY":"OVERGROWN_GRASS",
    "FESTIVE":"FROZEN_BAUBLE",
    "GLISTENING":"SHINY_PRISM",
    "STRENGTHENED":"SEARING_STONE",
    "WAXED":"BLAZE_WAX",
    "FORTIFIED":"METEOR_SHARD",
    "ROOTED":"BURROWING_SPORES",
    "BLOOMING":"FLOWERING_BOUQUET",
    "SNOWY":"TERRY'S_SNOWGLOBE",
    "BLOOD-SOAKED":"PRESUMED_GALLON_OF_RED_PAINT",
    "SALTY":"SALT_CUBE",
    "TREACHEROUS":"RUSTY_ANCHOR",
    "LUCKY":"LUCKY_DICE",
    "STIFF":"HARDENED_WOOD",
    "CHOMP":"KUUDRA_MANDIBLE",
    "PITCHIN'":"PITCHIN'_KOI",
    "UNYIELDING":"BLACKSMITH",
    "PROSPECTOR'S":"BLACKSMITH",
    "EXCELLENT":"BLACKSMITH",
    "STURDY":"BLACKSMITH",
    "FORTUNATE":"BLACKSMITH",
    "AMBERED":"AMBER_MATERIAL",
    "AUSPICIOUS":"ROCK_GEMSTONE",
    "FLEET":"DIAMONITE",
    "HEATED":"HOT_STUFF",
    "MAGNETIC":"LAPIS_CRYSTAL",
    "MITHRAIC":"PURE_MITHRIL",
    "REFINED":"REFINED_AMBER",
    "STELLAR":"PETRIFIED_STARFALL",
    "FRUITFUL":"ONYX",
    "GREAT":"BLACKSMITH",
    "RUGGED":"BLACKSMITH",
    "LUSH":"BLACKSMITH",
    "LUMBERJACK'S":"BLACKSMITH",
    "DOUBLE-BIT":"BLACKSMITH",
    "MOIL":"MOIL_LOG",
    "TOIL":"TOIL_LOG",
    "BLESSED":"BLESSED_FRUIT",
    "EARTHY":"LARGE_WALNUT",
    "ROBUST":"BLACKSMITH",
    "ZOOMING":"BLACKSMITH",
    "PEASANT'S":"BLACKSMITH",
    "GREEN_THUMB":"BLACKSMITH",
    "BOUNTIFUL":"GOLDEN_BALL",
    "CALCIFIED":"CALCIFIED_HEART",
    "BLAZING":"BLAZEN_SPHERE",
    "LUMBERJACK":"BLACKSMITH",
    "ROYAL":"DWARVEN_TREASURE",
    "DIMENSIONAL":"TITANIUM_TESSERACT",
    "COLDFUSION":"ENTROPY_SUPPRESSOR",
    "PITCHIN":"PITCHIN_KOI",
    "SQUEAKY":"SQUEAKY_TOY",
    "SCRAPED":"POCKET_ICEBERG",
    "PROSPECTOR":"BLACKSMITH",
    "ODD_SWORD":"BLACKSMITH",
    "RICH_BOW":"BLACKSMITH",
    "DOUBLE_BIT":"BLACKSMITH",
    "MOONGLADE":"MOONGLADE_JEWEL",
    "TRASHY":"OVERFLOWING_TRASH_CAN",
    "GROOVY":"MANGROVE_GEM",
    "LUSTROUS":"GLEAMING_CRYSTAL",
    "GLACIAL":"FRIGID_HUSK",
    "PEASANT":"BLACKSMITH",
    "JERRY_STONE":"JERRY_STONE",
    "GREATER_SPOOK":"BOO_STONE",
    "AOTE_STONE":"AOTE_STONE",


    # equipment
    "BLOOD_SHOT":"BLACKSMITH",
    "BLOODSHOT":"BLACKSMITH",
    "STAINED":"BLACKSMITH",
    "MENACING":"BLACKSMITH",
    "HEFTY":"BLACKSMITH",
    "SOFT":"BLACKSMITH",
    "HONORED":"BLACKSMITH",
    "BLENDED":"BLACKSMITH",
    "ASTUTE":"BLACKSMITH",
    "COLOSSAL":"BLACKSMITH",
    "BRILLIANT":"BLACKSMITH",

    # old
    "BIZARRE":"old_accessories_reforge",
    "ITCHY":"old_accessories_reforge",
    "OMINOUS":"old_accessories_reforge",
    "PLEASANT":"old_accessories_reforge",
    "PRETTY":"old_accessories_reforge",
    "SHINY":"old_accessories_reforge",
    "SIMPLE":"old_accessories_reforge",
    "STRANGE":"old_accessories_reforge",
    "VIVID":"old_accessories_reforge",
    "GODLY":"old_accessories_reforge",
    "DEMONIC":"old_accessories_reforge",
    "FORCEFUL":"old_accessories_reforge",
    "HURTFUL":"old_accessories_reforge",
    "KEEN":"old_accessories_reforge",
    "STRONG":"old_accessories_reforge",
    "SUPERIOR":"old_accessories_reforge",
    "UNPLEASANT":"old_accessories_reforge",
    "ZEALOUS":"old_accessories_reforge",
    "SILKY":"old_accessories_reforge",
    "BLOODY":"old_accessories_reforge",
    "SHADED":"old_accessories_reforge",
    "SWEET":"old_accessories_reforge",
}
_RUNE_CONVERT = {
    "RUNE_BLOOD":"RUNE_BLOOD_2",
    "RUNE_MAGICAL":"RUNE_MAGIC",
    "RUNE_END":"RUNE_ENDERSNAKE",
    "RUNE_PESTILENCE":"RUNE_PESTILENCE",
    "RUNE_FREEZING":"RUNE_GRAND_FREEZING",
    "RUNE_SPELLBOUND":"UNIQUE_RUNE_SPELLBOUND",
    "RUNE_PRIMAL_FEAR":"UNIQUE_RUNE_PRIMAL_FEAR",
    "RUNE_SEARING":"RUNE_GRAND_SEARING",
}
ROMIC_NUMBERS = {
    "I":1,
    "II":2,
    "III":3,
    "IV":4,
    "V":5,
    "VI":6,
    "VII":7,
    "VIII":8,
    "IX":9,
    "X":10
}


class Category(Enum):
    WEAPON = 'WEAPON'
    ARMOR = 'ARMOR'
    BLOCKS = 'BLOCKS'
    ACCESSORIES = 'ACCESSORIES'
    CONSUMABLES = 'CONSUMABLES'
    MISC = 'MISC'

class Config:
    TARGET_TIME_ZONE = "Europe/Berlin"

class HypixelAPIURL(Enum):
    BAZAAR_URL = "https://api.hypixel.net/skyblock/bazaar"
    AUCTION_URL = "https://api.hypixel.net/v2/skyblock/auctions"
    ITEM_URL = "https://api.hypixel.net/v2/resources/skyblock/items"
    PROFILE_URL = "https://api.hypixel.net/v2/skyblock/profile"
    PROFILES_URL = "https://api.hypixel.net/v2/skyblock/profiles"
    MAYOR_URL = "https://api.hypixel.net/v2/resources/skyblock/election"

class SkyCoflnetAPIURL:
    GET_URL_BAZAAR_HIST_HOUR = lambda itemTag: f"https://sky.coflnet.com/api/bazaar/{itemTag}/history/hour"
    GET_URL_BAZAAR_HIST_DAY = lambda itemTag: f"https://sky.coflnet.com/api/bazaar/{itemTag}/history/day"
    GET_URL_BAZAAR_HIST_WEEK = lambda itemTag: f"https://sky.coflnet.com/api/bazaar/{itemTag}/history/week"
    GET_URL_BAZAAR_HIST_COMPLETE = lambda itemTag: f"https://sky.coflnet.com/api/bazaar/{itemTag}/history"
    GET_URL_BAZAAR_HIST_SNAPSHOT = lambda itemTag, timestamp: f"https://sky.coflnet.com/api/bazaar/{itemTag}/history/snapshot?timestamp={timestamp}"

    GET_URL_ITEM_PRICE = lambda itemTag: f"https://sky.coflnet.com/api/item/price/{itemTag}/current"
    GET_URL_ITEM_HIST_DAY = lambda itemTag: f"https://sky.coflnet.com/api/item/price/{itemTag}/history/day"
    GET_URL_ITEM_HIST_WEEK = lambda itemTag: f"https://sky.coflnet.com/api/item/price/{itemTag}/history/week"
    GET_URL_ITEM_HIST_MONTH = lambda itemTag: f"https://sky.coflnet.com/api/item/price/{itemTag}/history/month"
    GET_URL_ITEM_HIST_COMPLETE = lambda itemTag: f"https://sky.coflnet.com/api/item/price/{itemTag}/history/full"

    GET_URL_CRAFT_RECIPE = lambda itemTag: f"https://sky.coflnet.com/api/craft/recipe/{itemTag}"

    GET_URL_AUCT_BY_UUID = lambda auctionUuid: f"https://sky.coflnet.com/api/auctions/{auctionUuid}"
    GET_URL_AUCT_LOW_SUPPLY = lambda: f"https://sky.coflnet.com/api/auctions/supply/low"
    GET_URL_AUCT_LOW_BINS = lambda itemTag: f"https://sky.coflnet.com/api/auctions/{itemTag}/active/bin"
    GET_URL_AUCT_LOW_BIN = lambda itemTag: f"https://sky.coflnet.com/api/item/price/{itemTag}/bin"
    GET_URL_AUCT_ITEM_RECENT_OVERVIEW = lambda itemTag: f"https://sky.coflnet.com/api/auctions/tag/{itemTag}/recent/overview"
    GET_URL_AUCT_ITEM_ACTIVE_OVERVIEW = lambda itemTag: f"https://sky.coflnet.com/api/auctions/tag/{itemTag}/active/overview"

    GET_URL_MAJOR_YEAR = lambda year: f"https://sky.coflnet.com/api/mayor/{year}"
    GET_URL_MAJOR_ACTIVE = lambda: f"https://sky.coflnet.com/api/mayor"

class Error(Enum):
    DECODE_ERROR = f"Could not decode api packet."
    API_REQUEST_ERROR = f"Could not request API.\n Check your internet connection."
    WRONG_API_KEY = f"Wrong API-Key check the settings."
    API_ON_COOLDOWN = f"API is currently on cooldown\ntry again in a minute!"

NORMAL_TO_HYPIXEL = {
    "ACACIA_LOG":"LOG_2",
    "BIRCH_LOG":"LOG-2",
    "DARK_OAK_LOG":"LOG_2-1",
    "JUNGLE_LOG":"LOG-3",
    "OAK_LOG":"LOG",
    "SPRUCE_LOG":"LOG-1",

    "ENCHANTED_BROWN_MUSHROOM_BLOCK":"ENCHANTED_HUGE_MUSHROOM_1",
    "ENCHANTED_RED_MUSHROOM_BLOCK":"ENCHANTED_HUGE_MUSHROOM_2",
    "BROWN_MUSHROOM_BLOCK":"HUGE_MUSHROOM_1",
    "RED_MUSHROOM_BLOCK":"HUGE_MUSHROOM_2",
    "RED_SAND":"SAND-1",

    "NETHER_WART":"NETHER_STALK",
    "ENCHANTED_NETHER_WART":"ENCHANTED_NETHER_STALK",
    "MUTANT_NETHER_WART":"MUTANT_NETHER_STALK",

    "POTATO":"POTATO_ITEM",
    "CARROT":"CARROT_ITEM",


    "LAPIS_LAZULI":"INK_SACK:4",
    "COCOA":"INK_SACK:3",

    "CLOWNFISH":"RAW_FISH-2",
    "PUFFERFISH":"RAW_FISH-3",
    "RAW_FISH":"RAW_FISH",
    "RAW_SALMON":"RAW_FISH-1",
}
HYPIXEL_TO_NORMAL = {v:k for k, v in iterDict(NORMAL_TO_HYPIXEL)}

def ensureTransHyp(item:str):
    if item in NORMAL_TO_HYPIXEL.keys():
        return NORMAL_TO_HYPIXEL[item]
    return item

def ensureTransNor(item:str):
    if item in HYPIXEL_TO_NORMAL.keys():
        return HYPIXEL_TO_NORMAL[item]
    return item
