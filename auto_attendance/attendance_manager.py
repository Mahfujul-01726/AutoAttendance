"""
Attendance Manager Module
Handles attendance tracking, storage, and export functionality.
"""

import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd

from .config import (
    ATTENDANCE_DIR,
    DATABASE_PATH,
    EXCEL_FILE,
    LOG_FILE,
)
from .database import AttendanceDatabase

logger = logging.getLogger(__name__)


class AttendanceManager:
    """
    Manages attendance records with SQLite persistence, Excel export, and logging.
    
    Features:
    - Duplicate prevention within session and across restarts
    - Real-time Excel updates
    - Structured log file output
    - CSV export capability
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the attendance manager.
        
        Args:
            db_path: Optional custom path to SQLite database
        """
        # Ensure directories exist
        ATTENDANCE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.db = AttendanceDatabase(db_path or str(DATABASE_PATH))
        self.daily_attendance = self._load_today_attendance()
        
        logger.info(
            f"AttendanceManager initialized with {len(self.daily_attendance)} "
            f"records for today ({datetime.now().strftime('%Y-%m-%d')})"
        )
    
    def mark_attendance(
        self,
        student_id: int,
        student_name: str,
        confidence: float
    ) -> bool:
        """
        Mark a student as present if not already marked today.
        
        Args:
            student_id: Unique student identifier
            student_name: Student's display name
            confidence: Recognition confidence score (0-1)
            
        Returns:
            True if marked successfully, False if duplicate or error
        """
        try:
            # Prevent duplicates within session and across restarts
            if student_name in self.daily_attendance:
                logger.debug(f"Duplicate attendance skip: {student_name}")
                return False
            
            timestamp = datetime.now()
            
            # Store in SQLite database
            inserted = self.db.mark_attendance(student_id, student_name, confidence)
            if not inserted:
                logger.warning(f"Failed to insert attendance for {student_name}")
                return False
            
            # Update in-memory cache
            self.daily_attendance[student_name] = {
                'id': student_id,
                'time': timestamp.strftime('%H:%M:%S'),
                'date': timestamp.strftime('%Y-%m-%d'),
                'confidence': confidence,
                'status': 'Present'
            }
            
            # Persist to files
            self._log_attendance(student_name, timestamp, confidence)
            self._update_excel(student_name, timestamp, confidence)
            
            logger.info(
                f"Attendance marked: {student_name} (ID: {student_id}, "
                f"Confidence: {confidence:.2%})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error marking attendance: {e}", exc_info=True)
            return False
    
    def _log_attendance(self, name: str, timestamp: datetime, confidence: float) -> None:
        """Log attendance to structured text file."""
        try:
            log_entry = (
                f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{name} | "
                f"Confidence: {confidence:.4f}\n"
            )
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write attendance log: {e}")
    
    def _update_excel(self, name: str, timestamp: datetime, confidence: float) -> None:
        """Update Excel attendance sheet with new record."""
        try:
            # Load existing or create new DataFrame
            if EXCEL_FILE.exists():
                df = pd.read_excel(EXCEL_FILE)
            else:
                df = pd.DataFrame(columns=[
                    'ID', 'Date', 'Name', 'Time', 'Confidence', 'Status'
                ])
            
            # Append new record
            new_record = {
                'ID': len(df) + 1,
                'Date': timestamp.strftime('%Y-%m-%d'),
                'Name': name,
                'Time': timestamp.strftime('%H:%M:%S'),
                'Confidence': f"{confidence:.4f}",
                'Status': 'Present'
            }
            
            df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
            
        except Exception as e:
            logger.error(f"Failed to update Excel: {e}")
    
    def get_attendance_summary(self) -> dict:
        """
        Get today's attendance summary.
        
        Returns:
            Dictionary mapping student names to their attendance records
        """
        return self.daily_attendance.copy()
    
    def get_marked_count(self) -> int:
        """Return the count of marked attendance today."""
        return len(self.daily_attendance)
    
    def export_daily_report(self, filename: Optional[str] = None) -> str:
        """
        Export today's attendance to CSV file.
        
        Args:
            filename: Custom filename (defaults to attendance_YYYY-MM-DD.csv)
            
        Returns:
            Path to the exported CSV file
        """
        if filename is None:
            filename = f"attendance_{datetime.now().strftime('%Y-%m-%d')}.csv"
        
        today = datetime.now().strftime('%Y-%m-%d')
        records = self.db.list_attendance(date=today, limit=10000)
        
        df = pd.DataFrame(records)
        csv_path = ATTENDANCE_DIR / filename
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        logger.info(f"Exported {len(df)} records to {csv_path}")
        return str(csv_path)
    
    def export_to_excel(self, filename: Optional[str] = None) -> str:
        """
        Export all attendance records to Excel file.
        
        Args:
            filename: Custom filename (defaults to attendance_all.xlsx)
            
        Returns:
            Path to the exported Excel file
        """
        if filename is None:
            filename = "attendance_all.xlsx"
        
        records = self.db.list_attendance(limit=100000)
        df = pd.DataFrame(records)
        
        excel_path = ATTENDANCE_DIR / filename
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        logger.info(f"Exported {len(df)} records to {excel_path}")
        return str(excel_path)
    
    def _load_today_attendance(self) -> dict:
        """
        Load today's records from SQLite to prevent double-counting on restart.
        
        Returns:
            Dictionary mapping student names to their attendance records
        """
        today = datetime.now().strftime('%Y-%m-%d')
        records = self.db.list_attendance(date=today, limit=10000)
        
        attendance = {}
        for record in records:
            attendance[record['student_name']] = {
                'id': record['student_id'],
                'time': record['time'],
                'date': record['date'],
                'confidence': record['confidence'],
                'status': record['status']
            }
        
        return attendance
    
    def clear_today(self) -> int:
        """
        Clear today's attendance records (admin function).
        
        Returns:
            Number of records deleted
        """
        count = self.db.clear_attendance(date=datetime.now().strftime('%Y-%m-%d'))
        self.daily_attendance.clear()
        logger.warning(f"Cleared {count} attendance records for today")
        return count
