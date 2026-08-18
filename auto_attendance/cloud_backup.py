"""
Cloud Backup & Database Persistence Engine for AutoAttendance.
Automatically syncs SQLite database and biometric face samples to a private Hugging Face Dataset repository,
and auto-restores on system startup/rebuild.
"""

import os
import shutil
import zipfile
import threading
import logging
from datetime import datetime
from pathlib import Path

from auto_attendance.config import (
    BASE_DIR,
    MODELS_DIR,
    FACE_DATA_DIR,
    DATABASE_PATH,
)

logger = logging.getLogger("AutoAttendance.CloudBackup")

BACKUP_DIR = MODELS_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Default dataset repo for backups
DEFAULT_BACKUP_REPO = os.getenv("HF_BACKUP_REPO", "mahfuj735/AutoAttendance-Storage")

_last_sync_time = None
_sync_lock = threading.Lock()


def get_token() -> str:
    """Get Hugging Face Token from environment variable."""
    return os.getenv("HF_TOKEN", "")


def create_local_snapshot() -> Path:
    """Create a timestamped local snapshot of the SQLite database."""
    try:
        if not os.path.exists(DATABASE_PATH):
            return None
            
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = BACKUP_DIR / f"attendance_backup_{timestamp}.sqlite3"
        shutil.copy2(DATABASE_PATH, snapshot_path)
        
        # Keep only latest 10 snapshots
        snapshots = sorted(BACKUP_DIR.glob("attendance_backup_*.sqlite3"), key=os.path.getmtime)
        if len(snapshots) > 10:
            for old in snapshots[:-10]:
                try:
                    os.remove(old)
                except Exception:
                    pass
                    
        logger.info(f"Created local DB snapshot: {snapshot_path.name}")
        return snapshot_path
    except Exception as e:
        logger.error(f"Error creating local DB snapshot: {e}")
        return None


def export_full_archive(output_path: Path = None) -> Path:
    """Export complete archive (database + all face samples) into a single zip file."""
    try:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = BACKUP_DIR / f"full_system_backup_{timestamp}.zip"
            
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.exists(DATABASE_PATH):
                zf.write(DATABASE_PATH, arcname="attendance.sqlite3")
                
            if os.path.exists(FACE_DATA_DIR):
                for root, _, files in os.walk(FACE_DATA_DIR):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, FACE_DATA_DIR.parent)
                        zf.write(full_path, arcname=rel_path)
                        
        return output_path
    except Exception as e:
        logger.error(f"Error exporting full archive: {e}")
        return None


def import_full_archive(archive_path: Path) -> bool:
    """Import and restore full system archive (.sqlite3 or .zip)."""
    try:
        if not os.path.exists(archive_path):
            return False
            
        # Create a safety backup first
        create_local_snapshot()
        
        if str(archive_path).endswith(".sqlite3") or str(archive_path).endswith(".db"):
            shutil.copy2(archive_path, DATABASE_PATH)
            logger.info("Restored database from SQLite file.")
            return True
            
        if str(archive_path).endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                for member in zf.infolist():
                    if member.filename == "attendance.sqlite3":
                        zf.extract(member, path=MODELS_DIR)
                        extracted_db = MODELS_DIR / "attendance.sqlite3"
                        if extracted_db != Path(DATABASE_PATH):
                            shutil.move(extracted_db, DATABASE_PATH)
                    elif member.filename.startswith("faces/"):
                        zf.extract(member, path=FACE_DATA_DIR.parent)
            logger.info("Restored database and face samples from zip archive.")
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error importing full archive: {e}")
        return False


def sync_to_cloud(repo_id: str = None) -> bool:
    """Synchronize local database and face images to private Hugging Face Dataset repository."""
    global _last_sync_time
    token = get_token()
    if not token:
        logger.warning("No Hugging Face token available for cloud sync.")
        return False
        
    repo = repo_id or DEFAULT_BACKUP_REPO
    
    with _sync_lock:
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
            
            # Ensure backup dataset repository exists (private)
            try:
                api.create_repo(repo_id=repo, repo_type="dataset", private=True, exist_ok=True)
            except Exception as e:
                logger.debug(f"Repo create check: {e}")
                
            # Create local snapshot
            create_local_snapshot()
            
            # Upload attendance.sqlite3
            if os.path.exists(DATABASE_PATH):
                api.upload_file(
                    path_or_fileobj=str(DATABASE_PATH),
                    path_in_repo="attendance.sqlite3",
                    repo_id=repo,
                    repo_type="dataset",
                    commit_message=f"Auto-backup database {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
            # Zip and upload face samples
            if os.path.exists(FACE_DATA_DIR) and any(FACE_DATA_DIR.iterdir()):
                temp_faces_zip = BACKUP_DIR / "faces_backup_latest.zip"
                with zipfile.ZipFile(temp_faces_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(FACE_DATA_DIR):
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, FACE_DATA_DIR)
                            zf.write(full_path, arcname=rel_path)
                            
                api.upload_file(
                    path_or_fileobj=str(temp_faces_zip),
                    path_in_repo="faces_backup_latest.zip",
                    repo_id=repo,
                    repo_type="dataset",
                    commit_message=f"Auto-backup face samples {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                try:
                    os.remove(temp_faces_zip)
                except Exception:
                    pass
                    
            _last_sync_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Successfully synced database to cloud dataset: {repo}")
            return True
        except Exception as e:
            logger.error(f"Cloud sync error: {e}")
            return False


def sync_to_cloud_async():
    """Trigger cloud sync in a non-blocking background daemon thread."""
    thread = threading.Thread(target=sync_to_cloud, daemon=True)
    thread.start()


def restore_from_cloud(repo_id: str = None) -> bool:
    """Restore database and face samples from cloud repository on startup."""
    token = get_token()
    if not token:
        logger.info("No Hugging Face token configured; skipping cloud restore.")
        return False
        
    repo = repo_id or DEFAULT_BACKUP_REPO
    
    try:
        from huggingface_hub import HfApi, hf_hub_download
        api = HfApi(token=token)
        
        # Check if repo exists
        try:
            repo_info = api.repo_info(repo_id=repo, repo_type="dataset")
        except Exception:
            logger.info(f"Cloud backup repo {repo} does not exist yet. Will create on next write.")
            return False
            
        restored = False
        
        # Download and restore attendance.sqlite3
        try:
            cloud_db = hf_hub_download(repo_id=repo, filename="attendance.sqlite3", repo_type="dataset", token=token)
            if os.path.exists(cloud_db):
                # Only overwrite if cloud DB exists and has size
                if os.path.getsize(cloud_db) > 0:
                    shutil.copy2(cloud_db, DATABASE_PATH)
                    logger.info("Restored attendance.sqlite3 from cloud repository!")
                    restored = True
        except Exception as e:
            logger.debug(f"No cloud database file found: {e}")
            
        # Download and extract faces_backup_latest.zip
        try:
            cloud_faces = hf_hub_download(repo_id=repo, filename="faces_backup_latest.zip", repo_type="dataset", token=token)
            if os.path.exists(cloud_faces) and os.path.getsize(cloud_faces) > 0:
                FACE_DATA_DIR.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(cloud_faces, "r") as zf:
                    zf.extractall(path=FACE_DATA_DIR)
                logger.info("Restored face samples from cloud repository!")
                restored = True
        except Exception as e:
            logger.debug(f"No cloud faces archive found: {e}")
            
        return restored
    except Exception as e:
        logger.error(f"Error during cloud restore: {e}")
        return False


def get_backup_status() -> dict:
    """Get status of local snapshots and cloud persistence."""
    token = get_token()
    snapshots = list(BACKUP_DIR.glob("attendance_backup_*.sqlite3")) if BACKUP_DIR.exists() else []
    
    return {
        "cloud_sync_enabled": bool(token),
        "backup_repo": DEFAULT_BACKUP_REPO,
        "last_sync_time": _last_sync_time or "Never",
        "local_snapshots_count": len(snapshots),
        "local_snapshots": [s.name for s in sorted(snapshots, key=os.path.getmtime, reverse=True)[:5]]
    }
