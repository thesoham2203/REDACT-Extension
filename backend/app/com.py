# backend/app/com.py
import os
from app.model.PDFRedact import PDFRedactor
from app.model.IMGRedact import ImageRedactor
from app.model.DOCRedact import DOCRedactor


def handle_file(file_path, redaction_type, redaction_level):
    ext = os.path.splitext(file_path)[-1].lower()

    if ext in [".pdf"]:
        return PDFRedactor.redact(file_path, redaction_type, redaction_level)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return ImageRedactor.redact(file_path, redaction_type, redaction_level)
    elif ext in [".doc", ".docx"]:
        return DOCRedactor.redact(file_path, redaction_type, redaction_level)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
