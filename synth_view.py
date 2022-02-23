# ------------------------------
# Imports
# ------------------------------
from guizero import App, Window, Drawing, Box, Combo, Slider, Text, TextBox, PushButton

import pygame
import pygame.mixer
import pygame.sndarray
import numpy as np

######################### Global constants #########################

SAMPLE_RATE = 44100

# Keyboard constants

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

# ADSR shaper constants (times in milli-second units)

MAX_ATTACK = 100
MAX_DECAY = 100
MAX_SUSTAIN = 400
MAX_RELEASE = 100
MAX_ENVELOPE_TIME = MAX_ATTACK + MAX_DECAY + MAX_SUSTAIN + MAX_RELEASE

# ------------------------------
# Variables
# ------------------------------
debug_level = 0
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
        
        self.panel_0 = Box(self.app, layout="grid")
        self.shaper_panel = Box(self.panel_0, layout="grid", grid=[0,0])
        self._shaper_controls()
        self.screen = Drawing(self.panel_0, grid=[1,0], width=500, height=220)
        
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
        self._draw_keyboard()
        # Link event handler functions to events. 
        self.keyboard.when_mouse_dragged = self.handle_kb_sweep        
        self.keyboard.when_left_button_pressed = self.handle_key_pressed         
        
        # set up exit function
        self.app.when_closed = self.handle_close_app
        
        # enter endless loop, waiting for user input.
        self.app.display()
        
        
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
        self._plot_sound(wave)
    
    
    def show_envelope(self, envelope):
        self._debug_2("New envelope available")
        self.screen.clear()
        self.screen.bg = "dark gray"
            
        # Plot signal to display
        origin_x = 0
        origin_y = self.screen.height
        previous_x = origin_x
        previous_y = origin_y        
        num_points = int(self.controller.sample_rate * MAX_ENVELOPE_TIME / 1000)
        sub_sampling_factor = int(self.controller.sample_rate * 5 / self.screen.width)
        scale_x = (self.screen.width - 5) * sub_sampling_factor / num_points
        scale_y = (self.screen.height - 5)
        self._debug_2("scale_y = " + str(scale_y))
        for i in range(num_points // sub_sampling_factor):
            #self._debug_2(envelope[int(i * sub_sampling_factor)])
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * envelope[int(i * sub_sampling_factor)]))
            plot_x = int(origin_x + (scale_x * i))
            self.screen.line(previous_x, previous_y, plot_x, plot_y, color="light green", width=2)
            previous_x = plot_x
            previous_y = plot_y
            
    #---------------------- Helper Functions --------------------
    # (intended only for use inside this module)

    def _shaper_controls(self):
            Text(self.shaper_panel, grid=[0,0], text="Attack time, ms: ")
            self.attack = Slider(self.shaper_panel, grid=[1,0], start=MAX_ATTACK//10, end=MAX_ATTACK,
                         width=180, command=self.handle_set_attack)
            self.attack.value = MAX_ATTACK // 2 # Initial value
            
            Text(self.shaper_panel, grid=[0,1], text="Decay time, ms:")
            self.decay = Slider(self.shaper_panel, grid=[1,1], start=MAX_DECAY//10, end=MAX_DECAY,
                         width=180, command=self.handle_set_decay)
            self.decay.value = MAX_DECAY // 2 # Initial value
            
            Text(self.shaper_panel, grid=[0,2], text="Sustain time, ms: ")
            self.sustain = Slider(self.shaper_panel, grid=[1,2], start=0, end=MAX_SUSTAIN,
                         width=180, command=self.handle_set_sustain)
            self.sustain.value = MAX_SUSTAIN // 2 # Initial value
            
            Text(self.shaper_panel, grid=[0,3], text="Sustain level, %: ")
            self.sustain_level = Slider(self.shaper_panel, grid=[1,3], start=10, end=100,
                         width=180, command=self.handle_set_sustain_level)
            self.sustain_level.value = 50 # Initial value
            
            Text(self.shaper_panel, grid=[0,4], text="Release time, ms: ")
            self.release = Slider(self.shaper_panel, grid=[1,4], start=MAX_RELEASE//10, end=MAX_RELEASE,
                         width=180, command=self.handle_set_release)
            self.release.value = MAX_RELEASE // 2 # Initial value
            
    
    def _draw_keyboard(self, num_octaves=NUM_OCTAVES):
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
                
                    
    def _plot_sound(self, wave):
        left_channel = np.hsplit(wave,2)[0]
        right_channel = np.hsplit(wave,2)[1]
        
        self.screen.clear()
        self.screen.bg = "dark gray"

        # Find the part of the waveform with the strongest signal
        samples_per_cycle = int(self.controller.sample_rate / self.controller.frequency)
        possible_offset = int(self.controller.sample_rate * self.controller.attack / 1000) - samples_per_cycle
        x_offset = 0
        max_level = 0.0
        min_level = 1.0
        for i in range(possible_offset, min(len(left_channel)-1, possible_offset + int(2 * samples_per_cycle))):
            current_level = left_channel[i] 
            if current_level > max_level:
                max_level = current_level
                x_offset = possible_offset
            elif current_level < 0:
                min_level = 1.0 # reset the minimum level
            if abs(current_level) < min_level:
                min_level = abs(current_level)
                possible_offset = i
        # self._debug_2("Starting plot at sample = " + str(x_offset))
        
        # Plot signal to display
        origin_x = 0
        origin_y = int(self.screen.height / 2)
        previous_x = origin_x
        previous_y = origin_y        
        num_points = min(500, len(left_channel))
        #num_points = len(left_channel)
        scale_x = (self.screen.width - 5)/ num_points
        scale_y = (self.screen.height - 5)/ 2.0
        for i in range(num_points):
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * left_channel[i + x_offset]))
            plot_x = int(origin_x + (scale_x * i))
            self.screen.line(previous_x, previous_y, plot_x, plot_y, color="light green", width=2)
            previous_x = plot_x
            previous_y = plot_y
    
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print(message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print(message)
    
    #-------------------- Event Handlers --------------------
    
    def handle_set_waveform(self, value):
        self.controller.on_request_waveform(value)
    
    def handle_set_frequency(self, value):
        self.controller.on_request_frequency(value)
        
    def handle_set_width(self, value):
        self.controller.on_request_width(value)
        
    def handle_set_attack(self, value):
        self.controller.on_request_attack(int(value))

    def handle_set_decay(self, value):
        self.controller.on_request_decay(int(value))
        
    def handle_set_sustain(self, value):
        self.controller.on_request_sustain(int(value))
        
    def handle_set_sustain_level(self, value):
        self.controller.on_request_sustain_level(value)
        
    def handle_set_release(self, value):
        self.controller.on_request_release(int(value))
        
    def handle_request_play(self):
        self.controller.on_request_play()
        if not self.sound is None:
            self.sound.play()
        
    def handle_request_save(self):
        self.controller.on_request_save()
        
    def handle_request_restore(self):
        self.controller.on_request_restore()
            
    def handle_kb_sweep(self, event):
        self.handle_key_pressed(event) # Temporary workaround until ADSR is implemented.
        
    def handle_key_pressed(self, event):
        #self.debug2("Mouse left button pressed event at: (" + str(event.x) + ", " + str(event.y) + ")")
        
        semitone = -1 # default value for "not a key"
        
        if event.y > BK_Y0 and event.y < BK_Y0 + BK_HEIGHT:
            
            if event.x > BK_X0 and (event.x - BK_X0) % KEY_X_SPACING < BK_WIDTH:
                octave = int((event.x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + BK_X0
                semitone = black_semitones[int((event.x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                #if semitone >= 0:
                #    self._debug_2("Black key pressed with number = " + str(semitone))
                      
        elif event.y > BK_Y0 + BK_HEIGHT and event.y < BK_Y0 + WK_HEIGHT:
            
            if event.x > WK_X0 and (event.x - WK_X0) % KEY_X_SPACING < WK_WIDTH:
                octave = int((event.x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + WK_X0
                semitone = white_semitones[int((event.x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                #if semitone >= 0:
                #    self._debug_2("White key pressed with number = " + str(semitone))
        
        if semitone >= 0:
            frequency = int((110 * np.power(2, semitone/12)) + 0.5)
            self.controller.on_request_frequency(frequency)
        else:
            self._debug_2("Not a key")        

    def handle_close_app(self):
        self._debug_2("\nNormal termination")
        pygame.mixer.music.stop()
        self.app.destroy()
#--------------------------- end of View class ---------------------------

#--------------------------- Test Functions ------------------------------
if __name__ == "__main__":

    class TestController:
        def __init__(self):
            self.waveform = "Sine"
            self.frequency = 440
            self.view = View(self)
        
        def main(self):
            self.view._debug_2("In main of test controller")
            self.view.main()

        def on_request_waveform(self, waveform):
            self.view._debug_2("Set waveform requested: " + waveform)
            
        def on_request_frequency(self, frequency):
            self.view._debug_2("Set frequency to " + str(frequency))
            
        def on_request_width(self, width):
            self.view._debug_2("Set width % to " + str(width))
        
        def on_request_attack(self, value):
            self.view._debug_2("Set attack to " + str(value))
                
        def on_request_decay(self, value):
            self.view._debug_2("Set decay to " + str(value))
            
        def on_request_sustain(self, value):
            self.view._debug_2("Set sustain to " + str(value))
            
        def on_request_sustain_level(self, value):
            self.view._debug_2("Set sustain level to " + str(value))
            
        def on_request_release(self, value):
            self.view._debug_2("Set release to " + str(value))
                
        def on_request_play(self):
            self.view._debug_2("Play Sound requested")
                  
        def on_request_save(self):
            self.view._debug_2("Save settings requested")
            
        def on_request_restore(self):
            self.view._debug_2("Restore settings requested")
            
    debug_level = 2       
    tc = TestController()
    tc.main()
