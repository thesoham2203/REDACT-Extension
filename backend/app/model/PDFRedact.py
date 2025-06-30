import fitz  # PyMuPDF
import spacy
import os
import re
from faker import Faker
from io import BytesIO

class PDFRedactor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")  # Load the Spacy NLP model
        self.fake = Faker()  # Faker for generating synthetic data

    def extract_text_and_coordinates(self, pdf_path):
        """Extract text and coordinates from the PDF."""
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

    def extract_sensitive_data(self, text):
        """Extract sensitive data (e.g., email, phone, IP addresses) from the text."""
        doc = self.nlp(text)
        sensitive_data = []

        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'GPE', 'ORG', 'DATE', 'MONEY']:
                sensitive_data.append((ent.start, ent.end, ent.text, ent.label_))

        # Regular expressions for more sensitive data
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        phone_pattern = r'\b(\+?[0-9]{1,3})?[-. ]?(\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4})\b'
        ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ipv6_pattern = r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b'

        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        ipv4s = re.findall(ipv4_pattern, text)
        ipv6s = re.findall(ipv6_pattern, text)

        # Add sensitive data from regular expressions
        for email in emails:
            sensitive_data.append((0, 0, email, 'EMAIL'))
        for phone in phones:
            sensitive_data.append((0, 0, phone[1], 'PHONE'))
        for ipv4 in ipv4s:
            sensitive_data.append((0, 0, ipv4, 'IPV4'))
        for ipv6 in ipv6s:
            sensitive_data.append((0, 0, ipv6, 'IPV6'))

        return sensitive_data

    def generate_synthetic_data(self, label):
        """Generate synthetic data based on the label."""
        if label == 'EMAIL':
            return self.fake.email()
        elif label == 'PHONE':
            return self.fake.phone_number()
        elif label == 'PERSON':
            return self.fake.name()
        elif label == 'GPE':
            return self.fake.city()
        elif label == 'ORG':
            return self.fake.company()
        elif label == 'DATE':
            return self.fake.date()
        elif label == 'MONEY':
            return self.fake.pricetag()
        elif label == 'IPV4':
            return self.fake.ipv4()
        elif label == 'IPV6':
            return self.fake.ipv6()
        else:
            return "SYNTHETIC_DATA"

    def redact_blackout(self, page, bbox):
        """Redact content by blacking it out."""
        x0, y0, x1, y1 = bbox
        rect = fitz.Rect(x0, y0, x1, y1)
        page.add_redact_annot(rect, fill=(0, 0, 0))  # Black fill
        page.apply_redactions()

    def redact_blur(self, page, bbox):
        """Redact content by blurring it."""
        x0, y0, x1, y1 = bbox
        rect = fitz.Rect(x0, y0, x1, y1)
        blur_color = (169 / 255, 169 / 255, 169 / 255, 0.5)  # Gray blur color
        page.draw_rect(rect, color=blur_color, fill=True)

    def replace_with_synthetic_data(self, page, bbox, label):
        """Replace sensitive data with synthetic data."""
        synthetic_text = self.generate_synthetic_data(label)
        x0, y0, x1, y1 = bbox
        rect = fitz.Rect(x0, y0, x1, y1)
        page.draw_rect(rect, color=(1, 1, 1), fill=True)  # White fill
        page.insert_text((x0, y1 - 5), synthetic_text, fontsize=12, color=(0, 0, 0))

    def process_pdf(self, pdf_path, redact_level, action):
        """Process the PDF file to apply redactions."""
        pdf_text, blocks = self.extract_text_and_coordinates(pdf_path)
        sensitive_data = self.extract_sensitive_data(pdf_text)

        if not sensitive_data:
            print("No sensitive data found.")
            return

        doc = fitz.open(pdf_path)
        entities_to_redact = set()

        # Adjust redaction levels based on sensitivity
        if redact_level >= "25":
            entities_to_redact.update(['EMAIL', 'PHONE', 'IPV4', 'IPV6'])
        if redact_level >= "50":
            entities_to_redact.update(['DATE'])
        if redact_level >= "75":
            entities_to_redact.update(['MONEY', 'ORG', 'GPE'])  # Redact city names (GPE)
        if redact_level == "100":
            entities_to_redact.update(['PERSON'])

        # Filter the sensitive data based on redact level
        filtered_data = [data for data in sensitive_data if data[3] in entities_to_redact]

        for _, _, sensitive_text, label in filtered_data:
            # Iterate through all pages and check for the matching block
            for block in blocks:
                if sensitive_text in block["text"]:
                    bbox = block["bbox"]
                    page_num = block["page_num"]
                    page = doc.load_page(page_num)

                    if action == 'blur':
                        self.redact_blur(page, bbox)
                    elif action == 'black':
                        self.redact_blackout(page, bbox)
                    elif action == 'synthetic':
                        self.replace_with_synthetic_data(page, bbox, label)

        redacted_pdf_path = os.path.join(os.path.dirname(pdf_path), "redacted_" + os.path.basename(pdf_path))
        doc.save(redacted_pdf_path)
        return redacted_pdf_path
