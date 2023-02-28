import uuid
from typing import Dict, Iterable, List, Optional

from encord.project_ontology.classification_attribute import ClassificationAttribute
from encord.project_ontology.classification_option import ClassificationOption
from encord.project_ontology.classification_type import ClassificationType
from encord.project_ontology.object_type import ObjectShape
from encord.project_ontology.ontology_classification import OntologyClassification
from encord.project_ontology.ontology_object import OntologyObject


# removal may require calling label/delete/object and label/delete/attribute
def generate_feature_node_hash() -> str:
    """
    Utility function to generate an 8-character hex string.
    """
    return str(uuid.uuid4())[0:8]


class Ontology:
    """
    DEPRECATED: prefer using :class:`encord.ontology.Ontology`
    """

    COLORS = (
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

    def __init__(self):
        self.ontology_objects: List[OntologyObject] = []
        self.ontology_classifications: List[OntologyClassification] = []
        self.color_index = 0

    def __str__(self):
        return str(self.to_dict())

    def __current_object_id(self):
        return len(self.ontology_objects) + 1

    def __current_classification_id(self):
        return len(self.ontology_classifications) + 1

    @classmethod
    def from_dict(cls, ontology_dict: Dict):
        """
        Convert python dictionary too an :class:`.Ontology` object.

        Args:
            ontology_dict: The dictionary to convert.
        """
        ontology = Ontology()
        ontology.ontology_objects = cls.__build_ontology_objects(ontology_dict["objects"])
        ontology.ontology_classifications = cls.__build_ontology_classifications(ontology_dict["classifications"])
        ontology.color_index = len(ontology.ontology_objects) % len(cls.COLORS)
        return ontology

    @classmethod
    def __build_ontology_objects(cls, ontology_objects_dict: List[Dict]):
        ontology_objects = []
        for ontology_object_dict in ontology_objects_dict:
            ontology_object = OntologyObject(
                ontology_object_dict["id"],
                ontology_object_dict["color"],
                ontology_object_dict["name"],
                ObjectShape(ontology_object_dict["shape"]),
                ontology_object_dict["featureNodeHash"],
            )
            ontology_objects.append(ontology_object)
        return ontology_objects

    @classmethod
    def __build_ontology_classifications(cls, ontology_classifications_dict: List[Dict]):
        ontology_classifications = []
        for classification_object_dict in ontology_classifications_dict:
            classification_attributes = []
            for attribute in classification_object_dict["attributes"]:
                classification_attribute = ClassificationAttribute(
                    attribute["id"],
                    attribute["name"],
                    ClassificationType(attribute["type"]),
                    attribute["required"],
                    attribute["featureNodeHash"],
                )
                options_dict = attribute.get("options")
                if options_dict is not None:
                    options = cls.__build_classification_options(attribute["options"])
                    classification_attribute.options = options
                classification_attributes.append(classification_attribute)
            ontology_classification = OntologyClassification(
                classification_object_dict["id"],
                classification_object_dict["featureNodeHash"],
                classification_attributes,
            )
            ontology_classifications.append(ontology_classification)
        return ontology_classifications

    @classmethod
    def __build_classification_options(cls, options_dict: List[Dict]):
        options = []
        for option_dict in options_dict:
            option = ClassificationOption(
                option_dict["id"], option_dict["label"], option_dict["value"], option_dict["featureNodeHash"]
            )
            options.append(option)
        return options

    def add_object(self, name: str, shape: ObjectShape) -> None:
        """
        Add an :class:`.OntologyObject` to the ontology.

        Args:
            name: A descriptive name of the object.
            shape: The shape of the object.

        """
        ontology_object = OntologyObject(
            str(self.__current_object_id()), self.COLORS[self.color_index], name, shape, generate_feature_node_hash()
        )
        self.ontology_objects.append(ontology_object)
        self.color_index = (self.color_index + 1) % len(self.COLORS)

    def add_classification(
        self,
        name: str,
        classification_type: ClassificationType,
        required: bool,
        options: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Add a classification to the ontology.

        Args:
             name: A descriptive name of the classification.
             classification_type: The type of the classification.
             required: Indicate whether annotating this classification is required.
             options: Nested classification options.

        """
        ontology_classification = OntologyClassification(
            str(self.__current_classification_id()),
            generate_feature_node_hash(),
            [self.__create_classification_attributes(name, classification_type, required, options)],
        )
        self.ontology_classifications.append(ontology_classification)

    def __create_classification_attributes(
        self, name: str, classification_type: ClassificationType, required: bool, options: Optional[Iterable[str]]
    ) -> ClassificationAttribute:
        attribute_id = 1
        classification_attribute = ClassificationAttribute(
            f"{self.__current_classification_id()}.{attribute_id}",
            name,
            classification_type,
            required,
            generate_feature_node_hash(),
        )
        if options:
            classification_options = []
            for option_id, option in enumerate(options, 1):
                classification_option = ClassificationOption(
                    f"{self.__current_classification_id()}.{attribute_id}.{option_id}",
                    option,
                    self.__format_option_value(option),
                    generate_feature_node_hash(),
                )
                classification_options.append(classification_option)
            classification_attribute.options = classification_options

        return classification_attribute

    def to_dict(self) -> dict:
        """
        Convert the ontology object to a python dictionary.
        """
        objects = []
        classifications = []

        for ontology_object in self.ontology_objects:
            objects.append(self.ontology_object_to_dict(ontology_object))

        for ontology_classification in self.ontology_classifications:
            classifications.append(self.ontology_classification_to_dict(ontology_classification))

        return {"objects": objects, "classifications": classifications}

    def ontology_object_to_dict(self, ontology_object: OntologyObject) -> Dict:
        return {
            "id": ontology_object.id,
            "color": ontology_object.color,
            "name": ontology_object.name,
            "shape": ontology_object.shape.value,
            "featureNodeHash": ontology_object.feature_node_hash,
        }

    def ontology_classification_to_dict(self, ontology_classification: OntologyClassification) -> Dict:
        classification = {
            "id": ontology_classification.id,
            "featureNodeHash": ontology_classification.feature_node_hash,
        }
        attributes = []
        for classification_attribute in ontology_classification.attributes:
            attribute = {
                "id": classification_attribute.id,
                "name": classification_attribute.name,
                "type": classification_attribute.classification_type.value,
                "required": classification_attribute.required,
                "featureNodeHash": classification_attribute.feature_node_hash,
            }
            if classification_attribute.options:
                options = []
                for classification_option in classification_attribute.options:
                    option = {
                        "id": classification_option.id,
                        "label": classification_option.label,
                        "value": classification_option.value,
                        "featureNodeHash": classification_option.feature_node_hash,
                    }
                    options.append(option)
                attribute["options"] = options
            attributes.append(attribute)

        classification["attributes"] = attributes
        return classification

    def __format_option_value(self, label: str):
        return label.replace(" ", "_")
