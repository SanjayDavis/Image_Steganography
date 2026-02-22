"""
LSB (Least Significant Bit) Steganography – Embedding
======================================================
Workflow
--------
1. Read cover image.
2. Read payload file, **compress** it, then **encrypt** the compressed bytes.
3. Bundle encrypted content + original file metadata into a JSON container.
4. Pack the JSON as bits and overwrite the LSBs of every pixel channel.
5. Save the stego image.

Returns
-------
``lsb_embed`` returns the generated encryption key so the GUI can display it.
"""

import os
import json
import numpy as np

from utils.crypto_utils import generate_key, encrypt_bytes
from utils.io_utils import ensure_dir, read_image, write_image, read_file_bytes
from utils.compression import compress_data, COMPRESSION_BACKEND


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lsb_embed(
    image_path: str,
    input_file_path: str,
    output_dir: str = "images",
    output_name: str = "output.png",
) -> str:
    """
    Embed a file into a cover image using LSB steganography.

    Pipeline: raw bytes → compress → encrypt → JSON → LSB-embed → PNG.

    Args:
        image_path:      Path to the cover (carrier) image.
        input_file_path: Path to the secret file to hide.
        output_dir:      Directory where the stego image is saved.
        output_name:     Filename for the stego image (should be ``.png``).

    Returns:
        The Fernet encryption key string.  **Store this — you need it to
        extract the file later.**

    Raises:
        ValueError: If the image cannot be opened or the payload is too large.
    """
    # ---- load resources ------------------------------------------------
    image = read_image(image_path)
    if image is None:
        raise ValueError(f"Cannot open image: {image_path}")

    raw_data = read_file_bytes(input_file_path)

    # ---- compress → encrypt -------------------------------------------
    compressed = compress_data(raw_data)
    user_key = generate_key()
    encrypted_content = encrypt_bytes(compressed, user_key)

    # ---- build JSON container -----------------------------------------
    file_details = {
        "name": os.path.basename(input_file_path),
        "original_size": len(raw_data),
        "compressed_size": len(compressed),
        "compression": COMPRESSION_BACKEND,
    }
    container = {"content": encrypted_content, "metadata": file_details}
    json_bytes = json.dumps(container).encode("utf-8")

    # ---- pack into bits -----------------------------------------------
    data_bytes = np.frombuffer(json_bytes, dtype=np.uint8)
    binary_data = np.unpackbits(data_bytes)

    if len(binary_data) > image.size:
        raise ValueError(
            f"Payload too large: needs {len(binary_data)} bits but image "
            f"only has {image.size} bits capacity."
        )

    # ---- embed into image ---------------------------------------------
    flat = image.flatten().copy()
    n = len(binary_data)
    flat[:n] = (flat[:n] & 0b11111110) | binary_data.astype(np.uint8)
    stego = flat.reshape(image.shape)

    # ---- save stego image ---------------------------------------------
    ensure_dir(output_dir)
    name_no_ext = os.path.splitext(output_name)[0]
    output_path = os.path.join(output_dir, name_no_ext + ".png")
    write_image(output_path, stego)

    return user_key
