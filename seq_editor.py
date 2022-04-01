# ------------------------------
# Imports
# ------------------------------
import guizero

import synth_constants as const

# ------------------------------
# Module globals
# ------------------------------
debug_level = 2

# ------------------------------
# Module class
# ------------------------------

class Seq_Editor:
    def __init__(self, view):
        self.view = view
        self.seq_voice_checks = []
       

    def main(self):
        self._debug_1("In main()")
        self.sequence_editor_window()
        self.show_sequence()
        
        
    def sequence_editor_window(self):
        self.window = guizero.Window(self.view.app, "Sequence editor", width = 1200, height = 750)
        self.sequence_window_open = True
        self.window.when_closed = self._closed_sequence_editor
        
        self.seq_box = guizero.Box(self.window, layout="grid")
       
        self.board = guizero.Waffle(self.seq_box, grid=[0,0], align="bottom", width=const.MAX_TIMESLOTS+3, height=const.NUM_KEYS,
                                    pad=0, dim=18, command=self._handle_toggle_seq_note)

        self.draw_seq_keyboard(const.NUM_OCTAVES)
        
        self.seq_controls = guizero.Box(self.seq_box, grid=[0,1], layout="grid")
        voice_name_list = []
        for i in range(self.view.controller.num_voices):
            voice_name = "Voice " + str(i+1)
            voice_name_list.append(voice_name)
        self.seq_voice_combo = guizero.Combo(self.seq_controls, grid=[0,0], options=voice_name_list,
                                     height="fill", command=self._handle_set_seq_voice)
        self.seq_voice_text = guizero.Text(self.seq_controls, grid=[1,0], text="    ",
                                           bg=self.view.controller.voices[self.view.controller.voice_index].colour)
        self.seq_beats_combo = guizero.Combo(self.seq_controls, grid=[2,0], options=["3 beats/bar", "4 beats/bar", "5 beats/bar"],
                                     height="fill", command=self._handle_set_seq_beats)
        guizero.Text(self.seq_controls, grid=[3,0], text="    ")
        self.seq_tempo_label = guizero.Text(self.seq_controls, grid=[4,0], text="Tempo, bpm")
        self.seq_tempo_slider = guizero.Slider(self.seq_controls, grid=[5,0], start=30, end=200, width=342, command=self._handle_set_tempo)
        self.seq_play_button = guizero.PushButton(self.seq_controls, grid=[6,0], text="Play", command=self._handle_play_sequence)
        self.seq_select_box = guizero.Box(self.seq_box, grid=[0,2], layout="grid")
        for i in range(self.view.controller.num_voices):
            voice_name = "Voice " + str(i+1)
            self.seq_voice_checks.append(guizero.CheckBox(self.seq_select_box, grid=[i,1], text=voice_name, command=self._handle_update_board))
            self.seq_voice_checks[i].text_color = self.view.controller.voices[i].colour
            self.seq_voice_checks[i].value = 1
            
       
    def draw_seq_keyboard(self, num_octaves=const.NUM_OCTAVES):
        self._debug_2("In draw_seq_keyboard()")
              
        for i in range(12 * const.NUM_OCTAVES + 1):
            if (i % 12) in [1,3,6,8,10]:
                self.board.set_pixel(0, 12 * const.NUM_OCTAVES - i, "black")
                self.board.set_pixel(1, 12 * const.NUM_OCTAVES - i, "black")
                self.board.set_pixel(2, 12 * const.NUM_OCTAVES - i, "black")
                
    def draw_seq_octaves(self):
        self._debug_2("In draw_seq_octaves()")
        for i in range(const.NUM_OCTAVES + 1):
            key = 12 * i
            for timeslot in range(self.view.controller.num_timeslots + 3):
                self.board.set_pixel(timeslot, const.NUM_KEYS - 1 - key, (230,230,230))
        
    def draw_seq_bars(self):
        self._debug_2("In draw_seq_bars()")
        for timeslot in range(self.view.controller.num_timeslots):
            if (timeslot % self.view.controller.sequence.beats_per_bar == 0):
                for key in range(12 * const.NUM_OCTAVES + 1):
                    self.board.set_pixel(timeslot+3, const.NUM_KEYS - 1 - key, (230,230,230))

    def draw_seq_notes(self):
        self._debug_2("In draw_seq_notes()")
        for vi in range(self.view.controller.num_voices):
            if self.seq_voice_checks[vi].value == 1:
                for timeslot in range(self.view.controller.num_timeslots):
                    for key in range(12 * const.NUM_OCTAVES + 1):
                        if self.view.controller.sequence.notes[vi, timeslot, key] > 0:
                            colour = self.view.controller.voices[vi].colour
                            self.board.set_pixel(timeslot+3, const.NUM_KEYS - 1 - key, colour)

    def show_sequence(self):
        self._debug_2("In show_sequence()")
        voice_name = "Voice " + str(self.view.controller.voice_index + 1)
        self.view.update_combo(self.seq_voice_combo, voice_name)
        self.seq_voice_text.bg = self.view.controller.voices[self.view.controller.voice_index].colour
        self.seq_tempo_slider.value = self.view.controller.sequence.tempo
        beats_name = str(self.view.controller.sequence.beats_per_bar) + " beats/bar"
        self.view.update_combo(self.seq_beats_combo, beats_name)
        self._handle_update_board()


    def _closed_sequence_editor(self):
        self._debug_1("Sequence editor closed")
        self.view.on_request_voice_editor_closed()
        self.window.destroy()
        

    def _handle_set_seq_voice(self, value):
        self._debug_2("In _handle_set_seq_voice: " + str(value))
        # pass on the number part of the string value
        vi = int(value[6:]) - 1
        self.view.controller.on_request_voice(vi)
        if self.view.voice_window_open == False:
            self.view.controller.on_request_note(15) # Illustrate new voice
        self.seq_voice_checks[vi].value = 1
        self.draw_seq_notes()


    def _handle_set_seq_beats(self, value):
        self._debug_2("In _handle_set_beats()")
        self.view.controller.on_request_beats(value[:1])
        self._handle_update_board()
        
        
    def _handle_set_tempo(self, value):
        self._debug_2("In _handle_set_tempo()")
        self.view.controller.on_request_tempo(value)
        
        
    def _handle_play_sequence(self):
        self._debug_2("In _handle_play_sequence()")
        self.view.controller.on_request_play_sequence()

    
    def _handle_toggle_seq_note(self, x, y):
        self._debug_2("In _handle_set_seq_note: " +  str(x) + ", " + str(y))
        semitone = (12 * const.NUM_OCTAVES) - y
        if semitone >= 0:
            self.view.controller.on_request_note(semitone)
            if x > 2:
                timeslot = x - 3
                vi = self.view.controller.voice_index
                if self.view.controller.sequence.notes[vi, timeslot, semitone] > 0:
                    colour = "white"
                else:
                    colour = self.view.controller.voices[vi].colour
                self.board.set_pixel(timeslot+3, const.NUM_KEYS - 1 - semitone, colour)
                self.view.controller.on_request_toggle_sequence_note(timeslot, vi, semitone)
        else:
            self._debug_2("Not a key")
    
    def _handle_update_board(self):
        self._debug_2("In _handle_update_board: ")
        self.board.set_all("white")
        self.draw_seq_bars()
        self.draw_seq_octaves()
        self.draw_seq_keyboard()
        self.draw_seq_notes()
        
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print("seq_editor.py: " + message)
    
    
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print("seq_editor.py: " + message)
            
