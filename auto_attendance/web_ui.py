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
import base64

from . import cloud_backup
from .database import AttendanceDatabase
from .face_recognition import FaceRecognitionModule
from .anti_spoofing import AntiSpoofing
from .attendance_manager import AttendanceManager
from .data_collection import DataCollectionModule
from .config import (
    CAMERA_ID, FACE_DATA_DIR, ATTENDANCE_DIR, 
    FRAME_WIDTH, FRAME_HEIGHT, FPS, DATABASE_PATH
)
from .logger import get_logger

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

def get_person_list():
    """Get list of all active registered persons synchronized with database."""
    try:
        persons_dict = {}
        # 1. Read from folders with samples
        if FACE_DATA_DIR.exists():
            for person_dir in FACE_DATA_DIR.iterdir():
                if person_dir.is_dir():
                    face_files = list(person_dir.glob('*.jpg')) + list(person_dir.glob('*.png'))
                    if len(face_files) > 0:
                        persons_dict[person_dir.name] = len(face_files)

        # 2. Check DB students with embeddings
        db_students = db.list_students()
        for st in db_students:
            name = st.get("name")
            emb_cnt = st.get("embedding_count", 0)
            if name and name not in persons_dict and emb_cnt > 0:
                persons_dict[name] = emb_cnt

        persons = [{'name': name, 'samples': samples} for name, samples in persons_dict.items()]
        return sorted(persons, key=lambda x: x['name'])
    except Exception as e:
        logger.error(f"Error getting person list: {e}")
        return []


def get_dashboard_stats():
    """Get statistics for dashboard, synchronized with active person list."""
    try:
        persons = get_person_list()
        total_persons = len(persons)
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
        
        # Auto-sync persistent database to cloud repository
        cloud_backup.sync_to_cloud_async()
        
        logger.info(f"Trained model for {person_name} with {samples} samples and synced to cloud")
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
        system_state['camera_running'] = True
        
        logger.info("Started attendance tracking via Web Camera")
        return jsonify({
            'success': True,
            'message': 'Attendance tracking started - Web Camera is now active',
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


@app.route('/api/frame/process', methods=['POST'])
def api_frame_process():
    """Process a single frame from the web camera."""
    if not system_state['is_running'] or not system_state['mode']:
        return jsonify({'success': False, 'message': 'System not running'})
        
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'success': False, 'message': 'No image provided'})
            
        # Decode base64 image
        encoded_data = data['image'].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        system_state['total_frames'] += 1
        
        newly_marked_name = None
        recognized_name = None
        if system_state['mode'] == 'attendance':
            results = recognizer.recognize_frame(frame)
            if results:
                for result in results:
                    x1, y1 = result['bbox'][0], result['bbox'][1]
                    w, h = result['bbox'][2], result['bbox'][3]
                    x2, y2 = x1 + w, y1 + h
                    
                    y1, x1 = max(0, int(y1)), max(0, int(x1))
                    y2, x2 = min(frame.shape[0], int(y2)), min(frame.shape[1], int(x2))
                    
                    face_crop = frame[y1:y2, x1:x2]
                    is_real = False
                    if face_crop.size > 0:
                        is_real, spoof_score = anti_spoofing.analyze(face_crop)
                        
                    if not is_real:
                        db.add_alert('spoof', f"Spoof attempt detected (score: {spoof_score:.3f})")
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                        cv2.putText(frame, "SPOOF", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    elif result['is_known']:
                        person_name = result['name']
                        recognized_name = person_name
                        student_id = result.get('student_id')
                        # Mark attendance in database
                        marked = db.mark_attendance(student_id, person_name, result.get('confidence', 0), CAMERA_ID, 'Present')
                        if marked:
                            system_state['recognized_faces_count'] += 1
                            newly_marked_name = person_name
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, person_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, "Unknown", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
        elif system_state['mode'] == 'collection':
            faces = recognizer.detect_faces(frame)
            if faces:
                for face in faces:
                    x1, y1, x2, y2 = recognizer._bbox_to_int(face.bbox, frame.shape)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
        # Encode back to base64 for preview
        _, buffer = cv2.imencode('.jpg', frame)
        processed_image = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{processed_image}',
            'recognized': system_state['recognized_faces_count'],
            'newly_marked': newly_marked_name is not None,
            'marked_name': newly_marked_name,
            'recognized_name': recognized_name
        })
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return jsonify({'success': False, 'message': str(e)})


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
        
        # 1. Delete physical directory
        person_dir = FACE_DATA_DIR / person_name
        if person_dir.exists():
            import shutil
            shutil.rmtree(person_dir, ignore_errors=True)
            logger.info(f"Deleted person folder: {person_name}")

        # 2. Delete from SQLite database
        db.delete_student(person_name)

        # 3. Reload model embeddings
        recognizer.load_model()
        
        # 4. Sync deletion to cloud repository
        cloud_backup.sync_to_cloud_async()
        logger.info(f"Reloaded face recognizer model after deleting {person_name} and synced to cloud")
        
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
        cloud_backup.sync_to_cloud_async()
        logger.info(f"Deleted attendance for {person_name} on {date}")
        
        return jsonify({
            'success': True,
            'message': f'Deleted attendance record',
        })
    except Exception as e:
        logger.error(f"Error deleting attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================================
# API ENDPOINTS - BACKUP & PERSISTENCE
# ============================================================================

@app.route('/api/backup/status')
def api_backup_status():
    """Get backup status and statistics."""
    try:
        status = cloud_backup.get_backup_status()
        return jsonify({'success': True, **status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/backup/download')
def api_backup_download():
    """Download a complete backup archive."""
    try:
        format_type = request.args.get('format', 'zip')
        if format_type == 'sqlite3':
            if not os.path.exists(DATABASE_PATH):
                return jsonify({'success': False, 'message': 'Database not found'}), 404
            return send_file(str(DATABASE_PATH), as_attachment=True, download_name="attendance.sqlite3")
        else:
            archive_path = cloud_backup.export_full_archive()
            if not archive_path or not os.path.exists(archive_path):
                return jsonify({'success': False, 'message': 'Failed to create backup'}), 500
            return send_file(str(archive_path), as_attachment=True, download_name=archive_path.name)
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/backup/upload', methods=['POST'])
def api_backup_upload():
    """Upload and restore a database backup archive."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Empty file'}), 400
            
        filename = secure_filename(file.filename)
        temp_path = cloud_backup.BACKUP_DIR / f"uploaded_{filename}"
        file.save(str(temp_path))
        
        success = cloud_backup.import_full_archive(temp_path)
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass
            
        if success:
            recognizer.load_model()
            cloud_backup.sync_to_cloud_async()
            return jsonify({'success': True, 'message': 'Database and face profiles restored successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Invalid backup file format (.sqlite3 or .zip required)'}), 400
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/backup/sync', methods=['POST'])
def api_backup_sync():
    """Manually trigger immediate cloud sync."""
    try:
        success = cloud_backup.sync_to_cloud()
        if success:
            return jsonify({'success': True, 'message': 'Database and face profiles synced to cloud successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Cloud sync failed. Check Hugging Face token.'}), 500
    except Exception as e:
        logger.error(f"Error during manual cloud sync: {e}")
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
        port=7860,
        debug=False,
        threaded=True,
    )
