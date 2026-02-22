"""
Compression utilities.

Backend: ``zlib`` (Python standard library — always available, fast, no extra
install required).

Note on pzip
  The ``pzip`` package is a password-protected file-archive library; it has no
  simple bytes-level compress/decompress API and is therefore unsuitable here.
  ``zlib`` is used instead.

Usage
-----
    from utils.compression import compress_data, decompress_data, COMPRESSION_BACKEND

    compressed   = compress_data(raw_bytes)
    decompressed = decompress_data(compressed)
    print(COMPRESSION_BACKEND)   # "zlib"
"""

import zlib

COMPRESSION_BACKEND: str = "zlib"


def compress_data(data: bytes) -> bytes:
    """Compress *data* with zlib (level 9) and return the compressed bytes."""
    return zlib.compress(data, level=9)


def decompress_data(data: bytes) -> bytes:
    """Decompress zlib-compressed *data* and return raw bytes."""
    return zlib.decompress(data)
