#!/usr/bin/env python3
"""
Backup SQLite database to DigitalOcean Spaces or local file.

Uses SQLite's online backup API for safe, consistent backups even during writes.
Handles WAL mode correctly by checkpointing before backup.

Usage:
    python -m scripts.backup_sqlite [--upload]
"""

import sys
import os
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import settings


def backup_to_file(db_path: str, backup_dir: str = "backups") -> str:
    """
    Backup SQLite database using online backup API.

    This method is safe even if the database is being written to:
    - Uses SQLite's online backup API (sqlite3.backup())
    - Checkpoints WAL before backup if WAL mode is enabled
    - Verifies backup integrity

    Args:
        db_path: Path to SQLite database file
        backup_dir: Directory to store backups

    Returns:
        Path to backup file
    """
    # Create backup directory
    Path(backup_dir).mkdir(exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"tiktok_keywords_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Connect to source database
    source_conn = sqlite3.connect(db_path)

    try:
        # Checkpoint WAL if in WAL mode (ensures consistency)
        # This writes all WAL transactions to the main database
        source_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        # Create backup connection
        backup_conn = sqlite3.connect(backup_path)

        try:
            # Perform online backup
            # This is safe even if source is being written to
            source_conn.backup(backup_conn)

            # Verify backup integrity
            backup_conn.execute("PRAGMA integrity_check")

            print(f"Database backed up to: {backup_path}")

        finally:
            backup_conn.close()

    finally:
        source_conn.close()

    # Also copy WAL and SHM files if they exist (for complete backup)
    # Note: These are only needed if you want to restore to exact state
    # For daily backups, the checkpointed main file is usually sufficient
    wal_path = db_path + "-wal"
    shm_path = db_path + "-shm"

    if os.path.exists(wal_path):
        shutil.copy2(wal_path, backup_path + "-wal")
        print(f"WAL file backed up: {backup_path}-wal")

    if os.path.exists(shm_path):
        shutil.copy2(shm_path, backup_path + "-shm")
        print(f"SHM file backed up: {backup_path}-shm")

    return backup_path


def upload_to_spaces(
    backup_path: str,
    spaces_key: str,
    spaces_secret: str,
    spaces_endpoint: str,
    bucket_name: str,
) -> bool:
    """
    Upload backup to DigitalOcean Spaces.

    Requires boto3 library (install with: pip install boto3)
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("boto3 not installed. Install with: pip install boto3")
        return False

    try:
        # Create S3 client for Spaces
        session = boto3.session.Session()
        client = session.client(
            "s3",
            region_name="nyc3",  # Adjust to your region
            endpoint_url=spaces_endpoint,
            aws_access_key_id=spaces_key,
            aws_secret_access_key=spaces_secret,
        )

        # Upload file
        backup_filename = os.path.basename(backup_path)
        client.upload_file(backup_path, bucket_name, backup_filename)

        print(f"Backup uploaded to Spaces: s3://{bucket_name}/{backup_filename}")
        return True

    except ClientError as e:
        print(f"Error uploading to Spaces: {e}")
        return False


def verify_backup(backup_path: str) -> bool:
    """
    Verify backup integrity by opening and running a simple query.

    Args:
        backup_path: Path to backup file

    Returns:
        True if backup is valid, False otherwise
    """
    try:
        conn = sqlite3.connect(backup_path)
        try:
            # Run integrity check
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result and result[0] == "ok":
                # Try a simple query
                conn.execute("SELECT 1").fetchone()
                return True
            else:
                print(f"Integrity check failed: {result}")
                return False
        finally:
            conn.close()
    except Exception as e:
        print(f"Error verifying backup: {e}")
        return False


def main():
    """Main backup function."""
    parser = argparse.ArgumentParser(description="Backup SQLite database")
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload backup to DigitalOcean Spaces",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data.db",
        help="Path to SQLite database file",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip backup verification (not recommended)",
    )

    args = parser.parse_args()

    # Extract database path from URL if needed
    db_path = args.db_path
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)

    # Create backup using SQLite online backup API
    print(f"Creating backup of {db_path}...")
    backup_path = backup_to_file(db_path)

    # Verify backup integrity
    if not args.skip_verify:
        print("Verifying backup integrity...")
        if not verify_backup(backup_path):
            print("ERROR: Backup verification failed!")
            os.remove(backup_path)
            sys.exit(1)
        print("Backup verified successfully")

    # Upload to Spaces if requested
    if args.upload:
        spaces_key = os.getenv("SPACES_ACCESS_KEY")
        spaces_secret = os.getenv("SPACES_SECRET_KEY")
        spaces_endpoint = os.getenv(
            "SPACES_ENDPOINT", "https://nyc3.digitaloceanspaces.com"
        )
        bucket_name = os.getenv("SPACES_BUCKET")

        if not all([spaces_key, spaces_secret, bucket_name]):
            print("Error: Spaces credentials not configured")
            print("Set SPACES_ACCESS_KEY, SPACES_SECRET_KEY, and SPACES_BUCKET")
            sys.exit(1)

        print("Uploading backup to Spaces...")
        if upload_to_spaces(
            backup_path, spaces_key, spaces_secret, spaces_endpoint, bucket_name
        ):
            print("Backup completed successfully!")
        else:
            print("Warning: Backup created but upload failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
