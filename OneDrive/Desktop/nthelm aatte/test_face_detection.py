import cv2
import os

def detect_face(image_path):
    try:
        cascade_path = "models/haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        img = cv2.imread(image_path)
        if img is None:
            return False
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces) > 0
    except Exception as e:
        print(f"Error: {e}")
        return False

# Paths to generated images
pos_img = r"C:\Users\achua\.gemini\antigravity\brain\3ca85ad4-87f7-4fb2-b50f-1908e44ca34d\test_face_positive_1773728803347.png"
neg_img = r"C:\Users\achua\.gemini\antigravity\brain\3ca85ad4-87f7-4fb2-b50f-1908e44ca34d\test_face_negative_1773728821832.png"

print(f"Testing positive image (should be True): {detect_face(pos_img)}")
print(f"Testing negative image (should be False): {detect_face(neg_img)}")
