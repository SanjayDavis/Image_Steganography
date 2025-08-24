# Image Steganography

This project hides files inside an image using Least Significant Bit (LSB) steganography and extracts them back.

## Features
- Hide any file inside a PNG image.
- Extract the file back with its original name.
- Works with any file type (data is stored in Base64).
- Minimal visual change in the image.

## How It Works
1. The file is read and encoded in Base64.
2. Metadata (like filename and size) along with the content is stored in JSON format.
3. The JSON is embedded in the least significant bits of the image pixels.
4. During decoding, the bits are read back, JSON is reconstructed, Base64 decoded, and the file is restored.

## Usage

### Hide a file inside an image
```bash
python encode.py
