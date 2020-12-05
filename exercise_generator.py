

from collections import defaultdict
from random import Random
from steno_keys import StenoKeys, Stroke, Chord
from exercise_log import TupleToJsonObjectConverter, ExerciseResult
from typing import List
from pathlib import Path
from learn_plover import learn_plover_lesson_words
import json


class StenoExerciseGenerator:
    """ Handles the generation of new exercises, that is, choosing words from plover lessons and determining how these
    can be typed (in order to guide the user). This is done based on the history of previous exercises, so the generator
    also keeps a log of completed exercises in a file. """
    def __init__(self,
                 steno_dict_path,
                 user_log_path):
        """
        :param steno_dict_path: path to the Plover stenography dictionary (in JSON format).
        :param user_log_path: path to the user log, where results from previous exercise sessions are stored
        (will be created if it does not already exist).
        """

        with open(steno_dict_path, "r") as f:
            self.steno_dict = json.load(f)

        self.reverse_dict = defaultdict(list)
        for chord, word in self.steno_dict.items():
            if not any(letter in "012345789" for letter in chord):
                self.reverse_dict[word].append(chord)

        self.user_log_path = Path(user_log_path)
        self._json_converter = TupleToJsonObjectConverter()

        try:
            with open(self.user_log_path, "r") as f:
                self.exercise_history = self._json_converter.from_json_object(json.load(f), List[ExerciseResult])
        except (json.JSONDecodeError, IOError):
            self.exercise_history = []

    def clear_exercise_history(self):
        """ Clears the entire exercise history. """
        self.exercise_history.clear()
        self._save_exercise_history()

    def _save_exercise_history(self):
        """ Internal method to save the exercise history to a file, invoked every time the history has changed. """
        self.user_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.user_log_path, "w") as f:
            json.dump(self._json_converter.to_json_object(self.exercise_history, List[ExerciseResult]), f)

    def record_exercise_result(self, exercise_result):
        """
        Records the given exercise result, saving it into the log of completed exercises.

        :param exercise_result: the exercise result to record.
        """
        self.exercise_history.append(exercise_result)
        self._save_exercise_history()

    def _compute_word_weights(self):
        """ Internal method used to compute a dictionary of (harmonic) mean typing time for words that have been typed
        in previous exercises. Words that once were typed incorrectly are not accounted for, due to difficulties in
        determining how long time it took to type it correctly. The mean typing time is then used to present words the
        user has difficulty typing more frequently. """
        typing_times_by_word = defaultdict(list)

        # create a mapping of typing times by word
        for historical_exercise in self.exercise_history:
            for word in historical_exercise.words[1:]:
                if word.is_typed_correctly:
                    typing_times_by_word[word.stroke.written_word].append(word.typing_time)

        # compute the weight of a word by the harmonic mean of its typing time. The harmonic mean has the property of
        # aggravating the impact of small values and reducing the impact of larger values - so if the user generally
        # types a word quickly, a single data point where the typing went slow wont have much of an impact.
        weight_by_word = {word: 1/sum(1/typing_time for typing_time in typing_times)
                          for word, typing_times in typing_times_by_word.items()}
        return weight_by_word

    def generate_exercise(self, exercise_settings):
        """
        Generates a new exercise (that is, a set of strokes) with the given settings, which determine what words from
        "Learn Plover" exercises to include, and how many words an exercise consists of. Words are chosen so the ones
        that the user is slowest at typing occur more frequently.

        :param exercise_settings: settings for the exercise.
        :return: a list of strokes.
        """
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
            """ Parses a stroke in the plover dictionary. A stroke consists of multiple chords separated by "/". Every
            chord consists of a sequence of letters in "Steno Order" (look it up in the Learn Plover series),
            optionally including a "-" to indicate separation between the left and right half of the stenography
            keyboard. """
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
