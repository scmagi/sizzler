#!/usr/bin/env python3

import yaml

def loadConfigFile(filename):
    try:
        config = yaml.load(open(filename, "r").read())
    except:
        raise Exception("Cannot read given config file.")

    try:
        assert type(config["key"]) == str
        assert type(config["ip"]["server"]) == str
        assert type(config["ip"]["client"]) == str

    except:
        raise Exception("Malformed config file.")

    return config
