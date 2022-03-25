# ------------------------------
# Imports
# ------------------------------
import guizero

import synth_constants as const

# ------------------------------
# Module globals
# ------------------------------
debug_level = 1

# ------------------------------
# Module class
# ------------------------------

class Seq_Editor:
    def __init__(self, view):
        self.view = view
       

    def main(self):
        self._debug_1("In main()")
        self.sequence_editor_window()
        self.show_new_settings()
        
        
    def sequence_editor_window(self):
        self.window = guizero.Window(self.view.app, "Sequence editor", width = 1200, height = 750)
        self.sequence_window_open = True
        self.window.when_closed = self._closed_sequence_editor
        
        self.seq_box = guizero.Box(self.window, layout="grid")
       
        self.board = guizero.Waffle(self.seq_box, grid=[0,0], align="bottom", width=63, height=37, pad=0, dim=18, command=self._handle_set_seq_note)

        self.draw_seq_keyboard(const.NUM_OCTAVES)
        
        self.seq_voice_combo = guizero.Combo(self.seq_box, grid=[0,1], options=["Voice 1", "Voice 2", "Voice 3", "Voice 4"],
                                     height="fill", command=self._handle_set_seq_voice)
        

    def draw_seq_keyboard(self, num_octaves=const.NUM_OCTAVES):
        self._debug_2("In draw_seq_keyboard()")
              
        for i in range(12 * const.NUM_OCTAVES + 1):
            if (i % 12) in [1,3,6,8,10]:
                self.board.set_pixel(0, 12 * const.NUM_OCTAVES - i, "black")
                self.board.set_pixel(1, 12 * const.NUM_OCTAVES - i, "black")
                self.board.set_pixel(2, 12 * const.NUM_OCTAVES - i, "black")


    def show_new_settings(self):
        self._debug_2("In show_new_setings()")
        voice_name = "Voice " + str(self.view.controller.voice_index + 1)
        self.view.update_combo(self.seq_voice_combo, voice_name)         


    def _closed_sequence_editor(self):
        self._debug_1("Sequence editor closed")
        self.view.on_request_voice_editor_closed()
        self.window.destroy()
        

    def _handle_set_seq_voice(self, value):
        self._debug_2("In _handle_set_seq_voice: " + str(value))
        # pass on the number part of the string value
        self.view.controller.on_request_voice(int(value[6:]) - 1)
    
    
    def _handle_set_seq_note(self, x, y):
        self._debug_2("In _handle_set_seq_note: " +  str(x) + ", " + str(y))
        semitone = (12 * const.NUM_OCTAVES) - y
        if semitone >= 0:
            self.view.controller.on_request_note(semitone)
            if x > 2:
                timeslot = x - 3
                vi = self.view.controller.voice_index
                old_colour = self.board.get_pixel(x, y)
                self._debug_2("Old pixel colour = " + str(old_colour))
                self.board.set_pixel(x, y, self.view.controller.voices[vi].colour)
                self.view.controller.on_request_add_sequence_note(timeslot, vi, semitone)
        else:
            self._debug_2("Not a key")
    
    
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print("seq_editor.py: " + message)
    
    
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print("seq_editor.py: " + message)
            
