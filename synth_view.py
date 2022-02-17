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
        self.sound = None

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
                         width=300, command=self.handle_set_frequency)
        
        self.screen.rectangle(10, 10, 210, 210, color="light blue")
        
        # set up exit function
        self.app.when_closed = self.close_app
        
        # enter endless loop, waiting for user input.
        self.app.display()
        
    def reset_user_interface(self):
        print("Reset user interface")
        
        
    def play_sound(self, wave):
        if not self.sound is None:
            self.sound.fadeout(500)
            del self.sound
        # Ensure that highest value is in 16-bit range
        audio = wave * (2**15 - 1) / np.max(np.abs(wave))
        # Convert to 16-bit data
        audio = audio.astype(np.int16)
        # create a pygame Sound object and play it.
        sound = pygame.sndarray.make_sound(audio)
        sound.play()
        self.sound = sound
        
        self.plot_sound(wave)
        
    def plot_sound(self, wave):
        left_channel = np.hsplit(wave,2)[0]
        right_channel = np.hsplit(wave,2)[1]
        
        self.screen.clear()
        origin_x = 0
        origin_y = int(self.screen.height / 2)
        previous_x = origin_x
        previous_y = origin_y
        num_points = 500
        scale_x = (self.screen.width - 5)/ num_points
        scale_y = (self.screen.height - 5)/ 2.0
        for i in range(num_points):
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * left_channel[i]))
            plot_x = int(origin_x + (scale_x * i))
            self.screen.line(previous_x, previous_y, plot_x, plot_y, color="dark blue", width=1)
            previous_x = plot_x
            previous_y = plot_y
           
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
        if not self.sound is None:
            self.sound.play()
        
    def handle_request_save(self):
        self.controller.on_request_save()
        
    def handle_request_restore(self):
        self.controller.on_request_restore()
            

#--------------------------- end of View class ---------------------------

#--------------------------- Test Functions ------------------------------
if __name__ == "__main__":

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
            
            
    tc = TestController()
    tc.main()
