#
#  Copyright (c) 2021 International Business Machines
#  All rights reserved.
#
#  SPDX-License-Identifier: LGPL-3.0-or-later
#
#  Authors: anita.shekar@ibm.com, sandy.kaur@ibm.com
#

import os
import configparser
import logging


class Settings:
    def __init__(self, filename):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger()
        if not os.path.isfile(filename):
            self.logger.error(f"Settings file {filename} not found.")
            raise FileNotFoundError
        self._settings = configparser.ConfigParser()
        self._settings.read(filename)

    def get(self, section, param):
        return self._settings.get(section, param)

    def getboolean(self, section, param):
        return self._settings.getboolean(section, param)

    def getint(self, section, param):
        return self._settings.getint(section, param)

    def getfloat(self, section, param):
        return self._settings.getfloat(section, param)

    def get_with_default(self, section, param, value):
        return self._settings.get(section, param, fallback=value)

    def getboolean_with_default(self, section, param, value):
        return self._settings.getboolean(section, param, fallback=value)

    def getint_with_default(self, section, param, value):
        return self._settings.getint(section, param, fallback=value)

    def getfloat_with_default(self, section, param, value):
        return self._settings.getfloat(section, param, fallback=value)
