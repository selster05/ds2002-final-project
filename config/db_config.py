import os

DB_CONFIG = {
    "host": "ds2002.cgls84scuy1e.us-east-1.rds.amazonaws.com",
    "port": 3306,
    "database": "library",
    "user": os.environ.get("DB_USER", "data_divers"),
    "password": os.environ.get("DB_PASSWORD", "data_divers"),
}