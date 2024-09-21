#!/usr/bin/env -S python -u

#
# Download and extract data from OpenStreetMap.
# Data includes countries, level1area, leve2area, settlements.
# Downloaded data is cached. Extracted data is overwritten.
# Requires CLDR data for country\level1area\level2area hierarchy.
#

from _codes import LOCALE_TAGS
from argparse import ArgumentParser
from hashlib import sha512
from json import dumps
from json import loads
from os import makedirs
from os import scandir
from os.path import abspath
from os.path import dirname
from os.path import expanduser
from os.path import isfile
from os.path import join
from re import match
from requests import request
from sys import argv

parser = ArgumentParser(prog=argv[0], description="Download OSM (Open Street Map) data.")
parser.add_argument("--cache-path", help="Path to cache of downloaded files.", default="~/.cache/django-terran/osm/")
parser.add_argument("--service-url", help="URL of OverPass API service.", default="https://overpass-api.de/api/interpreter")
parser.add_argument("--data-path", required=True, help="Path to data files.")
parser.add_argument("--accept-license", required=True, action="store_true")
arguments = parser.parse_args()

OSM_OVERPASS_URL = arguments.service_url
OSM_CACHE_DIR_PATH = abspath(join(dirname(__file__), expanduser(arguments.cache_path)))
OSM_BASE_PATH = abspath(join(dirname(__file__), arguments.data_path, "osm"))
CLDR_BASE_PATH = abspath(join(dirname(__file__), arguments.data_path, "cldr"))

makedirs(OSM_CACHE_DIR_PATH, exist_ok=True)
makedirs(join(OSM_BASE_PATH, "countries"), exist_ok=True)

LOCALE_PREFIXES = {locale_tag: f"{locale_tag}:" for locale_tag in LOCALE_TAGS}
WIKIPEDIA_TAGS = {locale_tag: f"wikipedia:{locale_tag}:" for locale_tag in LOCALE_TAGS}
COUNTRY_CLDR_DATA = {}


def osm_request(query, cache_tag):
    query_hash = sha512(query.encode("utf-8")).hexdigest()
    cache_path = join(OSM_CACHE_DIR_PATH, f"{cache_tag}-{query_hash}.json")

    if isfile(cache_path):
        with open(cache_path, "r") as f:
            elements = loads(f.read())

            if len(elements) > 0:
                return elements

    areas_response = request("POST", OSM_OVERPASS_URL, data={"data": query})
    areas_response.raise_for_status()
    elements = areas_response.json()["elements"]

    if len(elements) > 0:
        with open(cache_path, "w") as f:
            f.write(dumps(elements, ensure_ascii=False, indent=4))

    return elements


def flatten_postal_codes(value):
    if value is None:
        return None
    elif isinstance(value, str):
        return [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        result = []

        for item in value:
            if item is None:
                pass
            elif isinstance(item, (str, list)):
                result.extend(flatten_postal_codes(item))

        return result
    else:
        print("FLATTEN_LIST ERROR", value)
        return None


def osm_data_from_element(element: dict, default_locale_tag: str):
    element_type = element["type"]

    if element_type == "area":
        element_type = "relation"
        element["id"] -= 3600000000

    element_tags = element.get("tags", {})
    element_names = {k: v for k, v in [(default_locale_tag, element_tags.get("name"))] if v is not None}

    for locale_tag in LOCALE_TAGS:
        name = element_tags.get(f"name:{locale_tag}")

        if name:
            element_names[locale_tag] = name

    element_prefixes = {k: v for k, v in [(default_locale_tag, element_tags.get("name:prefix"))] if v is not None}

    for locale_tag in LOCALE_TAGS:
        prefix = element_tags.get(f"name:prefix:{locale_tag}")

        if prefix:
            element_prefixes[locale_tag] = prefix

    postal_codes = flatten_postal_codes(
        [
            element_tags.get("postal_code"),
            element_tags.get("postal_codes"),
            element_tags.get("openGeoDB:postal_codes"),
        ]
    )
    wikipedia_pages = {}
    wikipedia_tag = element_tags.get("wikipedia")

    if wikipedia_tag:
        for locale_tag, locale_prefix in LOCALE_PREFIXES.items():
            if wikipedia_tag.startswith(locale_prefix):
                wikipedia_pages[locale_tag] = wikipedia_tag[len(locale_prefix) :]
                wikipedia_tag = None
                break

    if wikipedia_tag:
        wikipedia_pages[default_locale_tag] = wikipedia_tag

    for locale_tag, wikipedia_tag_name in WIKIPEDIA_TAGS.items():
        wikipedia_tag = element_tags.get(wikipedia_tag_name)

        if wikipedia_tag:
            wikipedia_pages[locale_tag] = wikipedia_tag

    population_text = element_tags.get("population", "")
    population_text = population_text.replace(",", "").replace(".", "").replace(" ", "").lower()
    population = 0

    if population_text and (population_text != "0"):
        try:
            population = int(population_text)
        except:
            if population == 0:
                for pattern1 in [
                    r"\A([0-9]+)\+\Z",
                    r"\A~([0-9]+)\Z",
                    r"\A>([0-9]+)\Z",
                    r"\A([0-9]+)(?:people|familias|hab|habitantes|habitants|households|households|多|户)\Z",
                    r"\A(?:below|environ|lessthan|约)([0-9]+)\Z",
                    r"\A(?:about|around|environ|lessthan|morethan)([0-9]+)(?:people|habitantes|habitants|households|households)\Z",
                    r"\A([0-9]+)\(2[012][0-9][0-9]\)\Z",
                ]:
                    m = match(pattern1, population_text)

                    if m:
                        population = int(m.group(1))
                        break

            if population == 0:
                for pattern2 in [r"\A([0-9]+)-([0-9]+)\Z"]:
                    m = match(pattern2, population_text)

                    if m:
                        n1 = int(m.group(1))
                        n2 = int(m.group(2))
                        population = max(n1, n2)
                        break

            if population == 0:
                if not match(r"\A[^0-9]+\Z", population_text):
                    print()
                    print(f"WARNING: Invalid population format; format='{element_tags['population']}'; element={element_type}/{element['id']}.")

    element_expando = {
        k: v
        for k, v in [
            ("open_street_map_type", element_type),
            ("open_street_map_id", element["id"]),
            ("open_street_map_place", element_tags.get("place")),
            ("postal_codes", postal_codes),
            ("email", element_tags.get("email") or element_tags.get("contact:email")),
            ("facebook", element_tags.get("facebook") or element_tags.get("contact:facebook")),
            ("instagram", element_tags.get("instagram") or element_tags.get("contact:instagram")),
            ("phone", element_tags.get("phone") or element_tags.get("contact:phone")),
            ("tripadvisor", element_tags.get("tripadvisor") or element_tags.get("contact:tripadvisor")),
            ("twitter", element_tags.get("twitter") or element_tags.get("contact:twitter")),
            ("url", element_tags.get("url") or element_tags.get("contact:url")),
            ("website", element_tags.get("website") or element_tags.get("contact:website")),
            ("youtube", element_tags.get("youtube") or element_tags.get("contact:youtube")),
            ("wikidata_page_name", element_tags.get("wikidata")),
            ("wikipedia_pages", wikipedia_pages),
        ]
        if v is not None
    }

    return {
        k: v
        for k, v in [
            (f"__{element_type.upper()}_NAME__", element_tags.get("name")),
            (f"__{element_type.upper()}_A2__", element_tags.get("ISO3166-2", "").replace("-", "").lower()),
            ("names", {k: v for k, v in sorted([(k, v) for k, v in element_names.items()], key=lambda n: n[0])}),
            ("prefixes", {k: v for k, v in sorted([(k, v) for k, v in element_prefixes.items()], key=lambda n: n[0])}),
            ("place", element_tags.get("place")),
            ("population", population),
            ("expando", element_expando),
            ("_open_street_map_tags", element_tags),
        ]
        if (v is not None) and (v != "")
    }


print()
print(f"Reading country CLDR data...")

with scandir(join(CLDR_BASE_PATH, "countries")) as dir_iterator:
    is_first = True

    for dir_entry in dir_iterator:
        if dir_entry.is_file() and dir_entry.name.endswith(".json"):
            country_code = dir_entry.name[0:2]

            print(f"{country_code}" if is_first else f", {country_code}", end="")
            is_first = False

            with open(dir_entry.path, "r") as f:
                COUNTRY_CLDR_DATA[country_code] = loads(f.read())

print()
print(f"Quering OSM service...")

is_first = True
for country_code, country_cldr_data in sorted(list(COUNTRY_CLDR_DATA.items()), key=lambda d: d[0]):
    print(f"{country_code}" if is_first else f", {country_code}", end="")
    is_first = False
    default_locale_tag = country_cldr_data["languages"][0]
    path = join(OSM_BASE_PATH, f"countries/{country_code}.json")

    areas_query = f"""[out:json][timeout:300];

area["ISO3166-2"~"^{country_code}.*"]["boundary"="administrative"]["admin_level"];

out body;"""
    area_elements = {}

    for area_element in osm_request(areas_query, country_code):
        if area_element["type"] == "area":
            iso3166 = area_element["tags"]["ISO3166-2"].replace("-", "").lower()
            area_elements[iso3166] = area_element

    level1areas_settlement_ids = set()
    level1areas_osm_data = []

    for level1area_cldr_data in country_cldr_data["level1areas"]:
        level1area_iso3166 = level1area_cldr_data["iso_3166_a2"]
        level1area_element = area_elements.get(level1area_iso3166)

        if level1area_element:
            level2areas_osm_data = []
            level2areas_settlement_ids = set()

            for level2area_cldr_data in level1area_cldr_data["level2areas"]:
                level2area_iso3166 = level2area_cldr_data["iso_3166_a2"]
                level2area_element = area_elements.get(level2area_iso3166)

                if level2area_element:
                    level2areas_settlements_osm_data = []
                    settlements_query = f"""[out:json][timeout:300];

(
area["ISO3166-2"="{level2area_element["tags"]["ISO3166-2"]}"][admin_level="{level2area_element["tags"]["admin_level"]}"];
)->.searchArea;

(
node["place"="city"](area.searchArea);
node["place"="town"](area.searchArea);
node["place"="village"](area.searchArea);
node["place"="hamlet"](area.searchArea);
);

out body;"""

                    for settlement_element in osm_request(settlements_query, level2area_element["tags"]["ISO3166-2"]):
                        if settlement_element["type"] == "node":
                            settlement_osm_data = osm_data_from_element(settlement_element, default_locale_tag)
                            settlement_osm_data["latitude"] = settlement_element["lat"]
                            settlement_osm_data["longitude"] = settlement_element["lon"]
                            level2areas_settlements_osm_data.append(settlement_osm_data)
                            level2areas_settlement_ids.add(settlement_element["id"])

                    level2area_osm_data = osm_data_from_element(level2area_element, default_locale_tag)
                    level2areas_settlements_osm_data = sorted(level2areas_settlements_osm_data, key=lambda d: d["expando"]["open_street_map_id"])
                    level2area_osm_data["settlements"] = level2areas_settlements_osm_data
                    level2areas_osm_data.append(level2area_osm_data)

            level1areas_settlements_osm_data = []
            settlements_query = f"""[out:json][timeout:300];

(
area["ISO3166-2"="{level1area_element["tags"]["ISO3166-2"]}"][admin_level="{level1area_element["tags"]["admin_level"]}"];
)->.searchArea;

(
node["place"="city"](area.searchArea);
node["place"="town"](area.searchArea);
node["place"="village"](area.searchArea);
node["place"="hamlet"](area.searchArea);
);

out body;"""

            for settlement_element in osm_request(settlements_query, level1area_element["tags"]["ISO3166-2"]):
                if settlement_element["type"] == "node":
                    if settlement_element["id"] not in level2areas_settlement_ids:
                        settlement_osm_data = osm_data_from_element(settlement_element, default_locale_tag)
                        settlement_osm_data["latitude"] = settlement_element["lat"]
                        settlement_osm_data["longitude"] = settlement_element["lon"]
                        level1areas_settlements_osm_data.append(settlement_osm_data)

                    level1areas_settlement_ids.add(settlement_element["id"])

            level1areas_settlements_osm_data = sorted(level1areas_settlements_osm_data, key=lambda d: d["expando"]["open_street_map_id"])
            level1area_osm_data = osm_data_from_element(level1area_element, default_locale_tag)
            level1area_osm_data["level2areas"] = level2areas_osm_data
            level1area_osm_data["settlements"] = level1areas_settlements_osm_data
            level1areas_osm_data.append(level1area_osm_data)

    country_settlements_osm_data = []
    settlements_query = f"""[out:json][timeout:300];

(
area["ISO3166-2"="{country_code}"][admin_level="2"];
)->.searchArea;

(
node["place"="city"](area.searchArea);
node["place"="town"](area.searchArea);
node["place"="village"](area.searchArea);
node["place"="hamlet"](area.searchArea);
);

out body;"""

    for settlement_element in osm_request(settlements_query, country_code):
        if settlement_element["type"] == "node":
            if settlement_element["id"] not in level1areas_settlement_ids:
                settlement_osm_data = osm_data_from_element(settlement_element, default_locale_tag)
                settlement_osm_data["latitude"] = settlement_element["lat"]
                settlement_osm_data["longitude"] = settlement_element["lon"]
                country_settlements_osm_data.append(settlement_osm_data)

    country_settlements_osm_data = sorted(country_settlements_osm_data, key=lambda d: d["expando"]["open_street_map_id"])
    country_osm_data = {
        "level1areas": level1areas_osm_data,
        "settlements": country_settlements_osm_data,
    }

    with open(path, "w") as f:
        f.write(dumps(country_osm_data, ensure_ascii=False, indent=4))

print()
