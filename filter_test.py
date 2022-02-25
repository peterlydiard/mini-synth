#import FFT
import math
#import string
#import copy
import numpy as np
import pygame

from guizero import App, Window, Drawing, Box, PushButton


######################### Global variables #########################

FREQUENCY = 110    # Hz
WIDTH = 50
MAX_DURATION = 500
STEREO = True
ATTACK = 200
DECAY = 200
SUSTAIN_TIME = 500
SUSTAIN_LEVEL = 50
RELEASE = 100
# Debug levels: 0 = none, 1 = basic, 2 = long-winded.
debug_level = 1

####################################################################

class View:
    def __init__(self, controller):
        self.controller = controller
        self.sound = None
        self.previous_key = 0

    def main(self):
        self._debug_1("In view.main()")
        
        # initialise stereo mixer (default)
        pygame.mixer.init()
        pygame.init()

        self.app = App("Mini-synth", width = 940)
        
        self.panel_0 = Box(self.app, layout="grid")

        self.scope = Drawing(self.panel_0, grid=[1,0], width=500, height=220)
        
        self.panel_1 = Box(self.app, layout="grid", border=10)
        self.panel_1.set_border(thickness=10, color=self.app.bg)


        self.play_button = PushButton(self.panel_1, grid=[1,0], text="Test", command=self._handle_request_test)
        
        # set up exit function
        self.app.when_closed = self.handle_close_app
        
        # enter endless loop, waiting for user input.
        self.app.display()

    def show_graph(self, graph):
        self._debug_2("New graph available")
        self.scope.clear()
        self.scope.bg = "dark gray"
            
        # Plot signal to display
        origin_x = 0
        origin_y = self.scope.height / 2
        previous_x = origin_x
        previous_y = origin_y        
        num_points = len(graph)
        sub_sampling_factor = int(self.controller.sample_rate * 5 / self.scope.width)
        scale_x = (self.scope.width - 5) * sub_sampling_factor / num_points
        scale_y = (self.scope.height - 5) / 2
        self._debug_2("scale_y = " + str(scale_y))
        for i in range(num_points // sub_sampling_factor):
            #self._debug_2(envelope[int(i * sub_sampling_factor)])
            # Note pixel (0,0) is in the top left of the Drawing, so we need to invert the y data.
            plot_y = int(origin_y - (scale_y * graph[int(i * sub_sampling_factor)]))
            plot_x = int(origin_x + (scale_x * i))
            self.scope.line(previous_x, previous_y, plot_x, plot_y, color="light green", width=2)
            previous_x = plot_x
            previous_y = plot_y

    def handle_close_app(self):
        self._debug_1("\nNormal termination")
        pygame.mixer.music.stop()
        self.app.destroy()
        
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print(message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print(message)        
    
    def handle_set_frequency(self, value):
        self.controller.on_request_frequency(value)
        
    def _handle_request_test(self):
        self.controller.on_request_test()
        
        
class Model:
    def __init__(self, sample_rate, frequency=FREQUENCY, max_duration=MAX_DURATION):
        self.sample_rate = sample_rate     # Hz
        self.frequency = frequency         # Hz
        self.max_duration = max_duration   # milliseconds


    # Create a unit-amplitude sine wave, stereo by default.
    def sine_wave(self, frequency):
        self._debug_2("Sine wave freq, max duration (ms) = " + str(frequency) + ", " + str(self.max_duration))
        self.frequency = frequency
        # Generate array with duration*sample_rate steps, ranging between 0 and duration
        times_msec = np.linspace(0, self.max_duration, int(self.sample_rate * self.max_duration / 1000), False)
        self._debug_2("No. of samples = " + str(len(times_msec)))
        # Generate a sine wave
        radians_per_msec = 2 * np.pi * frequency / 1000
        tone = np.sin(radians_per_msec * times_msec)
        return tone

    
    def voltage_controlled_filters(self, tone, control):
        
        # Truncate raw tone to length of control waveform
        tone = tone[:len(control)]
        
        # Clear integrator stores for HP, BP and LP outputs.
        high_pass = np.zeros(len(tone) + 2)
        band_pass = np.zeros(len(tone) + 2)
        low_pass = np.zeros(len(tone) + 2)
        notch = np.zeros(len(tone) + 2)
        
        for i in range(len(tone)):
            low_pass[i+1] = low_pass[i] - (0.05 * control[i] * tone[i])
            
        return low_pass[2:]

    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print(message)
        
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print(message)

            
#------------------------- Module Test Funcctions -------------------------
if __name__ == "__main__":

    import time

    SAMPLE_RATE = 44100
    DURATION = 1000
    FERQUENCY = 55
    
    class TestController:
        def __init__(self):
            self.sample_rate = SAMPLE_RATE
            self.waveform = "Sine"
            self.frequency = 55
            self.view = View(self)
            self.model = Model(SAMPLE_RATE)
        
        def main(self):
            self.view._debug_2("In main of test controller")
            self.view.main()
           
        def on_request_frequency(self, frequency):
            self.view._debug_2("Set frequency to " + str(frequency))
                      
        def on_request_test(self):
            self.view._debug_2("Test requested")
                 
            sine_tone = self.model.sine_wave(FREQUENCY)
    
            control = np.ones(len(sine_tone))
            
            output =  self.model.voltage_controlled_filters(sine_tone, control)
            
            for i in range(100):
                print(i, " ", sine_tone[i])
                    
            for i in range(100):
                print(i, " ", output[i])
                
            self.view.show_graph(sine_tone)
                  
        def on_request_save(self):
            self.view._debug_2("Save settings requested")
            
        def on_request_restore(self):
            self.view._debug_2("Restore settings requested")
            

    debug_level = 2
    
    tc = TestController()
    tc.main()

    print("Calculating test waveforms: sine_tone, triangle_tone, sawtooth_tone, square_tone.")
 
    # Generate mono waveforms
    
    start = time.perf_counter()
    
    tc.model.duration = DURATION

    sine_tone = tc.model.sine_wave(FREQUENCY)

    finish = time.perf_counter()
    print("No of samples / tone = " +str(len(sine_tone)))
    print("Calculation of 1 tones in seconds = " + str(finish - start))
    
        

        
        
    

