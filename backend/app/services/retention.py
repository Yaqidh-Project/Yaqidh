import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger(__name__)


async def prune_old_clips(settings):
    clips_dir = Path(settings.CLIPS_DIR)

    if not clips_dir.exists():
        logger.debug(f"Clips directory {clips_dir} does not exist — skipping pruning")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.CLIP_RETENTION_DAYS)
    deleted = 0
    errors = 0

    for clip_path in clips_dir.rglob("*"):
        if not clip_path.is_file():
            continue
        try:
            stat = clip_path.stat()

            if hasattr(stat, "st_birthtime"):
                ctime = stat.st_birthtime
            else:
                logger.debug("st_birthtime unavailable — falling back to st_ctime (Linux inode change time)")
                ctime = stat.st_ctime
            created_time = datetime.fromtimestamp(ctime, tz=timezone.utc)

            if created_time < cutoff:
                clip_path.unlink()
                logger.info(f"Pruned clip: {clip_path} (created {created_time.isoformat()})")
                deleted += 1
        except Exception as e:
            logger.error(f"Error pruning {clip_path}: {e}")
            errors += 1

    # cleanup empty directories
    for dir_path in sorted(clips_dir.rglob("*"), reverse=True):
        if dir_path.is_dir():
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
            except Exception:
                pass

    logger.info(f"Retention pruning complete — deleted {deleted} clips, {errors} errors")


async def retention_loop():
    settings = get_settings()
    interval_seconds = getattr(settings, "CLIP_RETENTION_CHECK_INTERVAL", 86400)

    # startup delay
    await asyncio.sleep(5)

    while True:
        try:
            await prune_old_clips(settings)
        except Exception as e:
            logger.error(f"Retention loop error: {e}")
        await asyncio.sleep(interval_seconds)