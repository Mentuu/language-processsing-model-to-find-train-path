import unicodedata

def normalize_str(s):
    """
    Normalize a string to remove accents and convert to uppercase.
    """
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    return s.upper()
