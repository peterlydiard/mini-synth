# ------------------------------
# Imports
# ------------------------------
import guizero
import numpy as np
import time
import synth_constants as const
import synth_audio
import voice_editor
import seq_editor

# ------------------------------
# Variables
# ------------------------------
# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
sv_debug_level = 2
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
        self.voice_window_open = False
        self.sequence_window_open = False
        self.displayed_frequency = const.LOWEST_TONE
        

    def main(self):
        self._debug_1("In view.main()")
        
        synth_audio.initialise_audio()

        self.app = guizero.App("Mini-synth", width = 940, height = 710)
        
        self.top_menu = guizero.Box(self.app, layout = "grid")
        
        self.voice_editor_button = guizero.PushButton(self.top_menu, grid=[0,0], text="Voice editor", command=self.open_voice_editor)
        
        self.sequence_editor_button = guizero.PushButton(self.top_menu, grid=[1,0], text="Sequence editor", command=self.open_sequence_editor)

        # set up exit function
        self.app.when_closed = self._handle_close_app
        
        # enter endless loop, waiting for user input via guizero widgets.
        self.app.display()
        
        
    def open_voice_editor(self):
        self.voice_editor = voice_editor.Voice_Editor(self)
        self.voice_editor.main()
        self.voice_window_open = True
        
        
    def on_request_voice_editor_closed(self):
        self.voice_window_open = False
        
        
    def open_sequence_editor(self):
        self.seq_editor = seq_editor.Seq_Editor(self)
        self.seq_editor.main()
        self.sequence_window_open = True
        
        
    def on_request_seq_editor_closed(self):
        self.sequence_window_open = False

        
    def show_new_settings(self):
        self._debug_2("In show_new_settings()")
        if self.voice_window_open == True:
            self.voice_editor.show_new_settings()
        if self.sequence_window_open == True:
            self.seq_editor.show_sequence()            

    def show_sequence(self):
        self._debug_2("In show_sequence()")
        if self.sequence_window_open == True:
            self.seq_editor.show_sequence()           

    def show_sound(self, wave):
        if self.voice_window_open == True:
            self.voice_editor.plot_sound(wave)
        
        
    def show_envelope(self, envelope):
        if self.voice_window_open == True:
            self.voice_editor.plot_envelope(envelope)
        
            
    def play_sound(self, wave):
        self._debug_2("In play_sound()")
        synth_audio.play_sound(wave)
        
        
    def shutdown(self):
        self._debug_1("Normal termination")
        synth_audio.stop_audio_output()
        self.app.destroy()

    # Put the selected option at the top of the Combo list.    
    def update_combo(self, combo, option):
        self._debug_2("In update_combo()")
        if not combo.remove(option):
            self._debug_1("WARNING: Tried to remove unknown option = " + str(option))
        else:
            combo.insert(0, option)
            combo.select_default()
   
    def _handle_close_app(self):
        self._debug_2("In _handle_close_app()")
        self.controller.on_request_shutdown()
        

    def _debug_1(self, message):
        global debug_level
        if sv_debug_level >= 1:
            print("synth_view.py: " + message)
        
    def _debug_2(self, message):
        global debug_level
        if sv_debug_level >= 2:
            print("synth_view.py: " + message)
            
#--------------------------- end of View class ---------------------------

#--------------------------- Test Functions ------------------------------
if __name__ == "__main__":

    const.SAMPLE_RATE = 44100
    MAX_VOICES = 12
    MAX_TIMESLOTS = 60
    const.LOWEST_TONE = 110
    DEFAULT_FREQUENCY = 440
    DEFAULT_ATTACK = 20
    DEFAULT_DECAY = 20
    DEFAULT_SUSTAIN = 100
    DEFAULT_SUSTAIN_LEVEL = 50
    DEFAULT_RELEASE = 20
    
    sv_debug_level = 2

    class Voice_Parameters: 
        def __init__(self):
            self.number = 0 # This number may be unrelated to the position of the voice in any lists.
            self.name = "Unused"
            self.waveform = "Sine"
            self.colour = (0, 0, 0)
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
            self.harmonic_boost = 0
            
    class Sequence:
        def __init__(self):
            self.number = 0 
            self.name = "Blank"
            self.beats_per_bar = 4
            self.tempo = 100
            self.notes = np.zeros((MAX_VOICES, MAX_TIMESLOTS, const.NUM_KEYS), dtype=int)
        
    class TestController:
        def __init__(self):
            self.sample_rate = const.SAMPLE_RATE
            self.frequency = DEFAULT_FREQUENCY
            self.num_voices = 1
            self.voices = []
            self.voice_index = 0
            self.current_key = 12
            self.num_timeslots = 60
            self.view = View(self)
            self.sequence = Sequence()
        
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
            # Calculate frequency to display
            self.current_key = key
            self.displayed_frequency = int((const.LOWEST_TONE * np.power(2, key/12)) + 0.5)
            self.view.show_new_settings()
        
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
            self.view._debug_2("Set tremolo_rate to " + str(value))
        
        def on_request_tremolo_depth(self, value):
            self.view._debug_2("Set tremolo_depth to " + str(value))
            
        def on_request_harmonic_boost(self, value):
            self.view._debug_2("Set harmonic_boost to " + str(value))
            
        def on_request_vibrato_rate(self, value):
            self.view._debug_2("Set vibrato_rate to " + str(value))
        
        def on_request_vibrato_depth(self, value):
            self.view._debug_2("Set vibrato_depth to " + str(value))
           
        def on_request_play(self):
            self.view._debug_2("Play note requested")
            
        def on_request_test(self):
            self._debug_2("Play test requested.")
        
        def on_request_toggle_sequence_note(self, timeslot, vi, semitone):
            self._debug_2("Sequence note requested: timeslot, voice, semitone = "
                          + str(timeslot) + ", " + str(vi) + ", " + str(semitone))
            
        def on_request_beats(self, value):
            self._debug_2("Set beats/bar to " + str(value))
            self.sequence.beats_per_bar = int(value)
        
        def on_request_tempo(self, value):
            self.view._debug_2("Set tempo to " + str(value))
            self.sequence.tempo = int(value)
            
        def on_request_play_sequence(self):
            self.view._debug_2("Play sequence requested")
            
        def on_request_shutdown(self):
            self._debug_2("Shutdown requested")

        def _debug_1(self, message):
            global debug_level
            if sv_debug_level >= 1:
                print("synth_view.py: " + message)
            
        def _debug_2(self, message):
            global debug_level
            if sv_debug_level >= 2:
                print("synth_view.py: " + message)
            
            
    debug_level = 2       
    tc = TestController()
    tc.main()
