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

white_semitones = [0, 2, 4, 5, 7, 9, 11]
black_semitones = [1, 3, -1000, 6, 8, 10, -1000]
NUM_OCTAVES = 3
KEY_X_SPACING = 40
WK_X0 = 25
WK_Y0 = 25
BK_X0 = 45
BK_Y0 = 25
WK_HEIGHT = 60
WK_WIDTH = 30
BK_HEIGHT = 30
BK_WIDTH = 30
KEYBOARD_WIDTH = (7 * NUM_OCTAVES  * KEY_X_SPACING) + WK_WIDTH + (2 * WK_X0)
KEYBOARD_HEIGHT = WK_HEIGHT + (2 *  WK_Y0)
NUM_WHITE_KEYS = (NUM_OCTAVES * 7) + 1
NUM_BLACK_KEYS = (NUM_OCTAVES * 7) - 1

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

        self.app = App("Mini-synth", width = 940)
        
        self.box = Box(self.app)
        self.screen = Drawing(self.box, width=220, height=220)
        
        self.panel_1 = Box(self.app, layout="grid", border=10)
        self.panel_1.set_border(thickness=10, color=self.app.bg)
        self.waveform_button = Combo(self.panel_1, grid=[0,0], options=["Sine","Triangle","Sawtooth","Square"],
                                     height="fill", command=self.handle_set_waveform)

        self.play_button = PushButton(self.panel_1, grid=[1,0], text="Play", command=self.handle_request_play)
        
        self.panel_2 = Box(self.app, layout="grid", border=10)
        self.panel_2.set_border(thickness=5, color=self.app.bg)
        
        freq_label = Text(self.panel_2, grid=[0,1], text="Frequency, Hz: ")
        self.freq_display = Text(self.panel_2, grid=[1,1], text=str(self.controller.frequency))
        
        self.panel_3 = Box(self.app, layout="grid", border=10)
        self.panel_3.set_border(thickness=10, color=self.app.bg)
        
        width_label = Text(self.panel_3, grid=[0,1], text="Width, % ")
        self.width_button = Slider(self.panel_3, grid=[1,1], start=10, end=100,
                         width=180, command=self.handle_set_width)
        self.width_button.value = 100
        
        self.keyboard = Drawing(self.app, KEYBOARD_WIDTH, KEYBOARD_HEIGHT)
        self.draw_keyboard()
        # Link event handler functions to events. 
        self.keyboard.when_mouse_dragged = self.detect_key        
        self.keyboard.when_left_button_pressed = self.detect_key         
        
        # set up exit function
        self.app.when_closed = self.close_app
        
        # enter endless loop, waiting for user input.
        self.app.display()
        
    def reset_user_interface(self):
        print("Reset user interface")
        
        
    def draw_keyboard(self, num_octaves=NUM_OCTAVES):
            self.keyboard.rectangle(0, 0, KEYBOARD_WIDTH, KEYBOARD_HEIGHT, color = "green")

            for i in range(NUM_WHITE_KEYS):
                key_left = WK_X0 + KEY_X_SPACING * i
                key_top = WK_Y0
                self.keyboard.rectangle(key_left, key_top, key_left + WK_WIDTH, key_top + WK_HEIGHT, color = "white")

            for i in range(NUM_BLACK_KEYS):
                if (i % 7) in [0, 1, 3, 4, 5]:
                    key_left = BK_X0 + KEY_X_SPACING * i
                    key_top = BK_Y0
                    self.keyboard.rectangle(key_left, key_top, key_left + BK_WIDTH, key_top + BK_HEIGHT, color = "black")
        
        
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
        
        self.freq_display.value = int(self.controller.frequency)
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
        
    def handle_set_width(self, value):
        self.controller.on_request_width(value)
        
    def handle_request_play(self):
        self.controller.on_request_play()
        if not self.sound is None:
            self.sound.play()
        
    def handle_request_save(self):
        self.controller.on_request_save()
        
    def handle_request_restore(self):
        self.controller.on_request_restore()
            
    def detect_key(self, event):
        #print("Mouse left button pressed event at: (" + str(event.x) + ", " + str(event.y) + ")")
        
        semitone = -1 # default value for "not a key"
        
        if event.y > BK_Y0 and event.y < BK_Y0 + BK_HEIGHT:
            
            if event.x > BK_X0 and (event.x - BK_X0) % KEY_X_SPACING < BK_WIDTH:
                octave = int((event.x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + BK_X0
                semitone = black_semitones[int((event.x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                #if semitone >= 0:
                #    print("Black key pressed with number = " + str(semitone))
                      
        elif event.y > BK_Y0 + BK_HEIGHT and event.y < BK_Y0 + WK_HEIGHT:
            
            if event.x > WK_X0 and (event.x - WK_X0) % KEY_X_SPACING < WK_WIDTH:
                octave = int((event.x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + WK_X0
                semitone = white_semitones[int((event.x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                #if semitone >= 0:
                #    print("White key pressed with number = " + str(semitone))
        
        if semitone >= 0:
            frequency = int((110 * np.power(2, semitone/12)) + 0.5)
            self.controller.on_request_frequency(frequency)
        else:
            print("Not a key")        

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
            
        def on_request_width(self, width):
            print("Set width % to " + str(width))
            
        def on_request_play(self):
            print("Play Sound requested")
                  
        def on_request_save(self):
            print("Save game requested")
            
        def on_request_restore(self):
            print("Restore game requested")
            
            
    tc = TestController()
    tc.main()
