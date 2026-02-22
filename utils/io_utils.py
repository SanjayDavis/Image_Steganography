"""
File and image I/O helpers.
"""

import os
import cv2 as cv


def ensure_dir(path: str) -> None:
    """Create *path* (and any intermediate directories) if it does not exist."""
    os.makedirs(path, exist_ok=True)


def read_image(path: str):
    """
    Read an image with OpenCV.

    Returns:
        BGR NumPy array or ``None`` if the file cannot be opened.
    """
    return cv.imread(path)


def write_image(path: str, image) -> None:
    """Write a BGR NumPy array to *path*."""
    cv.imwrite(path, image)


def read_file_bytes(path: str) -> bytes:
    """Return the full binary contents of *path*."""
    with open(path, "rb") as fh:
        return fh.read()


def write_bytes(path: str, data: bytes) -> None:
    """Write *data* as raw bytes to *path*."""
    with open(path, "wb") as fh:
        fh.write(data)
