from utils.io_utils import read_image
from embed_lsb import embed as lsb_embed
from extract_lsb import extract_chunked as lsb_extract_chunked, extract_simple as lsb_extract_simple
from embed_dct import embed as dct_embed
from extract_dct import extract as dct_extract


def print_metadata(image_path: str) -> None:
    image = read_image(image_path)
    if image is None:
        raise ValueError("Image not found")
    print("Image Shape (H,W,C):", image.shape)
    print("Total Pixels:", image.shape[0] * image.shape[1])
    print("Total Bits Available:", image.size)
    print("Total Bytes:", image.nbytes)
    max_data_bits = image.size
    max_data_bytes = max_data_bits // 8
    print(f"Maximum embeddable data: {max_data_bytes} bytes ({max_data_bytes / 1024:.2f} KB)")


def main():
    print('Enter the choice:')
    print('1. Embed data in image (LSB)')
    print('2. Extract data from image (LSB, chunk method)')
    print('3. Extract data from image (LSB, simple method)')
    print('4. Get Metadata')
    print('5. DCT Embed data (placeholder)')
    print('6. DCT Extract data (placeholder)')
    choice = int(input())
    if choice == 1:
        image_path = input('Enter the image path: ')
        input_file = input('Enter the input file path: ')
        lsb_embed(image_path, input_file)
    elif choice == 2:
        image_path = input('Enter the image path: ')
        user_key = input('Enter the key to decrypt: ')
        lsb_extract_chunked(image_path, user_key)
    elif choice == 3:
        image_path = input('Enter the image path: ')
        user_key = input('Enter the key to decrypt: ')
        lsb_extract_simple(image_path, user_key)
    elif choice == 4:
        image_path = input('Enter the image path: ')
        print_metadata(image_path)
    elif choice == 5:
        image_path = input('Enter the image path: ')
        input_file = input('Enter the input file path: ')
        try:
            dct_embed(image_path, input_file)
        except NotImplementedError as e:
            print(e)
    elif choice == 6:
        image_path = input('Enter the image path: ')
        user_key = input('Enter the key to decrypt: ')
        try:
            dct_extract(image_path, user_key)
        except NotImplementedError as e:
            print(e)
    else:
        print('Invalid choice')


if __name__ == "__main__":
    main()