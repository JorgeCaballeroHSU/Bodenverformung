# Imports required libraries
from fastapi import FastAPI, Request, Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile

from database.database import *
from services.Importer import Importer
from pathlib import Path
import os


# Creates database according to defined schema
Schema()

# Creates FastAPI application
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

from fastapi import Request

@app.post("/api/upload-files")
async def upload_files(request: Request):

    form = await request.form()

    print("FORM CONTENTS:")
    print(form)

    return {"ok": True}

# @app.post("/api/upload-files")
# async def upload_files(files: list[UploadFile] = File(...)):

#     # creates an Importer object to handle the importation of the files
#     importer=Importer()

#     # initializes variables imported and failed to append according to the names of the variables
#     imported=[]
#     failed=[]

#     for uploaded_file in files:

#         temp_path=None

#         try:

#             with NamedTemporaryFile(delete=False, suffix=".xlsx" ) as tmp:

#                 content = await uploaded_file.read()
#                 tmp.write(content)

#                 temp_path = Path(tmp.name)

#             importer.import_file(temp_path)

#             imported.append(uploaded_file.filename)

#         except Exception as e:

#             failed.append(f"{uploaded_file.filename}: {e}")

#         finally:

#             if temp_path and temp_path.exists():
#                 os.remove(temp_path)

#     return {
#         "imported": imported,
#         "failed": failed,
#         "imported_count": len(imported),
#         "failed_count": len(failed)
#     }