# ------------------------------
# Imports
# ------------------------------
from synth_view import View

# ------------------------------
# Test Variables
# ------------------------------
#TEST_BOARD_SIZE = 16
#import numpy as np
#import random
#from access_game_settings import read_game_settings, write_game_settings
# ------------------------------
# Test Class
# ------------------------------

class TestController:
    def __init__(self):
        self.waveform = "Sine"
        self.frequency = 440
        self.view = View(self)
    
    def main(self):
        print("In main of test controller")
        
        self.view.main()

    def on_request_waveform(self, waveform):
        print("Set waveform requested: " + waveform)
        
    def on_request_frequency(self, frequency):
        print("Set frequency to " + str(frequency))
        
    def on_request_play(self):
        print("Play Sound requested")
              
    def on_request_save(self):
        print("Save game requested")
        
    def on_request_restore(self):
        print("Restore game requested")
        


        
def test_view():
    tc = TestController()
    tc.main()