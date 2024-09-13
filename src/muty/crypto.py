"""crypto utilities""" ""

import struct
from Crypto.Hash import SHA256, MD5, SHA1, BLAKE2b
import aiofiles


def hash_as_unique_int(buffer: str | bytes) -> int:
    """
    Hashes the given buffer using SHA256 and returns the hash as a unique integer (get first 8 bytes).

    Args:
        buffer (str | bytes): The buffer to be hashed.

    Returns:
        int: The hash value as a unique integer.
    """
    d = hash_sha256(buffer, return_bytes=True)
    s = struct.unpack("q", d[:8])
    return s


def hash_md5(buffer: str | bytes, return_bytes: bool = False) -> str | bytes:
    """
    Hashes the input buffer using the MD5 algorithm and returns the resulting digest as a hex string.

    Args:
        buffer (str or bytes): The input buffer to hash.
        return_bytes (bool, optional): Whether to return the digest as bytes. Defaults to False.

    Returns:
        The resulting digest as a hex string or bytes.
    """
    digest = MD5.new()
    if isinstance(buffer, str):
        bb = buffer.encode()
    else:
        bb = buffer
    digest.update(bb)
    if return_bytes:
        return digest.digest()

    return digest.hexdigest()


def hash_sha1(buffer: str | bytes, return_bytes: bool = False) -> str | bytes:
    """
    Hashes the input buffer using the SHA1 algorithm and returns the resulting digest as a hex string.

    Args:
        buffer (str or bytes): The input buffer to hash.
        return_bytes (bool, optional): Whether to return the digest as bytes. Defaults to False.

    Returns:
        The resulting digest as a hex string or bytes.
    """
    digest = SHA1.new()
    if isinstance(buffer, str):
        bb = buffer.encode()
    else:
        bb = buffer
    digest.update(bb)
    if return_bytes:
        return digest.digest()
    return digest.hexdigest()


def hash_blake2b(buffer: str | bytes, return_bytes: bool = False) -> str | bytes:
    """
    Hashes the input buffer using the BLAKE2b algorithm and returns the resulting digest as a hex string.

    Args:
        buffer (str or bytes): The input buffer to hash.
        return_bytes (bool, optional): Whether to return the digest as bytes. Defaults to False.

    Returns:
        The resulting digest as a hex string or bytes.
    """
    digest = BLAKE2b.new()
    if isinstance(buffer, str):
        bb = buffer.encode()
    else:
        bb = buffer
    digest.update(bb)
    if return_bytes:
        return digest.digest()

    return digest.hexdigest()


def hash_sha256(buffer: str | bytes, return_bytes: bool = False) -> str | bytes:
    """
    Hashes the input buffer using the SHA256 algorithm and returns the resulting digest as a hex string.

    Args:
        buffer (str or bytes): The input buffer to hash.
        return_bytes (bool, optional): Whether to return the digest as bytes. Defaults to False.
    Returns:
        str: The resulting digest as a hex string or bytes.
    """
    digest = SHA256.new()
    if isinstance(buffer, str):
        bb = buffer.encode()
    else:
        bb = buffer
    digest.update(bb)
    if return_bytes:
        return digest.digest()
    return digest.hexdigest()


async def hash_sha256_file(
    path: str, chunk_size: int = 1024 * 1000, return_bytes: bool = False
) -> str | bytes:
    """
    Calculate the SHA256 hash of a file.

    Args:
        path (str): The path to the file.
        chunk_size (int, optional): The size of each chunk to read from the file. Defaults to 1024*1000.
        return_bytes (bool, optional): Whether to return the digest as bytes. Defaults to False.

    Returns:
        str: The resulting digest as a hex string or bytes.
    """
    digest = SHA256.new()
    async with aiofiles.open(path, "rb") as f:
        while True:
            buf = await f.read(chunk_size)
            digest.update(buf)
            if len(buf) < chunk_size:
                break

    if return_bytes:
        return digest.digest()
    return digest.hexdigest()


async def hash_blake2b_file(
    path: str, chunk_size: int = 1024 * 1000, return_bytes: bool = False
) -> str | bytes:
    """
    Calculate the BLAKE2b hash of a file.

    Args:
        path (str): The path to the file.
        chunk_size (int, optional): The size of each chunk to read from the file. Defaults to 1024*1000.

    Returns:
        str: The resulting digest as a hex string or bytes.
    """
    digest = BLAKE2b.new()
    async with aiofiles.open(path, "rb") as f:
        while True:
            buf = await f.read(chunk_size)
            digest.update(buf)
            if len(buf) < chunk_size:
                break

    if return_bytes:
        return digest.digest()

    return digest.hexdigest()

def hash_crc24(value:str | bytes, encoder:str="utf-8"):
    """
    Calculates the CRC-24 hash of the given value.
    Args:
        value (str | bytes): The value to calculate the hash for. If it's a string, it will be encoded using the specified encoder.
        encoder (str, optional): The encoding to use if the value is a string. Defaults to "utf-8".
    Returns:
        int: The CRC-24 hash of the value.
    """
    if isinstance(value, str):
        value = value.encode(encoder)

    INIT = 0xB704CE
    POLY = 0x1864CFB
    crc = INIT
    for octet in value:
        crc ^= (octet << 16)
        for i in range(0,8):
            crc <<= 1
            if crc & 0x1000000: crc ^= POLY
    return crc & 0xFFFFFF