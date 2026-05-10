"""
Modern Web UI for AutoAttendance System
Professional and user-friendly web interface for face recognition attendance.
Designed for non-technical users with intuitive navigation and clear workflows.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import cv2
import numpy as np

from database import AttendanceDatabase
from face_recognition import FaceRecognitionModule
from anti_spoofing import AntiSpoofing
from attendance_manager import AttendanceManager
from data_collection import DataCollectionModule
from config import (
    CAMERA_ID, FACE_DATA_DIR, ATTENDANCE_DIR, 
    FRAME_WIDTH, FRAME_HEIGHT, FPS, DATABASE_PATH
)
from logger import get_logger

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = str(FACE_DATA_DIR)

logger = get_logger()

# Global system state
system_state = {
    'is_running': False,
    'mode': None,  # 'attendance', 'collection', None
    'current_person': None,
    'total_frames': 0,
    'collected_samples': 0,
    'camera_thread': None,
    'camera_running': False,
    'recognized_faces_count': 0,  # Track faces recognized in current session
}

# Global camera variables
camera = None
frame_buffer = None
frame_lock = threading.Lock()

# Initialize system components
db = AttendanceDatabase()
recognizer = FaceRecognitionModule()
anti_spoofing = AntiSpoofing()
attendance_manager = AttendanceManager()

# Load model on startup
try:
    recognizer.load_model()
    if recognizer.label_count == 0:
        logger.warning("No face embeddings loaded! Run: python train_model.py")
    else:
        logger.info(f"Loaded {recognizer.label_count} registered faces")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    logger.error("Face recognition will not work. Check embeddings with: python train_model.py")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_dashboard_stats():
    """Get statistics for dashboard."""
    try:
        total_persons = len(db.list_students())
        total_embeddings = db.get_total_embeddings()
        today = datetime.now().strftime('%Y-%m-%d')
        present_today = db.get_attendance_by_date(today)
        
        return {
            'total_persons': total_persons,
            'total_embeddings': total_embeddings,
            'present_today': len(present_today) if present_today else 0,
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {'total_persons': 0, 'total_embeddings': 0, 'present_today': 0}


def get_attendance_records(days=7):
    """Get recent attendance records."""
    try:
        records = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            attendance_list = db.get_attendance_by_date(date)
            if attendance_list:
                for record in attendance_list:
                    records.append({
                        'name': record[0],
                        'date': date,
                        'time': record[1],
                        'distance': f"{record[2]:.3f}" if len(record) > 2 else "N/A",
                    })
        return sorted(records, key=lambda x: x['date'], reverse=True)[:50]
    except Exception as e:
        logger.error(f"Error getting attendance records: {e}")
        return []


def get_person_list():
    """Get list of all registered persons."""
    try:
        persons = []
        if FACE_DATA_DIR.exists():
            for person_dir in FACE_DATA_DIR.iterdir():
                if person_dir.is_dir():
                    face_files = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
                    persons.append({
                        'name': person_dir.name,
                        'samples': len(face_files),
                    })
        return sorted(persons, key=lambda x: x['name'])
    except Exception as e:
        logger.error(f"Error getting person list: {e}")
        return []


def camera_worker():
    """Background thread for camera processing."""
    global camera, frame_buffer
    
    try:
        camera = cv2.VideoCapture(CAMERA_ID)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        camera.set(cv2.CAP_PROP_FPS, FPS)
        
        if not camera.isOpened():
            logger.error("Could not open camera")
            return
        
        logger.info(f"Camera opened successfully: {CAMERA_ID}")
        system_state['camera_running'] = True
        
        recognized_people = {}  # Track people recognized in this session
        
        while system_state['camera_running']:
            ret, frame = camera.read()
            if not ret:
                logger.error("Failed to read frame from camera")
                break
            
            try:
                # Flip frame for mirror effect
                frame = cv2.flip(frame, 1)
                system_state['total_frames'] += 1
                
                # Process frame based on mode
                if system_state['mode'] == 'attendance':
                    # Detect and recognize faces using the built-in method
                    results = recognizer.recognize_frame(frame)
                    
                    if not results:
                        # No faces detected - this is normal, just continue
                        pass
                    
                    for result in results:
                        x1, y1 = result['bbox'][0], result['bbox'][1]
                        w, h = result['bbox'][2], result['bbox'][3]
                        x2, y2 = x1 + w, y1 + h
                        
                        # Ensure bbox is within frame bounds
                        y1 = max(0, y1)
                        x1 = max(0, x1)
                        y2 = min(frame.shape[0], y2)
                        x2 = min(frame.shape[1], x2)
                        
                        # Check anti-spoofing on the face crop
                        face_crop = frame[y1:y2, x1:x2]
                        if face_crop.size > 0:  # Ensure crop is not empty
                            is_real, spoof_score = anti_spoofing.analyze(face_crop)
                        else:
                            is_real = False
                        
                        if not is_real:
                            # Spoofing detected - draw orange box
                            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 165, 255), 2)
                            cv2.putText(frame, "SPOOF", (int(x1), int(y1) - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                        elif result['is_known']:
                            # Known person - draw green box
                            person_name = result['name']
                            
                            # Mark attendance only once per session
                            if person_name not in recognized_people:
                                db.mark_attendance(
                                    None, 
                                    person_name, 
                                    result.get('confidence', 0),
                                    CAMERA_ID,
                                    'Present'
                                )
                                recognized_people[person_name] = True
                                system_state['recognized_faces_count'] += 1  # Update counter
                                logger.info(f"Marked attendance for {person_name}")
                            
                            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                            cv2.putText(frame, f"{person_name}", (int(x1), int(y1) - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        else:
                            # Unknown person - draw red box
                            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                            cv2.putText(frame, "Unknown", (int(x1), int(y1) - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                elif system_state['mode'] == 'collection':
                    # Face collection mode
                    faces = recognizer.detect_faces(frame)
                    for face in faces:
                        # Convert InsightFace face object to bbox coordinates
                        x1, y1, x2, y2 = recognizer._bbox_to_int(face.bbox, frame.shape)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Update frame buffer
                with frame_lock:
                    frame_buffer = frame.copy()
                    
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                continue
        
        logger.info("Camera worker thread stopped")
        
    except Exception as e:
        logger.error(f"Camera worker error: {e}")
    finally:
        if camera is not None:
            camera.release()
            logger.info("Camera released")
        system_state['camera_running'] = False


def generate_frames():
    """Generator for streaming video frames."""
    while system_state['camera_running']:
        with frame_lock:
            if frame_buffer is not None:
                ret, jpeg = cv2.imencode('.jpg', frame_buffer)
                if ret:
                    frame_bytes = jpeg.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                           + frame_bytes + b'\r\n')
        
        # Small delay to avoid overwhelming the client
        import time
        time.sleep(0.033)  # ~30 FPS


# ============================================================================
# ROUTES - MAIN PAGES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard."""
    stats = get_dashboard_stats()
    now = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', stats=stats, now=now)


@app.route('/register')
def register():
    """Register new person page."""
    persons = get_person_list()
    return render_template('register.html', persons=persons)


@app.route('/attendance')
def attendance():
    """View attendance records."""
    records = get_attendance_records(30)
    return render_template('attendance.html', records=records)


@app.route('/settings')
def settings():
    """Settings page."""
    persons = get_person_list()
    return render_template('settings.html', persons=persons)


# ============================================================================
# API ENDPOINTS - DASHBOARD
# ============================================================================

@app.route('/api/stats')
def api_stats():
    """Get dashboard statistics."""
    stats = get_dashboard_stats()
    stats['system_status'] = 'running' if system_state['is_running'] else 'idle'
    stats['current_mode'] = system_state['mode']
    return jsonify(stats)


@app.route('/api/recent-attendance')
def api_recent_attendance():
    """Get recent attendance records."""
    days = request.args.get('days', 7, type=int)
    records = get_attendance_records(days)
    return jsonify(records)


@app.route('/api/persons')
def api_persons():
    """Get all registered persons."""
    persons = get_person_list()
    return jsonify(persons)


# ============================================================================
# API ENDPOINTS - REGISTRATION
# ============================================================================

@app.route('/api/register/start', methods=['POST'])
def api_register_start():
    """Start face collection for new person."""
    try:
        data = request.json
        person_name = data.get('name', '').strip()
        
        if not person_name:
            return jsonify({'success': False, 'message': 'Name is required'}), 400
        
        # Create directory for person
        person_dir = FACE_DATA_DIR / person_name
        person_dir.mkdir(parents=True, exist_ok=True)
        
        system_state['mode'] = 'collection'
        system_state['current_person'] = person_name
        system_state['collected_samples'] = 0
        system_state['is_running'] = True
        
        logger.info(f"Started face collection for {person_name}")
        return jsonify({
            'success': True,
            'message': f'Started collecting faces for {person_name}',
            'person_name': person_name,
        })
    except Exception as e:
        logger.error(f"Error starting registration: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/register/stop', methods=['POST'])
def api_register_stop():
    """Stop face collection."""
    try:
        person_name = system_state['current_person']
        collected = system_state['collected_samples']
        
        system_state['mode'] = None
        system_state['current_person'] = None
        system_state['is_running'] = False
        
        logger.info(f"Stopped collection for {person_name}, {collected} samples collected")
        return jsonify({
            'success': True,
            'message': f'Collected {collected} face samples for {person_name}',
        })
    except Exception as e:
        logger.error(f"Error stopping registration: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/register/status')
def api_register_status():
    """Get registration status."""
    return jsonify({
        'is_running': system_state['is_running'],
        'person_name': system_state['current_person'],
        'collected_samples': system_state['collected_samples'],
        'mode': system_state['mode'],
    })


@app.route('/api/register/upload', methods=['POST'])
def api_register_upload():
    """Upload face image for registration."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        person_name = request.form.get('person_name')
        
        if not person_name:
            return jsonify({'success': False, 'message': 'Person name required'}), 400
        
        filename = secure_filename(f"{datetime.now().timestamp()}.jpg")
        person_dir = FACE_DATA_DIR / person_name
        person_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = person_dir / filename
        file.save(str(filepath))
        
        system_state['collected_samples'] += 1
        
        return jsonify({
            'success': True,
            'message': f'Face {system_state["collected_samples"]} uploaded',
            'samples_count': system_state['collected_samples'],
        })
    except Exception as e:
        logger.error(f"Error uploading face: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/register/train', methods=['POST'])
def api_register_train():
    """Train model with collected faces."""
    try:
        data = request.json
        person_name = data.get('person_name')
        
        if not person_name:
            return jsonify({'success': False, 'message': 'Person name required'}), 400
        
        # Check if person has enough samples
        person_dir = FACE_DATA_DIR / person_name
        samples = len(list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png')))
        
        if samples < 5:
            return jsonify({
                'success': False,
                'message': f'Need at least 5 samples, currently have {samples}',
            }), 400
        
        # Train the recognizer
        recognizer.train_on_faces(person_name)
        
        logger.info(f"Trained model for {person_name} with {samples} samples")
        return jsonify({
            'success': True,
            'message': f'Successfully trained model for {person_name} ({samples} samples)',
        })
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# API ENDPOINTS - ATTENDANCE CONTROL
# ============================================================================

@app.route('/api/attendance/start', methods=['POST'])
def api_attendance_start():
    """Start attendance tracking."""
    try:
        system_state['mode'] = 'attendance'
        system_state['is_running'] = True
        system_state['recognized_faces_count'] = 0  # Reset counter for new session
        
        # Start camera feed processing in background
        if not system_state['camera_running']:
            system_state['camera_running'] = True
            camera_thread = threading.Thread(target=camera_worker, daemon=True)
            camera_thread.start()
            system_state['camera_thread'] = camera_thread
            logger.info("Camera thread started")
        
        logger.info("Started attendance tracking")
        return jsonify({
            'success': True,
            'message': 'Attendance tracking started - Camera is now active',
        })
    except Exception as e:
        logger.error(f"Error starting attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/stop', methods=['POST'])
def api_attendance_stop():
    """Stop attendance tracking."""
    try:
        system_state['mode'] = None
        system_state['is_running'] = False
        system_state['camera_running'] = False
        
        # Wait for camera thread to finish
        if system_state['camera_thread'] is not None:
            system_state['camera_thread'].join(timeout=2)
            system_state['camera_thread'] = None
        
        logger.info("Stopped attendance tracking")
        return jsonify({
            'success': True,
            'message': 'Attendance tracking stopped',
        })
    except Exception as e:
        logger.error(f"Error stopping attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/status')
def api_attendance_status():
    """Get attendance tracking status."""
    return jsonify({
        'is_running': system_state['is_running'],
        'mode': system_state['mode'],
        'camera_running': system_state['camera_running'],
        'recognized_faces': system_state['recognized_faces_count'],
    })


@app.route('/api/camera/feed')
def api_camera_feed():
    """Stream camera feed as video/mjpeg."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={'Cache-Control': 'no-cache, no-store, must-revalidate'}
    )


# ============================================================================
# API ENDPOINTS - DATA EXPORT
# ============================================================================

@app.route('/api/export/csv')
def api_export_csv():
    """Export attendance data as CSV."""
    try:
        days = request.args.get('days', 30, type=int)
        records = get_attendance_records(days)
        
        # Generate CSV
        csv_content = "Name,Date,Time,Distance\n"
        for record in records:
            csv_content += f"{record['name']},{record['date']},{record['time']},{record['distance']}\n"
        
        filepath = ATTENDANCE_DIR / f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath.write_text(csv_content)
        
        return send_file(str(filepath), as_attachment=True, mimetype='text/csv')
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/export/json')
def api_export_json():
    """Export attendance data as JSON."""
    try:
        days = request.args.get('days', 30, type=int)
        records = get_attendance_records(days)
        
        filepath = ATTENDANCE_DIR / f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, 'w') as f:
            json.dump(records, f, indent=2)
        
        return send_file(str(filepath), as_attachment=True, mimetype='application/json')
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# API ENDPOINTS - MANAGEMENT
# ============================================================================

@app.route('/api/person/delete', methods=['POST'])
def api_person_delete():
    """Delete a registered person."""
    try:
        data = request.json
        person_name = data.get('name')
        
        if not person_name:
            return jsonify({'success': False, 'message': 'Person name required'}), 400
        
        person_dir = FACE_DATA_DIR / person_name
        if person_dir.exists():
            import shutil
            shutil.rmtree(person_dir)
            logger.info(f"Deleted person: {person_name}")
        
        return jsonify({
            'success': True,
            'message': f'Deleted {person_name} and all associated data',
        })
    except Exception as e:
        logger.error(f"Error deleting person: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/attendance/delete', methods=['POST'])
def api_attendance_delete():
    """Delete attendance record."""
    try:
        data = request.json
        person_name = data.get('name')
        date = data.get('date')
        
        if not person_name or not date:
            return jsonify({'success': False, 'message': 'Name and date required'}), 400
        
        db.delete_attendance(person_name, date)
        logger.info(f"Deleted attendance for {person_name} on {date}")
        
        return jsonify({
            'success': True,
            'message': f'Deleted attendance record',
        })
    except Exception as e:
        logger.error(f"Error deleting attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'success': False, 'message': 'Page not found'}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return jsonify({'success': False, 'message': 'Server error'}), 500


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting AutoAttendance Web UI")
    print("=" * 70)
    print("  AUTOATTENDANCE WEB UI")
    print("=" * 70)
    print("  Open your browser and go to: http://localhost:5000")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True,
    )
