import os


def embed_data(image_path: str, input_file_path: str) -> str:
	"""
	Placeholder for DCT-based steganography embedding.

	Args:
		image_path: Path to the cover image.
		input_file_path: Path to the file to embed.

	Returns:
		Path to the output stego image once implemented.

	Raises:
		NotImplementedError: This is a stub for future DCT implementation.
	"""
	raise NotImplementedError("DCT-based embedding not implemented yet. Add implementation in stego_dct.embed_data().")


def extract_data(image_path: str, key: str) -> None:
	"""
	Placeholder for DCT-based steganography extraction.

	Args:
		image_path: Path to the stego image.
		key: Decryption key for extracting the payload.

	Raises:
		NotImplementedError: This is a stub for future DCT implementation.
	"""
	raise NotImplementedError("DCT-based extraction not implemented yet. Add implementation in stego_dct.extract_data().")


