import os
import json
import numpy as np
import cv2 as cv

from utils.crypto_utils import generate_key, encrypt_bytes
from utils.io_utils import read_image, write_image, read_file_bytes, ensure_dir


def embed(image_path: str, input_file_path: str, output_dir: str = "images", output_name: str = "output.png") -> None:
    file_details = {
        'name': os.path.basename(input_file_path),
        'size': os.path.getsize(input_file_path)
    }

    image = read_image(image_path)
    if image is None:
        raise ValueError("Image not found")

    file_data = read_file_bytes(input_file_path)

    user_key = generate_key()
    print(f"Your key : {user_key}  ( Save this key for decrypting )")
    encrypted_content = encrypt_bytes(file_data, user_key)

    container = {
        "content": encrypted_content,
        "metadata": file_details
    }
    data = json.dumps(container)

    data_bytes = np.frombuffer(data.encode('utf-8'), dtype=np.uint8)
    binary_data = np.unpackbits(data_bytes)

    image_capacity_bits = image.size
    print(f"Image capacity (bits): {image_capacity_bits}")
    print(f"Data size (bits): {len(binary_data)}")

    if len(binary_data) > image_capacity_bits:
        raise ValueError("Data too large to fit in image")
    else:
        print("Data fits in image")

    flat_image = image.flatten()
    modified_image = flat_image.copy()

    modified_image[:len(binary_data)] = (modified_image[:len(binary_data)] & 0b11111110)
    modified_image[:len(binary_data)] |= binary_data.astype(np.uint8)

    result_image = modified_image.reshape(image.shape)

    ensure_dir(output_dir)
    output_path = os.path.join(output_dir, output_name)
    write_image(output_path, result_image)
    print(f"Data embedded successfully into {output_path}")


