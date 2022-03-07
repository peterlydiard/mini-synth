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
MAX_VOICES = 12
DEFAULT_FREQUENCY = 440
DEFAULT_ATTACK = 20
DEFAULT_DECAY = 20
DEFAULT_SUSTAIN = 100
DEFAULT_SUSTAIN_LEVEL = 50
DEFAULT_RELEASE = 20

# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 1
# ------------------------------
# Classes
# ------------------------------

# Note: Voice tones are stored separately in the model, because of their size.
class Voice_Parameters:
    def __init__(self):
        self.number = 0 # This number may be unrelated to the position of the voice in any lists.
        self.name = "Unused"
        self.waveform = "Sine"
        self.width = 100        
        self.attack = DEFAULT_ATTACK
        self.decay = DEFAULT_DECAY
        self.sustain_time = DEFAULT_SUSTAIN
        self.sustain_level = DEFAULT_SUSTAIN_LEVEL
        self.release = DEFAULT_RELEASE        
        
class Controller:
    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        self.frequency = DEFAULT_FREQUENCY
        self.voices = []
        self.voice_index = 0
        self.view = View(self)
        self.model = Model(SAMPLE_RATE)
        
    def main(self):
        self._debug_1("In main of controller")
        # Create a list of voice parameter objects for each voice
        for voice_index in range(MAX_VOICES):
            voice_params = Voice_Parameters()
            self.voices.append(voice_params)
        self.model.main()
        self.view.main()

    def on_request_waveform(self, waveform):
        self._debug_1("Set waveform requested: " + waveform)
        self.voices[self.voice_index].waveform = waveform
        note = self._change_note(self.voice_index)    
        if not note is None:
            self.view.play_sound(note)        
        
    def on_request_note(self, voice, key):
        self._debug_1("Getting note for voice, key " + str(voice) + ", " + str(key))
        tone = self.model.fetch_tone(voice, key)
        note = self.model.apply_envelope(tone)   
        if not note is None:
            self.view.play_sound(note)
            
    def on_request_frequency(self, frequency):
        self._debug_2("Set frequency to " + str(frequency))
        self.frequency = float(frequency)
        note = self._change_note(self.voice_index)    
        if not note is None:
            self.view.play_sound(note)
                       
    def on_request_width(self, width):
        voice = self.voices[self.voice_index]
        if voice.waveform == "Sawtooth" or voice.waveform == "Square":
            self._debug_2("Set width to " + str(width))
            self.voices[self.voice_index].width = float(width)
            note = self._change_note(self.voice_index)    
            if not note is None:
                self.view.play_sound(note)
        else:
            self._debug_1("Width of this waveform is fixed.")

    def on_request_attack(self, value):
        self._debug_1("Set attack to " + str(value))
        self.voices[self.voice_index].attack = int(value)
        self._change_envelope()
        
    def on_request_decay(self, value):
        self._debug_1("Set decay to " + str(value))
        self.voices[self.voice_index].decay = int(value)
        self._change_envelope()
        
    def on_request_sustain(self, value):
        self._debug_1("Set sustain to " + str(value))
        self.voices[self.voice_index].sustain_time = int(value)
        self._change_envelope()
        
    def on_request_sustain_level(self, value):
        self._debug_1("Set sustain level to " + str(value))
        self.voices[self.voice_index].sustain_level = int(value)
        self._change_envelope()
        
    def on_request_release(self, value):
        self._debug_1("Set release to " + str(value))
        self.voices[self.voice_index].release = int(value)
        self._change_envelope()
                    
    def on_request_play(self):
        self._debug_1("Play Sound requested.")
        note = self._change_note(self.voice_index)    
        if not note is None:
            self.view.play_sound(note)
              
    def on_request_save(self):
        self._debug_1("Save requested")
        
    def on_request_restore(self):
        self._debug_1("Restore requested")
    
    def save_settings(self):
        names = values = []
        
    # ------------------------------
    # Local Helper Functions
    # ------------------------------

    def _change_note(self, voice_index):
        voice = self.voices[voice_index]
        if voice.waveform == "Sine":
            tone = self.model.sine_wave(float(self.frequency))
        elif voice.waveform == "Triangle":
            tone = self.model.triangle_wave(float(self.frequency))
        elif voice.waveform == "Sawtooth":
            tone = self.model.pwm_sawtooth_wave(float(self.frequency), voice.width)
        elif voice.waveform == "Square":
            tone = self.model.pwm_square_wave(float(self.frequency), voice.width)
        else:
            self._debug_1("Warning, waveform unknown: " + str(voice.waveform))
            tone = None
        
        note = self.model.apply_envelope(tone)
        return note
    
    def _change_envelope(self):
        new_envelope = self.model.change_envelope(self.voices[self.voice_index])
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
     

