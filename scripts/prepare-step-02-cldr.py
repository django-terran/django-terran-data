#!/usr/bin/env -S python -u

#
# Download and extract data from Common Locale Data Repository
# Data includes country, level1area, level2area, currency and relations between them.
# Downloaded data is cached. Extracted data is overwritten.
#
# See also: https://en.wikipedia.org/wiki/Common_Locale_Data_Repository
# See also: https://cldr.unicode.org/
#


from _codes import COUNTRY_CODES
from _codes import LOCALE_TAGS
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import date
from json import dumps
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
from xml.dom import Node
from xml.dom.minidom import parseString
from zipfile import ZipFile

parser = ArgumentParser(prog=argv[0], description="Download CLDR (Common Locale Data Repository) data.")
parser.add_argument("--cache-path", help="Path to cache of downloaded files.", default="~/.cache/django-terran/cldr/")
parser.add_argument("--data-path", required=True, help="Path data files.")
parser.add_argument("--accept-license", required=True, action="store_true")
arguments = parser.parse_args()

CLDR_URL = "http://unicode.org/Public/cldr/45/cldr-common-45.0.zip"
CLDR_FILE_NAME = basename(CLDR_URL)
CLDR_CACHE_DIR_PATH = abspath(join(dirname(__file__), expanduser(arguments.cache_path)))
CLDR_CACHE_FILE_PATH = join(CLDR_CACHE_DIR_PATH, CLDR_FILE_NAME)
CLDR_TEMP_FILE_PATH = join(CLDR_CACHE_DIR_PATH, "~temp~")
CLDR_BASE_PATH = abspath(join(dirname(__file__), arguments.data_path, "cldr"))

makedirs(CLDR_CACHE_DIR_PATH, exist_ok=True)
makedirs(join(CLDR_BASE_PATH, "countries"), exist_ok=True)
makedirs(join(CLDR_BASE_PATH, "currencies"), exist_ok=True)


@dataclass
class Currency:
    iso_4217_n3: str
    iso_4217_a3: str
    names: dict[str, str]
    decimal_digits: int


@dataclass
class CountryCurrency:
    currency: str
    since: date
    until: date


@dataclass
class Level2Area:
    iso_3166_a2: str
    names: dict[str, str]


@dataclass
class Level1Area:
    iso_3166_a2: str
    names: dict[str, str]
    level2areas: dict[str, Level2Area]


@dataclass
class Country:
    iso_3166_n3: str
    iso_3166_a2: str
    iso_3166_a3: str
    names: dict[str, str]
    languages: dict[str, float]
    currency: str
    currencies: list[CountryCurrency]
    level1areas: dict[str, Level1Area]


def get_xml_element_from_zip_item(zip_archive: ZipFile, path: str):
    with zip_archive.open(path, "r") as zip_item:
        xml_dom = parseString(zip_item.read())

        return xml_dom.documentElement


def get_xml_element_child(parent: Node, child_tag_name: str):
    for node in parent.childNodes:
        if (node.nodeType == Node.ELEMENT_NODE) and (node.localName == child_tag_name):
            return node

    return None


def get_xml_element_children(parent: Node, child_tag_name: str):
    for node in parent.childNodes:
        if (node.nodeType == Node.ELEMENT_NODE) and (node.localName == child_tag_name):
            yield node


def get_xml_element_text(node: Node):
    if node.nodeType == Node.TEXT_NODE:
        return node.data

    result = ""
    for child in node.childNodes:
        result += get_xml_element_text(child)

    return result


LOCALE_TAG_FALLBACKS: dict[str, list[str]] = {}
COUNTRIES: dict[str, Country] = {}
TERRITORIES: dict[str, object] = {}
CURRENCIES: dict[str, Currency] = {}

for locale_tag in LOCALE_TAGS:
    tags = []

    if "-" in locale_tag:
        parts = locale_tag.split("-", 1)

        if len(parts[1]) == 2:
            tags.append(parts[0])
            tags.append(parts[0] + "-" + parts[1].upper())
        else:
            tags.append(parts[0])
            tags.append(parts[0] + "-" + parts[1].title())
    else:
        tags.append(locale_tag)

    LOCALE_TAG_FALLBACKS[locale_tag] = tags

if not isfile(CLDR_CACHE_FILE_PATH):
    print("Downloading CDLR ZIP archive...", end="")

    with request("GET", CLDR_URL, stream=True) as response:
        content_length = int(response.headers.get("Content-Length", "0"))

        with open(CLDR_TEMP_FILE_PATH, mode="wb") as file:
            read_length = 0

            for chunk in response.iter_content(64 * 1024):
                file.write(chunk)
                read_length += len(chunk)
                read_percent = 100 * read_length // content_length
                print(f"\rDownloading CDLR... {read_percent}%          ", end="")

    rename(CLDR_TEMP_FILE_PATH, CLDR_CACHE_FILE_PATH)

print()
print("Parsing CDLR ZIP archive...")

with ZipFile(CLDR_CACHE_FILE_PATH, "r") as zip_archive:
    namelist = set(zip_archive.namelist())

    with zip_archive.open("LICENSE", "r") as zip_item:
        license = zip_item.read()
        print(f"\033[33m{license.decode("utf-8")}\033[0m")
        print()

    with open(join(CLDR_BASE_PATH, "LICENSE"), "wb") as f:
        f.write(license)

    supplemental_data_xml = get_xml_element_from_zip_item(zip_archive, "common/supplemental/supplementalData.xml")
    code_mappings_node = get_xml_element_child(supplemental_data_xml, "codeMappings")

    # Equivalence of country codes, GE<=>GEO<=>268
    for territory_codes_node in get_xml_element_children(code_mappings_node, "territoryCodes"):
        type_attr = territory_codes_node.getAttribute("type")
        numeric_attr = territory_codes_node.getAttribute("numeric")
        alpha3_attr = territory_codes_node.getAttribute("alpha3")

        if type_attr and numeric_attr and alpha3_attr and (type_attr in COUNTRY_CODES):
            country = Country(numeric_attr, type_attr, alpha3_attr, {}, {}, None, [], {})
            COUNTRIES[type_attr] = country
            TERRITORIES[type_attr] = country

    # Equivalence of currency codes, GEL<=>981
    for currency_codes_node in get_xml_element_children(code_mappings_node, "currencyCodes"):
        type_attr = currency_codes_node.getAttribute("type")
        numeric_attr = currency_codes_node.getAttribute("numeric")

        if type_attr and numeric_attr:
            CURRENCIES[type_attr] = Currency(("00" + numeric_attr)[-3:], type_attr, {}, 2)

    # HACK Incomplete CLDR data in version 45.0
    # HACK Remove after upgrade to the next version
    # https://unicode-org.atlassian.net/browse/CLDR-17957
    CURRENCIES["BYN"] = Currency("933", "BYN", {}, 2)
    CURRENCIES["SLE"] = Currency("925", "SLE", {}, 2)

    currency_data_node = get_xml_element_child(supplemental_data_xml, "currencyData")

    if currency_data_node:
        # How many digits after decimal point are allowed.
        # In other words, how many cents are in a dollar.
        # cashDigits and cashRounding are not reliable
        # For example for GEL cashRounding must be 5, but this information is missing.
        # https://unicode-org.atlassian.net/browse/CLDR-17956
        fractions_node = get_xml_element_child(currency_data_node, "fractions")

        if fractions_node:
            for info_node in get_xml_element_children(fractions_node, "info"):
                iso4217_attr = info_node.getAttribute("iso4217")
                digits_attr = info_node.getAttribute("digits")

                if iso4217_attr and digits_attr and (iso4217_attr in CURRENCIES):
                    code = iso4217_attr
                    decimal_digits = int(digits_attr)
                    CURRENCIES[code].decimal_digits = decimal_digits

        # Relationships between countries and currencies
        # Each country may have one and only one current currency
        # Each country may have many historical currencies
        # Each currency many be used in many countries
        for region_node in get_xml_element_children(currency_data_node, "region"):
            iso3166_attr = region_node.getAttribute("iso3166")

            if iso3166_attr and (iso3166_attr in COUNTRIES):
                country = COUNTRIES[iso3166_attr]

                for currency_node in get_xml_element_children(region_node, "currency"):
                    iso4217_attr = currency_node.getAttribute("iso4217")
                    from_attr = currency_node.getAttribute("from")
                    to_attr = currency_node.getAttribute("to")
                    tender_attr = currency_node.getAttribute("tender")

                    if iso4217_attr and from_attr and (not tender_attr):
                        if to_attr:
                            country.currencies.append(CountryCurrency(iso4217_attr, date.fromisoformat(from_attr), date.fromisoformat(to_attr)))
                        else:
                            country.currency = iso4217_attr
                            country.currencies.append(CountryCurrency(iso4217_attr, date.fromisoformat(from_attr), None))

    territory_info_node = get_xml_element_child(supplemental_data_xml, "territoryInfo")

    if territory_info_node:
        for territory_node in get_xml_element_children(territory_info_node, "territory"):
            type_attr = territory_node.getAttribute("type")
            country = COUNTRIES.get(type_attr)

            if country:
                # Relationship between countries and languages
                # Languages will be sorted by popularity in descending order, i.e. most popular language first
                for language_population_node in get_xml_element_children(territory_node, "languagePopulation"):
                    type_attr = language_population_node.getAttribute("type")
                    official_status_attr = language_population_node.getAttribute("officialStatus")
                    population_percent_attr = language_population_node.getAttribute("populationPercent")

                    if official_status_attr in ["official", "de_facto_official", "official_regional"]:
                        country.languages[type_attr.replace("_", "-").lower()] = float(population_percent_attr)

    subdivisions_xml = get_xml_element_from_zip_item(zip_archive, "common/supplemental/subdivisions.xml")
    subdivision_containment_node = get_xml_element_child(subdivisions_xml, "subdivisionContainment")
    subdivisions = {}

    # Which territory is in which other territory
    # For example, which province is in which country.
    # Note that names of administrative divisions are country specific.
    # Note that hierarchy of administrative divisions is country specific.
    if subdivision_containment_node:
        for subgroup_node in get_xml_element_children(subdivision_containment_node, "subgroup"):
            type_attr = subgroup_node.getAttribute("type")
            contains_attr = subgroup_node.getAttribute("contains")

            if type_attr and contains_attr:
                code = type_attr
                child_codes = contains_attr.split(" ")
                subdivisions[code] = child_codes

    for country_code, level1area_codes in subdivisions.items():
        if country_code in COUNTRIES:
            country = COUNTRIES[country_code]

            for level1area_code in level1area_codes:
                level2area_codes = subdivisions.get(level1area_code, [])
                level2areas = {}

                for level2area_code in level2area_codes:
                    level2area = Level2Area(level2area_code, {})
                    level2areas[level2area_code] = level2area
                    TERRITORIES[level2area_code] = level2area

                level1area = Level1Area(level1area_code, {}, level2areas)
                country.level1areas[level1area_code] = level1area
                TERRITORIES[level1area_code] = level1area

    is_first = True

    for primary_locale_tag, fallback_locale_tags in LOCALE_TAG_FALLBACKS.items():
        print(f"{primary_locale_tag}" if is_first else f", {locale_tag}", end="")
        is_first = False

        for locale_tag in fallback_locale_tags:
            path = f"common/main/{locale_tag.replace('-', '_')}.xml"

            if path in namelist:
                main_xml = get_xml_element_from_zip_item(zip_archive, path)
                locale_display_names_node = get_xml_element_child(main_xml, "localeDisplayNames")

                if locale_display_names_node:
                    # Names of countries
                    territories_node = get_xml_element_child(locale_display_names_node, "territories")

                    if territories_node:
                        for territory_node in get_xml_element_children(territories_node, "territory"):
                            type_attr = territory_node.getAttribute("type")
                            alt_attr = territory_node.getAttribute("alt")

                            if (type_attr in COUNTRIES) and (not alt_attr):
                                COUNTRIES[type_attr].names[primary_locale_tag] = get_xml_element_text(territory_node)

                    # Names of administrative divisions within country
                    subdivisions_node = get_xml_element_child(locale_display_names_node, "subdivisions")

                    if subdivisions_node:
                        for subdivision_node in get_xml_element_children(subdivisions_node, "subdivision"):
                            type_attr = subdivision_node.getAttribute("type")
                            alt_attr = subdivision_node.getAttribute("alt")

                            if (type_attr in TERRITORIES) and (not alt_attr):
                                TERRITORIES[type_attr].names[primary_locale_tag] = get_xml_element_text(subdivision_node)

                numbers_node = get_xml_element_child(main_xml, "numbers")

                if numbers_node:
                    currencies_node = get_xml_element_child(numbers_node, "currencies")

                    if currencies_node:
                        for currency_node in get_xml_element_children(currencies_node, "currency"):
                            type_attr = currency_node.getAttribute("type")

                            if type_attr in CURRENCIES:
                                currency = CURRENCIES[type_attr]

                                for display_name_node in get_xml_element_children(currency_node, "displayName"):
                                    count_attr = display_name_node.getAttribute("count")

                                    if not count_attr:
                                        currency.names[primary_locale_tag] = get_xml_element_text(display_name_node)

            path = f"common/subdivisions/{locale_tag.replace('-', '_')}.xml"

            if path in namelist:
                subdivisions_xml = get_xml_element_from_zip_item(zip_archive, path)
                locale_display_names_node = get_xml_element_child(subdivisions_xml, "localeDisplayNames")

                if locale_display_names_node:
                    # Names of administrative divisions within country
                    subdivisions_node = get_xml_element_child(locale_display_names_node, "subdivisions")

                    if subdivisions_node:
                        for subdivision_node in get_xml_element_children(subdivisions_node, "subdivision"):
                            type_attr = subdivision_node.getAttribute("type")
                            alt_attr = subdivision_node.getAttribute("alt")

                            if (type_attr in TERRITORIES) and (not alt_attr):
                                TERRITORIES[type_attr].names[primary_locale_tag] = get_xml_element_text(subdivision_node)

print()
print("Updating CLDR data...")

for currency_code, currency in sorted(CURRENCIES.items()):
    path = join(CLDR_BASE_PATH, f"currencies/{currency_code}.json")
    data = {
        "iso_4217_n3": currency.iso_4217_n3,
        "iso_4217_a3": currency.iso_4217_a3,
        "names": dict(sorted(currency.names.items())),
        "decimal_digits": currency.decimal_digits,
    }

    with open(path, "w") as f:
        f.write(dumps(data, ensure_ascii=False, indent=4))

is_first = True

for country_code, country in sorted(COUNTRIES.items()):
    print(f"{country_code}" if is_first else f", {country_code}", end="")
    is_first = False
    path = join(CLDR_BASE_PATH, f"countries/{country_code}.json")
    data = {
        "iso_3166_n3": country.iso_3166_n3,
        "iso_3166_a2": country.iso_3166_a2,
        "iso_3166_a3": country.iso_3166_a3,
        "names": dict(sorted(country.names.items())),
        "currency": country.currency,
        "currencies": [],
        "languages": list(l[0] for l in sorted(country.languages.items(), key=lambda l: -l[1])),
        "level1areas": [],
    }

    for country_currency in sorted(country.currencies, key=lambda c: c.since):
        data["currencies"].append(
            {
                "iso_4217_a3": country_currency.currency,
                "since": country_currency.since.isoformat(),
                "until": country_currency.until.isoformat() if country_currency.until else None,
            }
        )

    for level1area in sorted(country.level1areas.values(), key=lambda p: p.iso_3166_a2):
        level1area_data = {"iso_3166_a2": level1area.iso_3166_a2, "names": dict(sorted(level1area.names.items())), "level2areas": []}

        for level2area in sorted(level1area.level2areas.values(), key=lambda m: m.iso_3166_a2):
            level1area_data["level2areas"].append(
                {
                    "iso_3166_a2": level2area.iso_3166_a2,
                    "names": dict(sorted(level2area.names.items())),
                }
            )

        data["level1areas"].append(level1area_data)

    with open(path, "w") as f:
        f.write(dumps(data, ensure_ascii=False, indent=4))

print()
