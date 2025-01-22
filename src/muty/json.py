"""
helper functions for working with json
"""

def flatten_json(d: dict, prefix="", separator=".", encoding="utf8", normalize=None, expand_lists=True) -> dict:
    """Flatten out a dict. If expand_lists is True, it also flattens lists. This is a recursive function.

    Args:
        d (dict): dictionary to flatten
        prefix (str, optional): prefix to use. Defaults to "".
        separator (str, optional): separator to use when naming flattened fields. Defaults to ".".
        normalize (func, optional): function to normalize the prefix, takes a string returns a string. Defaults to None.
        encoding (str, optional): encode any bytes value using the specified encoding, if `None` encodes as hexstring. Defaults to "utf8".
        expand_lists (bool, optional): expand lists. Defaults to True.

    Returns:
        dict: flattened dict
    """
    out = {}

    def encode_or_hexstring(s):
        # json does not support bytes hence we must make sure we always handling strings
        if encoding and isinstance(s, bytes):
            try:
                return s.decode(encoding)
            except Exception as e:
                return s.hex()
        else:
            return s

    def flatten(dd, prefix=prefix):
        if normalize:
            prefix = normalize(prefix)
        
        if isinstance(dd, dict):            
            for a in dd:                    
                flatten(dd[a], str(prefix) + encode_or_hexstring(a) + separator)
        elif isinstance(dd, list) and expand_lists:
            i = 0
            for a in dd:
                flatten(a, str(prefix) + str(i) + separator)
                i += 1
        else:
            out[prefix[:-1]] = encode_or_hexstring(dd)

    flatten(d)
    return out
