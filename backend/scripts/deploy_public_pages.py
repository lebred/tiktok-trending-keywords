#!/usr/bin/env python3
"""
Deploy public pages with atomic swap to avoid partial updates.

Usage:
    python -m scripts.deploy_public_pages --source <TEMP_DIR> --target <PUBLIC_DIR> [--user <USER>]
"""

import sys
import os
import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging()


def deploy_public_pages(
    source_dir: str,
    target_dir: str,
    user: Optional[str] = None,
    group: Optional[str] = None,
) -> bool:
    """
    Deploy public pages using atomic swap.

    Process:
    1. Generate to temp directory (source_dir)
    2. Move current public -> public_prev (backup)
    3. Move temp -> public (atomic swap)
    4. Remove old backup (optional)

    Args:
        source_dir: Source directory (temp, newly generated)
        target_dir: Target directory (final public pages location)
        user: User to set ownership (optional)
        group: Group to set ownership (optional)

    Returns:
        True if successful, False otherwise
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    backup_path = Path(f"{target_dir}_prev")

    if not source_path.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return False

    if not source_path.is_dir():
        logger.error(f"Source is not a directory: {source_dir}")
        return False

    try:
        # Step 1: Backup current public directory if it exists
        if target_path.exists():
            logger.info(f"Backing up current public directory to: {backup_path}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.move(str(target_path), str(backup_path))

        # Step 2: Move temp directory to public (atomic swap)
        logger.info(f"Moving {source_dir} -> {target_dir}")
        shutil.move(str(source_path), str(target_path))

        # Step 3: Set ownership and permissions
        if user or group:
            logger.info(f"Setting ownership: user={user}, group={group}")
            try:
                # Build chown command
                ownership = user if user else ""
                if group:
                    ownership = f"{ownership}:{group}" if ownership else f":{group}"

                if ownership:
                    subprocess.run(
                        ["chown", "-R", ownership, str(target_path)],
                        check=True,
                    )
                    logger.info(f"Set ownership to {ownership}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to set ownership: {e}")
                # Non-fatal, continue

        # Set permissions (readable by web server)
        try:
            subprocess.run(["chmod", "-R", "755", str(target_path)], check=True)
            logger.info("Set permissions to 755")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to set permissions: {e}")

        # Step 4: Remove old backup (optional, but recommended)
        if backup_path.exists():
            logger.info(f"Removing old backup: {backup_path}")
            shutil.rmtree(backup_path)

        logger.info(f"Successfully deployed public pages to: {target_dir}")
        return True

    except Exception as e:
        logger.error(f"Error deploying public pages: {e}", exc_info=True)

        # Attempt to restore from backup if deployment failed
        if backup_path.exists() and not target_path.exists():
            logger.info("Attempting to restore from backup...")
            try:
                shutil.move(str(backup_path), str(target_path))
                logger.info("Restored from backup")
            except Exception as restore_error:
                logger.error(f"Failed to restore from backup: {restore_error}")

        return False


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy public pages with atomic swap")
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Source directory (temp, newly generated pages)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target directory (final public pages location)",
    )
    parser.add_argument(
        "--user",
        type=str,
        default=None,
        help="User to set ownership (e.g., www-data)",
    )
    parser.add_argument(
        "--group",
        type=str,
        default=None,
        help="Group to set ownership (e.g., www-data)",
    )

    args = parser.parse_args()

    # Determine target directory
    target_dir = args.target
    if target_dir is None:
        target_dir = getattr(settings, "public_pages_dir", "/var/www/trendearly/public")

    logger.info(f"Deploying public pages: {args.source} -> {target_dir}")

    success = deploy_public_pages(
        source_dir=args.source,
        target_dir=target_dir,
        user=args.user,
        group=args.group,
    )

    if not success:
        logger.error("Deployment failed")
        sys.exit(1)

    logger.info("Deployment completed successfully")


if __name__ == "__main__":
    main()
