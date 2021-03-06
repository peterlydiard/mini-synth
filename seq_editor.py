# ------------------------------
# Imports
# ------------------------------
import guizero

import synth_constants as const

# ------------------------------
# Module globals
# ------------------------------

NUM_VISIBLE_TIMESLOTS = 60
MAX_WINDOW_HEIGHT = 800
WAFFLE_PIXEL_DIM = int((MAX_WINDOW_HEIGHT - 80) // const.NUM_KEYS)
WINDOW_WIDTH = max(800, int((NUM_VISIBLE_TIMESLOTS + 7) * WAFFLE_PIXEL_DIM))
WINDOW_HEIGHT = (const.NUM_KEYS * WAFFLE_PIXEL_DIM) + 80
debug_level = 2

# ------------------------------
# Module class
# ------------------------------

class Seq_Editor:
    def __init__(self, view):
        self.view = view
        self.seq_voice_checks = []
        self.seq_offset = 0
        self.old_pixel_colours = []
       

    def main(self):
        self._debug_1("In main()")
        self._sequence_editor_window()
        self.show_sequence()
        
        
    def _sequence_editor_window(self):
        self.window = guizero.Window(self.view.app, "Sequence editor", width = WINDOW_WIDTH, height = WINDOW_HEIGHT)
        self.sequence_window_open = True
        self.window.when_closed = self._closed_sequence_editor
        
        self.seq_box = guizero.Box(self.window, layout="grid")
       
        self.board = guizero.Waffle(self.seq_box, grid=[0,0], align="bottom", width=NUM_VISIBLE_TIMESLOTS+3, height=const.NUM_KEYS,
                                    pad=0, dim=WAFFLE_PIXEL_DIM, command=self._handle_toggle_seq_note)

        self._draw_seq_keyboard(const.NUM_OCTAVES)
        
        self.seq_controls = guizero.Box(self.seq_box, grid=[0,1], layout="grid")
        voice_name_list = []
        for i in range(self.view.controller.num_voices):
            voice_name = "Voice " + str(i+1)
            voice_name_list.append(voice_name)
        self.seq_voice_combo = guizero.Combo(self.seq_controls, grid=[0,0], options=voice_name_list,
                                     height="fill", command=self._handle_select_seq_voice)
        self.seq_voice_text = guizero.Text(self.seq_controls, grid=[1,0], text="    ",
                                           bg=self.view.controller.voice_params[self.view.controller.voice_index].colour)
        self.seq_beats_combo = guizero.Combo(self.seq_controls, grid=[2,0], options=["3 beats/bar", "4 beats/bar", "5 beats/bar"],
                                     height="fill", command=self._handle_set_seq_beats)
        guizero.Text(self.seq_controls, grid=[3,0], text="    ")
        self.seq_tempo_label = guizero.Text(self.seq_controls, grid=[4,0], text="Tempo, bpm")
        self.seq_tempo_slider = guizero.Slider(self.seq_controls, grid=[5,0], start=30, end=200, width=342, command=self._handle_set_tempo)
        self.seq_play_button = guizero.PushButton(self.seq_controls, grid=[6,0], text="Play", command=self._handle_play_sequence)
        guizero.Text(self.seq_controls, grid=[7,0], text="    ")
        self.seq_scroll_label = guizero.Text(self.seq_controls, grid=[8,0], text="Scroll")
        self.seq_scroll_slider = guizero.Slider(self.seq_controls, grid=[9,0], start=0, end=const.MAX_TIMESLOTS - NUM_VISIBLE_TIMESLOTS,
                                                width=303, command=self._handle_scroll)
        
        self.seq_select_box = guizero.Box(self.seq_box, grid=[0,2], layout="grid")
        for i in range(self.view.controller.num_voices):
            voice_name = "Voice " + str(i+1)
            self.seq_voice_checks.append(guizero.CheckBox(self.seq_select_box, grid=[i,1], text=voice_name, command=self._handle_update_board))
            self.seq_voice_checks[i].text_color = self.view.controller.voice_params[i].colour
            self.seq_voice_checks[i].value = 1
            
       
    def _draw_seq_keyboard(self, num_octaves=const.NUM_OCTAVES):
        self._debug_2("In _draw_seq_keyboard()")              
        for i in range(12 * const.NUM_OCTAVES + 1):
            if (i % 12) in [1,3,6,8,10]:
                self.board.set_pixel(0, 12 * const.NUM_OCTAVES - i, "black")
                self.board.set_pixel(1, 12 * const.NUM_OCTAVES - i, "black")
                self.board.set_pixel(2, 12 * const.NUM_OCTAVES - i, "black")
                
    def _draw_seq_octaves(self):
        self._debug_2("In _draw_seq_octaves()")
        for i in range(const.NUM_OCTAVES + 1):
            key = 12 * i
            for timeslot in range(NUM_VISIBLE_TIMESLOTS + 3):
                self.board.set_pixel(timeslot, const.NUM_KEYS - 1 - key, (230,230,230))
        
    def _draw_seq_bars(self):
        self._debug_2("In _draw_seq_bars()")
        for timeslot in range(NUM_VISIBLE_TIMESLOTS):
            if (timeslot % self.view.controller.sequence.beats_per_bar == 0):
                for key in range(12 * const.NUM_OCTAVES + 1):
                    self.board.set_pixel(timeslot+3, const.NUM_KEYS - 1 - key, (230,230,230))

    def _draw_seq_notes(self):
        self._debug_2("In _draw_seq_notes()")
        for vi in range(self.view.controller.num_voices):
            if self.seq_voice_checks[vi].value == 1:
                for column in range(NUM_VISIBLE_TIMESLOTS):
                    for key in range(12 * const.NUM_OCTAVES + 1):
                        if (
                            column + self.seq_offset < self.view.controller.num_timeslots
                            and self.view.controller.sequence.notes[vi, column + self.seq_offset, key] > 0
                        ):
                            colour = self.view.controller.voice_params[vi].colour
                            self.board.set_pixel(column+3, const.NUM_KEYS - 1 - key, colour)

    def show_sequence(self):
        self._debug_2("In show_sequence()")
        try:
            voice_name = "Voice " + str(self.view.controller.voice_index + 1)
            self.view.update_combo(self.seq_voice_combo, voice_name)
            self.seq_voice_text.bg = self.view.controller.voice_params[self.view.controller.voice_index].colour
            self.seq_tempo_slider.value = self.view.controller.sequence.tempo
            beats_name = str(self.view.controller.sequence.beats_per_bar) + " beats/bar"
            self.view.update_combo(self.seq_beats_combo, beats_name)
            self._handle_update_board()
        except:
            self._debug_1("Fatal ERROR in show_sequence().")
            
    # Draw moving grey pixels on the board to show the current timeslot being played.
    def show_cursor(self, timeslot):
        self._debug_2("In show_cursor: timeslot = " + str(timeslot)) 
        cursor_x = max(0, timeslot - self.seq_offset)
        if cursor_x > 1 and len(self.old_pixel_colours) == 2:
            # restore original pixel colours
            self.board.set_pixel(cursor_x+2, 0, self.old_pixel_colours[0])
            self.board.set_pixel(cursor_x+2, const.NUM_KEYS-1, self.old_pixel_colours[1])
        # remember pixel colours, then draw grey ones
        if cursor_x + 3 < self.board.width:
            self.old_pixel_colours = []
            self.old_pixel_colours.append(self.board.get_pixel(cursor_x+3, 0))
            self.board.set_pixel(cursor_x+3, 0, (64,64,64))
            self.old_pixel_colours.append(self.board.get_pixel(cursor_x+3, const.NUM_KEYS-1))
            self.board.set_pixel(cursor_x+3, const.NUM_KEYS-1, (64,64,64))

    def _closed_sequence_editor(self):
        self._debug_1("Sequence editor closed")
        self.view.on_request_seq_editor_closed()
        self.window.destroy()
        

    def _handle_select_seq_voice(self, value):
        self._debug_2("In _handle_set_seq_voice: " + str(value))
        # pass on the number part of the string value
        vi = int(value[6:]) - 1
        self.view.controller.on_request_select_voice(vi)
        if self.view.voice_window_open == False:
            self.view.controller.on_request_note(15) # Illustrate new voice
        self.seq_voice_checks[vi].value = 1
        self._draw_seq_notes()


    def _handle_set_seq_beats(self, value):
        self._debug_2("In _handle_set_beats()")
        self.view.controller.on_request_set_beats(value[:1])
        self._handle_update_board()
        
        
    def _handle_set_tempo(self, value):
        self._debug_2("In _handle_set_tempo()")
        self.view.controller.on_request_set_tempo(value)
        
        
    def _handle_play_sequence(self):
        self._debug_2("In _handle_play_sequence()")
        self.view.controller.on_request_play_sequence()

    def _handle_scroll(self, value):
        self._debug_2("In _handle_scroll()")
        self.seq_offset = int(value)
        self._handle_update_board()
        self.view.controller.on_request_set_seq_offset(value)
        
    def _handle_toggle_seq_note(self, x, y):
        self._debug_2("In _handle_set_seq_note: " +  str(x) + ", " + str(y))
        key = (12 * const.NUM_OCTAVES) - y
        if key >= 0:
            self.view.controller.on_request_note(key)
            if x > 2:
                timeslot = x - 3
                vi = self.view.controller.voice_index
                if self.view.controller.sequence.notes[vi, timeslot + self.seq_offset, key] > 0:
                    colour = "white"
                else:
                    colour = self.view.controller.voice_params[vi].colour
                self.board.set_pixel(timeslot+3, const.NUM_KEYS - 1 - key, colour)
                self.view.controller.on_request_toggle_sequence_note(timeslot + self.seq_offset, vi, key)
        else:
            self._debug_2("Not a key")
    
    def _handle_update_board(self):
        self._debug_2("In _handle_update_board: ")
        self.board.set_all("white")
        self._draw_seq_bars()
        self._draw_seq_octaves()
        self._draw_seq_keyboard()
        self._draw_seq_notes()
        
    def _debug_1(self, message):
        global debug_level
        if debug_level >= 1:
            print("seq_editor.py: " + message)
    
    
    def _debug_2(self, message):
        global debug_level
        if debug_level >= 2:
            print("seq_editor.py: " + message)
            
