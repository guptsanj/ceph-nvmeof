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
from .settings import NVMeGWConfig

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="python3 -m control",
                                     description="Manage NVMe gateways")
    parser.add_argument(
        "-c",
        "--config",
        default="main.settings",
        type=str,
        help="Path to settings file",
    )

    args = parser.parse_args()
    settings = NVMeGWConfig(args.config)
    with GatewayServer(settings) as gateway:
        gateway.serve()
