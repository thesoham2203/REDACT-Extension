import json
import sys
import base64
from pathlib import Path
from model.PDFRedact import PDFRedactor
from model.DOCRedact import DOCRedactor    # Placeholder for text file processing
from model.XelRedactor import FileRedactor  # Placeholder for Excel file processing
from model.PresentRedactor import PresentationRedactor  # Placeholder for Excel file processing

def encode_file_to_base64(file_path):
    """Encodes a file to base64 format."""
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

def process_file(file_path, redact_level, action, file_type):
    """Process the file based on its type and apply redaction."""
    try:
        if file_type == "pdf":
            pdf_redactor = PDFRedactor()  # Instantiate the PDFRedactor class
            output_path = pdf_redactor.process_pdf(file_path, redact_level, action)
        # elif file_type in ["jpg", "jpeg", "png"]:
        #     image_redactor = ImageRedactor()  # Instantiate the ImageRedactor class
        #     output_path = image_redactor.process_image(file_path, redact_level, action)
        elif file_type in ["txt", "doc", "docx"]:
            text_redactor = DOCRedactor()  # Instantiate the TextRedactor class
            output_path = text_redactor.process_text(file_path, redact_level, action)
        elif file_type in ["xlsx", "xls", "log", "csv"]:
            excel_redactor = FileRedactor()  # Instantiate the ExcelRedactor class
            output_path = excel_redactor.process_excel(file_path, redact_level, action)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return output_path

    except Exception as e:
        # If there is an error in redaction, raise an exception
        raise ValueError(f"Redaction failed: {e}")

def main():
    try:
        input_data = sys.argv[1]  # Ensure JSON is passed correctly
        if not input_data:
            raise ValueError("No input data provided.")

        input_data = json.loads(input_data)
        file_path = input_data.get("file_path")
        redaction_level = input_data.get("redaction_level")
        redaction_type = input_data.get("redaction_type")

        if not file_path or not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type based on file extension
        file_extension = Path(file_path).suffix.lower().lstrip(".")

        # Process the file and get the redacted content
        output_path = process_file(file_path, redaction_level, redaction_type, file_extension)

        return output_path
        # # Encode the redacted file to base64
        # base64_content = encode_file_to_base64(output_path)

        print(json.dumps({"success": True, "file_type": f"application/{file_extension}", "preview": base64_content}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    main()
