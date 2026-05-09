# 🚀 Quick Start Guide

Get AutoAttendance up and running in 5 minutes!

## System Requirements

- **Python**: 3.9 or higher
- **OS**: Windows, Linux, or macOS
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space
- **Webcam**: Any USB webcam or built-in camera

## Installation

### Option 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/Mahfujul-01726/AutoAttendance.git
cd AutoAttendance

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run the system
python main.py
```

### Option 2: Docker Installation

```bash
# Clone repository
git clone https://github.com/Mahfujul-01726/AutoAttendance.git
cd AutoAttendance

# Build and run with Docker Compose
docker-compose up --build

# API will be available at http://localhost:8000
```

### Option 3: Package Installation (PyPI)

```bash
pip install auto-attendance
auto-attendance
```

---

## Basic Usage

### 1. Run the Attendance System

```bash
python main.py
```

**What happens:**
- ✅ Camera initializes
- ✅ Face recognition model loads
- ✅ Live detection starts
- ✅ Attendance marked automatically

### 2. Collect Face Data for New Person

```bash
python cli.py collect
```

**Steps:**
1. Enter person's name
2. Enter email (optional)
3. Position face in frame
4. System captures ~100 samples from different angles
5. Press 'ESC' to stop

### 3. Train the Model

```bash
python cli.py train
```

The system trains on collected faces and registers them for future recognition.

### 4. View Attendance Records

```bash
python cli.py report --date 2026-05-09
```

---

## API Usage

### Start API Server

```bash
python api.py
```

Server starts at `http://localhost:8000`

### Quick API Examples

**Get attendance records:**
```bash
curl http://localhost:8000/attendance/records
```

**Mark attendance:**
```bash
curl -X POST http://localhost:8000/attendance/mark \
  -H "Content-Type: application/json" \
  -d '{"face_embedding": [...], "timestamp": "2026-05-09T10:00:00Z"}'
```

**View documentation:**
Visit `http://localhost:8000/docs` for interactive Swagger documentation

---

## Configuration

Edit `.env` file to customize settings:

```bash
# Camera settings
CAMERA_ID=0
FRAME_WIDTH=640
FRAME_HEIGHT=480
FPS=30

# Recognition threshold (0-1)
RECOGNITION_THRESHOLD=0.6

# Email notifications
ENABLE_EMAIL_NOTIFICATIONS=True
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## Data Management

```
data/
├── faces/              # Collected face samples
│   ├── john/
│   ├── jane/
│   └── ...
├── attendance/         # Attendance CSV files
│   └── attendance_2026-05-09.csv
└── training/           # Training data cache
```

### Export Attendance

```bash
python cli.py export --format excel --output report.xlsx
python cli.py export --format csv --output report.csv
```

---

## Troubleshooting

### Camera Not Working

```bash
# Check available cameras
python cli.py check-camera

# Try different camera ID
# Edit .env and change CAMERA_ID to 1, 2, 3, etc.
```

### Low Recognition Accuracy

- Collect more face samples (100+ per person)
- Ensure good lighting
- Collect samples from various angles
- Retrain the model

### Installation Issues

```bash
# Check Python version
python --version  # Should be 3.9+

# Verify dependencies
pip list

# Reinstall requirements
pip install --force-reinstall -r requirements.txt
```

---

## Next Steps

1. 📖 Read [full documentation](README.md)
2. 🏗️ Check [architecture guide](ARCHITECTURE.md)
3. 🔌 Explore [API documentation](API.md)
4. 🤝 Contribute via [CONTRIBUTING.md](CONTRIBUTING.md)
5. 💬 Join community discussions

---

## Support

- 📝 [Issues](https://github.com/Mahfujul-01726/AutoAttendance/issues)
- 💬 [Discussions](https://github.com/Mahfujul-01726/AutoAttendance/discussions)
- 📧 [Email](mailto:contact@autoattendance.dev)

---

## What's Next?

### Production Deployment
- Set up HTTPS
- Configure authentication
- Setup database backups
- Enable email notifications

### Advanced Features
- Multi-camera setup
- Mobile app integration
- Dashboard analytics
- Biometric integration

---

Happy tracking! 🎉
