# -*- coding: utf-8 -*-
"""
Sub-command implementation.
"""

from serprog import device
from serprog import loader
from serprog import exceptions

import serial.tools.list_ports

import progressbar
import serial
import sys

def do_print_devices(args):
    s  = "Available device list:\n"
    s += "    device name   \t num \t note\n"
    for dev in device.device_list:
        s += "  - {0:11s}  \t {1:4s}\t {2}\n".format(
            dev['name'], str(dev['dev_type']), dev['note'])

    print(s)

def do_print_ports(args):
    for (port, desc, hwid) in serial.tools.list_ports.comports():
        print("{:20}".format(port))
        print("    desc: {}".format(desc))
        print("    hwid: {}".format(hwid))

def do_prog(args):

    # Create Serial object
    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = 115200
    ser.timeout = 1
    try:
        ser.open()
    except:
        print('ERROR: com port has been opened by another application.').format(args.port)
        sys.exit(1)

    is_prog_flash     = bool(args.flash_file)
    is_ext_flash      = bool(args.ext_flash_file)
    is_prog_eeprom    = bool(args.eeprom_file)
    is_ext_flash_boot = bool(args.ext_flash_boot)

    # Device number
    device_type = device.get_device_by_str(args.device)

    try:
        l = loader.Loader(
            ser               = ser,
            device_type       = device_type,
            is_flash_prog     = is_prog_flash,
            is_ext_flash_prog = is_ext_flash,
            is_eeprom_prog    = is_prog_eeprom,
            is_ext_flash_boot = is_ext_flash_boot,
            is_go_app         = args.is_go_app,
            flash_file        = args.flash_file,
            ext_flash_file    = args.ext_flash_file,
            eeprom_file       = args.eeprom_file,
            go_app_delay      = args.go_app_delay
        )
    except exceptions.ComuError:
        print("ERROR: Can't communicate with the device.")
        print("       Please check the comport and the device.")
        sys.exit(1)
    except exceptions.CheckDeviceError as e:
        print("ERROR: Device is not match.")
        print("       Assigned device is '{0:s}'".format(device.device_list[e.in_dev]['name']))
        print("       Detected device is '{0:s}'".format(device.device_list[e.real_dev]['name']))
        sys.exit(1)

    print("Device is '{0:s}'".format(device.device_list[l.device_type]['name']))
    print('Flash hex size is {0:0.2f} KB ({1} bytes)'.format(l.flash_size/1024, l.flash_size))
    print('Externel Flash hex size is {0:0.2f} KB ({1} bytes)'.format(l.ext_flash_size/1024, l.ext_flash_size))
    print('EEPROM hex size is {0} bytes.'.format(l.eeprom_size))
    print('Estimated time  is {0:0.2f} s.'.format(l.prog_time))

    widgets = [
        ' [', progressbar.Timer('Elapsed Time: %(seconds)0.2fs', ), '] ',
        progressbar.Bar(),
        progressbar.Counter(format='%(percentage)0.2f%%'),
    ]

    bar = progressbar.ProgressBar(max_value=l.total_steps, widgets=widgets)
    bar.update(0)
    for i in range(l.total_steps):
        try:
            l.do_step()
            bar.update(i)
        except exceptions.ComuError:
            print("ERROR: Can't communicate with the device.")
            print("Please check the comport is correct.")
            break
        except Exception:
            bar.finish(end='\n', dirty=True)
            print("ERROR: Can't communicate with the device.")
            print("Please check the comport is correct.")
            break

    bar.finish(end='\n')
    ser.close()
