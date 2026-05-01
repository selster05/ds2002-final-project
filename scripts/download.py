import requests
from pathlib import Path
from urllib.parse import urlparse


def download_text(url):
    """
    Takes given url and returns storage path to downloaded text file

    Args: url to plain text file
    Return val: Download path on HPC
    
    """
    file_name = url.split('/')[-1]
    base_dir = Path("/standard/siller/ds2002/datadivers/downloads")
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


def extract_source(url):
    """
    Takes given url and extracts source

    Args: url to plain text file
    Return val: source as string
    
    """
    parsed = urlparse(url)
    source = parsed.netloc.replace("www.", "")

    return source


def update_source(cursor, url):
    """
    Updates database with source of url 

    Args: cursor object from mysql connector and url to plain text file
    
    """
    source = extract_source(url)

    cursor.execute(
        """
        UPDATE text_urls
        SET source = %s
        WHERE url = %s
        """,
        (source, url)
    )


def update_storage_path(cursor, url, file_path):
    """
    Updates database with storage path of url 

    Args: cursor object from mysql connector, url to plain text file and storage path
    
    """
    cursor.execute(
        """
        UPDATE text_urls
        SET storage_path = %s, status = %s
        WHERE url = %s
        """,
        (str(file_path), "downloaded", url)
    )