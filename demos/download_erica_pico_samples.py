#!/usr/bin/env python

"""
Download Erica Synths Pico Drum sample packs from their official server.

Saves samples to tmp/erica-pico-samples/ (local to pym8 project)

Original source: https://github.com/jhw (gist)
Adapted for pym8 demos.
"""

import json
import os
import re
import urllib.request
from pathlib import Path

Endpoint = "http://data.ericasynths.lv/picodrum"

# Local output directory (relative to project root)
OUTPUT_DIR = Path("tmp/erica-pico-samples")


def fetch_json(path, endpoint=Endpoint):
    """Fetch JSON data from Erica Synths server."""
    return json.loads(urllib.request.urlopen(f"{endpoint}/{path}").read())


def pack_list():
    """Get list of available sample packs."""
    return {item["name"]: item["file"] for item in fetch_json("pack_list.json")}


def fetch_bin(path, endpoint=Endpoint):
    """Fetch binary data from Erica Synths server."""
    return urllib.request.urlopen(f"{endpoint}/{path}").read()


def directory_name(pack_name):
    """Convert pack name to directory name."""
    pack_slug = pack_name.lower().replace(" ", "-")
    return OUTPUT_DIR / pack_slug


def filter_blocks(buf):
    """Extract individual WAV files from pack binary."""
    def format_block(i, block):
        tokens = block.split(b"data")
        name = tokens[0][1:-1]
        data = (b"data".join(tokens[1:]))
        offset = data.index(b"RIFF")
        return (i, name, data[offset:])
    return [format_block(i, block.split(b"<?xpacket begin")[0])
            for i, block in enumerate(buf.split(b"\202\244name")[1:])]


def init_project(fn):
    """Decorator to create output directory if needed."""
    def wrapped(pack_name, pack_file):
        dir_name = directory_name(pack_name)
        if not dir_name.exists():
            dir_name.mkdir(parents=True)
        return fn(pack_name, pack_file)
    return wrapped


@init_project
def dump_blocks(pack_name, pack_file):
    """Download and extract all samples from a pack."""
    dir_name = directory_name(pack_name)
    buf = fetch_bin(pack_file)
    blocks = filter_blocks(buf)
    for i, block_name, block in blocks:
        tokens = block_name.decode('utf-8').split(".")
        stub, ext = re.sub("\\W", "", "".join(tokens[:-1])), tokens[-1]
        file_name = dir_name / f"{stub}.{ext}"
        with open(file_name, 'wb') as f:
            f.write(block)


def main():
    """Download all Erica Pico sample packs."""
    print(f"Downloading Erica Synths Pico Drum sample packs...")
    print(f"Output directory: {OUTPUT_DIR.absolute()}\n")

    try:
        packs = pack_list()
        print(f"Found {len(packs)} packs to download:\n")

        for i, (pack_name, pack_file) in enumerate(packs.items(), 1):
            print(f"[{i}/{len(packs)}] Downloading: {pack_name}")
            dump_blocks(pack_name, pack_file)

        print(f"\n✓ All packs downloaded to {OUTPUT_DIR.absolute()}")
        print(f"  Total packs: {len(packs)}")

    except Exception as error:
        print(f"\n✗ Error: {error}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
