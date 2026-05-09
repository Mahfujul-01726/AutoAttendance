# 🎯 AutoAttendance Web UI - User Guide

> **Simple and Intuitive Interface for Non-Technical Users**

## Table of Contents

- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Registering People](#registering-people)
- [Marking Attendance](#marking-attendance)
- [Viewing Records](#viewing-records)
- [Managing Settings](#managing-settings)
- [Troubleshooting](#troubleshooting)
- [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Starting the Application

The AutoAttendance Web UI is designed to be simple for non-technical users.

#### **Windows Users:**
1. Double-click `run_web_ui.bat` in the AutoAttendance folder
2. A black window will open (this is normal)
3. Your browser will automatically open the web interface

#### **macOS/Linux Users:**
1. Open Terminal
2. Navigate to the AutoAttendance folder:
   ```bash
   cd /path/to/AutoAttendance
   ```
3. Run:
   ```bash
   bash run_web_ui.sh
   ```
4. Open your browser to: `http://localhost:5000`

### First Time Setup

On first launch:
- The system will check all components (camera, database, model)
- Dependencies will be installed automatically
- You'll see the web interface in your browser

---

## Dashboard Overview

The **Dashboard** is your home page. It shows:

### 📊 System Statistics

| Statistic | What it means |
|-----------|---------------|
| **Total Persons** | Number of people registered in the system |
| **Face Embeddings** | Total number of trained face samples |
| **Present Today** | How many people have already marked attendance today |

### 🎯 Quick Actions

Fast buttons to perform common tasks:
- **➕ Add New Person** - Register a new person
- **▶️ Start Attendance** - Begin real-time face recognition
- **📋 View Records** - See all attendance history
- **📥 Export Data** - Download your data as CSV or JSON

### 📈 Recent Activity

See the latest attendance records at a glance, including:
- Person's name
- Date and time of attendance
- Face recognition accuracy (distance score)

### 🔌 System Status

Check if all components are working:
- ✅ **Camera Status** - Is the camera connected?
- ✅ **Model Status** - Is the AI model loaded?
- ✅ **Database** - Is data storage working?
- ✅ **API Status** - Is the system running?

---

## Registering People

To use the attendance system, you first need to register people.

### Step-by-Step Registration

#### **Step 1: Enter Name**

1. Click **"Register Person"** in the sidebar
2. Enter the person's full name (e.g., "John Doe")
3. Click **"Next: Collect Faces"**

**Tips:**
- Use clear, complete names
- Avoid special characters if possible
- Names are case-insensitive

#### **Step 2: Collect Faces**

1. Position the person in front of the camera
2. Make sure the face is clearly visible
3. Click **"Start Collection"**
4. The system will automatically capture face samples

**Camera Setup:**
- **Good lighting** - Ensure the room is well-lit
- **Clear view** - Face should be directly facing camera
- **No obstructions** - Remove glasses, hats, or scarves
- **Different angles** - Move slowly left and right for variety

**Collection Tips:**
- Collect 20-30 samples for best accuracy
- Capture faces from different lighting conditions
- Include slight tilts and angles
- Take samples from about 1-2 meters away

5. When done, click **"Stop Collection"**
6. The system will show total samples collected

#### **Step 3: Train Model**

1. Click **"Next: Train Model"**
2. Review the details:
   - Person name
   - Total samples collected
3. Click **"Train Model"**
4. Wait for training to complete (usually 10-30 seconds)
5. You'll see a confirmation: **"Successfully trained model"**
6. Click **"Complete Registration"**

✅ The person is now registered and ready for attendance!

### Viewing Registered People

On the Register page, you can see all registered people:
- Their name
- Number of face samples
- Delete button (to remove if needed)

---

## Marking Attendance

### Manual Attendance

To start the real-time face recognition system:

1. Go to the **Dashboard**
2. Click **"Start Attendance"**
3. The system will process the camera feed
4. When a registered person is recognized, their attendance is automatically marked
5. When done, click **"Stop Attendance"**

### Status Indicators

- 🟢 **Green dot** - System is running
- 🔴 **Red dot** - System is idle or offline

### Attendance Marking

When a face is recognized:
- ✅ Name appears in recent attendance
- 🔔 Notification is displayed
- 📊 Record is saved to database

---

## Viewing Records

### Attendance Records Page

To view all attendance data:

1. Click **"Attendance Records"** in the sidebar
2. You'll see a table with:
   - **Name** - Person who marked attendance
   - **Date** - Date of attendance
   - **Time** - Time recorded
   - **Distance** - Recognition accuracy (lower is better)
   - **Status** - Present/Absent

### Filtering & Searching

**Search by Name:**
- Type in the "Search by name..." box
- Results update as you type

**Filter by Date:**
- Click the date input field
- Select a specific date
- Press Enter to filter

### Viewing Statistics

The page shows:
- **Total Records** - All attendance entries
- **Present** - Number of attendance marks
- **Absent** - Days without attendance (if configured)
- **Attendance Rate** - Percentage calculation

### Exporting Data

Export your data for reports or backup:

1. Click **"📥 CSV"** or **"📥 JSON"**
2. Select how many days to export
3. The file will download to your computer
4. Open in Excel or any text editor

**CSV Format:**
Great for Excel spreadsheets and reports

**JSON Format:**
Great for technical integration or backup

---

## Managing Settings

The **Settings** page allows you to configure the system.

### System Settings

#### Camera Device
- Select which camera to use
- Useful if you have multiple cameras

#### Recognition Confidence
- **Slider:** 0.0 (lenient) to 1.0 (strict)
- Higher values = more accurate but might miss faces
- Default (0.5) is recommended for most users

#### Frame Processing Rate
- Process every frame (slowest, most accurate)
- Process every 5 frames (balanced) - **Recommended**
- Process every 10 frames (faster, less accurate)

### Attendance Settings

#### Notifications
☑️ **Enable Notifications**
- Get alerts when attendance is marked
- Get alerts for unknown faces

☑️ **Enable Sound Alerts**
- Hear a beep when attendance is recorded
- Hear a warning for unknown faces

☑️ **Auto Backup**
- Automatically backup your data daily
- No action needed from you

### Email Notifications

Send reports via email:

1. Check **"Enable Email"**
2. Enter your email address
3. Select report frequency (Daily/Weekly/Monthly)
4. Click **"Test Email"** to verify

### Data Management

#### Backup Your Data
- Click **"Backup Data"** to create a backup
- Backups are saved with timestamp
- Great before making system changes

#### Export & Import Settings
- **Export Settings** - Save your configuration
- **Import Settings** - Restore from backup

### Maintenance

#### Clear Cache
- Frees up memory
- May temporarily slow down system on next use

#### Rebuild Database
- Optimizes database performance
- Takes a few minutes
- Only do if you have problems

#### View Logs
- See technical information about what happened
- Useful for troubleshooting

---

## Troubleshooting

### Common Issues

#### ❌ "Camera not found"

**Solution:**
1. Disconnect and reconnect the camera
2. Go to **Settings** and select correct camera device
3. Restart the application
4. Check if camera is in use by another app

#### ❌ "Face not recognized" or "Poor accuracy"

**Solution:**
1. Collect more face samples (30-50)
2. Ensure good lighting during collection AND during attendance
3. Retrain the model with better quality images
4. Try different camera angles
5. Remove glasses/hats/scarves if possible

#### ❌ "No faces detected"

**Solution:**
1. Make sure face is clearly visible and well-lit
2. Move closer to camera (about 1-2 meters)
3. Face should be directly facing camera
4. Check if camera lens is clean

#### ❌ "Database error" or "Cannot save attendance"

**Solution:**
1. Stop the application
2. Go to **Settings** → **Maintenance** → **Rebuild Database**
3. Wait for process to complete
4. Restart the application

#### ❌ "Attendance marks appearing twice"

**Solution:**
1. Increase the "Recognition Confidence" in Settings
2. Process fewer frames (use "Every 10 frames" mode)
3. Ensure person moves away from camera after marking

#### ❌ "Web page won't open"

**Solution:**
1. Make sure the application is running (black window should be visible)
2. Try opening `http://localhost:5000` manually in your browser
3. Make sure port 5000 is not used by another application
4. Close and restart the application

#### ❌ "Slow performance or freezing"

**Solution:**
1. Reduce number of registered persons (delete unused profiles)
2. Use **"Every 5-10 frames"** processing rate
3. Reduce camera resolution (lower FPS)
4. Clear cache in Settings
5. Restart the application

### Getting Help

If you have issues:

1. **Check Logs:**
   - Settings → View Logs
   - Look for error messages

2. **Backup and Reset:**
   - Settings → Backup Data
   - Settings → Maintenance → Rebuild Database

3. **Check Console Output:**
   - Look at the black window where app started
   - Error messages may be shown there

4. **Contact Support:**
   - Check documentation at GitHub
   - Create an issue with error details

---

## Tips & Best Practices

### ✅ For Best Recognition Accuracy

1. **Collect quality samples:**
   - Capture faces at different angles (left, center, right)
   - Vary lighting conditions (front light, side light)
   - Include various expressions (neutral, slight smile)
   - Collect 30-50 samples per person

2. **During attendance marking:**
   - Ensure proper lighting on the face
   - Face should be at right distance (1-2 meters)
   - Face directly facing camera
   - Remove temporary obstructions (hats, glasses, masks)

3. **System tuning:**
   - Start with Recognition Confidence at 0.5
   - Adjust if too many false positives or false negatives
   - Use "Every 5 frames" processing rate for balance

### 📊 For Best Data Management

1. **Regular backups:**
   - Backup data weekly using Export or Settings
   - Store backups in multiple locations
   - Keep important records archived

2. **Clean records:**
   - Delete duplicate entries if they occur
   - Archive old attendance data periodically
   - Keep database optimized (rebuild occasionally)

3. **Documentation:**
   - Export monthly reports as CSV
   - Keep records for audit trails
   - Document any manual entries

### 🔒 For Security

1. **Protect your system:**
   - Don't share access URLs
   - Keep your computer secure
   - Backup data regularly
   - Delete people when they leave

2. **Data privacy:**
   - Face samples are stored locally, not in cloud
   - Attendance records are private
   - Use access control on your computer

3. **System maintenance:**
   - Keep software updated
   - Run backups before updates
   - Monitor system performance

### 🎯 For Smooth Operation

1. **Initial setup:**
   - Start with small number of people (2-5)
   - Test system thoroughly before full rollout
   - Train staff on how to use system

2. **Ongoing:**
   - Register new people as they join
   - Do occasional system maintenance
   - Review records for accuracy
   - Update settings based on experience

3. **Troubleshooting:**
   - Keep detailed notes of issues
   - Document what solutions worked
   - Share knowledge with team

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` (Windows) or `Cmd+K` (Mac) | Open search |
| `Esc` | Close dialogs/modals |
| `Tab` | Navigate form fields |
| `Enter` | Submit forms |

---

## Frequently Asked Questions (FAQ)

**Q: How many people can I register?**
A: Theoretically unlimited, but performance may slow with 1000+. Start with 100-500 for best results.

**Q: How accurate is the system?**
A: 95-98% accuracy with good quality training samples and proper lighting.

**Q: Can I use an external camera?**
A: Yes! USB webcams work great. Connect and select in Settings.

**Q: Where is my data stored?**
A: All data is stored locally on your computer in the `data/` folder.

**Q: Can I delete someone's data?**
A: Yes! Go to Register page and click delete button next to their name.

**Q: How often should I backup?**
A: At least weekly, or before any major changes.

**Q: Can multiple cameras work?**
A: Currently, one camera at a time. You can switch cameras in Settings.

**Q: What if the system crashes?**
A: Your data is safe. Restart the application and everything will be restored.

**Q: Can I use this offline?**
A: Yes! The system runs completely offline on your computer.

**Q: Is there a mobile app?**
A: Not yet, but the web interface works on tablets and mobile browsers.

---

## System Requirements

### Minimum
- **CPU:** Intel Core i5 or equivalent
- **RAM:** 4 GB
- **Storage:** 500 MB free
- **Camera:** USB webcam or built-in camera

### Recommended
- **CPU:** Intel Core i7 or equivalent
- **RAM:** 8 GB
- **Storage:** 2 GB free
- **Camera:** HD or 4K camera
- **Internet:** Not required (works offline)

---

## Support & Documentation

For more help:
- 📖 [Full Documentation](https://github.com/Mahfujul-01726/AutoAttendance)
- 🐛 [Report Issues](https://github.com/Mahfujul-01726/AutoAttendance/issues)
- 💬 [Discussions](https://github.com/Mahfujul-01726/AutoAttendance/discussions)

---

**Happy tracking! 🎉**

*AutoAttendance - Making attendance management simple for everyone*
