import tkinter as tk

from learn_plover import *
import json
from pathlib import Path

from ui_elements import StenoMachinePreview, StenoExerciseFrame, StenoExerciseSettingsDialog
from exercise_log import TupleToJsonObjectConverter, ExerciseSettings
from exercise_generator import StenoExerciseGenerator


class StenoApplication(tk.Tk):
    def __init__(self):
        super(StenoApplication, self).__init__()

        self.configure(background="white")

        self._json_converter = TupleToJsonObjectConverter()

        self._settings_path = Path("output/config.json")
        if not self._settings_path.exists():
            self.current_settings = ExerciseSettings(20, learn_plover_lessons)
        else:
            with open(self._settings_path) as f:
                self.current_settings = self._json_converter.from_json_object(json.load(f), ExerciseSettings)

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

    def on_settings_dialog_close(self, not_canceled, new_settings):
        if not_canceled:
            if new_settings != self.current_settings:
                self.current_settings = new_settings
                self._settings_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._settings_path, "w") as f:
                    json.dump(self._json_converter.to_json_object(self.current_settings, ExerciseSettings), f)
                self._generate_exercise()
                return
        self.exercise_frame.resume_exercise()

    def finish_exercise(self, exercise_result):
        self.exercise_generator.record_exercise_result(exercise_result)
        self._generate_exercise()

    def _open_settings_dialog(self):
        self.exercise_frame.pause_exercise()
        StenoExerciseSettingsDialog(self, self, self.current_settings)

    def _generate_exercise(self):
        self.exercise_frame.set_exercise(self.exercise_generator.generate_exercise(self.current_settings))


if __name__ == "__main__":
    StenoApplication().mainloop()
