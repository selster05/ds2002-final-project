# Milestone 1

**Team name:** Data Divers  
**Team members:** Claudia Castagna, Ruixin Duan, Julie Wang, Sara Elster  
**Project:** B (HTC Text Analyzer)

## A) Data Structures

### 1) Input file types and sources

| Input | Format | Source | Example |
|---|---|---|---|
| URLs to plain text files | txt | Project Gutenberg | `https://www.gutenberg.org/cache/epub/78413/pg78413.txt` |
| Database host | String | Hardcoded in `config/db_config.py` | `ds2002.cgls84scuy1e.us-east-1.rds.amazonaws.com` |
| Database name | String | Hardcoded in `config/db_config.py` | `library` |
| Database table | String | Hardcoded in scripts | `text_urls` |
| DB username | Env variable `DB_USER` | User input / environment | `data_divers` |
| DB password | Env variable `DB_PASSWORD` | User input / environment | `data_divers` |
| Output / storage directory | String | HPC shared dir | `/standard/siller/ds2002/datadivers/` |

The registered URL list lives in `data/urls.txt` and currently contains 5 Project Gutenberg books (e.g. *Pride and Prejudice*, *Alice in Wonderland*, *Frankenstein*, *Sherlock Holmes*).

### 2) Database schema

Database hosted with MySQL on AWS RDS.  
- **db:** `library`  
- **table:** `text_urls`

| Field | Type | Example |
|---|---|---|
| id | INT (PK, auto-increment) | 1 |
| url | TEXT | `https://www.gutenberg.org/cache/epub/78413/pg78413.txt` |
| status | VARCHAR(25) | `unprocessed`, `downloaded`, `processed`, `failed` |
| source | TEXT | `gutenberg.org` |
| storage_path | TEXT | `/standard/siller/ds2002/datadivers/pg78413.txt` |
| results_path | TEXT | `/standard/siller/ds2002/datadivers/pg78413_results.csv` |
| title | TEXT | `Pride and Prejudice` |
| author | TEXT | `Jane Austen` |

### 3) Output files / results format

The `process_book.py` script writes a CSV file (`word,count`) containing the count of each lemmatized word in the text. Console output reports the total number of tokens and unique lemmatized words.

## B) Pipeline / Workflow

| Step | Label | Compute | Storage | Database | What happens |
|---|---|---|---|---|---|
| 1 | Extract | Personal Computer | Local (`data/urls.txt`) | — | Save list of text URLs into a plaintext input file. |
| 2 | Register | Personal Computer | Local | SQL Database (AWS) | `scripts/register.py` reads the URL file and checks each URL against the DB. If absent, inserts a new row with `status='unprocessed'`. |
| 3 | Query Work Queue | UVA HPC (login node) | Shared HPC dir | SQL Database (AWS) | `scripts/query_queue.py` queries the DB for URLs where `status='unprocessed'` and writes them to `unprocessed_urls.txt` for the Slurm job array. |
| 4 | Download | UVA HPC (Slurm array) | Shared HPC dir | SQL Database (AWS) | `scripts/download.py` downloads the raw text from each URL with `requests`, saves it to the shared directory, extracts the source domain, and records the storage path / source / status=`downloaded` in the DB. |
| 5 | Transform / Process | UVA HPC (Slurm array) | Shared HPC dir | SQL Database (AWS) | `scripts/process_book.py` (adapted from Lab 07) tokenizes, POS-tags, and lemmatizes the text using NLTK (`WordNetLemmatizer`), then writes word counts to a CSV results file. `scripts/collect_metadata.py` extracts title and author from the Gutenberg header. |
| 6 | Load / Update Status | UVA HPC (Slurm array) | Shared HPC dir | SQL Database (AWS) | Update the DB entry with `status='processed'`, results_path, title, and author. If a job fails, set `status='failed'`. |
| 7 | Query Results | Personal Computer / HPC | — | SQL Database (AWS) | A user-facing query script lets users check whether a URL has been analyzed and, if so, returns the analysis results path / summary. |

## C) Repository Structure

```
ds2002-final-project/
├── config/
│   └── db_config.py          # MySQL connection config (reads DB_USER / DB_PASSWORD env vars)
├── data/
│   └── urls.txt              # Input list of Project Gutenberg URLs
├── scripts/
│   ├── register.py           # Registers URLs in the DB with status='unprocessed'
│   ├── query_queue.py        # Writes unprocessed URLs to a file on HPC
│   ├── download.py           # Downloads text + updates source/storage_path in DB
│   ├── process_book.py       # Tokenize + lemmatize + word count (NLTK)
│   └── collect_metadata.py   # Extract title/author from Gutenberg header
├── DS2002 Final Ml1.pdf
├── Milestone1.md             # This file
├── LICENSE.md
├── README.md
└── requirements.txt          # mysql-connector-python, requests, nltk
```

## D) Environment / Requirements

Python packages (see `requirements.txt`):

- `mysql-connector-python` – MySQL access from `register.py`, `query_queue.py`, `download.py`
- `requests` – HTTP downloads in `download.py`
- `nltk` – tokenization, POS tagging, and lemmatization in `process_book.py` (uses `wordnet`, `omw-1.4`, `averaged_perceptron_tagger_eng`)

Environment variables required at runtime:

- `DB_USER` – MySQL username (defaults to `data_divers`)
- `DB_PASSWORD` – MySQL password (defaults to `data_divers`)

## E) Status of Implementation

- [x] URL input file (`data/urls.txt`) created.
- [x] DB config + connection (`config/db_config.py`) implemented.
- [x] Registration script (`scripts/register.py`) implemented.
- [x] Query / queue script (`scripts/query_queue.py`) implemented.
- [x] Download script (`scripts/download.py`) implemented; updates `storage_path` and `source`.
- [x] Text processing script (`scripts/process_book.py`) implemented (tokenization + lemmatization + counts).
- [x] Metadata extractor (`scripts/collect_metadata.py`) implemented.
- [ ] Slurm job array script wiring all of the above.
- [ ] User-facing DB query script that returns analysis results for a given URL.
- [ ] End-to-end run on UVA HPC.
