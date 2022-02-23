# ------------------------------
# Imports
# ------------------------------

#from access_game_scores import read_game_scores, write_game_scores
#from access_game_settings import read_game_settings, write_game_settings
import numpy as np
from synth_view import View
from synth_model import Model

# ------------------------------
# Variables
# ------------------------------
SAMPLE_RATE = 44100
DEFAULT_ATTACK = 200
DEFAULT_DECAY = 200
DEFAULT_SUSTAIN = 500
DEFAULT_SUSTAIN_LEVEL = 50
DEFAULT_RELEASE = 200

debug_level = 1
# ------------------------------
# Classes
# ------------------------------

class Controller:
    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        self.waveform = "Sine"
        self.frequency = 440
        self.width = 100
        self.attack = DEFAULT_ATTACK
        self.decay = DEFAULT_DECAY
        self.sustain = DEFAULT_SUSTAIN
        self.sustain_level = DEFAULT_SUSTAIN_LEVEL
        self.release = DEFAULT_RELEASE
        self.view = View(self)
        self.model = Model(SAMPLE_RATE)
       
    def main(self):
        self._debug_1("In main of test controller")
        
        self.view.main()

    def on_request_waveform(self, waveform):
        self._debug_1("Set waveform requested: " + waveform)
        self.waveform = waveform
        note = self._change_note(self.waveform, self.frequency, self.width)    
        if not note is None:
            self.view.play_sound(note)        
        
    def on_request_frequency(self, frequency):
        self._debug_2("Set frequency to " + str(frequency))
        self.frequency = float(frequency)
        note = self._change_note(self.waveform, self.frequency, self.width)    
        if not note is None:
            self.view.play_sound(note)
            
    def on_request_width(self, width):
        if self.waveform == "Sawtooth" or self.waveform == "Square":
            self._debug_2("Set width to " + str(width))
            self.width = float(width)
            note = self._change_note(self.waveform, self.frequency, self.width)    
            if not note is None:
                self.view.play_sound(note)
        else:
            self._debug_1("Width of this waveform is fixed.")

    def on_request_attack(self, value):
        self._debug_1("Set attack to " + str(value))
        self.attack = int(value)
        self._change_envelope()
        
    def on_request_decay(self, value):
        self._debug_1("Set decay to " + str(value))
        self.decay = int(value)
        self._change_envelope()
        
    def on_request_sustain(self, value):
        self._debug_1("Set sustain to " + str(value))
        self.sustain = int(value)
        self._change_envelope()
        
    def on_request_sustain_level(self, value):
        self._debug_1("Set sustain level to " + str(value))
        self.sustain_level = int(value)
        self._change_envelope()
        
    def on_request_release(self, value):
        self._debug_1("Set release to " + str(value))
        self.release = int(value)
        self._change_envelope()
                    
    def on_request_play(self):
        self._debug_1("Play Sound requested")
              
    def on_request_save(self):
        self._debug_1("Save requested")
        
    def on_request_restore(self):
        self._debug_1("Restore requested")
    
    # ------------------------------
    # Local Helper Functions
    # ------------------------------

    def _change_note(self, waveform, frequency, width):
        if waveform == "Sine":
            note = self.model.sine_wave(float(frequency))
        elif waveform == "Triangle":
            note = self.model.triangle_wave(float(frequency))
        elif waveform == "Sawtooth":
            note = self.model.pwm_sawtooth_wave(float(frequency), width)
        elif waveform == "Square":
            note = self.model.pwm_square_wave(float(frequency), width)
        else:
            self._debug_1("Warning, waveform unknown: " + str(waveform))
            note = None
        return note
    
    def _change_envelope(self):
        new_envelope = self.model.change_envelope(self.attack, self.decay, self.sustain, self.sustain_level, self.release)
        self.view.show_envelope(new_envelope)
  
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print(message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print(message)

# ------------------------------
# App
# ------------------------------

synth = Controller()
synth.main()
     

