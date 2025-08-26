import cv2 as cv
import json
import os
import base64
import sys

def embed_data_in_image():
    image_path = input('Enter the image path: ')
    input_file = input('Enter the input file path: ')
    
    # get file details
    file_details = {
        'name': os.path.basename(input_file),
        'size': os.path.getsize(input_file)
    }
    print("File Details:", file_details)

    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    # read file as bytes
    with open(input_file, 'rb') as file:
        file_data = file.read()
    
    # encode file content as base64
    file_data_b64 = base64.b64encode(file_data).decode('utf-8')

    container = {
        "content": file_data_b64,
        "metadata": file_details
    }
    data = json.dumps(container)

    binary_data = ''.join(format(ord(char), '08b') for char in data)
    image_capacity_bits = image.size  
    print(f"Image capacity (bits): {image_capacity_bits}")
    print(f"Data size (bits): {len(binary_data)}")

    if len(binary_data) > image_capacity_bits:
        print("Error: Data too large to fit in image!")
        sys.exit(1)
    else:
        print("Data fits in image")

    data_index = 0
    for row in image:
        for pixel in row:
            for channel in range(3):  # B, G, R
                if data_index < len(binary_data):
                    bit = binary_data[data_index]
                    if bit == '1':
                        pixel[channel] = pixel[channel] | 0b00000001
                    else:
                        pixel[channel] = pixel[channel] & 0b11111110
                    data_index += 1
                else:
                    break

    cv.imwrite('output.png', image)
    print('Data embedded successfully into output.png')


def extract_data_from_image():
    image_path = input('Enter the image path: ')
    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    binary_data = ""
    extracted_text = ""

    for row in image:
        for pixel in row:
            for channel in range(3):
                binary_data += str(pixel[channel] & 1)

                if len(binary_data) == 8:
                    char = chr(int(binary_data, 2))
                    extracted_text += char
                    binary_data = ""

                    # Try JSON parse
                    if extracted_text.strip().startswith("{") and extracted_text.strip().endswith("}"):
                        try:
                            container = json.loads(extracted_text)
                            file_data_b64 = container["content"]
                            metadata = container["metadata"]

                            file_data = base64.b64decode(file_data_b64)

                            with open(metadata["name"], "wb") as file:
                                file.write(file_data)

                            print("Data extracted successfully")
                            print("Metadata:", metadata)
                            return
                        except Exception:
                            pass

    print(" No valid JSON found, data may be corrupted.")


def get_metadata():
    image_path = input('Enter the image path: ')
    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    print("Image Shape (H,W,C):", image.shape)
    print("Total Pixels:", image.shape[0] * image.shape[1])
    print("Total Bits Available:", image.size)
    print("Total Bytes:", image.nbytes)


def main():
    print('Enter the choice:')
    print('1. Embed data in image')
    print('2. Extract data from image')
    print('3. Get Metadata')
    choice = int(input())
    if choice == 1:
        embed_data_in_image()
    elif choice == 2:
        extract_data_from_image()
    elif choice == 3:
        get_metadata()
    else:
        print('Invalid choice')


if __name__ == "__main__":
    main()
