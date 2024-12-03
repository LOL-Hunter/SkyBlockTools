from pysettings.jsonConfig import JsonConfig
from requests import get as getReq
from requests.exceptions import ConnectionError, ReadTimeout
from hyPI.hypixelAPI.loader import HypixelBazaarParser, HypixelAuctionParser, HypixelItemParser
from hyPI.constants import HypixelAPIURL, Config
from hyPI.APIError import NoAPIKeySetException, APIConnectionError, APITimeoutException

def APILoader(url:HypixelAPIURL, api_key, name, **kwargs) -> dict | None:
    if api_key == "": raise NoAPIKeySetException()
    data = {**{
             "key":api_key,
             "name":name,
            },
            **kwargs}
    if data["key"] == "": raise NoAPIKeySetException()

    try:
        return getReq(url.value, data).json()
    except ConnectionError:
        raise APIConnectionError(url)
    except ReadTimeout:
        raise APITimeoutException(url)

def fileLoader(path:str)->dict:
    return JsonConfig.loadConfig(path).data

