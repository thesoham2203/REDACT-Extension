
# 🕵️‍♂️ REDACT — Privacy-First Redaction Chrome Extension

![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)]
![Platform](https://img.shields.io/badge/platform-Chromium%20Extension-yellow?logo=googlechrome)

**REDACT** is a secure and easy-to-use Chrome Extension that performs redaction, masking, and anonymization of sensitive data—particularly Personally Identifiable Information (PII)—from documents. Built for privacy, it supports PDFs, images, and Word documents directly from your browser using a FastAPI Python backend.

---

## 📦 Project Structure

```

redact-chrome-extension/
│
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── main.py           # FastAPI app, handles /redact endpoint
│   │   ├── com.py            # Dispatcher: picks correct redactor based on file type
│   │   ├── model/            # Redaction logic for each file format
│   │   │   ├── PDFRedactor.py
│   │   │   ├── ImageRedactor.py
│   │   │   ├── DOCRedactor.py
│   │   │   └── ...
│   │   └── utils.py          # Temporary file handling, cleanup, CORS config
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Dockerized backend for deployment
│   └── .env.example          # Sample environment variable file
│
├── extension/                # Chrome Extension frontend
│   ├── manifest.json         # Chrome extension config (MV3)
│   ├── popup.html            # UI interface
│   ├── popup.css             # Styling
│   ├── popup.js              # Logic to send files to FastAPI backend
│   └── icons/                # 16x16, 48x48, 128x128 icons
│
├── docs/                     # Documentation & diagrams
│   └── architecture.md
│
├── .gitignore                # Ignored files & folders
├── README.md                 # You're here!
└── LICENSE                   # MIT License

````

---

## 🧠 System Architecture

```text
+-------------------------+         +--------------------------+
|     Chrome Extension    |         |   FastAPI Python Backend |
| (popup.html + popup.js) |         |      (Uvicorn server)    |
+------------+------------+         +------------+-------------+
             |                                |
             |  POST file + type + level      |
             |------------------------------->|
             |                                |
             |      com.py dispatches         |
             |    to PDF/Image/DOC script     |
             |                                |
             |  <----- Returns redacted file  |
             |                                |
+------------v------------+         +------------v-------------+
|   Download Redacted     |         |     Temp Files Auto      |
|      File (Blob)        |         |        Deleted           |
+-------------------------+         +--------------------------+
````

---

## 🚀 Features

* 🔐 **PII Protection**: Redact names, phone numbers, emails, faces, and more
* 📄 **File Support**: PDFs, images (JPG/PNG), DOCX (Word); more coming soon
* 🌐 **Chrome Native**: No need to leave the browser
* ⚡ **FastAPI Backend**: Ultra-light, async processing using Python
* 🧹 **Ephemeral Storage**: Files are deleted after processing
* 🧠 **Smart Redaction**: Configurable redaction level (e.g. 25%, 50%, 75%, 100%)
* 🔓 **Open Access**: No login, no tracking

---

## ⚙️ Getting Started

### 🔧 Backend Setup (Python 3.10+)

```bash
# Navigate to backend/
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run FastAPI with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, your API will be available at: `http://localhost:8000/redact`

---

### 🌐 Chrome Extension Setup

1. Navigate to `chrome://extensions`
2. Enable **Developer Mode**
3. Click **Load unpacked**
4. Select the `extension/` folder

Now your extension will be active in the Chrome toolbar.

---

## 📤 Upload Flow

1. Select a file using the extension popup
2. Choose redaction **level** (0% → 100%)
3. Choose redaction **type** (e.g. blackout, blur, synthetic)
4. Click **Redact**
5. A redacted version will be downloaded instantly

---

## 🧪 Testing Tips

* Use test documents with **mock PII** (names, emails, Aadhaar numbers)
* Run backend with `--reload` during development for auto-restart
* Verify extension behavior in **Incognito mode** too

---

## 🛠 Tech Stack

| Layer     | Technology                    |
| --------- | ----------------------------- |
| Frontend  | HTML, CSS, JavaScript (MV3)   |
| Backend   | Python 3.10, FastAPI, Uvicorn |
| Redaction | OpenCV, spaCy, PyMuPDF, etc.  |
| Packaging | Docker                        |
| Storage   | Ephemeral + tempfile-based    |

---

## 🧹 Cleanup & Security

* All uploaded files are saved in a temp folder and deleted immediately after processing
* CORS is restricted to the extension only
* No data is stored or logged

---

## 📚 License

This project is licensed under the GNU GENERAL PUBLIC LICENSE v3

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Push to your branch (`git push origin feat/my-feature`)
4. Create a Pull Request 🚀



