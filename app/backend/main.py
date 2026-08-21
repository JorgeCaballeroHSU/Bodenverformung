from fastapi import FastAPI,Body, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

from database.database import *
from services.Importer import Importer
from pathlib import Path
import os
import numpy as np
from pydantic import BaseModel
import pandas as pd

from itertools import product
import gc
import math

import tensorflow as tf
from services.auxiliary import (
    build_model,
    update_prediction_experiment_table,
    sequence_generator,
    fetch_training_data,
    build_naive_predictions,
    build_evaluation_data,
    build_plot_samples
)

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

# calls the prediction.html file when the /prediction endpoint is accessed
@app.get("/prediction")
async def prediction_page():

    # returns the prediction.html file from the frontend directory
    return FileResponse(str(FRONTEND_DIR / "prediction.html"))

##########################################################################
######################### DATABASE END POINTS ############################
##########################################################################

# calls the database.html file when the /database endpoint is accessed
@app.get("/database")
async def database_page():

    # returns the database.html file from the frontend directory
    return FileResponse(str(FRONTEND_DIR / "database.html"))

# checks if the files have already been uploaded to the database
@app.post("/api/check-files")
async def check_files(data: dict = Body(...)):

    # retrieves the list of filenames from the request body
    filenames = data.get("files", [])

    # creates a Database object to interact with the database
    db = Database()

    # opens a connection to the database and checks if the files have already been uploaded
    try:

        # opens a connection to the database
        db.openConnection()

        # initializes an empty list to store the names of the files that have already been uploaded
        uploaded_files = []

        # iterates through the list of filenames and checks if each file has already been uploaded to the database
        for filename in filenames:

            # executes a SQL query to check if the file has already been uploaded to the database
            result = db.fetchInfo("""SELECT filename FROM files WHERE filename = ?""", (filename,))

            # if the file has already been uploaded, appends the filename to the list of uploaded files
            if result:

                # appends the filename to the list of uploaded files
                uploaded_files.append(filename)

    # handles any exceptions that may occur during the file checking process
    except Exception as e:
        
        # if an error occurs while checking the files, raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # closes the database connection
        db.closeConnection()

        # returns a JSON response containing the list of uploaded files
        return {"uploaded": uploaded_files}


# handles the uploading of files to the database
@app.post("/api/upload-files")
async def upload_files(files: list[UploadFile] = File(...)):

    # creates an Importer object to handle the importation of the files
    importer=Importer()

    # initializes variables imported and failed to append according to the names of the variables
    imported=[]
    failed=[]

    # iterates through the list of uploaded files and attempts to import each file into the database
    for uploaded_file in files:

        # initializes a variable temp_path to None to store the path of the temporary file created for each uploaded file
        temp_path=None

        # attempts to import the uploaded file into the database
        try:

            # creates a temporary file with a .xlsx suffix to store the contents of the uploaded file
            with NamedTemporaryFile(delete=False,suffix=".xlsx") as tmp:

                # reads the contents of the uploaded file and writes them to the temporary file
                content = await uploaded_file.read()

                # writes the contents of the uploaded file to the temporary file
                tmp.write(content)

                # stores the path of the temporary file in the temp_path variable
                temp_path = Path(tmp.name)

            # imports the contents of the temporary file into the database using the Importer object
            importer.import_file(temp_path,uploaded_file.filename)

            # appends the name of the successfully imported file to the imported list
            imported.append(uploaded_file.filename)

        # handles any exceptions that may occur during the importation process
        except Exception as e:

            # if an error occurs while importing the file, appends the name of the failed file and the error message to the failed list
            failed.append(f"{uploaded_file.filename}: {e}")

        # removes the temporary file created for the uploaded file, if it exists
        finally:

            # removes the temporary file created for the uploaded file, if it exists
            if temp_path and temp_path.exists():

                # removes the temporary file created for the uploaded file
                os.remove(temp_path)

    # returns a JSON response containing the names of the successfully imported files, the names of the failed files, and the counts of each
    return {"imported": imported, "failed": failed, "imported_count": len(imported), "failed_count": len(failed)}

# Database summary
@app.get("/api/database-summary")
async def database_summary():

    # creates a Database object to interact with the database
    db = Database()

    # opens a connection to the database and retrieves summary information about the database
    try:

        # opens a connection to the database
        db.openConnection()

        # retrieves the total number of tests in the database
        total_tests = db.fetchInfo("SELECT COUNT(*) as value FROM tests")[0]["value"]

        # retrieves the total number of measurements in the database
        total_measurements = db.fetchInfo("SELECT COUNT(*) as value FROM measurements")[0]["value"]

        # retrieves the average stress value from the measurements table in the database
        avg_stress = db.fetchInfo("""SELECT AVG(stress_kpa) as value FROM measurements""")[0]["value"]

        # retrieves the maximum force value from the measurements table in the database
        max_force = db.fetchInfo("""SELECT MAX(force_kn) as value FROM measurements""")[0]["value"]

        # returns a JSON response containing the summary information about the database, 
        # including the total number of tests, total number of measurements, average stress value, and maximum force value
        return {"total_tests": total_tests, "total_measurements": total_measurements, "avg_stress": avg_stress or 0,
                "max_force": max_force or 0}

    # handles any exceptions that may occur during the database summary retrieval process
    except Exception as e:

        # if an error occurs while retrieving the database summary, raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))

    # finally block to ensure that the database connection is closed after the summary information has been retrieved
    finally:

        # closes the database connection
        db.closeConnection()


# Stress vs Strain
@app.get("/api/stress-strain")
async def stress_strain():

    # creates a Database object to interact with the database
    db = Database()

    # opens a connection to the database and retrieves stress and strain data from the measurements table
    try:

        # opens a connection to the database
        db.openConnection()

        # retrieves stress and strain data from the measurements table in the database,
        data = db.fetchInfo(
            """SELECT strain_pct, stress_kpa FROM measurements WHERE strain_pct IS NOT NULL AND stress_kpa IS NOT NULL
            ORDER BY RANDOM() LIMIT 20000"""
        )

        # returns a JSON response containing the stress and strain data as two separate lists
        return {"strain_pct":[row["strain_pct"] for row in data], "stress_kpa":[row["stress_kpa"] for row in data]}

    # handles any exceptions that may occur during the stress and strain data retrieval process
    except Exception as e:

        # if an error occurs while retrieving the stress and strain data, 
        # raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))

    # finally block to ensure that the database connection is closed after the stress and strain data has been retrieved
    finally:

        # closes the database connection
        db.closeConnection()

# Force vs Displacement
@app.get("/api/force-displacement")
async def force_displacement():

    # creates a Database object to interact with the database
    db = Database()

    # opens a connection to the database and retrieves force and displacement data from the measurements table
    try:

        # opens a connection to the database
        db.openConnection()

        # retrieves force and displacement data from the measurements table in the database, 
        # and returns a JSON response containing the data as two separate lists
        data = db.fetchInfo(
            """SELECT displacement_mm, force_kn FROM measurements WHERE displacement_mm IS NOT NULL AND force_kn IS NOT NULL
            ORDER BY RANDOM() LIMIT 20000"""
        )

        # returns a JSON response containing the force and displacement data as two separate lists
        return {"displacement_mm": [row["displacement_mm"] for row in data], "force_kn": [row["force_kn"] for row in data]}

    # handles any exceptions that may occur during the force and displacement data retrieval process
    except Exception as e:
        
        # if an error occurs while retrieving the force and displacement data, 
        # raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))

    # finally block to ensure that the database connection is closed after the force and displacement data has been retrieved
    finally:

        # closes the database connection
        db.closeConnection()

# Stress Histogram
@app.get("/api/stress-histogram")
async def stress_histogram():

    # creates a Database object to interact with the database
    db = Database()

    # opens a connection to the database and retrieves stress data from the measurements table
    try:

        # opens a connection to the database
        db.openConnection()

        # retrieves stress data from the measurements table in the database, and returns a JSON response containing the data as a list
        data = db.fetchInfo("""SELECT stress_kpa FROM measurements WHERE stress_kpa IS NOT NULL ORDER BY RANDOM() LIMIT 100000""")

        # returns a JSON response containing the stress data as a list
        return {"stress_kpa":[row["stress_kpa"] for row in data]}

    # handles any exceptions that may occur during the stress data retrieval process
    except Exception as e:
        
        # if an error occurs while retrieving the stress data, raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))

    # finally block to ensure that the database connection is closed after the stress data has been retrieved
    finally:

        # closes the database connection
        db.closeConnection()

# strain histogram
@app.get("/api/strain-histogram")
async def strain_histogram():

    # creates a Database object to interact with the database
    db = Database()
    
    # opens a connection to the database and retrieves strain data from the measurements table
    try:

        # opens a connection to the database
        db.openConnection()

        # retrieves strain data from the measurements table in the database, 
        # and returns a JSON response containing the data as a list
        data = db.fetchInfo("""SELECT strain_pct FROM measurements WHERE strain_pct IS NOT NULL ORDER BY RANDOM() LIMIT 100000""")

        # returns a JSON response containing the strain data as a list
        return {"strain_pct":[row["strain_pct"] for row in data]}

    # handles any exceptions that may occur during the strain data retrieval process
    except Exception as e:
        
        # if an error occurs while retrieving the strain data, raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))

    # finally block to ensure that the database connection is closed after the strain data has been retrieved
    finally:

        # closes the database connection
        db.closeConnection()

# correlation matrix
@app.get("/api/correlation")
async def correlation_matrix():

    # creates a Database object to interact with the database
    db = Database()
    
    # opens a connection to the database and retrieves data from the measurements table to compute the correlation matrix
    try:

        # opens a connection to the database
        db.openConnection()

        # retrieves data from the measurements table in the database, and computes the correlation matrix for the specified columns
        rows = db.fetchInfo(
            """SELECT force_kn, displacement_mm, sample_height_mm, strain_ratio, strain_pct, stress_kpa FROM measurements
            WHERE force_kn IS NOT NULL AND displacement_mm IS NOT NULL AND sample_height_mm IS NOT NULL AND strain_ratio IS NOT NULL
                AND strain_pct IS NOT NULL AND stress_kpa IS NOT NULL ORDER BY RANDOM() LIMIT 20000"""
        )

        # defines the columns for which the correlation matrix will be computed
        columns = ["force_kn", "displacement_mm", "sample_height_mm", "strain_ratio", "strain_pct", "stress_kpa"]

        # creates a matrix of the selected columns from the retrieved rows
        matrix = np.array([[row[col] for col in columns] for row in rows])

        # computes the correlation matrix using numpy's corrcoef function
        corr = np.corrcoef(matrix,rowvar=False)

        # returns a JSON response containing the correlation matrix and the corresponding column names
        return {"columns": columns,"matrix": corr.tolist()}

    # handles any exceptions that may occur during the correlation matrix computation process
    except Exception as e:
        
        # if an error occurs while computing the correlation matrix, raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))

    # finally block to ensure that the database connection is closed after the correlation matrix has been computed
    finally:

        # closes the database connection
        db.closeConnection()

# sample summary endpoint
@app.get("/api/sample-summary")
async def sample_summary():

    # creates a Database object to interact with the database
    db = Database()

    # opens a connection to the database and retrieves summary statistics for the samples in the database
    try:

        # opens a connection to the database
        db.openConnection()

        # executes a SQL query to retrieve summary statistics for the samples in the database, 
        # including mean, minimum, and maximum values for water content, density, and initial mass
        result = db.fetchInfo(
            """SELECT AVG(water_content) AS water_mean, MIN(water_content) AS water_min, MAX(water_content) AS water_max,
                AVG(density_kg_m3) AS density_mean, MIN(density_kg_m3) AS density_min, MAX(density_kg_m3) AS density_max,
                AVG(initial_mass_kg) AS mass_mean, MIN(initial_mass_kg) AS mass_min, MAX(initial_mass_kg) AS mass_max
            FROM samples"""
        )

        # returns a JSON response containing the summary statistics for the samples in the database
        return result[0]

    # handles any exceptions that may occur during the sample summary retrieval process
    except Exception as e:
        
        # if an error occurs while retrieving the sample summary, raises an HTTPException with a 500 status code and the error message
        raise HTTPException(status_code=500, detail=str(e))

    # finally block to ensure that the database connection is closed after the correlation matrix has been computed
    finally:

        # closes the database connection
        db.closeConnection()

##########################################################################
######################### TRAINING END POINTS ############################
##########################################################################

# calls the training.html file when the /training endpoint is accessed
@app.get("/training")
async def training_page():

    # returns the training.html file from the frontend directory
    return FileResponse(str(FRONTEND_DIR / "training.html"))


class TrainRequest(BaseModel):

    model: str

    lookback_steps: list[int]
    horizons: list[int]

    inputs: list[str]
    static_inputs: list[str]
    targets: list[str]

    train_split: float
    validation_split: float
    test_split: float

    epochs: list[int]
    batch_sizes: list[int]
    learning_rates: list[float]
    dropouts: list[float]
    units: list[int]


def count_sequences(
        dataframe: pd.DataFrame,
        lookback_steps: int,
        horizon: int) -> int:

    total_sequences = 0

    for _, group in dataframe.groupby("test_id"):

        sequence_count = (
            len(group)
            - lookback_steps
            - horizon
        )

        total_sequences += max(
            0,
            sequence_count
        )

    return total_sequences


def validate_training_configuration(
        config: TrainRequest) -> None:

    split_total = (
        config.train_split
        + config.validation_split
        + config.test_split
    )

    if abs(split_total - 100.0) > 0.01:

        raise HTTPException(
            status_code=400,
            detail=(
                "Training, validation and test percentages "
                "must add up to 100."
            )
        )

    if not config.inputs and not config.static_inputs:

        raise HTTPException(
            status_code=400,
            detail="Select at least one input variable."
        )

    if not config.targets:

        raise HTTPException(
            status_code=400,
            detail="Select at least one target variable."
        )

    if not config.lookback_steps:

        raise HTTPException(
            status_code=400,
            detail="Provide at least one lookback value."
        )

    if not config.horizons:

        raise HTTPException(
            status_code=400,
            detail="Provide at least one forecast horizon."
        )

    if not config.epochs:

        raise HTTPException(
            status_code=400,
            detail="Provide at least one epoch value."
        )

    if not config.batch_sizes:

        raise HTTPException(
            status_code=400,
            detail="Provide at least one batch size."
        )

    if not config.learning_rates:

        raise HTTPException(
            status_code=400,
            detail="Provide at least one learning rate."
        )

    if not config.dropouts:

        raise HTTPException(
            status_code=400,
            detail="Provide at least one dropout value."
        )

    if not config.units:

        raise HTTPException(
            status_code=400,
            detail="Provide at least one units value."
        )

    if any(value < 1 for value in config.lookback_steps):

        raise HTTPException(
            status_code=400,
            detail="Lookback values must be at least 1."
        )

    if any(value < 1 for value in config.horizons):

        raise HTTPException(
            status_code=400,
            detail="Forecast horizons must be at least 1."
        )

    if any(value < 1 for value in config.epochs):

        raise HTTPException(
            status_code=400,
            detail="Epoch values must be at least 1."
        )

    if any(value < 1 for value in config.batch_sizes):

        raise HTTPException(
            status_code=400,
            detail="Batch sizes must be at least 1."
        )

    if any(value <= 0 for value in config.learning_rates):

        raise HTTPException(
            status_code=400,
            detail="Learning rates must be greater than zero."
        )

    if any(
        value < 0 or value >= 1
        for value in config.dropouts
    ):

        raise HTTPException(
            status_code=400,
            detail="Dropout values must satisfy 0 <= dropout < 1."
        )

    if any(value < 1 for value in config.units):

        raise HTTPException(
            status_code=400,
            detail="Units must be at least 1."
        )


@app.post("/api/train-model")
async def train_model(config: TrainRequest):

    print("Training configuration received")
    print(config.model)

    validate_training_configuration(
        config
    )

    experiment_combinations = list(
        product(
            config.lookback_steps,
            config.horizons,
            config.epochs,
            config.batch_sizes,
            config.learning_rates,
            config.dropouts,
            config.units
        )
    )

    total_experiments = len(
        experiment_combinations
    )

    if total_experiments > 100:

        raise HTTPException(
            status_code=400,
            detail=(
                f"The selected values generate "
                f"{total_experiments} experiments. "
                "The maximum allowed is 100."
            )
        )

    rows = fetch_training_data()

    if not rows:

        raise HTTPException(
            status_code=400,
            detail="No training data were found."
        )

    df = pd.DataFrame(rows)

    inputs = (
        config.inputs
        + config.static_inputs
    )

    targets = config.targets

    required_columns = list(
        dict.fromkeys(
            ["test_id"]
            + inputs
            + targets
        )
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise HTTPException(
            status_code=400,
            detail=(
                "Missing columns: "
                + ", ".join(missing_columns)
            )
        )

    df = df.dropna(
        subset=required_columns
    ).copy()

    all_test_ids = sorted(
        df["test_id"].unique()
    )

    n_tests = len(all_test_ids)

    n_train = int(
        n_tests
        * config.train_split
        / 100
    )

    n_validation = int(
        n_tests
        * config.validation_split
        / 100
    )

    train_ids = all_test_ids[
        :n_train
    ]

    validation_ids = all_test_ids[
        n_train:
        n_train + n_validation
    ]

    test_ids = all_test_ids[
        n_train + n_validation:
    ]

    if not train_ids:

        raise HTTPException(
            status_code=400,
            detail="The training split contains no tests."
        )

    if not validation_ids:

        raise HTTPException(
            status_code=400,
            detail="The validation split contains no tests."
        )

    if not test_ids:

        raise HTTPException(
            status_code=400,
            detail="The test split contains no tests."
        )

    train_df = df[
        df["test_id"].isin(train_ids)
    ].copy()

    validation_df = df[
        df["test_id"].isin(validation_ids)
    ].copy()

    test_df = df[
        df["test_id"].isin(test_ids)
    ].copy()

    # Preserve original test values for metrics and benchmarks.
    test_df_unscaled = test_df.copy()

    # Separate columns prevent double transformation when a variable
    # is selected as both an input and a target.
    scaled_inputs = [
        f"x__{column}"
        for column in inputs
    ]

    scaled_targets = [
        f"y__{column}"
        for column in targets
    ]

    input_scaler = StandardScaler()
    target_scaler = StandardScaler()

    input_scaler.fit(
        train_df[inputs]
    )

    target_scaler.fit(
        train_df[targets]
    )

    train_df[scaled_inputs] = (
        input_scaler.transform(
            train_df[inputs]
        )
    )

    validation_df[scaled_inputs] = (
        input_scaler.transform(
            validation_df[inputs]
        )
    )

    test_df[scaled_inputs] = (
        input_scaler.transform(
            test_df[inputs]
        )
    )

    train_df[scaled_targets] = (
        target_scaler.transform(
            train_df[targets]
        )
    )

    validation_df[scaled_targets] = (
        target_scaler.transform(
            validation_df[targets]
        )
    )

    test_df[scaled_targets] = (
        target_scaler.transform(
            test_df[targets]
        )
    )

    experiment_results = []

    best_result = None
    best_rmse = float("inf")

    for experiment_number, combination in enumerate(
        experiment_combinations,
        start=1
    ):

        (
            lookback_steps,
            horizon,
            epochs,
            batch_size,
            learning_rate,
            dropout,
            units
        ) = combination

        print(
            f"\nExperiment "
            f"{experiment_number}/{total_experiments}"
        )

        print({
            "lookback_steps": lookback_steps,
            "horizon": horizon,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "dropout": dropout,
            "units": units
        })

        try:

            train_sequence_count = count_sequences(
                train_df,
                lookback_steps,
                horizon
            )

            validation_sequence_count = count_sequences(
                validation_df,
                lookback_steps,
                horizon
            )

            test_sequence_count = count_sequences(
                test_df,
                lookback_steps,
                horizon
            )

            if train_sequence_count == 0:

                raise ValueError(
                    "No training sequences could be generated."
                )

            if validation_sequence_count == 0:

                raise ValueError(
                    "No validation sequences could be generated."
                )

            if test_sequence_count == 0:

                raise ValueError(
                    "No testing sequences could be generated."
                )

            train_steps = math.ceil(
                train_sequence_count
                / batch_size
            )

            validation_steps = math.ceil(
                validation_sequence_count
                / batch_size
            )

            train_dataset = (
                tf.data.Dataset.from_generator(
                    lambda: sequence_generator(
                        train_df,
                        scaled_inputs,
                        scaled_targets,
                        lookback_steps,
                        horizon
                    ),
                    output_signature=(
                        tf.TensorSpec(
                            shape=(
                                lookback_steps,
                                len(scaled_inputs)
                            ),
                            dtype=tf.float32
                        ),
                        tf.TensorSpec(
                            shape=(
                                len(scaled_targets),
                            ),
                            dtype=tf.float32
                        )
                    )
                )
                .shuffle(
                    min(
                        10000,
                        train_sequence_count
                    )
                )
                .batch(batch_size)
                .repeat()
                .prefetch(
                    tf.data.AUTOTUNE
                )
            )

            validation_dataset = (
                tf.data.Dataset.from_generator(
                    lambda: sequence_generator(
                        validation_df,
                        scaled_inputs,
                        scaled_targets,
                        lookback_steps,
                        horizon
                    ),
                    output_signature=(
                        tf.TensorSpec(
                            shape=(
                                lookback_steps,
                                len(scaled_inputs)
                            ),
                            dtype=tf.float32
                        ),
                        tf.TensorSpec(
                            shape=(
                                len(scaled_targets),
                            ),
                            dtype=tf.float32
                        )
                    )
                )
                .batch(batch_size)
                .repeat()
                .prefetch(
                    tf.data.AUTOTUNE
                )
            )

            model = build_model(
                config=config,
                n_features=len(scaled_inputs),
                lookback_steps=lookback_steps,
                learning_rate=learning_rate,
                dropout=dropout,
                units=units
            )

            history = model.fit(
                train_dataset,
                validation_data=validation_dataset,
                epochs=epochs,
                steps_per_epoch=train_steps,
                validation_steps=validation_steps,
                verbose=1
            )

            eval_X, eval_y, eval_test_ids = (
                build_evaluation_data(
                    test_df,
                    test_df_unscaled,
                    scaled_inputs,
                    targets,
                    lookback_steps,
                    horizon
                )
            )

            if len(eval_X) == 0:

                raise ValueError(
                    "No evaluation sequences could be generated."
                )

            predictions_scaled = model.predict(
                eval_X
            )

            predictions = (
                target_scaler.inverse_transform(
                    predictions_scaled
                )
            )

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

            (
                benchmark_actual,
                pers_pred,
                ma_pred,
                trend_pred
            ) = build_naive_predictions(
                test_df_unscaled,
                targets,
                lookback_steps,
                horizon
            )

            pers_mae = mean_absolute_error(
                benchmark_actual,
                pers_pred
            )

            pers_rmse = np.sqrt(
                mean_squared_error(
                    benchmark_actual,
                    pers_pred
                )
            )

            pers_r2 = r2_score(
                benchmark_actual,
                pers_pred
            )

            ma_mae = mean_absolute_error(
                benchmark_actual,
                ma_pred
            )

            ma_rmse = np.sqrt(
                mean_squared_error(
                    benchmark_actual,
                    ma_pred
                )
            )

            ma_r2 = r2_score(
                benchmark_actual,
                ma_pred
            )

            trend_mae = mean_absolute_error(
                benchmark_actual,
                trend_pred
            )

            trend_rmse = np.sqrt(
                mean_squared_error(
                    benchmark_actual,
                    trend_pred
                )
            )

            trend_r2 = r2_score(
                benchmark_actual,
                trend_pred
            )

            experiment_id = (
                update_prediction_experiment_table(
                    model_type=config.model,
                    prediction_target=",".join(
                        config.targets
                    ),

                    prediction_horizon=horizon,
                    lookback_steps=lookback_steps,

                    epochs=epochs,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                    dropout=dropout,
                    units=units,

                    training_samples=len(train_ids),
                    validation_samples=len(
                        validation_ids
                    ),
                    test_samples=len(test_ids),

                    train_split=config.train_split,
                    validation_split=(
                        config.validation_split
                    ),
                    test_split=config.test_split,

                    mae=float(mae),
                    rmse=float(rmse),
                    r2=float(r2),

                    persistence_mae=float(
                        pers_mae
                    ),
                    persistence_rmse=float(
                        pers_rmse
                    ),
                    persistence_r2=float(
                        pers_r2
                    ),

                    moving_average_mae=float(
                        ma_mae
                    ),
                    moving_average_rmse=float(
                        ma_rmse
                    ),
                    moving_average_r2=float(
                        ma_r2
                    ),

                    linear_trend_mae=float(
                        trend_mae
                    ),
                    linear_trend_rmse=float(
                        trend_rmse
                    ),
                    linear_trend_r2=float(
                        trend_r2
                    )
                )
            )

            result = {
                "status": "completed",

                "experiment_id":
                    experiment_id,

                "model":
                    config.model,

                "lookback_steps":
                    lookback_steps,

                "horizon":
                    horizon,

                "epochs":
                    epochs,

                "batch_size":
                    batch_size,

                "learning_rate":
                    learning_rate,

                "dropout":
                    dropout,

                "units":
                    units,

                "mae":
                    float(mae),

                "rmse":
                    float(rmse),

                "r2":
                    float(r2),

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
                    "rmse": float(
                        trend_rmse
                    ),
                    "r2": float(trend_r2)
                }
            }

            experiment_results.append(
                result
            )

            if rmse < best_rmse:

                best_rmse = rmse

                plot_data = build_plot_samples(
                    eval_test_ids,
                    eval_y,
                    predictions,
                    targets,
                    n_samples=3
                )

                best_result = {
                    **result,

                    "samples":
                        plot_data["samples"],

                    "loss": [
                        float(value)
                        for value
                        in history.history["loss"]
                    ],

                    "val_loss": [
                        float(value)
                        for value
                        in history.history.get(
                            "val_loss",
                            []
                        )
                    ]
                }

        except Exception as error:

            print(
                f"Experiment failed: {error}"
            )

            experiment_results.append({
                "status": "failed",

                "lookback_steps":
                    lookback_steps,

                "horizon":
                    horizon,

                "epochs":
                    epochs,

                "batch_size":
                    batch_size,

                "learning_rate":
                    learning_rate,

                "dropout":
                    dropout,

                "units":
                    units,

                "error":
                    str(error)
            })

        finally:

            tf.keras.backend.clear_session()
            gc.collect()

    completed_runs = sum(
        result["status"] == "completed"
        for result in experiment_results
    )

    failed_runs = (
        total_experiments
        - completed_runs
    )

    if best_result is None:

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "All experiments failed."
                ),
                "experiments":
                    experiment_results
            }
        )

    return {
        "total_runs":
            total_experiments,

        "completed_runs":
            completed_runs,

        "failed_runs":
            failed_runs,

        "best_result":
            best_result,

        "experiments":
            experiment_results
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


# it shows the latest experiment
@app.get("/api/latest-experiment")
async def latest_experiment():

    db = Database()

    try:

        db.openConnection()

        experiment = db.fetchInfo(
            """
            SELECT *
            FROM prediction_experiments
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        if not experiment:
            return None

        experiment = experiment[0]

        return experiment

    finally:

        db.closeConnection()