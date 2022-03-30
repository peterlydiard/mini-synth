
import math
import string
import numpy as np
import synth_constants as const

######################### Global variables #########################

# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 2

####################################################################

class Model:
    def __init__(self, controller, sample_rate, max_duration=const.MAX_ENVELOPE_TIME,
                 duration=const.MAX_ENVELOPE_TIME, stereo=const.STEREO):
        self.controller = controller
        self.sample_rate = sample_rate     # Hz (also in Controller class)
        self.max_duration = max_duration   # milliseconds
        self.duration = duration           # milliseconds
        self.stereo = stereo               # Boolean
        self.envelopes = [] 
        self.voices = np.zeros((const.MAX_VOICES, const.NUM_KEYS, (int(sample_rate * const.MAX_ENVELOPE_TIME / 1000))), dtype=float)


    def main(self, max_voices=const.MAX_VOICES):
        for voice_index in range(const.MAX_VOICES):
            self.make_voice(voice_index)
            envelope = self.make_envelope(voice_index)
            self.envelopes.append(envelope)
        pass
        
    # Create a unit-amplitude sine wave with vibrato.
    def _sine_wave(self, frequency):
        self._debug_2("Sine wave freq, max duration (ms) = " + str(frequency) + ", " + str(self.max_duration))
        # Generate array with duration*sample_rate steps, ranging between 0 and duration
        times_sec = np.linspace(0, self.max_duration / 1000, int(self.sample_rate * self.max_duration / 1000), False)
        self._debug_2("No. of samples = " + str(len(times_sec)))
        # Generate a sine wave for the vibrato signal
        time_step = times_sec[1]
        vibrato_rate = self.controller.voices[self.controller.voice_index].vibrato_rate
        vibrato_depth = self.controller.voices[self.controller.voice_index].vibrato_depth
        vibrato_radians_per_sec = 2 * np.pi * vibrato_rate * frequency / 500
        vibrato_tone = vibrato_depth * time_step * np.sin(vibrato_radians_per_sec * times_sec)
        
        times_with_vibrato = times_sec + vibrato_tone
        
        # Generate a sine wave
        radians_per_sec = 2 * np.pi * frequency
        tone = np.sin(radians_per_sec * times_with_vibrato)
        return tone


    # Create a unit-amplitude triangle wave with vibrato and harmonic boost.
    def _triangle_wave(self, frequency):
        self._debug_2("Triangle wave freq, max duration (ms) = " + str(frequency) + ", " + str(self.max_duration))
        # Generate array with duration*sample_rate steps, ranging between 0 and duration (converted to seconds)
        times_sec = np.linspace(0, self.max_duration / 1000, int(self.sample_rate * self.max_duration / 1000), False)
        # Generate linear ramp with duration*sample_rate steps, ranging between 0 and 2*frequency*duration
        ramp = 2 * frequency * times_sec # e.g. from 0 to 2 * 110 * 0.1 for 110Hz over 0.1 seconds 
        # Generate a sine wave for the vibrato signal
        vibrato_rate = self.controller.voices[self.controller.voice_index].vibrato_rate
        vibrato_depth = self.controller.voices[self.controller.voice_index].vibrato_depth / 200
        time_step = times_sec[1]
        self._debug_2("time_step = " + str(time_step))
        vibrato_radians_per_sec = 2 * np.pi * vibrato_rate * frequency / 500
        vibrato_tone = vibrato_depth * 2 * np.sin(vibrato_radians_per_sec * times_sec)
        self._debug_2("Vibrato tone (min, max) = (" + str(min(vibrato_tone)) + ", " + str(max(vibrato_tone)) + ")") 
        # Generate a triangle wave
        ramp_with_vibrato = ramp + vibrato_tone
        tone = abs(((2 * ramp_with_vibrato + 3 ) % 4.0) - 2) - 1       
        return tone
    
    # Create a unit-amplitude sawtooth wave with pulse width control, vibrato and harmonic boost.
    def _pwm_sawtooth_wave(self, frequency, width):
        self._debug_2("Sawtooth wave: freq, width = " + str(frequency) + ", " + str(width))
        width = float(width)
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * self.max_duration/1000) + 2 - width/100,
                           int(self.sample_rate * self.max_duration / 1000), False)
        
        # Generate a sine wave for the vibrato signal
        vibrato_rate = self.controller.voices[self.controller.voice_index].vibrato_rate
        vibrato_depth = self.controller.voices[self.controller.voice_index].vibrato_depth
        vibrato_radians_per_msec = 2 * np.pi * vibrato_rate / 1000
        time_step = ramp[1]
        vibrato_tone = vibrato_depth * time_step * np.sin(vibrato_radians_per_msec * ramp) / 100
        
        # Generate a sawtooth wave
        tone = np.clip((100/width) * (((ramp + vibrato_tone) % 2.0) + width/100 - 2.0), -1.0, 1.0)
        return tone
    
    
    # Create a unit-amplitude square wave with pulse width control, vibrato and harmonic boost.
    def _pwm_square_wave(self, frequency, width):
        self._debug_2("Square wave: freq, width = " + str(frequency) + ", " + str(width))
        width = float(width)
        # Generate linear ramp with total of duration*sample_rate steps.
        ramp = np.linspace(2.0 - width/100, (2 * frequency * self.max_duration / 1000) + 2 - width/100,
                           int(self.sample_rate * self.max_duration / 1000), False)

        # Generate a sine wave for the vibrato signal
        vibrato_rate = self.controller.voices[self.controller.voice_index].vibrato_rate
        vibrato_depth = self.controller.voices[self.controller.voice_index].vibrato_depth
        vibrato_radians_per_msec = 2 * np.pi * vibrato_rate / 1000
        time_step = ramp[1]
        vibrato_tone = vibrato_depth * time_step * np.sin(vibrato_radians_per_msec * ramp) / 100
        
        # Generate a square wave, clip sine to avoid using scipy library.
        tone = np.clip(1000 * (((ramp + vibrato_tone) % 2.0) + (width/100) - 2.0), -1.0, 1.0)
        return tone
    
    # Suppress the fundamental frequency and amplify the result to boost the harmonics.
    def suppress_fundamental(self, tone, frequency):
        harmonic_boost = self.controller.voices[self.controller.voice_index].harmonic_boost 
        # Make a frequency control waveform
        freq_control = frequency * np.ones(len(tone), dtype=float)
        filter_q_factor = 2 # Magic number
        filtered_tone = self.bandpass_filter(tone, freq_control, filter_q_factor)
        # Compensate for settling time of filter, by merging more stable cycles with the early samples.
        two_cycles = int(2 * self.sample_rate / frequency)
        one_over_two_cycles = 1 / two_cycles # do division outside loop, to cut processor load.
        for i in range(two_cycles):
            filtered_tone[i] = (((two_cycles-i) * filtered_tone[i+two_cycles]) + (i * filtered_tone[i])) * one_over_two_cycles
        boost_ratio = harmonic_boost / 100
        tone = tone - (boost_ratio * filtered_tone)
        boost_factor = 1 / max(tone)
        tone = tone * boost_factor
        return tone
            
    # Bandpass Filter.
    # tone = input waveform to be filtered, freq_control = control signal to set filter centre frequency. 
    # q_factor = ratio of filter centre frequency divided by 3dB bandwidth (approximately).
    def bandpass_filter(self, tone, freq_control, q_factor):
        
        # Bandpass and bandstop (notch) biquadratic filters.
        band_pass = np.zeros(len(tone))
        #notch = np.zeros(len(tone))
        x0 = x1 = x2 = x3 = x4 = 0
        for i in range(len(tone)):
            # Recalculate filter coefficients, every 1.45 milliseconds.
            if i % 64 == 0:
                fc = freq_control[i]
                R = 1 - (np.pi * fc / (q_factor * self.sample_rate))
                b2 = - R
                a1 = - 2 * R * np.cos(2 * np.pi * fc / self.sample_rate)
                a2 = R * R            
                rescale = 1 - R
            
            # Calculate biquad filter.
            x0 = tone[i] - (a1 * x1) - (a2 * x2)
            band_pass[i] = rescale * (x0 + (b2 * x2))
            #notch[i] = tone[i] - band_pass[i]
            x2 = x1
            x1 = x0
        
        return band_pass
    
    # Apply the envelope amplitude to the tone to make a note
    def apply_envelope(self, voice_index, tone, stereo=True):
        self._debug_2("In apply_envelope() ")
        if tone is None:
            self._debug_1("ERROR: tone is None in apply_envelope().")
            return None
        if voice_index < 0 or voice_index > const.MAX_VOICES:
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
    
        
    def make_envelope(self, voice_index):
        self._debug_2("In make_envelope() ")
        voice = self.controller.voices[voice_index]
        attack = voice.attack
        decay = voice.decay
        sustain_time = voice.sustain_time
        sustain_level = voice.sustain_level / 100
        release = voice.release
        self.duration = voice.attack + voice.decay + voice.sustain_time + voice.release
        self._debug_2("Envelope duration, ms = " + str(self.duration))
        new_envelope_length = int(self.sample_rate * self.duration/1000)
        self._debug_2("Envelope length, samples = " + str(new_envelope_length))
        new_envelope = np.zeros(int(new_envelope_length), dtype=float)
        # Generate array with duration*sample_rate steps, ranging between 0 and duration (milli-seconds)
        times_msec = np.linspace(0, self.duration, int(new_envelope_length), False)
        self._debug_2("No. of samples = " + str(len(times_msec)))
            
        attack_level_change = 1.6 * times_msec[1] / attack  
        decay_level_change = 1.6 * times_msec[1] / decay 
        release_level_change = 1.6 * times_msec[1] / release
        self._debug_2("Attack level change = " + str(attack_level_change))
        self._debug_2("Decay level change = " + str(decay_level_change))
        self._debug_2("Release level change = " + str(release_level_change))
        self._debug_2("Time step, milliseconds = " + str(times_msec[1]))
                
        # Generate a tremolo sine wave
        radians_per_msec = 2 * np.pi * voice.tremolo_rate / 1000
        tremolo = (voice.tremolo_depth / 100) * np.sin(radians_per_msec * times_msec)
        
        level = 0.0
        for i in range(len(times_msec)):
            if times_msec[i] <= attack:
                level += attack_level_change * (1.24 - level)
                # print(str(i) + " Attack")
            elif times_msec[i] <= attack + decay:
                #print(str(i) + " Decay")
                level -= decay_level_change * (level + 0.1 - sustain_level)
                if level < sustain_level:
                    level = sustain_level
            elif times_msec[i] < attack + decay + sustain_time:
                #print(str(i) + " Sustain")
                level = sustain_level
            elif times_msec[i] < attack + decay + sustain_time + release:
                #print(str(i) + " Release")
                if level > 0:
                    level -= release_level_change * (level + 0.1)
            else:
                level = 0              
            new_envelope[i] = max(0, level + tremolo[i])
            
        # Replace old envelope with new one
        if len(self.envelopes) <= voice_index:
            self._debug_1("WARNING: list of envelopes length = " + str(len(self.envelopes)))
        else:
            self.envelopes.pop(voice_index)
        # Apply an exponential function to the envelope stored in the model.
        self.envelopes.insert(voice_index, np.exp2(new_envelope) - 1)
        return new_envelope
    
    # Mark all the tones for this voice as obsolete. Obsolete tones should be remade before being played.
    def scratch_voice(self, voice_index):
        self._debug_2("In scratch_voice() ")
        if voice_index >= const.MAX_VOICES:
            self._debug_1("ERROR: invalid voice number in scratch_voice() = " + str(voice_index))
            return
        for semitone in range(const.NUM_KEYS):
            self.voices[voice_index, semitone, 0] = -5 # Set first sample to an invalid value
        
    def make_voice(self, voice_index):
        self._debug_1("In make_voice() - making voice:  " + str(voice_index))
        if voice_index >= const.MAX_VOICES:
            self._debug_1("ERROR: invalid voice number in make_voice() = " + str(voice_index))
            return
        for semitone in range(const.NUM_KEYS):
            self.make_tone(voice_index, semitone)         
            
    def make_tone(self, voice_index, semitone):
        self._debug_2("In make_tone() ")
        if voice_index >= const.MAX_VOICES:
            self._debug_1("ERROR: invalid voice number in make_tone() = " + str(voice_index))
            return
        if semitone >= const.NUM_KEYS:
            self._debug_1("ERROR: invalid semitone in make_tone() = " + str(semitone))
            return
        frequency = int((const.LOWEST_TONE * np.power(2, semitone/12)) + 0.5)
        waveform = self.controller.voices[voice_index].waveform
        width = self.controller.voices[voice_index].width
        if waveform == "Sine":
            tone = self._sine_wave(frequency)
        elif waveform == "Triangle":
            tone = self._triangle_wave(frequency)
        elif waveform == "Sawtooth":
            tone = self._pwm_sawtooth_wave(frequency, width)
        elif waveform == "Square":
            tone = self._pwm_square_wave(frequency, width)
        else:
            self._debug_1("ERROR: invalid waveform in make_tone() = " + str(waveform))
        # If boosting harmonics, suppress the tone fundamental frequency.
        harmonic_boost = self.controller.voices[self.controller.voice_index].harmonic_boost 
        if waveform != "Sine" and harmonic_boost > 0:
            self.voices[voice_index, semitone] = self.suppress_fundamental(tone, frequency)
        else:
            self.voices[voice_index, semitone] = tone
            
    def fetch_tone(self, voice_index, semitone):
        self._debug_2("In fetch_tone()")
        if voice_index >= const.MAX_VOICES:
            self._debug_1("ERROR: invalid voice number in fetch_tone() = " + str(voice_index))
            return None
        if semitone >= const.NUM_KEYS:
            self._debug_1("ERROR: invalid semitone number in fetch_tone() = " + str(semitone))
            return None
        tone = self.voices[voice_index, semitone]
        # Check if tone needs to be regenerated
        if tone[0] < -2:
            self.make_tone(voice_index, semitone)
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
    DEFAULT_WIDTH = 100
    DURATION = 1000
    STEREO = True
    
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
            self.width = DEFAULT_WIDTH
            self.harmonic_boost = 0
            self.vibrato_rate = 0
            self.vibrato_depth = 0
            self.tremolo_rate = 0
            self.tremolo_depth = 0
            self.attack = DEFAULT_ATTACK
            self.decay = DEFAULT_DECAY
            self.sustain_time = DEFAULT_SUSTAIN
            self.sustain_level = DEFAULT_SUSTAIN_LEVEL
            self.release = DEFAULT_RELEASE
        
    class TestController:
        def __init__(self):
            self.sample_rate = SAMPLE_RATE
            self.frequency = DEFAULT_FREQUENCY
            self.num_voices = 1
            self.voices = []
            self.voice_index = 0
            self.model = Model(self, SAMPLE_RATE)
        
        def main(self):
            self.model._debug_2("In main of test controller")
            for voice_index in range(MAX_VOICES):
                voice_params = Voice_Parameters()
                self.voices.append(voice_params)
            self.model.main()

          
    debug_level = 2       
    tc = TestController()
    tc.main()
      
    model = Model(tc, SAMPLE_RATE)
    
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
    
    env = model.make_envelope(0)
        
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
    model.make_voice(0)
    finish = time.perf_counter()
    
    model._debug_1("Make 1 voice in seconds = " + str(finish - start))
    
#---------------------------- References and Acknowledgements --------------------------------
#
# The Fourier Series by Erik Cheever of Swathmore College. https://lpsa.swarthmore.edu/Fourier/Series/WhyFS.html
