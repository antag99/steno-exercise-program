

import tkinter as tk
import tkinter.ttk as ttk

from collections import namedtuple
from enum import IntEnum, unique


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


class StenoAppliation(tk.Tk):
    def __init__(self):
        super(StenoAppliation, self).__init__()

        self.preview = StenoMachinePreview(self)
        self.preview.pack()

        # self.preview.set_chord(Chord(keys=[StenoKeys.S_L, StenoKeys.K_L, StenoKeys.P_L]))
        # self.preview.set_chord(Chord(keys=[StenoKeys.R_L, StenoKeys.O, StenoKeys.R_R]))


if __name__ == "__main__":
    StenoAppliation().mainloop()
