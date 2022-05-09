from enum import Enum


class ClassificationType(Enum):
    """
    Enum used to define classification type in ontologies.
    """

    #: Single select option
    RADIO = "radio"
    #: Text option for free text input.
    TEXT = "text"
    #: Multi select option
    CHECKLIST = "checklist"
