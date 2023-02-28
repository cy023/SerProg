# -*- coding: utf-8 -*-
class Error(Exception):
    pass

class IhexFormatError(Error):
    filename: str
    def __init__(self, filename):
        self.filename = filename

class FlashIsNotIhexError(Error):
    filename: str
    def __init__(self, filename):
        self.filename = filename

class EepromIsNotIhexError(Error):
    filename: str
    def __init__(self, filename):
        self.filename = filename

class DeviceTypeError(Error):
    device_type: int
    def __init__(self, device_type):
        self.device_type = device_type

class DeviceNotResponseError(Error):
    def __init__(self):
        pass

class GoAppDelayValueError(Error):
    delay: int
    def __init__(self, delay):
        self.delay = delay

class ComuError(Error):
    def __init__(self):
        pass

class CheckDeviceError(Error):
    in_dev: int
    real_dev: int
    def __init__(self, in_dev, real_dev):
        self.in_dev = in_dev
        self.real_dev = real_dev
