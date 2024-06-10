from hyPI.constants import Config
from typing import Tuple

def getEnchantmentIDLvl(enchantmentID: str)->Tuple[str, int] | None:
    level = int(enchantmentID.split("_")[-1])
    name = "_".join(enchantmentID.split("_")[:-1])
    return name, level


def parseNumber(f:float)->str:
    pass

