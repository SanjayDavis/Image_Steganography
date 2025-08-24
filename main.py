import cv2 as cv
import json
import os
import base64

def embed_data_in_image():
    image_path = input('Enter the image path: ')
    input_file = input('Enter the input file path: ')
    
    # get file details
    file_details = {
        'name': os.path.basename(input_file),
        'size': os.path.getsize(input_file)
    }
    print(file_details)

    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    # read file as bytes (supports any type)
    with open(input_file, 'rb') as file:
        file_data = file.read()
    
    # encode file content as base64 to keep JSON safe
    file_data_b64 = base64.b64encode(file_data).decode('utf-8')

    container = {
        "content": file_data_b64,
        "metadata": file_details
    }
    data = json.dumps(container)

    # convert to binary
    binary_data = ''.join(format(ord(char), '08b') for char in data)

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
    print('Data embedded successfully')


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

                    # Try JSON parse as soon as it looks valid
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
    
    print("No valid JSON found, data may be corrupted.")


def get_metadata():
    image_path = input('Enter the image path: ')
    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    print("Image Shape:", image.shape)
    print("Total Pixels:", image.size)
    print("Data Type:", image.dtype)
    print("Bytes per Item:", image.itemsize)
    print("Total Bytes:", image.nbytes)
    print("Dimensions:", image.ndim)


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
        return


if __name__ == "__main__":
    main()
