import tkinter as tk

from learn_plover import *
import json
from pathlib import Path

from ui_elements import StenoMachinePreview, StenoExerciseFrame, StenoExerciseSettingsDialog, WelcomeDialog
from exercise_log import TupleToJsonObjectConverter, ExerciseSettings, ApplicationSettings
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
        """ Constructs the main application frame, reading user settings, exercise history and the stenography
        dictionary. Will also generate an initial exercise and show the welcome dialog if applicable. """
        super(StenoApplication, self).__init__()

        self.configure(background="white")

        self._json_converter = TupleToJsonObjectConverter()

        self._settings_path = Path("output", "config.json")

        # Attempt to load settings, setting defaults if loading fails due to missing or corrupt settings file
        try:
            with open(self._settings_path) as f:
                self.current_settings = self._json_converter.from_json_object(json.load(f), ApplicationSettings)
        except BaseException:
            self.current_settings = ApplicationSettings(ExerciseSettings(20, learn_plover_lessons), True)

        self.exercise_generator = StenoExerciseGenerator(Path("data", "main.json"), Path("output", "log.json"))

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

        if self.current_settings.show_welcome_dialog:
            WelcomeDialog(self, self)

    def _save_application_settings(self):
        """ Saves the current application settings to the file system. """
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._settings_path, "w") as f:
            json.dump(self._json_converter.to_json_object(self.current_settings, ApplicationSettings), f)

    def on_welcome_dialog_close(self, show_welcome_dialog_setting):
        """
        Called by the welcome dialog when it is closed.
        :param show_welcome_dialog_setting: whether to show the welcome dialog on next startup.
        """
        self.current_settings = ApplicationSettings(self.current_settings.exercise_settings, show_welcome_dialog_setting)
        self._save_application_settings()

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
            self.current_settings = ApplicationSettings(new_settings, self.current_settings.show_welcome_dialog)
            self._save_application_settings()
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
        StenoExerciseSettingsDialog(self, self, self.current_settings.exercise_settings)

    def _generate_exercise(self):
        """ Generates a new exercise and shows it in the exercise frame. """
        self.exercise_frame.set_exercise(self.exercise_generator.generate_exercise(self.current_settings.exercise_settings))


if __name__ == "__main__":
    StenoApplication().mainloop()
