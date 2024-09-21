#!/usr/bin/env -S python -u

#
# Download and extract data from GitHub.
# Data includes SVG images of country flags.
# Downloaded data is cached. Extracted data is overwritten.
#


from _codes import COUNTRY_CODES
from argparse import ArgumentParser
from os import makedirs
from os import rename
from os.path import abspath
from os.path import basename
from os.path import dirname
from os.path import expanduser
from os.path import isfile
from os.path import join
from requests import request
from sys import argv
from zipfile import ZipFile

parser = ArgumentParser(prog=argv[0], description="Download flags of countries in SVG format.")
parser.add_argument("--cache-path", help="Path to cache of downloaded files.", default="~/.cache/django-terran/flags/")
parser.add_argument("--static-path", required=True, help="Path to static files.")
parser.add_argument("--accept-license", required=True, action="store_true")
arguments = parser.parse_args()

FLAG_URL = "https://github.com/lipis/flag-icons/archive/refs/heads/main.zip"
FLAG_FILE_NAME = basename(FLAG_URL)
FLAG_CACHE_DIR_PATH = abspath(join(dirname(__file__), expanduser(arguments.cache_path)))
FLAG_CACHE_FILE_PATH = join(FLAG_CACHE_DIR_PATH, FLAG_FILE_NAME)
FLAG_TEMP_FILE_PATH = join(FLAG_CACHE_DIR_PATH, "~temp~")
STATIC_PATH = abspath(join(dirname(__file__), expanduser(arguments.static_path)))

makedirs(FLAG_CACHE_DIR_PATH, exist_ok=True)
makedirs(STATIC_PATH, exist_ok=True)


if not isfile(FLAG_CACHE_FILE_PATH):
    print("Downloading flags ZIP archive...", end="")

    with request("GET", FLAG_URL, stream=True) as response:
        with open(FLAG_TEMP_FILE_PATH, mode="wb") as file:
            read_length = 0

            for chunk in response.iter_content(64 * 1024):
                file.write(chunk)
                read_length += len(chunk) // 1024
                print(f"\rDownloading flags... {read_length} Kb          ", end="")

    rename(FLAG_TEMP_FILE_PATH, FLAG_CACHE_FILE_PATH)

print()
print("Extracting flags ZIP archive...")

with ZipFile(FLAG_CACHE_FILE_PATH, "r") as zip_archive:
    namelist = set(zip_archive.namelist())

    with zip_archive.open("flag-icons-main/LICENSE", "r") as zip_item:
        license = zip_item.read()
        print(f"\033[33m{license.decode("utf-8")}\033[0m")
        print()

    with open(join(STATIC_PATH, "LICENSE"), "wb") as f:
        f.write(license)

    is_first = True

    for country_code in COUNTRY_CODES:
        path = f"flag-icons-main/flags/4x3/{country_code.lower()}.svg"

        if path in namelist:
            print(f"{country_code}" if is_first else f", {country_code}", end="")
            is_first = False

            with zip_archive.open(path, "r") as zip_item:
                svg_data = zip_item.read()

                with open(join(STATIC_PATH, f"{country_code}.svg"), "wb") as f:
                    f.write(svg_data)
        else:
            print()
            print(f"\033[31mmissing {country_code}\033[0m")
            is_first = True

print()
