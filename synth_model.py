#import FFT
import math
import string
import copy
# import pylab
# import numpy
import numpy as np
# import simpleaudio as sa
#from scipy import signal


######################### Global variables #########################

FREQUENCY = 220    # Hz
WIDTH = 50
MAX_DURATION = 5000
STEREO = True
ATTACK = 200
DECAY = 200
SUSTAIN_TIME = 500
SUSTAIN_LEVEL = 50
RELEASE = 100
debug_level = 1

####################################################################

class Model:
    def __init__(self, sample_rate, frequency=FREQUENCY, width=WIDTH, duration=MAX_DURATION, stereo=STEREO,
                 attack=ATTACK, decay=DECAY, sustain_time=SUSTAIN_TIME, sustain_level=SUSTAIN_LEVEL, release=RELEASE):
        self.sample_rate = sample_rate # Hz
        self.frequency = frequency # Hz
        self.width = width       # range is 0..100
        self.duration = duration # milliseconds
        self.stereo = stereo     # Boolean
        self.attack = attack     # milliseconds
        self.decay = decay       # milliseconds
        self.sustain_time = sustain_time   # milliseconds
        self.sustain_level = sustain_level # range is 0..100
        self.release = release   # milliseconds
        self.envelope = np.zeros((400 + int(sample_rate * MAX_DURATION / 1000)), dtype=float)


    # Create a unit-amplitude sine wave, stereo by default.
    def sine_wave(self, frequency, stereo=True):
        self._debug_2("Sine wave freq, duration (ms) = " + str(frequency) + ", " + str(self.duration))
        self.frequency = frequency
        self.stereo = stereo
        # Generate array with duration*sample_rate steps, ranging between 0 and duration
        times_msec = np.linspace(0, self.duration, int(self.sample_rate * self.duration / 1000), False)
        self._debug_2("No. of samples = " + str(len(times_msec)))
        # Generate a sine wave
        radians_per_msec = 2 * np.pi * frequency / 1000
        note = np.sin(radians_per_msec * times_msec)
        for i in range(len(note)):
            if self.envelope[i] > 0:
                note[i] *= self.envelope[i]
            else:
                note[i] = 0
                
        if stereo == True:
            note = np.column_stack((note, note))
        return note


    # Create a unit-amplitude trianle wave, stereo by default.
    def triangle_wave(self, frequency, stereo=True):
        self.frequency = frequency
        self.stereo = stereo        
        # Generate linear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        ramp = np.linspace(0, (2 * frequency * self.duration/1000), int(self.sample_rate * self.duration/1000), False)
        # Generate a triangle wave
        note = abs(((2 * ramp + 3 ) % 4.0) - 2) - 1
        # Apply amplitude envelope
        for i in range(len(note)):
            if self.envelope[i] > 0:
                note[i] *= self.envelope[i]
            else:
                note[i] = 0
                
        if stereo == True:
            note = np.column_stack((note, note))
        return note

    
    # Create a unit-amplitude sawtooth wave with pulse width control, stereo by default.
    def pwm_sawtooth_wave(self, frequency, width, stereo=True):
        #print("Saw wave freq, width, duration = " + str(frequency) + ", " + str(width)+ ", " + str(duration))
        self.frequency = frequency
        self.width = width
        self.stereo = stereo
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * self.duration/1000) + 2 - width/100,
                           int(self.sample_rate * self.duration / 1000), False)
        # Generate a sawtooth wave
        note = np.clip((100/width) * ((ramp % 2.0) + width/100 - 2.0), -1.0, 1.0)
        # Apply amplitude envelope
        for i in range(len(note)):
            if self.envelope[i] > 0:
                note[i] *= self.envelope[i]
            else:
                note[i] = 0
                
        if stereo == True:
            note = np.column_stack((note, note))
        return note
    
    
    # Create a unit-amplitude square wave with pulse width control, stereo by default.
    def pwm_square_wave(self, frequency, width, stereo=True):
        #print("Square wave freq, duration = " + str(frequency) + ", " + str(duration))
        self.frequency = frequency
        self.width = width
        self.stereo = stereo
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * self.duration / 1000) + 2 - width/100,
                           int(self.sample_rate * self.duration / 1000), False)
        # Generate a square wave, clip sine to avoid using scipy library.
        note = np.clip(1000 * ((ramp % 2.0) + (width/100) - 2.0), -1.0, 1.0)
        
        self._debug_2("No. of samples = " + str(len(note)))
        # Apply amplitude envelope
        for i in range(len(note)):
            if self.envelope[i] > 0:
                note[i] *= self.envelope[i]
            else:
                note[i] = 0
                
        if stereo == True:
            note = np.column_stack((note, note))
        return note
    
    # Apply the envelope amplitude to the tone to make a note
    def apply_envelope(tone, stereo=True):
        self.stereo = stereo
        self._debug_2("No. of samples = " + str(len(tone)))
        # Apply amplitude envelope
        for i in range(len(tone)):
            if self.envelope[i] > 0:
                note[i] = tone[i] * self.envelope[i]
            else:
                note[i] = 0
        # Duplicate note to make left and right channels if required.
        if stereo == True:
            note = np.column_stack((note, note))
        return note
    
        
    def change_envelope(self, attack, decay, sustain_time, sustain_level, release):
        self.attack = attack
        self.decay = decay
        self.sustain_time = sustain_time
        self.sustain_level = sustain_level / 100
        self.release = release
        self.duration = attack + decay + sustain_time + release
        self._debug_1("Duration = " + str(self.duration))
        # Generate array with duration*sample_rate steps, ranging between 0 and duration (milli-seconds)
        times_msec = np.linspace(0, self.duration, int(self.sample_rate * self.duration/1000), False)
        self._debug_2("No. of samples = " + str(len(times_msec)))
            
        attack_level_change = 1.6 * times_msec[1] / self.attack  
        decay_level_change = 1.6 * times_msec[1] / self.decay 
        release_level_change = 1.6 * times_msec[1] / self.release
        self._debug_2("Attack level change = " + str(attack_level_change))
        self._debug_2("Decay level change = " + str(decay_level_change))
        self._debug_2("Release level change = " + str( release_level_change))
        self._debug_2("Time step = " + str(times_msec[1]))
                
        level = 0.0
        for i in range(len(times_msec)):
            if times_msec[i] <= self.attack:
                level += attack_level_change * (1.24 - level)
                # print(str(i) + " Attack")
            elif times_msec[i] <= self.attack + self.decay:
                #print(str(i) + " Decay")
                level -= decay_level_change * (level + 0.1 - self.sustain_level)
                if level < self.sustain_level:
                    level = self.sustain_level
            elif times_msec[i] < self.attack + self.decay + self.sustain_time:
                #print(str(i) + " Sustain")
                level = self.sustain_level
            elif times_msec[i] < self.attack + self.decay + self.sustain_time + self.release:
                #print(str(i) + " Release")
                if level > 0:
                    level -= release_level_change * (level + 0.1)
            else:
                level = 0              
            self.envelope[i] = level
            
        for i in range(len(times_msec), len(self.envelope)):
             self.envelope[i] = 0
             
        return self.envelope


    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print(message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print(message)

#------------------------- Module Test Funcctions -------------------------
if __name__ == "__main__":
    SAMPLE_RATE = 1000 # Hz
    FREQUENCY = 220    # Hz
    WIDTH = 50
    DURATION = 5000
    STEREO = True
    ATTACK = 200
    DECAY = 200
    SUSTAIN_TIME = 500
    SUSTAIN_LEVEL = 50
    RELEASE = 100
    
    model = Model(SAMPLE_RATE, FREQUENCY, WIDTH, DURATION, STEREO, ATTACK, DECAY, SUSTAIN_TIME, SUSTAIN_LEVEL, RELEASE)
    
    print("Calculating test waveforms: sine1,sine2, square1, square2, sawtooth1, sawtooth2, triangle1 & triangle2.")
 
    # Generate mono waveforms
    model.duration = DURATION
    sine1 = model.sine_wave(FREQUENCY, False)
    #square1 = model.square_wave(FREQUENCY, DURATION, False)
    #sawtooth1 = model.sawtooth_wave(FREQUENCY, DURATION, False)
    #triangle1 = model.triangle_wave(FREQUENCY, DURATION, False)
    
    #Generate stereo waveforms
    #sine2 = model.sine_wave(FREQUENCY, DURATION)
    #square2 = model.square_wave(FREQUENCY, DURATION)
    #sawtooth2 = model.sawtooth_wave(FREQUENCY, DURATION)
    #triangle2 = model.triangle_wave(FREQUENCY, DURATION)
    
    #sawtooth3 = model.pwm_sawtooth_wave(FREQUENCY, WIDTH, DURATION)
    #square3 = model.pwm_square_wave(FREQUENCY, WIDTH, DURATION, False)
    
    envelope = model.change_envelope(10, 10, 20, 70, 10)
    
    for i in range(100):
        print(str(i) + ": " + str(envelope[i]))
        
    