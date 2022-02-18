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
        self.width = 100
        self.view = View(self)
        self.model = Model(SAMPLE_RATE)
    
    def main(self):
        print("In main of test controller")
        
        self.view.main()

    def on_request_waveform(self, waveform):
        print("Set waveform requested: " + waveform)
        self.waveform = waveform
        note = self.__change_note(self.waveform, self.frequency, self.width)    
        if not note is None:
            self.view.play_sound(note)        
        
    def on_request_frequency(self, frequency):
        print("Set frequency to " + str(frequency))
        self.frequency = float(frequency)
        note = self.__change_note(self.waveform, self.frequency, self.width)    
        if not note is None:
            self.view.play_sound(note)
            
    def on_request_width(self, width):
        if self.waveform == "Sawtooth" or self.waveform == "Square":
            print("Set width to " + str(width))
            self.width = float(width)
            note = self.__change_note(self.waveform, self.frequency, self.width)    
            if not note is None:
                self.view.play_sound(note)
        else:
            print("Width of this waveform is fixed.")
        
    def on_request_play(self):
        print("Play Sound requested")
              
    def on_request_save(self):
        print("Save game requested")
        
    def on_request_restore(self):
        print("Restore game requested")
        

    def __change_note(self, waveform, frequency, width):
        if waveform == "Sine":
            note = self.model.sine_wave(float(frequency), 3.0)
        elif waveform == "Triangle":
            note = self.model.triangle_wave(float(frequency), 3.0)
        elif waveform == "Sawtooth":
            note = self.model.pwm_sawtooth_wave(float(frequency), width, 3.0)
        elif waveform == "Square":
            note = self.model.pwm_square_wave(float(frequency), width, 3.0)
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
