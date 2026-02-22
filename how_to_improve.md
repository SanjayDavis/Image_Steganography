# How to Improve: QR-Code-Like Robustness in Steganography

> **Goal:** Make hidden data recoverable even if part of the image is damaged — similar to how a QR code can still be decoded when partially obscured or torn.

---

## The Core Problem

Current LSB and DCT implementations embed each bit **once**, sequentially. A small crop, heavy compression, or localized damage destroys the bitstream from that point forward — no recovery possible.

QR codes survive damage because they use **Reed–Solomon error-correcting codes (ECC)** plus structured redundancy. We need the same layered approach.

---

## Strategy Overview

```
file
 ↓  zlib compress
 ↓  Fernet encrypt
 ↓  ECC encode          ← add parity bits so partial loss is recoverable
 ↓  scatter/repeat      ← spread bits so one damaged region ≠ total loss
 ↓  embed (LSB/DCT)     ← in transform domain for extra resilience
 ↓  output image / video frames
```

---

## Idea 1 — Bit Repetition + Majority Vote (Easiest)

Embed each bit N times; on extraction take the majority.

```
Embed:    1 → 1 1 1    0 → 0 0 0
Extract:  1 1 0  →  majority → 1
          0 0 1  →  majority → 0
```

- **N=3** → 3× size overhead, corrects 1-bit-in-3 errors
- **N=5** → 5× size overhead, corrects 2-bit-in-5 errors

**Pros:** trivially simple, works with existing LSB/DCT code.  
**Cons:** capacity drops to 1/N. Useless if the entire embedded region is wiped.

---

## Idea 2 — Hamming(7,4) Code (Best Balance)

Take 4 data bits, add 3 parity bits → 7-bit codeword.  
Can **detect and correct any single-bit error** per block.

```
Input block:  1 0 1 1          (4 bits)
Codeword:     1 0 1 1 0 1 0    (7 bits, example)
If one bit flips → auto-corrected on extraction.
```

- ~75% overhead (vs 200% for triple repetition)
- Standard library available: `crc` or pure Python `pyhamming`
- Scales up to Hamming(15,11), (31,26) for higher efficiency

**Implementation sketch:**
```python
import pyhamming  # or implement encode/decode from scratch

def hamming_encode(data: bytes) -> bytes: ...
def hamming_decode(data: bytes) -> bytes: ...

# pipeline: compress → encrypt → hamming_encode → embed
```

---

## Idea 3 — Reed–Solomon ECC (Production-Grade)

The same ECC used by QR codes, CDs, and DVDs.

- Takes K data bytes, produces K + 2T bytes (T = correctable symbol errors)
- Can recover from up to T **missing** symbols (erasures) or T/2 **corrupted** symbols
- Ishengoma (2014) showed ~97% secret recovery using RS parity embedding

```python
import reedsolo

rs = reedsolo.RSCodec(20)           # 20 parity symbols → fix up to 10 lost bytes
encoded = rs.encode(payload_bytes)  # embed this
decoded = rs.decode(extracted)      # correct errors on extraction
```

**Recommended parity:** 10–20% of payload size for normal use; up to 40–50% for high resilience.

---

## Idea 4 — Scatter Bits with Pseudo-Random Positions (Anti-Crop)

Sequential embedding is fragile — crop the top-left corner and the entire header/length field is gone.

Instead, derive pixel positions from the encryption key:

```python
import hashlib, random

def pixel_positions(key: str, n_bits: int, max_idx: int):
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    return rng.sample(range(max_idx), n_bits)
```

- Both embedder and extractor derive the same positions from the key
- Cropping a corner destroys ~(crop_area / total_area) fraction of bits, not all
- Combined with ECC, partial crop becomes fully recoverable

---

## Idea 5 — Multi-Channel Redundancy

Embed the same bit (or ECC-encoded copies) in **multiple channels or multiple images**.

```
R channel  ← copy 1
G channel  ← copy 2
B channel  ← copy 3  (majority vote across channels)
```

Or: embed the primary payload in channel R, a parity copy in G.  
If R is damaged, reconstruct from G.

**Cross-image:** split the ECC-encoded stream across two cover images. Losing one image only loses half the codeword — RS corrects the rest.

---

## Idea 6 — Transform-Domain Embedding (DCT/DWT/SVD)

Raw LSB is destroyed by JPEG recompression, resizing, or noise filters.  
Hiding in frequency coefficients survives these operations.

- **DCT** (already implemented): mid-band coefficients survive mild JPEG requantization
- **DWT (Discrete Wavelet Transform)**: embed in LL sub-band for survial under resizing
- **DWT + SVD**: Khassawneh et al. (2025) embedded a QR watermark this way — survived 50% cropping with normalized correlation ~0.99

**Our DCT implementation already uses this.** To improve: embed in lower-frequency bands (smaller `i+j` diagonal) for higher resilience, at the cost of capacity.

---

## Idea 7 — Video as Container (Maximum Redundancy)

Videos are sequences of frames — each frame is an image. This gives massive redundancy opportunity.

**Approach:**
1. ECC-encode the payload (e.g. RS with 30% parity)
2. Split the encoded bitstream into N chunks
3. Embed chunk `i` into frame `i`, AND repeat it in frame `i+K` (K = redundancy gap)
4. Extraction: collect all frames, vote/ECC-correct across duplicates

**Why video wins:**
- Losing 10 frames out of 300 = ~3% loss → RS corrects easily
- Can hide in motion vectors or DCT blocks of compressed video (H.264 macroblocks)
- Frames can collectively hold gigabytes of data

**Practical tools:** OpenCV `VideoCapture` / `VideoWriter`, or `ffmpeg-python`.

---

## Idea 8 — Checksum per Block (Corruption Detection)

Divide the embedded payload into blocks and append a CRC per block:

```
[ 32 bytes data ][ 2 bytes CRC16 ][ 32 bytes data ][ 2 bytes CRC16 ] ...
```

On extraction:
- If CRC matches → block is good
- If CRC fails → attempt recovery from a second embedded copy

Not error-correcting on its own, but combined with redundancy (Idea 5) gives detect-then-fallback.

---

## Recommended Implementation Order

| Priority | Idea | Effort | Gain |
|----------|------|--------|------|
| 1 | **Reed–Solomon ECC** (Idea 3) | Medium | High — actual error correction |
| 2 | **Pseudo-random scatter** (Idea 4) | Low | High — anti-crop |
| 3 | **Multi-channel redundancy** (Idea 5) | Low | Medium — anti-local-damage |
| 4 | **Video frame distribution** (Idea 7) | High | Very High — maximum resilience |
| 5 | Hamming code (Idea 2) | Low | Medium — simpler than RS |
| 6 | Bit repetition (Idea 1) | Trivial | Low — last resort |

---

## Full Robust Pipeline (Target Architecture)

```
Input file
  │
  ├─ zlib compress
  ├─ Fernet encrypt (key → also seeds scatter RNG)
  ├─ Reed–Solomon encode (+20% parity symbols)
  ├─ Scatter: map bit positions using key-derived RNG
  ├─ Embed: LSB across R+G+B channels (3× redundancy per bit)
  └─ Output: PNG (lossless)

Extraction:
  ├─ Scatter: recompute positions from key
  ├─ Collect bits from R+G+B → majority vote
  ├─ Reed–Solomon decode (correct up to 10% symbol errors)
  ├─ Fernet decrypt
  └─ zlib decompress → original file
```

This pipeline can survive:
- Up to ~15% of the image being cropped or overwritten (RS + scatter)
- JPEG re-saves at moderate quality (DCT domain)
- Single-channel corruption (multi-channel redundancy)

---

## References

- Ishengoma (2014) — Reed–Solomon parity embedding, ~97% recovery
- Khassawneh et al. (2025) — DWT+SVD+Schur QR watermark, survives 50% crop
- StackOverflow H.264 stego thread — "use forward error correction and lots of redundancy"
- YouTube: [How to store data in images robustly](https://youtu.be/l03Os5uwWmk)
- `reedsolo` Python library: https://github.com/tomerfiliba-org/reedsolomon
