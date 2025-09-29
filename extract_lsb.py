import json
import numpy as np
import cv2 as cv

from utils.crypto_utils import decrypt_to_bytes
from utils.io_utils import read_image, write_bytes


def _try_parse_container(text: str):
    if not text or '{' not in text:
        return None
    start_idx = text.find('{')
    brace_count = 0
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_text = text[start_idx:i+1]
                try:
                    return json.loads(json_text)
                except json.JSONDecodeError:
                    return None
    return None


def extract_chunked(image_path: str, user_key: str) -> None:
    image = read_image(image_path)
    if image is None:
        raise ValueError("Image not found")

    flat_image = image.flatten()
    lsbs = flat_image & 1

    chunk_size = 8192
    extracted_text = ""

    for i in range(0, len(lsbs), chunk_size * 8):
        chunk_bits = lsbs[i:i + chunk_size * 8]
        remainder = len(chunk_bits) % 8
        if remainder != 0:
            chunk_bits = np.pad(chunk_bits, (0, 8 - remainder), 'constant')

        if len(chunk_bits) == 0:
            continue

        chunk_bits_reshaped = chunk_bits.reshape(-1, 8)
        powers = np.array([128, 64, 32, 16, 8, 4, 2, 1])
        chunk_bytes = np.sum(chunk_bits_reshaped * powers, axis=1)

        try:
            chunk_text = ''.join(chr(b) for b in chunk_bytes if 0 <= b <= 127)
            extracted_text += chunk_text

            container = _try_parse_container(extracted_text.strip())
            if container:
                encrypted = container.get("content", "").encode()
                metadata = container.get("metadata", {})
                file_data = decrypt_to_bytes(encrypted, user_key)
                write_bytes(metadata.get("name", "output.bin"), file_data)
                print("Data extracted successfully")
                print("Metadata:", metadata)
                return
        except (ValueError, UnicodeDecodeError):
            continue

    print("No valid JSON found, data may be corrupted.")


def extract_simple(image_path: str, user_key: str) -> None:
    image = read_image(image_path)
    if image is None:
        raise ValueError("Image not found")

    flat_image = image.flatten()
    lsbs = flat_image & 1

    max_bits = min(len(lsbs), 100000 * 8)
    relevant_bits = lsbs[:max_bits]

    remainder = len(relevant_bits) % 8
    if remainder != 0:
        relevant_bits = np.pad(relevant_bits, (0, 8 - remainder), 'constant')

    bit_chunks = relevant_bits.reshape(-1, 8)
    powers = np.array([128, 64, 32, 16, 8, 4, 2, 1])
    byte_values = np.sum(bit_chunks * powers, axis=1)

    try:
        valid_bytes = byte_values[byte_values < 128]
        text = ''.join(chr(b) for b in valid_bytes)
        container = _try_parse_container(text)
        if container:
            encrypted = container.get("content", "").encode()
            metadata = container.get("metadata", {})
            file_data = decrypt_to_bytes(encrypted, user_key)
            write_bytes(metadata.get("name", "output.bin"), file_data)
            print("Data extracted successfully")
            print("Metadata:", metadata)
            return
    except Exception as e:
        print(f"Error during extraction: {e}")

    print("No valid JSON found, data may be corrupted.")


