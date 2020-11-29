
from steno_keys import *
from typing import List
from datetime import datetime


"""
Record of a word in an exercise. Tracks the time between the user beginning to type the word (previous word is finished
or the exercise began) and the word is fully typed. Also tracks if the user mistyped the word before typing it correctly.

:param stroke: the stroke that generates the word.
:param is_typed_correctly: whether the word was typed correctly (and not mistyped first)
:param typing_time: time it took between the user beginning to type the word and the typing was complete.
"""
ExerciseWordResult = namedtuple("ExerciseWordResult", "stroke is_typed_correctly typing_time")

"""
Record of a full exercise. Contains a timestamp (date and time) indicating when the exercise began, and the words typed
in the exercise in the order they appeared.

:param timestamp: date and time when the exercise was initiated.
:param words: words of the exercise in the order they occurred.
"""
ExerciseResult = namedtuple("ExerciseResult", "timestamp words")

"""
Exercise settings.

:param exercise_size: amount of words to include in an exercise.
:param enabled_lessons: lessons of the "Learn Plover" series that are included in an exercise.
"""
ExerciseSettings = namedtuple("ExerciseSettings", "exercise_size enabled_lessons")


class TupleToJsonObjectConverter:
    """
    Converts registered namedtuples to and from lists that can be serialized to JSON. Used for converting
    ExerciseResult and ExerciseSettings to a serializable form.
    """
    def __init__(self):
        # mapping of tuple types to the type of their fields.
        self.tuple_field_types = {
            Stroke: [List[Chord], str],
            Chord: [List[StenoKeys]],
            ExerciseResult: [datetime, List[ExerciseWordResult]],
            ExerciseWordResult: [Stroke, bool, float],
            ExerciseSettings: [int, List[str]]
        }

    def from_json_object(self, object, object_type):
        """
        Converts a JSON-representable list into a registered tuple or list of tuples.

        :param object: the object as returned by the JSON parser.
        :param object_type: the type of the object to convert.
        :return: the converted object.
        """
        if hasattr(object_type, "_name") and object_type._name == "List":
            return [self.from_json_object(elem, object_type.__dict__["__args__"][0]) for elem in object]
        elif object_type in [str, int, StenoKeys, bool, float]:
            return object_type(object)
        elif object_type is datetime:
            return datetime.fromisoformat(object)
        elif object_type in self.tuple_field_types:
            res = [self.from_json_object(elem, elem_type)
                   for elem, elem_type in zip(object, self.tuple_field_types[object_type])]
            return object_type(*res)
        else:
            raise RuntimeError(repr(object), repr(object_type))

    def to_json_object(self, object, object_type):
        """
        Converts a registered tuple into a JSON-representable list.

        :param object: the object to convert.
        :param object_type: the type of the object to convert
        :return: the object in JSON-representable form.
        """
        if hasattr(object_type, "_name") and object_type._name == "List":
            return [self.to_json_object(elem, object_type.__dict__["__args__"][0]) for elem in object]
        elif object_type in [str, int, StenoKeys, bool, float]:
            return object
        elif object_type is datetime:
            return str(object)
        elif object_type in self.tuple_field_types:
            res = [self.to_json_object(elem, elem_type)
                   for elem, elem_type in zip(object, self.tuple_field_types[object_type])]
            return res
        else:
            raise RuntimeError(repr(object), repr(object_type))
