import re

def extract_gutenberg_metadata(file_path):

    """
        Extracts title and author from plain text file

        Args: path to downloaded text file on HPC
        Return val: Dictionary storing title and author
        
     """
    
    metadata = {
        "title": "Not found",
        "author": "Not found"
    }

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if line.startswith("*** START OF"):
                break

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "title" and metadata["title"] == "Not found":
                metadata["title"] = value

            elif key == "author" and metadata["author"] == "Not found":
                metadata["author"] = value

            # stop early if both are found
            if metadata["title"] != "Not found" and metadata["author"] != "Not found":
                break

    return metadata

def update_metadata(cursor, metadata, file_path):

    """
        Updates title and author fields in database

        Args: cursor object from mysql connector, dictionary with metadata, storage path
        
    """

    title = metadata["title"]
    author = metadata["author"]
    
    cursor.execute(
        """
        UPDATE text_urls
        SET title = %s, author = %s
        WHERE storage_path = %s
        """,
        (title, author, file_path)
    )