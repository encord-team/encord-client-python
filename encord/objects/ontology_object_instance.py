"""---
title: "Objects - Ontology Object Instance"
slug: "sdk-ref-objects-ont-object-instance"
hidden: false
metadata:
  title: "Objects - Ontology Object Instance"
  description: "Encord SDK Objects - Ontology Object Instances."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

from encord.common.range_manager import RangeManager
from encord.constants.enums import DATA_TYPES_WITH_UNKNOWN_LAST_FRAME
from encord.exceptions import LabelRowError
from encord.objects import ChecklistAttribute, RadioAttribute, Shape, TextAttribute
from encord.objects.answers import Answer, NumericAnswerValue, _get_static_answer_map, get_default_answer_from_attribute
from encord.objects.attributes import Attribute, NumericAttribute, _get_attribute_by_hash
from encord.objects.constants import DEFAULT_MANUAL_ANNOTATION
from encord.objects.coordinates import (
    ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS,
    EVENT_SHAPES,
    NON_GEOMETRIC_COORDINATES,
    AudioCoordinates,
    Coordinates,
    EventCoordinates,
    GeometricCoordinates,
    HtmlCoordinates,
    TextCoordinates,
    TimeRangeCoordinates,
    UpsertEventCoordinates,
    zeroed_coordinates,
)
from encord.objects.events import (
    EventKind,
    LabelDeleteEvent,
    LabelEvent,
    LabelUpsertEvent,
    check_events_terminated,
    event_ranges,
    events_intersect,
    prune_dangling_deletes,
    resolve_event_at,
)
from encord.objects.frames import (
    Frames,
    Range,
    Ranges,
    frames_class_to_frames_list,
    frames_class_to_ranges,
    frames_to_ranges,
    ranges_list_to_ranges,
)
from encord.objects.html_node import HtmlRanges
from encord.objects.internal_helpers import (
    _infer_attribute_from_answer,
    _search_child_attributes,
)
from encord.objects.ontology_object import Object
from encord.objects.options import Option
from encord.objects.spaces.annotation.base_annotation import _AnnotationData, _AnnotationMetadata, _ObjectAnnotation
from encord.objects.spaces.annotation.geometric_annotation import _GeometricAnnotationData
from encord.objects.spaces.annotation.range_annotation import _RangeObjectAnnotationData
from encord.objects.types import (
    AnswerDict,
    AttributeDict,
    DynamicAttributeObject,
)
from encord.objects.utils import short_uuid_str

if TYPE_CHECKING:
    from encord.objects.ontology_labels_impl import LabelRowV2
    from encord.objects.spaces.base_space import Space


class ObjectInstance:
    """An object instance is an object that has coordinates and can be placed on one or multiple frames in a label row."""

    def __init__(self, ontology_object: Object, *, object_hash: Optional[str] = None):
        self._ontology_object = ontology_object
        self._object_hash = object_hash or short_uuid_str()
        self._parent: Optional[LabelRowV2] = None

        self._static_answer_map: Dict[str, Answer] = _get_static_answer_map(self._ontology_object.attributes)
        # feature_node_hash of attribute to the answer.

        self._dynamic_answer_manager = DynamicAnswerManager(self)

        # Only used for non-frame entities
        self._non_geometric = ontology_object.shape in (Shape.AUDIO, Shape.TIME_RANGE, Shape.TEXT)

        # Only for Range based modalities, where the ranged objects share the same metadata across all spaces
        self._instance_metadata: _AnnotationMetadata = _AnnotationMetadata()

        self._frames_to_instance_data: Dict[int, _AnnotationData] = {}
        self._spaces: dict[str, Space] = dict()

    def _is_assigned_to_space(self) -> bool:
        return bool(self._spaces)

    def _is_event_based(self) -> bool:
        """Whether this object's labels are sparse events on a continuous timeline.

        Range-based shapes (audio, text, time range) keep their range semantics regardless of the row flag, and
        objects on a space have no time axis of their own: neither is ever event-based.
        """
        return (
            not self._non_geometric
            and not self._is_assigned_to_space()
            and self._parent is not None
            and self._parent.is_event_based
        )

    def _stored_frames(self) -> set[int]:
        """Every frame this object has a stored entry on, `delete` markers included.

        The internal counterpart to `get_annotation_frames`, which is a read API and is refused outright on an
        event-based row. Serialisation and the frame-to-hash bookkeeping need the markers: dropping them would
        strip each object's terminator and leave it present with no end.
        """
        return set(self._frames_to_instance_data.keys())

    def _check_not_event_based(self, method: str, reason: str) -> None:
        """Internal. Refuse a frame-grid API on a row whose labels are sparse events.

        Raised rather than answered: every one of these either assumes a frame grid the row does not have, or
        would quietly report something that means a different thing here than it does on a dense row.
        """
        if self._is_event_based():
            raise LabelRowError(
                f"`{method}` is not available on an event-based label row. {reason} Read the object with "
                f"`get_events`, `get_ranges` and `get_annotation(frame)`; write it with `upsert_event`, "
                f"`delete_event` and `remove_event`."
            )

    def _event_kind_at(self, frame: int) -> EventKind:
        """The kind of the entry stored on `frame`, defaulting an untagged entry to `upsert`."""
        kind = self._frames_to_instance_data[frame].annotation_metadata.event_kind
        return "upsert" if kind is None else kind

    def _sorted_events(self) -> List[LabelEvent]:
        """This object's stored entries as events, sorted by frame ascending."""
        events: List[LabelEvent] = []
        for frame in sorted(self._frames_to_instance_data.keys()):
            data = self._frames_to_instance_data[frame]
            metadata = data.annotation_metadata
            if self._event_kind_at(frame) == "delete":
                events.append(LabelDeleteEvent(frame=frame, metadata=metadata))
            else:
                events.append(
                    LabelUpsertEvent(
                        frame=frame,
                        metadata=metadata,
                        coordinates=cast(EventCoordinates, cast(_GeometricAnnotationData, data).coordinates),
                    )
                )
        return events

    def _check_events_terminated(self) -> None:
        """Raise if this object's events end on an upsert, leaving it present with no end.

        Dangling while a caller is still building the object up is fine — `upsert` then `delete` must not be a
        two-step error — so the label row applies this only on parse and on save.
        """
        check_events_terminated(self._sorted_events(), object_hash=self.object_hash)

    def _has_event_tags(self) -> bool:
        """Whether any stored entry carries an `event` tag. Cheap: stored entries are sparse."""
        return any(data.annotation_metadata.event_kind is not None for data in self._frames_to_instance_data.values())

    def _event_tagged_frames(self) -> List[int]:
        """Frames whose stored entry carries an `event` tag, sorted ascending."""
        return [
            frame
            for frame in sorted(self._frames_to_instance_data)
            if self._frames_to_instance_data[frame].annotation_metadata.event_kind is not None
        ]

    def _is_present_over(self, ranges: Ranges) -> bool:
        """Whether this object is present anywhere in `ranges` on an event-based row.

        Presence is range containment, not keyframe membership: an object upserted once holds until its
        delete, so it is present at every offset in between even though nothing is stored there.
        """
        events = self._sorted_events()
        return any(events_intersect(events, range_.start, range_.end) for range_ in ranges)

    def _check_event_based(self, method: str) -> None:
        if self._parent is None and not self._is_assigned_to_space():
            raise LabelRowError(
                f"`{method}` requires this object to be attached to an event-based label row. "
                "Call `label_row.add_object_instance(object_instance)` first."
            )
        if not self._is_event_based():
            raise LabelRowError(
                f"`{method}` is only available on an event-based label row. "
                "This object's label row is not event-based; use `set_for_frames`, `get_annotation` and "
                "`remove_from_frames` instead."
            )

    def get_events(self) -> List[LabelEvent]:
        """All stored events of this object on an event-based label row, sorted by frame.

        Includes `delete` markers. Use :meth:`get_ranges` for the ranges the object is present over.

        Raises:
            LabelRowError: If the label row is not event-based.
        """
        self._check_event_based("get_events")
        return self._sorted_events()

    def get_ranges(self) -> Ranges:
        """The minimal closed ranges this object is present over.

        On a frame-based label row these are the frames it is annotated on, run-length encoded. On an
        event-based row they are the stretches each `upsert` holds over, closed by the `delete` that ends
        them. On a range-only object (audio, text, time range) they are the object's own ranges.

        Raises:
            LabelRowError: If the object's events end on an `upsert` with no closing `delete`.
        """
        if self._non_geometric:
            return self.range_list or []
        if self._is_event_based():
            return event_ranges(self._sorted_events())
        return frames_to_ranges(self.get_annotation_frames())

    def _store_event(
        self,
        frame: int,
        kind: EventKind,
        coordinates: Coordinates,
        *,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        geometric_coordinates = cast(GeometricCoordinates, coordinates)
        existing = self._frames_to_instance_data.get(frame)
        if existing is None:
            existing = _GeometricAnnotationData(
                coordinates=geometric_coordinates, annotation_metadata=_AnnotationMetadata()
            )
            self._frames_to_instance_data[frame] = existing
        cast(_GeometricAnnotationData, existing).coordinates = geometric_coordinates
        if kind == "delete":
            # A marker is not a keyframe: reserved keyframe fields must not carry over onto it.
            existing.annotation_metadata._interpolate = None
        existing.annotation_metadata.update_from_optional_fields(
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            event_kind=kind,
        )
        if self._parent is not None:
            # Re-register with the row: `_drop_event_frames` removes the object from `_objects_map` once it has
            # no frames left, but leaves `_parent` set. Without this, a later upsert would be added to
            # `_frame_to_hashes` but stay absent from `_objects_map`, so it would never be exported.
            self._parent._objects_map.setdefault(self.object_hash, self)
            self._parent.add_to_single_frame_to_hashes_map(self, frame)

    def _drop_event_frames(self, frames: Iterable[int]) -> None:
        frames_list = [f for f in frames if f in self._frames_to_instance_data]
        for frame in frames_list:
            self._frames_to_instance_data.pop(frame)
        if self._parent is not None:
            self._parent._remove_from_frame_to_hashes_map(frames_list, self.object_hash)
            if len(self._frames_to_instance_data) == 0 and self.object_hash in self._parent._objects_map:
                del self._parent._objects_map[self.object_hash]

    def _prune_dangling_deletes(self) -> None:
        if self._frames_to_instance_data:
            self._drop_event_frames(prune_dangling_deletes(self._sorted_events()))

    def upsert_event(
        self,
        coordinates: UpsertEventCoordinates,
        frame: int,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
    ) -> None:
        """Write a keyframe on an event-based label row: from `frame` on, the object has these coordinates.

        The keyframe holds until the object's next event, or indefinitely if there is none. A `delete` marker
        stored on `frame` is replaced.

        Args:
            coordinates: The geometry from `frame` onward. Must match the ontology object's shape.
            frame: The frame (nanosecond offset relative to the start of the scene on a continuous scene) the
                keyframe starts at. Must be >= 0.
            overwrite: Required to replace an upsert already stored on `frame`.
            created_at: Optionally the creation time. Defaults to now.
            created_by: Optionally the creator. Defaults to the SDK user.
            last_edited_at: Optionally the last edit time. Defaults to now.
            last_edited_by: Optionally the last editor. Defaults to the SDK user.
            confidence: Optionally the confidence. Defaults to `1.0`.
            manual_annotation: Optionally whether this was a manual annotation. Defaults to `True`.

        Raises:
            LabelRowError: If the row is not event-based, the coordinates do not match the ontology shape,
                `frame` is negative, or an upsert exists on `frame` and `overwrite` is False.
        """
        self._check_event_based("upsert_event")
        self._operation_not_allowed_for_objects_on_space()
        if self._ontology_object.shape not in EVENT_SHAPES:
            raise LabelRowError(
                f"Objects of shape `{self._ontology_object.shape}` cannot be written to an event-based label row; "
                f"only {sorted(s.value for s in EVENT_SHAPES)} are supported."
            )
        check_coordinate_type(coordinates, self._ontology_object, self._parent)
        if frame < 0:
            raise LabelRowError(f"The supplied frame of `{frame}` must be `0` or greater.")

        if frame in self._frames_to_instance_data and self._event_kind_at(frame) == "upsert" and not overwrite:
            raise LabelRowError(
                f"An upsert already exists at frame `{frame}`. Set `overwrite=True` to replace it, "
                "or call `remove_event(frame)` first."
            )

        self._store_event(
            frame,
            "upsert",
            coordinates,
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
        )
        self._prune_dangling_deletes()

    def delete_event(self, frame: int) -> None:
        """Write a `delete` on an event-based label row: from `frame` on, the object does not exist.

        The object reappears at its next upsert, if any. A delete that would terminate nothing (the object is
        already absent at `frame`) is not written. Where `frame` holds the object's own opening keyframe, that
        keyframe is removed instead. Deletes left terminating nothing are pruned, and an object with no events
        left is removed from its label row.

        Args:
            frame: The frame (nanosecond offset relative to the start of the scene on a continuous scene) the
                object ends at.

        Raises:
            LabelRowError: If the row is not event-based.
        """
        self._check_event_based("delete_event")
        self._operation_not_allowed_for_objects_on_space()

        events = self._sorted_events()
        resolved = resolve_event_at(events, frame)
        if resolved is None:
            return

        opens_a_stretch = resolved.frame == frame and (frame == 0 or resolve_event_at(events, frame - 1) is None)
        if opens_a_stretch:
            self._drop_event_frames([frame])
            self._prune_dangling_deletes()
            return

        self._store_event(
            frame,
            "delete",
            zeroed_coordinates(self._ontology_object.shape),
            created_at=resolved.metadata.created_at,
            created_by=resolved.metadata.created_by,
            last_edited_at=resolved.metadata.last_edited_at,
            last_edited_by=resolved.metadata.last_edited_by,
            confidence=resolved.metadata.confidence,
            manual_annotation=resolved.metadata.manual_annotation,
        )
        self._prune_dangling_deletes()

    def remove_event(self, frame: int) -> None:
        """Erase the event stored on `frame` on an event-based label row, as if it were never written.

        Unlike :meth:`delete_event`, which adds an event saying the object ends, this removes one. Deletes left
        terminating nothing are pruned. An object with no events left is removed from its label row.

        Args:
            frame: The frame of the stored event.

        Raises:
            LabelRowError: If the row is not event-based or nothing is stored on `frame`.
        """
        self._check_event_based("remove_event")
        self._operation_not_allowed_for_objects_on_space()
        if frame not in self._frames_to_instance_data:
            raise LabelRowError(f"No event is stored at frame `{frame}`. See `get_events()` for the stored frames.")
        self._drop_event_frames([frame])
        self._prune_dangling_deletes()

    def _add_to_space(self, space: Space) -> None:
        self._spaces[space.space_id] = space

    def _remove_from_space(self, space_id: str) -> None:
        self._spaces.pop(space_id)
        if not self._spaces:
            # Reset metadata if not on any space
            self._instance_metadata = _AnnotationMetadata()

    def is_assigned_to_label_row(self) -> Optional[LabelRowV2]:
        """Checks if the object instance is assigned to a label row.

        Returns:
            The LabelRowV2 instance if assigned, otherwise None.
        """
        return self._parent

    @property
    def object_hash(self) -> str:
        """A unique identifier for the object instance.

        Returns:
            The unique object hash.
        """
        return self._object_hash

    @property
    def ontology_item(self) -> Object:
        """The ontology object associated with this instance.

        Returns:
            The ontology object.
        """
        return self._ontology_object

    @property
    def feature_hash(self) -> str:
        """Feature node hash from the project ontology.

        Returns:
            The feature node hash.
        """
        return self._ontology_object.feature_node_hash

    @property
    def object_name(self) -> str:
        """Object name from the project ontology.

        Returns:
            The object name.
        """
        return self._ontology_object.name

    @property
    def _last_frame(self) -> Union[int, float]:
        if self._parent is None or self._parent.data_type in DATA_TYPES_WITH_UNKNOWN_LAST_FRAME:
            return float("inf")
        else:
            return self._parent.number_of_frames

    @property
    def range_list(self) -> Optional[Ranges]:
        if self._non_geometric:
            self._operation_not_allowed_for_objects_on_space(
                extended_message=" For getting ranges for objects on a space,"
                " use space.get_object_ranges(object_instance)."
            )

            non_geometric_annotation = self._get_non_geometric_annotation()
            if non_geometric_annotation is None:
                return None

            coordinates = non_geometric_annotation.coordinates

            if isinstance(coordinates, (AudioCoordinates, TimeRangeCoordinates, TextCoordinates)):
                return coordinates.range
            else:
                return None

        else:
            raise LabelRowError(
                "No ranges available for this object instance."
                "Please ensure the object instance was created with "
                "the range_only property to True (via a range aware shape)"
                "You can do ObjectInstance(audio_ontology_object) to achieve this."
            )

    @property
    def range_html(self) -> Optional[HtmlRanges]:
        if not self._non_geometric:
            return None

        non_geometric_annotation = self._get_non_geometric_annotation()
        if non_geometric_annotation is None:
            return None

        coordinates = non_geometric_annotation.coordinates

        if isinstance(coordinates, HtmlCoordinates):
            return coordinates.range
        else:
            return None

    def is_range_only(self) -> bool:
        return self._non_geometric

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, NumericAnswerValue, Option, Iterable[Option], None] = None,
        filter_frame: Optional[int] = None,
        is_dynamic: Optional[bool] = None,
    ) -> Union[str, NumericAnswerValue, Option, Iterable[Option], AnswersForFrames, None]:
        """Get the answer set for a given ontology Attribute. Returns `None` if the attribute is not yet answered.

        For the ChecklistAttribute, it returns None if and only if
        the attribute is nested and the parent is unselected. Otherwise, if not yet answered it will return an empty
        list.

        Args:
            attribute: The ontology attribute to get the answer for.
            filter_answer: A filter for a specific answer value. Only applies to dynamic attributes.
            filter_frame: A filter for a specific frame. Only applies to dynamic attributes.
            is_dynamic: Optionally specify whether a dynamic answer is expected or not. This will throw if it is
                set incorrectly according to the attribute. Set this to narrow down the return type.

        Returns:
            If the attribute is static, then the answer value is returned, assuming an answer value has already been
            set. If the attribute is dynamic, the AnswersForFrames object is returned.
        """
        if attribute is None:
            attribute = self._ontology_object.attributes[0]
        elif not self._is_attribute_valid_child_of_object_instance(attribute):
            raise LabelRowError("The attribute is not a valid child of the classification.")
        elif not attribute.dynamic and not self._is_selectable_child_attribute(attribute):
            return None

        if is_dynamic is not None and is_dynamic is not attribute.dynamic:
            raise LabelRowError(
                f"The attribute is {'dynamic' if attribute.dynamic else 'static'}, but is_dynamic is set to "
                f"{is_dynamic}."
            )

        if attribute.dynamic:
            return self._dynamic_answer_manager.get_answer(attribute, filter_answer, filter_frame)

        static_answer = self._static_answer_map[attribute.feature_node_hash]

        if not static_answer.is_answered():
            if isinstance(attribute, ChecklistAttribute):
                return []
            return None

        return static_answer.get()

    def set_answer(
        self,
        answer: Union[str, NumericAnswerValue, Option, Sequence[Option]],
        attribute: Optional[Attribute] = None,
        frames: Optional[Frames] = None,
        overwrite: bool = False,
        manual_annotation: bool = DEFAULT_MANUAL_ANNOTATION,
    ) -> None:
        """Set the answer for a given ontology Attribute. This is the equivalent of e.g. selecting a checkbox in the
        UI after drawing the ObjectInstance. There is only one answer per ObjectInstance per Attribute, unless
        the attribute is dynamic (check the args list for more instructions on how to set dynamic answers).

        Args:
            answer: The answer to set.
            attribute: The ontology attribute to set the answer for. If not set, this will be attempted to be
                inferred.  For answers to :class:`encord.objects.attributes.RadioAttribute` or
                :class:`encord.objects.attributes.ChecklistAttribute`, this can be inferred automatically.
                For :class:`encord.objects.attributes.TextAttribute` or :class:`encord.objects.attributes.NumericAttribute`,
                this will only be inferred if there is only one possible
                TextAttribute or NumericAttribute to set for the entire object instance.
                Otherwise, a :class:`encord.exceptions.LabelRowError` will be thrown.
            frames: Only relevant for dynamic attributes. The frames to set the answer for. If `None`, the
                answer is set for all frames that this object currently has set coordinates for (also overwriting
                current answers). This will not automatically propagate the answer to new frames that are added in the
                future.
                If this is anything but `None` for non-dynamic attributes, this will
                throw a ValueError.
            overwrite: If `True`, the answer will be overwritten if it already exists. If `False`, this will throw
                a LabelRowError if the answer already exists. This argument is ignored for dynamic attributes.
            manual_annotation: If `True`, the answer will be marked as manually annotated. This arg defaults to
                DEFAULT_MANUAL_ANNOTATION.
        """
        if attribute is None:
            attribute = _infer_attribute_from_answer(self._ontology_object.attributes, answer)
        if not self._is_attribute_valid_child_of_object_instance(attribute):
            raise LabelRowError("The attribute is not a valid child of the object.")
        elif not attribute.dynamic and not self._is_selectable_child_attribute(attribute):
            raise LabelRowError(
                "Setting a nested attribute is only possible if all parent attributes have been selected."
            )
        elif frames is not None and attribute.dynamic is False:
            raise LabelRowError("Setting frames is only possible for dynamic attributes.")

        if attribute.dynamic:
            self._dynamic_answer_manager.set_answer(answer, attribute, frames)
            return

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        if static_answer.is_answered() and overwrite is False:
            raise LabelRowError(
                "The answer to this attribute was already set. Set `overwrite` to `True` if you want to"
                "overwrite an existing answer to an attribute."
            )
        static_answer.set(answer, manual_annotation=manual_annotation)

    def set_answer_from_list(self, answers_list: List[AttributeDict]) -> None:
        """This is a low level helper function and should usually not be used directly.

        Sets the answer for the classification from a dictionary.

        Args:
            answers_list: The list of dictionaries to set the answer from.
        """
        grouped_answers = defaultdict(list)

        for answer_dict in answers_list:
            feature_hash = answer_dict["featureHash"]
            attribute = _get_attribute_by_hash(feature_hash, self._ontology_object.attributes)
            if attribute is None:
                raise LabelRowError(
                    f"Attribute with id [{feature_hash}] does not exist in the ontology. Cannot create a valid LabelRow."
                )
            if not self._is_attribute_valid_child_of_object_instance(attribute):
                raise LabelRowError(
                    "One of the attributes set for a classification is not a valid child of the classification. "
                    "Cannot create a valid LabelRow."
                )

            grouped_answers[attribute.feature_node_hash].append(answer_dict)

        #
        # UI structures answers for checkboxes differently from SDK.
        # It has separate answer dict with the same feature hash rather than just one dict with multiple answers,
        # as SDK expects.
        # So until we aligned the models, we need to introduce additional adaptation layer, that groups separate
        # dictionaries with one answer into one with multiple answer.
        # This is a hotfix rather than a proper solution.
        # TODO: agree on a one correct way to represent the checklist response, and change the SDK accordingly.
        #

        for feature_hash, answers_list in grouped_answers.items():
            attribute = _get_attribute_by_hash(feature_hash, self._ontology_object.attributes)
            assert attribute  # we already checked that attribute is not null above. So just silencing this for now
            self._set_answer_from_grouped_list(attribute, answers_list)

    @staticmethod
    def _merge_answers_to_non_overlapping_ranges(ranges: List[Tuple[Range, Set[str]]]) -> List[Tuple[Range, Set[str]]]:
        ranges.sort(key=lambda x: x[0].start)

        edges: List[Tuple[int, bool, Set[str]]] = []
        for r, option_ids in ranges:
            edges.extend(((r.start, True, set(option_ids)), (r.end, False, set(option_ids))))
        edges.sort(key=lambda x: x[0])

        result_ranges: Dict[Tuple[int, int], Tuple[Range, Set[str]]] = {}

        prev = 0
        prev_state: Set[str] = set()
        prev_close = False

        for frame_num, is_start, options in edges:
            if is_start:
                new_state = prev_state.union(options)
                start = prev
                end = frame_num - int((len(prev_state) > 0))
                prev_close = False
            else:
                start = prev + int(prev_close)
                end = frame_num
                prev_close = True
                new_state = prev_state.difference(options)

            if len(prev_state) > 0:
                if (start, end) in result_ranges:
                    result_ranges[(start, end)][1].update(prev_state.copy())
                else:
                    result_ranges[(start, end)] = (
                        Range(start, end),
                        prev_state.copy(),
                    )

            prev_state = new_state
            prev = frame_num

        return list(result_ranges.values())

    def _operation_not_allowed_for_objects_on_space(self, extended_message: Optional[str] = None) -> None:
        base_message = "This operation is not allowed for objects that exist on a space."
        error_message = base_message + extended_message if extended_message is not None else base_message
        if self._is_assigned_to_space():
            raise LabelRowError(error_message)

    def _set_answer_from_grouped_list(
        self, attribute: Attribute, answers_list: List[AttributeDict | DynamicAttributeObject]
    ) -> None:
        if isinstance(attribute, ChecklistAttribute):
            if not attribute.dynamic:
                options = []
                for answer_dict in answers_list:
                    checklist_answers = cast(List[AnswerDict], answer_dict["answers"])
                    for answer in checklist_answers:
                        feature_hash = answer["featureHash"]
                        option = attribute.get_child_by_hash(feature_hash, type_=Option)
                        options.append(option)

                self._set_answer_unsafe(options, attribute, None)
            else:
                dynamic_answers_list = cast(List[DynamicAttributeObject], answers_list)
                all_feature_hashes: Set[str] = set()
                ranges = []
                for answer_dict in dynamic_answers_list:
                    answers = answer_dict["answers"]
                    if isinstance(answers, list):
                        feature_hashes: Set[str] = {answer["featureHash"] for answer in answers}
                        all_feature_hashes.update(feature_hashes)
                        for frame_range in ranges_list_to_ranges(answer_dict["range"]):
                            ranges.append((frame_range, feature_hashes))

                options_cache = {
                    feature_hash: attribute.get_child_by_hash(feature_hash, type_=Option)
                    for feature_hash in all_feature_hashes
                }

                for frame_range, feature_hashes in self._merge_answers_to_non_overlapping_ranges(ranges):
                    options = [options_cache[feature_hash] for feature_hash in feature_hashes]
                    self._set_answer_unsafe(options, attribute, [frame_range])
        else:
            for answer in answers_list:
                self._set_answer_from_dict(answer, attribute)

    def delete_answer(
        self,
        attribute: Attribute,
        filter_answer: Optional[Union[str, Option, Iterable[Option]]] = None,
        filter_frame: Optional[int] = None,
    ) -> None:
        """Reset the answer of an attribute as if it was never set.

        Args:
            attribute: The attribute to delete the answer for.
            filter_answer: A filter for a specific answer value. Delete only answers with the provided value.
                Only applies to dynamic attributes.
            filter_frame: A filter for a specific frame. Only applies to dynamic attributes.
        """
        if attribute.dynamic:
            self._operation_not_allowed_for_objects_on_space(
                extended_message="For removing dynamic attributes for objects on a space, use VideoSpace.remove_answer_from_frame."
            )
            self._dynamic_answer_manager.delete_answer(attribute, filter_frame, filter_answer)
            return

        static_answer = self._static_answer_map[attribute.feature_node_hash]
        static_answer.unset()

    def check_within_range(self, frame: int) -> None:
        """Check if the given frame is within the acceptable range.

        Args:
            frame: The frame number to check.

        Raises:
            LabelRowError: If the frame is out of the acceptable range.
        """
        if frame < 0 or frame >= self._last_frame:
            raise LabelRowError(
                f"The supplied frame of `{frame}` is not within the acceptable bounds of `0` to `{self._last_frame}`."
            )

    def set_for_frames(
        self,
        coordinates: Coordinates,
        frames: Frames = 0,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,  # This field is deprecated. It will always be None.
        is_deleted: Optional[bool] = None,
        event_kind: Optional[EventKind] = None,  # Should only be set by internal functions.
    ) -> None:
        """Place the object onto the specified frame(s).

        If the object already exists on the frame and overwrite is set to `True`,
        the currently specified values will be overwritten.

        Args:
            coordinates: The coordinates of the object in the frame.
                This will throw an error if the type of the coordinates does not match the type of the attribute in the object instance.
            frames: The frames to add the object instance to. Defaults to the first frame for convenience.
            overwrite: If `True`, overwrite existing data for the given frames.
                This will not reset all the non-specified values.
                If `False` and data already exists for the given frames, raises an error.
            created_at: Optionally specify the creation time of the object instance on this frame.
                Defaults to `datetime.now()`.
            created_by: Optionally specify the creator of the object instance on this frame.
                Defaults to the current SDK user.
            last_edited_at: Optionally specify the last edit time of the object instance on this frame.
                Defaults to `datetime.now()`.
            last_edited_by: Optionally specify the last editor of the object instance on this frame.
                Defaults to the current SDK user.
            confidence: Optionally specify the confidence of the object instance on this frame. Defaults to `1.0`.
            manual_annotation: Optionally specify whether the object instance on this frame was manually annotated. Defaults to `True`.
            reviews: Should only be set by internal functions.
            is_deleted: Should only be set by internal functions.
            event_kind: Should only be set by internal functions.
        """
        if self._non_geometric:
            if not isinstance(coordinates, tuple(NON_GEOMETRIC_COORDINATES)):
                raise LabelRowError("Expecting non-geometric coordinate type")

            elif frames != 0:
                raise LabelRowError(
                    f"For objects with a non-geometric shape (e.g. {Shape.TEXT} and {Shape.AUDIO}), "
                    f"There is only one frame. Please ensure `set_for_frames` is called with `frames=0`."
                )

        self._check_not_event_based(
            "set_for_frames",
            "Labels are sparse events rather than per-frame entries; a keyframe is written with `upsert_event`.",
        )

        self._operation_not_allowed_for_objects_on_space(
            extended_message="For adding the object to different frames on a space, use Space.place_object."
        )

        self._set_for_frames(
            coordinates=coordinates,
            frames=frames,
            overwrite=overwrite,
            created_at=created_at,
            created_by=created_by,
            last_edited_at=last_edited_at,
            last_edited_by=last_edited_by,
            confidence=confidence,
            manual_annotation=manual_annotation,
            reviews=reviews,
            is_deleted=is_deleted,
            event_kind=event_kind,
        )

        if event_kind is None and self._has_event_tags():
            # A real (non-parsing) write of coordinates invalidates any `event` tag parsed onto this frame: the
            # row must not export freshly written geometry still labelled `event: "delete"`.
            #
            # Guarded, because this is a second expansion of `frames` on top of the one `_set_for_frames` just
            # did. Stored entries are sparse even on an event-based row, so the guard is cheap, and it skips the
            # pass outright on every row that has no tags to clear — which is every frame-based row.
            for frame in frames_class_to_frames_list(frames):
                frame_data = self._frames_to_instance_data.get(frame)
                if frame_data is not None:
                    frame_data.annotation_metadata.event_kind = None

    def _set_for_frames(
        self,
        coordinates: Coordinates,
        frames: Frames = 0,
        *,
        overwrite: bool = False,
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        last_edited_at: Optional[datetime] = None,
        last_edited_by: Optional[str] = None,
        confidence: Optional[float] = None,
        manual_annotation: Optional[bool] = None,
        reviews: Optional[List[dict]] = None,  # This field is deprecated. It will always be None.
        is_deleted: Optional[bool] = None,
        event_kind: Optional[EventKind] = None,
    ):
        """
        Used internally to set the frames on the object instance itself
        This is only when the object instance is NOT attached to a space.
        We also call this when we're detaching the object instance from a space,
        and therefore need to transfer frames data back to the object instance.
        """
        frames_list = frames_class_to_frames_list(frames)
        for frame in frames_list:
            existing_frame_data = self._frames_to_instance_data.get(frame)

            if overwrite is False and existing_frame_data is not None:
                raise LabelRowError(
                    "Cannot overwrite existing data for a frame. Set `overwrite` to `True` to overwrite."
                )

            check_coordinate_type(coordinates, self._ontology_object, self._parent)

            if isinstance(coordinates, (TextCoordinates, AudioCoordinates, TimeRangeCoordinates)):
                for non_geometric_range in coordinates.range:
                    self.check_within_range(non_geometric_range.end)
            else:
                self.check_within_range(frame)

            if existing_frame_data is None:
                if isinstance(coordinates, (TextCoordinates, AudioCoordinates, TimeRangeCoordinates)):
                    existing_frame_data = _RangeObjectAnnotationData(
                        annotation_metadata=_AnnotationMetadata(), range_manager=RangeManager()
                    )
                else:
                    # Note here we pretend HTML coordinates are geometric coordinates. To remove when we implement
                    # HTML space.
                    geometric_coordinates = cast(GeometricCoordinates, coordinates)
                    existing_frame_data = _GeometricAnnotationData(
                        coordinates=geometric_coordinates, annotation_metadata=_AnnotationMetadata()
                    )
                self._frames_to_instance_data[frame] = existing_frame_data

            existing_frame_data.annotation_metadata.update_from_optional_fields(
                created_at=created_at,
                created_by=created_by,
                last_edited_at=last_edited_at,
                last_edited_by=last_edited_by,
                confidence=confidence,
                manual_annotation=manual_annotation,
                is_deleted=is_deleted,
                reviews=reviews,
                event_kind=event_kind,
            )

            if isinstance(existing_frame_data, _GeometricAnnotationData):
                geometric_coordinates = cast(GeometricCoordinates, coordinates)
                existing_frame_data.coordinates = geometric_coordinates
            elif isinstance(existing_frame_data, _RangeObjectAnnotationData):
                non_geometric_coordinates = cast(
                    Union[TextCoordinates, AudioCoordinates, TimeRangeCoordinates], coordinates
                )

                # This is for backwards compatibility.
                # When set_for_frames is called for non_geometric objects, we replace the entire range, instead of simply adding to the range.
                existing_frame_data.range_manager.clear_ranges()
                existing_frame_data.range_manager.add_ranges(non_geometric_coordinates.range)

            if self._parent:
                self._parent.add_to_single_frame_to_hashes_map(self, frame)

    def _get_non_geometric_annotation(self) -> Optional[Annotation]:
        # Non-geometric annotations (e.g. Audio and Text) only have one frame.
        if 0 not in self._frames_to_instance_data:
            return None
        else:
            return self.get_annotation(0)

    def get_annotation(self, frame: Union[int, str] = 0) -> Annotation:
        """Get the annotation for the object instance on the specified frame.

        On an event-based label row this returns a read-only `ObjectInstance.ResolvedAnnotation` (see its
        `is_virtual` and `keyframe`) resolved from the keyframe holding over the frame; it raises where the
        object does not exist.

        Args:
            frame: Either the frame number or the image hash if the data type is an image or image group.
                Defaults to the first frame.

        Returns:
            Annotation: The annotation for the specified frame.

        Raises:
            LabelRowError: If the frame is not present in the label row.
        """
        self._operation_not_allowed_for_objects_on_space()

        if self._non_geometric and frame != 0:
            raise LabelRowError(
                'This annotation data for this object instance is stored on only one "frame". '
                "Use `get_annotation(0)` to get the frame data of the first frame."
            )

        if isinstance(frame, str):
            # TODO: this check should be consistent for both string and integer frames,
            #       but currently it is not possible due to the parsing logic
            if not self._parent:
                raise LabelRowError("Cannot get annotation for an object instance that is not assigned to a label row.")

            frame_num = self._parent.get_frame_number(frame)
            if frame_num is None:
                raise LabelRowError(f"Image hash {frame} is not present in the label row.")
        else:
            frame_num = frame

        if self._is_event_based():
            resolved = resolve_event_at(self._sorted_events(), frame_num)
            if resolved is None:
                raise LabelRowError(
                    f"The object does not exist at frame `{frame_num}` on this event-based label row: no upsert "
                    "holds over it. Use `get_ranges()` to see where the object is present."
                )
            return self.ResolvedAnnotation(self, frame_num, keyframe=resolved.frame)

        return self.Annotation(self, frame_num)

    def copy(self) -> ObjectInstance:
        """Create an exact copy of this ObjectInstance.

        The new copy will have a new object hash and will not be associated with any `LabelRowV2`.
        This is useful for adding the semantically same ObjectInstance to multiple `LabelRowV2`s.

        Returns:
            ObjectInstance: A new ObjectInstance that is a copy of the current instance.
        """
        ret = ObjectInstance(self._ontology_object)
        ret._frames_to_instance_data = deepcopy(self._frames_to_instance_data)
        ret._static_answer_map = deepcopy(self._static_answer_map)
        ret._dynamic_answer_manager = self._dynamic_answer_manager.copy()
        return ret

    def get_annotations(self) -> List[Annotation]:
        """Get all annotations for the object instance on all frames it has been placed on.

        Returns:
            List[Annotation]: A list of `ObjectInstance.Annotation` in order of available frames.

        Raises:
            LabelRowError: If the label row is event-based.
        """
        self._check_not_event_based(
            "get_annotations",
            "The object is present over ranges rather than on a list of frames, and its stored entries are "
            "keyframes and `delete` markers rather than annotations, so a marker would be reported as a label "
            "carrying zeroed geometry.",
        )

        if self._is_assigned_to_space():
            res: List[ObjectInstance.Annotation] = []
            for space in self._spaces.values():
                # We can cast here, because our ObjectAnnotation is built to mimic `ObjectInstance.Annotation`
                res.extend(
                    cast(
                        List[ObjectInstance.Annotation],
                        space._get_object_annotations(filter_object_instances=[self.object_hash]),
                    )
                )
            return res
        else:
            return [self.get_annotation(frame_num) for frame_num in sorted(self._frames_to_instance_data.keys())]

    def get_annotation_frames(self) -> set[int]:
        """Get all annotations for the object instance on all frames it has been placed on.

        Returns:
            List[Annotation]: A list of `ObjectInstance.Annotation` in order of available frames.

        Raises:
            LabelRowError: If the label row is event-based.
        """
        self._operation_not_allowed_for_objects_on_space()
        self._check_not_event_based(
            "get_annotation_frames",
            "The stored frames are keyframes and `delete` markers, so the answer would include the offset at "
            "which the object stops existing as one it is annotated on.",
        )

        return {self.get_annotation(frame_num).frame for frame_num in sorted(self._frames_to_instance_data.keys())}

    def remove_from_frames(self, frames: Frames) -> None:
        """Remove the object instance from the specified frames.

        Args:
            frames: The frames from which to remove the object instance.
        """
        if self._non_geometric and frames != 0:
            raise LabelRowError(
                f"For objects with a non-geometric shape (e.g. {Shape.TEXT} and {Shape.AUDIO}), "
                f"There is only one frame. Please ensure `remove_from_frames` is called with `frames=0`."
            )

        self._check_not_event_based(
            "remove_from_frames",
            "Labels are sparse events rather than per-frame entries; end the object with `delete_event` or erase "
            "a stored event with `remove_event`.",
        )

        self._operation_not_allowed_for_objects_on_space(
            extended_message="For removing the object from different frames on a space, use Space.unplace_object."
        )

        if self._is_assigned_to_space():
            raise LabelRowError(
                "This method is not allowed when the object instance already exists on a space. Instead use `Space.unplace_object`"
            )

        frames_list = frames_class_to_frames_list(frames)
        for frame in frames_list:
            self._frames_to_instance_data.pop(frame)

        if self._parent:
            self._parent._remove_from_frame_to_hashes_map(frames_list, self.object_hash)
            if len(self._frames_to_instance_data) == 0:
                del self._parent._objects_map[self.object_hash]

    def is_valid(self) -> None:
        """Check if the ObjectInstance is valid.

        Raises:
            LabelRowError: If the ObjectInstance is not on any frames.
        """
        if len(self._frames_to_instance_data) == 0:
            raise LabelRowError("ObjectInstance is not on any frames. Please add it to at least one frame.")

        self.are_dynamic_answers_valid()

    def are_dynamic_answers_valid(self) -> None:
        """Validate if there are any dynamic answers on frames that have no coordinates.

        Raises:
            LabelRowError: If there are dynamic answers on frames without coordinates.
        """
        self._operation_not_allowed_for_objects_on_space()
        self._check_dynamic_answers_within(self.get_ranges())

    def _check_dynamic_answers_within(self, ranges: Ranges) -> None:
        """Raise if any dynamic answer sits outside `ranges`, the frames the object has coordinates on."""
        answered = RangeManager(self._dynamic_answer_manager.answered_ranges())
        answered.remove_ranges(ranges)

        if answered.get_ranges():
            raise LabelRowError(
                "There are some dynamic answers on frames that have no coordinates. "
                "Please ensure that all the dynamic answers are only on frames where coordinates "
                "have been set previously."
            )

    class Annotation(_ObjectAnnotation):
        """
        Represents an annotation for a specific frame of an ObjectInstance.
        Allows setting or getting data for the ObjectInstance on the given frame number.
        This is deprecated, we will be using the ObjectAnnotation that this inherits from.
        """

        def __init__(self, object_instance: ObjectInstance, frame: int):
            self._object_instance = object_instance
            self._frame = frame

        @property
        def coordinates(self) -> Coordinates:
            self._check_if_annotation_is_valid()
            annotation_data = self._get_annotation_data()
            if isinstance(annotation_data, _GeometricAnnotationData):
                return annotation_data.coordinates
            elif isinstance(annotation_data, _RangeObjectAnnotationData):
                ranges = annotation_data.range_manager.get_ranges()
                if self._object_instance._ontology_object.shape == Shape.TEXT:
                    return TextCoordinates(range=ranges)
                elif self._object_instance._ontology_object.shape == Shape.AUDIO:
                    return AudioCoordinates(range=ranges)
                elif self._object_instance._ontology_object.shape == Shape.TIME_RANGE:
                    return TimeRangeCoordinates(range=ranges)
                else:
                    raise LabelRowError("No coordinates for this annotation.")
            else:
                raise LabelRowError("Invalid annotation data found.")

        @coordinates.setter
        def coordinates(self, coordinates: Coordinates) -> None:
            self._check_if_annotation_is_valid()
            self._object_instance.set_for_frames(coordinates, self._frame, overwrite=True)

        @property
        def space(self) -> Space:
            raise LabelRowError("This annotation does not exist on a space")

        @property
        def frame(self) -> int:
            return self._frame

        @property
        def reviews(self) -> Optional[List[Dict[str, Any]]]:
            self._check_if_annotation_is_valid()
            return self._get_annotation_data().annotation_metadata.reviews

        @property
        def is_deleted(self) -> Optional[bool]:
            """This is merely here for backwards compatibility.
            Returns:
                Optional[List[Dict[str, Any]]]: A list of review dictionaries, if any.
            """
            self._check_if_annotation_is_valid()
            return self._get_annotation_data().annotation_metadata.is_deleted

        def _get_annotation_data(self) -> _AnnotationData:
            return self._object_instance._frames_to_instance_data[self._frame]

        def _check_if_annotation_is_valid(self) -> None:
            if self._frame not in self._object_instance._frames_to_instance_data:
                raise LabelRowError(
                    "Trying to use an ObjectInstance.Annotation for an ObjectInstance that is not on the frame"
                )

    class ResolvedAnnotation(Annotation):
        """A read-only view of an object at a frame on an event-based label row.

        The view reads from the upsert keyframe holding over `frame`. `is_virtual` is `False` when an upsert is
        stored on exactly this frame and `True` when the frame inherits an earlier keyframe. Writes must go
        through `ObjectInstance.upsert_event`, `delete_event` and `remove_event`; every setter here raises.
        """

        _READ_ONLY_MESSAGE = (
            "This is a read-only resolved view on an event-based label row. "
            "Use `ObjectInstance.upsert_event(...)` to write a keyframe instead."
        )

        def __init__(self, object_instance: ObjectInstance, frame: int, *, keyframe: int):
            super().__init__(object_instance, frame)
            self._keyframe = keyframe

        @property
        def keyframe(self) -> int:
            """The frame of the stored upsert this view reads from."""
            return self._keyframe

        @property
        def is_virtual(self) -> bool:
            """True when no upsert is stored on exactly this frame and the view inherits an earlier keyframe."""
            return self._frame != self._keyframe

        def _get_annotation_data(self) -> _AnnotationData:
            return self._object_instance._frames_to_instance_data[self._keyframe]

        def _check_if_annotation_is_valid(self) -> None:
            if self._keyframe not in self._object_instance._frames_to_instance_data:
                raise LabelRowError("The keyframe this resolved view reads from no longer exists.")

        @property
        def coordinates(self) -> Coordinates:
            self._check_if_annotation_is_valid()
            return cast(_GeometricAnnotationData, self._get_annotation_data()).coordinates

        @coordinates.setter
        def coordinates(self, coordinates: Coordinates) -> None:
            raise LabelRowError(self._READ_ONLY_MESSAGE)

        @property
        def created_at(self) -> datetime:
            return super().created_at

        @created_at.setter
        def created_at(self, created_at: datetime) -> None:
            raise LabelRowError(self._READ_ONLY_MESSAGE)

        @property
        def created_by(self) -> Optional[str]:
            return super().created_by

        @created_by.setter
        def created_by(self, created_by: Optional[str]) -> None:
            raise LabelRowError(self._READ_ONLY_MESSAGE)

        @property
        def last_edited_at(self) -> datetime:
            return super().last_edited_at

        @last_edited_at.setter
        def last_edited_at(self, last_edited_at: datetime) -> None:
            raise LabelRowError(self._READ_ONLY_MESSAGE)

        @property
        def last_edited_by(self) -> Optional[str]:
            return super().last_edited_by

        @last_edited_by.setter
        def last_edited_by(self, last_edited_by: Optional[str]) -> None:
            raise LabelRowError(self._READ_ONLY_MESSAGE)

        @property
        def confidence(self) -> float:
            return super().confidence

        @confidence.setter
        def confidence(self, confidence: float) -> None:
            raise LabelRowError(self._READ_ONLY_MESSAGE)

        @property
        def manual_annotation(self) -> bool:
            return super().manual_annotation

        @manual_annotation.setter
        def manual_annotation(self, manual_annotation: bool) -> None:
            raise LabelRowError(self._READ_ONLY_MESSAGE)

    @dataclass
    class FrameData:
        """Data class for storing frame-specific data.

        Attributes:
            coordinates (Coordinates): The coordinates associated with the frame.
            annotation_metadata (_AnnotationMetadata): The frame's metadata information.
        """

        coordinates: Coordinates
        annotation_metadata: _AnnotationMetadata
        # Probably the above can be flattened out into this class.

    def _set_answer_unsafe(
        self,
        answer: Union[str, NumericAnswerValue, Option, Iterable[Option]],
        attribute: Attribute,
        ranges: Optional[Ranges],
    ) -> None:
        if attribute.dynamic:
            frames = sorted(self._frames_to_instance_data.keys()) if ranges is None else ranges

            self._dynamic_answer_manager._set_answer(answer, attribute, frames=frames)
        else:
            static_answer = self._static_answer_map[attribute.feature_node_hash]
            static_answer.set(answer)

    def _set_answer_from_dict(self, answer_dict: AttributeDict | DynamicAttributeObject, attribute: Attribute) -> None:
        if attribute.dynamic:
            dynamic_answer_dict = cast(DynamicAttributeObject, answer_dict)
            ranges = ranges_list_to_ranges(dynamic_answer_dict["range"])
        else:
            ranges = None

        answers = answer_dict["answers"]
        if isinstance(attribute, TextAttribute):
            text_answer = cast(str, answers)
            self._set_answer_unsafe(text_answer, attribute, ranges)
        elif isinstance(attribute, RadioAttribute):
            radio_option_answers = cast(List[AnswerDict], answers)
            if len(radio_option_answers) == 1:
                feature_hash = radio_option_answers[0]["featureHash"]
                option = attribute.get_child_by_hash(feature_hash, type_=Option)
                self._set_answer_unsafe(option, attribute, ranges)
        elif isinstance(attribute, ChecklistAttribute):
            checklist_answers = cast(List[AnswerDict], answers)
            options = []
            for answer in checklist_answers:
                feature_hash = answer["featureHash"]
                option = attribute.get_child_by_hash(feature_hash, type_=Option)
                options.append(option)

            self._set_answer_unsafe(options, attribute, ranges)

        elif isinstance(attribute, NumericAttribute):
            value = cast(float, answer_dict["answers"])

            if not isinstance(value, float) and not isinstance(value, int):
                raise LabelRowError(f"The answer for a numeric attribute must be a float or an int. Found {value}.")

            self._set_answer_unsafe(value, attribute, ranges)
        else:
            raise NotImplementedError(f"The attribute type {type(attribute)} is not supported.")

    def _is_attribute_valid_child_of_object_instance(self, attribute: Attribute) -> bool:
        is_static_child = attribute.feature_node_hash in self._static_answer_map
        is_dynamic_child = self._dynamic_answer_manager.is_valid_dynamic_attribute(attribute)
        return is_dynamic_child or is_static_child

    def _is_selectable_child_attribute(self, attribute: Attribute) -> bool:
        ontology_object = self._ontology_object
        for search_attribute in ontology_object.attributes:
            if search_attribute.dynamic:
                continue

            if _search_child_attributes(attribute, search_attribute, self._static_answer_map):
                return True
        return False

    def _get_all_static_answers(self) -> List[Answer]:
        return list(self._static_answer_map.values())

    def _get_all_dynamic_answers(self) -> List[Tuple[Answer, Ranges]]:
        return self._dynamic_answer_manager.get_all_answers()

    def __repr__(self) -> str:
        return (
            f"ObjectInstance(object_hash={self._object_hash}, object_name={self._ontology_object.name}, "
            f"feature_hash={self._ontology_object.feature_node_hash})"
        )

    def __hash__(self) -> int:
        return hash(id(self))

    def __lt__(self, other: ObjectInstance) -> bool:
        return self._object_hash < other._object_hash


def check_coordinate_type(coordinates: Coordinates, ontology_object: Object, parent: Optional[LabelRowV2]) -> None:
    """Check if the coordinate type matches the expected type for the ontology object.

    Args:
        coordinates (Coordinates): The coordinates to check.
        ontology_object (Object): The ontology object to check against.
        parent (LabelRowV2): The parent label row (if any) of the ontology object.

    Raises:
        LabelRowError: If the coordinate type does not match the expected type.
    """
    expected_coordinate_types = ACCEPTABLE_COORDINATES_FOR_ONTOLOGY_ITEMS[ontology_object.shape]
    if all(
        not isinstance(coordinates, expected_coordinate_type) for expected_coordinate_type in expected_coordinate_types
    ):
        raise LabelRowError(
            f"Expected coordinates of one of the following types: `{expected_coordinate_types}`, but got type `{type(coordinates)}`."
        )

    # An ontology object with `Text` shape can have both coordinates `HtmlCoordinates` and `TextCoordinates`
    # Therefore, we need to further check the file type, to ensure that `HtmlCoordinates` are only used for
    # HTML files, and `TextCoordinates` are only used for plain text files.
    if isinstance(coordinates, TextCoordinates):
        if parent is not None and parent.file_type == "text/html":
            raise LabelRowError(f"Expected coordinates of type {HtmlCoordinates}`, but got type `{type(coordinates)}`.")
    elif isinstance(coordinates, HtmlCoordinates):
        if parent is not None and parent.file_type != "text/html":
            raise LabelRowError(
                "For non-html labels, ensure the `range` property is set when instantiating the TextCoordinates."
            )


class AnswerRangeIndex:
    """Internal range storage for dynamic answers, preserving global answer insertion order.

    The attribute index contains sorted, non-overlapping intervals. The answer index
    maps interval starts to ends so replacing a fragment does not shift a sorted list.
    All mutations update both indexes together.
    """

    def __init__(self) -> None:
        self._answers_to_ranges: Dict[Answer, Dict[int, int]] = {}
        self._ranges_by_attribute: Dict[str, List[Tuple[int, int, Answer]]] = {}

    def assign(self, answer: Answer, ranges: Ranges) -> None:
        """Assign an answer over ranges, replacing overlaps and merging equal neighbors."""
        ranges = RangeManager(ranges).get_ranges()
        if not ranges:
            return
        attribute = answer.ontology_attribute

        # Replace a complete interval in place to avoid shifting the index twice per point edit.
        replace_in_place = False
        intervals = self._ranges_by_attribute.get(attribute.feature_node_hash, [])
        if len(ranges) == 1:
            range_ = ranges[0]
            index = bisect_left(intervals, (range_.start,))
            if index < len(intervals):
                start, end, previous_answer = intervals[index]
                if start == range_.start and end == range_.end and previous_answer.ontology_attribute == attribute:
                    replace_in_place = True
                    previous_ranges = self._answers_to_ranges[previous_answer]
                    del previous_ranges[start]
                    if not previous_ranges:
                        del self._answers_to_ranges[previous_answer]
        if not replace_in_place:
            self.remove(attribute, ranges)

        answer_ranges = self._answers_to_ranges.setdefault(answer, {})
        intervals = self._ranges_by_attribute.setdefault(attribute.feature_node_hash, [])
        for range_ in ranges:
            first = last = bisect_left(intervals, (range_.start,))
            if replace_in_place:
                last += 1
            start, end = range_.start, range_.end
            if first > 0 and intervals[first - 1][1] == start - 1 and intervals[first - 1][2] == answer:
                first -= 1
                start = intervals[first][0]
                del answer_ranges[start]
            if last < len(intervals) and intervals[last][0] == end + 1 and intervals[last][2] == answer:
                del answer_ranges[intervals[last][0]]
                end = intervals[last][1]
                last += 1
            answer_ranges[start] = end
            intervals[first:last] = [(start, end, answer)]

    def remove(
        self,
        attribute: Attribute,
        ranges: Optional[Ranges] = None,
        filter_answer: Union[str, NumericAnswerValue, Option, Iterable[Option], None] = None,
    ) -> None:
        """Remove matching answers on selected ranges, or throughout the attribute when omitted."""
        intervals = self._ranges_by_attribute.get(attribute.feature_node_hash)
        if not intervals:
            return
        if ranges is None:
            ranges = [Range(intervals[0][0], intervals[-1][1])]
        for range_ in ranges:
            if range_.start > range_.end:
                continue
            first, last = self._overlap_bounds(intervals, range_)
            remaining = []
            for start, end, answer in intervals[first:last]:
                if answer.ontology_attribute != attribute or (
                    filter_answer is not None and answer.is_answered() and answer.get() != filter_answer
                ):
                    remaining.append((start, end, answer))
                    continue
                answer_ranges = self._answers_to_ranges[answer]
                del answer_ranges[start]
                if start < range_.start:
                    remaining.append((start, range_.start - 1, answer))
                    answer_ranges[start] = range_.start - 1
                if end > range_.end:
                    remaining.append((range_.end + 1, end, answer))
                    answer_ranges[range_.end + 1] = end
                if not answer_ranges:
                    del self._answers_to_ranges[answer]
            intervals[first:last] = remaining
        if not intervals:
            del self._ranges_by_attribute[attribute.feature_node_hash]

    def overlapping(self, attribute: Attribute, ranges: Ranges) -> Set[Answer]:
        """Find answers whose intervals overlap any selected range."""
        matching_answers: Set[Answer] = set()
        intervals = self._ranges_by_attribute.get(attribute.feature_node_hash, [])
        for range_ in ranges:
            if range_.start > range_.end:
                continue
            first, last = self._overlap_bounds(intervals, range_)
            matching_answers.update(answer for _, _, answer in intervals[first:last])
        return matching_answers

    @staticmethod
    def _overlap_bounds(intervals: List[Tuple[int, int, Answer]], range_: Range) -> Tuple[int, int]:
        first = bisect_left(intervals, (range_.start,))
        if first > 0 and intervals[first - 1][1] >= range_.start:
            first -= 1
        last = bisect_left(intervals, (range_.end + 1,))
        return first, last

    def answers(self) -> Iterable[Answer]:
        """Iterate answers in insertion order across all attributes."""
        return self._answers_to_ranges.keys()

    def ranges_for(self, answer: Answer) -> Ranges:
        """Return independent, sorted ranges for a stored answer."""
        return [Range(start, end) for start, end in sorted(self._answers_to_ranges[answer].items())]

    def answered_ranges(self) -> Ranges:
        """Return the merged coverage of every stored answer."""
        merged = RangeManager()
        # Merge in frame order to avoid repeatedly shifting interleaved answer fragments.
        intervals = sorted(
            interval for answer_ranges in self._answers_to_ranges.values() for interval in answer_ranges.items()
        )
        merged.add_ranges([Range(start, end) for start, end in intervals])
        return merged.get_ranges()

    def copy(self) -> AnswerRangeIndex:
        """Copy both indexes together so they share the same copied answer objects."""
        ret = AnswerRangeIndex()
        ret._answers_to_ranges, ret._ranges_by_attribute = deepcopy(
            (self._answers_to_ranges, self._ranges_by_attribute)
        )
        return ret

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AnswerRangeIndex):
            return False
        return self._answers_to_ranges == other._answers_to_ranges


class DynamicAnswerManager:
    """Manages dynamic answers for different frames of an ObjectInstance.

    This class is an internal helper class and should not be interacted with directly by the user.
    """

    def __init__(self, object_instance: ObjectInstance):
        self._object_instance = object_instance
        self._range_index = AnswerRangeIndex()
        # Unanswered templates used to validate which dynamic attributes belong to this object.
        self._dynamic_uninitialised_answer_options: Set[Answer] = self._get_dynamic_answers()

    def is_valid_dynamic_attribute(self, attribute: Attribute) -> bool:
        """Check if the attribute is a valid dynamic attribute.

        Args:
            attribute (Attribute): The attribute to check.

        Returns:
            bool: True if the attribute is valid, False otherwise.
        """
        return any(
            answer.ontology_attribute.feature_node_hash == attribute.feature_node_hash
            for answer in self._dynamic_uninitialised_answer_options
        )

    def delete_answer(
        self,
        attribute: Attribute,
        frames: Optional[Frames] = None,
        filter_answer: Union[str, Option, Iterable[Option], None] = None,
    ) -> None:
        """Delete the answer for a given attribute and frames.

        Args:
            attribute (Attribute): The attribute to delete the answer for.
            frames (Optional[Frames]): The frames to delete the answer for.
            filter_answer (Union[str, Option, Iterable[Option], None]): The specific answer to delete.
        """
        ranges = None if frames is None else frames_class_to_ranges(frames)
        self._range_index.remove(attribute, ranges, filter_answer)

    def set_answer(
        self,
        answer: Union[str, NumericAnswerValue, Option, Iterable[Option]],
        attribute: Attribute,
        frames: Optional[Frames] = None,
    ) -> None:
        """Set the answer for a given attribute and frames.

        Args:
            answer (Union[str, Option, Iterable[Option]]): The answer to set.
            attribute (Attribute): The attribute to set the answer for.
            frames (Optional[Frames]): The frames to set the answer for.
        """
        if frames is None:
            if self._object_instance._is_event_based():
                # Everywhere the object has coordinates: the stretches its upserts hold over, not the keyframes.
                self._set_answer(answer, attribute, self._object_instance.get_ranges())
            else:
                # Preserve dense update order, including the insertion order of serialized answers.
                for annotation in self._object_instance.get_annotations():
                    self._set_answer(answer, attribute, annotation.frame)
            return
        self._set_answer(answer, attribute, frames)

    def _set_answer(
        self,
        answer: Union[str, NumericAnswerValue, Option, Iterable[Option]],
        attribute: Attribute,
        frames: Frames,
    ) -> None:
        # Validate every range before deleting anything, including later entries in a range list.
        ranges = sorted(frames_class_to_ranges(frames), key=lambda range_: range_.start)
        for range_ in ranges:
            self._object_instance.check_within_range(range_.start)
            # Report the first invalid frame, as the expanded-frame implementation did.
            end = min(range_.end, self._object_instance._last_frame)
            self._object_instance.check_within_range(cast(int, end))

        default_answer = get_default_answer_from_attribute(attribute)
        try:
            default_answer.set(answer)
        except Exception:
            # Preserve the existing deletion-before-answer-validation behavior on failed writes.
            self.delete_answer(attribute, ranges)
            raise

        self._range_index.assign(default_answer, ranges)

    def get_answer(
        self,
        attribute: Attribute,
        filter_answer: Union[str, NumericAnswerValue, Option, Iterable[Option], None] = None,
        filter_frames: Optional[Frames] = None,
    ) -> AnswersForFrames:
        """Get answers for a given attribute, filtered by the specified criteria.

        Args:
            attribute (Attribute): The attribute to get the answers for.
            filter_answer (Union[str, Option, Iterable[Option], None]): The specific answer to filter by.
            filter_frames (Optional[Frames]): The specific frames to filter by.

        Returns:
            AnswersForFrames: A list of answers and their associated frames.
        """
        ret = []
        filter_ranges = None if filter_frames is None else frames_class_to_ranges(filter_frames)
        matching_answers = None if filter_ranges is None else self._range_index.overlapping(attribute, filter_ranges)
        for answer in self._range_index.answers():
            if answer.ontology_attribute != attribute:
                continue
            if not answer.is_answered():
                continue
            if not (filter_answer is None or filter_answer == answer.get()):
                continue
            # Filters select whole answers whose ranges overlap, without clipping the returned ranges.
            if matching_answers is not None and answer not in matching_answers:
                continue

            ranges = self._range_index.ranges_for(answer)
            ret.append(AnswerForFrames(answer=answer.get(), ranges=ranges))
        return ret

    def answered_ranges(self) -> Ranges:
        """Get the ranges that have answers set, merged across every answer."""
        return self._range_index.answered_ranges()

    def get_all_answers(self) -> List[Tuple[Answer, Ranges]]:
        """Get all answers that are set.

        Returns:
            List[Tuple[Answer, Ranges]]: A list of tuples containing the answer and its associated ranges.
        """
        return [(answer, self._range_index.ranges_for(answer)) for answer in self._range_index.answers()]

    def copy(self) -> DynamicAnswerManager:
        """Create a deep copy of the DynamicAnswerManager instance.

        Returns:
            DynamicAnswerManager: A new instance of DynamicAnswerManager with copied data.
        """
        ret = DynamicAnswerManager(self._object_instance)
        ret._range_index = self._range_index.copy()
        return ret

    def _get_dynamic_answers(self) -> Set[Answer]:
        ret: Set[Answer] = set()
        for attribute in self._object_instance.ontology_item.attributes:
            if attribute.dynamic:
                answer = get_default_answer_from_attribute(attribute)
                ret.add(answer)
        return ret

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DynamicAnswerManager):
            return False
        return self._range_index == other._range_index

    def __hash__(self) -> int:
        return hash(id(self))


@dataclass
class AnswerForFrames:
    """Data class for storing an answer and its associated frame ranges.

    Attributes:
        answer (Union[str, Option, Iterable[Option]]): The answer set for the frames.
        ranges (Ranges): The ranges representing the frames where the answer is set.

    The ranges are essentially a run-length encoding of the frames where the unique answer is set.
    They are sorted in ascending order.
    """

    answer: Union[str, Option, Iterable[Option]]
    ranges: Ranges


AnswersForFrames = List[AnswerForFrames]
"""
A list of AnswerForFrames objects, representing answers and their associated frame ranges.
"""
