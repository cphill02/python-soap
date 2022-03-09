import configparser
import os
from os.path import dirname, join, abspath

# a simple function to read an array of configuration files into a config object
# config .properties files must be in the same folder as this module
def read_config(cfg_files):
    if (cfg_files != None):
        config = configparser.ConfigParser()
        # merges all files into a single config
        for i, cfg_file in enumerate(cfg_files):
            cfg_file = abspath(join(dirname(__file__), cfg_file))
            if (os.path.exists(cfg_file)):
                config.read(cfg_file)
                config.sections()
        return config