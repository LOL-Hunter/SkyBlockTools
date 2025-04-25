

class _BaseException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self._msg = message
    def getMessage(self):
        return self._msg

class YearNotAvailableInData(_BaseException):
    def __init__(self, year):
        super().__init__(f"Year {year} not available!")


class NoAPIKeySetException(_BaseException):
    def __init__(self):
        super().__init__(f"Wrong API-Key check the settings.")

class APITimeoutException(_BaseException):
    def __init__(self):
        super().__init__(f"Request timeout!")


class CouldNotReadDataPackageException(_BaseException):
    def __init__(self, data):
        _msg = "Could not decode api packet."
        if "cause" in data.keys():
            _msg += (" ["+data["cause"]+"]")
        super().__init__(_msg)


class APIOnCooldownException(_BaseException):
    def __init__(self):
        super().__init__(f"API is currently on cooldown\ntry again in a minute!")


class APIConnectionError(_BaseException):
    def __init__(self, url):
        url = url.value if hasattr(url, "value") else url
        super().__init__(f"Could not request API.\nCheck your internet connection.\nURL: {url}")






