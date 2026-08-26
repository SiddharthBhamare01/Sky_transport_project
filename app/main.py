import mimetypes
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .extractor import ExtractionError, extract_from_bytes
from .sample_mode import SAMPLES

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
SAMPLES_DIR = BASE_DIR / "samples"

ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg"}

app = FastAPI(title="Shipment Document Data Extractor")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://sky-transport-project.*\.vercel\.app",
    allow_origins=["http://localhost:8811", "http://127.0.0.1:8811"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.get("/api/config")
def get_config():
    return {"has_api_key": config.has_api_key()}


@app.get("/api/samples")
def list_samples():
    return [
        {"sample_id": sample_id, "display_name": s["display_name"], "filename": s["filename"]}
        for sample_id, s in SAMPLES.items()
    ]


@app.get("/samples/{filename}")
def get_sample_file(filename: str):
    path = (SAMPLES_DIR / filename).resolve()
    if SAMPLES_DIR.resolve() not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Sample not found")
    return FileResponse(path)


@app.post("/api/extract")
async def extract(file: UploadFile | None = File(None), sample_id: str | None = None):
    if sample_id:
        sample = SAMPLES.get(sample_id)
        if not sample:
            raise HTTPException(status_code=404, detail="Unknown sample_id")
        return {"fields": sample["fields"], "source": "sample"}

    if file is None:
        raise HTTPException(status_code=400, detail="Provide a file upload or sample_id")

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0]
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime_type}")

    if file.size is not None and file.size > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (10MB limit)")

    file_bytes = await file.read()
    if len(file_bytes) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (10MB limit)")

    try:
        fields = extract_from_bytes(file_bytes, mime_type)
    except ExtractionError as e:
        return JSONResponse({"error": e.kind, "message": e.message}, status_code=200)

    return {"fields": fields, "source": "live"}


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
