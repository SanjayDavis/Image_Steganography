import cv2 as cv
import numpy as np
import json
import os
from cryptography.fernet import Fernet
import sys

def embed_data_in_image():
    image_path = input('Enter the image path: ')
    input_file = input('Enter the input file path: ')
    
    file_details = {
        'name': os.path.basename(input_file),
        'size': os.path.getsize(input_file)
    }
    print("File Details:", file_details)

    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    with open(input_file, 'rb') as file:
        file_data = file.read()
    
    User_key = Fernet.generate_key()
    print(f'Your key : {User_key.decode()}  ( Save this key for decrypting )')
    fernet = Fernet(User_key)
    file_data_encrypted = fernet.encrypt(file_data).decode()

    container = {
        "content": file_data_encrypted,
        "metadata": file_details
    }
    data = json.dumps(container)

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
    
    modified_image[:len(binary_data)] = (modified_image[:len(binary_data)] & 0b11111110)
    
    modified_image[:len(binary_data)] |= binary_data.astype(np.uint8)
    
    result_image = modified_image.reshape(image.shape)

    cv.imwrite('output.png', result_image)
    print('Data embedded successfully into output.png')


def extract_data_from_image():
    image_path = input('Enter the image path: ')
    User_key = input('Enter the key to decrypt: ')

    fernet = Fernet(User_key.encode())

    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    flat_image = image.flatten()
    
    lsbs = flat_image & 1
    
  
    chunk_size = 8192 
    extracted_text = ""
    
    for i in range(0, len(lsbs), chunk_size * 8):
        chunk_bits = lsbs[i:i + chunk_size * 8]
        
        remainder = len(chunk_bits) % 8
        if remainder != 0:
            chunk_bits = np.pad(chunk_bits, (0, 8 - remainder), 'constant')
        
        if len(chunk_bits) > 0:
            chunk_bits_reshaped = chunk_bits.reshape(-1, 8)
            powers = np.array([128, 64, 32, 16, 8, 4, 2, 1])
            chunk_bytes = np.sum(chunk_bits_reshaped * powers, axis=1)
            
            try:
                chunk_text = ''.join(chr(b) for b in chunk_bytes if 0 <= b <= 127)
                extracted_text += chunk_text
                
                if extracted_text.strip().startswith("{"):
                    brace_count = 0
                    json_end = -1
                    for idx, char in enumerate(extracted_text):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = idx + 1
                                break
                    
                    if json_end != -1:
                        json_text = extracted_text[:json_end]
                        try:
                            container = json.loads(json_text)
                            file_data_encrypted = container["content"].encode()
                            metadata = container["metadata"]

                            file_data = fernet.decrypt(file_data_encrypted)

                            with open(metadata["name"], "wb") as file:
                                file.write(file_data)

                            print("Data extracted successfully")
                            print("Metadata:", metadata)
                            return
                        except (json.JSONDecodeError, KeyError):
                            pass
            except (ValueError, UnicodeDecodeError):
                continue

    print("No valid JSON found, data may be corrupted.")


def extract_data_from_image_simple():
    """Alternative simpler extraction method - processes more data at once"""
    image_path = input('Enter the image path: ')
    User_key = input('Enter the key to decrypt: ')

    fernet = Fernet(User_key.encode())

    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    # Flatten image and extract all LSBs
    flat_image = image.flatten()
    lsbs = flat_image & 1
    
    # Take first 100KB worth of bits to look for JSON
    max_bits = min(len(lsbs), 100000 * 8)  # 100KB max
    relevant_bits = lsbs[:max_bits]
    
    # Reshape to bytes (pad if necessary)
    remainder = len(relevant_bits) % 8
    if remainder != 0:
        relevant_bits = np.pad(relevant_bits, (0, 8 - remainder), 'constant')
    
    # Convert to bytes using numpy vectorization
    bit_chunks = relevant_bits.reshape(-1, 8)
    powers = np.array([128, 64, 32, 16, 8, 4, 2, 1])
    byte_values = np.sum(bit_chunks * powers, axis=1)
    
    # Convert to string, handling potential invalid characters
    try:
        # Filter out non-printable characters for JSON detection
        valid_bytes = byte_values[byte_values < 128]  # ASCII only
        text = ''.join(chr(b) for b in valid_bytes)
        
        # Find complete JSON object
        if '{' in text and '}' in text:
            start_idx = text.find('{')
            brace_count = 0
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_text = text[start_idx:i+1]
                        try:
                            container = json.loads(json_text)
                            file_data_encrypted = container["content"].encode()
                            metadata = container["metadata"]

                            file_data = fernet.decrypt(file_data_encrypted)

                            with open(metadata["name"], "wb") as file:
                                file.write(file_data)

                            print("Data extracted successfully")
                            print("Metadata:", metadata)
                            return
                        except (json.JSONDecodeError, KeyError):
                            pass
    except Exception as e:
        print(f"Error during extraction: {e}")

    print("No valid JSON found, data may be corrupted.")


def get_metadata():
    image_path = input('Enter the image path: ')
    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    print("Image Shape (H,W,C):", image.shape)
    print("Total Pixels:", image.shape[0] * image.shape[1])
    print("Total Bits Available:", image.size)
    print("Total Bytes:", image.nbytes)
    
    # Additional capacity info
    max_data_bits = image.size  # 1 bit per pixel channel
    max_data_bytes = max_data_bits // 8
    print(f"Maximum embeddable data: {max_data_bytes} bytes ({max_data_bytes / 1024:.2f} KB)")


def main():
    print('Enter the choice:')
    print('1. Embed data in image')
    print('2. Extract data from image (chunk method)')
    print('3. Extract data from image (simple method)')
    print('4. Get Metadata')
    choice = int(input())
    if choice == 1:
        embed_data_in_image()
    elif choice == 2:
        extract_data_from_image()
    elif choice == 3:
        extract_data_from_image_simple()
    elif choice == 4:
        get_metadata()
    else:
        print('Invalid choice')


if __name__ == "__main__":
    main()