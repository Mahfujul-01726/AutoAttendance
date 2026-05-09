# AutoAttendance Project Architecture

## 1. Purpose

AutoAttendance is a face-recognition attendance system with two operating modes:

- a desktop real-time attendance application that uses a webcam to recognize people and mark them present
- a lightweight web dashboard and API that show attendance and registration data from the same database

The project is designed for day-to-day use by an operator, while also being structured clearly enough for academic review, prototyping, and further research.

## 2. What The System Does

At a high level, the system:

1. collects face images for each person
2. converts those images into face embeddings using a pretrained InsightFace model
3. stores the embeddings in SQLite
4. runs live recognition from a webcam
5. checks whether the detected face looks real or spoofed
6. records attendance for known people
7. exposes attendance data through exported files and a web dashboard

## 3. High-Level Architecture

```text
                         +----------------------+
                         |      User/Admin      |
                         +----------+-----------+
                                    |
                +-------------------+-------------------+
                |                                       |
                v                                       v
    +-------------------------+             +-------------------------+
    |  Desktop Camera System  |             |   Web Dashboard / API   |
    |       (main.py)         |             |        (api.py)         |
    +-----------+-------------+             +------------+------------+
                |                                        |
                v                                        v
       +------------------+                    +----------------------+
       | Recognition Core |<------------------>| SQLite Database      |
       | face_recognition |                    | attendance.sqlite3   |
       +--------+---------+                    +----------------------+
                |
                v
       +------------------+
       | Anti-Spoofing    |
       | anti_spoofing.py |
       +------------------+
                |
                v
       +------------------+
       | Attendance       |
       | Manager          |
       +------------------+
                |
                v
       +------------------+
       | CSV / Excel /    |
       | Log Exports      |
       +------------------+
```

## 4. Core Design Idea

This project is built around **embedding-based face recognition**.

That means the system does not train a face classifier from scratch. Instead, it uses a pretrained deep model to convert each face into a numeric vector called an embedding. During recognition, the system compares a new face embedding against the stored embeddings of registered people and finds the closest match.

This is the most important architectural idea in the project.

## 5. Main Subsystems

### 5.1 Configuration Layer

File: `config.py`

This file centralizes runtime settings such as:

- camera device and frame size
- processing interval for recognition
- InsightFace model configuration
- recognition threshold
- database and data directory paths
- anti-spoofing threshold

Important active settings:

- `INSIGHTFACE_MODEL_NAME = 'buffalo_l'`
- `INSIGHTFACE_PROVIDERS = ['CPUExecutionProvider']`
- `RECOGNITION_THRESHOLD = 0.45`
- `DATABASE_PATH = 'models/attendance.sqlite3'`
- `FRAME_PROCESS_INTERVAL = 5`

Architecturally, this file acts as the control panel for the entire system.

### 5.2 Data Collection Subsystem

File: `data_collection.py`

Purpose:

- collect face samples from the webcam
- save them under `data/faces/<person_name>/`
- guide the operator to capture different face angles

How it works:

1. the operator enters one or more names
2. the camera opens
3. the operator presses `c` to capture face samples
4. cropped face images are stored in that person's folder

This stage is the enrollment input stage of the system.

### 5.3 Registration / Training Subsystem

File: `train_model.py`

Purpose:

- process collected face images
- extract embeddings using InsightFace
- save the embeddings into SQLite

Important note:

This stage is called "training" in the script name, but in the current architecture it is closer to **registration** than full model training. The deep model itself is pretrained. What changes over time is the set of stored person embeddings.

### 5.4 Recognition Engine

File: `face_recognition.py`

This is the core machine-learning module.

Responsibilities:

- load the pretrained InsightFace `FaceAnalysis` app
- detect faces in incoming frames
- produce normalized face embeddings
- compare each new embedding with stored embeddings
- classify the face as known or unknown based on cosine distance

Recognition logic:

1. detect faces in the frame
2. compute an embedding for each face
3. compare the embedding with all stored embeddings
4. choose the best match by highest cosine similarity
5. convert similarity to distance using `1 - similarity`
6. accept the match only if distance is below the configured threshold

So the recognition path is:

```text
frame -> face detection -> embedding -> similarity search -> threshold decision
```

### 5.5 Anti-Spoofing Subsystem

File: `anti_spoofing.py`

Purpose:

- reduce false acceptance from printed photos or screen displays

Current method:

- Laplacian texture variance
- grayscale contrast
- high-frequency energy
- color variation

These features are combined into a liveness score. If the score is above `SPOOF_THRESHOLD`, the face is treated as real.

Research note:

This is a **heuristic passive liveness module**, not a learned anti-spoofing network. It is useful as a lightweight safety layer, but it should not be treated as a state-of-the-art spoof defense.

### 5.6 Live Attendance Runtime

File: `main.py`

Purpose:

- run the webcam-driven attendance workflow in real time

Responsibilities:

- initialize the camera
- load registered embeddings
- process frames continuously
- run recognition every `FRAME_PROCESS_INTERVAL` frames
- run liveness checks on face crops
- mark attendance for known faces
- show results visually in the camera window
- play alerts for unknown or spoofed detections
- export the final report when the session ends

This is the primary operational application of the project.

### 5.7 Attendance Management Subsystem

File: `attendance_manager.py`

Purpose:

- maintain daily attendance state
- prevent duplicate attendance entries
- write records to SQLite
- generate operator-friendly output files

Outputs:

- `attendance.log`
- `data/attendance/attendance.xlsx`
- `data/attendance/attendance_YYYY-MM-DD.csv`

This module acts as the bridge between recognition events and administrative reporting.

### 5.8 Data Persistence Subsystem

File: `database.py`

Purpose:

- provide SQLite-backed storage for the whole system

Main tables:

- `students`
- `face_embeddings`
- `attendance`
- `alerts`

This database is the single source of truth used by both the desktop application and the web API.

### 5.9 Dashboard and API Subsystem

File: `api.py`

Purpose:

- expose current attendance information through a FastAPI application
- provide a built-in dashboard page

Endpoints:

- `/` : HTML dashboard
- `/api/summary` : summary counts
- `/api/students` : student records
- `/api/attendance` : attendance records
- `/api/alerts` : alert records

This subsystem is read-oriented. It visualizes and serves the data already generated by the desktop runtime and registration pipeline.

## 6. End-To-End Operational Workflow

### Stage 1: Setup

Script:

```powershell
python setup.py
```

What it does:

- checks dependencies
- creates required directories
- prepares `.env`
- tests the camera

### Stage 2: Collect Face Samples

Script:

```powershell
python data_collection.py
```

Output:

- multiple cropped face images per person
- stored under `data/faces/<person_name>/`

### Stage 3: Register Embeddings

Script:

```powershell
python train_model.py
```

Output:

- people inserted or updated in SQLite
- embeddings stored in `models/attendance.sqlite3`

### Stage 4: Run Real-Time Attendance

Script:

```powershell
python main.py
```

Runtime behavior:

- webcam starts
- faces are detected
- known faces are matched and marked present
- unknown faces trigger visual and audio alerts
- spoof-like faces are rejected

### Stage 5: View Results

Desktop outputs:

- Excel file
- CSV daily export
- text log

Web dashboard:

```powershell
uvicorn api:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## 7. Detailed Runtime Data Flow

### 7.1 Enrollment Data Flow

```text
Operator
  -> data_collection.py
  -> webcam frame
  -> detected face crop
  -> saved image file
  -> data/faces/<person_name>/
```

### 7.2 Registration Data Flow

```text
Saved face images
  -> face_recognition.py
  -> InsightFace embedding extraction
  -> AttendanceDatabase.upsert_student()
  -> AttendanceDatabase.add_embedding()
  -> models/attendance.sqlite3
```

### 7.3 Attendance Data Flow

```text
Live camera frame
  -> main.py
  -> face_recognition.recognize_frame()
  -> best embedding match
  -> anti_spoofing.is_liveness_detected()
  -> attendance_manager.mark_attendance()
  -> database attendance table
  -> Excel / CSV / log output
```

### 7.4 Dashboard Data Flow

```text
SQLite database
  -> AttendanceDatabase queries
  -> FastAPI endpoints
  -> HTML dashboard and JSON API
```

## 8. Database Architecture

The database file is:

```text
models/attendance.sqlite3
```

### 8.1 students

Stores identity-level information.

Typical fields:

- `id`
- `name`
- `external_id`
- `department`
- `email`
- `phone`
- `status`
- `created_at`

### 8.2 face_embeddings

Stores one or more embeddings for each student.

Typical fields:

- `id`
- `student_id`
- `embedding`
- `embedding_dim`
- `image_path`
- `model_name`
- `quality_score`
- `created_at`

This design allows multiple face samples per student, which is useful for better recognition robustness across pose and lighting changes.

### 8.3 attendance

Stores daily attendance events.

Typical fields:

- `id`
- `student_id`
- `student_name`
- `date`
- `time`
- `status`
- `confidence`
- `camera_id`
- `created_at`

The current schema enforces:

```text
UNIQUE(student_name, date)
```

So one person is recorded at most once per day.

### 8.4 alerts

Stores security or anomaly alerts.

Typical fields:

- `id`
- `alert_type`
- `message`
- `image_path`
- `created_at`

## 9. Folder Structure

```text
AutoAttendance/
├── api.py
├── main.py
├── config.py
├── database.py
├── face_recognition.py
├── anti_spoofing.py
├── attendance_manager.py
├── data_collection.py
├── train_model.py
├── setup.py
├── email_notification.py
├── face_detection.py
├── data/
│   ├── attendance/
│   ├── faces/
│   ├── training/
│   └── unknown_faces/
├── models/
│   └── attendance.sqlite3
└── Reportformat/
```

### Folder meanings

- `data/faces/` contains enrolled face images
- `data/attendance/` contains generated attendance reports
- `data/training/` exists for compatibility and project organization
- `data/unknown_faces/` is reserved for unknown-person related handling
- `models/` stores the SQLite database
- `Reportformat/` contains report-writing assets and is separate from the runtime system

## 10. File Responsibility Map

### Runtime-critical files

- `main.py` - real-time attendance loop
- `face_recognition.py` - detection, embeddings, matching
- `anti_spoofing.py` - liveness heuristics
- `attendance_manager.py` - record management and exports
- `database.py` - persistence layer
- `config.py` - global settings

### Enrollment and preparation files

- `data_collection.py` - collect face images
- `train_model.py` - register embeddings
- `setup.py` - environment bootstrap

### Monitoring files

- `api.py` - web dashboard and JSON API

### Optional or legacy-adjacent files

- `face_detection.py` - Haar-cascade helper module, not the main active recognition path
- `email_notification.py` - email utility module, currently not wired into the main runtime flow

## 11. User View Of The System

A normal operator can understand the project in four steps:

1. collect face samples for each person
2. register those people into the system
3. run the camera-based attendance app
4. view attendance in reports or the dashboard

From a user perspective, the desktop app is the main tool and the dashboard is the reporting interface.

## 12. Researcher View Of The System

A researcher should understand the project through these architectural properties:

- the system uses a pretrained deep face model rather than training a new classifier
- recognition is embedding-based and threshold-driven
- the database stores multiple embeddings per identity
- attendance is event-based and deduplicated per day
- anti-spoofing is heuristic, lightweight, and passive
- the dashboard is a thin read layer over operational data

This makes the system suitable for:

- applied computer vision coursework
- prototyping attendance automation
- studying threshold-based recognition behavior
- extending toward stronger liveness detection or multi-camera deployments

## 13. Strengths Of The Current Architecture

- simple end-to-end workflow
- clear separation between capture, recognition, storage, and presentation
- one shared database for both the desktop app and web dashboard
- multiple embeddings per person for stronger matching robustness
- easy to extend because modules are already separated by responsibility

## 14. Current Limitations

These limitations are important for both users and researchers:

- anti-spoofing is heuristic and not highly robust against advanced attacks
- matching currently appears to use a linear scan over stored embeddings, which is fine for small deployments but not ideal at large scale
- some older documentation still describes an LBPH/Haar-centered design, while the live code now uses InsightFace plus SQLite
- `RECOGNITION_MODEL_PATH = 'models/face_recognizer.yml'` remains in configuration even though the active recognition path is database-based
- email notification utilities exist but are not integrated into the live attendance workflow

## 15. Conceptual Architecture Summary

In one sentence:

> AutoAttendance is an embedding-based face-recognition attendance platform in which enrollment images are converted into stored face embeddings, live camera frames are matched against those embeddings, attendance is written into SQLite, and results are exposed through exported reports and a FastAPI dashboard.

## 16. Minimal Architecture Summary For Presentation

If you need a short explanation for a user, teacher, or report:

```text
The system first collects face images for each student, then converts those
images into numerical face embeddings using a pretrained InsightFace model.
During live attendance, each webcam frame is analyzed, matched against the
stored embeddings, checked for basic liveness, and then recorded in a SQLite
database. The same database powers exported attendance reports and a web
dashboard.
```

## 17. Suggested Future Improvements

- replace heuristic anti-spoofing with a learned liveness model
- store unknown-face snapshots in `data/unknown_faces/`
- integrate `alerts` table writes directly from the live runtime
- connect `email_notification.py` into attendance and alert events
- add student metadata management through API endpoints
- support multi-camera deployments
- add ANN or vector indexing if the number of registered people grows large

## 18. Important Reality Check

Some files in the repository still reflect an older architecture based on LBPH and Haar cascades. The current live code path is different:

- main recognition is handled by `face_recognition.py` using InsightFace
- long-term storage is handled by SQLite in `models/attendance.sqlite3`
- the dashboard reads from the same SQLite store

So this document describes the **actual active architecture in code**, not just the original intended design.
