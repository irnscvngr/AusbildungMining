"""
Function to take a dictionary with Umlauts in keys
and return "the same" dictionary but without Umlauts
(only affects keys, not values!)
"""
change_map = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
}

def replace_umlauts(text):
    """
    Take umlaut-map and replace umlauts in strings
    with non-umlauts.
    """
    for umlaut, replacement in change_map.items():
        text = text.replace(umlaut, replacement)
    return text

def clean_dict_keys(original_dict):
    """
    Actual function to return a dictionary without umlauts in keys.
    """
    new_dict = {}
    for key, value in original_dict.items():
        if isinstance(key, str):  # Check if the key is a string
            new_key = replace_umlauts(key)
        else:
            new_key = key  # If the key is not a string, keep it as is
        new_dict[new_key] = value
    return new_dict
