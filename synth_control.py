# ------------------------------
# Imports
# ------------------------------

#from access_game_scores import read_game_scores, write_game_scores
#from access_game_settings import read_game_settings, write_game_settings

#from synth_model import Model
from synth_view import View
from synth_model import Model

# ------------------------------
# Variables
# ------------------------------
SAMPLE_RATE = 44100

# ------------------------------
# Classes
# ------------------------------


class Controller:
    def __init__(self):
        self.waveform = "Sine"
        self.frequency = 440
        self.view = View(self)
        self.model = Model(SAMPLE_RATE)
    
    def main(self):
        print("In main of test controller")
        
        self.view.main()

    def on_request_waveform(self, waveform):
        print("Set waveform requested: " + waveform)
        self.waveform = waveform
        note = self.__change_note(self.waveform, self.frequency)    
        if not note is None:
            self.view.play_sound(note)        
        
    def on_request_frequency(self, frequency):
        print("Set frequency to " + str(frequency))
        self.frequency = float(frequency)
        note = self.__change_note(self.waveform, self.frequency)    
        if not note is None:
            self.view.play_sound(note)
        
    def on_request_play(self):
        print("Play Sound requested")
              
    def on_request_save(self):
        print("Save game requested")
        
    def on_request_restore(self):
        print("Restore game requested")
        

    def __change_note(self, waveform, frequency):
        if waveform == "Sine":
            note = self.model.sine_wave(float(frequency), 3.0)
        elif waveform == "Triangle":
            note = self.model.triangle_wave(float(frequency), 3.0)
        elif waveform == "Sawtooth":
            note = self.model.sawtooth_wave(float(frequency), 3.0)
        elif waveform == "Square":
            note = self.model.square_wave(float(frequency), 3.0)
        else:
            print("Warning, waveform unknown: " + str(waveform))
            note = None
        return note
        
# ------------------------------
# Helper Functions
# ------------------------------


# ------------------------------
# App
# ------------------------------

synth = Controller()
synth.main()
     
#game.restore_control_state("floodit_control_state.txt")
