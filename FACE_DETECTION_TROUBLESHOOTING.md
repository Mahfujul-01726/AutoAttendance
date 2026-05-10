# Face Detection Not Working - Troubleshooting Guide

## Quick Fix Checklist

### Step 1: Train Face Embeddings (CRITICAL)
If you haven't done this yet, faces won't be recognized. Run:

```bash
python train_model.py
```

**Expected output:**
```
Processing karim: 100 images
  karim: 100/100 images registered
Processing masud: 50 images
Processing rudo: 40 images
Processing soumitra: 60 images
Registration completed successfully!
Total people registered: 4
Total embeddings registered: 250
```

### Step 2: Restart the Web UI
After training, restart the web UI:

```bash
python run_web_ui.py
```

### Step 3: Check Dashboard
- Open http://localhost:5000
- Check if "Face Embeddings" count shows > 0
- If it shows 0, embeddings didn't load properly

### Step 4: Test Face Detection
Click **"Start Attendance"** button:
- Camera should open
- **Green box** = Known person (attendance marked)
- **Red box** = Unknown person (not in database)
- **Orange box** = Spoofing detected (printed photo or screen)
- **No boxes** = No faces detected (see troubleshooting below)

---

## Troubleshooting If Faces Still Not Detected

### Issue 1: No Face Boxes Appear at All

**Possible Causes:**

1. **Camera Problem**
   - Is camera facing you?
   - Is there enough light?
   - Try moving closer to camera (30-60cm away)

2. **InsightFace Model Not Loaded**
   - Check logs: `logs/attendance_*.log`
   - Look for errors mentioning InsightFace or ONNX

3. **Embeddings Not Trained**
   - Check if database has embeddings:
     ```bash
     python -c "from database import AttendanceDatabase; db = AttendanceDatabase(); print(f'Embeddings: {db.get_total_embeddings()}')"
     ```
   - If shows 0, run `python train_model.py`

### Issue 2: Faces Detected But Not Recognized (Always "Unknown")

**Possible Causes:**

1. **Training Images Are Poor Quality**
   - Use images with:
     - Clear, frontal face view
     - Good lighting
     - Neutral expression
   - Remove blurry or side-view images

2. **Recognition Threshold Too Strict**
   - Edit `config.py`:
     ```python
     RECOGNITION_THRESHOLD = 0.50  # Increase from 0.45 for more lenient matching
     ```
   - Restart web UI
   - Run `python train_model.py` again

3. **Not Enough Training Images**
   - Retrain with more images (100+ per person recommended)
   - Delete `models/attendance.sqlite3`
   - Run `python train_model.py`

### Issue 3: Model Loading Errors

**Check Debug Output:**

1. Open new terminal and run:
   ```bash
   python -c "from face_recognition import FaceRecognitionModule; r = FaceRecognitionModule(); r.load_model()"
   ```

2. Look for errors about:
   - InsightFace import failures → Install: `pip install insightface onnx onnxruntime`
   - Model download failures → Check internet connection
   - ONNX runtime errors → Install correct version: `pip install onnxruntime`

---

## Key Components

### 1. Training Pipeline
```
Raw Images (data/faces/person_name/*.jpg)
    ↓
InsightFace Detector (detects face in image)
    ↓
Face Embedding (512-dimensional vector)
    ↓
SQLite Database (models/attendance.sqlite3)
```

### 2. Recognition Pipeline (Real-time)
```
Camera Frame
    ↓
InsightFace Detector (detects faces in frame)
    ↓
Face Embedding for each detected face
    ↓
Compare with Database Embeddings
    ↓
Display Result (Green/Red/Orange box)
```

### 3. Anti-Spoofing Check
- Analyzes texture (Difference of Gaussians method)
- Detects printed photos and screen replays
- Must pass before attendance is marked

---

## Verify Everything Works

Run this Python script to diagnose:

```python
from database import AttendanceDatabase
from face_recognition import FaceRecognitionModule
import cv2

# Check embeddings
db = AttendanceDatabase()
embeddings = db.get_total_embeddings()
print(f"✓ Database embeddings: {embeddings}")

# Check model
rec = FaceRecognitionModule()
rec.load_model()
print(f"✓ Model loaded, known faces: {rec.label_count}")

# Check camera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    faces = rec.detect_faces(frame)
    print(f"✓ Camera works, detected {len(faces)} faces")
cap.release()
```

---

## Still Having Issues?

1. **Check logs:**
   ```bash
   tail -50 logs/attendance_202605.log
   ```

2. **Look for these error patterns:**
   - "No face embeddings found" → Run `python train_model.py`
   - "Failed to load model" → Check InsightFace installation
   - "Cannot open camera" → Check CAMERA_ID in config.py
   - "Error processing frame" → Check anti_spoofing module

3. **Common fixes:**
   - Delete `models/attendance.sqlite3` and retrain
   - Update InsightFace: `pip install --upgrade insightface`
   - Verify camera ID: Check System Information for correct device

---

## How It Should Look

When working correctly:
- ✓ Dashboard shows count of registered faces
- ✓ Camera feed displays in real-time
- ✓ Faces show colored boxes (green = known, red = unknown)
- ✓ Names appear above faces
- ✓ Attendance records update in real-time
