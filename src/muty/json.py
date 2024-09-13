def flatten_json(d: dict, prefix="", separator=".", expand_lists=True) -> dict:
    """Flatten out a dict. If expand_lists is True, it also flattens lists. This is a recursive function.

    Args:
        d (dict): dictionary to flatten
        prefix (str, optional): prefix to use
        separator (str, optional): separator to use when naming flattened fields. Defaults to ".".
        expand_lists (bool, optional): expand lists. Defaults to True.

    Returns:
        dict: flattened dict
    """
    out = {}

    def flatten(dd, prefix=prefix):
        if isinstance(dd, dict):
            for a in dd:
                flatten(dd[a], prefix + a + separator)
        elif isinstance(dd, list) and expand_lists:
            i = 0
            for a in dd:
                flatten(a, prefix + str(i) + separator)
                i += 1
        else:
            out[prefix[:-1]] = dd

    flatten(d)
    return out
