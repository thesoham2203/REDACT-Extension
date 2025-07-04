import cv2
import pytesseract
import re
import os
import numpy as np
from faker import Faker
import dlib

class ImageRedactor:
    fake = Faker()

    # Face Detection Setup
    face_detector = dlib.get_frontal_face_detector()
    model_path = os.path.join(os.path.dirname(__file__), "shape_predictor_68_face_landmarks.dat")
    landmark_predictor = dlib.shape_predictor(model_path)

    @staticmethod
    def extract_sensitive_data(text):
        patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            'PHONE': r'\b(\+?[0-9]{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
            'AADHAAR': r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
            'PAN': r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
            'DATE': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            'NAME': r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b'  # crude full name guess
        }

        sensitive_matches = []
        for label, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                value = match if isinstance(match, str) else " ".join(match)
                sensitive_matches.append((value.strip(), label))

        return sensitive_matches

    @staticmethod
    def generate_synthetic_data(label):
        return {
            'EMAIL': ImageRedactor.fake.email(),
            'PHONE': ImageRedactor.fake.phone_number(),
            'AADHAAR': ImageRedactor.fake.bothify(text='#### #### ####'),
            'PAN': ImageRedactor.fake.bothify(text='?????####?'),
            'DATE': ImageRedactor.fake.date(),
            'NAME': ImageRedactor.fake.name()
        }.get(label, "SYNTHETIC")

    @staticmethod
    def redact_faces(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = ImageRedactor.face_detector(gray, 1)
        for face in faces:
            landmarks = ImageRedactor.landmark_predictor(gray, face)
            points = np.array([[landmarks.part(i).x, landmarks.part(i).y] for i in range(68)])
            hull = cv2.convexHull(points)
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillConvexPoly(mask, hull, 255)
            blurred = cv2.GaussianBlur(image, (55, 55), 30)
            image[mask == 255] = blurred[mask == 255]
        return image

    @staticmethod
    def redact(file_path: str, redaction_type: str, redaction_level: int) -> str:
        image = cv2.imread(file_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Optional preprocessing
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

        # Tesseract OCR with Hindi + English
        config = r'--oem 3 --psm 6 -l eng+hin'
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config=config)
        full_text = " ".join(data['text'])

        # Get sensitive entities
        sensitive_items = ImageRedactor.extract_sensitive_data(full_text)

        # Redact matched blocks
        for i, word in enumerate(data['text']):
            if not word.strip():
                continue

            for sensitive_text, label in sensitive_items:
                if sensitive_text in word or word in sensitive_text:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

                    # Slightly expand redaction box
                    pad = 2
                    x, y = max(x - pad, 0), max(y - pad, 0)
                    w, h = w + 2 * pad, h + 2 * pad

                    if redaction_type == 'black':
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)

                    elif redaction_type == 'blur':
                        roi = image[y:y + h, x:x + w]
                        if roi.size > 0:
                            roi = cv2.GaussianBlur(roi, (23, 23), 30)
                            image[y:y + h, x:x + w] = roi

                    elif redaction_type == 'synthetic':
                        synthetic = ImageRedactor.generate_synthetic_data(label)
                        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), -1)
                        cv2.putText(image, synthetic, (x, y + h - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

        # Face redaction
        if redaction_level >= 100:
            image = ImageRedactor.redact_faces(image)

        output_path = os.path.join(os.path.dirname(file_path), "redacted_" + os.path.basename(file_path))
        cv2.imwrite(output_path, image)
        return output_path
