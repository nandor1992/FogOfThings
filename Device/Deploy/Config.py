#!/usr/bin/env python

import ConfigParser
Config=ConfigParser.ConfigParser()
Config.read("../config.ini")
print(Config.sections())
