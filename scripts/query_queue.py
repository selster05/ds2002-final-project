import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG
import mysql.connector
import subprocess
#Run this file on HPC to find every unprocessed url and submit job array.
def query_unprocessed(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "unprocessed_urls.txt")

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

    n = len(urls)
    subprocess.run([
        "sbatch",
        f"--array=1-{n}",
        "slurm/job_array.slurm",
        output_dir
    ])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("arguments: python query_queue.py output directory")
        sys.exit(1)
    query_unprocessed(sys.argv[1])