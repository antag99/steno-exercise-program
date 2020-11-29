

from collections import defaultdict
from random import Random
from steno_keys import StenoKeys, Stroke, Chord
from exercise_log import TupleToJsonObjectConverter, ExerciseResult
from typing import List
from pathlib import Path
from learn_plover import learn_plover_lesson_words
import json


class StenoExerciseGenerator:
    def __init__(self,
                 dictionary_file,
                 user_log_file):

        with open(dictionary_file, "r") as f:
            self.steno_dict = json.load(f)

        self.reverse_dict = defaultdict(list)
        for chord, word in self.steno_dict.items():
            if not any(letter in "012345789" for letter in chord):
                self.reverse_dict[word].append(chord)

        self.user_log_file = user_log_file
        self.exercise_history = []
        self._json_converter = TupleToJsonObjectConverter()
        user_log_path = Path(user_log_file)
        user_log_path.parent.mkdir(parents=True, exist_ok=True)
        if user_log_path.exists():
            with open(self.user_log_file, "r") as f:
                self.exercise_history = self._json_converter.from_json_object(json.load(f), List[ExerciseResult])

    def clear_exercise_history(self):
        self.exercise_history.clear()
        self._save_exercise_history()

    def _save_exercise_history(self):
        with open(self.user_log_file, "w") as f:
            json.dump(self._json_converter.to_json_object(self.exercise_history, List[ExerciseResult]), f)

    def record_exercise_result(self, exercise_result):
        self.exercise_history.append(exercise_result)
        self._save_exercise_history()

    def _compute_word_weights(self):
        typing_times_by_word = defaultdict(list)

        for historical_exercise in self.exercise_history:
            for word in historical_exercise.words[1:]:
                if word.is_typed_correctly:
                    typing_times_by_word[word.stroke.written_word].append(word.typing_time)

        weight_by_word = {word: 1/sum(1/typing_time for typing_time in typing_times)
                          for word, typing_times in typing_times_by_word.items()}
        return weight_by_word

    def generate_exercise(self, exercise_settings):
        exercise_length = exercise_settings.exercise_size
        words_to_include = []
        for lesson in exercise_settings.enabled_lessons:
            words_to_include += learn_plover_lesson_words[lesson]

        random = Random()
        word_weights = self._compute_word_weights()
        weights_of_words_to_include = [word_weights.get(word, 0.5) for word in words_to_include]
        random_words = random.choices(words_to_include, weights_of_words_to_include, k=exercise_length)
        # random_words = words_to_include  # just for testing chord parsing

        def parse_chords(stroke):
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
                        assert matching_key is not None, stroke
                        min_order = matching_key.order
                        keys.add(matching_key)
                chords.append(Chord(keys))
            return chords

        return [Stroke(parse_chords(self.reverse_dict[word][0]), word) for word in random_words]
