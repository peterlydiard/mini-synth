#import FFT
import math
import string
import copy
# import pylab
# import numpy
import numpy as np
# import simpleaudio as sa
#from scipy import signal


######################### Global variables #########################

LOWEST_TONE = 110
FREQUENCY = 220    # Hz
WIDTH = 50
MAX_DURATION = 1000
STEREO = False
ATTACK = 200
DECAY = 200
SUSTAIN_TIME = 500
SUSTAIN_LEVEL = 50
RELEASE = 100
NUM_OCTAVES = 3
NUM_KEYS = (12 * NUM_OCTAVES) + 1
MAX_VOICES = 4

# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 1

####################################################################

class Model:
    def __init__(self, sample_rate, frequency=FREQUENCY, width=WIDTH, max_duration=MAX_DURATION, duration=MAX_DURATION, stereo=STEREO,
                 attack=ATTACK, decay=DECAY, sustain_time=SUSTAIN_TIME, sustain_level=SUSTAIN_LEVEL, release=RELEASE):
        self.sample_rate = sample_rate     # Hz
        self.frequency = frequency         # Hz
        self.max_duration = max_duration   # milliseconds
        self.duration = duration           # milliseconds
        self.stereo = stereo               # Boolean
        self.attack = attack               # milliseconds
        self.decay = decay                 # milliseconds
        self.sustain_time = sustain_time   # milliseconds
        self.sustain_level = sustain_level # range is 0..100
        self.release = release             # milliseconds
        self.envelopes = [] 
        self.voices = np.zeros((MAX_VOICES, NUM_KEYS, (int(sample_rate * MAX_DURATION / 1000))), dtype=float)


    def main(self, max_voices=MAX_VOICES):
        self.make_voice(0, "Sine")
        self.make_voice(1, "Triangle")
        self.make_voice(2, "Sawtooth", 100)
        self.make_voice(3, "Square", 100)
        for voice_index in range(MAX_VOICES):
            envelope = np.zeros((int(self.sample_rate * MAX_DURATION / 1000)), dtype=float)
            self.envelopes.append(envelope)
        pass
        
    # Create a unit-amplitude sine wave.
    def _sine_wave(self, frequency):
        self._debug_2("Sine wave freq, max duration (ms) = " + str(frequency) + ", " + str(self.max_duration))
        self.frequency = frequency
        # Generate array with duration*sample_rate steps, ranging between 0 and duration
        times_msec = np.linspace(0, self.max_duration, int(self.sample_rate * self.max_duration / 1000), False)
        self._debug_2("No. of samples = " + str(len(times_msec)))
        # Generate a sine wave
        radians_per_msec = 2 * np.pi * frequency / 1000
        tone = np.sin(radians_per_msec * times_msec)
        return tone


    # Create a unit-amplitude trianle wave.
    def _triangle_wave(self, frequency):
        self.frequency = frequency   
        # Generate linear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        ramp = np.linspace(0, (2 * frequency * self.max_duration/1000), int(self.sample_rate * self.max_duration/1000), False)
        # Generate a triangle wave
        tone = abs(((2 * ramp + 3 ) % 4.0) - 2) - 1
        return tone

    
    # Create a unit-amplitude sawtooth wave with pulse width control.
    def _pwm_sawtooth_wave(self, frequency, width):
        #print("Saw wave freq, width, duration = " + str(frequency) + ", " + str(width)+ ", " + str(duration))
        self.frequency = frequency
        width = float(width)
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * self.max_duration/1000) + 2 - width/100,
                           int(self.sample_rate * self.max_duration / 1000), False)
        # Generate a sawtooth wave
        tone = np.clip((100/width) * ((ramp % 2.0) + width/100 - 2.0), -1.0, 1.0)
        return tone
    
    
    # Create a unit-amplitude square wave with pulse width control.
    def _pwm_square_wave(self, frequency, width):
        #print("Square wave freq, duration = " + str(frequency) + ", " + str(duration))
        self.frequency = frequency
        width = float(width)
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * self.max_duration / 1000) + 2 - width/100,
                           int(self.sample_rate * self.max_duration / 1000), False)
        # Generate a square wave, clip sine to avoid using scipy library.
        tone = np.clip(1000 * ((ramp % 2.0) + (width/100) - 2.0), -1.0, 1.0)
        return tone
    
    
    # Apply the envelope amplitude to the tone to make a note
    def apply_envelope(self, voice_index, tone, stereo=True):
        self._debug_2("In apply_envelope() ")
        if tone is None:
            self._debug_1("ERROR: tone is None in apply_envelope().")
            return None
        if voice_index < 0 or voice_index > MAX_VOICES:
            self._debug_1("ERROR: voice_index = " + str(voice_index))
            return None
        self.stereo = stereo
        
        self._debug_2("No. of samples = " + str(len(self.envelopes[voice_index])))
        self._debug_2("Tone shape = " + str(tone.shape))
        self._debug_2("Envelope shape = " + str(self.envelopes[voice_index].shape))       

        if (len(self.envelopes[voice_index]) > len(tone)):
            self._debug_1("Error: Tone is shorter than envelope in apply_envelope.")
            return None
        else:
            # Truncate input tone to match length of the envelope.
            tone = tone[:len(self.envelopes[voice_index])]
            # Multiply each tone sample by the matching envelope sample.
            note = np.multiply(tone, self.envelopes[voice_index])
            
        # Duplicate note to make left and right channels if required.
        if stereo == True:
            note = np.column_stack((note, note))
        return note
    
        
    def change_envelope(self, voice_index, voice):
        self._debug_2("In change_envelope() ")
        self.attack = voice.attack
        self.decay = voice.decay
        self.sustain_time = voice.sustain_time
        self.sustain_level = voice.sustain_level / 100
        self.release = voice.release
        self.duration = voice.attack + voice.decay + voice.sustain_time + voice.release
        self._debug_2("Envelope duration, ms = " + str(self.duration))
        new_envelope_length = int(self.sample_rate * self.duration/1000)
        self._debug_2("Envelope length, samples = " + str(new_envelope_length))
        new_envelope = np.zeros(int(new_envelope_length), dtype=float)
        # Generate array with duration*sample_rate steps, ranging between 0 and duration (milli-seconds)
        times_msec = np.linspace(0, self.duration, int(new_envelope_length), False)
        self._debug_2("No. of samples = " + str(len(times_msec)))
            
        attack_level_change = 1.6 * times_msec[1] / self.attack  
        decay_level_change = 1.6 * times_msec[1] / self.decay 
        release_level_change = 1.6 * times_msec[1] / self.release
        self._debug_2("Attack level change = " + str(attack_level_change))
        self._debug_2("Decay level change = " + str(decay_level_change))
        self._debug_2("Release level change = " + str( release_level_change))
        self._debug_2("Time step, milliseconds = " + str(times_msec[1]))
                
        level = 0.0
        for i in range(len(times_msec)):
            if times_msec[i] <= self.attack:
                level += attack_level_change * (1.24 - level)
                # print(str(i) + " Attack")
            elif times_msec[i] <= self.attack + self.decay:
                #print(str(i) + " Decay")
                level -= decay_level_change * (level + 0.1 - self.sustain_level)
                if level < self.sustain_level:
                    level = self.sustain_level
            elif times_msec[i] < self.attack + self.decay + self.sustain_time:
                #print(str(i) + " Sustain")
                level = self.sustain_level
            elif times_msec[i] < self.attack + self.decay + self.sustain_time + self.release:
                #print(str(i) + " Release")
                if level > 0:
                    level -= release_level_change * (level + 0.1)
            else:
                level = 0              
            new_envelope[i] = level
            
        # Replace old envelope with new one
        if len(self.envelopes) <= voice_index:
            self._debug_1("WARNING: list of envelopes length = " + str(len(self.envelopes)))
        else:
            self.envelopes.pop(voice_index)
        # Apply an exponential function to the envelope stored in the model.
        self.envelopes.insert(voice_index, np.exp2(new_envelope) - 1)
        return new_envelope
    
    
    def make_voice(self, voice_index, waveform, width=100):
        self._debug_2("In make_voice() ")
        if voice_index >= MAX_VOICES:
            self._debug_1("ERROR: invalid voice number in make_voice() = " + str(voice_index))
            return
        for semitone in range(NUM_KEYS):
            frequency = int((LOWEST_TONE * np.power(2, semitone/12)) + 0.5)
            if waveform == "Sine":
                self.voices[voice_index, semitone] = self._sine_wave(frequency)
            elif waveform == "Triangle":
                self.voices[voice_index, semitone] = self._triangle_wave(frequency)
            elif waveform == "Sawtooth":
                self.voices[voice_index, semitone] = self._pwm_sawtooth_wave(frequency, width)
            elif waveform == "Square":
                self.voices[voice_index, semitone] = self._pwm_square_wave(frequency, width)
            else:
                self._debug_1("ERROR: invalid waveform in make_voice() = " + str(waveform))
                
    def fetch_tone(self, voice_index, semitone):
        self._debug_2("In fetch_tone()")
        if voice_index >= MAX_VOICES:
            self._debug_1("ERROR: invalid voice number in fetch_tone() = " + str(voice_index))
            return None
        if semitone >= NUM_KEYS:
            self._debug_1("ERROR: invalid semitone number in fetch_tone() = " + str(semitone))
            return None
        tone = self.voices[voice_index, semitone]
        return tone        
                
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print("synth_model.py: " + message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print("synth_model.py: " + message)

#------------------------- Module Test Funcctions -------------------------
if __name__ == "__main__":
    
    import time
    
    SAMPLE_RATE = 44100 # Hz
    FREQUENCY = 220    # Hz
    WIDTH = 50
    DURATION = 1000
    STEREO = True
    ATTACK = 200
    DECAY = 200
    SUSTAIN_TIME = 500
    SUSTAIN_LEVEL = 50
    RELEASE = 100
    
    MAX_VOICES = 12
    NUM_OCTAVES = 3
    NUM_KEYS = (12 * NUM_OCTAVES) + 1
    LOWEST_TONE = 110
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
            self.vibrato_rate = 0
            self.vibrato_depth = 0
            self.tremelo_rate = 0
            self.tremelo_depth = 0
            self.attack = DEFAULT_ATTACK
            self.decay = DEFAULT_DECAY
            self.sustain_time = DEFAULT_SUSTAIN
            self.sustain_level = DEFAULT_SUSTAIN_LEVEL
            self.release = DEFAULT_RELEASE
        
    debug_level = 2
    
    model = Model(SAMPLE_RATE, FREQUENCY, WIDTH, DURATION, STEREO, ATTACK, DECAY, SUSTAIN_TIME, SUSTAIN_LEVEL, RELEASE)
    
    voice_params = Voice_Parameters()
    
    model._debug_1("Calculating test waveforms: sine_tone, triangle_tone, sawtooth_tone, square_tone.")
 
    # Generate mono waveforms
    
    start = time.perf_counter()
    
    model.duration = DURATION
    width = 50
    sine_tone = model._sine_wave(FREQUENCY)
    triangle_tone = model._triangle_wave(FREQUENCY)
    sawtooth_tone = model._pwm_sawtooth_wave(FREQUENCY, width)
    square_tone = model._pwm_square_wave(FREQUENCY, width)
    
    finish = time.perf_counter()
    model._debug_1("No of samples / tone = " +str(len(sine_tone)))
    model._debug_1("Calculation of 4 tones in seconds = " + str(finish - start))
    
    model._debug_1("\nCalculating envelope waveform.")
    
    start = time.perf_counter()
    
    env = model.change_envelope(0, voice_params)
        
    finish = time.perf_counter()
    
    model._debug_1("Envelope calculation in seconds = " + str(finish - start))
           
    model._debug_1("\nDoing mono amplitude modulation")
    
    start = time.perf_counter()
    
    sine_note_1 = model.apply_envelope(0, sine_tone, False)
    
    model._debug_1("\nDoing stereo amplitude modulation")
    
    sine_note_2 = model.apply_envelope(0, sine_tone)    
    
    finish = time.perf_counter()
    
    model._debug_1("Modulation in mono and stereo in seconds = " + str(finish - start))
    
    model._debug_1("\nDoing make_voice()")
    
    start = time.perf_counter()    
    model.make_voice(0, "Sine")
    finish = time.perf_counter()
    
    model._debug_1("Make 1 voice in seconds = " + str(finish - start))