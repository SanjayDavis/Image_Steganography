# Image Steganography Tool

A comprehensive image steganography application with GUI support for hiding and extracting files from images using LSB and DCT techniques.

## Features
- **LSB Steganography**: Hide files in the least significant bits of image pixels
- **DCT Steganography**: Advanced embedding using discrete cosine transform on mid-band coefficients
- **Encryption**: All embedded data is encrypted using Fernet symmetric encryption
- **Multiple Extraction Methods**: Chunked (robust) and simple (fast) extraction for LSB
- **Image Metadata**: View image capacity and steganography information
- **User-Friendly GUI**: Modern interface with tabs for different operations
- **File Support**: Works with any file type

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the GUI application:
```bash
python gui.py
```

Or use the library programmatically:
```python
from steganography import lsb_embed, lsb_extract_chunked

# Embed a file
lsb_embed('cover.png', 'secret.txt')

# Extract a file
lsb_extract_chunked('stego.png', 'encryption_key')
```

## Capacity
- For 1920x1080 image: ~758 KB maximum file size
- For larger files: Use compression software (zip, 7z, etc.)

## Supported Formats
- **Images**: PNG, JPG, JPEG, BMP
- **Files**: Any file type (text, binary, archives, etc.)

