import os
import cv2 as cv


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_image(path: str):
    return cv.imread(path)


def write_image(path: str, image) -> None:
    cv.imwrite(path, image)


def read_file_bytes(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


def write_bytes(path: str, data: bytes) -> None:
    with open(path, 'wb') as f:
        f.write(data)


