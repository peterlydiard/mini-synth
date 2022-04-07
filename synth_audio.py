# ------------------------------
# Imports
# ------------------------------
import pygame
import pygame.mixer
import pygame.sndarray
import numpy as np
import time

# ------------------------------
# Variables
# ------------------------------
# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 1
last_output_time = 0
sound = None

def initialise_audio():
    _debug_2("In initialise_audio()")
    # initialise stereo mixer (default)
    pygame.mixer.init()
    pygame.init()

def play_sound(wave):
    _debug_2("In play_sound()")
    global last_output_time, sound
    
    # Reduce demand on audio output by fading out previous note.
    if not sound is None:
        # sound.fadeout(100)
        sound = None
    # Ensure that highest value is in 16-bit range
    max_level = np.max(np.abs(wave))
    if max_level == 0:
        _debug_1("WARNING: zero waveform in play_sound().")
        return -1
    
    audio = wave * (2**15 - 1) / max_level
    # Convert to 16-bit data
    audio = audio.astype(np.int16)
    # create a pygame Sound object and play it.
    sound = pygame.sndarray.make_sound(audio)
    sound.play()
    now = time.perf_counter()
    _debug_2("Time since last note = " + str(now-last_output_time))
    last_output_time = now       
    return 0

def stop_audio_output():
    _debug_2("In stop_audio_output()")
    pygame.mixer.music.stop()
    
def _debug_1(message):
    global debug_level
    if debug_level >= 1:
        print("synth_audio.py: " + message)
    
def _debug_2(message):
    global debug_level
    if debug_level >= 2:
        print("synth_audio.py: " + message)
