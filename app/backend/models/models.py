import numpy as np
from abc import ABC, abstractmethod
from tensorflow.keras.models import (Sequential,Model)
from tensorflow.keras.layers import (Input,Dense,Dropout,LSTM,GRU, Bidirectional, RepeatVector, TimeDistributed, Attention,
                                     Concatenate, Conv1D, MaxPooling1D)
from tensorflow.keras.optimizers import Adam
from neuralforecast.models import TFT

class BaseModel(ABC):

    def __init__(self):
        self.model = None
        self.train_history = None

    @abstractmethod
    def build(self):
        """Build the model architecture."""
        pass

    def fit(self, X_train, y_train, **kwargs):
        """Train model."""

        # trains the model
        self.train_history = self.model.fit( X_train, y_train, **kwargs)

        # returns train history of the model
        return self.train_history

    def predict(self, X):
        """Predict values."""

        # provides the results of the prediction
        return self.model.predict(X)

    def evaluate(self, X_test, y_test, **kwargs):
        """Evaluate model."""

        # returns model evaluation results
        return self.model.evaluate(X_test, y_test, **kwargs)

    def summary(self):
        """Show model summary."""

        # returns summary of the model
        return self.model.summary()

    def save(self, filepath):
        """Save model."""

        # saves the model in the indicated path
        self.model.save(filepath)

    def load_weights(self, filepath):
        """Load model weights."""

        # loads the model from the indicated path
        self.model.load_weights(filepath)


class LSTMForecaster(BaseModel):

    def __init__(self, input_steps: int, n_features: int, units: int = 64, dropout: float = 0.2, learning_rate: float = 0.001):

        super().__init__()

        # defines hyperparameters of the model
        self.input_steps = input_steps
        self.n_features = n_features
        self.units = units
        self.dropout = dropout
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # defines the model architecture
        self.model = Sequential([
            LSTM(
                units=self.units,
                input_shape=(self.input_steps,self.n_features)
            ),
            Dropout(self.dropout),
            Dense(32, activation="relu"),
            Dense(1)
        ])

        # compiles the model
        self.model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss="mse",
            metrics=["mae"]
        )


class StackedLSTMForecaster(BaseModel):

    def __init__(self, input_steps: int, n_features: int, units: int = 64, dropout: float = 0.2, learning_rate: float = 0.001):

        super().__init__()

        # defines the hyperparameters of the model
        self.input_steps = input_steps
        self.n_features = n_features
        self.units = units
        self.dropout = dropout
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # defines the architecture of the model
        self.model = Sequential([
            
            LSTM(# First LSTM layer
                self.units,
                return_sequences=True,
                input_shape=(self.input_steps,self.n_features)            ),
            Dropout(self.dropout),
            LSTM(self.units, return_sequences=True),# Second LSTM layer
            Dropout(self.dropout),
            LSTM(self.units),# Third LSTM layer
            Dropout(self.dropout),
            Dense(32, activation="relu"),
            Dense(1)
        ])

        self.model.compile(
            optimizer=Adam(
                learning_rate=self.learning_rate
            ),
            loss="mse",
            metrics=["mae"]
        )

class BiLSTMForecaster(BaseModel):

    def __init__(self, input_steps: int, n_features: int, units: int = 64, dropout: float = 0.2, learning_rate: float = 0.001):

        super().__init__()

        # defines the hyperparameters 
        self.input_steps = input_steps
        self.n_features = n_features
        self.units = units
        self.dropout = dropout
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # defines the architecture of the model
        self.model = Sequential([
            Bidirectional(LSTM(self.units), input_shape=(self.input_steps, self.n_features)),
            Dropout(self.dropout),
            Dense(32, activation="relu"),
            Dense(1)])

        # compiles the model
        self.model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss="mse", metrics=["mae"])

class EncoderDecoderLSTMForecaster(BaseModel):

    def __init__(self, input_steps: int, output_steps: int, n_features: int, units: int = 64, dropout: float = 0.2, 
                 learning_rate: float = 0.001):

        super().__init__()

        # defines the hyperparameters of the model
        self.input_steps = input_steps
        self.output_steps = output_steps
        self.n_features = n_features
        self.units = units
        self.dropout = dropout
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # defines the architecture of the model
        self.model = Sequential([
            LSTM(self.units, input_shape=(self.input_steps, self.n_features)),# Encoder
            Dropout(self.dropout),
            RepeatVector(self.output_steps),            # Repeat context vector
            LSTM(self.units, return_sequences=True),    # Decoder
            Dropout(self.dropout),
            TimeDistributed(Dense(1))                   # Output layer
        ])

        # compiles the model
        self.model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss="mse", metrics=["mae"])

class Seq2SeqAttentionLSTMForecaster(BaseModel):

    def __init__(self, input_steps: int, output_steps: int, n_features: int, units: int = 64, learning_rate: float = 0.001):

        super().__init__()

        # defines hyperparameter for the model
        self.input_steps = input_steps
        self.output_steps = output_steps
        self.n_features = n_features
        self.units = units
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # Encoder
        encoder_inputs = Input(shape=(self.input_steps, self.n_features))
        encoder_outputs, state_h, state_c = LSTM(self.units, return_sequences=True, return_state=True)(encoder_inputs)

        # Decoder Input
        decoder_inputs = Input(shape=(self.output_steps, 1))
        decoder_outputs = LSTM(self.units, return_sequences=True)(decoder_inputs, initial_state=[state_h, state_c])

        # Attention Layer
        attention = Attention()([decoder_outputs, encoder_outputs])

        # Combine Decoder and Attention
        decoder_combined = Concatenate()([decoder_outputs, attention])

        outputs = TimeDistributed(Dense(1))(decoder_combined)

        # defines the architecture of the model
        self.model = Model(inputs=[encoder_inputs,decoder_inputs], outputs=outputs)

        # compiles the model
        self.model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss="mse", metrics=["mae"])

class CNNLSTMForecaster(BaseModel):

    def __init__(self, input_steps: int, n_features: int, filters: int = 64, kernel_size: int = 3, units: int = 64,
                 dropout: float = 0.2, learning_rate: float = 0.001):

        super().__init__()

        # defines the hyperparameters for the model
        self.input_steps = input_steps
        self.n_features = n_features
        self.filters = filters
        self.kernel_size = kernel_size
        self.units = units
        self.dropout = dropout
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # defines the architecture of the model
        self.model = Sequential([
            Conv1D(filters=self.filters, kernel_size=self.kernel_size, activation="relu", input_shape=(self.input_steps, self.n_features)),
            MaxPooling1D(pool_size=2),
            LSTM(self.units),
            Dropout(self.dropout),
            Dense(32, activation="relu"),
            Dense(1)
        ])

        # compiles the model
        self.model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss="mse", metrics=["mae"])

class DeepARForecaster(BaseModel):

    def __init__(self, input_steps: int, n_features: int, units: int = 64, dropout: float = 0.2,learning_rate: float = 0.001):

        super().__init__()

        # defines the hyperparameters of the model
        self.input_steps = input_steps
        self.n_features = n_features
        self.units = units
        self.dropout = dropout
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # defines the architecture of the model
        self.model = Sequential([LSTM(self.units, input_shape=(self.input_steps,self.n_features)), 
                                 Dropout(self.dropout),
                                 Dense(32, activation="relu"),
                                 Dense(1)# mean forecast
        ])

        self.model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss="mse", metrics=["mae"])

class TFTForecaster(BaseModel):

    def __init__(self, horizon: int, input_size: int, hidden_size: int = 64):

        super().__init__()

        # defines the hyperparameters for the model
        self.horizon = horizon
        self.input_size = input_size
        self.hidden_size = hidden_size

        # builds the model
        self.build()

    def build(self):

        # defines the model
        self.model = TFT(
            h=self.horizon,
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            learning_rate=1e-3,
            max_steps=1000
        )

class XLSTMForecaster(BaseModel):

    def __init__(self, input_steps: int, n_features: int, hidden_size: int = 64, num_layers: int = 2):

        super().__init__()

        # defines the hyperparameters for the model
        self.input_steps = input_steps
        self.n_features = n_features
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # builds the model
        self.build()

    def build(self):
        """Build xLSTM architecture."""

        # TODO:
        # instantiate xLSTM model here

        pass

class GRUForecaster(BaseModel):

    def __init__(self, input_steps: int, n_features: int, units: int = 64, dropout: float = 0.2, learning_rate: float = 0.001):

        super().__init__()

        # defines the hyperparameters of the model
        self.input_steps = input_steps
        self.n_features = n_features
        self.units = units
        self.dropout = dropout
        self.learning_rate = learning_rate

        # builds the model
        self.build()

    def build(self):

        # defines the architecture of the model
        self.model = Sequential([
            GRU(units=self.units, input_shape=(self.input_steps, self.n_features)),
            Dropout(self.dropout),
            Dense(32, activation="relu"),
            Dense(1)
        ])

        # compiles the model
        self.model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss="mse",metrics=["mae"] )