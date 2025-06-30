import spacy
import re
import os
from faker import Faker
from docx import Document

class DOCRedactor:
    nlp = spacy.load("en_core_web_sm")
    fake = Faker()

    @staticmethod
    def extract_text_and_coordinates(docx_path):
        doc = Document(docx_path)
        text = ""
        paragraphs = []

        for para_num, para in enumerate(doc.paragraphs):
            text += para.text + "\n"
            paragraphs.append({"text": para.text, "para_num": para_num})

        return text, paragraphs

    @staticmethod
    def extract_sensitive_data(text):
        doc = DOCRedactor.nlp(text)
        sensitive_data = []

        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'GPE', 'ORG', 'DATE', 'MONEY']:
                sensitive_data.append((ent.start, ent.end, ent.text, ent.label_))

        patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            'PHONE': r'\b(\+?[0-9]{1,3})?[-. ]?(\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4})\b',
            'IPV4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'IPV6': r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b',
            'TIME': r'\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b',
        }

        for label, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                value = match if isinstance(match, str) else ":".join(match)
                sensitive_data.append((0, 0, value, label))

        return sensitive_data

    @staticmethod
    def generate_synthetic_data(label):
        fake = DOCRedactor.fake
        return {
            'EMAIL': fake.email(),
            'PHONE': fake.phone_number(),
            'PERSON': fake.name(),
            'GPE': fake.city(),
            'ORG': fake.company(),
            'DATE': fake.date(),
            'MONEY': fake.pricetag(),
            'IPV4': fake.ipv4(),
            'IPV6': fake.ipv6(),
            'TIME': fake.time()
        }.get(label, "SYNTHETIC_DATA")

    @staticmethod
    def redact_blackout(obj, sensitive_text):
        obj.text = obj.text.replace(sensitive_text, "█" * len(sensitive_text))

    @staticmethod
    def redact_blur(obj, sensitive_text):
        obj.text = obj.text.replace(sensitive_text, "-" * len(sensitive_text))

    @staticmethod
    def replace_with_synthetic_data(obj, sensitive_text, label):
        synthetic = DOCRedactor.generate_synthetic_data(label)
        obj.text = obj.text.replace(sensitive_text, synthetic)

    @staticmethod
    def redact_table(table, sensitive_data, action):
        for row in table.rows:
            for cell in row.cells:
                for _, _, sensitive_text, label in sensitive_data:
                    if sensitive_text in cell.text:
                        if action == 'black':
                            DOCRedactor.redact_blackout(cell, sensitive_text)
                        elif action == 'blur':
                            DOCRedactor.redact_blur(cell, sensitive_text)
                        elif action == 'synthetic':
                            DOCRedactor.replace_with_synthetic_data(cell, sensitive_text, label)

    @staticmethod
    def redact(file_path: str, redaction_type: str, redaction_level: int) -> str:
        doc_text, _ = DOCRedactor.extract_text_and_coordinates(file_path)
        sensitive_data = DOCRedactor.extract_sensitive_data(doc_text)
        if not sensitive_data:
            return file_path  # no changes needed

        doc = Document(file_path)
        entities_to_redact = set()

        if redaction_level >= 25:
            entities_to_redact.update(['EMAIL', 'PHONE', 'IPV4', 'IPV6'])
        if redaction_level >= 50:
            entities_to_redact.update(['DATE'])
        if redaction_level >= 75:
            entities_to_redact.update(['MONEY', 'ORG', 'GPE'])
        if redaction_level == 100:
            entities_to_redact.update(['PERSON'])

        filtered_data = [d for d in sensitive_data if d[3] in entities_to_redact]

        for _, _, sensitive_text, label in filtered_data:
            for para in doc.paragraphs:
                if sensitive_text in para.text:
                    if redaction_type == 'black':
                        DOCRedactor.redact_blackout(para, sensitive_text)
                    elif redaction_type == 'blur':
                        DOCRedactor.redact_blur(para, sensitive_text)
                    elif redaction_type == 'synthetic':
                        DOCRedactor.replace_with_synthetic_data(para, sensitive_text, label)

        for table in doc.tables:
            DOCRedactor.redact_table(table, filtered_data, redaction_type)

        for section in doc.sections:
            for header in section.header.paragraphs:
                for _, _, sensitive_text, label in filtered_data:
                    if sensitive_text in header.text:
                        if redaction_type == 'black':
                            DOCRedactor.redact_blackout(header, sensitive_text)
                        elif redaction_type == 'blur':
                            DOCRedactor.redact_blur(header, sensitive_text)
                        elif redaction_type == 'synthetic':
                            DOCRedactor.replace_with_synthetic_data(header, sensitive_text, label)

        output_path = file_path.replace('.docx', '_redacted.docx')
        doc.save(output_path)
        return output_path
