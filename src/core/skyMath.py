from typing import List as _List, Tuple as _Tuple
from numpy import median, percentile

from .constants import Constants as _Constants, CUSTOM_PET_XP_MAX, PET_XP_MAX


def getPlotTicksFromInterval(data:list, interval:int)->list:
    """
    This function is used to configure the x/y-Axis label amount.
    if interval us per ex. 2 -> every second label is removed.
    The plot stays the same. Only the labels gets removed.

    @param data:
    @param interval:
    @return:
    """
    data = data.copy()
    length = len(data)
    while True:
        if length % interval == 0: break
        data.pop(0)
        length = len(data)
    return data[::interval]
def parsePrizeList(prizes:_List[float], exponent:int)->_List[float]:
    """
    Returns the prizes parsed to fix exponent.

    @param prizes:
    @param exponent:
    @return:
    """
    mappedPrizes = []
    for x in range(len(prizes)):
        mappedPrizes.append(prizes[x] / (10 ** (exponent * 3)))
    return mappedPrizes
def getMedianExponent(prizes:list)->_Tuple[int, str] | _Tuple[None, None]:
    """
    Returns the median Exponent of given list and the Prefix.

    @param prizes:
    @return:
    """
    inputPrize = median(prizes)
    prefixList = ["", "k", "m", "b", "Tr", "Q"]
    exponent = 0
    while inputPrize > 1000:
        inputPrize = inputPrize / 1000
        exponent += 1
        if exponent > 5:
            return None, None
    return exponent, prefixList[exponent]
def getFlattenList(inputList:_List[float])->_List[float]:
    inputList = inputList.copy()
    listOfSusData = getSuspiciousData(inputList)
    clearedList = []
    x = 0
    if len(listOfSusData) == 0:
        return inputList
    for single in inputList:
        if single in listOfSusData:
            y = 0
            while inputList[x - y] in listOfSusData:
                y += 1
            clearedList.append(inputList[x - y])
        else:
            clearedList.append(inputList[x])
        x += 1
    return clearedList
def getMedianFromList(_in:_List[float])->float:
    return float(median(_in))
def getSuspiciousData(inputList: _List[float], flattenFactor: float = 1.0) -> _List[float]:
    isSusList = []
    x = 0
    underMedian, overMedian = percentile(inputList, [25 - x, 75 + x])
    IQR = overMedian - underMedian

    while IQR <= 0.2 and len(inputList) < 500000:
        if x >= 25:
            underMedian, overMedian = percentile(inputList, [0.1, 99.9])
            IQR = overMedian - underMedian
            break
        underMedian, overMedian = percentile(inputList, [25 - x, 75 + x])
        IQR = overMedian - underMedian
        x += 0.1

    # Catch Data that is SUS
    borderUp = overMedian + IQR * 1.5
    borderDown = underMedian - IQR * 1.5
    # Safe the SUS data
    for single in inputList:
        if single < borderDown or single > borderUp:
            isSusList.append(single)
    return isSusList
def applyBazaarTax(in_:float)->float:
    tax = float(_Constants.BAZAAR_TAX)
    in_ *= (100 - tax) / 100  # apply tax to instaSell Result
    return in_
class TimeDelta:
    def __init__(self, day, hours, minutes, seconds):
        self.day = day
        self.hour = hours
        self.minute = minutes
        self.second = seconds
    def toSeconds(self):
        return self.second + self.minute*60 + self.hour*60*60 + self.day*60*60*24
def parseTimeDelta(td)->TimeDelta:
    minutes = (td.seconds//60) % 60
    day = td.days
    hour = td.seconds//3600
    minute = minutes
    seconds = td.seconds % 60
    return TimeDelta(day, hour, minute, seconds)
def capPetXP(xp: float, itemID: str, rarity: str) -> float:
    if itemID in CUSTOM_PET_XP_MAX.keys():
        maxXP = CUSTOM_PET_XP_MAX[itemID]
    else:
        maxXP = PET_XP_MAX[rarity]
    if xp < maxXP:
        return xp
    return maxXP