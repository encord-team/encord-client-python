from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional, Set, Union

from encord.constants.enums import DataType

"""
DENIS:
I'd like to optimise the reads and writes.

For reads I needs some associations

For writes I need the builder pattern same as the OntologyStructure.


"""


@dataclass
class LabelObject:
    pass

    def add_coordinates(
        self,
        coordinates: Any,
        range_: Union[Set[int], Set[str]],
    ):
        pass

    def add_dynamic_answers(self, range_: Any, answers: Any):
        """Again, do intelligent range merging with the current ranges of the same answers"""
        pass


@dataclass
class LabelClassification:
    pass


@dataclass
class SingleLabel:
    objects: List[LabelObject]
    classifications: List[LabelClassification]

    def add_object(
        self,
        feature_hash: str,
        coordinates: Any,
        range_: Union[Set[int], Set[str]],
        # ^ should range be a more intelligent range? Maybe a custom class?
        answers: Optional[Any] = None,
        *,
        created_at: datetime = datetime.now(),
        created_by: Optional[str] = None,
        last_edited_at: datetime = datetime.now(),
        last_edited_by: Optional[str] = None,
        confidence: float = 1.0,
        manual_annotation: bool = True,
        color: Optional[str] = None,
    ):
        """
        * dynamic answers.

        * TODO: do I want to have an `add_bounding_box`, `add_polygon`, ... function instead?
            It can simply complain right away if the wrong coordinate is added.
        * say reviews are read only

        Args:
            range_: The range_ in which this object with the exact same coordinates and answers will be placed.
        """
        pass

    def add_classification(
        self,
        feature_hash: str,
        range_: Union[Set[int], Set[str]],
        answer: Any,
        *,
        created_at: datetime = datetime.now(),
        created_by: Optional[str] = None,
        last_edited_at: datetime = datetime.now(),
        last_edited_by: Optional[str] = None,
        confidence: float = 1.0,
        manual_annotation: bool = True,
    ):
        """
        * Ensure that the client can supply the classification answers.
        * How does the client add a classification range?
        * Note: no support for dynamic attributes is needed.
        * Say somewhere that `reviews` is a read only property that will not be added to the server.
        TODO: the default should be clear from the signature.
        """
        pass
        x = range_
        """Frames need to be added intelligently - as in adjacent range_ are added intelligently."""
        y = answer
        """
        The answer could be a text, or a specific choice of radio or classification. Likely we'd want
        to have a separate class for this. 
        """


@dataclass
class LabelStructure:
    """DENIS: this thing probably should take the corresponding ontology, ideally automatically"""

    label_hash: str
    dataset_hash: str
    dataset_title: str
    data_title: str
    data_type: DataType
    # DENIS: the above fields could be translated less literally.

    """
    Now the data units will either be keyed by the video_hash. Unless it is an image group, then it is keyed
    by the individual image_hashes.
    
    for image groups and images we'd have only one label
    for videos and dicoms we have multiple frames. 
    
    It seems like I'd like to create the common "labels" thing first, and then see how I want to glue
    it together.
    probably something like "add_label" which goes for a specific frame (data_sequence in img group) or for
    a specific hash. 
    """
