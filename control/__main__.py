#
#  Copyright (c) 2021 International Business Machines
#  All rights reserved.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  Authors: anita.shekar@ibm.com, sandy.kaur@ibm.com
#

import argparse
from .server import GatewayServer
from .settings import Settings

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="python3 -m control",
                                     description="Manage NVMe gateways")
    parser.add_argument(
        "-s",
        "--settings_file",
        default="main.settings",
        type=str,
        help="Path to settings file",
    )

    args = parser.parse_args()
    settings = Settings(args.settings_file)
    with GatewayServer(settings) as gateway:
        gateway.serve()
