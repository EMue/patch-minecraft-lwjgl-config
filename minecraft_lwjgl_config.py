#!/usr/bin/env python3

import hashlib
import sys
import urllib.request

def handle(section, handlers, *args):
    if section in handlers:
        handlers[section](*args)

def scan_artifact(json, prefix, handlers, lib_name, classifier = None):
    for entry in ("sha1", "size", "url"):
        if not entry in json:
            raise ValueError(prefix + ": No " + entry)
    handle("artifact", handlers, json, lib_name, classifier)

def scan_classifiers(json, prefix, handlers, lib_name):
    for classifier in json:
        scan_artifact(
                json[classifier], prefix + [classifier], handlers, lib_name,
                classifier)

def scan_download(json, prefix, handlers, lib_name):
    if not "artifact" in json:
        raise ValueError(prefix + ": No artifact")
    scan_artifact(json["artifact"], prefix + ["artifact"], handlers, lib_name)
    if "classifiers" in json:
        handle("classifiers", handlers, json["classifiers"])
        scan_classifiers(
                json["classifiers"], prefix + ["classifiers"], handlers,
                lib_name)

def scan_library(json, prefix, handlers):
    if "name" not in json:
        raise ValueError(prefix + ": No name")
    handle("library", handlers, json)
    name = json["name"]
    if "downloads" in json:
        scan_download(json["downloads"], prefix + ["downloads"], handlers, name)
    if "natives" in json:
        handle("natives", handlers, json["natives"], name)

def scan_libraries(json, prefix, handlers):
    for i, library in enumerate(json):
        scan_library(library, prefix + ["[" + str(i) + "]"], handlers)

def scan_config(json, handlers):
    if not "libraries" in json:
        raise ValueError("No libraries")
    if not "type" in json:
        raise ValueError("No type")
    if not "version" in json:
        raise ValueError("No version")
    handle("lwjgl3", handlers, json)
    scan_libraries(json["libraries"], ["libraries"], handlers)

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
