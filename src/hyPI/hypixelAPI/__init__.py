from pysettings.jsonConfig import JsonConfig
from requests import get as getReq

from hyPI.hypixelAPI.loader import HypixelBazaarParser, HypixelAuctionParser, HypixelItemParser
from hyPI.constants import HypixelAPIURL, Config
from hyPI.APIError import NoAPIKeySetException


def APILoader(url:HypixelAPIURL, api_key, name, **kwargs)->dict:
    if api_key == "": raise NoAPIKeySetException()
    data = {**{
             "key":api_key,
             "name":name,
            },
            **kwargs}
    if data["key"] == "": raise NoAPIKeySetException()

    req = getReq(url.value, data)
    return req.json()

def fileLoader(path:str)->dict:
    return JsonConfig.loadConfig(path).data

