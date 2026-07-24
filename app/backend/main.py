# Imports required libraries
from fastapi import FastAPI, Request, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database.database import *
from services.Importer import Importer
from pathlib import Path

# Create database according to defined schema
Schema()

# Create FastAPI application
app = FastAPI()

# defines directories base and front end directory
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app.mount(
    "/frontend",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="frontend"
)

# HTML templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/database")
async def database_page():
    return FileResponse(str(FRONTEND_DIR / "database.html"))


@app.get("/training")
async def training_page():
    return FileResponse(str(FRONTEND_DIR / "training.html"))


@app.get("/prediction")
async def prediction_page():
    return FileResponse(str(FRONTEND_DIR / "prediction.html"))

@app.post("/api/check-files")
async def check_files(data: dict = Body(...)):

    filenames = data.get("files", [])

    db = Database()
    db.openConnection()

    uploaded_files = []

    try:

        for filename in filenames:

            result = db.fetchInfo(
                """
                SELECT filename
                FROM files
                WHERE filename = ?
                """,
                (filename,)
            )

            if result:
                uploaded_files.append(filename)

    finally:

        db.closeConnection()

    return {
        "uploaded": uploaded_files
    }


@app.post("/api/upload-files")
async def upload_files(data: dict = Body(...)):

    files = data.get("files", [])

    importer = Importer()

    imported = []
    failed = []

    for file_path in files:

        try:

            importer.import_file(file_path)

            imported.append(file_path)

        except Exception as e:

            failed.append({
                "file": file_path,
                "error": str(e)
            })

    return {
        "imported": imported,
        "failed": failed,
        "imported_count": len(imported),
        "failed_count": len(failed)
    }