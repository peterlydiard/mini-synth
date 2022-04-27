# ------------------------------
# Imports
# ------------------------------

import time
import threading
import numpy as np
import synth_constants as const
import synth_view
import synth_model
import synth_data

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
        self.unison_voices = 1
        self.unison_detune = 0
        self.tremolo_rate = 0
        self.tremolo_depth = 0
        self.ring_mod_rate = 0
        self.attack = const.DEFAULT_ATTACK
        self.decay = const.DEFAULT_DECAY
        self.sustain_time = const.DEFAULT_SUSTAIN
        self.sustain_level = const.DEFAULT_SUSTAIN_LEVEL
        self.release = const.DEFAULT_RELEASE
        
class Sequence:
    def __init__(self):
        self.number = 0 
        self.name = "Blank"
        self.beats_per_bar = 4
        self.tempo = 100
        self.length = 0
        self.notes = np.zeros((const.MAX_VOICES, const.MAX_TIMESLOTS, const.NUM_KEYS), dtype=int)
        
class Controller:
    def __init__(self):
        self.sample_rate = const.SAMPLE_RATE
        self.frequency = const.DEFAULT_FREQUENCY
        self.num_voices = 1
        self.current_key = 12
        self.voice_params = []
        self.voice_index = 0
        self.num_timeslots = const.MAX_TIMESLOTS
        self.view = synth_view.View(self)
        self.model = synth_model.Model(self, const.SAMPLE_RATE)
        self.sequence = Sequence()
        self.thread_1 = None
        self.thread_2 = None
        
    def main(self):
        self._debug_2("In main of controller")
        # Create a list of voice parameter objects for each voice
        for voice_index in range(const.MAX_VOICES):
            voice_params = Voice_Parameters()
            self.voice_params.append(voice_params)
            self.voice_params[voice_index].colour = self.make_voice_colour(voice_index)
        self.restore_settings()
        self.restore_sequence()
        self.model.main(self.num_voices)
        self.view.main() # This function does not return control here.
        
    # Calculate colours for different voices/instruments on graphs and charts.
    def make_voice_colour(self, voice_index):
        shade_step = int(256 / const.MAX_VOICES)
        # start with black.
        red = 0
        blue = 0
        green = 0 
        # Calculate unique colours for each voice.
        if (voice_index % 3) == 0:
            red = max(30, 255 - int(voice_index * shade_step))
            green = min(255, int(voice_index * shade_step))
        if ((voice_index+2) % 3) == 0:
            green = max(30, 255 - int ((voice_index) * shade_step))
            blue = min(255, int((voice_index - 1) * shade_step))
        if ((voice_index+1) % 3) == 0:
            blue = max(30, 255 - int ((voice_index) * shade_step))
            red = min(255, int((voice_index - 2) * shade_step))
        self._debug_2("Made colour: (" + str(red) + ", " + str(green) + ", " + str(blue) + ")")
        return (red, green, blue)
        
    # Process request from view (user interface) for a new voice.
    def on_request_new_voice(self):
        self._debug_2("In on_request_new_voice() ")
        if self.num_voices < const.MAX_VOICES:
            self.voice_index = self.num_voices
            self.num_voices += 1
            self.view.show_new_settings()
        else:
            self._debug_1("WARNING: number of voices is at maximum already.")
        
    # Process request from view (user interface) to select an existing voice to display.
    def on_request_select_voice(self, voice):
        self._debug_2("In on_request_voice: " + str(voice))
        vi = int(voice)
        if vi >= 0 and vi < const.MAX_VOICES:
            self.voice_index = vi
            if vi > self.num_voices:
                self.num_voices = vi
            self.view.show_new_settings()
        else:
            self._debug_1("ERROR: unexpected voice index = " + str(voice))

    # Process request from view (user interface) to play the note for the given key and voice/instrument.
    def on_request_note(self, key, voice_index=-1):
        self._debug_2("In on_request_note(key, voice_index) = (" + str(key) + ", " + str(voice_index) + ")")
        self.current_key = key
        if voice_index >= 0:
            self.voice_index = voice_index
        self._play_current_note()            
        
    # Process request from view (user interface) to set the basic waveform for the current voice/instrument.
    def on_request_waveform(self, waveform):
        self._debug_2("In on_request_waveform: " + waveform)
        self.voice_params[self.voice_index].waveform = waveform
        self.view.show_new_settings()
        # Mark the old voice data as obsolete.
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the on/off ratio for a sawtooth or square wave.
    def on_request_width(self, width):
        self._debug_2("In on_request_width: " + str(width))
        voice = self.voice_params[self.voice_index]
        if voice.waveform == "Sawtooth" or voice.waveform == "Square":
            self._debug_2("Set width to " + str(width))
            self.voice_params[self.voice_index].width = float(width)
            self.model.scratch_voice(self.voice_index)
            self._play_current_note()
        else:
            self._debug_1("Width of this waveform is fixed.")

    # Process request from view (user interface) to adjust the attack time of the ADSR envelope.
    def on_request_attack(self, value):
        self._debug_2("In on_request_attack: " + str(value))
        self.voice_params[self.voice_index].attack = int(value)
        self._change_envelope()
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the decay time of the ADSR envelope.
    def on_request_decay(self, value):
        self._debug_2("In on_request_decay: " + str(value))
        self.voice_params[self.voice_index].decay = int(value)
        self._change_envelope()
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the sustain time of the ADSR envelope.
    def on_request_sustain(self, value):
        self._debug_2("In on_request_sustain: " + str(value))
        self.voice_params[self.voice_index].sustain_time = int(value)
        self._change_envelope()
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the sustain level of the ADSR envelope.
    def on_request_sustain_level(self, value):
        self._debug_2("In on_request_sustain_level: " + str(value))
        self.voice_params[self.voice_index].sustain_level = int(value)
        self._change_envelope()
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the release time of the ADSR envelope.
    def on_request_release(self, value):
        self._debug_2("In on_request_release: " + str(value))
        self.voice_params[self.voice_index].release = int(value)
        self._change_envelope()
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the tremolo rate of the ADSR envelope.
    def on_request_tremolo_rate(self, value):
        self._debug_2("In on_request_tremolo_rate: " + str(value))
        self.voice_params[self.voice_index].tremolo_rate = int(value)
        self._change_envelope()
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the tremolo depth of the ADSR envelope.
    def on_request_tremolo_depth(self, value):
        self._debug_2("In on_request_tremolo_depth: " + str(value))
        self.voice_params[self.voice_index].tremolo_depth = int(value)
        self._change_envelope()
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the fundamental fequency suppression of the tone.
    def on_request_harmonic_boost(self, value):
        self._debug_2("In on_request_harmonic_boost: " + str(value))
        self.voice_params[self.voice_index].harmonic_boost = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the vibrato rate of the tone.
    def on_request_vibrato_rate(self, value):
        self._debug_2("In on_request_vibrato_rate: " + str(value))
        self.voice_params[self.voice_index].vibrato_rate = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the vibrato depth of the tone.
    def on_request_vibrato_depth(self, value):
        self._debug_2("In on_request_vibrato_depth: " + str(value))
        self.voice_params[self.voice_index].vibrato_depth = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the number of unison voices in the tone.
    def on_request_unison_voices(self, value):
        self._debug_2("In on_request_unison_voices: " + str(value))
        self.voice_params[self.voice_index].unison_voices = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the frequency spread of unison voices in the tone.
    def on_request_unison_detune(self, value):
        self._debug_2("In on_request_unison_detune: " + str(value))
        self.voice_params[self.voice_index].unison_detune = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
        
    # Process request from view (user interface) to adjust the ring modulator frequency applied to the tone.
    def on_request_ring_mod_rate(self, value):
        self._debug_2("In on_request_ring_mod_rate: " + str(value))
        self.voice_params[self.voice_index].ring_mod_rate = int(value)
        self.model.scratch_voice(self.voice_index)
        self._play_current_note()
    
    # Local helper function to display and play the current note as recently modified in the voice editor.
    def _play_current_note(self):
        self._debug_2("In _play_current_note().")        
        tone, frequency = self.model.fetch_tone(self.voice_index, self.current_key)
        note = self.model.apply_envelope(self.voice_index, tone) 
        if not note is None:
            self.view.play_sound(note)
            self.view.show_sound(note)
            self.view.show_frequency(frequency)
        else:
            self._debug_1("WARNING: No note in _play_current_note().")
            
    # Process request from view (user interface) to play the current note.
    def on_request_play(self):
        self._debug_2("In on_request_play().")
        self._play_current_note()
            
    # Process request from view (user interface) to play 100 notes. (All keys in order.)
    def on_request_test(self):
        self._debug_2("In on_request_test().")
        if not self.thread_1 is None:
            self._debug_2("Waiting for previous test to complete.")
            self.thread_1.join()
        self.thread_1 = threading.Thread(target=self._run_test)
        self.thread_1.start()
    
    def _run_test(self):
        self._debug_2("In _run_test().")
        self._debug_2("Doing 100 note test")
        start = time.perf_counter()
        self._debug_1("Timer start = " + str(start))
        next_time = start + 0.100
        time_asleep = 0
        key = 0
        while key < 100:
            tone, frequency = self.model.fetch_tone(self.voice_index, key % const.NUM_KEYS)
            self.frequency = frequency # noqa
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

    # Process request from view (user interface) to add or remove a note on the sequence editor grid.
    def on_request_toggle_sequence_note(self, timeslot, voice_index, key):
        self._debug_2("In on_request_toggle_sequence_note: " + str(timeslot) + ", " + str(voice_index) + ", " + str(key))
        if self.sequence.notes[voice_index, timeslot, key] == 1:
            self.sequence.notes[voice_index, timeslot, key] = 0
            self._debug_2("Cleared note.")
            # Note: sequence length is recalcualted when sequence is read back from the file.
        else:
            self.sequence.notes[voice_index, timeslot, key] = 1
            self._debug_2("Set note.")
            if timeslot >= self.sequence.length:
                self.sequence.length = timeslot + 1
        
    # Process request from view (user interface) to set the beats per bar shown in the sequence editor.
    def on_request_set_beats(self, value):
        self._debug_2("Set beats/bar to " + str(value))
        self.sequence.beats_per_bar = int(value)
        
    # Process request from view (user interface) to set the bars per minute in the sequence editor.
    def on_request_set_tempo(self, value):
        self._debug_2("Set tempo to " + str(value))
        self.sequence.tempo = int(value)
        
    # Process request from view (user interface) to play the sequence.
    def on_request_play_sequence(self):
        self._debug_2("In on_request_play_sequence()")
        if not self.thread_2 is None:
            self._debug_2("Waiting for previous sequence to complete.")
            self.thread_2.join()
        self.thread_2 = threading.Thread(target=self._play_sequence)
        self.thread_2.start()

    def _play_sequence(self):
        self._debug_2("In _play_sequence()")
        timeslot = 0
        note_spacing_secs = 60.0 / (self.sequence.tempo * self.sequence.beats_per_bar)
        start = time.perf_counter()
        self._debug_1("Timer start = " + str(start))
        next_time = start + note_spacing_secs
        time_asleep = 0
        while timeslot < self.sequence.length:
            self._debug_2("Timeslot = " + str(timeslot))
            for vi in range(self.num_voices):
                for key in range(const.NUM_KEYS):
                    if self.sequence.notes[vi, timeslot, key] > 0:
                        tone, frequency = self.model.fetch_tone(vi, key)
                        self.frequncy = frequency # noqa
                        note = self.model.apply_envelope(vi, tone) 
                        if not note is None:
                            self.view.play_sound(note)
            now = time.perf_counter()
            sleep_time = next_time - now
            time_asleep += sleep_time
            time.sleep(max(0, sleep_time))
            next_time += note_spacing_secs
            timeslot += 1
        finish = time.perf_counter()
        self._debug_1("Sequence duration, secs = " + str(finish - start))
        self._debug_1("Time asleep in seconds = " + str(time_asleep))                               
            
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
            values.append(self.voice_params[vi].number)
            names.append(name_prefix + "name")
            values.append(self.voice_params[vi].name)
            names.append(name_prefix + "waveform")
            values.append(self.voice_params[vi].waveform)
            names.append(name_prefix + "width")
            values.append(int(self.voice_params[vi].width))
            names.append(name_prefix + "harmonic_boost")
            values.append(int(self.voice_params[vi].harmonic_boost))
            names.append(name_prefix + "vibrato_rate")
            values.append(int(self.voice_params[vi].vibrato_rate))
            names.append(name_prefix + "vibrato_depth")
            values.append(int(self.voice_params[vi].vibrato_depth))
            names.append(name_prefix + "unison_voices")
            values.append(int(self.voice_params[vi].unison_voices))
            names.append(name_prefix + "unison_detune")
            values.append(int(self.voice_params[vi].unison_detune))
            names.append(name_prefix + "ring_mod_rate")
            values.append(int(self.voice_params[vi].ring_mod_rate))
            names.append(name_prefix + "tremolo_rate")
            values.append(int(self.voice_params[vi].tremolo_rate))
            names.append(name_prefix + "tremolo_depth")
            values.append(int(self.voice_params[vi].tremolo_depth))
            names.append(name_prefix + "attack")
            values.append(int(self.voice_params[vi].attack))
            names.append(name_prefix + "decay")
            values.append(int(self.voice_params[vi].decay))
            names.append(name_prefix + "sustain_time")
            values.append(int(self.voice_params[vi].sustain_time))
            names.append(name_prefix + "sustain_level")
            values.append(int(self.voice_params[vi].sustain_level))
            names.append(name_prefix + "release")
            values.append(int(self.voice_params[vi].release))
        synth_data.write_synth_data("synth_settings.txt", names, values)
        
    def restore_settings(self):
        names, values = synth_data.read_synth_data("synth_settings.txt")
        for i in range(len(names)):
            if names[i] == "sample_rate":
                self.sample_rate = int(values[i])
            elif names[i] == "frequency":
                self.frequency = int(values[i])
            elif names[i] == "num_voices":
                self.num_voices = min(int(values[i]), const.MAX_VOICES)
            elif names[i] == "voice_index":
                self.voice_index = min(int(values[i]), self.num_voices - 1)
            else:
                for vi in range(self.num_voices):
                    name_prefix = "voice_" + str(vi) + "_"
                    if names[i] == name_prefix + "number":
                        self.voice_params[vi].number = int(values[i])
                    elif names[i] == name_prefix + "name":
                        self.voice_params[vi].name = values[i]
                    elif names[i] == name_prefix + "waveform":
                        self.voice_params[vi].waveform = values[i]
                    elif names[i] == name_prefix + "width":
                        self.voice_params[vi].width = int(values[i])
                    elif names[i] == name_prefix + "harmonic_boost":
                        self.voice_params[vi].harmonic_boost = int(values[i])
                    elif names[i] == name_prefix + "vibrato_rate":
                        self.voice_params[vi].vibrato_rate = int(values[i])
                    elif names[i] == name_prefix + "vibrato_depth":
                        self.voice_params[vi].vibrato_depth = int(values[i])
                    elif names[i] == name_prefix + "unison_voices":
                        self.voice_params[vi].unison_voices = int(values[i])
                    elif names[i] == name_prefix + "unison_detune":
                        self.voice_params[vi].unison_detune = int(values[i])
                    elif names[i] == name_prefix + "ring_mod_rate":
                        self.voice_params[vi].ring_mod_rate = int(values[i])
                    elif names[i] == name_prefix + "tremolo_rate":
                        self.voice_params[vi].tremolo_rate = int(values[i])
                    elif names[i] == name_prefix + "tremolo_depth":
                        self.voice_params[vi].tremolo_depth = int(values[i])
                    elif names[i] == name_prefix + "attack":
                        self.voice_params[vi].attack = int(values[i])
                    elif names[i] == name_prefix + "decay":
                        self.voice_params[vi].decay = int(values[i])
                    elif names[i] == name_prefix + "sustain_time":
                        self.voice_params[vi].sustain_time = int(values[i])
                    elif names[i] == name_prefix + "sustain_level":
                        self.voice_params[vi].sustain_level = int(values[i])
                    else:
                        pass # no error reporting!
                    

    def save_sequence(self):
        names = []
        values = []
        names.append("sequence_number")
        values.append(int(self.sequence.number))
        names.append("sequence_name")
        values.append(self.sequence.name)
        names.append("beats_per_bar")
        values.append(int(self.sequence.beats_per_bar))
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
        synth_data.write_synth_data("sequence.txt", names, values)


    def restore_sequence(self):
        names, values = synth_data.read_synth_data("sequence.txt")
        for i in range(len(names)):
            if names[i] == "sequence_number":
                self.sequence.number = int(values[i])
            if names[i] == "sequence_name":
                self.sequence.name = values[i]
            if names[i] == "beats_per_bar":
                self.sequence.beats_per_bar = int(values[i])  
            if names[i] == "sequence_tempo":
                self.sequence.tempo = int(values[i])
            self.sequence.length = 0  # length is calulated below!          
            for vi in range(self.num_voices):
                voice_name = "voice_" + str(vi) + "_"
                for timeslot in range(self.num_timeslots):
                    timeslot_name = "timeslot_" + str(timeslot) + "_"
                    for key in range(const.NUM_KEYS):
                        key_name = "key_" + str(key)
                        if names[i] == voice_name + timeslot_name + key_name:
                            self.sequence.notes[vi, timeslot, key] = values[i]
                            self.sequence.length = timeslot + 1


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


#--------------------------- Test Functions ------------------------------
if __name__ == "__main__":

    # ------------------------------
    # App
    # ------------------------------

    synth = Controller()
    synth.main()

