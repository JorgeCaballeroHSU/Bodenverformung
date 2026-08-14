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

import tensorflow as tf
from services.auxiliary import (build_model, update_prediction_experiment_table, sequence_generator, 
fetch_training_data, build_naive_predictions, build_plot_sample)

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
    lookback_steps: int
    horizon: int
    inputs: list[str]
    static_inputs: list[str]
    targets: list[str]
    train_split: float
    validation_split: float
    test_split: float
    epochs: int
    batch_size: int
    learning_rate: float
    dropout: float
    units: int

# training endpoint
@app.post("/api/train-model")
async def train_model(config: TrainRequest):

    # informs the user the configuration for model training was received. Likewise, prints the configuration model
    print("Training configuration received")
    print(config.model)

    # fetches the training data
    rows = fetch_training_data()

    # converst the list into a data frame for rapid handling
    df = pd.DataFrame(rows)

    # split by test id
    all_test_ids = sorted(df["test_id"].unique())

    n_tests = len(all_test_ids)

    n_train = int(n_tests * config.train_split / 100)

    n_validation = int(n_tests * config.validation_split / 100)

    train_ids = all_test_ids[:n_train]

    validation_ids = all_test_ids[n_train:n_train + n_validation]

    test_ids = all_test_ids[n_train + n_validation:]

    # makes a list of the required columns
    required_columns = (config.inputs + config.static_inputs + config.targets)

    # drops the rows with NaN values
    df = df.dropna(subset=required_columns)

    # makes a list of input values
    inputs = (config.inputs + config.static_inputs)

    # initializes a variable that contains the targets to tbe calculated
    targets = config.targets

    # split data first
    train_df = df[df["test_id"].isin(train_ids)].copy()
    validation_df = df[df["test_id"].isin(validation_ids)].copy()
    test_df = df[df["test_id"].isin(test_ids)].copy()

    # calculation of benchmark performance
    benchmark_actual, pers_pred, ma_pred, trend_pred = (build_naive_predictions(
        test_df, targets, config.lookback_steps, config.horizon))

    # fit scalers ONLY on training data
    input_scaler = StandardScaler()
    target_scaler = StandardScaler()

    input_scaler.fit(train_df[inputs])

    target_scaler.fit(train_df[targets])

    # transform train data
    train_df[inputs] = input_scaler.transform(train_df[inputs])
    train_df[targets] = target_scaler.transform(train_df[targets])

    # transform validation data
    validation_df[inputs] = input_scaler.transform(validation_df[inputs])
    validation_df[targets] = target_scaler.transform(validation_df[targets])

    # transform test data
    test_df[inputs] = input_scaler.transform(test_df[inputs])
    test_df[targets] = target_scaler.transform(test_df[targets])

    # creates the dataset of sequences necessary to feed up the models for training
    train_dataset = tf.data.Dataset.from_generator(
        lambda: sequence_generator(
            train_df,
            inputs,
            targets,
            config.lookback_steps,
            config.horizon
        ),
        output_signature=(
            tf.TensorSpec(
                shape=(config.lookback_steps,
                    len(inputs)),
                dtype=tf.float32
            ),
            tf.TensorSpec(
                shape=(len(targets),),
                dtype=tf.float32
            )
        )
    )

    # creates validation dataset
    validation_dataset = tf.data.Dataset.from_generator(
        lambda: sequence_generator(
            validation_df,
            inputs,
            targets,
            config.lookback_steps,
            config.horizon
        ),
        output_signature=(
            tf.TensorSpec(
                shape=(config.lookback_steps,
                    len(inputs)),
                dtype=tf.float32
            ),
            tf.TensorSpec(
                shape=(len(targets),),
                dtype=tf.float32
            )
        )
    )

    validation_dataset = (
        validation_dataset
        .batch(config.batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )

    train_dataset = (
        train_dataset
        .shuffle(10000)
        .batch(config.batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )


    model = build_model(config, len(inputs))
    history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=config.epochs,
        verbose=1
    )

    # creates dataset for plotting
    plot_data = build_plot_sample(model, test_df,inputs, targets, config.lookback_steps, config.horizon, target_scaler)

    #compute metrics
    # calculates the mean absolute error regression loss
    eval_X = []
    eval_y = []

    for _, group in test_df.groupby("test_id"):

        input_values = group[inputs].to_numpy(dtype=np.float32)
        target_values = group[targets].to_numpy(dtype=np.float32)

        for i in range(config.lookback_steps,len(group) - config.horizon):

            eval_X.append(input_values[i-config.lookback_steps:i])
            eval_y.append(target_values[i+config.horizon-1])

    eval_X = np.asarray(eval_X, dtype=np.float32)
    eval_y = np.asarray(eval_y, dtype=np.float32)

    predictions = model.predict(eval_X)
    predictions = (target_scaler.inverse_transform(predictions))

    eval_y = (target_scaler.inverse_transform(eval_y))

    mae = mean_absolute_error(eval_y, predictions)
    rmse = np.sqrt(mean_squared_error(eval_y, predictions))

    r2 = r2_score(eval_y,predictions)

    # computes metrics for persistence model
    # calculates the mean absolute error regression loss
    pers_mae = mean_absolute_error(benchmark_actual, pers_pred)

    # calculates the mean squared error regression loss
    pers_rmse = np.sqrt(mean_squared_error(benchmark_actual,pers_pred))

    # calculates r² 
    pers_r2 = r2_score(benchmark_actual,pers_pred)

    # computes metrics for moving average model
    # calculates the mean absolute error regression loss
    ma_mae = mean_absolute_error(benchmark_actual, ma_pred)

    # calculates the mean squared error regression loss
    ma_rmse = np.sqrt(mean_squared_error(benchmark_actual, ma_pred))

    # calculates r² 
    ma_r2 = r2_score(benchmark_actual, ma_pred)

    # computes metrics for linear trend model
    # calculates the mean absolute error regression loss
    trend_mae = mean_absolute_error(benchmark_actual, trend_pred)

    # calculates the mean squared error regression loss
    trend_rmse = np.sqrt(mean_squared_error(benchmark_actual,trend_pred))

    # calculates r² 
    trend_r2 = r2_score(benchmark_actual, trend_pred)

    # updates the prediction experiment table
    update_prediction_experiment_table(model_type=config.model, prediction_target=",".join(config.targets),
        prediction_horizon=config.horizon, lookback_steps=config.lookback_steps, training_samples=len(train_ids),
        validation_samples=len(validation_ids), test_samples=len(test_ids), train_split=config.train_split,
        validation_split=config.validation_split, test_split=config.test_split, mae=float(mae), rmse=float(rmse),
        r2=float(r2), persistence_mae=float(pers_mae), persistence_rmse=float(pers_rmse), persistence_r2=float(pers_r2),
        moving_average_mae=float(ma_mae), moving_average_rmse=float(ma_rmse), moving_average_r2=float(ma_r2), 
        linear_trend_mae=float(trend_mae), linear_trend_rmse=float(trend_rmse),linear_trend_r2=float(trend_r2)
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),

        "plots":plot_data["plots"],  

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
        },
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