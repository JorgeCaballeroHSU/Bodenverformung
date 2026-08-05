# imports required libraries
from database.database import Database
import json
from datetime import datetime
import dataframe as pd
import numpy as np

# Defines the models that can be used for training
from models.models import (LSTMForecaster, StackedLSTMForecaster, BiLSTMForecaster, EncoderDecoderLSTMForecaster,
                           Seq2SeqAttentionLSTMForecaster, CNNLSTMForecaster, GRUForecaster, DeepARForecaster, TFTForecaster)

##### AUXILIARY FUNCTIONS FOR TRAINING PAGE #####

# dataset loader
def fetch_training_data():
    """
        Fetches training data from the database, joining measurements, tests, and samples tables.
        Returns a list of dictionaries containing the relevant data for training.
        Each dictionary represents a row of data with keys corresponding to column names.
        The data is ordered by test_id and time_s to ensure proper sequencing for time series analysis
    """

    # initializes a Database object to handle database operations
    db = Database()
    
    # opens a connection to the database and fetches the training data using a SQL query, ensuring that the connection is closed afterward
    try:

        # opens a connection to the database
        db.openConnection()

        # executes a SQL query to fetch training data, joining measurements, tests, and samples tables
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

    # catches any exceptions that occur during the database operations, prints an error message, 
    # and returns an empty list to indicate that no data could be fetched
    except Exception as e:

        # prints an error message indicating that there was an issue fetching the training data from the database
        print(f"Error fetching training data: {e}")
        return []

    # ensures that the database connection is closed after the operations are complete,
    # regardless of whether they were successful or if an exception was raised
    finally:

        # closes the database connection to free up resources and maintain good database hygiene
        db.closeConnection()

# sequence generator for training
def sequence_generator(df: pd.DataFrame, inputs: list, targets: list, lookback: int, horizon: int)-> object:
    """
    Generates sequences of input and target values for training a model.
    Arguments:
    - df: The DataFrame containing the data.
    - inputs: List of input feature column names.
    - targets: List of target feature column names.
    - lookback: Number of time steps to look back for input sequences.
    - horizon: Number of time steps to look ahead for target values.
    Yields tuples of (input_sequence, target_value) for each sequence in the DataFrame.
    """

    # calculates the total number of unique tests in the DataFrame and initializes a counter for total sequences generated
    total_tests = df["test_id"].nunique()
    total_sequences = 0

    # iterates over each unique test_id in the DataFrame, grouping the data by test_id
    for idx, (_, group) in enumerate(df.groupby("test_id"), start=1):

        # prints the progress of processing each test, including the current index and total number of tests, as well as the number of rows in the current group
        print(f"Processing test {idx}/{total_tests}, "f"rows={len(group)}")

        # converts the input and target columns of the current group to numpy arrays of type float32 for efficient processing
        input_values = group[inputs].to_numpy(dtype=np.float32)
        target_values = group[targets].to_numpy(dtype=np.float32)

        # iterates over the range of indices in the current group, generating sequences of input and target values based on the specified lookback and horizon
        for i in range(lookback, len(group) - horizon):

            # increments the total_sequences counter for each generated sequence
            total_sequences += 1

            # prints the total number of sequences generated every 50,000 sequences to provide feedback on the progress of sequence generation
            if total_sequences % 50000 == 0: print(f"{total_sequences:,} sequences generated")

            # yields a tuple containing the input sequence (from i-lookback to i) and the corresponding target value (at i+horizon)
            yield (input_values[i-lookback:i], target_values[i+horizon])


# builds the model based on the configuration provided
def build_model(config: object, n_features: int)->object:
    """
    Builds and returns the model based on the configuration provided.
    Arguments:
    - config: The configuration object containing model details.
    - n_features: The number of features in the input data.
    Returns the initialized model."""

    # checks the model type specified in the configuration and initializes the corresponding model with the provided parameters
    if config.model == "LSTMForecaster":

        # initializes and returns an instance of the LSTMForecaster model with the specified parameters
        return LSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    # checks if the model type is "EncoderDecoderLSTMForecaster" and initializes the corresponding model
    elif config.model == "StackedLSTMForecaster":

        # initializes and returns an instance of the StackedLSTMForecaster model with the specified parameters
        return StackedLSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    # checks if the model type is "BiLSTMForecaster" and initializes the corresponding model
    elif config.model == "BiLSTMForecaster":

        # initializes and returns an instance of the BiLSTMForecaster model with the specified parameters
        return BiLSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    # checks if the model type is "EncoderDecoderLSTMForecaster" and initializes the corresponding model
    elif config.model == "CNNLSTMForecaster":

        # initializes and returns an instance of the CNNLSTMForecaster model with the specified parameters
        return CNNLSTMForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    # checks if the model type is "Seq2SeqAttentionLSTMForecaster" and initializes the corresponding model
    elif config.model == "GRUForecaster":

        # initializes and returns an instance of the GRUForecaster model with the specified parameters
        return GRUForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    # checks if the model type is "DeepARForecaster" and initializes the corresponding model
    elif config.model == "DeepARForecaster":

        # initializes and returns an instance of the DeepARForecaster model with the specified parameters
        return DeepARForecaster(
            input_steps=config.lookback_steps,
            n_features=n_features,
            n_targets=len(config.targets),
            units=config.units,
            dropout=config.dropout,
            learning_rate=config.learning_rate
        )

    # checks if the model type is "TFTForecaster" and initializes the corresponding model
    raise ValueError(f"Unsupported model: {config.model}")

# updates database prediction_experiment table with the new experiment
def update_prediction_experiment_table(config: object, eval_X: object, mae: float, rmse: float, 
                                       r2: float, pers_mae: float, pers_rmse: float, pers_r2: float)->int:
    """
    Updates the prediction_experiment table in the database with the new experiment details.
    Arguments:
    - config: The configuration object containing experiment details.
    - eval_X: The evaluation data used for the experiment.
    - mae: Mean Absolute Error of the model.
    - rmse: Root Mean Square Error of the model.
    - r2: R-squared value of the model.
    - pers_mae: Mean Absolute Error of the persistence model.
    - pers_rmse: Root Mean Square Error of the persistence model.
    - pers_r2: R-squared value of the persistence model.
    Returns the ID of the newly inserted experiment.
    """

    # creates a new instance of the Database class
    db = Database()

    try:
        # opens a connection to the database
        db.openConnection()

        # inserts the new experiment details into the prediction_experiments table and retrieves the experiment_id
        experiment_id, _ = db.insertItemsTable(
            """
            INSERT INTO prediction_experiments
            (experiment_name, model_type, prediction_target, prediction_horizon, lookback_steps, training_samples,
            mae, rmse, r2, benchmark_mae, benchmark_rmse, benchmark_r2, created_at, experiment_config )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"{config.model}_{datetime.now()}", config.model, ",".join(config.targets), config.horizon,
                config.lookback_steps, len(eval_X), float(mae), float(rmse), float(r2), float(pers_mae),
                float(pers_rmse), float(pers_r2), datetime.now().isoformat(),
                json.dumps(
                    {
                        "inputs": config.inputs,
                        "static_inputs": config.static_inputs,
                        "targets": config.targets,
                        "epochs": config.epochs,
                        "batch_size": config.batch_size,
                        "learning_rate": config.learning_rate,
                        "dropout": config.dropout,
                        "units": config.units
                    }
                )
            )
        )

        # returns the experiment_id of the newly inserted experiment
        return experiment_id

    except Exception as e:

        # prints an error message if there is an exception while updating the prediction_experiment table
        print(f"Error updating prediction_experiment table: {e}")

    finally:

        # closes the database connection
        db.closeConnection()

# stores prediction samples
def store_prediction_samples(experiment_id: int, actual: list, predictions: list)->None:
    """
    Stores the prediction samples in the database for a given experiment.
    Arguments:
    - experiment_id: The ID of the experiment for which the predictions are being stored.
    - actual: The actual target values.
    - predictions: The predicted values generated by the model.
    """
    
    # creates a new instance of the Database class
    db = Database()

    try:
        # opens a connection to the database
        db.openConnection()

        # retrieves the actual target values from the evaluation data
        for actual_value, predicted_value in zip(actual[:500],predictions[:, 0][:500]):

            # inserts the actual and predicted values into the predictions table in the database
            db.insertItemsTable(
                """INSERT INTO predictions(experiment_id, measurement_id, actual_value, predicted_value, prediction_error)
                VALUES (?, ?, ?, ?, ?)""",
                (experiment_id, 0, float(actual_value), float(predicted_value), float(actual_value - predicted_value))
            )

    # handles any exceptions that occur during the database operations
    except Exception as e:

        # prints an error message if there is an exception while storing prediction samples
        print(f"Error storing prediction samples: {e}")

    finally:

        # closes the database connection
        db.closeConnection()

