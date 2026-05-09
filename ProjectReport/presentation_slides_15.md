# AutoAttendance Presentation Slides

This Markdown file is a 15-slide presentation outline for the AutoAttendance project. It is based on the current codebase, the project report, and the active implementation in the repository.

## Slide 1. Title Slide
- **Project title:** AutoAttendance
- **Subtitle:** Real-Time Face Recognition Based Automated Attendance System with Passive Liveness Detection
- **Presenter:** Md. Mahfujul Karim Sheikh
- **Course:** CSE 4206, Neural Network Lab
- **Institution:** Northern University of Business and Technology Khulna

## Slide 2. Problem Statement
- Manual attendance takes time and interrupts class or work.
- Paper registers and roll calls are prone to proxy attendance and recording errors.
- A better system should be contactless, fast, and easier to manage.
- AutoAttendance addresses these issues using webcam-based face recognition.

## Slide 3. Project Goal
- Capture and register face data for each person.
- Recognize known faces from a live camera stream.
- Mark attendance automatically and prevent duplicates.
- Store data locally and expose it through a dashboard.
- Add a lightweight liveness check to reduce spoofing.

## Slide 4. System Overview
- The project has two main runtime parts.
- Desktop app: `main.py` for live camera attendance.
- Web app: `api.py` for dashboard and summary data.
- Database: `models/attendance.sqlite3` stores students, embeddings, attendance, and alerts.

## Slide 5. Project Architecture
- `data_collection.py` collects face samples from the webcam.
- `train_model.py` registers embeddings from collected images.
- `face_recognition.py` performs detection and matching.
- `anti_spoofing.py` checks passive liveness.
- `attendance_manager.py` writes attendance to SQLite, Excel, CSV, and logs.

## Slide 6. Technology Stack
- Python is the main language.
- OpenCV handles camera input and display.
- InsightFace provides pretrained face analysis and embeddings.
- SQLite stores all persistent data locally.
- FastAPI powers the lightweight dashboard and API.
- Pandas and OpenPyXL support reporting exports.

## Slide 7. Face Data Collection
- The operator enters one or more person names.
- The webcam opens and face images are captured manually.
- The script recommends varied angles and lighting for better recognition.
- Images are saved under `data/faces/<person_name>/`.
- The default collection target is 80 samples per person.

## Slide 8. Registration and Model Setup
- `train_model.py` does not train a new deep model from scratch.
- It registers embeddings extracted from collected face images.
- Each person is inserted or updated in SQLite.
- The project uses a pretrained InsightFace model named `buffalo_l`.
- This makes enrollment faster than retraining a classic LBPH model.

## Slide 9. Recognition Workflow
- A frame is captured from the webcam.
- InsightFace detects faces and extracts normalized embeddings.
- The embedding is compared with stored embeddings in SQLite.
- Matching uses cosine similarity converted to cosine distance.
- The configured recognition threshold is `0.45`.

## Slide 10. Attendance Logic
- Known faces are marked present automatically.
- Attendance is stored only once per person per day.
- Duplicate prevention is enforced both in memory and in SQLite.
- The system writes to `attendance.log` and `data/attendance/attendance.xlsx`.
- A CSV daily report can also be exported.

## Slide 11. Anti-Spoofing
- The project uses passive liveness detection.
- It checks texture variance, contrast, frequency energy, and color variation.
- A weighted score determines whether a face looks real.
- The liveness threshold is `0.35`.
- This helps block simple printed-photo or screen-based spoofing.

## Slide 12. Web Dashboard and API
- `api.py` serves a dashboard in the browser.
- It shows total students, total embeddings, and present count for today.
- It lists recent attendance records with confidence values.
- It includes API endpoints for summary, students, attendance, and alerts.
- The dashboard uses a clean, responsive HTML interface.

## Slide 13. Data and Outputs
- Registered students are stored in the `students` table.
- Face embeddings are stored in the `face_embeddings` table.
- Attendance events are stored in the `attendance` table.
- Security and unknown-face events are stored in the `alerts` table.
- Main outputs include SQLite data, Excel files, CSV reports, and logs.

## Slide 14. Current Project Status
- The repository contains a complete working prototype.
- The report documents two enrolled people: `karim` and `soumitra`.
- The project report also documents 200 stored face embeddings.
- Example attendance data already exists in `data/attendance/`.
- The system runs on CPU using `CPUExecutionProvider`.

## Slide 15. Conclusion and Future Work
- AutoAttendance shows a practical end-to-end attendance workflow.
- It combines recognition, liveness checking, storage, and reporting.
- The most useful future improvements are stronger liveness detection, multi-face support, authentication for the dashboard, and encrypted biometric storage.
- The project is a solid base for a real deployment or further research.

## Slide 16. References
- **InsightFace:** A face analysis toolkit. https://github.com/deepinsight/insightface
- **OpenCV:** Open Source Computer Vision Library. https://opencv.org/
- **FastAPI:** Modern, fast web framework for building APIs with Python. https://fastapi.tiangolo.com/
- **SQLite:** Lightweight embedded relational database. https://www.sqlite.org/
- **Face Recognition:** Dlib face recognition and deep learning. http://dlib.net/
- **Liveness Detection:** Passive face liveness detection using texture analysis and frequency domain methods.
- **Embeddings:** ArcFace: Additive Angular Margin Loss for Deep Face Recognition. arXiv:1801.07698
- **Project Repository:** AutoAttendance - Real-time face recognition-based automated attendance system.

## Optional Speaker Note
- If you want, this outline can be converted into a PowerPoint-style script with short speaking points for each slide.