from typing import List, Tuple
from numpy import median
from datetime import datetime

def addPositiveTax(price, taxVal):
    return
def addNegativeTax(price, taxVal):
    return

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
def parsePrizeList(prizes:List[float], exponent:int)->List[float]:
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
def getMedianExponent(prizes:list)->Tuple[int, str] | Tuple[None, None]:
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


class TimeDelta:
    def __init__(self, day, hours, minutes, seconds):
        self.day = day
        self.hour = hours
        self.minute = minutes
        self.second = seconds




def parseTimeDelta(td):
    minutes = (td.seconds//60) % 60
    day = td.days
    hour = td.seconds//3600
    minute = minutes
    seconds = td.seconds % 60
    print(day)
    return TimeDelta(day, hour, minute, seconds)
