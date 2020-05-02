#!/usr/bin/env python3

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
