#!/usr/bin/env python3

import json
import sys
from sys import stdin

def patch_version(config, version):
    if "requires" not in config:
        raise ValueError("No requires")
    for requires in config["requires"]:
        uid = requires["uid"]
        if uid == "org.lwjgl3":
            if "equals" in requires:
                requires["equals"] = version
            if "suggests" in requires:
                requires["suggests"] = version
        break
    else:
        raise ValueError("requires: No org.lwjgl3")

def make_args():
    return {
            "version": None
    }

def parse_request(request, args):
    request_list = None
    request_name = request
    if request.count("=") == 1:
        request_name_raw, request_list_raw = request.split("=")
        request_name = request_name_raw.strip()
        request_list = [entry.strip() for entry in request_list_raw.split(",")]
    if (request_name == "version"
        and request_list is not None
        and len(request_list) == 1):
        args[request_name] = request_list[0]
    else:
        raise ValueError("Invalid request: " + request)

def parse_args(argv):
    args = make_args()
    for arg in argv:
        parse_request(arg, args)
    return args

def patch_from_args(config, args):
    if args["version"]:
        patch_version(config, args["version"])

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    config = json.load(sys.stdin)
    patch_from_args(config, args)
    json.dump(config, sys.stdout, indent = 4)
