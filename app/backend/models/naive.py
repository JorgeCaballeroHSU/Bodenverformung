# this files contains three naive forecast equations use for benchmarking purposes
# imports required libraries
import numpy as np

# implements the persistence forcast class
class PersistenceForecast:

    # provides prediction 
    def predict(self, series):

        return series[-1]

# implements the moving average forecast 
class MovingAverageForecast:

    def __init__(self, window=5):

        # defines the size of the window for the moving average
        self.window = window

    # calculates the predicted value
    def predict(self, series):

        # returns the moving average according to the provide window
        return np.mean(series[-self.window:])

# implements linear trend forecast class
class LinearTrendForecast:

    # gers the predictions
    def predict(self, series):

        # gets the values to calculate the slope
        last = series[-1]
        previous = series[-2]

        # calculates the slop
        slope = last - previous

        # returns the prediction
        return last + slope