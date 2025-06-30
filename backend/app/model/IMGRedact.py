import cv2
import pytesseract
import re
import os
import numpy as np
from faker import Faker

class ImageRedactor:
    fake = Faker()

    @staticmethod
    def extract_sensitive_data(text):
        patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            'PHONE': r'\b(\+?[0-9]{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
            'AADHAAR': r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
            'PAN': r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
            'DATE': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
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
            'DATE': ImageRedactor.fake.date()
        }.get(label, "SYNTHETIC")

    @staticmethod
    def redact(file_path: str, redaction_type: str, redaction_level: int) -> str:
        image = cv2.imread(file_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # OCR
        custom_config = r'--oem 3 --psm 6'
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config=custom_config)
        raw_text = " ".join(data['text'])

        # Extract sensitive content
        sensitive_items = ImageRedactor.extract_sensitive_data(raw_text)

        # Apply redactions
        for i, word in enumerate(data['text']):
            for sensitive_text, label in sensitive_items:
                if sensitive_text in word:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

                    if redaction_type == 'black':
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 0), -1)

                    elif redaction_type == 'blur':
                        roi = image[y:y+h, x:x+w]
                        if roi.size > 0:
                            roi = cv2.GaussianBlur(roi, (23, 23), 30)
                            image[y:y+h, x:x+w] = roi

                    elif redaction_type == 'synthetic':
                        synthetic_text = ImageRedactor.generate_synthetic_data(label)
                        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), -1)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        font_scale = 0.5
                        thickness = 1
                        color = (0, 0, 0)
                        cv2.putText(image, synthetic_text, (x, y + h - 5), font, font_scale, color, thickness, cv2.LINE_AA)

        # Save the redacted image
        output_path = os.path.join(os.path.dirname(file_path), "redacted_" + os.path.basename(file_path))
        cv2.imwrite(output_path, image)
        return output_path
