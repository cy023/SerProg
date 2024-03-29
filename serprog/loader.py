# -*- coding: utf-8 -*-
""" Loader API
CommandTrnasHandler Object is internal object of Loader.
"""

import enum
import os
import time
import serial
import sys
import datetime
from pathlib import Path

from serprog import bootprotocol
from serprog import device
from serprog import exceptions
from serprog import ihex

from typing import Union

__all__ = ['Loader']


class CommandTrnasHandler():
    """ Manager of Command Response.

    The main task.
        1. Send command
        2. wait
        3. Receive response

    You can use the functions `cmd_xxx` to send commands and receive responses.
    For the parameters of each command, see the function and bootprotocol specifications.
    """

    def __init__(self, ser: serial.Serial):
        """ Initialization
        Args:
            ser (serial.Serial): The serial object used for communication must be opened by the outside first.
        """
        self._ser = ser
        self._pd = bootprotocol.Decoder()
        self.timeout = 5

    def _get_packet(self):
        """ Get Packet function (polling)

        Raises:
            exceptions.ComuError: Timeout or packet format error.

        Returns:
            [dict[serprog.alp.Command, bytearray]]: Packet object.

        Packet object format:
            res = {
                'command': (serprog.alp.Command) command number,
                'data': (bytearray) packet data.
            }
        """
        if sys.platform == 'win32':
            start_time = time.perf_counter()
        elif sys.platform == 'linux':
            start_time = time.process_time()

        exec_time = 0
        exit_flag = False
        pac_decode_err_flag = False
        packet = None

        while exec_time < 3 and exit_flag is False:
            ch = self._ser.read(1)

            if len(ch) != 0:
                self._pd.step(ch[0])

            if self._pd.isDone():
                packet = self._pd.getPacket()
                exit_flag = True
            elif self._pd.isError():
                pac_decode_err_flag = True
                exit_flag = True

            if sys.platform == 'win32':
                exec_time = time.perf_counter() - start_time
            elif sys.platform == 'linux':
                exec_time = time.process_time() - start_time

        if exec_time > self.timeout:
            # TODO: timeout error, packet format error
            raise exceptions.ComuError

        if pac_decode_err_flag:
            # packet decode error
            raise exceptions.ComuError
        # print('\033[93m' + '[_get_packet]' + '\033[0m', packet)
        return packet

    def _block_get_packet(self):
        """ Get Packet function (blocking mode), for the long time operation.
        """
        packet = None

        while True:
            ch = self._ser.read(1)

            if len(ch) != 0:
                self._pd.step(ch[0])

            if self._pd.isDone():
                packet = self._pd.getPacket()
                break
            elif self._pd.isError():
                raise exceptions.ComuError
        # print('\033[93m' + '[_block_get_packet]' + '\033[0m', packet)
        return packet

    def _put_packet(self, cmd: Union[bootprotocol.CMD, int], data: bytearray):
        """ Put Packet function (polling)

        Args:
            cmd (Union[alp.Command, int]): command number.
            data (bytearray): packet data.
        """
        req_raw = bootprotocol.encode(cmd, data)
        # print('\033[93m' + '\n[_put_packet]' + '\033[0m', req_raw)
        self._ser.write(req_raw)

    ###############################

    def cmd_chk_protocol(self):
        self._put_packet(bootprotocol.CMD.CHK_PROTOCOL, b'test')
        res = self._get_packet()

        if res == None:
            return False, 0
        elif res['command'] == bootprotocol.CMD.CHK_PROTOCOL and res['data'][0] == 0:
            return True, res['data'][1]
        else:
            return False, 0

    def cmd_chk_device(self):
        self._put_packet(bootprotocol.CMD.CHK_DEVICE, b'')
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.CHK_DEVICE and res['data'][0] == 0:
            return True, res['data'][1]
        else:
            return False, int(0)

    def cmd_prog_end(self):
        self._put_packet(bootprotocol.CMD.PROG_END, b'')
        res = self._get_packet()
        return res['command'] == bootprotocol.CMD.PROG_END and res['data'][0] == 0

    def cmd_prog_ext_flash_boot(self):
        self._put_packet(bootprotocol.CMD.PROG_EXT_FLASH_BOOT, b'')
        res = self._block_get_packet() # waiting for a while ...
        return res['command'] == bootprotocol.CMD.PROG_EXT_FLASH_BOOT and res['data'][0] == 0

    def cmd_flash_set_pgsz(self, size):
        self._put_packet(bootprotocol.CMD.FLASH_SET_PGSZ, size.to_bytes(4, 'little'))
        res = self._get_packet()
        return res['command'] == bootprotocol.CMD.FLASH_SET_PGSZ and res['data'][0] == 0

    def cmd_flash_get_pgsz(self):
        self._put_packet(bootprotocol.CMD.FLASH_GET_PGSZ, b'')
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.FLASH_GET_PGSZ and res['data'][0] == 0:
            return True, int.from_bytes(res['data'][1:3], 'little')
        else:
            return False, int(0)

    ###############################

    def cmd_flash_write(self, page_addr, data):
        paylod = page_addr.to_bytes(4, 'little') + data
        self._put_packet(bootprotocol.CMD.FLASH_WRITE, paylod)
        res = self._get_packet()
        return res['command'] == bootprotocol.CMD.FLASH_WRITE and res['data'][0] == 0

    def cmd_flash_read(self):
        self._put_packet(bootprotocol.CMD.FLASH_READ, b'')
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.FLASH_READ and res['data'][0] == 0:
            return True, res['data']
        else:
            return False, bytearray(b'')

    def cmd_flash_erase_sector(self, num):
        self._put_packet(bootprotocol.CMD.FLASH_ERASE_SECTOR,
                         num.to_bytes(2, 'little'))
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.FLASH_ERASE_SECTOR and res['data'][0] == 0:
            return True, int.from_bytes(res['data'][1:5], 'little')
        else:
            return False, int(0)
        
    def cmd_flash_erase_all(self):
        self._put_packet(bootprotocol.CMD.FLASH_ERASE_ALL, b'')
        res = self._block_get_packet() # waiting for a while ...
        return res['command'] == bootprotocol.CMD.FLASH_ERASE_ALL and res['data'][0] == 0

    ###############################

    def cmd_ext_flash_fopen(self):
        self._put_packet(bootprotocol.CMD.EXT_FLASH_FOPEN, b'fopen')
        res = self._get_packet()
        return res['command'] == bootprotocol.CMD.EXT_FLASH_FOPEN and res['data'][0] == 0

    def cmd_ext_flash_write(self, page_addr, data):
        paylod = page_addr.to_bytes(4, 'little') + data
        self._put_packet(bootprotocol.CMD.EXT_FLASH_WRITE, paylod)
        res = self._get_packet()
        return res['command'] == bootprotocol.CMD.EXT_FLASH_WRITE and res['data'][0] == 0

    def cmd_ext_flash_read(self):
        pass

    def cmd_ext_flash_fclose(self):
        now = datetime.datetime.now()
        t_stamp = bytearray([now.minute, now.hour, now.day, now.month, (now.year - 2000)])
        self._put_packet(bootprotocol.CMD.EXT_FLASH_FCLOSE, t_stamp)
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.EXT_FLASH_FCLOSE and res['data'][0] == 0:
            return True
        else:
            return False

    ###############################

    def cmd_eeprom_set_pgsz(self, size):
        self._put_packet(bootprotocol.CMD.EEPROM_SET_PGSZ, size.to_bytes(4, 'little'))
        res = self._get_packet()
        return res['command'] == bootprotocol.CMD.EEPROM_SET_PGSZ and res['data'][0] == 0

    def cmd_eeprom_get_pgsz(self):
        self._put_packet(bootprotocol.CMD.EEPROM_GET_PGSZ, b'')
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.EEPROM_GET_PGSZ and res['data'][0] == 0:
            return True, int.from_bytes(res['data'][1:3], 'little')
        else:
            return False, int(0)

    def cmd_eeprom_write(self, page_data):
        self._put_packet(bootprotocol.CMD.EEPROM_WRITE, page_data)
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.EEPROM_WRITE and res['data'][0] == 0:
            return True, int.from_bytes(res['data'][1:5], 'little')
        else:
            return False, int(0)

    def cmd_eeprom_read(self):
        self._put_packet(bootprotocol.CMD.EEPROM_READ, b'')
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.EEPROM_READ and res['data'][0] == 0:
            return True, int.from_bytes(res['data'][1:5], 'little')
        else:
            return False, int(0)

    def cmd_eeprom_erase(self):
        self._put_packet(bootprotocol.CMD.EEPROM_ERASE, b'')
        res = self._get_packet()
        if res['command'] == bootprotocol.CMD.EEPROM_ERASE and res['data'][0] == 0:
            return True, int.from_bytes(res['data'][1:5], 'little')
        else:
            return False, int(0)

    def cmd_eeprom_erase_all(self):
        self._put_packet(bootprotocol.CMD.EEPROM_ERASE_ALL, b'')
        res = self._get_packet()
        return res['command'] == bootprotocol.CMD.EEPROM_ERASE_ALL and res['data'][0] == 0


class Loader():
    """ Programming transaction management object.

    Raises:
        exceptions.CheckDeviceError: Device can't be dectected.
        exceptions.DeviceTypeError: The detected device is a different type than the specified device.
        FileNotFoundError: Can't find flash or eeprom programming file (image).
        exceptions.ComuError: Communication error.
        exceptions.FlashIsNotIhexError: The flash programming file (image) is not intel hex format.
        exceptions.EepromIsNotIhexError: The eeprom programming file (image) is not intel hex format.
    """
    _device_type       = int()
    _device_name       = str()

    _is_flash_prog     = bool()
    _is_ext_flash_prog = bool()
    _is_ext_flash_boot = bool()
    _is_eeprom_prog    = bool()

    _flash_file        = str()
    _ext_flash_file    = str()
    _eeprom_file       = str()

    class _Stage(enum.IntEnum):
        """ Programming transaction management object status
        """
        PREPARE        = 0  # Preparing. check image file, parameter ...
        FLASH_PROG     = 1  # flash programming ...
        EEPROM_PROG    = 2  # eeprom programming ...
        EXT_FLASH_PROG = 3  # external flash programming ...
        EXT_FLASH_BOOT = 4  # external to internel programming ...
        END            = 5  # Finish. Send 'END' or 'JUMP to APP' command.

    _stage = _Stage(_Stage.PREPARE)
    _stage_iter = None

    _total_steps = 0
    _cur_step    = 0

    _flash_pages        = list()
    _flash_page_idx     = int()
    _ext_flash_pages    = list()
    _ext_flash_page_idx = int()
    _eeprom_pages       = list()
    _eeprom_page_idx    = int()

    # output info
    _flash_size     = int(0)
    _ext_flash_size = int(0)
    _eeprom_size    = int(0)
    _prog_time      = float(0)

    def __init__(
        self,
        ser:                serial.Serial,
        device_type:        int = 0,
        is_flash_prog:      bool = False,
        is_ext_flash_prog:  bool = False,
        is_eeprom_prog:     bool = False,
        is_ext_flash_boot:  bool = False,
        flash_file:         str = '',
        ext_flash_file:     str = '',
        eeprom_file:        str = '',
    ):
        """ Initialization

        Args:
            ser (serial.Serial):
                The serial object used for communication must be opened by the outside first.
            device_type (int, optional):
                Device type. The default is 0.
            is_flash_prog (bool, optional):
                Whether to program flash. The default is False.
            is_ext_flash_prog (bool, optional):
                Whether to program external flash. The default is False.
            is_eeprom_prog (bool, optional):
                Whether to program eeprom. The default is False.
            is_ext_flash_boot (bool, optional):
                Whether to burn files from external flash to internal flash. The default is False.
            flash_file (str, optional):
                The flash image. The default is ''.
            eeprom_file (str, optional):
                The eeprom image. The default is ''.
        """
        self._ser = ser

        self._cth = CommandTrnasHandler(ser)

        self._device_type       = device_type
        self._is_flash_prog     = is_flash_prog
        self._is_ext_flash_prog = is_ext_flash_prog
        self._is_eeprom_prog    = is_eeprom_prog
        self._is_ext_flash_boot = is_ext_flash_boot
        self._flash_file        = flash_file
        self._ext_flash_file    = ext_flash_file
        self._eeprom_file       = eeprom_file

        self._prepare()

        self._prog_time

    @property
    def stage(self):
        return self._stage

    @property
    def device_type(self):
        return self._device_type

    @property
    def device_name(self):
        return self._device_name

    @property
    def total_steps(self):
        return self._total_steps

    @property
    def flash_size(self):
        return self._flash_size

    @property
    def ext_flash_size(self):
        return self._ext_flash_size

    @property
    def eeprom_size(self):
        return self._eeprom_size

    @property
    def prog_time(self):
        return self._prog_time

    @property
    def ext_flash_file(self):
        return Path(self._ext_flash_file).stem

    def _prepare(self):
        """ Preparation function before programming.

        1. Check parameters
        2. Check the flash and eeprom burning files
        3. Detection device
        4. Generate action list
        """
        if self._device_type > len(device.device_list):
            raise exceptions.DeviceTypeError(self._device_type)

        if self._is_flash_prog and os.path.isfile(self._flash_file) is False:
            raise FileNotFoundError

        if self._is_ext_flash_prog and os.path.isfile(self._ext_flash_file) is False:
            raise FileNotFoundError

        if self._is_eeprom_prog:
            if os.path.isfile(self._eeprom_file) is False:
                raise FileNotFoundError

        self._prepare_flash()
        self._prepare_ext_flash()
        self._prepare_eeprom()
        self._prepare_device()

        # Stage
        stg_list = list()
        if self._is_flash_prog:
            stg_list.append(self._Stage.FLASH_PROG)
            self._total_steps += len(self._flash_pages)
        if self._is_ext_flash_prog:
            stg_list.append(self._Stage.EXT_FLASH_PROG)
            self._total_steps += len(self._ext_flash_pages)
        if self._is_eeprom_prog:
            stg_list.append(self._Stage.EEPROM_PROG)
            self._total_steps += len(self._eeprom_pages)
        if self._is_ext_flash_boot:
            stg_list.append(self._Stage.EXT_FLASH_BOOT)
        stg_list.append(self._Stage.END)
        self._total_steps += 1
        self._stage_iter = iter(stg_list)
        self._stage = next(self._stage_iter)

        # prog time
        if self._device_type == 1: # D_ATSAME54_DEVB
            self._prog_time = len(self._flash_pages) * 0.23 + \
                                len(self._eeprom_pages) * 0.05 + \
                                len(self._ext_flash_pages) * 0.3 + 4.5
        if self._device_type == 2: # D_NUM487KM_DEVB
            self._prog_time = len(self._flash_pages) * 0.14 + \
                                len(self._eeprom_pages) * 0.05 + \
                                len(self._ext_flash_pages) * 0.2 + 3.3

    def _prepare_device(self):
        """ Check if the device matches the set device number.

        Raises:
            exceptions.ComuError: Unable to communicate
            exceptions.CheckDeviceError: Device comparison error.
        """
        res, self._protocol_version = self._cth.cmd_chk_protocol()

        if res and self._protocol_version == 1:
            res2, detected_device = self._cth.cmd_chk_device()
            if res2 is False:
                raise exceptions.ComuError()
        else:
            raise exceptions.ComuError()

        # auto detect device
        if device.device_list[self._device_type]['protocol_version'] == 0:
            self._device_type = detected_device

        elif device.device_list[self._device_type]['protocol_version'] == 1:
            if detected_device != self._device_type:
                raise exceptions.CheckDeviceError(self._device_type, detected_device)

        self._device_name = device.device_list[self._device_type]['name']

    def _prepare_flash(self):
        """ Process flash programming file

        Raises:
            exceptions.FlashIsNotIhexError: flash image file is not in intel hex format.

        1. Detect whether it is intel hex format
        2. Take out the data
        3. padding_space
        4. cut_to_pages
        """
        if self._is_flash_prog:
            try:
                blocks = ihex.parse(self._flash_file)
                self._flash_size = sum([len(block['data']) for block in blocks])
                blocks = ihex.padding_space(blocks, 512, bytes.fromhex('FF'))
                self._flash_pages = ihex.cut_to_pages(blocks, 512)
            except Exception:
                raise exceptions.FlashIsNotIhexError(self._flash_file)
    
    def _prepare_ext_flash(self):
        """ Process external flash programming files

        The basic operation is the same as _prepare_flash, and the difference will only be made when sending subsequent packets.
        """
        if self._is_ext_flash_prog:
            try:
                blocks = ihex.parse(self._ext_flash_file)
                self._ext_flash_size = sum([len(block['data']) for block in blocks])
                blocks = ihex.padding_space(blocks, 512, bytes.fromhex('FF'))
                self._ext_flash_pages = ihex.cut_to_pages(blocks, 512)
            except Exception:
                raise exceptions.FlashIsNotIhexError(self._ext_flash_file)

    def _prepare_eeprom(self):
        # TODO Discuss eeprom programming specifications, and complete.
        """ Process eeprom programming file.

        Raises:
            exceptions.EepromIsNotIhexError: eeprom image file is not in intel hex format

        1. Detect whether it is intel hex format
        2. Take out the data
        3. padding_space
        4. cut_to_pages
        """
        if self._is_eeprom_prog:
            try:
                blocks = ihex.parse(self._eeprom_file)
                self._eeprom_size = sum([len(block['data']) for block in blocks])
                blocks = ihex.padding_space(blocks, 512, bytes.fromhex('FF'))
                self._eeprom_pages = ihex.cut_to_pages(blocks, 512)
            except Exception:
                raise exceptions.EepromIsNotIhexError(self._eeprom_file)

    def _do_flash_prog_step(self):
        address = self._flash_pages[self._flash_page_idx]['address']
        data = self._flash_pages[self._flash_page_idx]['data']

        if self._flash_page_idx == 0:
            self._cth.cmd_flash_erase_all()
        self._cth.cmd_flash_write(address, data)

        self._flash_page_idx += 1
        self._cur_step += 1

        if self._flash_page_idx == len(self._flash_pages):
            self._stage = next(self._stage_iter)

    def _do_ext_flash_prog_step(self):
        # Programming to external flash, the actual action content is the same as flash_prog
        address = self._ext_flash_pages[self._ext_flash_page_idx]['address']
        data = self._ext_flash_pages[self._ext_flash_page_idx]['data']

        if self._ext_flash_page_idx == 0:
            self._cth.cmd_ext_flash_fopen()
        self._cth.cmd_ext_flash_write(address, data)

        self._ext_flash_page_idx += 1
        self._cur_step += 1

        if self._ext_flash_page_idx == len(self._ext_flash_pages):
            self._cth.cmd_ext_flash_fclose()
            self._stage = next(self._stage_iter)

    def _do_ext_flash_boot_step(self):
        # Send external flash programming to internal flash command
        self._cth.cmd_prog_ext_flash_boot()

    def _do_eeprom_prog_step(self):
        self._cth.cmd_eeprom_write(self._eeprom_pages[self._eeprom_page_idx])

        self._eeprom_page_idx += 1
        self._cur_step += 1
        if self._eeprom_page_idx == len(self._eeprom_pages):
            self._stage = next(self._stage_iter)

    def _do_prog_end_step(self):
        self._cth.cmd_prog_end()
        self._cur_step += 1

    def do_step(self):
        if self.stage == self._Stage.FLASH_PROG:
            self._do_flash_prog_step()
        elif self.stage == self._Stage.EEPROM_PROG:
            self._do_eeprom_prog_step()
        elif self.stage == self._Stage.EXT_FLASH_PROG:
            self._do_ext_flash_prog_step()
        elif self.stage == self._Stage.EXT_FLASH_BOOT:
            self._do_ext_flash_boot_step()
        elif self.stage == self._Stage.END:
            self._do_prog_end_step()
