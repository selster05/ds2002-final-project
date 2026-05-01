import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG
import mysql.connector
import subprocess
#Run this file on HPC to find every unprocessed url.
def query_unprocessed():
    output_file = "/standard/siller/ds2002/datadivers/unprocessed_urls.txt"

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("SELECT url FROM text_urls WHERE status = 'unprocessed'")
    urls = cursor.fetchall()

    cursor.close()
    conn.close()

    if not urls:
        print("All URLS processed!")
        return

    with open(output_file, "w") as f:
        for (url,) in urls:
            f.write(url + "\n")

    print(f" {len(urls)} URL,written to {output_file}")

if __name__ == "__main__":
    
    query_unprocessed()