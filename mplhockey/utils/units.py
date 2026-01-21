UNITS = {
    "m": 1.0,
    "ft": 0.3048,
    "cm": 0.01,
    "in": 0.0254,
    "yd": 0.9144,
    "km": 1000.0,
    "mi": 1609.34,
    "mm": 0.001,
    "nm": 1e-9,
    "pm": 1e-12,
    "um": 1e-6,
    "ang": 1e-10,
    "pc": 0.000352778,
    "ly": 9.4607e15,
    "au": 149597870700.0,
    "parsec": 3.085677581491367e16,
    "lightyear": 9.4607e15,
    "angstrom": 1e-10,
    "nautical_mile": 1852.0,
    "furlong": 201.168,
    "chain": 20.1168,
    "rod": 5.0292,
    "link": 0.201168,
    "mil": 0.0000254,
    "point": 0.000352778,
    "barleycorn": 0.00846667,
    "cubit": 0.4572,
    "ell": 1.143,
    "fathom": 1.8288,
    "hand": 0.1016,
    "span": 0.2286,
    "palm": 0.0762,
    "digit": 0.01905,
    "finger": 0.0254,
    "foot": 0.3048,
}


def conversion_factor(from_units, to_units):
    """
    Convert from one unit to another.
    """
    assert from_units in UNITS, f"Unsupported from_units: {from_units}"
    assert to_units in UNITS, f"Unsupported to_units: {to_units}"

    return UNITS[from_units] / UNITS[to_units]
