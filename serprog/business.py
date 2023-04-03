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
    print("Available device list:")
    print("    device name   \t num \t note")
    print("-" * 40)
    devices = [f"  - {dev['name']:11s}  \t {dev['dev_type']:4}\t {dev['note']}" for dev in device.device_list]
    print('\n'.join(devices))

def do_print_ports(args):
    for (port, desc, hwid) in serial.tools.list_ports.comports():
        print(f"{port:20}")
        print(f"    desc: {desc}")
        print(f"    hwid: {hwid}")

def do_prog(args):

    # Create Serial object
    ser = serial.Serial()
    ser.port = args.port
    ser.baudrate = 115200
    ser.timeout = 1
    try:
        ser.open()
    except:
        print(f"ERROR: {args.port} has been opened by another application.")
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
            flash_file        = args.flash_file,
            ext_flash_file    = args.ext_flash_file,
            eeprom_file       = args.eeprom_file,
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

    print(f"Device is '{device.device_list[l.device_type]['name']}'")
    print(f"Flash hex size is {l.flash_size/1024:.2f} KB ({l.flash_size} bytes)")
    print(f"Externel Flash hex size is {l.ext_flash_size/1024:.2f} KB ({l.ext_flash_size} bytes)")
    print(f"EEPROM hex size is {l.eeprom_size} bytes.")
    print(f"Estimated time  is {l.prog_time:.2f} s.")

    # Progress bar
    widgets = [
        ' [', progressbar.Timer('Elapsed Time: %(seconds)0.2fs', ), '] ',
        progressbar.Bar(),
        progressbar.Counter(format='%(percentage)0.2f%%'),
    ]

    bar = progressbar.ProgressBar(max_value=l.total_steps, widgets=widgets)
    bar.update(0)

    # Program device
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
