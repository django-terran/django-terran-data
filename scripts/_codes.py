# Django must be installed, as there is not other way to know
from django.conf.global_settings import LANGUAGES

# ISO 3166 A2 codes of supported countries
COUNTRY_CODES = sorted(
    """AD AE AF AG AL AM AO AR AT AU AZ
BA BB BD BE BF BG BH BI BJ BN BO BR BS BT BW BY BZ
CA CD CF CG CH CI CL CM CN CO CR CU CV CY CZ
DE DJ DK DM DO DZ
EC EE EG ER ES ET
FI FJ FK FM FO FR
GA GB GD GE GI GH GL GM GN GQ GR GT GW GY
HN HR HT HU
ID IE IL IN IQ IR IS IT
JM JO JP
KE KG KH KI KM KN KP KR KW KZ
LA LB LC LI LK LR LS LT LU LV LY
MA MC MD ME MG MH MK ML MM MN MR MT MU MV MW MX MY MZ
NA NE NG NI NL NO NP NR NZ
OM
PA PE PG PH PK PL PS PT PW PY
QA
RO RS RU RW
SA SB SC SD SE SG SI SK SL SM SN SO SR SS ST SV SY SZ
TD TG TH TJ TL TM TN TO TR TT TV TW TZ
UA UG US UY UZ
VA VG VC VE VN VU
WS
XK
YE
ZA ZM ZW""".split()
)

# IETF BCP 47 tags of supported locales
LOCALE_TAGS = sorted(language[0] for language in LANGUAGES)