import tkinter as tk

from learn_plover import *
import json
from pathlib import Path

from ui_elements import StenoMachinePreview, StenoExerciseFrame, StenoExerciseSettingsDialog
from exercise_log import TupleToJsonObjectConverter, ExerciseSettings
from exercise_generator import StenoExerciseGenerator


class StenoApplication(tk.Tk):
    """
    Main application frame. The application picks randomly picks word from a predefined list of lessons, and shows
    them to the user. The application tracks how quickly the user types the given words, and also shows suggestions
    on how to type them on a stenography keyboard using the Plover stenography system. This class couples the various
    components of the application, generating a new exercise when the previous is finished or settings have changed,
    as well as allowing for configuration changes via a menu accessible via a button.
    """
    def __init__(self):
        super(StenoApplication, self).__init__()

        self.configure(background="white")

        self._json_converter = TupleToJsonObjectConverter()

        self._settings_path = Path("output/config.json")

        # Attempt to load settings, setting defaults if loading fails due to missing or corrupt settings file
        try:
            with open(self._settings_path) as f:
                self.current_settings = self._json_converter.from_json_object(json.load(f), ExerciseSettings)
        except (json.JSONDecodeError, IOError):
            self.current_settings = ExerciseSettings(20, learn_plover_lessons)

        self.exercise_generator = StenoExerciseGenerator("data/main.json", "output/log.json")

        self.exercise_settings_button = tk.Button(self,
                                                  text="Exercise Settings...",
                                                  command=self._open_settings_dialog)
        self.exercise_settings_button.pack()

        self.exercise_frame = StenoExerciseFrame(self, self)
        self.exercise_frame.pack(expand=True, fill=tk.BOTH)

        self.machine_preview = StenoMachinePreview(self)
        self.machine_preview.pack(expand=True, fill=tk.BOTH)
        self.set_chord_preview = self.machine_preview.set_chord

        self._generate_exercise()

    def on_settings_dialog_close(self,
                                 regenerate_exercise,
                                 settings_changed,
                                 new_settings):
        """
        Called by settings dialog when it is closed.

        :param regenerate_exercise: whether to generate a new exercise. This is done when settings are changed or the
        history of old exercises has been cleared.
        :param settings_changed: whether the settings have changed.
        :param new_settings: the new settings, or None if not changed.
        """
        if settings_changed:
            self.current_settings = new_settings
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_path, "w") as f:
                json.dump(self._json_converter.to_json_object(self.current_settings, ExerciseSettings), f)
        if regenerate_exercise:
            self._generate_exercise()
        else:
            self.exercise_frame.resume_exercise()

    def on_settings_dialog_clear_history(self):
        """
        Called by settings dialog to clear exercise history.
        """
        self.exercise_generator.clear_exercise_history()

    def finish_exercise(self, exercise_result):
        """
        Called by the exercise frame when the current exercise is finished.

        :param exercise_result: the result of the current exercise
        """
        self.exercise_generator.record_exercise_result(exercise_result)
        self._generate_exercise()

    def _open_settings_dialog(self):
        """ Called when the button to open the settings dialog is pressed. """
        self.exercise_frame.pause_exercise()
        StenoExerciseSettingsDialog(self, self, self.current_settings)

    def _generate_exercise(self):
        """ Generates a new exercise and shows it in the exercise frame. """
        self.exercise_frame.set_exercise(self.exercise_generator.generate_exercise(self.current_settings))


if __name__ == "__main__":
    StenoApplication().mainloop()
