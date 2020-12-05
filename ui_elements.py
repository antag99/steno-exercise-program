import tkinter as tk
import tkinter.ttk as ttk
from datetime import datetime
import time
import webbrowser

from steno_keys import StenoKeys, Chord
from exercise_log import ExerciseResult, ExerciseWordResult, ExerciseSettings
from learn_plover import learn_plover_lessons


class StenoMachinePreview(ttk.Frame):
    """
    Shows a steno machine view, highlighting the keys that should be pressed to complete the current word.
    """
    def __init__(self,
                 parent,
                 key_size=50,
                 key_spacing=2):
        """
        :param parent: the parent widget.
        :param key_size: size of keys on the keyboard preview.
        :param key_spacing: spacing between keys on the keyboard preview.
        """
        super().__init__(parent)

        self.canvas = tk.Canvas(self, width=800, height=200)
        self.canvas.pack()

        self.keys = []

        column_offsets = [0, 1, 2, 3,  # S TPH/KWR
                          2.5, 3.5,  # AO
                          4,  # STAR
                          4.5, 5.5,  # EU
                          5, 6, 7, 8, 9]  # FPLTD/RBGSZ

        for key in StenoKeys.__members__.values():
            x = column_offsets[key.column] * (key_size + key_spacing)
            y = key.row * (key_size + key_spacing)
            w = key_size
            h = key_size if key not in (StenoKeys.S_L, StenoKeys.STAR) else key_size * 2 + key_spacing
            key_square = self.canvas.create_rectangle(x, y, x + w, y + h, fill='gray')
            self.canvas.create_text(x + w * 0.5, y + h * 0.5, text=key.letter)
            self.keys.append((key, key_square))

    def set_chord(self, chord: Chord):
        """
        Updates the preview to highlight the keys in the given chord.
        """
        for key, key_square in self.keys:
            self.canvas.itemconfigure(key_square, fill='yellow' if chord is not None and key in chord.keys else 'gray')


class StenoExerciseFrame(ttk.Frame):
    """
    Presents an exercise to the user and records the progress made.
    """
    def __init__(self, parent, listener):
        """
        :param parent: the parent widget
        :param listener: object that will receive callbacks for exercise events.
        """
        super().__init__(parent)

        self.words = []
        self.word_i = 0
        self.exercise_begin_time = 0
        self.exercise_begin_date = None

        # the tk.Text widget can host any widgets in a flow layout, which we exploit here
        self.words_flow_container = tk.Text(self)
        self.words_flow_container.configure(borderwidth=0, highlightthickness=0)
        self.words_flow_container.pack(expand=True, fill=tk.BOTH)

        style = ttk.Style(self)
        style.configure("Exercise.TLabel", foreground="black", background="white", font=('Monospace', 16))
        style.configure("Exercise.TEntry", foreground="black", background="white",
                        fieldbackground="white", borderwidth=0)
        style.configure("Exercise.TFrame", foreground="white", background="white", borderwidth=0)
        style.map("Exercise.TEntry", fieldbackground=[('disabled', 'white')], foreground=[('disabled', 'black')])

        self.configure(borderwidth=0, style="Exercise.TFrame")

        self.listener = listener

    class WordInExercise(ttk.Frame):
        """ Handles a single word in the exercise. Has a label showing the word to type and an entry underneath that
        text is entered into. The active entry/word is automatically changed when the previous word is finished. """
        def __init__(self,
                     exercise_frame,
                     index,
                     stroke):
            """
            :param exercise_frame: exercise frame the word belongs to
            :param index: index of the word in the exerciseå
            :param stroke: stroke for the word, that is the chords to type it as well as the actual written word
            """
            super().__init__(exercise_frame, style="Exercise.TFrame")

            self.exercise_frame = exercise_frame

            self.index = index
            self.stroke = stroke

            self._label = ttk.Label(self, text=" " + stroke.written_word, style="Exercise.TLabel")
            self._label.pack(anchor="w")
            self._text_entry_var = tk.StringVar(self, "")
            self._text_entry = ttk.Entry(self,
                                         textvariable=self._text_entry_var,
                                         style="Exercise.TEntry",
                                         state=tk.DISABLED,
                                         width=len(self.text_to_type),  # assign width based on label width
                                         font=('Monospace', 16))
            self._text_entry.pack(anchor="w")
            self._text_entry_var.trace_add("write", self._on_change)

            self.incorrectly_typed = False
            self.finished = False
            self.is_first_word = False
            self.finish_time = 0

        @property
        def text_to_type(self):
            """Text that is emitted by a keyboard when the word is typed correctly. This is the text in the dictionary
            preceded by a whitespace."""
            return f" {self.stroke.written_word}"

        def begin(self):
            """
            Called when this word is focused, will enable changing the text and show a preview of the chord to press.
            """
            self.exercise_frame.word_i = self.index
            self._text_entry.config(state=tk.NORMAL)
            self._show_chord_preview()
            self.resume()

        def pause(self):
            """
            Called when the settings menu is opened while this word is active.
            """
            pass

        def resume(self):
            """
            Called when the settings menu is closed while this word is active, will re-focus the text entry.
            """
            self._text_entry.focus()
            self._text_entry.icursor(len(self._text_entry_var.get()))

        def _on_change(self, *_):
            """
            Called by tkinter when the contents of the text entry is updated.
            """
            self.on_contents_update()

        def _show_chord_preview(self):
            """ Shows the chord to use to type this word in the preview. """
            self.exercise_frame.listener.set_chord_preview(self.stroke.chord_sequence[0])

        def _on_completely_typed(self):
            """ Called when this word is completely typed, will set the finish time accordingly and show the preview
            of the next word. """
            self.finish_time = time.monotonic()
            self.finished = True
            if self._has_next_word:
                self._next_word._show_chord_preview()
            else:
                self.exercise_frame.listener.set_chord_preview(None)

        def _on_incorrectly_typed(self):
            """ Called whenever this word is typed incorrectly, affects how it is treated in the exercise log.
            (Mistyped words do not count towards the average time it takes to type a word). """
            self.incorrectly_typed = True
            self.finished = False
            self._show_chord_preview()

        @property
        def _has_next_word(self):
            """ Determines whether there is a next word after this in the exercise. """
            return self.index + 1 < len(self.exercise_frame.words)

        @property
        def _next_word(self):
            """ Returns the next word after this, if there is none raises IndexError. """
            return self.exercise_frame.words[self.index + 1]

        def on_contents_update(self):
            """
            Called when the contents of the text entry is changed, either because of direct text entry, or because of
            excess text entered in the entry of the previous word in the exercise.
            """
            new_contents = self._text_entry_var.get()

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
            advance_to_next_word = completely_typed and remaining_chars_to_type <= 0 or not self._has_next_word

            if not correctly_typed:  # mark the word as incorrectly typed when it is
                self._on_incorrectly_typed()
            elif completely_typed:
                if not self.finished:
                    self._on_completely_typed()
                if advance_to_next_word:
                    overflown_content = new_contents[len(self.text_to_type):]
                    if len(overflown_content) > 0 and not self._has_next_word:
                        self.incorrectly_typed = True
                    else:
                        self._text_entry_var.set(self.text_to_type)
                        if not self._has_next_word:
                            self.exercise_frame._on_finish_exercise()
                        else:
                            self._text_entry.config(state=tk.DISABLED)
                            self._next_word._set_overflown_content(overflown_content)
                            self._next_word.begin()

            if not advance_to_next_word:  # update the width of the entry to reflect the width of the entered text.
                self._text_entry.configure(width=max(len(self.text_to_type), len(self._text_entry_var.get())))

        def _set_overflown_content(self, contents_to_set):
            """ Called when the text entered into the entry of the previous exercise flows over into the entry of this word. """
            self._text_entry_var.set(contents_to_set)
            self.on_contents_update()

    def _on_finish_exercise(self):
        """ Called by the final word in the exercise when it is finished.
        Calculates the typing time for each word and reports to the main application class that the exercise is finished.
        """
        word_results = []
        last_time = self.exercise_begin_time
        for word in self.words:
            word_results.append(ExerciseWordResult(word.stroke, not word.incorrectly_typed, word.finish_time - last_time))
            last_time = word.finish_time
        exercise_result = ExerciseResult(self.exercise_begin_date, word_results)
        self.listener.finish_exercise(exercise_result)

    def pause_exercise(self):
        """ Called to pause the exercise when the settings menu is opened. """
        self.words[self.word_i].pause()

    def resume_exercise(self):
        """ Called to resume the exercise when the settings menu is closed. """
        self.words[self.word_i].resume()

    def set_exercise(self, strokes):
        """
        Sets a new exercise consisting of the given strokes.
        """
        for word in self.words:
            word.destroy()
        self.words.clear()

        self.exercise_begin_time = time.monotonic()
        self.exercise_begin_date = datetime.now()

        for i, stroke in enumerate(strokes):
            word = self.WordInExercise(self, i, stroke)
            self.words_flow_container.window_create(tk.INSERT, window=word)
            self.words.append(word)
        self.words_flow_container.configure(state=tk.DISABLED)
        self.words[0].begin()


class StenoExerciseSettingsDialog(tk.Toplevel):
    """
    Settings dialog that allows changing the length of exercises, the lessons that appear in an exercise,
    and clearing the history of past exercises.
    """
    def __init__(self, parent, listener, initial_settings):
        """
        Opens the dialog.

        :param parent: the parent window.
        :param listener: listener that will be notified when the dialog is closed.
        :param initial_settings: the current exercise settings.
        """
        super(StenoExerciseSettingsDialog, self).__init__(parent)

        self.title("Update exercise settings")
        self.parent = parent
        self.listener = listener

        # needed for this toplevel to behave as a dialog.
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self.initial_settings = initial_settings
        exercise_size_frame = ttk.Frame(self)
        ttk.Label(exercise_size_frame, text="Length of exercises").pack(side="left")
        self.exercise_size_var = tk.StringVar(self, value=str(initial_settings.exercise_size))
        self.exercise_size_entry = ttk.Entry(exercise_size_frame, textvariable=self.exercise_size_var, width=3)
        self.exercise_size_entry.pack(anchor="e", side="right")
        exercise_size_frame.pack()

        ttk.Label(self, text="Exercises to include").pack()

        self.lesson_checkboxes = []

        checkboxes_wrapping_frame = ttk.Frame(self)

        # create a checkbox for each plover lesson that may be toggled on or off
        for row, plover_lesson in enumerate(learn_plover_lessons):
            var = tk.IntVar(self, 1 if plover_lesson in initial_settings.enabled_lessons else 0)
            label = ttk.Label(checkboxes_wrapping_frame, text=plover_lesson)
            label.grid(column=0, row=row, sticky="W", padx=2)
            checkbox = ttk.Checkbutton(checkboxes_wrapping_frame, variable=var)
            checkbox.grid(column=1, row=row)
            self.lesson_checkboxes.append((plover_lesson, var))
        checkboxes_wrapping_frame.pack(padx=12, pady=12)

        self.history_cleared = False

        tk.Button(self, text="Clear exercise history", command=self._on_clear_history).pack()

        tk.Button(self, text="OK", command=self._on_ok).pack(side='right')
        tk.Button(self, text="Cancel", command=self._on_cancel).pack(side='left')

    def _on_clear_history(self):
        """ Called when the "Clear exercise history" button is closed. """
        self.listener.on_settings_dialog_clear_history()
        self.history_cleared = True

    def _on_ok(self):
        """ Called when the "OK" button is pressed, will report the new settings to the application class. """
        try:
            exercise_size = max(1, int(self.exercise_size_entry.get()))
        except ValueError:
            exercise_size = self.initial_settings.exercise_size
        enabled_lessons = [lesson for lesson, var in self.lesson_checkboxes if var.get()] or ["One Syllable Words"]
        new_settings = ExerciseSettings(exercise_size, enabled_lessons)
        settings_changed = new_settings != self.initial_settings
        self._close()
        self.listener.on_settings_dialog_close(settings_changed or self.history_cleared, settings_changed, new_settings)

    def _on_cancel(self):
        """ Called when the "OK" button is pressed, will report that the dialog is closed to the application class. """
        self._close()
        self.listener.on_settings_dialog_close(self.history_cleared, False, None)

    def _close(self):
        """ Called whenever the dialog is closed, by the window manager or by OK/Cancel buttons. """
        self.parent.focus_set()
        self.destroy()


class WelcomeDialog(tk.Toplevel):
    """
    Dialog that is shown on start to instruct the user on how to use the program.
    """
    def __init__(self, parent, listener):
        """
        Opens the dialog.

        :param parent: the parent window
        :param listener: listener that will be notified when the dialog is closed.
        """
        super(WelcomeDialog, self).__init__(parent, background="white")
        self.title("Update exercise settings")
        self.parent = parent
        self.listener = listener

        # needed for this toplevel to behave as a dialog.
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)

        self.text = tk.Text(self, wrap=tk.WORD, borderwidth=0, highlightthickness=0)
        self.text.insert(tk.END, "Welcome! This is a training program for the Plover stenography system. To use it, "
                                 "you should begin with installing ")
        plover_link = tk.Label(self, text="Plover", fg="blue", bg="white")
        plover_link.bind("<Button-1>", self._on_plover_label_click)
        self.text.window_create(tk.INSERT, window=plover_link)

        self.text.insert(tk.END, ". Then you can start to type the suggested words using a stenography keyboard."
                                 "\n\n"
                                 "The exercises presented are generated randomly, and are based on the lessons in the ")

        learn_plover_link = tk.Label(self, text="Learn Plover", fg="blue", bg="white")
        learn_plover_link.bind("<Button-1>", self._on_learn_plover_label_click)
        self.text.window_create(tk.INSERT, window=learn_plover_link)

        self.text.insert(tk.END, " series. You should, if you do not have prior Plover experience, read the "
                                 "corresponding chapters in the series before attempting the related exercises. "
                                 "You may select the parts of the Learn Plover series that should be included in "
                                 "\"Exercise Settings\", where you can also select how many words to include in an "
                                 "exercise. "
                                 "\n\n"
                                 "As you finish exercises, the time it takes to type the words are logged, and "
                                 "used to generate new exercises. You may find that words you type the slowest will "
                                 "occur more frequently."
                                 "\n\n"
                                 "For each word in an exercise, the first chord used to type the word is shown in the "
                                 "stenography keyboard preview. If you do not have a stenography keyboard available, "
                                 "you can also try the program with a regular keyboard. Then you should type a space "
                                 "before each word (this is the way Plover emits words by default)."
                                 "\n\n"
                                 "Good luck!")

        self.text.config(state=tk.DISABLED)
        self.text.pack()

        self.do_not_show_again_var = tk.IntVar(self)

        self.do_not_show_again_checkbox = tk.Checkbutton(self,
                                                         text="Do not show this again",
                                                         bg="white",
                                                         borderwidth=0,
                                                         highlightthickness=0,
                                                         variable=self.do_not_show_again_var)
        self.do_not_show_again_checkbox.pack(side="left")

        tk.Button(self, text="OK", command=self._close).pack(side="right")

    @staticmethod
    def _on_plover_label_click(*_):
        """ Called when the "Plover" text is clicked, will open the Plover homepage in a web browser. """
        webbrowser.open_new("http://www.openstenoproject.org/plover/")

    @staticmethod
    def _on_learn_plover_label_click(*_):
        """ Called when the "Learn Plover" text is clicked, will open the main page of the Learn Plover series in a
        web browser. """
        webbrowser.open_new("https://sites.google.com/site/learnplover/")

    def _close(self):
        """ Called whenever the dialog is closed, by the window manager or by the OK button. """
        self.parent.focus_set()
        self.destroy()
        self.listener.on_welcome_dialog_close(not self.do_not_show_again_var.get())
