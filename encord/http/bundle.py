"""
---
title: "Bundle (Batch)"
slug: "sdk-ref-bundle"
hidden: false
metadata:
  title: "Bundle"
  description: "Encord SDK Bundle (Batch)."
category: "64e481b57b6027003f20aaa0"
---
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, is_dataclass
from functools import reduce
from typing import Callable, ClassVar, Dict, Generic, List, Optional, Protocol, Type, TypeVar
from collections.abc import Iterator

from encord.http.limits import LABEL_ROW_BUNDLE_DEFAULT_LIMIT

log = logging.getLogger(__name__)

BundlablePayloadT = TypeVar("BundlablePayloadT", bound="BundlablePayload")


class BundlablePayload(Protocol[BundlablePayloadT]):
    """
    All payloads that work with bundles need to provide "add" method
    that would allow bundler to combine multiple payloads into one or few aggregates.
    """

    # This line ensures we're only allowing dataclasses for now
    __dataclass_fields__: ClassVar[dict]

    def add(self, other: BundlablePayloadT) -> BundlablePayloadT: ...


T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BundleResultHandler(Generic[T]):
    predicate: str
    handler: Callable[[T], None]


@dataclass
class BundleResultMapper(Generic[T]):
    result_mapping_predicate: Callable[[T], str]
    result_handler: BundleResultHandler[T]


class BundledOperation(Generic[BundlablePayloadT, R]):
    def __init__(
        self,
        operation: Callable[..., list[R]],
        result_mapper: Callable[[R], str] | None,
        limit: int,
    ) -> None:
        self.operation = operation
        self.result_mapper = result_mapper
        self.limit = limit
        self.payloads: list[BundlablePayloadT] = []
        self.result_handlers: dict[str, Callable[[BundlablePayloadT], None]] = {}

    def append(self, payload: BundlablePayloadT, result_handler: BundleResultHandler | None):
        self.payloads.append(payload)
        if result_handler is not None:
            self.result_handlers[result_handler.predicate] = result_handler.handler

    def get_bundled_payload(self) -> Iterator[BundlablePayloadT]:
        for i in range(0, len(self.payloads), self.limit):
            yield reduce(lambda x, y: x.add(y), self.payloads[i : i + self.limit])


class Bundle:
    """
    This class allows to perform operations in bundles to improve performance by reducing number of network calls.

    It is not supposed to be instantiated directly by a user. Use :meth:`encord.project.Project.create_bundle()`
    method to initiate bundled operations.

    To execute batch you can either call  :meth:`.execute()` directly, or use a Context Manager.
    """

    def __init__(self, bundle_size: int | None = None) -> None:
        self._bundle_size = bundle_size
        self._operations: dict[Callable, BundledOperation] = {}

    def __register_operation(
        self,
        payload_type: type[BundlablePayloadT],
        operation: Callable[..., list[R]],
        result_mapping_predicate: Callable[[R], str] | None,
        limit: int,
    ) -> BundledOperation[BundlablePayloadT, R]:
        if operation not in self._operations:
            self._operations[operation] = BundledOperation[BundlablePayloadT, R](
                operation, result_mapping_predicate, limit
            )

        return self._operations[operation]

    def add(
        self,
        operation: Callable[..., list[R]],
        result_mapper: BundleResultMapper[R] | None,
        payload: BundlablePayloadT,
        limit: int,
    ) -> None:
        """
        This is an internal method and normally is not supposed to be used externally.

        Adds an operation to a bundle for delayed execution.
        """
        result_mapping_getter = result_mapper.result_mapping_predicate if result_mapper else None
        result_handler = result_mapper.result_handler if result_mapper else None
        self.__register_operation(type(payload), operation, result_mapping_getter, self._bundle_size or limit).append(
            payload, result_handler
        )

    def execute(self) -> None:
        """
        Executes all scheduled operations in bundles and populates results
        """

        for operation in self._operations.values():
            for bundled_payload in operation.get_bundled_payload():
                bundle_result = operation.operation(**asdict(bundled_payload))

                if operation.result_mapper is not None:
                    for br in bundle_result:
                        result_handler = operation.result_handlers.get(operation.result_mapper(br))
                        if result_handler is not None:
                            result_handler(br)
        self._operations = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            log.warning(f"Cancelling operation due to exception: {exc_type.__name__}")
        else:
            self.execute()


def bundled_operation(
    bundle,
    operation,
    payload: BundlablePayloadT,
    result_mapper: BundleResultMapper | None = None,
    limit: int = LABEL_ROW_BUNDLE_DEFAULT_LIMIT,
) -> None:
    assert is_dataclass(payload), "Bundling only works with dataclasses"
    if not bundle:
        result = operation(**asdict(payload))
        if result_mapper:
            assert len(result) == 1, f"Expected a singular response for a singular request, got {len(result)} items!"
            assert result_mapper.result_mapping_predicate(result[0]) == result_mapper.result_handler.predicate
            result_mapper.result_handler.handler(result[0])
    else:
        bundle.add(
            operation=operation,
            result_mapper=result_mapper,
            payload=payload,
            limit=limit,
        )
