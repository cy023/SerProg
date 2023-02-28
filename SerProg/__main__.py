# -*- coding: utf-8 -*-
"""
SerProg CLI entry.
"""

from SerProg import cli_arg
from SerProg import business

import argparse
import sys

def run():
    # Parse CLI command
    parser = argparse.ArgumentParser()
    cli_arg.parser_init(parser)
    args = parser.parse_args()

    # Parse CLI sub-command
    if args.subcmd == 'print-devices' or args.subcmd == 'pd':
        if cli_arg.chk_print_devices_args(args) is False:
            sys.exit(1)
        else:
            business.do_print_devices(args)

    elif args.subcmd == 'print-ports' or args.subcmd == 'pp':
        if cli_arg.chk_print_ports_args(args) is False:
            sys.exit(1)
        else:
            business.do_print_ports(args)

    elif args.subcmd == 'prog':
        if cli_arg.chk_prog_args(args) is False:
            sys.exit(1)
        else:
            business.do_prog(args)

    else:
        parser.print_help()


if __name__ == '__main__':
    run()
