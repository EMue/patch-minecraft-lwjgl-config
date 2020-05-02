#!/usr/bin/env python3

from minecraft_lwjgl_config import *
import hashlib
import json
import sys
from sys import stdin
import urllib.request

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

def parse_lib_name(lib_name):
    if lib_name.count(":") != 2:
        raise ValueError("Invalid library name: " + lib_name)
    org, module, version = lib_name.split(":")
    return (org, module, version)

def make_lib_name(org, module, version):
    return org + ":" + module + ":" + version

def make_default_url(url_prefix, linux_arch, lib_name, classifier):
    if url_prefix is None:
        raise ValueError("No URL prefix specified.")
    _, module, _ = parse_lib_name(lib_name)
    url = url_prefix + "/" + module + "/" + module
    if classifier is not None:
        url += "-" + classifier
        if linux_arch is not None and classifier.startswith("natives-linux"):
            url += "-" + linux_arch
    url += ".jar"
    return url

def patch_urls(config, make_url):
    artifacts = []
    scan_config(config, {
        "artifact": lambda *args: artifacts.append(args)
    })
    for artifact, lib_name, classifier in artifacts:
        artifact["url"] = make_url(lib_name, classifier)

def patch_size_hash(config):
    artifacts = []
    scan_config(config, {
        "artifact": lambda artifact, _2, _3: artifacts.append(artifact)
    })
    for artifact in artifacts:
        url = artifact["url"]
        print("Accessing " + url + "...", file = sys.stderr)
        with urllib.request.urlopen(url) as request:
            content = request.read()
            hash = hashlib.sha1()
            hash.update(content)
            artifact["size"] = len(content)
            artifact["sha1"] = hash.hexdigest()

def patch_natives(config, patched_natives):
    classifiers_list = []
    natives_list = []
    scan_config(config, {
        "classifiers": classifiers_list.append,
        "natives": lambda natives, name: natives_list.append(natives)
    })
    for classifiers in classifiers_list:
        for classifier in list(classifiers):
            if classifier.startswith("natives-"):
                suffix = classifier.split("-")[1]
                if suffix not in patched_natives:
                    del classifiers[classifier]
    for natives in natives_list:
        for native in list(natives):
            if natives[native].startswith("natives-"):
                suffix = natives[native].split("-")[1]
                if suffix not in patched_natives:
                    del natives[native]

def patch_version_build_type(config, patched_version, patched_build_type):
    lwjgl3_configs = []
    libraries = []
    scan_config(config, {
        "lwjgl3": lwjgl3_configs.append,
        "library": libraries.append
    })
    for lwjgl3_config in lwjgl3_configs:
        if patched_version:
            lwjgl3_config["version"] = patched_version
        if patched_build_type:
            lwjgl3_config["type"] = patched_build_type
    if patched_version:
        for library in libraries:
            org, module, version = parse_lib_name(library["name"])
            library["name"] = make_lib_name(org, module, patched_version)

args = parse_args(sys.argv[1:])
config = json.load(sys.stdin)

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

json.dump(config, sys.stdout, indent = 4)
