import pygame
import pygame.mixer
import pygame.sndarray
#import FFT
import math
import string
import copy
# import pylab
# import numpy
import numpy as np
# import simpleaudio as sa
from scipy import signal

#import synth_model
#from synth_model import sine_wave, triangle_wave, sawtooth_wave, square_wave

######################### Global constants #########################

SAMPLE_RATE = 44100

####################################################################
pygame.mixer.init ()
pygame.init ()


def get_sound ():
    """Load the sound file"""
    s = pygame.mixer.Sound ("chicken.wav")
    # t = pygame.sndarray.array (s)
    return s
    
def play_sound(s):
    s.play ()

def test_1():
    print("chargement du son")
    s = get_sound ()
    print ("duree : ", s.get_length (), " secondes")
    print ("musique")
    play_sound (s)
    pygame.time.delay (6000)

# test_1 ()

# Create a unit-amplitude sine wave, stereo by default.
def sine_wave(frequency, duration, stereo=True):
    # Generate array with duration*sample_rate steps, ranging between 0 and duration
    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), False)
    # Generate a sine wave
    note = np.sin(2 * np.pi * frequency * t)
    if stereo == True:
        note = np.column_stack((note, note))
    return note

# Convert mono or stereo waveform(s) into a pygame Sound object
def create_sound(wave, level=1.0):
    # scale wave according to level
    wave = wave * level
    # Ensure that highest value is in 16-bit range
    audio = wave * (2**15 - 1) / np.max(np.abs(wave))
    # Convert to 16-bit data
    audio = audio.astype(np.int16)
    # create a pygame Sound object
    sound = pygame.sndarray.make_sound(audio)
    return sound

frequency = 440  # Our played note will be 440 Hz
seconds = 1  # Note duration of 1 seconds

    
print("\nSine wave of " + str(frequency) + "Hz")

wave = sine_wave(frequency, seconds)

left = np.hsplit(wave,2)[0]

sound = create_sound(wave)

sound.play()

wave = sine_wave(460, seconds)

left = np.hsplit(wave,2)[0]

sound = create_sound(wave)

sound.play()

'''
pygame.time.delay(2000)

print("\nTriangle wave of " + str(frequency) + "Hz")

wave = triangle_wave(frequency, seconds)

sound = create_sound(wave)

sound.play()

pygame.time.delay(2000)

print("\nSawtooth wave of " + str(frequency) + "Hz")

wave = sawtooth_wave(frequency, seconds)

sound = create_sound(wave)

sound.play()

pygame.time.delay(2000)

print("\nSquare wave of " + str(frequency) + "Hz")

wave = square_wave(frequency, seconds)

sound = create_sound(wave)

sound.play()
'''

