import cv2 as cv
import numpy as np
import json
import os
from cryptography.fernet import Fernet
import sys


def embed_data(image_path: str, input_file_path: str) -> str:
	file_details = {
         'name': os.path.basename(input_file_path),
         'size': os.path.getsize(input_file_path)
    }
	print(file_details)
	image = cv.imread(image_path)
	if image is None:
		raise ValueError("Image not found")
    
	with open(input_file_path, 'rb') as file:
		file_data = file.read()
	
	print("Do you want encryption ?")
	print("1. Yes ( More space is taken , file should be small )")
	print("2. No  ( A Medium sized file upto 10kb can be stored )")
	choice = int(input(print("Enter a choice :")))

	container = {} 

	if choice == 1:
		User_key = Fernet.generate_key()
		print(f'Your key : {User_key.decode()}  ( Save this key for decrypting )')
		fernet = Fernet(User_key)
		file_data_encrypted = fernet.encrypt(file_data).decode()

		container = {
			"content": file_data_encrypted,
			"metadata": file_details,
			"encrypted": 1
		}

	elif choice == 0:
		container = {
			"content": file_data,
			"metadata": file_details,
		}  

	data = json.dumps(container)s
	data_bytes = np.frombuffer(data.encode('utf-8'), dtype=np.uint8)
	binary_data = np.unpackbits(data_bytes)
    
	image_capacity_bits = image.size  
	print(f"Image capacity (bits): {image_capacity_bits}")
	print(f"Data size (bits): {len(binary_data)}")

	if len(binary_data) > image_capacity_bits:
		print("Error: Data too large to fit in image!")
		sys.exit(1)
	else:
		print("Data fits in image")

	flat_image = image.flatten()

	modified_image = flat_image.copy()
    
	# now we need to modify the image
    
	result_image = modified_image.reshape(image.shape)

	os.makedirs('images', exist_ok=True)
	output_path = os.path.join('images', 'output.png')
	cv.imwrite(output_path, result_image)
	print(f'Data embedded successfully into {output_path}')


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


