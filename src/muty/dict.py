"""dict utility functions.
"""

import json
from typing import Any

import json5

import muty.list


def from_json_file(path: str) -> dict:
    """
    reads json from file, also supports json5

    @param path file path
    @return dict
    """
    with open(path, "r") as f:
        js = json5.loads(f.read())
    return js


def to_json_file(path, js, indent=2) -> None:
    """!
    writes json to file

    @param path path to the file to be created
    @param js dict to be written
    @param indent optional indentantion spaces, default=2
    """

    # write
    with open(path, "w") as f:
        jjs = json.dumps(js, indent=indent)
        f.write(jjs)


def dict_of_list_to_chunks(d: dict[str, list[str]], n_chunks: int) -> list[dict]:
    """takes a dictionay of [str, list[str]] and splits it into as close to n_chunks as possible, returns list of dict[str, list[str]], last chunk might be smaller if d cant be split evenly

    Args:
        d (dict[str,list]): dictionary to split, must be dict[str, list[str]]
        n_chunks (int): number of chunks to split dictionary in

    Returns:
        list[dict]: returns list of dictionaries
    """

    results: list[dict] = []

    for i in range(n_chunks):
        results.append({})

    for k, v in d.items():
        list_chunks = muty.list.split_list_in_n_lists(v, n_chunks)
        for i in range(len(list_chunks)):
            if len(list_chunks[i]) > 0:
                if k not in (results[i % n_chunks]).keys():
                    (results[i % n_chunks])[k] = list_chunks[i]
                else:
                    (results[i % n_chunks])[k].extend(list_chunks[i])

    return list(filter(lambda item: item != {}, results))


def check_exists_and_add_if_valid(
    src_dict: dict,
    k: str,
    default: Any,
    dst_dict: dict,
    force: bool = False,
    alt_k: str = None,
):
    """
    Check if a key exists in a source dictionary and add it to a destination dictionary if it is valid.

    Args:
        src_dict (dict): The source dictionary to check for the key.
        k (str): The key to check for in the source dictionary.
        default (Any): The default value to use if the key is not found in the source dictionary.
        dst_dict (dict): The destination dictionary to add the key and value to if it is valid.
        force (bool, optional): Whether to force adding the key and value to the destination dictionary even if it is not valid. Defaults to False.
        alt_k (str, optional): An alternate key to use for the destination dictionary if the key is valid. Defaults to None.
    """
    if src_dict is None:
        return

    add_to_dict_if_valid(
        src_dict.get(k, default), dst_dict, k if alt_k is None else alt_k, force
    )


def add_to_dict_if_valid(s: Any, d: dict, k: str, force_add: bool = False):
    """
    Add a value to a dictionary if it is valid.

    Args:
        s (Any): The value to add to the dictionary.
        d (dict): The dictionary to add the value to.
        k (str): The key to use for the value in the dictionary.
        force_add (bool, optional): Whether to force adding the value to the dictionary even if it is not valid. Defaults to False.
    """
    if s is None and force_add:
        d[k] = s

    elif isinstance(s, dict) or isinstance(s, list) or isinstance(s, str):
        if isinstance(s, str):
            # avoid whitespaces only
            if len(s.strip()) > 0 or force_add:
                d[k] = s
        else:
            if len(s) > 0 or force_add:
                d[k] = s

    elif isinstance(s, bool):
        if s or force_add:
            d[k] = s
    elif isinstance(s, int) or isinstance(s, float):
        if s > 0 or force_add:
            d[k] = s


def clear_dict(
    d: dict,
    keep_numbers: bool = False,
    keep_bool: bool = False,
    keep_strings: bool = False,
    keep_lists: bool = False,
    keep_dicts: bool = False,
    keep_none: bool = False,
) -> dict:
    """
    Recursively remove all None values from a dictionary.

    Args:
        d (dict): The dictionary to remove None values from.
        keep_numbers (bool, optional): Whether to keep numbers when removing None values. Defaults to False.
        keep_bool (bool, optional): Whether to keep bool values when removing None values. Defaults to False.
        keep_strings (bool, optional): Whether to keep strings when removing None values. Defaults to False.
        keep_lists (bool, optional): Whether to keep lists when removing None values. Defaults to False.
        keep_dicts (bool, optional): Whether to keep dictionaries when removing None values. Defaults to False.
        keep_none (bool, optional): Whether to keep generic None values. Defaults to False.

    Returns:
        dict: The dictionary with all None values removed.
    """
    cleared_dict = {}

    # check if method exists or the recursive loops would fail (e.g. for strings)
    method = getattr(d, "items", None)
    if method is None:
        return d

    for k, v in d.items():
        if v is not None or keep_none:
            if isinstance(v, dict):
                cleared_v = clear_dict(v)
                if cleared_v is not None or keep_dicts:
                    cleared_dict[k] = cleared_v
            elif isinstance(v, list):
                cleared_v = [clear_dict(item) for item in v]
                if keep_lists or (cleared_v is not None and len(cleared_v) > 0):
                    cleared_dict[k] = cleared_v
            elif isinstance(v, str):
                if len(v.strip()) > 0 or keep_strings:
                    cleared_dict[k] = v
            elif isinstance(v, bool):
                if v or keep_bool:
                    cleared_dict[k] = v
            elif isinstance(v, int) or isinstance(v, float):
                if v > 0 or keep_numbers:
                    cleared_dict[k] = v
            else:
                if v is not None or keep_none:
                    cleared_dict[k] = v
    return cleared_dict

def remove_keys(d: dict, keys: list[str]) -> dict:
    """
    Removes the specified keys from the dictionary.

    Args:
        d (dict): The dictionary to remove keys from.
        keys (list[str]): The keys to remove.

    Returns:
        dict: The dictionary with the keys removed.
    """
    return {k: v for k, v in d.items() if k not in keys}

