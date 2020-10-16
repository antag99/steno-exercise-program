# Specifikation

## Introduktion

Programmet ska träna maskinstenografi enligt [Plover-systemet](https://www.openstenoproject.org/plover/) genom att
presentera övningar av lagom svårighetsgrad för användaren. Ett grafiskt användargränssnitt ska öppnas vid uppstart av
programmet, och övningshistoriken ska läsas in. Därefter kan användaren specifiera vilka områden av maskinstenografi
(indelning enligt kapitlen i [Learn Plover-serien](https://sites.google.com/site/learnplover/)) hen ska träna, och få
övningar i form av ett par meningar. Efter fullbordad övning ska resultatet lagras i historiken och användas
tillsammans med övriga historiken för att presentera nya övningar.


Det mest utmanande/tidskrävande är att göra en bra indelning av stenografiordboken för de olika områdena inom
maskinstenografi, alltså en klassifiering av ackord/ord. Detta ska genomföras genom att programmera in reglerna för
ordbildning inom stenografin, och filtrering på vilka regler som ledde till ett ord.


För ett program som detta förväntas också i allmänhet en bra algoritm för att presentera nya övningar baserat på
resultat från gamla övningar, och att ordkombinationer som presenteras inte ska vara förolämpande för användaren. Detta
utelämnas som krav från denna specifikation i syfte att begränsa uppgiftens omfattning - jag anser också att det
viktigaste är att man kan välja vilka ordbildningsregler man ska träna.


## Användarscenarier

### Scenario 1
Användaren vill träna de mest grundläggande reglerna för stenografi, och
startar därför programmet. Då presenteras övningar som användaren tycker är
alldeles för svåra. Användaren går därför in i inställningarna, och avmarkerar
rutor för de mer avancerade reglerna. Därefter genomför användaren de nya
genererade övningarna.


### Scenario 2
Användaren har någon kvart över i sitt livspussel och startar därför
träningsprogrammet för att lära sig lite mer maskinstenografi. Då presenteras
omedelbart övningar efter inställnigarna som tidigare gjorts i programmet.
Användaren får träna precis de ordbildningsregler som användaren tar längst tid
på sig att komma ihåg.


## Kodskelett

### Maskinstenografimodell

```Python
from enum import IntEnum
from collections import namedtuple


class StenoKeys(IntEnum):
  """
  Enumerates the keys on a stenography keyboard.
  """
  S_L = 0
  T_L = 1
  K_L = 2
  # ...
  E_R = 20
  U_R = 21
  F_R = 22
  # ...

  @property
  def letter(self):
    """
    The letter associated with this key.
    """

  @property
  def column(self):
    """
    The number of the column on the keyboard where this key appears.
    """

  @property
  def row(self):
    """
    The number of the row on the keyboard where this key appears.
    """



"""
A chord is a set of keys pressed simultaneously.
"""
Chord = namedtuple('Chord', 'keys')

"""
A stroke is a list of chords that together form a word.
"""
Stroke = namedtuple('Stroke', 'chord_sequence written_word')

"""
Key press in a logged exercise.
"""
LoggedKeyPress = namedtuple('LoggedKeyPress', 'key timestamp')

"""
Completed stroke in a logged exercise.
"""
LoggedStroke = namedtuple('LoggedStroke', 'stroke timestamp')

"""
Entry in the exercise log.
"""
LoggedExercise = namedtuple('LoggedExercise', 'exercise_type key_log stroke_log begin_timestamp end_timestamp')


class ExerciseLog:
    """
    Log of completed exercises, backed by a file.
    """
    def __init__(self, application_data_directory):
        """
        Initializes the exercise log from the given data directory.
        If no previous exercise data is logged, an empty log will be created in the directory.

        :param application_data_directory: directory containing data files for the application.
        """
        self.application_data_directory = application_data_directory

    def append(self, logged_exercise):
        """
        Appends the given exercise to the log. The backing file will automatically be updated.
        """

    def clear(self):
        """
        Clears the exercise log. The backing file will automatically be updated.
        """

    def __iter__(self):
        """
        Gets an iterator over all logged exercises.
        """

    def close(self):
        """
        Closes any open files. Further operations on this object are undefined in behavior.
        """
```


### UI

```Python
import tkinter as tk
from typing import Mapping
from enum import Enum


class StenoExerciseApp(tk.Tk):
    """
    Application class, shows the main frame.
    """
    def __init__(self):
        super().__init__()


class StenoExerciseSetting(Enum):
    """
    Enumerates possible exercise settings.
    """
    ENABLE_SIMPLE_WORDS = bool
    ENABLE_ADVANCED_WORDS = bool
    # ...
    EXERCISE_LENGTH = int


class StenoExerciseGenerator:
    """
    Generates exercises based on previously completed exercises.
    """
    def __init__(self, exercise_log: ExerciseLog, exercise_settings: Mapping[StenoExerciseSetting, object]):
        self.exercise_log = exercise_log
        self.exercise_settings = exercise_settings

    def generate_exercise(self):
        """
        Generates an exercise (a list of strokes) based on the log of previous exercises.
        """


class StenoExerciseFrame(tk.Frame):
    """
    Presents an exercise to the user and records the progress made.
    """
    def __init__(self, parent, listener):
        """
        Setups the exercise frame.

        :param parent: the parent widget
        :param listener: object that will receive callbacks for exercise events.
        """
        super().__init__(parent)
        self.listener = listener

    def start_session(self):
        """
        Starts the exercise session, will initiate monitoring of user strokes.
        """

    def end_session(self):
        """
        Ends the exercise session.
        """

    def set_exercise(self, strokes):
        """
        Sets a new exercise consisting of the given strokes.
        """


class StenoExerciseSettingsFrame(tk.Frame):
    """
    Frame with exercise settings.
    """
    def __init__(self, parent, listener, settings):
        """
        :param parent: the parent widget
        :param listener: object that will receive callbacks when settings are changed
        :param settings: initial settings
        """
        super().__init__(parent)
        self.listener = listener
        self.settings = settings


class StrokeLogWatcher:
    """
    Watches the plover strokes log for chord presses. This is used to determine which stroke the user used to type a
    word.
    """

    def __init__(self, listener, plover_data_directory):
        """
        :param listener: the object that will receive notifications for typed strokes
        :param plover_data_directory: the path to plover's data directory
        """
        self.listener = listener
        self.plover_data_directory = plover_data_directory

    def start_watching(self):
        """
        Starts watching the log for strokes.
        """

    def stop_watching(self):
        """
        Stops watching the log for strokes.
        """


class StenoMachinePreview(tk.Frame):
    """
    Shows a steno machine view, highlighting the keys that should be pressed to complete the current word.
    """
    def __init__(self, parent):
        super().__init__(parent)

    def set_chord(self, chord: Chord):
        """
        Updates the preview to highlight the keys in the given chord.
        """

```

## Programflöde och dataflöde
Vid programmets start instansieras `StenoExerciseApp` varvid historik läses in, samt generatorn för övningar
instansieras med denna historik. Generatorn för övningar läser in ordboken med förteckning över regler som används
för att bilda ord. Sedan instansieras `StenoExerciseFrame`, vars `start_session`-metod anropas. `StenoExerciseFrame`
börjar då lyssna efter ackord som användarn trycker ned. `StenoExerciseApp` genererar första övningen, vilket ges till
`StenoExerciseFrame`. När användarn trycker ner knappar registreras detta av `StenoExerciseFrame`. Vid första
knapptryckningen påbörjas tidräkningen för övningen. När övningen är klar ges anrop till `StenoExerciseApp`, som loggar
övningen i historiken (historiken lagras löpande i tillhörande fil) och påbörjar en ny övning. Om användaren väljer att
ändra inställningar avbryts den nuvarande övningen och ersätts av en övning med de nya inställningarna.
