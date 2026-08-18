import os
import sys

# Add the current directory to sys.path so we can import the package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Auto-restore persistent database from cloud if available
try:
    from auto_attendance.cloud_backup import restore_from_cloud
    restore_from_cloud()
except Exception as e:
    print(f"Cloud restore notice: {e}")

from auto_attendance.web_ui import app, recognizer

# Reload model embeddings into memory after cloud restore
try:
    recognizer.load_model()
except Exception as e:
    print(f"Model load notice: {e}")

if __name__ == "__main__":
    # Hugging Face Spaces uses port 7860 by default
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)
