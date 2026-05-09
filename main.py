"""
AutoAttendance - Main Attendance System Application

Professional real-time face recognition attendance system with:
- InsightFace-based face detection and recognition
- Anti-spoofing liveness detection
- SQLite database for reliable data storage
- CSV and Excel export capabilities
- Email notifications for attendance and alerts

Usage:
    python main.py                 # Run attendance system
    python cli.py --help          # Show CLI options
"""

import cv2
import sys
import threading
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(__file__).rsplit("/", 1)[0] if "/" in __file__ else ".")

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from config import (
    CAMERA_ID,
    FPS,
    FRAME_PROCESS_INTERVAL,
    FRAME_WIDTH,
    FRAME_HEIGHT,
)
from face_recognition import FaceRecognitionModule
from anti_spoofing import AntiSpoofing
from attendance_manager import AttendanceManager
from database import AttendanceDatabase
from logger import get_logger, log_system_event

# Initialize logger
logger = get_logger()


class AttendanceSystem:
    """
    Main attendance system with real-time face recognition.
    
    Features:
    - Live camera feed with face detection
    - Real-time recognition with cosine distance scoring
    - Anti-spoofing for liveness detection
    - Automatic attendance marking
    - Excel and CSV export
    - Audio alerts for unknown persons
    """
    
    def __init__(self):
        """Initialize the attendance system."""
        logger.info("Initializing Attendance System")
        print("=" * 60)
        print("  AUTOATTENDANCE SYSTEM - Initializing...")
        print("=" * 60)
        
        # Initialize components
        self.recognizer = FaceRecognitionModule()
        self.anti_spoofing = AntiSpoofing()
        self.attendance_manager = AttendanceManager()
        self.db = AttendanceDatabase()
        
        # Load trained model
        logger.info("Loading face recognition model")
        self.recognizer.load_model()
        
        # System state
        self.running = False
        self.cap = None
        self.frame_count = 0
        
        # Statistics
        self.stats = {
            "faces_detected": 0,
            "faces_recognized": 0,
            "attendance_marked": 0,
            "spoof_attempts": 0,
        }
        
        print("✓ System initialized successfully!")
        logger.info("System initialized successfully")
    
    def initialize_camera(self) -> bool:
        """
        Initialize the camera capture device.
        
        Returns:
            bool: True if camera initialized successfully, False otherwise
        """
        logger.info(f"Initializing camera (ID: {CAMERA_ID})")
        self.cap = cv2.VideoCapture(CAMERA_ID)
        
        if not self.cap.isOpened():
            logger.error("Failed to open camera")
            print("✗ ERROR: Cannot open camera")
            print("  Try changing CAMERA_ID in config.py (0, 1, 2, 3...)")
            return False
        
        # Configure camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        
        # Verify settings
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        logger.info(f"Camera configured: {actual_width}x{actual_height}")
        print(f"✓ Camera initialized ({int(actual_width)}x{int(actual_height)})")
        return True
    
    def play_alert_sound(self) -> None:
        """Play alert sound in a separate thread."""
        def _play():
            try:
                if HAS_WINSOUND:
                    winsound.Beep(1000, 500)  # Frequency: 1000Hz, Duration: 500ms
            except Exception as e:
                logger.warning(f"Failed to play alert sound: {e}")
        
        thread = threading.Thread(target=_play, daemon=True)
        thread.start()
    
    def _draw_ui(self, frame: cv2.typing.MatLike, recognition_results: list) -> cv2.typing.MatLike:
        """
        Draw recognition results on the frame.
        
        Args:
            frame: Input video frame
            recognition_results: List of recognition results
            
        Returns:
            Annotated frame
        """
        for result in recognition_results:
            bbox = result.get("bbox", (0, 0, 0, 0))
            x, y, w, h = bbox
            face_crop = result.get("crop")
            
            if face_crop is None or face_crop.size == 0:
                continue
            
            # Anti-spoofing check
            is_real, spoof_score = self.anti_spoofing.analyze(face_crop)
            
            if is_real:
                # Real face detected
                self.stats["faces_detected"] += 1
                
                confidence = result.get("confidence", 0)
                is_known = result.get("is_known", False)
                
                if is_known:
                    # Known person
                    student_id = result.get("student_id", "Unknown")
                    name = result.get("name", "Unknown")
                    distance_text = f"dist: {confidence:.3f}"
                    
                    # Draw green box for recognized faces
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, name, (x, y - 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(frame, distance_text, (x, y + h + 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Mark attendance if processed frame
                    if self.frame_count % FRAME_PROCESS_INTERVAL == 0:
                        if self.attendance_manager.mark_attendance(student_id, name, confidence):
                            self.stats["attendance_marked"] += 1
                            self.stats["faces_recognized"] += 1
                            logger.info(f"Attendance marked: {name} (dist={confidence:.3f})")
                            cv2.putText(frame, "✓ PRESENT", (x + w - 100, y - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    # Unknown person - alert!
                    distance_text = f"dist: {confidence:.3f}"
                    
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 2)
                    cv2.putText(frame, "UNKNOWN", (x, y - 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
                    cv2.putText(frame, distance_text, (x, y + h + 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    
                    if self.frame_count % FRAME_PROCESS_INTERVAL == 0:
                        self.play_alert_sound()
                        cv2.putText(frame, "⚠ ALERT!", (x + w - 80, y - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        logger.warning(f"Unknown person detected (dist={confidence:.3f})")
            else:
                # Spoof attempt detected
                self.stats["spoof_attempts"] += 1
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "SPOOF!", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                logger.warning(f"Spoof attempt detected (score={spoof_score:.3f})")
                
                if self.frame_count % FRAME_PROCESS_INTERVAL == 0:
                    self.play_alert_sound()
        
        return frame
    
    def run(self) -> None:
        """
        Main system loop - runs until interrupted or 'q' pressed.
        """
        if not self.initialize_camera():
            return
        
        self.running = True
        last_results = []
        
        print("\n" + "=" * 60)
        print("  ATTENDANCE SYSTEM RUNNING")
        print("=" * 60)
        print("  Controls:")
        print("    'q' - Quit system")
        print("    's' - Export report")
        print("=" * 60 + "\n")
        
        logger.info("Attendance system started")
        log_system_event("info", "System started")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.error("Failed to read frame from camera")
                    print("✗ Error: Failed to read frame")
                    break
                
                self.frame_count += 1
                
                # Mirror frame for natural interaction
                frame = cv2.flip(frame, 1)
                
                # Process every N frames (performance optimization)
                should_process = self.frame_count % FRAME_PROCESS_INTERVAL == 0
                
                if should_process:
                    last_results = self.recognizer.recognize_frame(frame)
                
                # Draw UI elements
                frame = self._draw_ui(frame, last_results)
                
                # Draw status bar
                present_count = len(self.attendance_manager.daily_attendance)
                status_text = f"Present: {present_count} | Detected: {self.stats['faces_detected']}"
                cv2.putText(frame, status_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Show frame
                cv2.imshow("AutoAttendance System", frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    logger.info("Quit key pressed")
                    print("\nShutting down system...")
                    break
                elif key == ord('s'):
                    report_file = self.attendance_manager.export_daily_report()
                    print(f"\n✓ Report exported: {report_file}")
                    logger.info(f"Report exported: {report_file}")
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            print("\n\nInterrupted by user. Shutting down...")
        
        self.shutdown()
    
    def shutdown(self) -> None:
        """Clean up resources and export final report."""
        logger.info("System shutting down")
        
        self.running = False
        
        # Release camera
        if self.cap:
            self.cap.release()
            logger.info("Camera released")
        
        # Close all windows
        cv2.destroyAllWindows()
        logger.info("Windows closed")
        
        # Export final report
        report_file = self.attendance_manager.export_daily_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("  SYSTEM SHUTDOWN COMPLETE")
        print("=" * 60)
        print(f"  Final report: {report_file}")
        print(f"  Today's attendance: {len(self.attendance_manager.daily_attendance)}")
        print(f"  Faces detected: {self.stats['faces_detected']}")
        print(f"  Faces recognized: {self.stats['faces_recognized']}")
        print(f"  Attendance marked: {self.stats['attendance_marked']}")
        print(f"  Spoof attempts: {self.stats['spoof_attempts']}")
        print("=" * 60)
        
        log_system_event("info", "System stopped", **self.stats)


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  AUTOATTENDANCE - Face Recognition System")
    print("=" * 60 + "\n")
    
    try:
        system = AttendanceSystem()
        system.run()
    except Exception as e:
        logger.exception("Fatal error in main")
        print(f"\n✗ Fatal error: {e}")
        print("Check logs/attendance_[YYYYMM].log for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
