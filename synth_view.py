# ------------------------------
# Imports
# ------------------------------
from guizero import App, Window, Drawing, Box, Combo, Slider, Text, TextBox, PushButton

import pygame
import pygame.mixer
import pygame.sndarray
import numpy as np

# ------------------------------
# Variables
# ------------------------------
######################### Global constants #########################

SAMPLE_RATE = 44100

# ------------------------------
#  Notes:
#  
#  1. None of the View method functions return any values.
#  2. The View methods can read and write View variables.
#  3. The View methods can read but not write Controller variables.
#  4. View data is transferred to the Controller using Controller request methods.
#  5. The View class only communicates with the Controller, not the Model.
#  6. All the commands called by GUI widgets are event handler methods in the View class.
#     This enables the appropriate data to be sent to the controller, independent of any
#     Widget peculiarities or limitations.
# ------------------------------
class View:
    def __init__(self, controller):
        self.controller = controller
        self.old_sound = None

    def main(self):
        self._debug_1("In view.main()")
        
        # initialise stereo mixer (default)
        pygame.mixer.init()
        pygame.init()

        self.app = App("Mini-synth")
        
        self.box = Box(self.app)
        self.screen = Drawing(self.box, width=220, height=220)
        
        self.panel = Box(self.app, layout="grid", border=10)
        self.panel.set_border(thickness=10, color=self.app.bg)
        self.waveform_button = Combo(self.panel, grid=[0,0], options=["Sine","Triangle","Sawtooth","Square"],
                                     height="fill", command=self.handle_set_waveform)

        #mywidth = Slider(app, start=1, end=10)

        self.play_button = PushButton(self.panel, grid=[2,0], text="Play", command=self.handle_request_play)
        #self.play_button.text_color = "grey"
        
        self.frequency_button = Slider(self.app, start=200, end=500,
                         width=200, command=self.handle_set_frequency)
        
        self.screen.rectangle(10, 10, 210, 210, color="light blue")
        self.screen.oval(30, 30, 50, 50, color="white", outline=True)

        # set up exit function
        self.app.when_closed = self.close_app
        
        # enter endless loop, waiting for user input.
        self.app.display()
        
    def reset_user_interface(self):
        print("Reset user interface")
        
        
    def play_sound(self, wave):
        if not self.old_sound is None:
            self.old_sound.stop()
        # Ensure that highest value is in 16-bit range
        audio = wave * (2**15 - 1) / np.max(np.abs(wave))
        # Convert to 16-bit data
        audio = audio.astype(np.int16)
        # create a pygame Sound object and play it.
        sound = pygame.sndarray.make_sound(audio)
        sound.play()
        self.old_sound = sound
           
           
    def close_app(self):
        print("\nNormal termination")
        pygame.mixer.music.stop()
        self.app.destroy()
    
    #################### Helper Functions ################
        
    def _debug_1(self, message):
        # pass
        print(message)
        
    def _debug_2(self, message):
        # pass
        print(message)
    
    #################### Event Handlers ##################
    
    def handle_set_waveform(self, value):
        self.controller.on_request_waveform(value)
    
    def handle_set_frequency(self, value):
        self.controller.on_request_frequency(value)
        
    def handle_request_play(self):
        self.controller.on_request_play()
        
    def handle_request_save(self):
        self.controller.on_request_save()
        
    def handle_request_restore(self):
        self.controller.on_request_restore()
            

#--------------------------- end of View class ---------------------------

