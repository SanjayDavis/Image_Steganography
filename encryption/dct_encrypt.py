import json, os, struct
import numpy as np
import cv2 as cv
from utils.crypto_utils import generate_key, encrypt_bytes
from utils.io_utils import ensure_dir, read_image, read_file_bytes
from utils.compression import compress_data, COMPRESSION_BACKEND


def _midband_positions():
    """Return mid-band (i,j) positions in a fixed reproducible order."""
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


_Q = 8   # Quantization step: IDCT noise must stay < Q/2=4 for round-trip stability


def _embed_block(pixels, bits, bit_idx):
    """
    Embed bits into the mid-band DCT coefficients of one 8x8 block.

    Uses Q=8 quantized coefficient embedding:
      - Quantize float coefficient to step-8 integer: c_q = round(c / 8)
      - Flip c_q parity to match desired bit if needed
      - De-quantize back: c_out = c_q * 8
    The quantization boundary is at ±Q/2=4, which is wider than typical
    mid-band IDCT round-trip noise, so no verification loop is needed.
    """
    n_avail = min(len(_POSITIONS), len(bits) - bit_idx)
    if n_avail <= 0:
        return pixels, bit_idx

    dct_block = cv.dct(pixels.astype(np.float32) - 128.0)
    for k, (i, j) in enumerate(_POSITIONS[:n_avail]):
        desired = int(bits[bit_idx + k])
        c_q = int(np.rint(dct_block[i, j] / _Q))   # quantize
        if c_q % 2 != desired:
            c_q = c_q + 1 if desired == 1 else c_q - 1
        dct_block[i, j] = float(c_q * _Q)           # de-quantize

    reconstructed = np.clip(cv.idct(dct_block) + 128.0, 0, 255).astype(np.uint8)
    return reconstructed, bit_idx + n_avail


def _embed_channel(channel, bits, bit_idx):
    padded, (oh, ow) = _pad_channel(channel)
    h, w = padded.shape
    out = padded.copy()
    for y in range(0, h, 8):
        if bit_idx >= len(bits):
            break
        for x in range(0, w, 8):
            if bit_idx >= len(bits):
                break
            new_block, bit_idx = _embed_block(padded[y:y+8, x:x+8], bits, bit_idx)
            out[y:y+8, x:x+8] = new_block
    return out[:oh, :ow], bit_idx


def dct_embed(image_path, input_file_path, output_dir="images", output_name="output_dct.png"):
    """
    Embed a secret file into a cover image using DCT steganography.

    Saves as PNG (lossless) so the embedded pixel differences survive.
    A 32-bit big-endian length header is prepended to the bit-stream so
    extraction can read exactly the right number of bits.

    Returns the Fernet encryption key string.
    """
    bgr = read_image(image_path)
    if bgr is None:
        raise ValueError(f"Cannot open image: {image_path}")

    raw_data = read_file_bytes(input_file_path)
    compressed = compress_data(raw_data)
    user_key = generate_key()
    encrypted_content = encrypt_bytes(compressed, user_key)

    file_meta = {
        "name": os.path.basename(input_file_path),
        "original_size": len(raw_data),
        "compressed_size": len(compressed),
        "compression": COMPRESSION_BACKEND,
    }
    container = {"content": encrypted_content, "metadata": file_meta}
    json_bytes = json.dumps(container).encode("utf-8")

    # 32-bit big-endian header = number of JSON bytes
    header = struct.pack(">I", len(json_bytes))
    payload_bytes = header + json_bytes
    bits = np.unpackbits(np.frombuffer(payload_bytes, dtype=np.uint8))

    b_ch, g_ch, r_ch = cv.split(bgr)

    bit_idx = 0
    b_out, bit_idx = _embed_channel(b_ch, bits, bit_idx)
    g_out, bit_idx = _embed_channel(g_ch, bits, bit_idx) if bit_idx < len(bits) else (g_ch, bit_idx)
    r_out, bit_idx = _embed_channel(r_ch, bits, bit_idx) if bit_idx < len(bits) else (r_ch, bit_idx)

    if bit_idx < len(bits):
        raise ValueError(
            f"Payload too large: embedded {bit_idx}/{len(bits)} bits. "
            "Use a larger cover image."
        )

    stego_bgr = cv.merge((b_out, g_out, r_out))
    ensure_dir(output_dir)
    # Always save as PNG (lossless) regardless of output_name extension
    name_no_ext = os.path.splitext(output_name)[0]
    output_path = os.path.join(output_dir, name_no_ext + ".png")
    cv.imwrite(output_path, stego_bgr)
    return user_key
