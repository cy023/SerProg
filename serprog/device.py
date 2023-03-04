# -*- coding: utf-8 -*-
"""
Device list and the associated function.
"""

device_list = [
    {
        'name': 'auto',
        'dev_type': 0,
        'protocol_version': 0,
        'userapp_start': 0,
        'userapp_size':  0,
        'note': 'Default, auto detect device type.'
    },
    {
        'name': 'ATSAME54_DEVB',
        'dev_type': 1,
        'protocol_version': 1,
        'userapp_start': 0x00010000,
        'userapp_size':  0x000F0000,
        'note': ''
    }
    # {
    #     'name': 'NUM487KM_DEVB',
    #     'dev_type': 2,
    #     'protocol_version': 1,
    #     'userapp_start': 0x00010000,
    #     'userapp_size':  0x000F0000,
    #     'note': ''
    # },
]

def get_device_by_str(s: str) -> int:
    """ Get the device number.

    Args:
        s (str): String. Device name, device number are accepted.

    Returns:
        int: Device number. If returned -1, it failed. (wrong format s)
    """
    if s.isdigit():
        for d in device_list:
            if int(s) == d['dev_type']:
                return d['dev_type']
    else:
        for d in device_list:
            if s == d['name']:
                return d['dev_type']
    return -1
