import json, os, struct
import numpy as np
import cv2 as cv
from utils.crypto_utils import decrypt_to_bytes
from utils.io_utils import ensure_dir, read_image, write_bytes
from utils.compression import decompress_data


def _midband_positions():
    """Same position order as dct_encrypt — must never diverge."""
    return [(i, j) for i in range(8) for j in range(8)
            if (i + j) in range(3, 7) and not (i == 0 and j == 0)]


_POSITIONS = _midband_positions()


def _pad_channel(ch):
    h, w = ch.shape
    ph = (8 - h % 8) % 8
    pw = (8 - w % 8) % 8
    if ph or pw:
        ch = cv.copyMakeBorder(ch, 0, ph, 0, pw, cv.BORDER_REPLICATE)
    return ch, (h, w)


_Q = 8   # Must match encryption/dct_encrypt._Q exactly


def _extract_block_bits(pixels):
    """Decode Q=8-quantized parity from all mid-band DCT positions."""
    dct_block = cv.dct(pixels.astype(np.float32) - 128.0)
    return [int(np.rint(dct_block[i, j] / _Q)) % 2 for i, j in _POSITIONS]


def _extract_all_channel_bits(channel):
    """Extract ALL parity bits from every 8x8 block in the channel."""
    padded, _ = _pad_channel(channel)
    h, w = padded.shape
    bits = []
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            bits.extend(_extract_block_bits(padded[y:y+8, x:x+8]))
    return bits


def _bits_to_bytes(bits):
    arr = np.array(bits, dtype=np.uint8)
    pad = (8 - len(arr) % 8) % 8
    if pad:
        arr = np.concatenate([arr, np.zeros(pad, dtype=np.uint8)])
    return np.packbits(arr).tobytes()


def dct_extract(image_path, user_key, output_dir="extracted"):
    """
    Extract and decrypt a hidden file from a DCT stego PNG.

    Reads the 32-bit length header first, then reads exactly that many bytes
    from the bit-stream — no fragile JSON scanning needed.

    Returns {"output_path": str, "metadata": dict}.
    """
    bgr = read_image(image_path)
    if bgr is None:
        raise ValueError(f"Cannot open image: {image_path}")

    b_ch, g_ch, r_ch = cv.split(bgr)

    HEADER_BITS = 32
    all_bits = []
    payload_bytes_count = None
    total_bits_needed = None

    # Single pass: collect channel bits until we have everything we need
    for channel in (b_ch, g_ch, r_ch):
        all_bits.extend(_extract_all_channel_bits(channel))

        # Parse header as soon as we have 32 bits
        if payload_bytes_count is None and len(all_bits) >= HEADER_BITS:
            (payload_bytes_count,) = struct.unpack(
                ">I", _bits_to_bytes(all_bits[:HEADER_BITS])[:4]
            )
            if payload_bytes_count == 0 or payload_bytes_count > 50_000_000:
                raise ValueError(
                    f"Invalid payload length {payload_bytes_count} — "
                    "wrong image or not embedded with this tool."
                )
            total_bits_needed = HEADER_BITS + payload_bytes_count * 8

        if total_bits_needed is not None and len(all_bits) >= total_bits_needed:
            break

    if payload_bytes_count is None:
        raise ValueError(
            "Could not read length header — image too small or not a stego image."
        )
    if len(all_bits) < total_bits_needed:
        raise ValueError(
            f"Only {len(all_bits)} bits extracted, need {total_bits_needed}. "
            "Image may be corrupt or the wrong file."
        )

    payload_bits = all_bits[HEADER_BITS: HEADER_BITS + payload_bytes_count * 8]
    json_raw = _bits_to_bytes(payload_bits)[:payload_bytes_count]

    try:
        container = json.loads(json_raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(
            f"Failed to parse embedded JSON: {exc}\n"
            "The key may be wrong, or the image was not created by this tool."
        ) from exc

    try:
        compressed = decrypt_to_bytes(container["content"].encode(), user_key)
    except Exception as exc:
        raise ValueError(
            f"Decryption failed (wrong key or corrupt data): {exc}"
        ) from exc

    raw_data = decompress_data(compressed)
    metadata = container["metadata"]

    ensure_dir(output_dir)
    out_path = os.path.join(output_dir, metadata["name"])
    write_bytes(out_path, raw_data)
    return {"output_path": out_path, "metadata": metadata}
