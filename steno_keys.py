
from enum import IntEnum, unique
from collections import namedtuple


@unique
class StenoKeys(IntEnum):
    """
    Keys on a stenography keyboard. Roughly, the left half denotes consonant sounds in the beginning of a syllable
    (with multiple keys combined to form missing sounds), lower center keys are used to form vowel sounds, and the
    right half consonant sounds ending a syllable.
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
        """
        :return: a number that may be used to determine the location of this key in steno order. For a definition of
        steno order, look it up in the "Learn Plover" series.
        """
        left_half_order = "STKPWHRAO*"
        right_half_order = "EUFRPBLGTSDZ"
        if self.value <= self.STAR:
            return left_half_order.index(self.letter)
        else:
            return len(left_half_order) + right_half_order.index(self.letter)

    @property
    def letter(self):
        """
        :return: the letter printed on this key.
        """
        return "STPHKWRAO*EUFPLTDRBGSZ"[self.value]

    @property
    def column(self):
        """
        :return: the column this key is present in on the keyboard. The center vowels have separate columns.
        """
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
        """
        :return: the row this key is present in on the keyboard.
        """
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
A set of steno keys that are pressed simultaneously to form a word or part of a word.

:param keys: the keys in the chord
"""
Chord = namedtuple('Chord', 'keys')


"""
A sequence of chords that together form a written word.

:param chord_sequence: the sequence of chords used to form the word.
:param written_word: the word that is written.
"""
Stroke = namedtuple('Stroke', 'chord_sequence written_word')
