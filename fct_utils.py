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

def find_governing_verb(token):
    for ancestor in token.ancestors:
        if ancestor.pos_ in ['VERB', 'AUX']:
            return ancestor
    return None

