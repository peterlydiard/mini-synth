# ------------------------------
# Imports
# ------------------------------

import time
import numpy as np
import synth_constants as const
from synth_view import View
from synth_model import Model
from synth_settings import read_synth_settings, write_synth_settings

# ------------------------------
# Variables
# ------------------------------

# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 2
# ------------------------------
# Classes
# ------------------------------

# Note: Voice tones are stored separately in the model, because of their size.
class Voice_Parameters:
    def __init__(self):
        self.number = 0 # This number may be unrelated to the position of the voice in any lists.
        self.name = "Blank"
        self.colour = (0,0,0)
        self.waveform = "Sine"
        self.width = 100
        self.harmonic_boost = 0
        self.vibrato_rate = 0
        self.vibrato_depth = 0
        self.tremolo_rate = 0
        self.tremolo_depth = 0
        self.attack = const.DEFAULT_ATTACK
        self.decay = const.DEFAULT_DECAY
        self.sustain_time = const.DEFAULT_SUSTAIN
        self.sustain_level = const.DEFAULT_SUSTAIN_LEVEL
        self.release = const.DEFAULT_RELEASE
        
class Sequence:
    def __init__(self):
        self.number = 0 
        self.name = "Blank"
        self.tempo = 100
        self.notes = np.zeros((const.MAX_VOICES, const.MAX_TIMESLOTS, const.NUM_KEYS), dtype=int)
        
class Controller:
    def __init__(self):
        self.sample_rate = const.SAMPLE_RATE
        self.frequency = const.DEFAULT_FREQUENCY
        self.num_voices = 1
        self.current_key = 12
        self.voices = []
        self.voice_index = 0
        self.num_timeslots = const.MAX_TIMESLOTS
        self.view = View(self)
        self.model = Model(self, const.SAMPLE_RATE)
        self.sequence = Sequence()
        
    def main(self):
        self._debug_2("In main of controller")
        # Create a list of voice parameter objects for each voice
        for voice_index in range(const.MAX_VOICES):
            voice_params = Voice_Parameters()
            self.voices.append(voice_params)
            self.voices[voice_index].colour = self.make_voice_colour(voice_index)
        self.restore_settings()
        self.restore_sequence()
        self.model.main()
        self.view.main() # This function does not return control here.
        
    def make_voice_colour(self, voice_index):
        shade_step = int(192 * 3 / const.MAX_VOICES)
        # start with black.
        red = 0
        blue = 0
        green = 0 
        # Pick bright colours in rotation making the colours components darker for higher voices.
        if (voice_index % 3) == 0:
            red = 255 - int(voice_index * shade_step)
        if ((voice_index+1) % 3) == 0:
            green = 255 - int (voice_index * shade_step)
        if ((voice_index+2) % 3) == 0:
            blue = 255 - int (voice_index * shade_step)
        return (red, green, blue)
        
    def on_request_voice(self, voice):
        self._debug_2("In on_request_voice: " + str(voice))
        vi = int(voice)
        if vi >= 0 and vi < const.MAX_VOICES:
            self.voice_index = vi
            if vi > self.num_voices:
                self.num_voices = vi
            self.view.show_new_settings()
        else:
            self._debug_1("ERROR: unexpected voice index = " + str(voice))

    def on_request_note(self, key, voice_index = -1):
        self._debug_2("In on_request_note(key, voice_index) = (" + str(key) + ", " + str(voice_index) + ")")
        # Calculate frequency to display
        self.current_key = key
        self.frequency = int((const.LOWEST_TONE * np.power(2, key/12)) + 0.5)
        if voice_index < 0: # If no voice_index given, use last stored value.
            voice_index = self.voice_index
        self._play_current_note()            
        
    def on_request_waveform(self, waveform):
        self._debug_2("In on_request_waveform: " + waveform)
        self.voices[self.voice_index].waveform = waveform
        self.view.show_new_settings()
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    def on_request_width(self, width):
        self._debug_2("In on_request_width: " + str(width))
        voice = self.voices[self.voice_index]
        if voice.waveform == "Sawtooth" or voice.waveform == "Square":
            self._debug_2("Set width to " + str(width))
            self.voices[self.voice_index].width = float(width)
            self.model.scratch_voice(self.voice_index)
            self._play_current_note()
        else:
            self._debug_1("Width of this waveform is fixed.")

    def on_request_attack(self, value):
        self._debug_2("In on_request_attack: " + str(value))
        self.voices[self.voice_index].attack = int(value)
        self._change_envelope()
        self._play_current_note()
        
    def on_request_decay(self, value):
        self._debug_2("In on_request_decay: " + str(value))
        self.voices[self.voice_index].decay = int(value)
        self._change_envelope()
        self._play_current_note()
        
    def on_request_sustain(self, value):
        self._debug_2("In on_request_sustain: " + str(value))
        self.voices[self.voice_index].sustain_time = int(value)
        self._change_envelope()
        self._play_current_note()
        
    def on_request_sustain_level(self, value):
        self._debug_2("In on_request_sustain_level: " + str(value))
        self.voices[self.voice_index].sustain_level = int(value)
        self._change_envelope()
        self._play_current_note()
        
    def on_request_release(self, value):
        self._debug_2("In on_request_release: " + str(value))
        self.voices[self.voice_index].release = int(value)
        self._change_envelope()
        self._play_current_note()
        
    def on_request_tremolo_rate(self, value):
        self._debug_2("In on_request_tremolo_rate: " + str(value))
        self.voices[self.voice_index].tremolo_rate = int(value)
        self._change_envelope()
        self._play_current_note()
        
    def on_request_tremolo_depth(self, value):
        self._debug_2("In on_request_tremolo_depth: " + str(value))
        self.voices[self.voice_index].tremolo_depth = int(value)
        self._change_envelope()
        self._play_current_note()
        
    def on_request_harmonic_boost(self, value):
        self._debug_2("In on_request_harmonic_boost: " + str(value))
        self.voices[self.voice_index].harmonic_boost = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    def on_request_vibrato_rate(self, value):
        self._debug_2("In on_request_vibrato_rate: " + str(value))
        self.voices[self.voice_index].vibrato_rate = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    def on_request_vibrato_depth(self, value):
        self._debug_2("In on_request_vibrato_depth: " + str(value))
        self.voices[self.voice_index].vibrato_depth = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
                   
    def _play_current_note(self):
        tone = self.model.fetch_tone(self.voice_index, self.current_key)
        note = self.model.apply_envelope(self.voice_index, tone) 
        if not note is None:
            self.view.play_sound(note)
            self.view.show_sound(note)
            
    def on_request_play(self):
        self._debug_2("In on_request_play().")
        self._play_current_note()
            
    def on_request_test(self):
        self._debug_2("In on_request_test().")
        self._debug_2("\nDoing 100 note test")
        start = time.perf_counter()
        self._debug_1("Timer start = " + str(start))
        next_time = start + 0.100
        time_asleep = 0
        key = 0
        while key < 100:
            tone = self.model.fetch_tone(self.voice_index, key % const.NUM_KEYS)
            note = self.model.apply_envelope(self.voice_index, tone) 
            if not note is None:
                self.view.play_sound(note)
            now = time.perf_counter()
            sleep_time = next_time - now
            time_asleep += sleep_time
            time.sleep(max(0, sleep_time))
            next_time += 0.100
            key += 1
        finish = time.perf_counter()
        self._debug_1("100 notes in seconds = " + str(finish - start))
        self._debug_1("Time asleep in seconds = " + str(time_asleep))

    def on_request_toggle_sequence_note(self, timeslot, voice_index, key):
        self._debug_2("In on_request_toggle_sequence_note: " + str(timeslot) + ", " + str(voice_index) + ", " + str(key))
        if self.sequence.notes[voice_index, timeslot, key] == 1:
            self.sequence.notes[voice_index, timeslot, key] = 0
            self._debug_2("Cleared note.")
        else:
            self.sequence.notes[voice_index, timeslot, key] = 1
            self._debug_2("Set note.")
        
    def on_request_tempo(self, value):
        self._debug_2("Set tempo to " + str(value))
        self.sequence.tempo = int(value)
        
    def on_request_play_sequence(self):
        self._debug_2("Play sequence requested")
            
    def on_request_shutdown(self):
        self._debug_2("Shutdown requested")
        self.save_settings()
        self.save_sequence()
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
            names.append(name_prefix + "harmonic_boost")
            values.append(int(self.voices[vi].harmonic_boost))
            names.append(name_prefix + "vibrato_rate")
            values.append(int(self.voices[vi].vibrato_rate))
            names.append(name_prefix + "vibrato_depth")
            values.append(int(self.voices[vi].vibrato_depth))
            names.append(name_prefix + "tremolo_rate")
            values.append(int(self.voices[vi].tremolo_rate))
            names.append(name_prefix + "tremolo_depth")
            values.append(int(self.voices[vi].tremolo_depth))
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
                    if names[i] == name_prefix + "number":
                        self.voices[vi].number = int(values[i])
                    elif names[i] == name_prefix + "name":
                        self.voices[vi].name = values[i]
                    elif names[i] == name_prefix + "waveform":
                        self.voices[vi].waveform = values[i]
                    elif names[i] == name_prefix + "width":
                        self.voices[vi].width = int(values[i])
                    elif names[i] == name_prefix + "harmonic_boost":
                        self.voices[vi].harmonic_boost = int(values[i])
                    elif names[i] == name_prefix + "vibrato_rate":
                        self.voices[vi].vibrato_rate = int(values[i])
                    elif names[i] == name_prefix + "vibrato_depth":
                        self.voices[vi].vibrato_depth = int(values[i])
                    elif names[i] == name_prefix + "tremolo_rate":
                        self.voices[vi].tremolo_rate = int(values[i])
                    elif names[i] == name_prefix + "tremolo_depth":
                        self.voices[vi].tremolo_depth = int(values[i])
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
                    

    def save_sequence(self):
        names = []
        values = []
        names.append("sequence_number")
        values.append(int(self.sequence.number))
        names.append("sequence_name")
        values.append(self.sequence.name)
        names.append("sequence_tempo")
        values.append(int(self.sequence.tempo))
        for vi in range(self.num_voices):
            voice_name = "voice_" + str(vi) + "_"
            for timeslot in range(self.num_timeslots):
                timeslot_name = "timeslot_" + str(timeslot) + "_"
                for key in range(const.NUM_KEYS):
                    key_name = "key_" + str(key)
                    if self.sequence.notes[vi, timeslot, key] > 0:
                        names.append(voice_name + timeslot_name + key_name)
                        values.append(int(self.sequence.notes[vi, timeslot, key]))
        write_synth_settings("sequence.txt", names, values)


    def restore_sequence(self):
        names, values = read_synth_settings("sequence.txt")
        for i in range(len(names)):
            if names[i] == "sequence_number":
                self.sequence.number = int(values[i])
            if names[i] == "sequence_name":
                self.sequence.name = values[i]
            if names[i] == "sequence_tempo":
                self.sequence.tempo = int(values[i])  
            for vi in range(self.num_voices):
                voice_name = "voice_" + str(vi) + "_"
                for timeslot in range(self.num_timeslots):
                    timeslot_name = "timeslot_" + str(timeslot) + "_"
                    for key in range(const.NUM_KEYS):
                        key_name = "key_" + str(key)
                        if names[i] == voice_name + timeslot_name + key_name:
                            self.sequence.notes[vi, timeslot, key] = values[i]


    # ------------------------------
    # Local Helper Functions
    # ------------------------------
    
    def _change_envelope(self):
        new_envelope = self.model.make_envelope(self.voice_index)
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
     


