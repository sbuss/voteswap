from django import template
import us

register = template.Library()

# Stateface is a font, and each state corresponds to a letter
STATE_MAP = {
    "AL": "B",
    "AK": "A",
    "AZ": "D",
    "AR": "C",
    "CA": "E",
    "CO": "F",
    "CT": "G",
    "DE": "H",
    "DC": "y",
    "FL": "I",
    "GA": "J",
    "HI": "K",
    "ID": "M",
    "IL": "N",
    "IN": "O",
    "IA": "L",
    "KS": "P",
    "KY": "Q",
    "LA": "R",
    "ME": "U",
    "MD": "T",
    "MA": "S",
    "MI": "V",
    "MN": "W",
    "MS": "Y",
    "MO": "X",
    "MT": "Z",
    "NE": "c",
    "NV": "g",
    "NH": "d",
    "NJ": "e",
    "NM": "f",
    "NY": "h",
    "NC": "a",
    "ND": "b",
    "OH": "i",
    "OK": "j",
    "OR": "k",
    "PA": "l",
    "RI": "m",
    "SC": "n",
    "SD": "o",
    "TN": "p",
    "TX": "q",
    "UT": "r",
    "VT": "t",
    "VA": "s",
    "WA": "u",
    "WV": "w",
    "WI": "v",
    "WY": "x",
    "US": "z",
}


@register.filter
def stateface(state_name):
    return STATE_MAP[us.states.lookup(unicode(state_name)).abbr.upper()]
