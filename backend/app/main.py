from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.com import handle_file
import shutil
import tempfile
import os

app = FastAPI()

# ✅ Allow requests from Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],  # lock to your extension ID later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def hello():
    return {"message": "Backend is up"}

@app.post("/redact")
async def redact_file(
    file: UploadFile = File(...),
    redaction_type: str = Form(...),
    redaction_level: int = Form(...),
):
    with tempfile.TemporaryDirectory() as tmpdirname:
        original_filename = file.filename or "uploaded_file"
        file_path = os.path.join(tmpdirname, original_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 🧠 Redact inside temp folder
        redacted_path = handle_file(file_path, redaction_type, redaction_level)

        # ✅ Move redacted file OUTSIDE tempdir before it gets deleted
        output_dir = "redacted_files"
        os.makedirs(output_dir, exist_ok=True)

        final_path = os.path.join(output_dir, os.path.basename(redacted_path))
        shutil.copyfile(redacted_path, final_path)

    return FileResponse(
        path=final_path,
        filename=os.path.basename(final_path),
        media_type="application/octet-stream",
    )
