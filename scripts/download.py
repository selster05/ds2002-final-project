import requests
from pathlib import Path

def download(url):

    file_name = url.split('/')[-1]
    base_dir = Path("/standard/siller/ds2002/datadivers")
    file_path = base_dir / file_name

    if file_path.exists():
        return file_path

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Download failed: {e}")
        return None

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(response.text)

    return file_path