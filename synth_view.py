# ------------------------------
# Imports
# ------------------------------
from guizero import App, Window, Drawing, Box, Combo, Slider, Text, TextBox, PushButton

import pygame
import pygame.mixer
import pygame.sndarray
import numpy as np
import time

######################### Global constants #########################

SAMPLE_RATE = 44100

# Keyboard constants

white_semitones = [0, 2, 4, 5, 7, 9, 11]
black_semitones = [1, 3, -1000, 6, 8, 10, -1000]
NUM_OCTAVES = 3
LOWEST_TONE = 110
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
NUM_KEYS = (12 * NUM_OCTAVES) + 1

# ADSR shaper constants (times in milli-second units)

MAX_ATTACK = 100
MAX_DECAY = 100
MAX_SUSTAIN = 400
MAX_RELEASE = 100
MAX_TREMOLO_RATE = 100
MAX_TREMOLO_DEPTH = 100
MAX_VIBRATO_RATE = 100
MAX_VIBRATO_DEPTH = 100
MAX_ENVELOPE_TIME = MAX_ATTACK + MAX_DECAY + MAX_SUSTAIN + MAX_RELEASE

# ------------------------------
# Variables
# ------------------------------
# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 1
last_output_time = 0
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
        self.previous_key = 0
        self.update_display = True

    def main(self):
        self._debug_1("In view.main()")
        
        # initialise stereo mixer (default)
        pygame.mixer.init()
        pygame.init()

        self.app = App("Mini-synth", width = 940, height = 640)
        
        self.panel_0 = Box(self.app, layout="grid")
        self.settings_panel = Box(self.panel_0, layout="grid", grid=[0,0])
        self._settings_controls()
        self.scope = Drawing(self.panel_0, grid=[1,0], width=500, height=220)
        
        self.panel_1 = Box(self.app, layout="grid", border=10)
        self.panel_1.set_border(thickness=10, color=self.app.bg)
                
        self.voice_combo = Combo(self.panel_1, grid=[0,0], options=["Voice 1", "Voice 2", "Voice 3", "Voice 4"],
                                     height="fill", command=self.handle_set_voice)
                
        self.waveform_combo = Combo(self.panel_1, grid=[1,0], options=["Sine","Triangle","Sawtooth","Square"],
                                     height="fill", command=self.handle_set_waveform)

        self.play_button = PushButton(self.panel_1, grid=[2,0], text="Play", command=self.handle_request_play)

        self.sequence_button = PushButton(self.panel_1, grid=[3,0], text="Sequence", command=self.handle_request_sequence)

        self.panel_2 = Box(self.app, layout="grid", border=10)
        self.panel_2.set_border(thickness=5, color=self.app.bg)
        
        freq_label = Text(self.panel_2, grid=[0,1], text="Tone frequency, Hz: ")
        self.freq_display = Text(self.panel_2, grid=[1,1], text=str(self.controller.frequency))
        
        self.panel_3 = Box(self.app, layout="grid", border=10)
        self.panel_3.set_border(thickness=10, color=self.app.bg)
        
        self.width_label = Text(self.panel_3, grid=[0,1], text="Width, % ")
        self.width_slider = Slider(self.panel_3, grid=[1,1], start=10, end=100,
                            width=180, command=self.handle_set_width)
        self.width_slider.value = 100
        
        self.keyboard = Drawing(self.app, KEYBOARD_WIDTH, KEYBOARD_HEIGHT)
        self._draw_keyboard()
        # Link event handler functions to events. 
        self.keyboard.when_mouse_dragged = self.handle_mouse_dragged        
        self.keyboard.when_left_button_pressed = self.handle_key_pressed         
        
        # set up exit function
        self.app.when_closed = self.handle_close_app
        
        self.show_new_settings()
        
        # enter endless loop, waiting for user input via guizero widgets.
        self.app.display()
        
    def show_new_settings(self):
        self._debug_2("In show_new_setings()")
        voice_name = "Voice " + str(self.controller.voice_index + 1)
        self._update_combo(self.voice_combo, voice_name)
        waveform_name = self.controller.voices[self.controller.voice_index].waveform
        self._update_combo(self.waveform_combo, waveform_name)
        self.attack_slider.value = str(self.controller.voices[self.controller.voice_index].attack)
        self.decay_slider.value = self.controller.voices[self.controller.voice_index].decay
        self.sustain_slider.value = self.controller.voices[self.controller.voice_index].sustain_time
        self.sustain_level_slider.value = self.controller.voices[self.controller.voice_index].sustain_level
        self.release_slider.value = self.controller.voices[self.controller.voice_index].release
        waveform = self.controller.voices[self.controller.voice_index].waveform
        if waveform == "Sawtooth" or waveform == "Square":
            self.width_label.show()
            self.width_slider.show()
            self.width_slider.value = self.controller.voices[self.controller.voice_index].width
        else:
            self.width_label.hide()
            self.width_slider.hide()
        self.tremolo_rate_slider.value = self.controller.voices[self.controller.voice_index].tremolo_rate
        self.tremolo_depth_slider.value = self.controller.voices[self.controller.voice_index].tremolo_depth
        
    def _update_combo(self, combo, option):
        self._debug_2("In _update_combo()")
        if not combo.remove(option):
            self._debug_1("WARNING: Tried to remove unknown option = " + str(option))
        else:
            combo.insert(0, option)
            combo.select_default()
        
    def play_sound(self, wave):
        self._debug_2("In play_sound()")
        global last_output_time
        
        if not self.sound is None:
            self.sound.fadeout(200)
            self.sound = None
        # Ensure that highest value is in 16-bit range
        max_level = np.max(np.abs(wave))
        if max_level == 0:
            self._debug_1("ERROR: zero waveform in play_sound().")
            return -1
        
        audio = wave * (2**15 - 1) / max_level
        # Convert to 16-bit data
        audio = audio.astype(np.int16)
        # create a pygame Sound object and play it.
        sound = pygame.sndarray.make_sound(audio)
        sound.play()
        self.sound = sound
        now = time.perf_counter()
        self._debug_2("Time since last note = " + str(now-last_output_time))
        last_output_time = now
        
        if self.update_display == True:
            self._debug_2("Updating display")
            self.freq_display.value = int(self.controller.frequency)
            self._plot_sound(wave)
        
        return 0
    
    
    def show_envelope(self, envelope):
        self._debug_2("In show_envelope()")
        self.scope.clear()
        self.scope.bg = "dark gray"
            
        # Plot signal to display
        origin_x = 0
        origin_y = self.scope.height
        previous_x = origin_x
        previous_y = origin_y        
        num_points = int(self.controller.sample_rate * MAX_ENVELOPE_TIME / 1000)
        sub_sampling_factor = 9 # found by trial and error
        scope_trace = np.zeros(int(num_points), dtype = float)
        max_env = max(envelope)
        for i in range(len(envelope)):
            scope_trace[i] += envelope[i] / max_env
        #sub_sampling_factor = int(self.controller.sample_rate * 5 / self.scope.width)
        scale_x = (self.scope.width - 5) * sub_sampling_factor / num_points
        scale_y = (self.scope.height - 5) 
        self._debug_2("scale_y = " + str(scale_y))
        for i in range(num_points // sub_sampling_factor):
            #self._debug_2(envelope[int(i * sub_sampling_factor)])
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * scope_trace[int(i * sub_sampling_factor)]))
            plot_x = int(origin_x + (scale_x * i))
            self.scope.line(previous_x, previous_y, plot_x, plot_y, color="light green", width=2)
            previous_x = plot_x
            previous_y = plot_y
            
    def shutdown(self):
        self._debug_1("\nNormal termination")
        pygame.mixer.music.stop()
        self.app.destroy()        
            
    #---------------------- Helper Functions --------------------
    # (intended only for use inside this module)

    def _settings_controls(self):
        self._debug_2("In _shaper_controls()")
        Text(self.settings_panel, grid=[0,0], text="Attack time, ms: ")
        self.attack_slider = Slider(self.settings_panel, grid=[1,0], start=1, end=MAX_ATTACK,
                                    width=200, command=self.handle_set_attack)
        self.attack_slider.value = self.controller.voices[self.controller.voice_index].attack
        
        Text(self.settings_panel, grid=[0,1], text="Decay time, ms:")
        self.decay_slider = Slider(self.settings_panel, grid=[1,1], start=1, end=MAX_DECAY,
                                   width=200, command=self.handle_set_decay)
        self.decay_slider.value = self.controller.voices[self.controller.voice_index].decay
        
        Text(self.settings_panel, grid=[0,2], text="Sustain time, ms: ")
        self.sustain_slider = Slider(self.settings_panel, grid=[1,2], start=0, end=MAX_SUSTAIN,
                                     width=200, command=self.handle_set_sustain)
        self.sustain_slider.value = self.controller.voices[self.controller.voice_index].sustain_time

        Text(self.settings_panel, grid=[0,3], text="Sustain level, %: ")
        self.sustain_level_slider = Slider(self.settings_panel, grid=[1,3], start=10, end=100,
                                           width=200, command=self.handle_set_sustain_level)
        self.sustain_level_slider.value = self.controller.voices[self.controller.voice_index].sustain_level
        
        Text(self.settings_panel, grid=[0,4], text="Release time, ms: ")
        self.release_slider = Slider(self.settings_panel, grid=[1,4], start=1, end=MAX_RELEASE,
                                     width=200, command=self.handle_set_release)
        self.release_slider.value = self.controller.voices[self.controller.voice_index].release
            
        Text(self.settings_panel, grid=[0,5], text="Tremolo rate, Hz: ")
        self.tremolo_rate_slider = Slider(self.settings_panel, grid=[1,5], start=0, end=MAX_TREMOLO_RATE,
                                     width=200, command=self.handle_set_tremolo_rate)
        self.tremolo_rate_slider.value = self.controller.voices[self.controller.voice_index].tremolo_rate
        
        Text(self.settings_panel, grid=[0,6], text="Tremolo depth, %: ")
        self.tremolo_depth_slider = Slider(self.settings_panel, grid=[1,6], start=0, end=MAX_TREMOLO_DEPTH,
                                     width=200, command=self.handle_set_tremolo_depth)
        self.tremolo_depth_slider.value = self.controller.voices[self.controller.voice_index].tremolo_depth
        
        Text(self.settings_panel, grid=[0,7], text="Vibrato rate, %: ")
        self.vibrato_rate_slider = Slider(self.settings_panel, grid=[1,7], start=0, end=MAX_VIBRATO_RATE,
                                     width=200, command=self.handle_set_vibrato_rate)
        self.vibrato_rate_slider.value = self.controller.voices[self.controller.voice_index].vibrato_rate
        
        Text(self.settings_panel, grid=[0,8], text="Vibrato depth, %: ")
        self.vibrato_depth_slider = Slider(self.settings_panel, grid=[1,8], start=0, end=MAX_VIBRATO_DEPTH,
                                     width=200, command=self.handle_set_vibrato_depth)
        self.vibrato_depth_slider.value = self.controller.voices[self.controller.voice_index].vibrato_depth
            
   
    def _draw_keyboard(self, num_octaves=NUM_OCTAVES):
        self._debug_2("In _draw_keyboard()")
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
        self._debug_2("In _plot_sound()")
        left_channel = np.hsplit(wave,2)[0]
        right_channel = np.hsplit(wave,2)[1]
        self._debug_2("Waveform length in _plot_sound() = " + str(len(wave)))
        
        self.scope.clear()
        self.scope.bg = "dark gray"

        x_offset = 0
        self._debug_2("Starting plot at sample = " + str(x_offset))
        
        # Plot signal to display
        origin_x = 0
        origin_y = int(self.scope.height / 2)
        previous_x = origin_x
        previous_y = origin_y
        sub_sampling_factor = 9
        #sub_sampling_factor = int(self.controller.sample_rate * 3 / self.scope.width)
        num_points = int(len(left_channel) / sub_sampling_factor) - x_offset
        self._debug_2("Sub sampling factor = " + str(sub_sampling_factor))
        scale_x = (self.scope.width - 5)/ num_points
        max_y = max(left_channel)
        min_y = min(left_channel)
        self._debug_2("Audio waveform (min, max) = " + str(min_y) + ", " + str(max_y) + ")")
        max_y_range = max_y - min_y
        scale_y = (self.scope.height - 5)/ max_y_range
        for i in range(num_points):
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * left_channel[(i*sub_sampling_factor) + x_offset]))
            plot_x = int(origin_x + (scale_x * i))
            self.scope.line(previous_x, previous_y, plot_x, plot_y, color="light green", width=2)
            previous_x = plot_x
            previous_y = plot_y
    
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print("synth_view.py: " + message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print("synth_view.py: " + message)
    
    def _identify_key_number(self, x, y):
        self._debug_2("In _identify_key_number()")
        semitone = -1 # default value for "not a key"
        
        if y > BK_Y0 and y < BK_Y0 + BK_HEIGHT:
            
            if x > BK_X0 and (x - BK_X0) % KEY_X_SPACING < BK_WIDTH:
                octave = int((x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + BK_X0
                semitone = black_semitones[int((x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                if semitone >= 0:
                    self._debug_2("Black key pressed with number = " + str(semitone))
                      
        elif y > BK_Y0 + BK_HEIGHT and y < BK_Y0 + WK_HEIGHT:
            
            if x > WK_X0 and (x - WK_X0) % KEY_X_SPACING < WK_WIDTH:
                octave = int((x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + WK_X0
                semitone = white_semitones[int((x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                if semitone >= 0:
                    self._debug_2("White key pressed with number = " + str(semitone))
        # Do extra safety-check (shouldn't really be necessary!)
        if semitone >= NUM_KEYS:
            semitone = -1
        return semitone
        
    #-------------------- Event Handlers --------------------
    
    def handle_set_voice(self, value):
        self._debug_2("In handle_set_voice()")
        # pass on the number part of the string value
        self.controller.on_request_voice(int(value[6:]) - 1)
    
    def handle_set_waveform(self, waveform):
        self._debug_2("In handle_set_waveform()")
        if waveform == "Sawtooth" or waveform == "Square":
            self.width_label.show()
            self.width_slider.show()
        else:
            self.width_label.hide()
            self.width_slider.hide()
        self.controller.on_request_waveform(waveform)
        
    def handle_set_width(self, value):
        self._debug_2("In handle_set_width()")
        self.controller.on_request_width(value)
        
    def handle_set_attack(self, value):
        self._debug_2("In handle_set_attack()")
        self.controller.on_request_attack(int(value))

    def handle_set_decay(self, value):
        self._debug_2("In handle_set_decay()")
        self.controller.on_request_decay(int(value))
        
    def handle_set_sustain(self, value):
        self._debug_2("In handle_set_sustain()")
        self.controller.on_request_sustain(int(value))
        
    def handle_set_sustain_level(self, value):
        self._debug_2("In handle_set_sustain_level()")
        self.controller.on_request_sustain_level(value)
        
    def handle_set_release(self, value):
        self._debug_2("In handle_set_release()")
        self.controller.on_request_release(int(value))
        
    def handle_set_tremolo_rate(self, value):
        self._debug_2("In handle_set_tremolo_rate()")
        self.controller.on_request_tremolo_rate(int(value))
        
    def handle_set_tremolo_depth(self, value):
        self._debug_2("In handle_set_tremolo_depth()")
        self.controller.on_request_tremolo_depth(int(value))
        
    def handle_set_vibrato_rate(self, value):
        self._debug_2("In handle_set_vibrato_rate()")
        self.controller.on_request_vibrato_rate(int(value))
        
    def handle_set_vibrato_depth(self, value):
        self._debug_2("In handle_set_vibrato_depth()")
        self.controller.on_request_vibrato_depth(int(value))
        
    def handle_request_play(self):
        self._debug_2("In handle_request_play()")
        self.controller.on_request_play()
        
    def handle_request_sequence(self):
        self._debug_2("In handle_request_sequence()")
        self.update_display = False
        self.controller.on_request_sequence()
        self.update_display = True
               
    def handle_mouse_dragged(self, event):
        self._debug_2("Mouse (pointer) deragged event at: (" + str(event.x) + ", " + str(event.y) + ")")
        if event.x < 0 or event.x >= self.keyboard.width or event.y < 0 or event.y >= self.keyboard.height:
            self._debug_2("WARNING: Mouse out of keyboard drawing.")
            return
        semitone = self._identify_key_number(event.x, event.y)
        if semitone >= 0:
            if semitone != self.previous_key:
                self.controller.on_request_note(semitone)
        else:
            self._debug_2("Not a key")
        self.previous_key = semitone
        
    def handle_key_pressed(self, event):
        self._debug_2("Mouse left button pressed event at: (" + str(event.x) + ", " + str(event.y) + ")")
        semitone = self._identify_key_number(event.x, event.y)
        if semitone >= 0:
            self.controller.on_request_note(semitone)
        else:
            self._debug_2("Not a key")        

    def handle_close_app(self):
        self._debug_2("In handle_close_app()")
        self.controller.on_request_shutdown()

#--------------------------- end of View class ---------------------------

#--------------------------- Test Functions ------------------------------
if __name__ == "__main__":

    SAMPLE_RATE = 44100
    MAX_VOICES = 12
    DEFAULT_FREQUENCY = 440
    DEFAULT_ATTACK = 20
    DEFAULT_DECAY = 20
    DEFAULT_SUSTAIN = 100
    DEFAULT_SUSTAIN_LEVEL = 50
    DEFAULT_RELEASE = 20

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
            self.vibrato_rate = 0
            self.vibrato_depth = 0
            self.tremolo_rate = 0
            self.tremolo_depth = 0
        
    class TestController:
        def __init__(self):
            self.sample_rate = SAMPLE_RATE
            self.frequency = DEFAULT_FREQUENCY
            self.num_voices = 1
            self.voices = []
            self.voice_index = 0
            self.view = View(self)
        
        def main(self):
            self.view._debug_2("In main of test controller")
            for voice_index in range(MAX_VOICES):
                voice_params = Voice_Parameters()
                self.voices.append(voice_params)
            self.view.main()

        def on_request_voice(self, voice):
            self._debug_2("Set voice requested, index = " + str(voice))
        
        def on_request_waveform(self, waveform):
            self.view._debug_2("Set waveform requested: " + waveform)
            
        def on_request_frequency(self, frequency):
            self.view._debug_2("Set tone frequency to " + str(frequency) + " Hz")
        
        def on_request_note(self, key, voice = -1):
            self.view._debug_2("Set key to " + str(key))
            
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
            
        def on_request_tremolo_rate(self, value):
            self.view._debug_2("Set tremolo_Rate to " + str(value))
        
        def on_request_tremolo_depth(self, value):
            self.view._debug_2("Set tremolo_depth to " + str(value))
            
        def on_request_vibrato_rate(self, value):
            self.view._debug_2("Set vibrato_Rate to " + str(value))
        
        def on_request_vibrato_depth(self, value):
            self.view._debug_2("Set vibrato_depth to " + str(value))
           
        def on_request_play(self):
            self.view._debug_2("Play Sound requested")
            
        def on_request_sequence(self):
            self._debug_2("Play Sequence requested.")
        
        def on_request_shutdown(self):
            self._debug_2("Shutdown requested")

        def _debug_1(self, message):
            global debug_level
            if debug_level >= 1:
                print("synth_view.py: " + message)
            
        def _debug_2(self, message):
            global debug_level
            if debug_level >= 2:
                print("synth_view.py: " + message)
            
            
    debug_level = 2       
    tc = TestController()
    tc.main()
