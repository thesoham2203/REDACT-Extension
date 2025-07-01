import fitz  # PyMuPDF
import spacy
import os
import re
from faker import Faker


class PDFRedactor:
    nlp = spacy.load("en_core_web_sm")  # Load once
    fake = Faker()

    @staticmethod
    def extract_text_and_coordinates(pdf_path):
        doc = fitz.open(pdf_path)
        text = ""
        blocks = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text("text")  # type: ignore[attr-defined]
            for block in page.get_text("dict")["blocks"]:  # type: ignore[attr-defined]
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

        patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            'PHONE': r'\b(\+?[0-9]{1,3})?[-. ]?(\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4})\b',
            'IPV4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'IPV6': r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b',
        }

        for label, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if label == 'PHONE':
                for phone in matches:
                    sensitive_data.append((0, 0, phone[1], label))  # phone[1] = number part
            else:
                for match in matches:
                    sensitive_data.append((0, 0, match, label))

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
    def redact(file_path: str, redaction_type: str, redaction_level: int) -> str:
        text, blocks = PDFRedactor.extract_text_and_coordinates(file_path)
        sensitive_data = PDFRedactor.extract_sensitive_data(text)
        doc = fitz.open(file_path)

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

        redactions_by_page = {}

        for _, _, sensitive_text, label in filtered_data:
            target = sensitive_text.strip().lower()
            for block in blocks:
                if target in block["text"].strip().lower():
                    page_num = block["page_num"]
                    bbox = tuple(block["bbox"])
                    if page_num not in redactions_by_page:
                        redactions_by_page[page_num] = []
                    redactions_by_page[page_num].append((bbox, label))

        for page_num, items in redactions_by_page.items():
            page = doc.load_page(page_num)
            for bbox, label in items:
                rect = fitz.Rect(*bbox)
                if redaction_type == 'black':
                    page.add_redact_annot(rect, fill=(0, 0, 0))
                elif redaction_type == 'blur':
                    page.draw_rect(rect, color=(169/255, 169/255, 169/255, 0.5), fill=True)  # gray # type: ignore[attr-defined]
                elif redaction_type == 'synthetic':
                    page.draw_rect(rect, color=(1, 1, 1), fill=True)  # white background # type: ignore[attr-defined]
                    synthetic = PDFRedactor.generate_synthetic_data(label)
                    page.insert_text((bbox[0], bbox[3] - 5), synthetic, fontsize=12, color=(0, 0, 0))  # black text # type: ignore[attr-defined]

            if redaction_type == 'black':
                page.apply_redactions()  # type: ignore[attr-defined]

        output_path = os.path.join(os.path.dirname(file_path), "redacted_" + os.path.basename(file_path))
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        return output_path
