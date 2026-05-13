"""
Train the face recognition model
Run this after collecting training data
"""

from .face_recognition import FaceRecognitionModule

def train_model():
    """Register face embeddings with the pretrained InsightFace model."""
    
    print("Starting face embedding registration...")
    recognizer = FaceRecognitionModule()
    people_count, embedding_count = recognizer.train_from_directory()

    if embedding_count == 0:
        print("No usable face images found. Please collect faces first using data_collection.py")
        return

    print("Registration completed successfully!")
    print("Embeddings saved to SQLite and ready for use")
    print(f"Total people registered: {people_count}")
    print(f"Total embeddings registered: {embedding_count}")

if __name__ == "__main__":
    train_model()
