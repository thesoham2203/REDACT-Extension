import cv2
import pytesseract
import re
import os
import numpy as np
from faker import Faker
import dlib
import pathlib

class ImageRedactor:
    fake = Faker()

    # Load Dlib's face detector and 68-point landmark model
    face_detector = dlib.get_frontal_face_detector()
    model_path = pathlib.Path(__file__).parent / "shape_predictor_68_face_landmarks.dat"
    landmark_predictor = dlib.shape_predictor(str(model_path))


    @staticmethod
    def extract_sensitive_data(text):
        patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            'PHONE': r'\b(\+?[0-9]{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
            'AADHAAR': r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
            'PAN': r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
            'DATE': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
        }

        matches = []
        for label, pattern in patterns.items():
            found = re.findall(pattern, text)
            for item in found:
                value = item if isinstance(item, str) else " ".join(item)
                matches.append((value.strip(), label))
        return matches

    @staticmethod
    def generate_synthetic_data(label):
        return {
            'EMAIL': ImageRedactor.fake.email(),
            'PHONE': ImageRedactor.fake.phone_number(),
            'AADHAAR': ImageRedactor.fake.bothify(text='#### #### ####'),
            'PAN': ImageRedactor.fake.bothify(text='?????####?'),
            'DATE': ImageRedactor.fake.date()
        }.get(label, "SYNTHETIC")

    @staticmethod
    def blur_faces(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = ImageRedactor.face_detector(gray, 1)

        for face in faces:
            landmarks = ImageRedactor.landmark_predictor(gray, face)
            points = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(68)]
            hull = cv2.convexHull(np.array(points))
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillConvexPoly(mask, hull, 255)
            blurred = cv2.GaussianBlur(image, (55, 55), 30)
            image = np.where(mask[:, :, None] == 255, blurred, image)
        return image

    @staticmethod
    def redact(file_path: str, redaction_type: str, redaction_level: int) -> str:
        image = cv2.imread(file_path)
        image = ImageRedactor.blur_faces(image)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        config = r'--oem 3 --psm 6'
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config=config)
        text = " ".join(data['text'])

        sensitive_items = ImageRedactor.extract_sensitive_data(text)
        redacted_texts = []

        for i, word in enumerate(data['text']):
            conf = int(data['conf'][i])
            if not word.strip() or conf < 60:
                continue

            for sensitive_text, label in sensitive_items:
                if sensitive_text in word or word in sensitive_text:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    pad = 2
                    x, y = max(x - pad, 0), max(y - pad, 0)
                    w, h = w + 2 * pad, h + 2 * pad

                    redacted_texts.append((word, label))

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

        print("🔍 Redacted items:")
        for word, label in redacted_texts:
            print(f" - [{label}] {word}")

        output_path = os.path.join(os.path.dirname(file_path), "redacted_" + os.path.basename(file_path))
        cv2.imwrite(output_path, image)
        return output_path
