from hyPI.skyCoflnetAPI import SkyConflnetAPI




def modeToBazaarAPIFunc(mode):
    match mode:
        case "hour":
            return SkyConflnetAPI.getBazaarHistoryHour
        case "day":
            return SkyConflnetAPI.getBazaarHistoryDay
        case "week":
            return SkyConflnetAPI.getBazaarHistoryWeek
        case "all":
            return SkyConflnetAPI.getBazaarHistoryComplete



def prizeToStr(inputPrize:int)->str:
    exponent = 0
    prefix = ["coins", "k coins", "m coins", "b coins", "Tr", "Q"]
    while inputPrize > 1000:
        inputPrize = inputPrize/1000
        exponent += 1
        if exponent > 5:
            return "Overfolw"
    return str(round(inputPrize, 1)) +" "+ prefix[exponent]