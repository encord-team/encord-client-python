from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4

from encord.objects.classification import Classification
from encord.objects.common import Shape
from encord.objects.ontology_object import Object

AVAILABLE_COLORS = (
    "#D33115",
    "#E27300",
    "#16406C",
    "#FE9200",
    "#FCDC00",
    "#DBDF00",
    "#A4DD00",
    "#68CCCA",
    "#73D8FF",
    "#AEA1FF",
    "#FCC400",
    "#B0BC00",
    "#68BC00",
    "#16A5A5",
    "#009CE0",
    "#7B64FF",
    "#FA28FF",
    "#B3B3B3",
    "#9F0500",
    "#C45100",
    "#FB9E00",
    "#808900",
    "#194D33",
    "#0C797D",
    "#0062B1",
    "#653294",
    "#AB149E",
)


@dataclass
class OntologyStructure:
    """
    This class is currently in BETA. Its API might change in future minor version releases.
    """

    objects: List[Object] = field(default_factory=list)
    classifications: List[Classification] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> OntologyStructure:
        """
        Args:
            d: a JSON blob of an "ontology structure" (e.g. from Encord web app)

        Raises:
            KeyError: If the dict is missing a required field.
        """
        objects_ret: List[Object] = list()
        for object_dict in d["objects"]:
            objects_ret.append(Object.from_dict(object_dict))

        classifications_ret: List[Classification] = list()
        for classification_dict in d["classifications"]:
            classifications_ret.append(Classification.from_dict(classification_dict))

        return OntologyStructure(objects=objects_ret, classifications=classifications_ret)

    def to_dict(self) -> dict:
        """
        Returns:
            The dict equivalent to the ontology.

        Raises:
            KeyError: If the dict is missing a required field.
        """
        ret = dict()
        ontology_objects = list()
        ret["objects"] = ontology_objects
        for ontology_object in self.objects:
            ontology_objects.append(ontology_object.to_dict())

        ontology_classifications = list()
        ret["classifications"] = ontology_classifications
        for ontology_classification in self.classifications:
            ontology_classifications.append(ontology_classification.to_dict())

        return ret

    def add_object(
        self,
        name: str,
        shape: Shape,
        uid: Optional[int] = None,
        color: Optional[str] = None,
        feature_node_hash: Optional[str] = None,
    ) -> Object:
        """
        Adds an object class definition to the structure.

        .. code::

            structure = ontology_structure.OntologyStructure()

            eye = structure.add_object(
                name="Eye",
            )
            nose = structure.add_object(
                name="Nose",
            )
            nose_detail = nose.add_attribute(
                encord.objects.common.ChecklistAttribute,
            )
            nose_detail.add_option(feature_node_hash="2bc17c88", label="Is it a cute nose?")
            nose_detail.add_option(feature_node_hash="86eaa4f2", label="Is it a wet nose? ")

        Args:
            name: the user-visible name of the object
            shape: the kind of object (bounding box, polygon, etc). See :py:class:`encord.objects.common.Shape` enum for possible values
            uid: integer identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure
            color: the color of the object in the label editor. Normally auto-assigned, should be in '#1A2B3F' syntax.
            feature_node_hash: global identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure

        Returns:
            the created object class that can be further customised with attributes.
        """
        if uid is None:
            if self.objects:
                uid = max([obj.uid for obj in self.objects]) + 1
            else:
                uid = 1
        else:
            if any([obj.uid == uid for obj in self.objects]):
                raise ValueError(f"Duplicate uid '{uid}'")

        if color is None:
            color_index = 0
            if self.objects:
                try:
                    color_index = AVAILABLE_COLORS.index(self.objects[-1].color) + 1
                except ValueError:
                    pass
            color = AVAILABLE_COLORS[color_index]

        if feature_node_hash is None:
            feature_node_hash = str(uuid4())[:8]

        if any([obj.feature_node_hash == feature_node_hash for obj in self.objects]):
            raise ValueError(f"Duplicate feature_node_hash '{feature_node_hash}'")

        obj = Object(uid, name, color, shape, feature_node_hash)
        self.objects.append(obj)
        return obj

    def add_classification(
        self,
        uid: Optional[int] = None,
        feature_node_hash: Optional[str] = None,
    ) -> Classification:
        """
        Adds an classification definition to the ontology.

        .. code::

            structure = ontology_structure.OntologyStructure()

            cls = structure.add_classification(feature_node_hash="a39d81c0")
            cat_standing = cls.add_attribute(
                encord.objects.common.RadioAttribute,
                feature_node_hash="a6136d14",
                name="Is the cat standing?",
                required=True,
            )
            cat_standing.add_option(feature_node_hash="a3aeb48d", label="Yes")
            cat_standing.add_option(feature_node_hash="d0a4b373", label="No")

        Args:
            uid: integer identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure
            feature_node_hash: global identifier of the object. Normally auto-generated;
                    omit this unless the aim is to create an exact clone of existing structure

        Returns:
            the created classification node. Note that classification attribute should be further specified by calling its `add_attribute()` method.
        """
        if uid is None:
            if self.classifications:
                uid = max([cls.uid for cls in self.classifications]) + 1
            else:
                uid = 1
        else:
            if any([cls.uid == uid for cls in self.classifications]):
                raise ValueError(f"Duplicate uid '{uid}'")

        if feature_node_hash is None:
            feature_node_hash = str(uuid4())[:8]

        if any([cls.feature_node_hash == feature_node_hash for cls in self.classifications]):
            raise ValueError(f"Duplicate feature_node_hash '{feature_node_hash}'")

        cls = Classification(uid, feature_node_hash, list())
        self.classifications.append(cls)
        return cls
