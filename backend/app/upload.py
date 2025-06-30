from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import os
from model.PDFRedact import PDFRedactor
from model.DocRedact import DocumentRedactor
import base64
import cv2
from model.image_redaction import redact_faces_in_image
import numpy as np
router = APIRouter()

# Directory to store uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Supported file types
ALLOWED_FILE_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document","application/msword",
    "video/mp4", "video/x-matroska"
}

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    gradational_scale: int = Form(...),  # Assuming the scale is an integer
    redaction_method: str = Form(...)
):
    # Process file (redaction logic here)
    if file.content_type in ["image/jpeg", "image/jpg", "image/png"]:
        try:
            # Read file content
            file_content = await file.read()
            temp_path = os.path.join("temp", file.filename)

            # Save temporarily for processing
            os.makedirs("temp", exist_ok=True)
            with open(temp_path, "wb") as temp_file:
                temp_file.write(file_content)

            # Process the image using redact_faces_in_image
            redacted_image = redact_faces_in_image(temp_path)

            # Remove temp file after processing
            os.remove(temp_path)

            if redacted_image is not None:
                # Encode redacted image to Base64
                if file.content_type == "image/jpeg":
                    _, buffer = cv2.imencode('.jpeg', redacted_image)
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    return JSONResponse(content={
                        "redacted_image": image_base64,
                        "format": "jpeg"  # You can change this based on the format used
                    })
                elif file.content_type == "image/jpg":
                    _, buffer = cv2.imencode('.jpg', redacted_image)
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    return JSONResponse(content={
                        "redacted_image": image_base64,
                        "format": "jpg"  # You can change this based on the format used
                    })
                elif file.content_type == "image/png":
                    _, buffer = cv2.imencode('.png', redacted_image)
                    image_base64 = base64.b64encode(buffer).decode('utf-8')
                    return JSONResponse(content={
                        "redacted_image": image_base64,
                        "format": "png"  # You can change this based on the format used
                    })
            else:
                raise HTTPException(status_code=500, detail="Error during image redaction")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during image handling: {str(e)}")


    if file.content_type == "application/pdf":
        file_content = await file.read()
        temp_path = os.path.join("temp", file.filename)

        # Save temporarily for processing
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as temp_file:
            temp_file.write(file_content)

        # Initialize PDFRedactor and process
        redactor = PDFRedactor()
        try:
            processed_content = redactor.process_pdf(temp_path, gradational_scale, redaction_method[0])
            # Remove temp file
            os.remove(temp_path)

            # Convert processed content to base64
            pdf_base64 = base64.b64encode(processed_content.read()).decode('utf-8')
            return JSONResponse(content={"redacted_pdf": pdf_base64})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during redaction: {str(e)}")
        
    
    if file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file.content_type == "application/msword":
        file_content = await file.read()
        temp_path = os.path.join("temp", file.filename)
        print("file:",file.filename)
        # Save temporarily for processing
        os.makedirs("temp", exist_ok=True)
        with open(temp_path, "wb") as temp_file:
            temp_file.write(file_content)
            print("open:",file.filename)

        # Initialize PDFRedactor and process
        redactor = DocumentRedactor()
        try:
            print("beforeprocess:",file.filename)
            processed_content = redactor.redact_document(temp_path, gradational_scale, redaction_method[0])
            print("afterprocess:",file.filename)
            # Remove temp file
            os.remove(temp_path)

            # Convert processed content to base64
            doc_base64 = base64.b64encode(processed_content.read()).decode('utf-8')
            print("trycatch:",file.filename)
            return JSONResponse(content={"redacted_doc": doc_base64})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during redaction: {str(e)}")


    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Validate gradational scale
    if not (1 <= gradational_scale <= 100):
        raise HTTPException(status_code=400, detail="Invalid gradational scale. Must be between 1 and 100.")

    # Validate redaction method
    if redaction_method not in ["blurred", "blackout", "synthetic_data"]:
        raise HTTPException(status_code=400, detail="Invalid redaction method")

    # Save the file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    redaction_details = {
        "gradational_scale": gradational_scale,
        "redaction_method": redaction_method,
        "file_path": file_path,
        "processing": f"File saved and ready for {redaction_method} redaction.",
    }

    print("Redaction Details:", redaction_details)
    
    return redaction_details
