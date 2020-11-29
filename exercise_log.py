
from steno_keys import *
from typing import List
from datetime import datetime


ExerciseWordResult = namedtuple("ExerciseWordResult", "stroke is_typed_correctly typing_time")
ExerciseResult = namedtuple("ExerciseResult", "timestamp words")
ExerciseSettings = namedtuple("ExerciseSettings", "exercise_size enabled_lessons")


class TupleToJsonObjectConverter:
    def __init__(self):
        self.tuple_field_types = {
            Stroke: [List[Chord], str],
            Chord: [List[StenoKeys]],
            ExerciseResult: [datetime, List[ExerciseWordResult]],
            ExerciseWordResult: [Stroke, bool, float],
            ExerciseSettings: [int, List[str]]
        }

    def from_json_object(self, object, object_type):
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
