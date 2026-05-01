#!/bin/bash
#SBATCH --job-name=htc_text_array
#SBATCH --output=logs/htc_%A_%a.out
#SBATCH --error=logs/htc_%A_%a.err
#SBATCH --time=00:20:00
#SBATCH --mem=2G
#SBATCH --cpus-per-task=1

# Run like: sbatch --array=1-N htc_array.sh /standard/siller/ds2002/datadivers/unprocessed_urls.txt /standard/siller/ds2002/datadivers/results

set -euo pipefail

URL_FILE="$1"
RESULTS_DIR="$2"

TASK_ID="${SLURM_ARRAY_TASK_ID}"
URL=$(sed -n "${TASK_ID}p" "$URL_FILE")

mkdir -p logs
mkdir -p "$RESULTS_DIR"

if [ -z "$URL" ]; then
    echo "No URL found for task $TASK_ID"
    exit 1
fi

echo "Task $TASK_ID processing: $URL"

python3 - <<PY
import os
import sys
import mysql.connector

sys.path.append("/standard/siller/ds2002/datadivers")

from config.db_config import DB_CONFIG
from scripts.Download import download
from scripts.collect_metadata import extract_gutenberg_metadata, update_metadata

url = """$URL"""
results_dir = """$RESULTS_DIR"""

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

cursor.execute(
    "SELECT status FROM text_urls WHERE url = %s",
    (url,)
)
row = cursor.fetchone()

if row and row["status"] == "processed":
    print("Already processed. Skipping.")
    cursor.close()
    conn.close()
    sys.exit(0)

cursor.execute(
    "UPDATE text_urls SET status = %s WHERE url = %s",
    ("processing", url)
)
conn.commit()

file_path = download(url)

if file_path is None:
    cursor.execute(
        "UPDATE text_urls SET status = %s WHERE url = %s",
        ("failed", url)
    )
    conn.commit()
    cursor.close()
    conn.close()
    sys.exit(1)

cursor.execute(
    """
    UPDATE text_urls
    SET storage_path = %s, status = %s
    WHERE url = %s
    """,
    (str(file_path), "downloaded", url)
)
conn.commit()

metadata = extract_gutenberg_metadata(file_path)
update_metadata(cursor, metadata, str(file_path))
conn.commit()

safe_name = os.path.basename(str(file_path)).replace(".txt", "")
results_path = os.path.join(results_dir, safe_name + "_results.csv")

cursor.close()
conn.close()

print(f"TEXT_PATH={file_path}")
print(f"RESULTS_PATH={results_path}")

with open("task_paths_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.txt", "w") as f:
    f.write(str(file_path) + "\\n")
    f.write(results_path + "\\n")
PY

TEXT_PATH=$(sed -n '1p' task_paths_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.txt)
RESULTS_PATH=$(sed -n '2p' task_paths_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.txt)

echo "Running process_book.py..."
python3 scripts/process_book.py "$TEXT_PATH" "$RESULTS_PATH"

python3 - <<PY
import sys
import mysql.connector

sys.path.append("/standard/siller/ds2002/datadivers")

from config.db_config import DB_CONFIG

url = """$URL"""
results_path = """$RESULTS_PATH"""

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute(
    """
    UPDATE text_urls
    SET status = %s,
        results_path = %s
    WHERE url = %s
    """,
    ("processed", results_path, url)
)

conn.commit()
cursor.close()
conn.close()

print("Database updated to processed.")
PY

rm -f task_paths_${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}.txt

echo "Finished task $TASK_ID"