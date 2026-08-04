from fastapi import FastAPI,Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile

from sympy import group

from database.database import *
from services.Importer import Importer
from pathlib import Path
import os
import numpy as np
from pydantic import BaseModel
import pandas as pd

import tensorflow as tf

# Defines the models that can be used for training
from models.models import (LSTMForecaster, StackedLSTMForecaster, BiLSTMForecaster, EncoderDecoderLSTMForecaster,
                           Seq2SeqAttentionLSTMForecaster, CNNLSTMForecaster, GRUForecaster, DeepARForecaster, TFTForecaster)

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
    history = model.model.fit(dataset,epochs=config.epochs,verbose=1)

    return {"message": "Training completed"}

    # actual = y_test[:,0].tolist()

    # predicted = predictions[:,0].tolist()

    # # metrics
    # mae = mean_absolute_error(
    #     y_test,
    #     predictions,
    #     multioutput="uniform_average"
    # )

    # rmse = np.sqrt(
    #     mean_squared_error(
    #         actual,
    #         predictions,
    #         multioutput="uniform_average"
    #     )
    # )

    # r2 = r2_score(
    #     actual,
    #     predictions,
    #     multioutput="uniform_average"
    # )

    # return {

    #     "mae": float(mae),
    #     "rmse": float(rmse),
    #     "r2": float(r2),

    #     "persistence": {
    #         "mae": 0.071,
    #         "rmse": 0.105,
    #         "r2": 0.68
    #     },

    #     "moving_average": {
    #         "mae": 0.055,
    #         "rmse": 0.089,
    #         "r2": 0.75
    #     },

    #     "linear_trend": {
    #         "mae": 0.062,
    #         "rmse": 0.092,
    #         "r2": 0.73
    #     },

    #     "actual": actual[:500],
    #     "predicted": predicted[:500],

    #     "naive": [
    #         10,10,11,12,13,14,15,16,17
    #     ],

    #     "loss": [
    #         float(x)
    #         for x in history.history["loss"]
    #     ],

    #     "val_loss": [
    #         float(x)
    #         for x in history.history["val_loss"]
    #     ]
    # }

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

# dataset loader
def fetch_training_data():

    db = Database()
    db.openConnection()

    try:

        return db.fetchInfo(
            """
            SELECT

                measurements.test_id,

                measurements.time_s,

                measurements.force_kn,
                measurements.displacement_mm,
                measurements.sample_height_mm,
                measurements.strain_ratio,
                measurements.strain_pct,
                measurements.stress_kpa,

                samples.water_content,
                samples.density_kg_m3,
                samples.initial_mass_kg

            FROM measurements

            INNER JOIN tests
                ON tests.id = measurements.test_id

            INNER JOIN samples
                ON samples.id = tests.sample_id

            ORDER BY
                measurements.test_id,
                measurements.time_s
            """
        )

    finally:

        db.closeConnection()


# sequence generator for training
def sequence_generator(df, inputs, targets, lookback, horizon):

    total_tests = df["test_id"].nunique()
    total_sequences = 0

    for idx, (_, group) in enumerate(df.groupby("test_id"), start=1):

        print(
            f"Processing test {idx}/{total_tests}, "
            f"rows={len(group)}"
        )

        input_values = group[inputs].to_numpy(dtype=np.float32)
        target_values = group[targets].to_numpy(dtype=np.float32)

        for i in range(
            lookback,
            len(group) - horizon
        ):
            total_sequences += 1

            if total_sequences % 50000 == 0:
                print(f"{total_sequences:,} sequences generated")


            yield (
                input_values[i-lookback:i],
                target_values[i+horizon]
            )

def build_model(config, n_features):

    if config.model == "LSTMForecaster":

        return LSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    elif config.model == "StackedLSTMForecaster":

        return StackedLSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    elif config.model == "BiLSTMForecaster":

        return BiLSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    elif config.model == "CNNLSTMForecaster":

        return CNNLSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    elif config.model == "GRUForecaster":

        return GRUForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    elif config.model == "DeepARForecaster":

        return DeepARForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    raise ValueError(
        f"Unsupported model: {config.model}"
    )