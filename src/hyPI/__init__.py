from hyPI.constants import Config
from typing import Tuple
from hyPI.constants import BazaarItemID, ALL_ENCHANTMENT_IDS

def getEnchantmentIDLvl(enchantmentID:BazaarItemID | str)->Tuple[str, int] | None:
    enchantmentID = enchantmentID.name if hasattr(enchantmentID, "name") else enchantmentID

    if enchantmentID not in ALL_ENCHANTMENT_IDS:
        return None
    level = int(enchantmentID.split("_")[-1])
    name = "_".join(enchantmentID.split("_")[:-1])

    return name, level


def parseNumber(f:float)->str:
    pass

