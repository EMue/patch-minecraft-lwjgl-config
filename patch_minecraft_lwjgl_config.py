#!/usr/bin/env python3

from minecraft_lwjgl_config import *
import json
from sys import stdin

def make_args():
    return {
            "natives": None,
            "urls": False,
            "url-prefix": None,
            "linux-arch": None,
            "version": None,
            "build-type": None
    }

def parse_request(request, args):
    request_list = None
    request_name = request
    if request.count("=") == 1:
        request_name_raw, request_list_raw = request.split("=")
        request_name = request_name_raw.strip()
        request_list = [entry.strip() for entry in request_list_raw.split(",")]
    if request_name == "urls" and request_list is None:
        args["urls"] = True
    elif (request_name in (
            "natives", "url-prefix", "linux-arch", "version", "build-type")
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
    if args["version"] or args["build-type"]:
        patch_version_build_type(config, args["version"], args["build-type"])
    if args["natives"]:
        patch_natives(config, args["natives"])
    if args["urls"]:
        patch_urls(
                config,
                lambda lib_name, classifier: make_default_url(
                    args["url-prefix"], args["linux-arch"], lib_name, classifier))
        patch_size_hash(config)

if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    config = json.load(sys.stdin)
    patch_from_args(config, args)
    json.dump(config, sys.stdout, indent = 4)
