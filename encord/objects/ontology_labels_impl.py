from __future__ import annotations

import logging
from typing import Type, Union

from encord.objects.classification import Classification
from encord.objects.ontology_object import Object

log = logging.getLogger(__name__)


OntologyTypes = Union[Type[Object], Type[Classification]]
OntologyClasses = Union[Object, Classification]
