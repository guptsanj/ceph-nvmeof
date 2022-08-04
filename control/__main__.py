#
#  Copyright (c) 2021 International Business Machines
#  All rights reserved.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  Authors: anita.shekar@ibm.com, sandy.kaur@ibm.com
#

import os
import logging
import argparse
from .server import GatewayServer
from .settings import Settings

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

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
    if not os.path.isfile(args.settings_file):
        logger.error(f"Settings file {args.settings_file} not found.")
        raise FileNotFoundError

    settings = Settings(args.settings_file)
    with GatewayServer(settings) as gateway:
        gateway.serve()
