#!/usr/bin/env python3
"""
Database migration runner
Auto-discovers and applies SQL migrations in numeric order
Migrations should be named: NNN_description.sql (e.g., 001_create_tables.sql)
"""
import logging
import glob
import os
import re
import psycopg2
from config.config import DB_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_migration_files(sql_dir="tmp/sql"):
    """
    Auto-discover NNN_*.sql files in sql_dir (sorted by numeric prefix)
    Returns sorted list of migration file paths (excluding subdirectories)
    """
    files = glob.glob(os.path.join(sql_dir, "[0-9][0-9][0-9]_*.sql"))
    if not files:
        logger.warning(f"No migration files found in {sql_dir}")
        return []

    # Sort by numeric prefix (e.g., 001, 002, 003, ...)
    def extract_number(filepath):
        match = re.match(r"(\d+)_", os.path.basename(filepath))
        return int(match.group(1)) if match else float('inf')

    return sorted(files, key=extract_number)

def run_migration(migration_file):
    """Run a single migration file"""
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        conn = psycopg2.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )

        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()

        conn.close()
        logger.info(f"✓ Migration applied: {os.path.basename(migration_file)}")
        return True
    except Exception as e:
        logger.error(f"✗ Migration failed ({os.path.basename(migration_file)}): {e}")
        return False

if __name__ == "__main__":
    migrations = get_migration_files()
    if not migrations:
        logger.error("No migrations found")
        exit(1)

    logger.info(f"Found {len(migrations)} migration(s)")
    failed = False

    for migration_file in migrations:
        if not run_migration(migration_file):
            failed = True
            # Continue with next migration even if one fails

    if failed:
        logger.error("Some migrations failed")
        exit(1)
    else:
        logger.info(f"✓ All {len(migrations)} migration(s) applied successfully")
        exit(0)
