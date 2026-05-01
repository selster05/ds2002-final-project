# Data Divers — Project B: Gutenberg Text Pipeline

**Team:** Claudia Castagna, Ruixin Duan, Julie Wang, Sara Elster

A parallel text processing pipeline that downloads, processes, and stores 
Project Gutenberg books using UVA HPC (Slurm) and AWS MySQL.

---

## Pipeline Overview

| Step | Label | Where It Runs | What Happens |
|------|-------|---------------|--------------|
| 1 | Extract | Local | Build a `.txt` file of Gutenberg URLs |
| 2 | Register | Local → AWS DB | Insert new URLs into DB with `status = 'unprocessed'` |
| 3 | Query Work Queue | HPC login node | Query DB for unprocessed/failed URLs, write to input file |
| 4 | Download | Slurm array job | Download raw text, store path in DB |
| 5 | Transform | Slurm array job | Run `process_book.py`, extract metadata |
| 6 | Load | Slurm array job | Update DB with results path and `status = 'processed'` |

---

## Database Schema

**DB:** `library` | **Table:** `text_urls`

| Field | Type | Example |
|---|---|---|
| id | INT (PK, auto-increment) | 1 |
| url | TEXT | `https://www.gutenberg.org/cache/epub/78413/pg78413.txt` |
| status | VARCHAR(25) | `unprocessed`, `downloaded`, `processed`, `failed` |
| source | TEXT | `gutenberg.org` |
| storage_path | TEXT | `/standard/siller/ds2002/datadivers/downloads/pg78413.txt` |
| results_path | TEXT | `/standard/siller/ds2002/datadivers/results/pg78413_results.csv` |
| title | TEXT | `Pride and Prejudice` |
| author | TEXT | `Jane Austen` |

---

## How to Run

### 1. Register URLs
Add URLs to the database:
```bash
python3 scripts/register_urls.py path/to/urls.txt
```

### 2. Query the Work Queue (on HPC)
```bash
python3 scripts/query.py
```
This writes unprocessed and failed URLs to:
`/standard/siller/ds2002/datadivers/unprocessed_urls.txt`

### 3. Submit the Slurm Array Job (on HPC)
```bash
# Count the number of URLs
N=$(wc -l < /standard/siller/ds2002/datadivers/unprocessed_urls.txt)
```
```
# Submit
sbatch --array=1-$N scripts/htc_array.sh /standard/siller/ds2002/datadivers/unprocessed_urls.txt
```

### 4. Look Up Results for a URL
```
# Prints status, metadata, and (if processed) the top lemmas from the results CSV.
python3 scripts/query_results.py <url>
```

---

## Repository Structure

```
ds2002-final-project/
├── config/
│   └── db_config.py          # MySQL connection config (reads DB_USER / DB_PASSWORD env vars)
├── data/
│   └── urls.txt              # Input list of Project Gutenberg URLs
├── scripts/
│   ├── logs                  # Stores error and output logs for slurm jobs
│   ├── register_urls.py      # Registers URLs in the DB with status='unprocessed'
│   ├── query.py              # Writes unprocessed/failed URLs to a file on HPC
│   ├── htc_array.sh          # Slurm array job: download, process, update DB per URL
│   ├── download.py           # Downloads text + updates source/storage_path in DB
│   ├── process_book.py       # Tokenize + lemmatize + word count (NLTK)
│   ├── collect_metadata.py   # Extract title/author from Gutenberg header
│   └── query_results.py      # User-facing: look up results for a URL
├── Milestone1.pdf
├── LICENSE.md
├── README.md
└── requirements.txt          # mysql-connector-python, requests, nltk
```

## Error Handling

- If a download fails, the URL is marked `status = 'failed'` in the DB
- If `process_book.py` fails, the URL is marked `status = 'failed'`
- Failed URLs are **automatically retried** on the next run of `query.py`
- URLs already marked `processed` are always skipped

## Requirements

- Python 3
- `mysql-connector-python`
- UVA HPC access (Rivanna/Afton)
- AWS RDS MySQL instance


