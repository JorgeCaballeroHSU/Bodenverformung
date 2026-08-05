from fastapi import FastAPI,Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sympy import group

from database.database import *
from services.Importer import Importer
from pathlib import Path
import os
import numpy as np
from pydantic import BaseModel
import pandas as pd

import tensorflow as tf
from services.auxiliary import build_model, update_prediction_experiment_table, sequence_generator, fetch_training_data


# Defines the naive models for comparison
from models.naive import (PersistenceForecast, MovingAverageForecast, LinearTrendForecast)

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

# API endpoints
# calls the index.html file when the root endpoint is accessed
@app.get("/")
async def home():

    # returns the index.html file from the frontend directory
    return FileResponse(str(FRONTEND_DIR / "index.html"))

# calls the database.html file when the /database endpoint is accessed
@app.get("/database")
async def database_page():

    # returns the database.html file from the frontend directory
    return FileResponse(str(FRONTEND_DIR / "database.html"))

# calls the training.html file when the /training endpoint is accessed
@app.get("/training")
async def training_page():

    # returns the training.html file from the frontend directory
    return FileResponse(str(FRONTEND_DIR / "training.html"))

# calls the prediction.html file when the /prediction endpoint is accessed
@app.get("/prediction")
async def prediction_page():

    # returns the prediction.html file from the frontend directory
    return FileResponse(str(FRONTEND_DIR / "prediction.html"))

# checks if the files have already been uploaded to the database
@app.post("/api/check-files")
async def check_files(data: dict = Body(...)):

    filenames = data.get("files", [])

    db = Database()
    db.openConnection()

    uploaded_files = []

    try:

        for filename in filenames:

            result = db.fetchInfo("""SELECT filename FROM files WHERE filename = ?""", (filename,))

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

class TrainRequest(BaseModel):

    model: str

    lookback_steps: int

    horizon: int

    inputs: list[str]

    static_inputs: list[str]

    targets: list[str]

    epochs: int

    batch_size: int

    learning_rate: float

    dropout: float

    units: int

# training endpoint
@app.post("/api/train-model")
async def train_model(config: TrainRequest):

    print("Training configuration received")
    print(config.model)

    rows = fetch_training_data()

    df = pd.DataFrame(rows)

    required_columns = (
        config.inputs +
        config.static_inputs +
        config.targets
    )

    df = df.dropna(
        subset=required_columns
    )

    inputs = (
        config.inputs +
        config.static_inputs
    )

    targets = config.targets

    dataset = tf.data.Dataset.from_generator(
    lambda: sequence_generator(df, inputs, targets, config.lookback_steps, config.horizon),
    output_signature=(
        tf.TensorSpec(shape=(config.lookback_steps, len(inputs)), dtype=tf.float32),
        tf.TensorSpec(shape=(len(targets),), dtype=tf.float32)
    ))
    dataset = dataset.batch(config.batch_size)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    model = build_model(config, len(inputs))
    history = model.fit(dataset, epochs=config.epochs, verbose=1)

    # creates an evaluation dataset for testing
    eval_X = []
    eval_y = []

    for _, group in df.groupby("test_id"):

        input_values = group[inputs].to_numpy(dtype=np.float32)
        target_values = group[targets].to_numpy(dtype=np.float32)

        for i in range(
            config.lookback_steps,
            len(group) - config.horizon
        ):

            eval_X.append(
                input_values[
                    i-config.lookback_steps:i
                ]
            )

            eval_y.append(
                target_values[
                    i+config.horizon
                ]
            )

            if len(eval_X) >= 5000:
                break

        if len(eval_X) >= 5000:
            break

    eval_X = np.asarray(eval_X, dtype=np.float32)
    eval_y = np.asarray(eval_y, dtype=np.float32)

    predictions = model.predict(eval_X)

    # add benchmarking with naive models
    persistence = PersistenceForecast()
    moving_average = MovingAverageForecast()
    linear_trend = LinearTrendForecast()

    pers_pred = []
    ma_pred = []
    trend_pred = []

    for sample in eval_X:

        # use first target variable from the sequence
        series = sample[:, 0]

        pers_pred.append(
            persistence.predict(series)
        )

        ma_pred.append(
            moving_average.predict(series)
        )

        trend_pred.append(
            linear_trend.predict(series)
        )

    pers_pred = np.array(pers_pred)
    ma_pred = np.array(ma_pred)
    trend_pred = np.array(trend_pred)

    actual = eval_y[:, 0]

    #compute metrics
    mae = mean_absolute_error(
        eval_y,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            eval_y,
            predictions
        )
    )

    r2 = r2_score(
        eval_y,
        predictions
    )

    # computes metrics for persistence model
    pers_mae = mean_absolute_error(
        actual,
        pers_pred
    )

    pers_rmse = np.sqrt(
        mean_squared_error(
            actual,
            pers_pred
        )
    )

    pers_r2 = r2_score(
        actual,
        pers_pred
    )

    # computes metrics for moving average model
    ma_mae = mean_absolute_error(
        actual,
        ma_pred
    )

    ma_rmse = np.sqrt(
        mean_squared_error(
            actual,
            ma_pred
        )
    )

    ma_r2 = r2_score(
        actual,
        ma_pred
    )

    # computes metrics for linear trend model
    trend_mae = mean_absolute_error(
        actual,
        trend_pred
    )

    trend_rmse = np.sqrt(
        mean_squared_error(
            actual,
            trend_pred
        )
    )

    trend_r2 = r2_score(
        actual,
        trend_pred
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),

        "actual": actual.tolist()[:500],
        "predicted": predictions[:, 0].tolist()[:500],

        "loss": [
            float(x)
            for x in history.history["loss"]
        ],

        "val_loss": history.history.get(
            "val_loss",
            []
        ),

        "persistence": {
            "mae": float(pers_mae),
            "rmse": float(pers_rmse),
            "r2": float(pers_r2)
        },

        "moving_average": {
            "mae": float(ma_mae),
            "rmse": float(ma_rmse),
            "r2": float(ma_r2)
        },

        "linear_trend": {
            "mae": float(trend_mae),
            "rmse": float(trend_rmse),
            "r2": float(trend_r2)
        }
    }

# available features endpoint
@app.get("/api/features")
async def features():

    return {

        "time_series": [

            "force_kn",
            "displacement_mm",
            "sample_height_mm",
            "strain_ratio",
            "strain_pct",
            "stress_kpa"

        ],

        "static": [

            "water_content",
            "density_kg_m3",
            "initial_mass_kg"

        ]
    }

# experiements endpoint
@app.get("/api/experiments")
async def experiments():

    db = Database()
    db.openConnection()

    try:

        rows = db.fetchInfo(
            """
            SELECT *
            FROM prediction_experiments
            ORDER BY created_at DESC
            LIMIT 100
            """
        )

        return rows

    finally:

        db.closeConnection()

# training methadata endpoint
@app.get("/api/training-metadata")
async def training_metadata():

    return {

        "models":[

            "LSTMForecaster",
            "StackedLSTMForecaster",
            "BiLSTMForecaster",
            "EncoderDecoderLSTMForecaster",
            "Seq2SeqAttentionLSTMForecaster",
            "CNNLSTMForecaster",
            "GRUForecaster",
            "DeepARForecaster",
            "TFTForecaster"

        ],

        "timeseries_features":[

            "force_kn",
            "displacement_mm",
            "sample_height_mm",
            "strain_ratio",
            "strain_pct",
            "stress_kpa"

        ],

        "static_features":[

            "water_content",
            "density_kg_m3",
            "initial_mass_kg"

        ],

        "default_inputs":[

            "force_kn",
            "displacement_mm",
            "sample_height_mm"

        ],

        "default_static":[

            "water_content",
            "density_kg_m3"

        ],

        "default_targets":[

            "strain_pct",
            "stress_kpa"

        ]

    }




