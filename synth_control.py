# ------------------------------
# Imports
# ------------------------------

import time
import numpy as np
from synth_view import View
from synth_model import Model
from synth_settings import read_synth_settings, write_synth_settings

# ------------------------------
# Variables
# ------------------------------
SAMPLE_RATE = 44100
MAX_VOICES = 12
NUM_OCTAVES = 3
NUM_KEYS = (12 * NUM_OCTAVES) + 1
DEFAULT_FREQUENCY = 440
DEFAULT_ATTACK = 20
DEFAULT_DECAY = 20
DEFAULT_SUSTAIN = 100
DEFAULT_SUSTAIN_LEVEL = 50
DEFAULT_RELEASE = 20

# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 2
# ------------------------------
# Classes
# ------------------------------

# Note: Voice tones are stored separately in the model, because of their size.
class Voice_Parameters:
    def __init__(self):
        self.number = 0 # This number may be unrelated to the position of the voice in any lists.
        self.name = "Unused"
        self.waveform = "Sine"
        self.width = 100
        self.vibrato_rate = 0
        self.vibrato_depth = 0
        self.tremelo_rate = 0
        self.tremelo_depth = 0
        self.attack = DEFAULT_ATTACK
        self.decay = DEFAULT_DECAY
        self.sustain_time = DEFAULT_SUSTAIN
        self.sustain_level = DEFAULT_SUSTAIN_LEVEL
        self.release = DEFAULT_RELEASE        
        
class Controller:
    def __init__(self):
        self.sample_rate = SAMPLE_RATE
        self.frequency = DEFAULT_FREQUENCY
        self.num_voices = 1
        self.voices = []
        self.voice_index = 0
        self.view = View(self)
        self.model = Model(SAMPLE_RATE)
        
    def main(self):
        self._debug_2("In main of controller")
        # Create a list of voice parameter objects for each voice
        for voice_index in range(MAX_VOICES):
            voice_params = Voice_Parameters()
            self.voices.append(voice_params)
        self.restore_settings()
        self.model.main()
        self.view.main() # This function does not return control here.
        

    def on_request_voice(self, voice):
        self._debug_2("Set voice requested: " + str(voice))
        vi = int(voice)
        if vi >= 0 and vi < MAX_VOICES:
            self.voice_index = vi
            if vi > self.num_voices:
                self.num_voices = vi
            self.view.show_new_settings()
        else:
            self._debug_1("ERROR: unexpected voice index = " + str(voice))
        
    def on_request_waveform(self, waveform):
        self._debug_2("Set waveform requested: " + waveform)
        self.voices[self.voice_index].waveform = waveform
        note = self._change_note(self.voice_index)    
        if not note is None:
            self.view.play_sound(note)        
        
    def on_request_note(self, voice, key):
        self._debug_2("Getting note for voice, key " + str(voice) + ", " + str(key))
        tone = self.model.fetch_tone(voice, key)
        note = self.model.apply_envelope(tone)   
        if not note is None:
            self.view.play_sound(note)
            
    def on_request_frequency(self, frequency):
        self._debug_2("Set frequency to " + str(frequency))
        self.frequency = float(frequency)
        note = self._change_note(self.voice_index)    
        if not note is None:
            self.view.play_sound(note)
                       
    def on_request_width(self, width):
        voice = self.voices[self.voice_index]
        if voice.waveform == "Sawtooth" or voice.waveform == "Square":
            self._debug_2("Set width to " + str(width))
            self.voices[self.voice_index].width = float(width)
            note = self._change_note(self.voice_index)    
            if not note is None:
                self.view.play_sound(note)
        else:
            self._debug_1("Width of this waveform is fixed.")

    def on_request_attack(self, value):
        self._debug_2("Set attack to " + str(value))
        self.voices[self.voice_index].attack = int(value)
        self._change_envelope()
        
    def on_request_decay(self, value):
        self._debug_2("Set decay to " + str(value))
        self.voices[self.voice_index].decay = int(value)
        self._change_envelope()
        
    def on_request_sustain(self, value):
        self._debug_2("Set sustain to " + str(value))
        self.voices[self.voice_index].sustain_time = int(value)
        self._change_envelope()
        
    def on_request_sustain_level(self, value):
        self._debug_2("Set sustain level to " + str(value))
        self.voices[self.voice_index].sustain_level = int(value)
        self._change_envelope()
        
    def on_request_release(self, value):
        self._debug_2("Set release to " + str(value))
        self.voices[self.voice_index].release = int(value)
        self._change_envelope()
                    
    def on_request_play(self):
        self._debug_2("Play Sound requested.")
        note = self._change_note(self.voice_index)    
        if not note is None:
            self.view.play_sound(note)
            
    def on_request_sequence(self):
        self._debug_2("Play Sequence requested.")
        self._debug_2("\nDoing 100 note sequence")
        start = time.perf_counter()
        next_time = start + 0.1
        voice = 0
        note = 0
        while voice < 4:
            while note < 25:
                self.on_request_note(voice, note % NUM_KEYS)
                now = time.perf_counter()
                time.sleep(next_time - now)
                #time.sleep(0.15)
                next_time += 0.100
                note += 1
            voice += 1
            note = 0
        finish = time.perf_counter()
        self._debug_2("100 notes in seconds = " + str(finish - start))
  
        
    def on_request_shutdown(self):
        self._debug_2("Shutdown requested")
        self.save_settings()
        self.view.shutdown()
    
    def save_settings(self):
        names = []
        values = []
        names.append("sample_rate")
        values.append(self.sample_rate)
        names.append("frequency")
        values.append(int(self.frequency))
        names.append("num_voices")
        values.append(self.num_voices)
        names.append("voice_index")
        values.append(self.voice_index)
        for vi in range(self.num_voices):
            name_prefix = "voice_" + str(vi) + "_"
            #print("name_prefix = " + name_prefix)
            names.append(name_prefix + "number")
            values.append(self.voices[vi].number)
            names.append(name_prefix + "name")
            values.append(self.voices[vi].name)
            names.append(name_prefix + "waveform")
            values.append(self.voices[vi].waveform)
            names.append(name_prefix + "width")
            values.append(int(self.voices[vi].width))
            names.append(name_prefix + "vibrato_rate")
            values.append(int(self.voices[vi].vibrato_rate))
            names.append(name_prefix + "vibrato_depth")
            values.append(int(self.voices[vi].vibrato_depth))
            names.append(name_prefix + "tremelo_rate")
            values.append(int(self.voices[vi].tremelo_rate))
            names.append(name_prefix + "tremelo_depth")
            values.append(int(self.voices[vi].tremelo_depth))
            names.append(name_prefix + "attack")
            values.append(int(self.voices[vi].attack))
            names.append(name_prefix + "decay")
            values.append(int(self.voices[vi].decay))
            names.append(name_prefix + "sustain_time")
            values.append(int(self.voices[vi].sustain_time))
            names.append(name_prefix + "sustain_level")
            values.append(int(self.voices[vi].sustain_level))
            names.append(name_prefix + "release")
            values.append(int(self.voices[vi].release))
        write_synth_settings("synth_settings.txt", names, values)
        
    def restore_settings(self):
        names, values = read_synth_settings("synth_settings.txt")
        for i in range(len(names)):
            if names[i] == "sample_rate":
                self.sample_rate = int(values[i])
            elif names[i] == "frequency":
                self.frequency = int(values[i])
            elif names[i] == "num_voices":
                self.num_voices = int(values[i])
            elif names[i] == "voice_index":
                self.voice_index = int(values[i])
            else:
                for vi in range(self.num_voices):
                    name_prefix = "voice_" + str(vi) + "_"
                    #print("name_prefix = " + name_prefix)
                    if names[i] == name_prefix + "number":
                        self.voices[vi].number = int(values[i])
                    elif names[i] == name_prefix + "name":
                        self.voices[vi].name = values[i]
                    elif names[i] == name_prefix + "waveform":
                        self.voices[vi].waveform = values[i]
                    elif names[i] == name_prefix + "width":
                        self.voices[vi].width = int(values[i])
                    elif names[i] == name_prefix + "vibrato_rate":
                        self.voices[vi].vibrato_rate = int(values[i])
                    elif names[i] == name_prefix + "vibrato_depth":
                        self.voices[vi].vibrato_depth = int(values[i])
                    elif names[i] == name_prefix + "tremelo_rate":
                        self.voices[vi].tremelo_rate = int(values[i])
                    elif names[i] == name_prefix + "tremelo_depth":
                        self.voices[vi].tremelo_depth = int(values[i])
                    elif names[i] == name_prefix + "attack":
                        self.voices[vi].attack = int(values[i])
                    elif names[i] == name_prefix + "decay":
                        self.voices[vi].decay = int(values[i])
                    elif names[i] == name_prefix + "sustain_time":
                        self.voices[vi].sustain_time = int(values[i])
                    elif names[i] == name_prefix + "sustain_level":
                        self.voices[vi].sustain_level = int(values[i])
                    else:
                        pass # no error reporting!
                    

    # ------------------------------
    # Local Helper Functions
    # ------------------------------

    def _change_note(self, voice_index):
        voice = self.voices[voice_index]
        if voice.waveform == "Sine":
            tone = self.model.sine_wave(float(self.frequency))
        elif voice.waveform == "Triangle":
            tone = self.model.triangle_wave(float(self.frequency))
        elif voice.waveform == "Sawtooth":
            tone = self.model.pwm_sawtooth_wave(float(self.frequency), voice.width)
        elif voice.waveform == "Square":
            tone = self.model.pwm_square_wave(float(self.frequency), voice.width)
        else:
            self._debug_1("Warning, waveform unknown: " + str(voice.waveform))
            tone = None
        
        note = self.model.apply_envelope(tone)
        return note
    
    def _change_envelope(self):
        new_envelope = self.model.change_envelope(self.voices[self.voice_index])
        self.view.show_envelope(new_envelope)
  
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print("synth_control.py: " + message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print("synth_control.py: " + message)

# ------------------------------
# App
# ------------------------------

synth = Controller()
synth.main()
     


