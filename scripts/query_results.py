import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import DB_CONFIG
import mysql.connector


def query_results(url, top_n=10):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT url, status, storage_path, results_path, title, author
        FROM text_urls
        WHERE url = %s
        """,
        (url,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        print(f"Not registered: {url}")
        return 1

    print(f"URL:          {row['url']}")
    print(f"Status:       {row['status']}")
    print(f"Title:        {row.get('title') or '(unknown)'}")
    print(f"Author:       {row.get('author') or '(unknown)'}")
    print(f"Storage path: {row.get('storage_path') or '-'}")
    print(f"Results path: {row.get('results_path') or '-'}")

    if row["status"] != "processed":
        print(f"\nNot yet analyzed (status={row['status']}).")
        return 0

    results_path = row.get("results_path")
    if not results_path or not os.path.exists(results_path):
        print("\nResults file not found on disk.")
        return 0

    with open(results_path, encoding="utf-8") as f:
        header = f.readline()
        rows = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            word, count = line.rsplit(",", 1)
            rows.append((word, int(count)))

    total_tokens = sum(c for _, c in rows)
    print(f"\nUnique lemmas: {len(rows)}")
    print(f"Total tokens:  {total_tokens}")
    print(f"\nTop {top_n} lemmas:")
    for word, count in sorted(rows, key=lambda r: r[1], reverse=True)[:top_n]:
        print(f"  {word}: {count}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python query_results.py <url>", file=sys.stderr)
        sys.exit(1)
    sys.exit(query_results(sys.argv[1]))