import os
from imagekitio import ImageKit 
from config import IMAGEKIT_URL_ENDPOINT

imagekit = ImageKit(
    private_key=os.environ('IMAGEKIT_PRIVATE_KEY')
)

def upload_file(file_bytes: bytes, file_name: str, folder: str, content_type: str = 'image/png'):
    """ Upload the file to imagekit and return the CDN URL """
    try:
        response = imagekit.files.upload(
            file=(file_bytes, file_name, content_type),
            file_name=file_name,
            folder=folder,
            is_private_file=False,
            use_unique_file_name=True
        )
        return response.url
    except Exception as e:
        print(f'Error uploading to Imagekit: {e}')
        return None


def get_variants(base_url: str) -> dict[str, str]:
    """
    Generate multiple variants from base_url using imagekit transformations
    """
    return {
        'original': base_url,
        'web': f'{base_url}?tr=w-1280,h=720, c-maintain_ratio, fo-auto',
        'social': f'{base_url}?tr=w-1080,h=1080, c-maintain_ratio, fo-auto',
        'thumbnail': f'{base_url}?tr=w-640,h=360, c-maintain_ratio, fo-auto'
    }