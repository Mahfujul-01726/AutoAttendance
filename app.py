import os
import sys

# Add the current directory to sys.path so we can import the package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auto_attendance.web_ui import app

if __name__ == "__main__":
    # Hugging Face Spaces uses port 7860 by default
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)
