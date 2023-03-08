# -*- coding: utf-8 -*-
"""
Bootloader Protocol implementation.
"""
import enum
from typing import Union

HEADER = b'\xA5\xA5\xA5'

class Command(enum.IntEnum):
    CHK_PROTOCOL            = 0x01
    CHK_DEVICE              = 0x02
    PROG_END                = 0x03
    PROG_EXT_FLASH_BOOT     = 0x04

    FLASH_SET_PGSZ          = 0x10
    FLASH_GET_PGSZ          = 0x11
    FLASH_WRITE             = 0x12
    FLASH_READ              = 0x13
    FLASH_VERIFY            = 0x14
    FLASH_EARSE_SECTOR      = 0x15
    FLASH_EARSE_ALL         = 0x16

    EEPROM_SET_PGSZ         = 0x20
    EEPROM_GET_PGSZ         = 0x21
    EEPROM_WRITE            = 0x22
    EEPROM_READ             = 0x23
    EEPROM_EARSE            = 0x24
    EEPROM_EARSE_ALL        = 0x25

    EXT_FLASH_FOPEN         = 0x30
    EXT_FLASH_FCLOSE        = 0x31
    EXT_FLASH_WRITE         = 0x32
    EXT_FLASH_READ          = 0x33
    EXT_FLASH_VERIFY        = 0x34
    EXT_FLASH_EARSE_SECTOR  = 0x35
    EXT_FLASH_HEX_DEL       = 0x36

class Decoder(object):
    class _Status(enum.IntEnum):
        HEADER  = 0
        COMMAND = 1
        LENGTH  = 2
        DATA    = 3
        CHKSUM  = 4

    _header_buffer = b'\x00\x00\x00'
    _counter = int()
    _command = int()
    _length  = int()
    _data    = bytes()
    _chksum  = int()
    _isError = bool()
    _isDone  = bool()

    def __init__(self):
        super(Decoder, self).__init__()
        self._status = self._Status(self._Status.HEADER)

    def step(self, ch):

        if self._status is self._Status.HEADER:
            self._header_buffer = self._header_buffer[1:3] + bytes([ch])
            if self._header_buffer == HEADER:
                self._chksum = 0
                self._status = self._Status.COMMAND

        elif self._status is self._Status.COMMAND:
            self._command = Command(ch)
            self._counter = 0
            self._status = self._Status.LENGTH

        elif self._status is self._Status.LENGTH:
            self._counter = self._counter + 1
            if self._counter == 1:
                self._length = ch << 8
            elif self._counter == 2:
                self._length += ch
                self._counter = 0
                self._data = b''
                if self._length == 0:
                    self._status = self._Status.CHKSUM
                else:
                    self._status = self._Status.DATA

        elif self._status is self._Status.DATA:
            self._chksum += ch
            self._counter = self._counter + 1
            self._data += bytes([ch])
            if self._counter == self._length:
                self._status = self._Status.CHKSUM

        elif self._status is self._Status.CHKSUM:
            if self._chksum % 256 != ch:
                self._error = True
            self._status = self._Status.HEADER
            self._header_buffer = b'\x00\x00\x00'
            self._isDone = True

    def isDone(self):
        return self._isDone

    def isError(self):
        return self._isError

    def getPacket(self):
        if self.isDone():
            res = {
                'command': self._command,
                'data': self._data
            }
            self._isDone = False
        else:
            res = {
                'command': None,
                'data': b''
            }
        return res

def encode(cmd: Union[int, Command], data: bytes) -> bytes:
    """Encode command, data to a package.
    
    Args:
        cmd (Union[int, Command]): Command in the package.
        data (bytes): Data in the package.
    
    Returns:
        bytes: Package as bytes.
    """

    res  = bytes()
    res += HEADER
    res += cmd.to_bytes(1, 'little')
    res += len(data).to_bytes(2, 'big')
    res += data
    res += (sum(data) % 256).to_bytes(1, 'little')
    return res
