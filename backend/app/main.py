# backend/app/main.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.com import handle_file
import shutil
import tempfile
import os

app = FastAPI()

# Allow only your extension to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["chrome-extension://<YOUR-ID>"] before publishing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/redact")
async def redact_file(
    file: UploadFile = File(...),
    redaction_type: str = Form(...),
    redaction_level: int = Form(...),
):
    with tempfile.TemporaryDirectory() as tmpdirname:
        file_path = os.path.join(tmpdirname, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        redacted_path = handle_file(file_path, redaction_type, redaction_level)

        return FileResponse(
            path=redacted_path,
            filename=os.path.basename(redacted_path),
            media_type="application/octet-stream",
        )
