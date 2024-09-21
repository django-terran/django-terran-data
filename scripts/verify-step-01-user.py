#!/usr/bin/env -S python -u

#
# Verify user data.
#

from argparse import ArgumentParser
from collections import defaultdict
from jinja2 import Template
from json import loads
from jsonschema import validate
from os import scandir
from os.path import abspath
from os.path import dirname
from os.path import join
from sys import argv

parser = ArgumentParser(prog=argv[0], description="Validate user data.")
parser.add_argument("--data-path", required=True, help="Path data files.")
arguments = parser.parse_args()

USER_BASE_PATH = abspath(join(dirname(__file__), arguments.data_path, "user"))

with open(join(USER_BASE_PATH, "country-schema.json"), "r") as f:
    schema = loads(f.read())

UNIQUE_ADDRESS_OUTPUT_FORMATS = defaultdict(list)

with scandir(join(USER_BASE_PATH, "countries")) as dir_iterator:
    for dir_entry in dir_iterator:
        if dir_entry.is_file() and dir_entry.name.endswith(".json"):
            print(dir_entry.path)

            with open(dir_entry.path, "r") as f:
                data = loads(f.read())
                validate(data, schema)

                UNIQUE_ADDRESS_OUTPUT_FORMATS[data["address"]["output_format"]].append(dir_entry.path)


for address_output_format, paths in UNIQUE_ADDRESS_OUTPUT_FORMATS.items():
    country_options = [False, True] if ("{{ country_name }}" in address_output_format) else [False]
    level1area_options = [False, True] if (("{{ level1area_name }}" in address_output_format) or ("{{ level1area_code }}" in address_output_format)) else [False]
    level2area_options = [False, True] if (("{{ level2area_name }}" in address_output_format) or ("{{ level2area_code }}" in address_output_format)) else [False]
    postcode_options = [False, True] if ("{{ postcode_text }}" in address_output_format) else [False]
    settlement_options = [False, True] if ("{{ settlement_text }}" in address_output_format) else [False]
    street_options = [False, True] if ("{{ street_text }}" in address_output_format) else [False]
    recipient_options = [False, True] if ("{{ recipient_text }}" in address_output_format) else [False]

    for has_country in country_options:
        for has_level1area in level1area_options:
            for has_level2area in level2area_options:
                for has_postcode in postcode_options:
                    for has_settlement in settlement_options:
                        for has_street in street_options:
                            for has_recipient in recipient_options:
                                template = Template(address_output_format)
                                result = template.render(
                                    has_country=has_country,
                                    country_name="$country_name$",
                                    has_level1area=has_level1area,
                                    level1area_name="$level1area_name$",
                                    level1area_code="$level1area_code$",
                                    has_level2area=has_level2area,
                                    level2area_name="$level2area_name$",
                                    level2area_code="$level2area_code$",
                                    has_postcode=has_postcode,
                                    postcode_text="$postcode_text$",
                                    has_settlement=has_settlement,
                                    settlement_text="$settlement_text$",
                                    has_street=has_street,
                                    street_text="$street_text$",
                                    has_recipient=has_recipient,
                                    recipient_text="$recipient_text$",
                                )

                                if (
                                    (has_country and ("$country_name$" not in result)) or
                                    ((not has_country) and ("$country_name$" in result)) or

                                    (has_level1area and ("$level1area_name$" not in result) and ("$level1area_code$" not in result)) or
                                    ((not has_level1area) and (("$level1area_name$" in result) or ("$level1area_code$" in result))) or

                                    (has_level2area and ("$level2area_name$" not in result) and ("$level2area_code$" not in result)) or
                                    ((not has_level2area) and (("$level2area_name$" in result) or ("$level2area_code$" in result))) or

                                    (has_postcode and ("$postcode_text$" not in result)) or
                                    ((not has_postcode) and ("$postcode_text$" in result)) or

                                    (has_settlement and ("$settlement_text$" not in result)) or
                                    ((not has_settlement) and ("$settlement_text$" in result)) or

                                    (has_street and ("$street_text$" not in result)) or
                                    ((not has_street) and ("$street_text$" in result)) or

                                    (has_recipient and ("$recipient_text$" not in result)) or
                                    ((not has_recipient) and ("$recipient_text$" in result))
                                ):
                                    print("INVALID FORMAT")
                                    print(address_output_format.replace("\n", "\\n"))
                                    print("USED IN")
                                    print("\n".join(paths))
