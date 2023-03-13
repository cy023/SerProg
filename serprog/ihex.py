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

    # IHEX record types
    DATA_RECORD = 0
    EOF_RECORD = 1
    EXT_SEG_ADDR_RECORD = 2
    START_SEG_ADDR_RECORD = 3
    EXT_LINEAR_ADDR_RECORD = 4
    START_LINEAR_ADDR_RECORD = 5

    with open(filename, 'r') as hexfile:
        sections = []
        section_index = 0
        extended_address = 0
        eof_flag = False

        for line in hexfile.readlines():
            # line is end up with '\n'
            if len(line) < 12:
                # less than minimum length of General Record Format
                raise exceptions.IhexFormatError(filename)

            # Check record mark
            if not line.startswith(':'):
                raise exceptions.IhexFormatError(filename)
            
            # Parse IHEX record fields
            record_length = int(line[1:3], 16)
            address = int(line[3:7], 16)
            record_type = int(line[7:9], 16)
            checksum = int(line[-3:-1], 16)

            # check record length and parse data
            if record_length != 0:
                if len(line) != 12 + record_length * 2:
                    raise exceptions.IhexFormatError(filename)
                else:
                    data = bytearray.fromhex(line[9 : 9 + record_length*2])
            else:
                data = b''

            if record_type == DATA_RECORD:
                # Data record
                if section_index == 0:
                    # First section
                    sections.append({
                        'address': (extended_address << 16) + address,
                        'data': data
                    })
                    section_index += 1

                elif (extended_address << 16) + address == sections[section_index-1]['address'] + len(sections[section_index-1]['data']):
                    # Add data to previous section
                    sections[section_index-1]['data'] += data

                else:
                    # Start new section
                    sections.append({
                        'address': (extended_address << 16) + address,
                        'data': data
                    })
                    section_index += 1

            elif record_type == EOF_RECORD:
                # End of file record
                if address == 0:
                    eof_flag = True
                else:
                    raise exceptions.IhexFormatError(filename)

            elif record_type == EXT_SEG_ADDR_RECORD:
                # Extended Segment Address
                pass

            elif record_type == START_SEG_ADDR_RECORD:
                # Start Segment Address
                pass

            elif record_type == EXT_LINEAR_ADDR_RECORD:
                # Extended Linear Address
                extended_address = int(line[9:13], 16)
                pass

            elif record_type == START_LINEAR_ADDR_RECORD:
                # Start Linear Address
                pass

        if not eof_flag:
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
        sect_addr, sect_data = sect['address'], sect['data']

        # (start address) not equal (pgsz * N)
        # Pad before the data
        start_padding_len = sect_addr % pgsz
        start_padding = bytes(space_data * start_padding_len)
        sect_data = start_padding + sect_data

        # (end address + 1) not equal (pgsz * N)
        # Pad after the data
        end_padding_len = pgsz - len(sect_data) % pgsz if len(sect_data) % pgsz != 0 else 0
        end_padding = bytes(space_data * end_padding_len)
        sect_data = sect_data + end_padding

        res.append({'address': (sect_addr // pgsz) * pgsz, 'data': sect_data})

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
        sect_addr, sect_data = sect['address'], sect['data']
        for i in range(0, len(sect_data), pgsz):
            page = {'address': sect_addr + i, 'data': sect_data[i : i + pgsz]}
            res.append(page)
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
