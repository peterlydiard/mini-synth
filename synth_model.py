#import FFT
import math
import string
import copy
# import pylab
# import numpy
import numpy as np
# import simpleaudio as sa
#from scipy import signal


######################### Global constants #########################

SAMPLE_RATE = 44100

####################################################################

class Model:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
            
    # Create a unit-amplitude sine wave, stereo by default.
    def sine_wave(self, frequency, duration, stereo=True):
        #print("Sine wave freq, duration = " + str(frequency) + ", " + str(duration))
        # Generate array with duration*sample_rate steps, ranging between 0 and duration
        t = np.linspace(0, duration, int(duration * self.sample_rate), False)
        # Generate a sine wave
        note = np.sin(2 * np.pi * frequency * t)
        if stereo == True:
            note = np.column_stack((note, note))
        return note

    # Create a unit-amplitude sawtooth wave, stereo by default.
    def sawtooth_wave(self, frequency, duration, stereo=True):
        #print("Saw wave freq, duration = " + str(frequency) + ", " + str(duration))
        # Generate linear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        ramp = np.linspace(1.0, (2 * frequency * duration) + 1, int(duration * self.sample_rate), False)
        # Generate a sawtooth wave
        note = (ramp % 2.0) - 1.0
        if stereo == True:
            note = np.column_stack((note, note))
        return note


    # Create a unit-amplitude trianle wave, stereo by default.
    def triangle_wave(self, frequency, duration, stereo=True):
        # Generate linear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        ramp = np.linspace(0, (2 * frequency * duration), int(duration * self.sample_rate), False)
        # Generate a triangle wave
        note = abs(((2 * ramp + 3 ) % 4.0) - 2) - 1
        if stereo == True:
            note = np.column_stack((note, note))
        return note


    # Create a unit-amplitude square wave, stereo by default.
    def square_wave(self, frequency, duration, stereo=True):
        #print("Square wave freq, duration = " + str(frequency) + ", " + str(duration))
        # Generate inear ramp with duration*sample_rate steps, ranging between 0 and duration
        t = np.linspace(0, duration, int(duration * self.sample_rate), False)
        # Generate a square wave, clip sine to avoid using scipy library.
        note = np.clip(1000 * np.sin(2 * np.pi * frequency * t), -1.0, 1.0)
        if stereo == True:
            note = np.column_stack((note, note))
        return note
    
    # Create a unit-amplitude sawtooth wave with pulse width control, stereo by default.
    def pwm_sawtooth_wave(self, frequency, width, duration, stereo=True):
        #print("Saw wave freq, width, duration = " + str(frequency) + ", " + str(width)+ ", " + str(duration))
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * duration) + 2 - width/100, int(duration * self.sample_rate), False)
        # Generate a sawtooth wave
        note = np.clip((100/width) * ((ramp % 2.0) + width/100 - 2.0), -1.0, 1.0)
        if stereo == True:
            note = np.column_stack((note, note))
        return note
    
    # Create a unit-amplitude square wave with pulse width control, stereo by default.
    def pwm_square_wave(self, frequency, width, duration, stereo=True):
        #print("Square wave freq, duration = " + str(frequency) + ", " + str(duration))
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * duration) + 2 - width/100, int(duration * self.sample_rate), False)
        # Generate a square wave, clip sine to avoid using scipy library.
        note = np.clip(1000 * ((ramp % 2.0) + (width/100) - 2.0), -1.0, 1.0)
        if stereo == True:
            note = np.column_stack((note, note))
        return note

#------------------------- Module Test Funcctions -------------------------
if __name__ == "__main__":
    print("Calculating test waveforms: sine1,sine2, square1, square2, sawtooth1, sawtooth2, triangle1 & triangle2.")
    model = Model(SAMPLE_RATE)
    frequency = 200
    width = 0.5
    duration = 1
    # Generate mono waveforms
    sine1 = model.sine_wave(frequency, duration, False)
    square1 = model.square_wave(frequency, duration, False)
    sawtooth1 = model.sawtooth_wave(frequency, duration, False)
    triangle1 = model.triangle_wave(frequency, duration, False)
    #Generate stereo waveforms
    sine2 = model.sine_wave(frequency, duration)
    square2 = model.square_wave(frequency, duration)
    sawtooth2 = model.sawtooth_wave(frequency, duration)
    triangle2 = model.triangle_wave(frequency, duration)
    
    square3 = model.pwm_square_wave(frequency, width, duration, False)
    