# Django Terran Data Manipulation Scripts

This repository contains Python scripts and JSON data files used to generate fixtures for the `django-terran` application. The fixtures include data for:

- Currencies;
- Countries;
- Administrative divisions of countries;
- Settlements;
- and relationships between them all.

In praticular answers to the following questions are provided:
- About languages
    - What are the [defacto] official languages of a country X?
- About currencies
    - What are ISO 4217 codes of a currency X?
    - What is the name of a currency X in locale Y?
    - What countries use a currency X as a legal tender?
    - What is the current currency of a country X?
    - What are historic currencies in a country X which are not in curculation anymore?
- About countries
    - What are ISO 3166 codes of a country X?
    - What is the name of a country X in locale Y?
    - What are administrative divisions of a country X? What is their hierarchy?
    - What are names of administrative divisions of a country X?
    - What settlements are in an administrative division?
    - What does a post address look like a country X?
        - Does is have a post code? What is the format? What do they call a post code?
        - Does is have an administrative division?
        - What is the order of fields in the address?
    - Is there a government registry of organizations in a country X?
        - What does an organization ID look like?
    - Is there a government registry of people in a country X?
        - What does a person ID look like?
    - What the calling code a country X?
        - What do phone numbers look line in a country X?
    - Does the country support IBAN?

## What is Django Terran?

See https://github.com/django-terran/django-terran

## Examples

1. Belarus

    Address has one level of administartive divisions which are called Region.

    Belarus has post codes which must look like "{6 digits}".

    Address is written as:
    ```
    Belarus
    Region
    PostCode Settlement
    District, road, house number
    ```
    Belarus has IBAN which must look like "BY{2 digits}{2 symbols}{4 digits}{16 symbols}".

    Calling code of Belarus is +375.

    There is a government registry of organizations in Belarus.
    Organization ID is called "VAT identification number" and must look like "{9 digits}".

1. France

    Address has one or two levels of administartive divisions which are called Region and Department.

    France has post codes which must look like "{5 digits}".

    Address is written as:
    ```
    House number, road
    PostCode, Settlement
    Region, Department
    France
    ````
    France has IBAN which must look like "FR{12 digits}{11 symbols}{2 digits}".

    Calling code of France is +33.

    There is a government registry of organizations in France.
    Organization ID is called "VAT identification number" and must look like "FR{2 symbols}{9 digits}".

1. Georgia

    Address has one level of administartive divisions which are called Mkhare.

    Georgia has post codes which must look like "{4 digits}".

    Post codes are called post indexes.
    Address is written as:
    ```
    House number, road
    PostCode Settlement
    Mkhare
    Georgia
    ```
    Georgia has IBAN which must look like "GE{2 digits}{2 letters}{16 digits}".

    Calling code of Georgia is +995.

    There is a government registry of organizations in Georgia.
    Organization ID is called "Identificaion Code" and must look like "{9 digits}".

    There is a government registry of people in Georgia.
    Person ID is called "Personal Number" and must look like "{11 digits}".

1. United Arab Emirates

    Address has one level of administartive divisions which are called Emirate.

    UAE has no post codes.

    Address is written as:
    ```
    House number, road, district
    Settlement
    Emirate
    United Arab Emirates
    ```
    UAE has no IBAN.

    Calling code of UAE is +971.

1. United Stated of America

    Address has one level of administartive divisions which are called State.

    USA has post codes which must look like "{5 digits}" optionally followed by a dash and additional digits.
    Post codes are called ZIP codes.

    Address is written as:
    ```
    House number, road,
    Apartment or unit,
    Settlement, State abbreviation, ZIP code
    United States of America
    ```
    Calling code of USA is +1

    There is a government registry of organizations in USA.
    Organization ID is called "Employer Identification Number" and must look like "{9 digits}".

    There is a government registry of people in USA, but we pretend there is not, since SSN is very confidential.
    If your web-site collects SSN, you may configure that in data/user/countries/US.json file and regenerate fixtures.

## How can I help?

### Fix user data, that's where I really need some help

1. Go to data/user/countries/{YOUR-COUNTRY-CODE}.json
1. Look at data/user/countries/GE.json and data/user/countries/US.json for inspuration.
1. Make sure data is correct. I believe citizens/residents should know better what their country does or does not do. I respect Wikipedia very much, but information may be incomplete and/or outdated.
1. Fork repository and fix errors.
1. Run verification script to make sure nothing is broken. That will validate JSON schema and address_output_format.
    ```bash
    cd ./scripts/
    ./verify-step-01-user.py --data-path ../data/
    ```
1. Open a pull request.
1. https://www.youtube.com/watch?v=LuseG4MoZyY

### JSON schema is not enough to understand data/user/countries/{XX}.json format

Yeah, fair enough.

- `address.input_layout`

    An array which defined the order is which address fields should be placed.

    Note that fields are dependent, so level2area should go after level1area. The following fields are allowed:
     - level1area
     - level2area
     - postcode
     - settlement
     - street
- `address.output_format`

    A string, Django/Jinja2 template which formats address from parts.
    Use a syntax subset supported by both Django and Jinja2.

    The following context variables are expected:
    - has_country
    - has_level1area
    - has_level2area
    - has_postcode
    - has_recipient
    - has_settlement
    - has_street
    - country_name
    - level1area_code (ISO 3166 A2 uppercase, only USA uses that)
    - level1area_name
    - level2area_code (ISO 3166 A2 uppercase, no country uses that)
    - level2area_name
    - postcode_text
    - recipient_text
    - settlement_text
    - street_text
- `address.level1area_names`

    A dictionary with names of level 1 administrative unit; or null if country has no level 1 administrative unit.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Examples of valid English names are "Province", "Region".
- `address.level2area_names`

    A dictionary with names of level 2 administrative unit; or null if country has no level 2 administrative unit.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Examples of valid English names are "Territory", "Governorate".
- `address.settlement_names`

    A dictionary with names of settlement.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Examples of valid English names are "City or Village", "Settlement".
- `address.postcode_names`

    A dictionary with names of post code; or null if country has no post code.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Examples of valid English names are "Post code", "Post index", "ZIP code".
- `address.postcode_input_pattern`

    A regular expression for a valid post code; or null if country has no post code.

    Use syntax subset supported by both Python, JavaScript and HTML.
- `address.postcode_input_example`

    An example of a valid post code; or null if country has no post code.
- `address.street_names`

    A dictionary with names of street.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. If street part should be split in lines (like in USA), exach value is not a string, but an array of strings.
- `phone.names`

    A dictionary with names of phone number.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Examples of valid English names are "Phone number", "Telephone number".
- `phone.prefixes`

    An array of calling codes. A country may have multiple calling codes.

    Values are digit only strings.
- `phone.input_pattern`

    A regular expression for a valid phone number.

    Use syntax subset supported by both Python, JavaScript and HTML.
- `phone.input_example`

    An example of a valid phone number.
- `phone.output_format`

    A dictionary of regular expression patterns and replacement describing grouping up digits of a phone number.

    Patterns are tried in the order they are defined.

    Use Python syntax \\{n} for backreferences.

    Python syntax for backreferences can be converted into JavaScript syntax with a simple str.replace("\\", "$").
- `organization_id.names`

    A dictionary with names of an organization ID; or null if country has no organization ID.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Examples of valid English names are "Value Added Tax ID", "Registration number".
- `organization_id.abbreviations`

    A dictionary with abbreviations of an organization ID; or null if country has no organization ID.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are abbreviation. Examples of valid English names are "VAT ID", "R/N".
- `organization_id.input_pattern`

    A regular expression for a valid organization ID; or null if country has no organization ID.

    Use syntax subset supported by both Python, JavaScript and HTML.
- `organization_id.input_example`

    An example of a valid organization ID; or null if country has no organization ID.
- `organization_id.output_format`

    A dictionary of regular expression patterns and replacement describing grouping up symbols of an organization ID.

    Patterns are tried in the order they are defined.

    Use Python syntax \\{n} for backreferences.
    Python syntax for backreferences can be converted into JavaScript syntax with a simple str.replace("\\", "$").
- `person_id.names`

    A dictionary with names of an person ID; or null if country has no person ID.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Examples of valid English names are "Person ID", "Personal number".
- `person_id.abbreviations`

    A dictionary with abbreviations of an person ID; or null if country has no person ID.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are abbreviation. Examples of valid English names are "PID", "P/N".
- `person_id.input_pattern`

    A regular expression for a valid person ID; or null if country has no person ID.

    Use syntax subset supported by both Python, JavaScript and HTML.
- `person_id.input_example`

    An example of a valid person ID; or null if country has no person ID.
- `person_id.output_format`

    A dictionary of regular expression patterns and replacement; or null if country has no person ID.

    Patterns are tried in the order they are defined.

    Use Python syntax \\{n} for backreferences.
    Python syntax for backreferences can be converted into JavaScript syntax with a simple str.replace("\\", "$").
- `iban.names`

    A dictionary with names of an IBAN; or null if country has no IBAN.

    Keys are locale codes supported by Django, see `django.conf.global_settings.LANGUAGES`.

    Values are names. Example of valid English name is "IBAN".
- `iban.input_pattern`

    A regular expression for a valid IBAN; or null if country has no IBAN.

    Use syntax subset supported by both Python, JavaScript and HTML.
- `iban.input_example`

    An example of a valid IBAN; or null if country has no IBAN.
- `iban.output_format`

    A dictionary of regular expression patterns and replacement; or null if country has no IBAN.

    Patterns are tried in the order they are defined.

    Use Python syntax \\{n} for backreferences.
    Python syntax for backreferences can be converted into JavaScript syntax with a simple str.replace("\\", "$").

### What if there is an error in Common Locale Data Repository data?

I am happy to add a workaround fix here, but if and only if you have filed a ticket for CLDR first https://unicode-org.atlassian.net/

This project is not a fork of CLDR, CLDR is an upstream and all CLDR errors should be fixed in CLDR.

### What if there is an error in OpenStreetMaps data?

Edit data in OpenStreetMaps, I am happy to rebuild fixtures after that.

There are a few types of issues:
- Settlement is not present.
    Add it. It's not easy probably, a lof of fields must be populated.
- Settlement is present, but population has invalid format.
    See https://wiki.openstreetmap.org/wiki/Key:population for documentation. Population should be a number, but many settlements have human friendly text instead, like "about 1000 people" instead of just "1000".

    prepare-step-03-osm.py tries it's best to parse these sentences, but sometimes it's not easy.
    In that case prepare-step-03-osm.py will write a warning like below
    ```
    WARNING: Invalid population format; format='Modale 2'; element=node/5007910631
    ```
- Settlement is present, but is not logically related to an administrative division. In that case prepare-step-03-osm.py will write a warning like below
    ```
    WARNING: No OSM data for np1, Central, Nepal
    ```

    I'm pretty sure in many cases it can be autofixed by overlapping administrative division area and settlement point.
    I'm not an OSM guru to do that myself in a reasonable way. I do not feel comfortable issuing one request per settlement to OSM servers.

## Rebuilding Fixtures

STOP! Why? Maybe just use the prebuilt fixures?

### Prerequisites

Ensure you have the following installed:

- Python 3.12
- Django 5.x
- `jsonschema` library
- `requests` library
- A virtual environment (preferred)

Ensure your machine meets the following minimum hardware requirements:

- 12 GB RAM
- 5 GB free disk space for data
- 3 GB free disk space for cache

### Build Process

The scripts cache of downloaded files is under `~/.cache/django-terran/`.
Keeping this cache around is important for execution speed.
Please avoid deleting the cache unless absolutely necessary, as it will cause an unreasonable load on OpenStreetMap servers.
The first time the scripts run, it may take several **hours** depending on your CPU and Internet connection speed.

Run the scripts to generate the fixtures:

1. Verify user provided data. Usually takes under a minute.
    ```bash
    cd ./scripts/
    ./verify-step-01-user.py   --data-path ../data/
    ```
1. Download and extract SVG flags. Usually takes under a minute for the first time.
    ```bash
    cd ./scripts/
    ./prepare-step-01.py --static-path {path-to-django-terran}/src/static/terran/flags/ --accept-license
    ```
1. Download and extract Common Locale Data Repository data. Usually takes several minutes for the first time.
    ```bash
    cd ./scripts/
    ./prepare-step-02.py --data-path ../data/ --accept-license
    ```
1. Query OpenStreetMaps data via Overpass API. Usually takes several **hours** for the first time.
    ```bash
    cd ./scripts/
    ./prepare-step-03.py --data-path ../data/ --accept-license
    ```
1. Generate fixtures. Usually takes under an **hour**.
    ```bash
    cd ./scripts/
    ./generate-fixtures.py --data-path ../data/ -fixture-path {path-to-django-terran-fixtures}
    ```

## Licenses

Files under "data/cldr" are licensed under UNICODE LICENSE V3, see LICENSE-cldr

Files under "data/osm" are licensed under Open Data Commons Open Database License (ODbL) v1.0, see "https://opendatacommons.org/licenses/odbl/1-0/"

Files under "data/user" and everythng else are licensed under Creative Commons Attribution-ShareAlike 4.0 International, see "https://creativecommons.org/licenses/by-sa/4.0/"

## Acknowledgments

Thanks to (in alphabetical order):
- https://github.com/lipis/
- The OpenStreetMap Foundation
- The Unicode Consortium
- The Wikimedia Foundation
