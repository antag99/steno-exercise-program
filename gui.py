import functools
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tk_font

from collections import namedtuple
from enum import IntEnum, unique
import time

from learn_plover import *
import json
from random import Random
from collections import defaultdict


@unique
class StenoKeys(IntEnum):
    """
    Enumerates the keys on a stenography keyboard.
    """
    S_L = 0
    T_L = 1
    P_L = 2
    H_L = 3
    K_L = 4
    W_L = 5
    R_L = 6
    A = 7
    O = 8
    STAR = 9
    E = 10
    U = 11
    F_R = 12
    P_R = 13
    L_R = 14
    T_R = 15
    D_R = 16
    R_R = 17
    B_R = 18
    G_R = 19
    S_R = 20
    Z_R = 21

    @property
    def order(self):
        left_half_order = "STKPWHRAO*"
        right_half_order = "EUFRPBLGTSDZ"
        if self.value <= self.STAR:
            return left_half_order.index(self.letter)
        else:
            return len(left_half_order) + right_half_order.index(self.letter)

    @property
    def letter(self):
        return "STPHKWRAO*EUFPLTDRBGSZ"[self.value]

    @property
    def column(self):
        if StenoKeys.S_L <= self.value <= StenoKeys.H_L:
            return self.value
        elif StenoKeys.K_L <= self.value <= StenoKeys.R_L:
            return 1 + self.value - StenoKeys.K_L
        elif StenoKeys.A <= self.value <= StenoKeys.U:
            return self.value - StenoKeys.A + StenoKeys.H_L + 1
        elif StenoKeys.F_R <= self.value <= StenoKeys.D_R:
            return self.value - StenoKeys.F_R + StenoKeys.H_L + 6
        elif StenoKeys.R_R <= self.value <= StenoKeys.Z_R:
            return self.value - StenoKeys.R_R + StenoKeys.H_L + 6
        else:
            raise AssertionError("I am an unknown key.")

    @property
    def row(self):
        rows = [
            [range(StenoKeys.S_L, StenoKeys.H_L + 1), range(StenoKeys.F_R, StenoKeys.D_R + 1), [StenoKeys.STAR]],
            [range(StenoKeys.K_L, StenoKeys.R_L + 1), range(StenoKeys.R_R, StenoKeys.Z_R + 1)],
            [[StenoKeys.A, StenoKeys.O, StenoKeys.E, StenoKeys.U]]
        ]
        for i, row in enumerate(rows):
            if any(self in row_section for row_section in row):
                return i
        raise AssertionError("I am an unknown key.")


"""
A chord is a set of keys pressed simultaneously.
"""
Chord = namedtuple('Chord', 'keys')


"""
A stroke is a list of chords that together form a word.
"""
Stroke = namedtuple('Stroke', 'chord_sequence written_word')


class StenoMachinePreview(ttk.Frame):
    """
    Shows a steno machine view, highlighting the keys that should be pressed to complete the current word.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, width=800, height=200)
        self.canvas.pack()

        self.keys = []

        column_offsets = [0, 1, 2, 3,  # S TPH/KWR
                          2.5, 3.5,  # AO
                          4,  # STAR
                          4.5, 5.5,  # EU
                          5, 6, 7, 8, 9]  # FPLTD/RBGSZ

        assert column_offsets[StenoKeys.A.column] == 2.5
        assert column_offsets[StenoKeys.E.column] == 4.5
        assert column_offsets[StenoKeys.F_R.column] == 5

        for key in StenoKeys.__members__.values():
            grid_x = column_offsets[key.column] * 50
            grid_y = key.row * 50

            begin_x = grid_x + 2
            begin_y = grid_y + 2
            end_x = grid_x + 48
            end_y = grid_y + 48

            if key == StenoKeys.S_L or key == StenoKeys.STAR:
                end_y += 50

            key_square = self.canvas.create_rectangle(begin_x, begin_y, end_x, end_y, fill='gray')
            self.canvas.create_text((begin_x + end_x) * 0.5, (begin_y + end_y) * 0.5, text=key.letter)
            self.keys.append((key, key_square))


    def set_chord(self, chord: Chord):
        """
        Updates the preview to highlight the keys in the given chord.
        """

        for key, key_square in self.keys:
            self.canvas.itemconfigure(key_square, fill='yellow' if key in chord.keys else 'gray')


class StenoExerciseFrame(ttk.Frame):
    """
    Presents an exercise to the user and records the progress made.
    """
    def __init__(self, parent, listener):
        """
        Setups the exercise frame.

        :param parent: the parent widget
        :param listener: object that will receive callbacks for exercise events.
        """
        super().__init__(parent)

        self.words = []
        self.word_i = 0

        # the tk.Text widget can host any widgets in a flow layout, which we exploit here
        self.words_flow_container = tk.Text(self)
        self.words_flow_container.pack()

        # self.preview = StenoMachinePreview(self)
        # self.preview.pack()

        style = ttk.Style()
        style.configure("Exercise.TLabel", foreground="black", background="white", font=('SansBold', 16))
        style.configure("Exercise.TEntry", foreground="black", background="white",
                        fieldbackground="white", borderwidth=0)
        style.configure("Exercise.TFrame", foreground="white", background="white")
        style.map("Exercise.TEntry", fieldbackground=[('disabled', 'white')], foreground=[('disabled', 'black')])

        self.listener = listener

    class WordInExercise(ttk.Frame):
        def __init__(self,
                     exercise_frame,
                     index,
                     stroke):
            super().__init__(exercise_frame, style="Exercise.TFrame")

            self.exercise_frame = exercise_frame

            self.index = index
            self.stroke = stroke

            self._label = ttk.Label(self, text=" " + stroke.written_word, style="Exercise.TLabel")
            self._label.pack(ipadx=0, ipady=2)
            self._text_entry_var = tk.StringVar(self, "", name="word_var_{}".format(index))
            self._text_entry = ttk.Entry(self,
                                         textvariable=self._text_entry_var,
                                         style="Exercise.TEntry",
                                         state=tk.DISABLED,
                                         validate="key",
                                         width=0,  # assign width based on label width
                                         font=('SansBold', 16))
            # self._text_entry.configure(validatecommand=(self.register(self._on_validate), "%s"))
            self._text_entry.pack(fill=tk.X, expand=False)
            self._text_entry_var.trace("w", self._on_change)

            self.incorrectly_typed = False
            self.finished = False
            self.is_first_word = False
            self.finish_time = 0

        @property
        def text_to_type(self):
            """Text that is emitted by a keyboard when the word is typed correctly. This is the text in the dictionary
            preceded by a whitespace."""
            return f" {self.stroke.written_word}"

        @property
        def is_active(self):
            return self.index == self.exercise_frame.word_i

        def begin(self):
            self.exercise_frame.word_i = self.index
            self._text_entry.config(state=tk.NORMAL)
            self._text_entry.focus()
            self._text_entry.icursor(len(self._text_entry_var.get()))

        def _on_change(self, *_):
            self.on_contents_update()

        def on_contents_update(self):
            new_contents = self._text_entry_var.get()
            is_last = self.index + 1 == len(self.exercise_frame.words)

            n_typed_chars = len(new_contents)
            # correctly_typed reflects whether the contents so far is typed correctly,
            # so it only compares the contents to the beginning of the text to type.
            correctly_typed = new_contents == f"{self.text_to_type} "[:len(new_contents)]
            # chars to be typed before we can conclude the current word is typed correctly.
            # this is both the text to type in this word, as well as a whitespace that follows.
            remaining_chars_to_type = len(self.text_to_type) + 1 - n_typed_chars
            # we take time to the point where the complete word is typed. we cannot know that it is correctly typed
            # before we receive a whitespace beginning the next word.
            completely_typed = correctly_typed and remaining_chars_to_type <= 1
            # we advance to the next word once the first whitespace after this word is received, or if this is the last
            # word.
            advance_to_next_word = completely_typed and remaining_chars_to_type <= 0 or is_last

            if not correctly_typed:
                self.incorrectly_typed = True
                self.finished = False
            elif completely_typed:
                if not self.finished:
                    self.finish_time = time.monotonic()
                if advance_to_next_word:
                    overflown_content = new_contents[len(self.text_to_type):]
                    if len(overflown_content) > 0 and is_last:
                        self.incorrectly_typed = True
                    else:
                        self._text_entry.config(state=tk.DISABLED)
                        self._text_entry_var.set(self.text_to_type)
                        if is_last:
                            print("Finished, yay!")
                        else:
                            next_word = self.exercise_frame.words[self.index + 1]
                            next_word.set_overflown_content(overflown_content)
                            next_word.begin()

        def set_overflown_content(self, contents_to_set):
            self._text_entry_var.set(contents_to_set)
            self.on_contents_update()

    def start_session(self):
        """
        Starts the exercise session, will initiate monitoring of user strokes.
        """

    def end_session(self):
        """
        Ends the exercise session.
        """

    def set_exercise(self, strokes):
        """
        Sets a new exercise consisting of the given strokes.
        """
        for i, stroke in enumerate(strokes):
            word = self.WordInExercise(self, i, stroke)
            self.words_flow_container.window_create(tk.INSERT, window=word)
            self.words.append(word)
        self.words_flow_container.configure(state=tk.DISABLED)
        self.words[0].begin()


class StenoApplication(tk.Tk):
    def __init__(self):
        super(StenoApplication, self).__init__()

        with open("data/main.json", "r") as f:
            self.steno_dict = json.load(f)

        self.reverse_dict = defaultdict(list)
        for chord, word in self.steno_dict.items():
            self.reverse_dict[word].append(chord)

        self.exercise_frame = StenoExerciseFrame(self, self)
        self._generate_exercise()
        self.exercise_frame.pack()

        # self.preview.set_chord(Chord(keys=[StenoKeys.S_L, StenoKeys.K_L, StenoKeys.P_L]))
        # self.preview.set_chord(Chord(keys=[StenoKeys.R_L, StenoKeys.O, StenoKeys.R_R]))

    def _generate_exercise(self):
        exercise_length = 10
        all_plover_words = []
        for lesson in learn_plover_lessons:
            all_plover_words += learn_plover_lesson_words[lesson]

        random = Random()
        exercise = []
        for i in range(0, exercise_length):
            word = random.choice(all_plover_words)
            stroke = self.reverse_dict[word][0]

            chords = []
            for chord in stroke.split("/"):
                min_order = -1
                keys = set()
                for letter in chord:
                    if letter == "-":
                        min_order = StenoKeys.STAR
                    else:
                        matching_key = None
                        for key in StenoKeys.__members__.values():
                            if key.letter == letter and key.order > min_order and \
                                    (matching_key is None or matching_key.order > key.order):
                                matching_key = key
                        assert matching_key is not None
                        keys.add(matching_key)
                chords.append(Chord(keys))
            exercise.append(Stroke(chords, word))
        self.exercise_frame.set_exercise(exercise)

if __name__ == "__main__":
    StenoApplication().mainloop()
