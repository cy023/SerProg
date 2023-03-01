# -*- coding: utf-8 -*-
"""
CLI parameter paser
"""

from serprog import device
from serprog import business
from serprog import ihex

import serial.tools.list_ports
import argparse
import os


def parser_init(parser: argparse.ArgumentParser):

    parser.description = 'A serial and secure programming tool for microcontroller.'

    subparsers = parser.add_subparsers(dest='subcmd')

    # parser of 'prog' subcommand
    parser_pr = subparsers.add_parser(
        'prog',
        aliases = [],
        help = 'Program the image to the board.'
    )

    parser_prog_init(parser_pr)

    # parser of 'print-devices' subcommand
    parser_pd = subparsers.add_parser(
        'print-devices',
        aliases = ['pd'],
        help = 'List all available devices.'
    )

    # parser of 'print-ports' subcommand
    parser_pp = subparsers.add_parser(
        'print-ports',
        aliases = ['pp'],
        help = 'List all available serial ports.'
    )


def parser_prog_init(parser: argparse.ArgumentParser):
    """ Parser of CLI sub-command.

    Args:
        parser (argparse.ArgumentParser): Parser of CLI sub-command
    """

    ## Select device type. -d
    arg_d_help = 'The name or number of the device type to be programmed. '
    arg_d_help += 'Can see available device type by subcommand print-device-list.'
    parser.add_argument(
        *('-d', '--decice'),
        action      = 'store',
        dest        = 'device',
        type        = str,
        default     = 'auto',
        help        = arg_d_help
    )

    ## Select serial com port. -p
    arg_p_help = 'The serial port which program burn the device.'
    parser.add_argument(
        *('-p', '--port'),
        action      = 'store',
        dest        = 'port',
        type        = str,
        required    = True,
        help        = arg_p_help
    )

    # Select programmed flash image. -f
    arg_f_help = 'Set binary file which program to flash.'
    parser.add_argument(
        *('-f', '--flash'),
        action      = 'store',
        dest        = 'flash_file',
        type        = str,
        required    = False,
        help        = arg_f_help
    )

    # Select programmed external flash image. -E
    arg_E_help = 'Set binary file which program to externel flash.'
    parser.add_argument(
        *('-E', '--extflash'),
        action      = 'store',
        dest        = 'ext_flash_file',
        type        = str,
        required    = False,
        help        = arg_E_help
    )

    # Select programmed file name in embedded file system. -i
    arg_i_help = 'Program from externel flash to internel flash.'
    parser.add_argument(
        *('-i', '--ext2int'),
        action      = 'store_true',
        dest        = 'ext_to_int',
        # type        = str,
        required    = False,
        help        = arg_i_help
    )

    # Select programmed eeprom image. -e
    arg_e_help = 'Set binary file which program to eeprom.'
    parser.add_argument(
        *('-e', '--eeprom'),
        action      = 'store',
        dest        = 'eep_file',
        type        = str,
        required    = False,
        help        = arg_e_help
    )

    # Select execute after programming. -a
    arg_a_help = 'Enter the application after programing.'
    parser.add_argument(
        *('-a', '--after-prog-go-app'),
        action      = 'store_true',
        dest        = 'is_go_app',
        required    = False,
        help        = arg_a_help
    )

    # Select delay time of execution after programming. -D
    arg_D_help = 'Set delay time from programing completion to executing application.(in ms)'
    parser.add_argument(
        *('-D', '--go-app-delay'),
        dest        = 'go_app_delay',
        type        = int,
        required    = False,
        default     = 50,
        help        = arg_D_help
    )


def chk_prog_args(args: argparse.Namespace) -> bool:
    """ Check the 'prog' sub-command.

    Args:
        args (argparse.Namespace): CLI paser command.

    Returns:
        bool: True, legal; False, illegal.
    """

    ## Select device type. -d
    res = device.get_device_by_str(args.device)

    if res == -1:
        print('Error: Parameter --device is illegal.')
        business.do_print_devices(args)
        return False

    # Check whether it is ext_to_int status.
    if (args.ext_to_int):
        pass
    elif (args.flash_file is None) and (args.eep_file is None) and (args.ext_flash_file is None):
        errmsg = 'Error: No flash or eeprom needs to be burned, please use \'-f \', \'-e \', \'-E \' to specify the file.'
        print(errmsg)
        return False

    # Flash file check.
    if args.flash_file is not None:
        if not os.path.isfile(args.flash_file):
            errmsg = 'Error: Cannot find flash binary file {0}.'
            print(errmsg.format(args.flash_file))
            return False
        elif not ihex.is_ihex(args.flash_file):
            errmsg = 'Error: The flash binary file {0} is not ihex formatted.'
            print(errmsg.format(args.flash_file))
            return False

    # External flash file check.
    if args.ext_flash_file is not None:
        if not os.path.isfile(args.ext_flash_file):
            errmsg = 'Error: Cannot find flash binary file {0}.'
            print(errmsg.format(args.ext_flash_file))
            return False
        elif not ihex.is_ihex(args.ext_flash_file):
            errmsg = 'Error: The flash binary file {0} is not ihex formatted.'
            print(errmsg.format(args.ext_flash_file))
            return False

    # EEPROM file check.
    if args.eep_file is not None:
        if not os.path.isfile(args.eep_file):
            errmsg = 'Error: Cannot find eeprom binary file {0}.'
            print(errmsg.format(args.eep_file))
            return False
        elif not ihex.is_ihex(args.eep_file):
            errmsg = 'Error: The eeprom binary file {0} is not ihex formatted.'
            print(errmsg.format(args.eep_file))
            return False

    # Serial port check.
    if args.port not in [p[0] for p in serial.tools.list_ports.comports()]:
        print('Error: Cannot find serial port {0}.').format(args.port)
        print('The available serial ports are as follows:')
        business.do_print_ports(args)
        return False

def chk_print_ports_args(args: argparse.Namespace) -> bool:
    """ Check the 'print-ports' sub-command.

    Args:
        args (argparse.Namespace): CLI paser command.

    Returns:
        bool: True, legal; False, illegal.
    """
    # No check ...
    return True

def chk_print_devices_args(args: argparse.Namespace) -> bool:
    """ Check the 'print-devices' sub-command.

    Args:
        args (argparse.Namespace): CLI paser command.

    Returns:
        bool: True, legal; False, illegal.
    """
    # No check ...
    return True
