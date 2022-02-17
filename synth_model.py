#import FFT
import math
import string
import copy
# import pylab
# import numpy
import numpy as np
# import simpleaudio as sa
from scipy import signal


######################### Global constants #########################

SAMPLE_RATE = 44100

####################################################################

class Model:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
            
    # Create a unit-amplitude sine wave, stereo by default.
    def sine_wave(self, frequency, duration, stereo=True):
        # Generate array with duration*sample_rate steps, ranging between 0 and duration
        t = np.linspace(0, duration, int(duration * self.sample_rate), False)
        # Generate a sine wave
        note = np.sin(2 * np.pi * frequency * t)
        if stereo == True:
            note = np.column_stack((note, note))
        return note

    # Create a unit-amplitude sawtooth wave, stereo by default.
    def sawtooth_wave(self, frequency, duration, stereo=True):
        print(" wave freq, duration = " + str(frequency) + ", " + str(duration))
        # Generate linear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        t = np.linspace(0, (2 * frequency * duration), int(duration * self.sample_rate), False)
        # t = np.linspace(0, 2000.1, 100, False)
        # Generate a sawtooth wave
        note = (t % 2.0) - 1.0
        if stereo == True:
            note = np.column_stack((note, note))
        return note


    # Create a unit-amplitude trianle wave, stereo by default.
    def triangle_wave(self, frequency, duration, stereo=True):
        # Generate linear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        t = np.linspace(0, (2 * frequency * duration), int(duration * SAMPLE_RATE), False)
        # Generate a triangle wave
        note = 2 * abs((t % 2.0) - 1.0) - 1.0
        if stereo == True:
            note = np.column_stack((note, note))
        return note


    # Create a unit-amplitude square wave, stereo by default.
    def square_wave(self, frequency, duration, stereo=True):
        # Generate inear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        t = np.linspace(0, (2 * frequency * duration), int(duration * SAMPLE_RATE), False)
        # Generate a square wave
        note = signal.square(2 * np.pi * frequency * t)
        if stereo == True:
            note = np.column_stack((note, note))
        return note


if __name__ == "__main__":
    model = Model(SAMPLE_RATE)
    note = model.sine_wave(444.3, 10)