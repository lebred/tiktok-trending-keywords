"""
APScheduler configuration for daily automation.

Sets up scheduled jobs to run the daily pipeline automatically.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from app.services.daily_pipeline import run_daily_pipeline
from app.config import settings

logger = logging.getLogger(__name__)


def create_scheduler() -> BackgroundScheduler:
    """
    Create and configure the APScheduler instance.

    Returns:
        Configured BackgroundScheduler
    """
    jobstores = {"default": MemoryJobStore()}
    executors = {"default": ThreadPoolExecutor(2)}
    job_defaults = {
        "coalesce": True,  # Combine multiple pending executions
        "max_instances": 1,  # Only one instance running at a time
        "misfire_grace_time": 3600,  # 1 hour grace period for missed jobs
    }

    scheduler = BackgroundScheduler(
        jobstores=jobstores, executors=executors, job_defaults=job_defaults
    )

    # Schedule daily pipeline to run at 2 AM UTC
    scheduler.add_job(
        func=run_daily_pipeline_job,
        trigger=CronTrigger(hour=2, minute=0),  # 2 AM UTC daily
        id="daily_pipeline",
        name="Daily TikTok Keyword Pipeline",
        replace_existing=True,
    )

    logger.info("Scheduler configured: Daily pipeline scheduled for 2 AM UTC")

    return scheduler


def run_daily_pipeline_job():
    """
    Job function to run the daily pipeline.

    This function is called by the scheduler.
    """
    logger.info("Starting scheduled daily pipeline job")
    try:
        results = run_daily_pipeline()
        if results.get("success"):
            logger.info(
                f"Daily pipeline completed successfully: "
                f"{results['scores_calculated']} scores calculated"
            )
        else:
            logger.warning(
                f"Daily pipeline completed with errors: {len(results.get('errors', []))} errors"
            )
    except Exception as e:
        logger.error(f"Error in scheduled daily pipeline job: {e}", exc_info=True)


def start_scheduler():
    """Start the scheduler."""
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler


if __name__ == "__main__":
    # For testing: run scheduler in foreground
    logging.basicConfig(level=logging.INFO)
    scheduler = start_scheduler()

    try:
        # Keep the script running
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.shutdown()

