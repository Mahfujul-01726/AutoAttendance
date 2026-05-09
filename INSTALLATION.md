# Detailed Installation Guide

Complete step-by-step guide for installing AutoAttendance on all platforms.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Windows Installation](#windows-installation)
3. [Linux Installation](#linux-installation)
4. [macOS Installation](#macos-installation)
5. [Docker Installation](#docker-installation)
6. [Virtual Environment Setup](#virtual-environment-setup)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **Python**: 3.9 or higher
- **RAM**: 4 GB
- **Disk**: 2 GB free space
- **Processor**: Dual-core processor
- **Camera**: USB webcam or built-in camera

### Recommended Requirements
- **Python**: 3.11 or higher
- **RAM**: 8 GB
- **Disk**: 5 GB SSD
- **Processor**: Quad-core processor
- **GPU**: NVIDIA GPU (optional, for acceleration)

### Supported Operating Systems
- ✅ Windows 10/11
- ✅ Ubuntu 20.04+
- ✅ CentOS 8+
- ✅ macOS 10.15+

---

## Windows Installation

### Step 1: Install Python

1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ **Important**: Check "Add Python to PATH"
4. Complete installation

**Verify installation:**
```bash
python --version
pip --version
```

### Step 2: Install Git (Optional but Recommended)

Download from [git-scm.com](https://git-scm.com/download/win)

### Step 3: Clone Repository

```bash
# Using Git
git clone https://github.com/Mahfujul-01726/AutoAttendance.git
cd AutoAttendance

# Or download ZIP from GitHub and extract
```

### Step 4: Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate

# Verify activation (prompt should show (venv))
```

### Step 5: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 6: Configure Environment

```bash
# Copy configuration template
copy .env.example .env

# Edit .env with your settings
# You can use any text editor (Notepad, VS Code, etc.)
```

### Step 7: Test Installation

```bash
# Run tests
pytest tests/ -v

# Check camera
python cli.py check-camera
```

### Step 8: Run Application

```bash
# Start attendance system
python main.py

# Or start API server
python api.py
```

---

## Linux Installation

### Ubuntu/Debian

#### Step 1: Update System

```bash
sudo apt-get update
sudo apt-get upgrade
```

#### Step 2: Install Python and Dependencies

```bash
# Install Python 3.11
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Install system libraries
sudo apt-get install build-essential cmake git
sudo apt-get install libopencv-dev python3-opencv
sudo apt-get install libsm6 libxext6 libxrender-dev
```

#### Step 3: Clone Repository

```bash
git clone https://github.com/Mahfujul-01726/AutoAttendance.git
cd AutoAttendance
```

#### Step 4: Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

#### Step 5: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 6: Configure

```bash
cp .env.example .env
nano .env  # Edit with your settings
```

#### Step 7: Run

```bash
python main.py
```

### CentOS/RHEL

#### System Setup

```bash
sudo yum update
sudo yum install python39 python39-devel python39-virtualenv
sudo yum install opencv opencv-devel
sudo yum groupinstall "Development Tools"
```

#### Virtual Environment

```bash
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## macOS Installation

### Step 1: Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Dependencies

```bash
brew install python@3.11
brew install opencv
brew install cmake
```

### Step 3: Clone and Setup

```bash
git clone https://github.com/Mahfujul-01726/AutoAttendance.git
cd AutoAttendance

python3.11 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Grant Camera Permission

**macOS requires permission for camera access:**

1. Go to **System Preferences** → **Security & Privacy**
2. Click **Camera**
3. Allow Terminal or Python

### Step 5: Run

```bash
python main.py
```

---

## Docker Installation

### Using Docker Desktop

#### Step 1: Install Docker Desktop

- [Windows](https://www.docker.com/products/docker-desktop)
- [macOS](https://www.docker.com/products/docker-desktop)
- [Linux](https://docs.docker.com/engine/install/ubuntu/)

#### Step 2: Clone Repository

```bash
git clone https://github.com/Mahfujul-01726/AutoAttendance.git
cd AutoAttendance
```

#### Step 3: Start with Docker Compose

```bash
docker-compose up --build
```

#### Step 4: Access

- API: http://localhost:8000
- Documentation: http://localhost:8000/docs

### Using Docker CLI

```bash
# Build image
docker build -t auto-attendance .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --device /dev/video0 \
  auto-attendance
```

### Docker on Linux with GPU

```bash
docker run --gpus all \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --device /dev/video0 \
  auto-attendance:gpu
```

---

## Virtual Environment Setup

### Why Use Virtual Environments?

- ✅ Isolates project dependencies
- ✅ Prevents version conflicts
- ✅ Easy to manage multiple projects
- ✅ Clean system Python installation

### Create Virtual Environment

```bash
# Using venv (built-in)
python -m venv venv

# Using virtualenv (more features)
pip install virtualenv
virtualenv venv

# Using conda
conda create -n attendance python=3.11
conda activate attendance
```

### Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Deactivate:**
```bash
deactivate
```

### Verify Activation

```bash
which python  # Should show venv path
pip list      # Should be minimal
```

---

## Troubleshooting

### Python Not Found

**Windows:**
```bash
# Add Python to PATH manually
C:\Users\YourName\AppData\Local\Programs\Python\Python311
```

**Linux/macOS:**
```bash
python3 --version
alias python=python3
```

### Camera Not Working

```bash
# Check available cameras
python cli.py check-camera

# List video devices (Linux)
ls /dev/video*

# Check camera permissions (macOS)
# System Preferences → Security & Privacy → Camera
```

### Slow Performance

- ✅ Increase `FRAME_PROCESS_INTERVAL` in .env
- ✅ Lower `FRAME_WIDTH` and `FRAME_HEIGHT`
- ✅ Close other applications
- ✅ Use GPU acceleration

### Memory Issues

```bash
# Monitor memory usage
python -m memory_profiler main.py

# Reduce batch size
# Edit FRAME_PROCESS_INTERVAL in config.py
```

### Import Errors

```bash
# Verify all packages installed
pip list

# Reinstall requirements
pip install --force-reinstall -r requirements.txt

# Check Python path
import sys
print(sys.path)
```

### Permission Denied (Linux/macOS)

```bash
# Make scripts executable
chmod +x main.py cli.py api.py

# Or run with python
python main.py
```

---

## Verification

### Test Installation

```bash
# Check Python version
python --version

# Check virtual environment
which python

# List packages
pip list

# Run unit tests
pytest tests/ -v

# Check camera
python cli.py check-camera

# Verify all components
python -c "from face_recognition import FaceRecognitionModule; print('✓ Face recognition OK')"
python -c "from anti_spoofing import AntiSpoofing; print('✓ Anti-spoofing OK')"
python -c "from database import AttendanceDatabase; print('✓ Database OK')"
```

### First Run

```bash
# Start the system
python main.py

# You should see:
# ✓ System initialized successfully!
# ✓ Camera initialized
# ✓ Model loaded
# Face detection started...
```

---

## Next Steps

1. ✅ [Quick Start Guide](./QUICKSTART.md)
2. ✅ [Configuration Guide](./README.md#-configuration)
3. ✅ [API Documentation](./API.md)
4. ✅ [Contributing](./CONTRIBUTING.md)

---

## Support

If you encounter issues:
- 📖 Check [Troubleshooting](#troubleshooting)
- 🐛 [Report Issue](https://github.com/Mahfujul-01726/AutoAttendance/issues)
- 📧 [Email Support](mailto:support@autoattendance.dev)
