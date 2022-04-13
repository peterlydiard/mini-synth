#--------------------------------- Voice editor -------------------------                
# ------------------------------
# Imports
# ------------------------------
import guizero
import numpy as np
import synth_constants as const

# ------------------------------
# Module globals
# ------------------------------
# Keyboard constants

white_keys = [0, 2, 4, 5, 7, 9, 11]
black_keys = [1, 3, -1000, 6, 8, 10, -1000]
NUM_WHITE_KEYS = int((7 * const.NUM_OCTAVES) + 1)
KEY_X_SPACING = int(min(40, (1200 / NUM_WHITE_KEYS)))
WK_X0 = 25
WK_Y0 = 25
BK_X0 = int(25 + KEY_X_SPACING/2)
BK_Y0 = 25
WK_HEIGHT = 60
WK_WIDTH = int(0.75 * KEY_X_SPACING)
BK_HEIGHT = 30
BK_WIDTH = int(0.75 * KEY_X_SPACING)
KEYBOARD_WIDTH = (7 * const.NUM_OCTAVES  * KEY_X_SPACING) + WK_WIDTH + (2 * WK_X0)
KEYBOARD_HEIGHT = WK_HEIGHT + (2 *  WK_Y0)
NUM_WHITE_KEYS = (const.NUM_OCTAVES * 7) + 1
NUM_BLACK_KEYS = (const.NUM_OCTAVES * 7) - 1
NUM_KEYS = (12 * const.NUM_OCTAVES) + 1

# Widget sizes

VOICE_EDITOR_WIDTH = KEYBOARD_WIDTH + 50
SCOPE_HEIGHT = 280
SCOPE_WIDTH = VOICE_EDITOR_WIDTH - 440
NUM_TONE_SLIDERS = 3 + (2 * const.UNISON_ENABLED) + const.HARMONIC_BOOST_ENABLED + const.RING_MODULATION_ENABLED
NUM_ENVELOPE_SLIDERS = 5 + (2 * const.TREMOLO_ENABLED)
VOICE_EDITOR_HEIGHT = 200 + max(50 + (NUM_TONE_SLIDERS * 40), SCOPE_HEIGHT) + max(NUM_ENVELOPE_SLIDERS * 40, SCOPE_HEIGHT)

debug_level = 2

# ------------------------------
# Module class
# ------------------------------

class Voice_Editor:
    def __init__(self, view):
        self.view = view
        self.previous_key = 0
        self.displayed_frequency = const.LOWEST_TONE
       

    def main(self):
        self._debug_1("In main()")
        self._voice_editor_window()
        self.show_new_settings()
        
        
    def _voice_editor_window(self):
        self.window = guizero.Window(self.view.app, "Voice editor", width = VOICE_EDITOR_WIDTH, height = VOICE_EDITOR_HEIGHT)
        self.window.when_closed = self._closed_voice_editor
        self.voice_window_open = True
        
        self.panel_0 = guizero.Box(self.window, layout="grid")
        
        self.tone_settings_panel = guizero.Box(self.panel_0, layout="grid", grid=[0,0])
        self._tone_settings_controls()
        
        self.envelope_settings_panel = guizero.Box(self.panel_0, layout="grid", grid=[0,1])
        self._envelope_settings_controls()
        
        self.audio_scope = guizero.Drawing(self.panel_0, grid=[1,0], width=SCOPE_WIDTH, height=SCOPE_HEIGHT)
        self.control_scope = guizero.Drawing(self.panel_0, grid=[1,1], width=SCOPE_WIDTH, height=SCOPE_HEIGHT)
        
        self.panel_1 = guizero.Box(self.window, layout="grid", border=10)
        self.panel_1.set_border(thickness=10, color=self.view.app.bg)
        freq_label = guizero.Text(self.panel_1, grid=[0,0], text="Tone frequency, Hz: ")
        self.freq_display = guizero.Text(self.panel_1, grid=[1,0], text=str(self.displayed_frequency))
        guizero.Text(self.panel_1, grid=[2,0], text="  ")
        duration_label = guizero.Text(self.panel_1, grid=[3,0], text="Note length, ms: ")
        self.duration_display = guizero.Text(self.panel_1, grid=[4,0], text="0")
        guizero.Text(self.panel_1, grid=[5,0], text="  ")      
        self.play_button = guizero.PushButton(self.panel_1, grid=[6,0], text="Play note", command=self._handle_request_play)
        self.sequence_button = guizero.PushButton(self.panel_1, grid=[7,0], text="100 notes", command=self._handle_request_test)
               
        self.keyboard = guizero.Drawing(self.window, KEYBOARD_WIDTH, KEYBOARD_HEIGHT)
        self._draw_keyboard()
        # Link event handler functions to events. 
        self.keyboard.when_mouse_dragged = self._handle_mouse_dragged        
        self.keyboard.when_left_button_pressed = self._handle_key_pressed         
        
        self.show_new_settings()
        
        
    def _tone_settings_controls(self):
        self._debug_2("In _tone_settings_controls()")
        self.voice_controls_panel = guizero.Box(self.tone_settings_panel, layout="grid", grid=[0,0])
        self.new_voice_button = guizero.PushButton(self.voice_controls_panel, grid=[0,0], text="New Voice", command=self._handle_new_voice)
        voice_name_list = []
        for i in range(self.view.controller.num_voices):
            voice_name = "Voice " + str(i+1)
            voice_name_list.append(voice_name)
        self.voice_combo = guizero.Combo(self.voice_controls_panel, grid=[1,0], options=voice_name_list,
                                     height="fill", command=self._handle_select_voice)                
        self.waveform_combo = guizero.Combo(self.voice_controls_panel, grid=[2,0], options=["Sine","Triangle","Sawtooth","Square"],
                                     height="fill", command=self._handle_set_waveform)
        
        self.voice_sliders_panel = guizero.Box(self.tone_settings_panel, layout="grid", grid=[0,1])
        self.width_label = guizero.Text(self.voice_sliders_panel, grid=[0,1], text="Width, % ")
        self.width_slider = guizero.Slider(self.voice_sliders_panel, grid=[1,1], start=10, end=100,
                            width=200, command=self._handle_set_width)
        self.width_slider.value = 100

        self.harmonic_boost_label = guizero.Text(self.voice_sliders_panel, grid=[0,2], text="Harmonic boost, %: ")
        self.harmonic_boost_slider = guizero.Slider(self.voice_sliders_panel, grid=[1,2], start=0, end=const.MAX_HARMONIC_BOOST,
                                     width=200, command=self._handle_set_harmonic_boost)
        self.harmonic_boost_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].harmonic_boost
        
        self.vibrato_rate_label = guizero.Text(self.voice_sliders_panel, grid=[0,3], text="Vibrato rate, %: ")
        self.vibrato_rate_slider = guizero.Slider(self.voice_sliders_panel, grid=[1,3], start=0, end=const.MAX_VIBRATO_RATE,
                                     width=200, command=self._handle_set_vibrato_rate)
        self.vibrato_rate_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].vibrato_rate
        
        self.vibrato_depth_label = guizero.Text(self.voice_sliders_panel, grid=[0,4], text="Vibrato depth, %: ")
        self.vibrato_depth_slider = guizero.Slider(self.voice_sliders_panel, grid=[1,4], start=0, end=const.MAX_VIBRATO_DEPTH,
                                     width=200, command=self._handle_set_vibrato_depth)
        self.vibrato_depth_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].vibrato_depth
        
        self.unison_voices_label = guizero.Text(self.voice_sliders_panel, grid=[0,5], text="Unison voices: ")
        self.unison_voices_slider = guizero.Slider(self.voice_sliders_panel, grid=[1,5], start=1, end=const.MAX_UNISON_VOICES,
                                     width=200, command=self._handle_set_unison_voices)
        self.unison_voices_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].unison_voices
        
        self.unison_detune_label = guizero.Text(self.voice_sliders_panel, grid=[0,6], text="Unison detune, %: ")
        self.unison_detune_slider = guizero.Slider(self.voice_sliders_panel, grid=[1,6], start=0, end=const.MAX_UNISON_DETUNE,
                                     width=200, command=self._handle_set_unison_detune)
        self.unison_detune_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].unison_detune
        
        self.ring_mod_label = guizero.Text(self.voice_sliders_panel, grid=[0,7], text="Ring modulation rate, %: ")
        self.ring_mod_rate_slider = guizero.Slider(self.voice_sliders_panel, grid=[1,7], start=0, end=const.MAX_RING_MOD_RATE,
                                     width=200, command=self._handle_set_ring_mod_rate)
        self.ring_mod_rate_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].ring_mod_rate
        
        if not const.HARMONIC_BOOST_ENABLED:
            self.harmonic_boost_label.hide()
            self.harmonic_boost_slider.hide()
        if not const.VIBRATO_ENABLED:
            self.vibrato_rate_label.hide()
            self.vibrato_rate_slider.hide()
            self.vibrato_depth_label.hide()
            self.vibrato_depth_slider.hide()
        if not const.RING_MODULATION_ENABLED:
            self.ring_mod_label.hide()
            self.ring_mod_rate_slider.hide()
        if not const.UNISON_ENABLED:
            self.unison_voices_label.hide()
            self.unison_voices_slider.hide()
            self.unison_detune_label.hide()
            self.unison_detune_slider.hide()
            

    def _envelope_settings_controls(self):
        self._debug_2("In _envelope_settings_controls()")
        
        guizero.Text(self.envelope_settings_panel, grid=[0,0], text="Attack time, ms: ")
        self.attack_slider = guizero.Slider(self.envelope_settings_panel, grid=[1,0], start=1, end=const.MAX_ATTACK,
                                    width=200, command=self._handle_set_attack)
        self.attack_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].attack
        
        guizero.Text(self.envelope_settings_panel, grid=[0,1], text="Decay time, ms:")
        self.decay_slider = guizero.Slider(self.envelope_settings_panel, grid=[1,1], start=1, end=const.MAX_DECAY,
                                   width=200, command=self._handle_set_decay)
        self.decay_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].decay
        
        guizero.Text(self.envelope_settings_panel, grid=[0,2], text="Sustain time, ms: ")
        self.sustain_slider = guizero.Slider(self.envelope_settings_panel, grid=[1,2], start=0, end=const.MAX_SUSTAIN,
                                     width=200, command=self._handle_set_sustain)
        self.sustain_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].sustain_time

        guizero.Text(self.envelope_settings_panel, grid=[0,3], text="Sustain level, %: ")
        self.sustain_level_slider = guizero.Slider(self.envelope_settings_panel, grid=[1,3], start=10, end=100,
                                           width=200, command=self._handle_set_sustain_level)
        self.sustain_level_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].sustain_level
        
        guizero.Text(self.envelope_settings_panel, grid=[0,4], text="Release time, ms: ")
        self.release_slider = guizero.Slider(self.envelope_settings_panel, grid=[1,4], start=1, end=const.MAX_RELEASE,
                                     width=200, command=self._handle_set_release)
        self.release_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].release
            
        self.tremolo_rate_label = guizero.Text(self.envelope_settings_panel, grid=[0,5], text="Tremolo rate, Hz: ")
        self.tremolo_rate_slider = guizero.Slider(self.envelope_settings_panel, grid=[1,5], start=0, end=const.MAX_TREMOLO_RATE,
                                     width=200, command=self._handle_set_tremolo_rate)
        self.tremolo_rate_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].tremolo_rate
        
        self.tremolo_depth_label = guizero.Text(self.envelope_settings_panel, grid=[0,6], text="Tremolo depth, %: ")
        self.tremolo_depth_slider = guizero.Slider(self.envelope_settings_panel, grid=[1,6], start=0, end=const.MAX_TREMOLO_DEPTH,
                                     width=200, command=self._handle_set_tremolo_depth)
        self.tremolo_depth_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].tremolo_depth
        
        if not const.TREMOLO_ENABLED:
            self.tremolo_rate_label.hide()
            self.tremolo_rate_slider.hide()    
            self.tremolo_depth_label.hide()
            self.tremolo_depth_slider.hide()           
   
    def _draw_keyboard(self, num_octaves=const.NUM_OCTAVES):
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


    def show_new_settings(self):
        self._debug_2("In show_new_setings()")
        voice_name_list = []
        for i in range(self.view.controller.num_voices):
            voice_name = "Voice " + str(i+1)
            voice_name_list.append(voice_name)
        self.voice_combo.destroy()
        self.voice_combo = guizero.Combo(self.voice_controls_panel, grid=[1,0], options=voice_name_list,
                                     height="fill", command=self._handle_select_voice)
        voice_name = "Voice " + str(self.view.controller.voice_index + 1)
        self.view.update_combo(self.voice_combo, voice_name)
        waveform = self.view.controller.voice_params[self.view.controller.voice_index].waveform
        self.view.update_combo(self.waveform_combo, waveform)
        self.attack_slider.value = str(self.view.controller.voice_params[self.view.controller.voice_index].attack)
        self.decay_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].decay
        self.sustain_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].sustain_time
        self.sustain_level_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].sustain_level
        self.release_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].release
        self.vibrato_rate_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].vibrato_rate
        self.vibrato_depth_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].vibrato_depth
        self.ring_mod_rate_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].ring_mod_rate
        self.tremolo_rate_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].tremolo_rate
        self.tremolo_depth_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].tremolo_depth
        if waveform == "Sawtooth" or waveform == "Square":
            self.width_label.show()
            self.width_slider.show()
            self.width_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].width
            if const.UNISON_ENABLED:
                self.unison_voices_label.show()
                self.unison_voices_slider.show()
                self.unison_voices_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].unison_voices
                self.unison_detune_label.show()
                self.unison_detune_slider.show()
                self.unison_detune_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].unison_detune
        else:
            self.width_label.hide()
            self.width_slider.hide()
            self.unison_voices_label.hide()
            self.unison_voices_slider.hide()
            self.unison_detune_label.hide()
            self.unison_detune_slider.hide()
        if not waveform == "Sine" and const.HARMONIC_BOOST_ENABLED:
            self.harmonic_boost_label.show()
            self.harmonic_boost_slider.show()
            self.harmonic_boost_slider.value = self.view.controller.voice_params[self.view.controller.voice_index].harmonic_boost
        else:
            self.harmonic_boost_label.hide()
            self.harmonic_boost_slider.hide()

    def show_frequency(self, frequency):
        self._debug_2("In show_frequency()")
        self.displayed_frequency = int(frequency)
        self.freq_display.value = self.displayed_frequency

    def plot_envelope(self, envelope):
        self._debug_2("In plot_envelope()")
        self.control_scope.clear()
        self.control_scope.bg = "dark gray"            
        # Set graph origin to the bottom, left corner of the drawing area. Envelope always >= 0.
        origin_x = 0
        origin_y = self.control_scope.height
        # Set initial values of the start of the lines being drawn.
        previous_x = origin_x
        previous_y = origin_y
        # Set the number of points to plot. 
        num_points = const.SAMPLE_RATE * 0.020 # 20 miliseconds worth of input samples.
        # Increase no. of points to plot in steps of 50ms worth of samples.
        while num_points < len(envelope):
            if num_points < const.SAMPLE_RATE * 0.1:
                num_points += const.SAMPLE_RATE * 0.020 # add 20 msec to timescale
            else:
                num_points += const.SAMPLE_RATE * 0.050 # add 50 msec to timescale
        # Scale down the x axis
        sub_sampling_factor = 9 # found by trial and error
        num_points = int(num_points // sub_sampling_factor) + sub_sampling_factor
        self._debug_2("Envelope length, graph length = " + str(len(envelope)) + ", " + str(num_points))
        scope_trace = np.zeros(int(num_points), dtype = float)
        max_env = max(envelope)
        env_points = int(len(envelope) / sub_sampling_factor)
        # Select and normalise the envelope points to be plotted
        for i in range(env_points):
            scope_trace[i] += envelope[int(i * sub_sampling_factor)] / max_env
        # Calculate scale factors to fit plot inside drawing widget.
        scale_x = (self.control_scope.width - 5) / num_points
        scale_y = (self.control_scope.height - 5) 
        self._debug_2("scale_y = " + str(scale_y))
        for i in range(num_points):
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * scope_trace[i]))
            plot_x = int(origin_x + (scale_x * i))
            self.control_scope.line(previous_x, previous_y, plot_x, plot_y, color="light green", width=2)
            previous_x = plot_x
            previous_y = plot_y
            
                    
    def plot_sound(self, wave):
        self._debug_2("In _plot_sound()")
        if self.voice_window_open == False:
            self._debug_2("Can't plot sounds as voice editor window is closed.")
            return
        left_channel = np.hsplit(wave,2)[0]
        # right_channel = np.hsplit(wave,2)[1]
        self._debug_2("Waveform length in _plot_sound() = " + str(len(wave)))
        max_level = np.max(np.abs(left_channel))
        if max_level == 0:
            self._debug_1("WARNING: zero waveform in plot_sound().")
            return -1
        
        self.audio_scope.clear()
        self.audio_scope.bg = "dark gray"
        self.duration_display.value = str(int(len(left_channel) * 1000 / const.SAMPLE_RATE))
        
        # Set graph origin to the middle, left edge of the drawing area.
        origin_x = 0
        origin_y = int(self.audio_scope.height / 2)
        # Set initial values of the start of the lines being drawn.
        previous_x = origin_x
        previous_y = origin_y
        # Set the number of points to plot. 
        num_points = const.SAMPLE_RATE * 0.020 # 20 miliseconds worth of input samples.
        # Increase no. of points to plot in steps of 50ms worth of samples.
        while num_points < len(left_channel):
            if num_points < const.SAMPLE_RATE * 0.1:
                num_points += const.SAMPLE_RATE * 0.020 # add 20 msec to timescale
            else:
                num_points += const.SAMPLE_RATE * 0.050 # add 50 msec to timescale
        # Scale down the x axis
        sub_sampling_factor = 2 # found by trial and error
        num_points = int(num_points // sub_sampling_factor) + sub_sampling_factor
        self._debug_2("Note length, graph length = " + str(len(left_channel)) + ", " + str(num_points))
        scope_trace = np.zeros(int(num_points), dtype = float)
        
        note_points = int(len(left_channel) / sub_sampling_factor)
        # Select the note points to be plotted
        for i in range(note_points):
            scope_trace[i] += left_channel[int(i * sub_sampling_factor)]
        # Calculate scale factors to fit plot inside drawing widget.
        scale_x = (self.audio_scope.width - 5)/ num_points
        max_y = max(left_channel)
        min_y = min(left_channel)
        self._debug_2("Audio waveform (min, max) = " + str(min_y) + ", " + str(max_y) + ")")
        max_y_range = max_y - min_y
        scale_y = 0.9 * (self.audio_scope.height - 5)/ max_y_range
        x_offset = 0
        for i in range(num_points):
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * scope_trace[int(i + x_offset)]))
            plot_x = int(origin_x + (scale_x * i))
            self.audio_scope.line(previous_x, previous_y, plot_x, plot_y, color="light green", width=2)
            previous_x = plot_x
            previous_y = plot_y

    def _closed_voice_editor(self):
        self._debug_1("Voice editor closed")
        self.view.on_request_voice_editor_closed()
        self.window.destroy()

            
    #---------------------- Helper Functions --------------------
    # (intended only for use inside this module)
                

    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print("voice_editor.py: " + message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print("voice_editor.py: " + message)
    
    def _identify_key_number(self, x, y):
        self._debug_2("In _identify_key_number()")
        key = -1 # default value for "not a key"
        
        if y > BK_Y0 and y < BK_Y0 + BK_HEIGHT:
            
            if x > BK_X0 and (x - BK_X0) % KEY_X_SPACING < BK_WIDTH:
                octave = int((x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + BK_X0
                key = black_keys[int((x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                if key >= 0:
                    self._debug_2("Black key pressed with number = " + str(key))
                      
        elif y > BK_Y0 + BK_HEIGHT and y < BK_Y0 + WK_HEIGHT:
            
            if x > WK_X0 and (x - WK_X0) % KEY_X_SPACING < WK_WIDTH:
                octave = int((x - WK_X0) / (7 * KEY_X_SPACING))
                octave_origin = (7 * octave * KEY_X_SPACING) + WK_X0
                key = white_keys[int((x - octave_origin) / KEY_X_SPACING)] + (12 * octave)
                if key >= 0:
                    self._debug_2("White key pressed with number = " + str(key))
        # Do extra safety-check (shouldn't really be necessary!)
        if key >= NUM_KEYS:
            key = -1
        return key
        
    #-------------------- Event Handlers --------------------
       
    def _handle_new_voice(self):
        self._debug_2("In _handle_new_voice: ")
        # Request new voice
        self.view.controller.on_request_new_voice()        
        
    def _handle_select_voice(self, value):
        self._debug_2("In _handle_set_voice: " + str(value))
        # pass on the number part of the string value
        self.view.controller.on_request_select_voice(int(value[6:]) - 1)
    
    def _handle_set_waveform(self, waveform):
        self._debug_2("In _handle_set_waveform()")
        if waveform == "Sawtooth" or waveform == "Square":
            self.width_label.show()
            self.width_slider.show()
        else:
            self.width_label.hide()
            self.width_slider.hide()
        self.view.controller.on_request_waveform(waveform)
        
    def _handle_set_width(self, value):
        self._debug_2("In _handle_set_width()")
        self.view.controller.on_request_width(value)
        
    def _handle_set_attack(self, value):
        self._debug_2("In _handle_set_attack()")
        self.view.controller.on_request_attack(int(value))

    def _handle_set_decay(self, value):
        self._debug_2("In _handle_set_decay()")
        self.view.controller.on_request_decay(int(value))
        
    def _handle_set_sustain(self, value):
        self._debug_2("In _handle_set_sustain()")
        self.view.controller.on_request_sustain(int(value))
        
    def _handle_set_sustain_level(self, value):
        self._debug_2("In _handle_set_sustain_level()")
        self.view.controller.on_request_sustain_level(value)
        
    def _handle_set_release(self, value):
        self._debug_2("In _handle_set_release()")
        self.view.controller.on_request_release(int(value))
        
    def _handle_set_tremolo_rate(self, value):
        self._debug_2("In _handle_set_tremolo_rate()")
        self.view.controller.on_request_tremolo_rate(int(value))
        
    def _handle_set_tremolo_depth(self, value):
        self._debug_2("In _handle_set_tremolo_depth()")
        self.view.controller.on_request_tremolo_depth(int(value))
        
    def _handle_set_harmonic_boost(self, value):
        self._debug_2("In _handle_set_harmonic_boost()")
        self.view.controller.on_request_harmonic_boost(int(value))
        
    def _handle_set_vibrato_rate(self, value):
        self._debug_2("In _handle_set_vibrato_rate()")
        self.view.controller.on_request_vibrato_rate(int(value))
        
    def _handle_set_vibrato_depth(self, value):
        self._debug_2("In _handle_set_vibrato_depth()")
        self.view.controller.on_request_vibrato_depth(int(value))
        
    def _handle_set_unison_voices(self, value):
        self._debug_2("In _handle_set_unison_voices()")
        self.view.controller.on_request_unison_voices(int(value))
        
    def _handle_set_unison_detune(self, value):
        self._debug_2("In _handle_set_unison_detune()")
        self.view.controller.on_request_unison_detune(int(value))
        
    def _handle_set_ring_mod_rate(self, value):
        self._debug_2("In _handle_set_ring_mod_rate()")
        self.view.controller.on_request_ring_mod_rate(int(value))
        
    def _handle_request_play(self):
        self._debug_2("In _handle_request_play()")
        self.view.controller.on_request_play()
        
    def _handle_request_test(self):
        self._debug_2("In _handle_request_test()")
        self.update_display = False
        self.view.controller.on_request_test()
        self.update_display = True
               
    def _handle_mouse_dragged(self, event):
        self._debug_2("Mouse (pointer) deragged event at: (" + str(event.x) + ", " + str(event.y) + ")")
        if event.x < 0 or event.x >= self.keyboard.width or event.y < 0 or event.y >= self.keyboard.height:
            self._debug_2("WARNING: Mouse out of keyboard drawing.")
            return
        key = self._identify_key_number(event.x, event.y)
        if key >= 0:
            if key != self.previous_key:
                self.view.controller.on_request_note(key)
        else:
            self._debug_2("Not a key")
        self.previous_key = key
        
    def _handle_key_pressed(self, event):
        self._debug_2("Mouse left button pressed event at: (" + str(event.x) + ", " + str(event.y) + ")")
        key = self._identify_key_number(event.x, event.y)
        if key >= 0:
            self.view.controller.on_request_note(key)
        else:
            self._debug_2("Not a key")        


