# =========================================================
# database.py
# =========================================================

import sqlite3
import pandas as pd
from datetime import datetime
import os
import pytz

# =========================================================
# IST TIMEZONE
# =========================================================
IST = pytz.timezone("Asia/Kolkata")

# =========================================================
# DATABASE PATH
# =========================================================
DB_FOLDER = "database"

DB_FILE = os.path.join(
    DB_FOLDER,
    "nifty_oi.db"
)

os.makedirs(DB_FOLDER, exist_ok=True)

# =========================================================
# CREATE TABLE
# =========================================================
def initialize_database():

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS oi_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT,

            spot REAL,

            atm INTEGER,

            total_ce_oi REAL,

            total_pe_oi REAL,

            total_pcr REAL,

            index_name TEXT
        )
        """
    )

    conn.commit()

    conn.close()


# =========================================================
# SAVE SNAPSHOT
# =========================================================
def save_oi_snapshot(

    spot,
    atm,
    total_ce_oi,
    total_pe_oi,
    total_pcr,
    index_name,
):

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    # -----------------------------------------------------
    # IST TIMESTAMP
    # -----------------------------------------------------
    timestamp = datetime.now(IST).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute(
        """
        INSERT INTO oi_history (

            timestamp,
            spot,
            atm,
            total_ce_oi,
            total_pe_oi,
            total_pcr,
            index_name
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            spot,
            atm,
            total_ce_oi,
            total_pe_oi,
            total_pcr,
            index_name,
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# LOAD TODAY HISTORY
# =========================================================
def load_today_history(index_name):

    conn = sqlite3.connect(DB_FILE)

    today = datetime.now(IST).strftime(
        "%Y-%m-%d"
    )

    query = f"""

        SELECT *

        FROM oi_history

        WHERE date(timestamp) = '{today}'
        AND time(timestamp) >= '09:15:00'
        AND index_name = '{index_name}'

        ORDER BY timestamp
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df


# =========================================================
# LOAD FULL HISTORY
# =========================================================
def load_full_history(index_name):

    conn = sqlite3.connect(DB_FILE)

    query = f"""

        SELECT *

        FROM oi_history

        WHERE index_name = '{index_name}'

        ORDER BY timestamp
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df