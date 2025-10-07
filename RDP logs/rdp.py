#!/usr/bin/env python3
"""
rdp_csv_to_mysql.py  –  ZERO‑ARG RDP loader
• Expects CSV in the same directory, default name rdp_dataset.csv
• Validates required columns
• Prints preview
• Inserts into MySQL
"""

import os, sys, pandas as pd, mysql.connector as mc
from datetime import datetime
from pathlib import Path

# ─── CONFIG ────────────────────────────────────────────────────────────────
CSV_FILE      = "rdp_dataset.csv"      # change if your filename differs
MYSQL         = dict(host="localhost", user="root", password="rootroot")
DB_NAME       = "siem"
TABLE         = "rdp_events"
REQUIRED_COLS = {
    "session_id", "username", "remote_address",
    "remote_port", "status", "timestamp",
}
# ───────────────────────────────────────────────────────────────────────────

def load_csv(csv_path: Path) -> pd.DataFrame:
    print(f"🔍 Reading CSV → {csv_path.resolve()}")
    if not csv_path.exists():
        sys.exit(f"[FATAL] File not found: {csv_path}")
    df = pd.read_csv(csv_path)
    df.columns = [c.lower() for c in df.columns]

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        sys.exit(f"[FATAL] Missing columns: {missing}")

    df["remote_port"] = df["remote_port"].astype(int)
    df["timestamp"]   = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().any():
        bad = df[df["timestamp"].isna()].head()
        sys.exit(f"[FATAL] Un‑parsable timestamp(s):\n{bad}")

    print("\n📑 Preview (first 3 rows):")
    print(df.head(3).to_string(index=False))
    print(f"… total rows = {len(df)}\n")
    return df[list(REQUIRED_COLS)]

def ensure_schema():
    conn = mc.connect(**MYSQL)
    cur  = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    conn.database = DB_NAME
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS `{TABLE}` (
          id              BIGINT AUTO_INCREMENT PRIMARY KEY,
          session_id      VARCHAR(60),
          username        VARCHAR(100),
          remote_address  VARCHAR(45),
          remote_port     SMALLINT UNSIGNED,
          status          VARCHAR(30),
          ts              DATETIME
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    conn.commit(); cur.close(); conn.close()
    print("🛠️  Database & table ready.\n")

def insert_rows(df: pd.DataFrame):
    conn = mc.connect(database=DB_NAME, **MYSQL)
    cur  = conn.cursor()
    sql  = (f"INSERT INTO `{TABLE}` "
            "(session_id, username, remote_address, remote_port, status, ts) "
            "VALUES (%s,%s,%s,%s,%s,%s)")
    batch = [
        (
            r.session_id, r.username, r.remote_address,
            int(r.remote_port), r.status, r.timestamp.to_pydatetime()
        )
        for r in df.itertuples(index=False)
    ]
    print("🚀 Inserting rows …")
    cur.executemany(sql, batch)
    conn.commit()
    print(f"✅ {cur.rowcount} rows inserted into {DB_NAME}.{TABLE}")
    cur.close(); conn.close()

if __name__ == "__main__":
    csv_path = Path(__file__).with_name(CSV_FILE)   # same folder as script
    df = load_csv(csv_path)
    ensure_schema()
    insert_rows(df)
