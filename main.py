import cv2 as cv


end_string = "###END###"

def embed_data_in_image():
    image_path = input('Enter the image path:')
    input_file = input('Enter the input file path:')
    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    with open(input_file, 'r') as file:
        data = file.read()
    data += end_string

    #get binary data
    binary_data = ''.join(format(ord(char),'08b') for char in data)
    binary_data += ''


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
    image_path = input('Enter the image path:')
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

                    if extracted_text.endswith(end_string):
                        with open('output.txt', 'w') as file:
                            file.write(extracted_text[:-len(end_string)])
                        print("Data extracted successfully")
                        return
    
    print("No END marker found, data may be corrupted.")



def get_metadata():
    image_path = input('Enter the image path:')
    image = cv.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    
    print(image)
    print(image.shape)
    print(image.size)
    print(image.dtype)
    print(image.itemsize)
    print(image.nbytes)
    print(image.ndim)


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