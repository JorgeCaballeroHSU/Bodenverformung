# Imports required libraries
from fastapi import FastAPI, Request, Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile

from database.database import *
from services.Importer import Importer, calculate_sha256 
from pathlib import Path
import os
import numpy as np


# Creates database according to defined schema
Schema()

# Creates FastAPI application
app = FastAPI()

# defines directories base and front end directory
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
print(FRONTEND_DIR)
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

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

            result = db.fetchInfo("""SELECT filename FROM files WHERE sha256 = ?""", (calculate_sha256(filename),))

            if result:

                uploaded_files.append(filename)

    finally:

        db.closeConnection()

    return {"uploaded": uploaded_files}

@app.post("/api/upload-files")
async def upload_files(files: list[UploadFile] = File(...)):

    # creates an Importer object to handle the importation of the files
    importer=Importer()

    # initializes variables imported and failed to append according to the names of the variables
    imported=[]
    failed=[]

    for uploaded_file in files:

        temp_path=None

        try:

            with NamedTemporaryFile(delete=False,suffix=".xlsx") as tmp:

                content = await uploaded_file.read()
                tmp.write(content)

                temp_path = Path(tmp.name)

            importer.import_file(temp_path,uploaded_file.filename)

            imported.append(uploaded_file.filename)

        except Exception as e:

            failed.append(f"{uploaded_file.filename}: {e}")

        finally:

            if temp_path and temp_path.exists():
                os.remove(temp_path)

    return {
        "imported": imported,
        "failed": failed,
        "imported_count": len(imported),
        "failed_count": len(failed)
    }

# Database summary
@app.get("/api/database-summary")
async def database_summary():

    db = Database()
    db.openConnection()

    try:

        total_tests = db.fetchInfo(
            "SELECT COUNT(*) as value FROM tests"
        )[0]["value"]

        total_measurements = db.fetchInfo(
            "SELECT COUNT(*) as value FROM measurements"
        )[0]["value"]

        avg_stress = db.fetchInfo(
            """
            SELECT AVG(stress_kpa) as value
            FROM measurements
            """
        )[0]["value"]

        max_force = db.fetchInfo(
            """
            SELECT MAX(force_kn) as value
            FROM measurements
            """
        )[0]["value"]

        return {
            "total_tests": total_tests,
            "total_measurements": total_measurements,
            "avg_stress": avg_stress or 0,
            "max_force": max_force or 0
        }

    finally:
        db.closeConnection()

# stress vs strain
@app.get("/api/stress-strain")
async def stress_strain():

    db = Database()
    db.openConnection()

    try:

        data = db.fetchInfo(
            """SELECT strain_pct, stress_kpa FROM measurements WHERE strain_pct IS NOT NULL AND stress_kpa IS NOT NULL
            ORDER BY RANDOM() LIMIT 20000"""
        )

        return {
            "strain_pct":[row["strain_pct"] for row in data],
            "stress_kpa":[row["stress_kpa"] for row in data]
        }

    finally:
        db.closeConnection()

# Force vs Displacement
@app.get("/api/force-displacement")
async def force_displacement():

    db = Database()
    db.openConnection()

    try:

        data = db.fetchInfo(
            """
            SELECT displacement_mm,
                   force_kn
            FROM measurements
            WHERE displacement_mm IS NOT NULL
              AND force_kn IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 20000
            """
        )

        return {
            "displacement_mm":
                [row["displacement_mm"] for row in data],
            "force_kn":
                [row["force_kn"] for row in data]
        }

    finally:
        db.closeConnection()

# Stress Histogram
@app.get("/api/stress-histogram")
async def stress_histogram():

    db = Database()
    db.openConnection()

    try:

        data = db.fetchInfo(
            """
            SELECT stress_kpa
            FROM measurements
            WHERE stress_kpa IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 100000
            """
        )

        return {
            "stress_kpa":
                [row["stress_kpa"] for row in data]
        }

    finally:
        db.closeConnection()

# strain histogram
@app.get("/api/strain-histogram")
async def strain_histogram():

    db = Database()
    db.openConnection()

    try:

        data = db.fetchInfo(
            """
            SELECT strain_pct
            FROM measurements
            WHERE strain_pct IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 100000
            """
        )

        return {
            "strain_pct":
                [row["strain_pct"] for row in data]
        }

    finally:
        db.closeConnection()

# correlation matrix
@app.get("/api/correlation")
async def correlation_matrix():

    db = Database()
    db.openConnection()

    try:

        rows = db.fetchInfo(
            """
            SELECT
                force_kn,
                displacement_mm,
                sample_height_mm,
                strain_ratio,
                strain_pct,
                stress_kpa
            FROM measurements
            WHERE
                force_kn IS NOT NULL
                AND displacement_mm IS NOT NULL
                AND sample_height_mm IS NOT NULL
                AND strain_ratio IS NOT NULL
                AND strain_pct IS NOT NULL
                AND stress_kpa IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 20000
            """
        )

        columns = [
            "force_kn",
            "displacement_mm",
            "sample_height_mm",
            "strain_ratio",
            "strain_pct",
            "stress_kpa"
        ]

        matrix = np.array(
            [
                [row[col] for col in columns]
                for row in rows
            ]
        )

        corr = np.corrcoef(
            matrix,
            rowvar=False
        )

        return {
            "columns": columns,
            "matrix": corr.tolist()
        }

    finally:
        db.closeConnection()

@app.get("/api/sample-summary")
async def sample_summary():

    db = Database()
    db.openConnection()

    try:

        result = db.fetchInfo(
            """
            SELECT
                AVG(water_content) AS water_mean,
                MIN(water_content) AS water_min,
                MAX(water_content) AS water_max,

                AVG(density_kg_m3) AS density_mean,
                MIN(density_kg_m3) AS density_min,
                MAX(density_kg_m3) AS density_max,

                AVG(initial_mass_kg) AS mass_mean,
                MIN(initial_mass_kg) AS mass_min,
                MAX(initial_mass_kg) AS mass_max

            FROM samples
            """
        )

        return result[0]

    finally:
        db.closeConnection()