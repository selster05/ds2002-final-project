#!/bin/bash

#SBATCH --partition=standard
#SBATCH --job-name=htc_text_array
#SBATCH --output=/standard/siller/ds2002/datadivers/logs/htc_%A_%a.out
#SBATCH --error=/standard/siller/ds2002/datadivers/logs/htc_%A_%a.err
#SBATCH --time=00:20:00
#SBATCH --mem=2G
#SBATCH --cpus-per-task=1

# Run like: sbatch --array=1-N htc_array.sh /standard/siller/ds2002/datadivers/unprocessed_urls.txt /standard/siller/ds2002/datadivers/results

cd "$SLURM_SUBMIT_DIR"

set -euo pipefail

# Add this near the top, after set -euo pipefail
trap 'on_error' ERR

on_error() {
    echo "Unexpected error in task $TASK_ID — marking failed in DB"
    python3 - <<PY
import os, sys
sys.path.insert(0, os.environ.get("SLURM_SUBMIT_DIR", "."))
try:
    import mysql.connector
    from config.db_config import DB_CONFIG
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE text_urls SET status = %s WHERE url = %s",
        ("failed", """$URL""")
    )
    conn.commit()
    cursor.close()
    conn.close()
    print("DB marked failed.")
except Exception as e:
    print(f"Could not update DB: {e}", file=sys.stderr)
PY
}

URL_FILE="$1"
DOWNLOAD_DIR="/standard/siller/ds2002/datadivers/downloads"
OUT_DIR="/standard/siller/ds2002/datadivers/results"

TASK_ID="${SLURM_ARRAY_TASK_ID}"
URL=$(sed -n "${TASK_ID}p" "$URL_FILE")

mkdir -p /standard/siller/ds2002/datadivers/logs
mkdir -p "$DOWNLOAD_DIR"
mkdir -p "$OUT_DIR"

if [ -z "$URL" ]; then
    echo "No URL found for task $TASK_ID"
    exit 1
fi

echo "Task $TASK_ID processing: $URL"

python3 - <<PY
import os
import sys
import mysql.connector


PROJECT_ROOT = os.environ["SLURM_SUBMIT_DIR"]
sys.path.insert(0, PROJECT_ROOT)


from config.db_config import DB_CONFIG
from scripts.download import download_text, update_source
from scripts.collect_metadata import extract_gutenberg_metadata, update_metadata

url = """$URL"""
out_dir = """$OUT_DIR"""

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

file_path = download_text(url)

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
update_source(cursor, url)
conn.commit()

safe_name = os.path.basename(str(file_path)).replace(".txt", "")
results_path = os.path.join(out_dir, safe_name + "_results.csv")

cursor.close()
conn.close()

print(f"TEXT_PATH={file_path}")
print(f"RESULTS_PATH={results_path}")


PY

TEXT_PATH=$(python3 - <<PY
import os, sys, mysql.connector
sys.path.insert(0, os.environ["SLURM_SUBMIT_DIR"])
from config.db_config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT storage_path FROM text_urls WHERE url = %s", ("""$URL""",))
row = cursor.fetchone()
cursor.close()
conn.close()
print(row["storage_path"])
PY
)
RESULTS_PATH="/standard/siller/ds2002/datadivers/results/$(basename ${TEXT_PATH%.txt})_results.csv"


echo "Running process_book.py..."
if ! python3 scripts/process_book.py "$TEXT_PATH" "$RESULTS_PATH"; then
    echo "process_book.py failed for task $TASK_ID"
    python3 - <<PY
import os, sys, mysql.connector
sys.path.insert(0, os.environ["SLURM_SUBMIT_DIR"])
from config.db_config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute(
    "UPDATE text_urls SET status = %s WHERE url = %s",
    ("failed", """$URL""")
)
conn.commit()
cursor.close()
conn.close()
print("Database updated to failed.")
PY
    exit 1
fi

python3 - <<PY
import os
import sys
import mysql.connector

sys.path.insert(0, os.environ["SLURM_SUBMIT_DIR"])

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

echo "Finished task $TASK_ID"