import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG
import mysql.connector
## The file regists books from a local url file and sets the status in the database as unprocessed
def register_urls(url_file):
    with open(url_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for url in urls:
        cursor.execute("SELECT id FROM text_urls WHERE url = %s", (url,))
        result = cursor.fetchone()

        if result:
            print(f"[Existed] {url}")
        else:
            cursor.execute(
                "INSERT INTO text_urls (url, status) VALUES (%s, %s)",
                (url, "unprocessed")
            )
            conn.commit()
            print(f"[registered] {url}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("arguments: python register.py URL")
        sys.exit(1)
    register_urls(sys.argv[1])