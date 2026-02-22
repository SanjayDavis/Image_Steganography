"""
LSB (Least Significant Bit) Steganography – Extraction
=======================================================
Workflow
--------
1. Read the stego image and collect every pixel-channel LSB.
2. Scan the bit-stream in chunks, assembling a text buffer until a valid
   JSON container is found.
3. Decrypt the payload, **decompress** it, then save with the original name.

Returns
-------
``lsb_extract`` returns a dict with ``output_path`` and ``metadata`` so the
GUI can show a success summary without having to re-open the file.
"""

import json
import numpy as np

from utils.crypto_utils import decrypt_to_bytes
from utils.io_utils import ensure_dir, read_image, write_bytes
from utils.compression import decompress_data


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _try_parse_container(text: str) -> dict | None:
    """
    Scan *text* for the first valid JSON object and return it, or ``None``.

    Searches from the first ``{`` and counts braces to find the closing ``}``.
    """
    if not text or "{" not in text:
        return None
    start = text.find("{")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _bits_to_text_chunk(bits: np.ndarray) -> str:
    """Convert a bit-array (multiple of 8) to an ASCII/printable string."""
    reshaped = bits.reshape(-1, 8)
    powers = np.array([128, 64, 32, 16, 8, 4, 2, 1], dtype=np.uint8)
    byte_vals = (reshaped * powers).sum(axis=1)
    return "".join(chr(b) for b in byte_vals if 0 <= b <= 127)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lsb_extract(
    image_path: str,
    user_key: str,
    output_dir: str = "extracted",
) -> dict:
    """
    Extract and decrypt a hidden file from an LSB stego image.

    The function reads the image in 8 192-byte chunks so it can stop as
    soon as the JSON container is fully assembled (early exit = fast).

    Pipeline: LSBs → JSON container → decrypt → decompress → file.

    Args:
        image_path: Path to the stego image.
        user_key:   Fernet key produced during embedding.
        output_dir: Directory where the recovered file is saved.

    Returns:
        ``{"output_path": str, "metadata": dict}``

    Raises:
        ValueError: Key invalid, image unreadable, or no hidden data found.
    """
    image = read_image(image_path)
    if image is None:
        raise ValueError(f"Cannot open image: {image_path}")

    lsbs = (image.flatten() & 1).astype(np.uint8)

    chunk_bits = 8_192 * 8            # bits per iteration
    extracted_text = ""

    for start in range(0, len(lsbs), chunk_bits):
        chunk = lsbs[start : start + chunk_bits]

        # Pad to a multiple of 8
        remainder = len(chunk) % 8
        if remainder:
            chunk = np.pad(chunk, (0, 8 - remainder), constant_values=0)

        extracted_text += _bits_to_text_chunk(chunk)

        container = _try_parse_container(extracted_text.strip())
        if container:
            # ---- decrypt → decompress → save --------------------------
            encrypted = container["content"].encode()
            metadata = container["metadata"]

            compressed = decrypt_to_bytes(encrypted, user_key)
            raw_data = decompress_data(compressed)

            ensure_dir(output_dir)
            out_path = f"{output_dir}/{metadata['name']}"
            write_bytes(out_path, raw_data)
            return {"output_path": out_path, "metadata": metadata}

    raise ValueError("No hidden data found in the image (wrong key or untouched image?).")
