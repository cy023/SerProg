# -*- coding: utf-8 -*-
"""Intel hex functions.

This module provides functions to handle ihex file.
Include parse, format check and others.

Ihex file means the file which is in "Intel Hex Format".
The ihex is common use to store program data. And many mcu
loader is supprot ihex file. The output binary data of compiler
(e.g. GCC, ARMCC, IAR) is also ihex in fefault.

.. _Intel Hexadecimal Object File Format Specification:
    http://www.interlog.com/~speff/usefulinfo/Hexfrmt.pdf
"""

from serprog import exceptions

def parse(filename: str) -> list:
    """ Parse ihex file to data blocks.
    
    Args:
        filename (str): The file to parse.
    
    Raises:
        serprog.exceptions.IhexFormatError:
    
    Returns:
        list: data blocks with start address.
    """
    with open(filename, 'r') as hexfile:
        s_i = 0 # sections index
        sections = []
        ext_addr = 0
        eof_flag = False

        for line in hexfile.readlines():
            # NOTE line is end up with '\n'

            if len(line) < 12:
                # less than minimum length of General Record Format
                raise exceptions.IhexFormatError(filename)

            if line[0] != ':':
                # Record Mark is not ':'
                raise exceptions.IhexFormatError(filename)
            
            # parse basic info from line
            reclen = int(line[1:3], 16)
            address = int(line[3:7], 16)
            content_type = int(line[7:9], 16)
            chksum = int(line[-3:-1], 16)

            # check record length and parse data
            if reclen != 0:
                if len(line) != 12 + reclen * 2:
                    raise exceptions.IhexFormatError(filename)
                else:
                    data = bytearray.fromhex(line[9: 9 + reclen*2])
            else:
                data = b''
            if content_type == 0:
                # Data
                if s_i == 0:
                    sections += [{
                        'address': (ext_addr << 16) + address,
                        'data': data
                    }]
                    s_i = s_i + 1
                elif (
                    (ext_addr << 16) + address ==
                    sections[s_i-1]['address'] + len(sections[s_i-1]['data'])
                ):
                    sections[s_i-1]['data'] = sections[s_i-1]['data'] + data
                else:
                    sections += [{
                        'address': (ext_addr << 16) + address,
                        'data': data
                    }]
                    s_i = s_i + 1
            elif content_type == 1:
                # End Of File
                if address == 0:
                    eof_flag = True
                else:
                    raise exceptions.IhexFormatError(filename)
            elif content_type == 2:
                # Extended Segment Address
                pass
            elif content_type == 3:
                # Start Segment Address
                pass
            elif content_type == 4:
                # Extended Linear Address
                ext_addr = int(line[9:13], 16)
                pass
            elif content_type == 5:
                # Start Linear Address
                pass
    
    if eof_flag is False:
        raise exceptions.IhexFormatError(filename)

    return sections

def padding_space(h, pgsz: int, space_data: bytes) -> list: 
    """Padding each data block with `space_data` to let block size fit pgsz * N.
    
    Args:
        h (list): response from `serprog.ihex.parse`.
        pgsz (int): page size, e.g. 256, 512.
        space_data (bytes): the byte data used to padding.
    
    Returns:
        list: data blocks
    """
    res = []
    for sect in h:
        sect_addr = sect['address']
        sect_data = sect['data']

        # (start address) not equal (pgsz * N)
        # 0xFF padding forward
        if sect_addr % pgsz != 0:
            n = sect_addr // pgsz
            l = sect_addr - pgsz * n
            sect_addr = pgsz * n
            a = bytes([0xff for i in range(l)])
            sect_data = a + sect_data
        
        # (end address + 1) not equal (pgsz * N)
        # 0xFF padding
        if (sect_addr + len(sect_data)) % pgsz != 0:
            n = (sect_addr + len(sect_data)) // pgsz
            l = pgsz * (n + 1) - (sect_addr + len(sect_data))
            a = bytes([0xff for i in range(l)])
            sect_data = sect_data + a

        res += [{
            'address': sect_addr,
            'data': sect_data
        }]
    
    return res
        
def cut_to_pages(h, pgsz):
    """Cut each data block to pages.
    
    Args:
        h (list): response from `serprog.ihex.padding_space`.
        pgsz (int): page size, e.g. 256, 512.
    
    Returns:
        list: data pages
    """
    res = []
    for sect in h:
        sect_addr = sect['address']
        sect_data = sect['data']
        for i in range(len(sect_data)//pgsz):
            res += [{
                'address': sect_addr + i * pgsz,
                'data': sect_data[i * pgsz : i * pgsz + pgsz]
            }]
    return res


def is_ihex(filename: str) -> bool:
    """Check the file is ihex format.
    
    Args:
        filename (str): The file to check.
    
    Returns:
        bool: Ture or False.
    """
    try:
        parse(filename)
    except exceptions.IhexFormatError:
        return False
    return True
