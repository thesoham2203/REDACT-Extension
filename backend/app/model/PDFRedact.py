# backend/app/model/PDFRedactor.py

import fitz  # PyMuPDF
import spacy
import os
import re
from faker import Faker
from io import BytesIO


class PDFRedactor:
    nlp = spacy.load("en_core_web_sm")  # class-level load
    fake = Faker()

    @staticmethod
    def extract_text_and_coordinates(pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        blocks = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")
            for block in page.get_text("dict")["blocks"]:
                if block['type'] == 0:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            blocks.append({
                                "text": span["text"],
                                "bbox": span["bbox"],
                                "page_num": page_num,
                            })
        return text, blocks

    @staticmethod
    def extract_sensitive_data(text):
        doc = PDFRedactor.nlp(text)
        sensitive_data = []

        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'GPE', 'ORG', 'DATE', 'MONEY']:
                sensitive_data.append((ent.start, ent.end, ent.text, ent.label_))

        # Regex for common PII
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        phone_pattern = r'\b(\+?[0-9]{1,3})?[-. ]?(\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4})\b'
        ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ipv6_pattern = r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b'

        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        ipv4s = re.findall(ipv4_pattern, text)
        ipv6s = re.findall(ipv6_pattern, text)

        for email in emails:
            sensitive_data.append((0, 0, email, 'EMAIL'))
        for phone in phones:
            sensitive_data.append((0, 0, phone[1], 'PHONE'))
        for ipv4 in ipv4s:
            sensitive_data.append((0, 0, ipv4, 'IPV4'))
        for ipv6 in ipv6s:
            sensitive_data.append((0, 0, ipv6, 'IPV6'))

        return sensitive_data

    @staticmethod
    def generate_synthetic_data(label):
        fake = PDFRedactor.fake
        return {
            'EMAIL': fake.email(),
            'PHONE': fake.phone_number(),
            'PERSON': fake.name(),
            'GPE': fake.city(),
            'ORG': fake.company(),
            'DATE': fake.date(),
            'MONEY': fake.pricetag(),
            'IPV4': fake.ipv4(),
            'IPV6': fake.ipv6()
        }.get(label, "SYNTHETIC_DATA")

    @staticmethod
    def redact_blackout(page, bbox):
        rect = fitz.Rect(*bbox)
        page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()

    @staticmethod
    def redact_blur(page, bbox):
        rect = fitz.Rect(*bbox)
        page.draw_rect(rect, color=(169/255, 169/255, 169/255, 0.5), fill=True)

    @staticmethod
    def replace_with_synthetic_data(page, bbox, label):
        synthetic_text = PDFRedactor.generate_synthetic_data(label)
        rect = fitz.Rect(*bbox)
        page.draw_rect(rect, color=(1, 1, 1), fill=True)
        page.insert_text((bbox[0], bbox[3] - 5), synthetic_text, fontsize=12, color=(0, 0, 0))

    @staticmethod
    def redact(file_path: str, redaction_type: str, redaction_level: int) -> str:
        text, blocks = PDFRedactor.extract_text_and_coordinates(file_path)
        sensitive_data = PDFRedactor.extract_sensitive_data(text)

        doc = fitz.open(file_path)
        entities_to_redact = set()

        # Redaction levels
        if redaction_level >= 25:
            entities_to_redact.update(['EMAIL', 'PHONE', 'IPV4', 'IPV6'])
        if redaction_level >= 50:
            entities_to_redact.update(['DATE'])
        if redaction_level >= 75:
            entities_to_redact.update(['MONEY', 'ORG', 'GPE'])
        if redaction_level == 100:
            entities_to_redact.update(['PERSON'])

        filtered_data = [data for data in sensitive_data if data[3] in entities_to_redact]

        for _, _, sensitive_text, label in filtered_data:
            for block in blocks:
                if sensitive_text in block["text"]:
                    page = doc.load_page(block["page_num"])
                    bbox = block["bbox"]
                    if redaction_type == 'black':
                        PDFRedactor.redact_blackout(page, bbox)
                    elif redaction_type == 'blur':
                        PDFRedactor.redact_blur(page, bbox)
                    elif redaction_type == 'synthetic':
                        PDFRedactor.replace_with_synthetic_data(page, bbox, label)

        output_path = os.path.join(os.path.dirname(file_path), "redacted_" + os.path.basename(file_path))
        doc.save(output_path)
        return output_path
