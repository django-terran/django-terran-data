#!/usr/bin/env -S python -u

#
# Generate fixtures from available data.
# Fixtures include Country, Currency, Level1Area, Level2Area, and Settlement models.
# See prepare-step-*.py scripts.
#

from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime
from itertools import batched
from json import dumps
from json import loads
from os import scandir
from os.path import abspath
from os.path import dirname
from os.path import join
from sys import argv

parser = ArgumentParser(prog=argv[0], description="Generate Django fixtures.")
parser.add_argument("--data-path", required=True, help="Path data files.")
parser.add_argument("--fixture-path", required=True, help="Path to fixture files.")
arguments = parser.parse_args()

FIXTURE_BASE_PATH = abspath(join(dirname(__file__), arguments.fixture_path))
CLDR_BASE_PATH = abspath(join(dirname(__file__), arguments.data_path, "cldr"))
OSM_BASE_PATH = abspath(join(dirname(__file__), arguments.data_path, "osm"))
USER_BASE_PATH = abspath(join(dirname(__file__), arguments.data_path, "user"))

# https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts
# Some CLDR and OSM names were copy-pasted from sources and have footnote superscripts in them.
FOOTNOTE_DIGITS = "¹²³⁴⁵⁶⁷⁸⁹"
PLACE_TYPES = {
    "city": ord("C"),
    "hamlet": ord("H"),
    "town": ord("T"),
    "village": ord("V"),
}

CURRENCY_CLDR_DATA = {}
COUNTRY_CLDR_DATA = {}
COUNTRY_OSM_DATA = {}
COUNTRY_USER_DATA = {}

GLOBAL_COUNTERS = defaultdict(int)
COUNTRY_COUNTERS = defaultdict(lambda: defaultdict(int))

now = datetime.now()
version = now.year * 10000 + now.month * 100 + now.day

print(f"Version = {version}")
print(f"Reading currency CLDR data")

with scandir(join(CLDR_BASE_PATH, "currencies")) as dir_iterator:
    is_first = True

    for dir_entry in dir_iterator:
        if dir_entry.is_file() and dir_entry.name.endswith(".json"):
            currency_code = dir_entry.name[0:3]

            print(f"{currency_code}" if is_first else f", {currency_code}", end="")
            is_first = False

            with open(dir_entry.path, "r") as f:
                CURRENCY_CLDR_DATA[currency_code] = loads(f.read())

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
print(f"Reading country OSM data...")

with scandir(join(OSM_BASE_PATH, "countries")) as dir_iterator:
    is_first = True

    for dir_entry in dir_iterator:
        if dir_entry.is_file() and dir_entry.name.endswith(".json"):
            country_code = dir_entry.name[0:2]

            print(f"{country_code}" if is_first else f", {country_code}", end="")
            is_first = False

            with open(dir_entry.path, "r") as f:
                COUNTRY_OSM_DATA[country_code] = loads(f.read())

print()
print(f"Reading country USER data...")

with scandir(join(USER_BASE_PATH, "countries")) as dir_iterator:
    is_first = True

    for dir_entry in dir_iterator:
        if dir_entry.is_file() and dir_entry.name.endswith(".json"):
            country_code = dir_entry.name[0:2]

            print(f"{country_code}" if is_first else f", {country_code}", end="")
            is_first = False

            with open(dir_entry.path, "r") as f:
                COUNTRY_USER_DATA[country_code] = loads(f.read())

print()
print(f"Writing currency fixtures...")

currencies_fixtures = []
is_first = True

for currency_code, cldr_data in sorted(CURRENCY_CLDR_DATA.items()):
    print(f"{currency_code}" if is_first else f", {currency_code}", end="")
    is_first = False

    currency_fixtures = []
    currency_fixtures.append(
        {
            "model": "terran.currency",
            "fields": {
                "iso_4217_n3": int(cldr_data["iso_4217_n3"]),
                "iso_4217_a3": cldr_data["iso_4217_a3"],
                "version": version,
                "names": {k: v.strip(FOOTNOTE_DIGITS) for k, v in cldr_data["names"].items()},
                "decimal_digits": cldr_data["decimal_digits"],
            },
        }
    )
    GLOBAL_COUNTERS["currencies"] += 1
    currencies_fixtures.extend(currency_fixtures)

currencies_fixtures = sorted(currencies_fixtures, key=lambda f: f["fields"]["iso_4217_n3"])

with open(join(FIXTURE_BASE_PATH, "currencies.json"), "w") as f:
    print(f"Writing {f.name} fixture")
    f.write(dumps(currencies_fixtures, ensure_ascii=False, indent=4))

print()
print(f"Writing country fixtures...")


def get_country_fixture(cldr_data: dict, user_data: dict):
    names = {k: v.strip(FOOTNOTE_DIGITS) for k, v in cldr_data["names"].items()}
    names = {k: v for k, v in sorted([(k, v) for k, v in names.items()], key=lambda n: n[0])}
    organization_id = user_data["organization_id"]
    person_id = user_data["person_id"]
    iban = user_data["iban"]

    return {
        "model": "terran.country",
        "fields": {
            "iso_3166_n3": int(cldr_data["iso_3166_n3"]),
            "iso_3166_a2": cldr_data["iso_3166_a2"],
            "iso_3166_a3": cldr_data["iso_3166_a3"],
            "version": version,
            "names": names,
            "currency": [cldr_data["currency"]],
            "languages": cldr_data["languages"],
            "address_input_layout": user_data["address"]["input_layout"],
            "address_output_format": user_data["address"]["output_format"],
            "address_level1area_names": user_data["address"]["level1area_names"],
            "address_level2area_names": user_data["address"]["level2area_names"],
            "address_settlement_names": user_data["address"]["settlement_names"],
            "address_postcode_names": user_data["address"]["postcode_names"],
            "address_postcode_input_pattern": user_data["address"]["postcode_input_pattern"],
            "address_postcode_input_example": user_data["address"]["postcode_input_example"],
            "address_street_names": user_data["address"]["street_names"],
            "phone_names": user_data["phone"]["names"],
            "phone_prefixes": user_data["phone"]["prefixes"],
            "phone_input_pattern": user_data["phone"]["input_pattern"],
            "phone_input_example": user_data["phone"]["input_example"],
            "phone_output_format": user_data["phone"]["output_format"],
            "organization_id_names": organization_id["names"] if organization_id else None,
            "organization_id_abbreviations": organization_id["abbreviations"] if organization_id else None,
            "organization_id_input_pattern": organization_id["input_pattern"] if organization_id else None,
            "organization_id_input_example": organization_id["input_example"] if organization_id else None,
            "organization_id_output_format": organization_id["output_format"] if organization_id else None,
            "person_id_names": person_id["names"] if person_id else None,
            "person_id_abbreviations": person_id["abbreviations"] if person_id else None,
            "person_id_input_pattern": person_id["input_pattern"] if person_id else None,
            "person_id_input_example": person_id["input_example"] if person_id else None,
            "person_id_output_format": person_id["output_format"] if person_id else None,
            "iban_names": iban["names"] if iban else None,
            "iban_input_pattern": iban["input_pattern"] if iban else None,
            "iban_input_example": iban["input_example"] if iban else None,
            "iban_output_format": iban["output_format"] if iban else None,
        },
    }


def get_currency_fixture(country_id: int, cldr_data: dict):
    return {
        "model": "terran.countrycurrency",
        "fields": {
            "country": country_id,
            "currency": cldr_data["iso_4217_a3"],
            "version": version,
            "since": cldr_data["since"],
            "until": cldr_data["until"],
        },
    }


def get_level1area_fixture(country_id: int, cldr_data: dict, osm_data: dict):
    names = {k: v.strip(FOOTNOTE_DIGITS) for k, v in cldr_data["names"].items()}
    names = {k: v for k, v in sorted([(k, v) for k, v in names.items()], key=lambda n: n[0])}
    return {
        "model": "terran.level1area",
        "fields": {
            "country": country_id,
            "iso_3166_a2": cldr_data["iso_3166_a2"],
            "version": version,
            "names": names,
            "expando": osm_data.get("expando", {}) if osm_data else {},
        },
    }


def get_level2area_fixture(country_id: int, level1area_id: str, cldr_data: dict, osm_data: dict):
    names = {k: v.strip(FOOTNOTE_DIGITS) for k, v in cldr_data["names"].items()}
    names = {k: v for k, v in sorted([(k, v) for k, v in names.items()], key=lambda n: n[0])}
    return {
        "model": "terran.level2area",
        "fields": {
            "country": country_id,
            "level1area": [level1area_id],
            "iso_3166_a2": cldr_data["iso_3166_a2"],
            "version": version,
            "names": names,
            "expando": osm_data.get("expando", {}) if osm_data else {},
        },
    }


def get_settlement_fixture(country_id: int, level1area_id: str, level2area_id: str, osm_data: dict):
    global last_settlement_id

    names = {k: v.strip(FOOTNOTE_DIGITS) for k, v in osm_data["names"].items()}
    names = {k: v for k, v in sorted([(k, v) for k, v in names.items()], key=lambda n: n[0])}
    expando = osm_data.get("expando", {})
    settlement_id = expando.get("open_street_map_id")
    population = osm_data.get("population", 0)
    latitude = osm_data.get("latitude", 0)
    longitude = osm_data.get("longitude", 0)
    geocell = 3600 * int(10 * (latitude + 90)) + int(10 * (longitude + 180))

    if not settlement_id:
        settlement_id = last_settlement_id
        last_settlement_id -= 1

    return {
        "model": "terran.settlement",
        "fields": {
            "id": settlement_id,
            "country": country_id,
            "level1area": [level1area_id] if level1area_id else None,
            "level2area": [level2area_id] if level2area_id else None,
            "version": version,
            "names": names,
            "place_type": PLACE_TYPES.get(osm_data["place"]),
            "population": population,
            "latitude": latitude,
            "longitude": longitude,
            "geocell": geocell,
            "expando": osm_data.get("expando"),
        },
    }


countries_fixtures = []
level1area_fixtures = []
level2area_fixtures = []
last_settlement_id = -1

for country_code, cldr_data in sorted(COUNTRY_CLDR_DATA.items()):
    user_data = COUNTRY_USER_DATA[country_code]
    osm_data = COUNTRY_OSM_DATA[country_code]
    country_id = int(cldr_data["iso_3166_n3"])
    settlement_fixtures = []
    settlement_10k_fixtures = []

    countries_fixtures.append(get_country_fixture(cldr_data, user_data))
    GLOBAL_COUNTERS["countries"] += 1

    for currency_cldr_data in sorted(cldr_data["currencies"], key=lambda c: c["since"]):
        countries_fixtures.append(get_currency_fixture(country_id, currency_cldr_data))
        COUNTRY_COUNTERS[country_code]["currencies"] += 1

    for settlement_osm_data in osm_data["settlements"]:
        names = {k: v.strip(FOOTNOTE_DIGITS) for k, v in settlement_osm_data["names"].items()}
        names = {k: v for k, v in sorted([(k, v) for k, v in names.items()], key=lambda n: n[0])}
        settlement_id = settlement_osm_data.get("expando", {}).get("open_street_map_id")

        if not settlement_id:
            settlement_id = last_settlement_id
            last_settlement_id -= 1

        settlement_fixture = get_settlement_fixture(country_id, None, None, settlement_osm_data)
        settlement_fixtures.append(settlement_fixture)

        if settlement_fixture["fields"]["population"] >= 10000:
            settlement_10k_fixtures.append(settlement_fixture)
            COUNTRY_COUNTERS[country_code]["settlements_10k"] += 1
            GLOBAL_COUNTERS["settlements_10k"] += 1

        COUNTRY_COUNTERS[country_code]["settlements"] += 1
        GLOBAL_COUNTERS["settlements"] += 1

    for level1area_cldr_data in sorted(cldr_data["level1areas"], key=lambda a: a["iso_3166_a2"]):
        if level1area_cldr_data["names"].get("en"):
            level1area_osm_data = None

            for data in osm_data["level1areas"]:
                if data["__RELATION_A2__"] == level1area_cldr_data["iso_3166_a2"]:
                    level1area_osm_data = data
                    break

            if not level1area_osm_data:
                print(f"WARNING: No OSM data for {level1area_cldr_data["iso_3166_a2"]}, {level1area_cldr_data["names"]["en"]}, {cldr_data["names"]["en"]}")

            level1area_fixtures.append(get_level1area_fixture(country_id, level1area_cldr_data, level1area_osm_data))
            COUNTRY_COUNTERS[country_code]["level1areas"] += 1
            GLOBAL_COUNTERS["level1areas"] += 1

    for level1area_cldr_data in sorted(cldr_data["level1areas"], key=lambda a: a["iso_3166_a2"]):
        if level1area_cldr_data["names"].get("en"):
            level1area_osm_data = None

            for data in osm_data["level1areas"]:
                if data["__RELATION_A2__"] == level1area_cldr_data["iso_3166_a2"]:
                    level1area_osm_data = data
                    break

            for level2area_cldr_data in sorted(level1area_cldr_data["level2areas"], key=lambda a: a["iso_3166_a2"]):
                if level2area_cldr_data["names"].get("en"):
                    level2area_osm_data = None

                    if level1area_osm_data:
                        for data in level1area_osm_data["level2areas"]:
                            if data["__RELATION_A2__"] == level2area_cldr_data["iso_3166_a2"]:
                                level2area_osm_data = data
                                break

                    if not level2area_osm_data:
                        print(
                            f"WARNING: No OSM data for {level2area_cldr_data["iso_3166_a2"]}, {level1area_cldr_data["names"]["en"]}, {level2area_cldr_data["names"]["en"]}, {cldr_data["names"]["en"]}"
                        )
                    names = {k: v.strip(FOOTNOTE_DIGITS) for k, v in level2area_cldr_data["names"].items()}
                    names = {k: v for k, v in sorted([(k, v) for k, v in names.items()], key=lambda n: n[0])}
                    level2area_fixtures.append(
                        get_level2area_fixture(country_id, level1area_cldr_data["iso_3166_a2"], level2area_cldr_data, level2area_osm_data)
                    )
                    COUNTRY_COUNTERS[country_code]["level2areas"] += 1
                    GLOBAL_COUNTERS["level2areas"] += 1

    for level1area_cldr_data in sorted(cldr_data["level1areas"], key=lambda a: a["iso_3166_a2"]):
        if level1area_cldr_data["names"].get("en"):
            level1area_osm_data = None

            for data in osm_data["level1areas"]:
                if data["__RELATION_A2__"] == level1area_cldr_data["iso_3166_a2"]:
                    level1area_osm_data = data
                    break

            if level1area_osm_data:
                for settlement_osm_data in level1area_osm_data["settlements"]:
                    settlement_fixture = get_settlement_fixture(country_id, level1area_cldr_data["iso_3166_a2"], None, settlement_osm_data)
                    settlement_fixtures.append(settlement_fixture)

                    if settlement_fixture["fields"]["population"] >= 10000:
                        settlement_10k_fixtures.append(settlement_fixture)
                        COUNTRY_COUNTERS[country_code]["settlements_10k"] += 1
                        GLOBAL_COUNTERS["settlements_10k"] += 1

                    COUNTRY_COUNTERS[country_code]["settlements"] += 1
                    GLOBAL_COUNTERS["settlements"] += 1

                for level2area_cldr_data in sorted(level1area_cldr_data["level2areas"], key=lambda a: a["iso_3166_a2"]):
                    if level2area_cldr_data["names"].get("en"):
                        level2area_osm_data = None

                        for data in level1area_osm_data["level2areas"]:
                            if data["__RELATION_A2__"] == level2area_cldr_data["iso_3166_a2"]:
                                level2area_osm_data = data
                                break

                        if level2area_osm_data:
                            for settlement_osm_data in level2area_osm_data["settlements"]:
                                settlement_fixture = get_settlement_fixture(
                                    country_id, level1area_cldr_data["iso_3166_a2"], level2area_cldr_data["iso_3166_a2"], settlement_osm_data
                                )
                                settlement_fixtures.append(settlement_fixture)

                                if settlement_fixture["fields"]["population"] >= 10000:
                                    settlement_10k_fixtures.append(settlement_fixture)
                                    COUNTRY_COUNTERS[country_code]["settlements_10k"] += 1
                                    GLOBAL_COUNTERS["settlements_10k"] += 1

                                COUNTRY_COUNTERS[country_code]["settlements"] += 1
                                GLOBAL_COUNTERS["settlements"] += 1

    settlement_fixtures = sorted(settlement_fixtures, key=lambda s: s["fields"]["id"])

    for index, fixtures in enumerate(batched(settlement_fixtures, 50000)):
        with open(join(FIXTURE_BASE_PATH, f"settlements/{country_code}-{index:03d}.json"), "w") as f:
            print(f"Writing {f.name} fixture, {len(fixtures)} settlements")
            f.write(dumps(fixtures, ensure_ascii=False, indent=4))

    settlement_10k_fixtures = sorted(settlement_10k_fixtures, key=lambda s: s["fields"]["id"])

    for index, fixtures in enumerate(batched(settlement_10k_fixtures, 50000)):
        with open(join(FIXTURE_BASE_PATH, f"settlements_10k/{country_code}-{index:03d}.json"), "w") as f:
            print(f"Writing {f.name} fixture, {len(fixtures)} settlements")
            f.write(dumps(fixtures, ensure_ascii=False, indent=4))

with open(join(FIXTURE_BASE_PATH, f"countries.json"), "w") as f:
    print(f"Writing {f.name} fixture")
    f.write(dumps(countries_fixtures, ensure_ascii=False, indent=4))

with open(join(FIXTURE_BASE_PATH, f"level1areas.json"), "w") as f:
    print(f"Writing {f.name} fixture")
    f.write(dumps(level1area_fixtures, ensure_ascii=False, indent=4))

with open(join(FIXTURE_BASE_PATH, f"level2areas.json"), "w") as f:
    print(f"Writing {f.name} fixture")
    f.write(dumps(level2area_fixtures, ensure_ascii=False, indent=4))

with open(join(FIXTURE_BASE_PATH, f"mandatory.json"), "w") as f:
    print(f"Writing {f.name} fixture")
    f.write(dumps(currencies_fixtures + countries_fixtures + level1area_fixtures + level2area_fixtures, ensure_ascii=False, indent=4))


print()
print()
print("| Country | Currencies | Level 1<br/>Administrative<br/>Divisions | Level 2<br/>Administrative<br/>Divisions | Settlements | Settlements 10K+ |")
print("| :-- | --: | --: | --: | --: | --: |")

for country_code, cldr_data in sorted(COUNTRY_CLDR_DATA.items()):
    name = cldr_data["names"]["en"]
    c = COUNTRY_COUNTERS[country_code]["currencies"]
    l1a = COUNTRY_COUNTERS[country_code]["level1areas"]
    l2a = COUNTRY_COUNTERS[country_code]["level2areas"]
    s = COUNTRY_COUNTERS[country_code]["settlements"]
    s10k = COUNTRY_COUNTERS[country_code]["settlements_10k"]
    c = c if c > 0 else "-"
    l1a = l1a if l1a > 0 else "-"
    l2a = l2a if l2a > 0 else "-"
    s = s if s > 0 else "-"
    s10k = s10k if s10k > 0 else "-"

    print(f"| {country_code}, {name} | {c} | {l1a} | {l2a} | {s} | {s10k} |")

c = GLOBAL_COUNTERS["currencies"]
l1a = GLOBAL_COUNTERS["level1areas"]
l2a = GLOBAL_COUNTERS["level2areas"]
s = GLOBAL_COUNTERS["settlements"]
s10k = GLOBAL_COUNTERS["settlements_10k"]
print(f"| Total | {c} | {l1a} | {l2a} | {s} | {s10k} |")
print()
print()
