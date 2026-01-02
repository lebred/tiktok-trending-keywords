#!/usr/bin/env python3
"""
Backup SQLite database to DigitalOcean Spaces or local file.

Usage:
    python -m scripts.backup_sqlite [--upload]
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import settings

def backup_to_file(db_path: str, backup_dir: str = "backups") -> str:
    """
    Backup SQLite database to a file.
    
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
    
    # Copy database file
    shutil.copy2(db_path, backup_path)
    
    print(f"Database backed up to: {backup_path}")
    return backup_path


def upload_to_spaces(backup_path: str, spaces_key: str, spaces_secret: str, 
                     spaces_endpoint: str, bucket_name: str) -> bool:
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
            's3',
            region_name='nyc3',  # Adjust to your region
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
    
    args = parser.parse_args()
    
    # Extract database path from URL if needed
    db_path = args.db_path
    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)
    
    # Create backup
    backup_path = backup_to_file(db_path)
    
    # Upload to Spaces if requested
    if args.upload:
        spaces_key = os.getenv("SPACES_ACCESS_KEY")
        spaces_secret = os.getenv("SPACES_SECRET_KEY")
        spaces_endpoint = os.getenv("SPACES_ENDPOINT", "https://nyc3.digitaloceanspaces.com")
        bucket_name = os.getenv("SPACES_BUCKET")
        
        if not all([spaces_key, spaces_secret, bucket_name]):
            print("Error: Spaces credentials not configured")
            print("Set SPACES_ACCESS_KEY, SPACES_SECRET_KEY, and SPACES_BUCKET")
            sys.exit(1)
        
        upload_to_spaces(backup_path, spaces_key, spaces_secret, spaces_endpoint, bucket_name)


if __name__ == "__main__":
    main()

