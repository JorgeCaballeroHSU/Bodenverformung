# this files contains three naive forecast equations use for benchmarking purposes
# imports required libraries
import numpy as np

# implements the persistence forcast class
class PersistenceForecast:

    def predict(self, series, horizon=1):

        if len(series) == 0:
            return 0.0

        return series[-1]

# implements the moving average forecast 
class MovingAverageForecast:

    def __init__(self, window=5):

        # defines the size of the window for the moving average
        self.window = window

    # calculates the predicted value
    def predict(self, series,horizon=1):

        if len(series) == 0:

            return 0.0

        # returns the moving average according to the provide window
        return np.mean(series[-self.window:])

# implements linear trend forecast class
class LinearTrendForecast:

    def predict(
            self,
            series,
            horizon=1):

        if len(series) == 0:
            return 0.0

        if len(series) == 1:
            return series[-1]

        last = series[-1]
        previous = series[-2]

        slope = last - previous

        return last + horizon * slope