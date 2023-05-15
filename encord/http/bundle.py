import logging
from typing import Callable, TypeVar, Optional, List, Dict, Tuple, Generic, Generator
from dataclasses import asdict, dataclass, field
from functools import reduce

log = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BundleResultHandler(Generic[T]):
    predicate: str
    handler: Callable[[T], None]


@dataclass
class BundleResultMapper(Generic[T]):
    mapping_function: Callable[[T], str]
    result_handler: BundleResultHandler[T]


@dataclass
class BundledOperation(Generic[T, R]):
    operation: Callable[..., List[R]]
    reducer: Callable[[T, T], T]
    mapper: Optional[Callable[[R], str]]
    limit: int
    payloads: List[T] = field(default_factory=lambda: [])
    result_handlers: Dict[str, Callable[[T], None]] = field(default_factory=lambda: dict())

    def append(self, payload: T, result_handler: Optional[BundleResultHandler]):
        self.payloads.append(payload)
        if result_handler is not None:
            self.result_handlers[result_handler.predicate] = result_handler.handler

    def get_bundled_payload(self) -> Generator[T, None, None]:
        for i in range(0, len(self.payloads), self.limit):
            yield reduce(self.reducer, self.payloads[i : i + self.limit])


class Bundle:
    """
    This class allows to perform operations in bundles to improve performance by reducing number of network calls.

    It is not supposed to be instantiated directly by a user. Use :meth:`encord.project.Project.create_bundle()`
    method to initiate bundled operations.

    To execute batch you can either call  :meth:`.execute()` directly, or use a Context Manager.

        .. code::

                # Code example of performing batched label initialisation
                project = ... # assuming you already have instantiated this Project object
                label_rows = project.list_label_rows_v2()
                bundle = project.create_bundle()
                for label_row in label_rows:
                    label_row.initialise_labels(bundle=bundle)
                    # no real network operations happened at this point

                # now, trigger the actual network interaction
                bundle.execute()

                # all labels are initialised at this point


        And this is the same flow with the Context Manager approach:

        .. code::

                # Code example of performing batched label initialisation
                project = ... # assuming you already have instantiated this Project object
                label_rows = project.list_label_rows_v2()
                with project.create_bundle() as bundle:
                    for label_row in label_rows:
                        label_row.initialise_labels(bundle=bundle)
                        # no real network operations happened at this point

                # At this point all labels will be initialised
    """

    def __init__(self) -> None:
        self._operations: Dict[Callable, BundledOperation] = dict()

    def __register_operation(
        self,
        operation: Callable[..., List[R]],
        reducer: Callable[[T, T], T],
        mapper: Optional[Callable[[R], str]],
        limit: int,
    ) -> BundledOperation[T, R]:
        if operation not in self._operations:
            self._operations[operation] = BundledOperation(operation, reducer, mapper, limit)

        return self._operations[operation]

    def add(
        self,
        operation: Callable[..., List[R]],
        request_reducer: Callable[[T, T], T],
        result_mapper: Optional[BundleResultMapper[R]],
        payload: T,
        limit: int,
    ) -> None:
        """
        This is an internal method and normally is not supposed to be used externally.

        Adds an operation to a bundle for delayed execution.
        """
        mapping_function = result_mapper.mapping_function if result_mapper is not None else None
        result_handler = result_mapper.result_handler if result_mapper is not None else None
        self.__register_operation(operation, request_reducer, mapping_function, limit).append(payload, result_handler)

    def execute(self) -> None:
        """
        Executes all scheduled operations in bundles and populates results
        """

        for operation in self._operations.values():
            for bundled_payload in operation.get_bundled_payload():
                bundle_result = operation.operation(**asdict(bundled_payload))

                if operation.mapper is not None:
                    for br in bundle_result:
                        result_handler = operation.result_handlers.get(operation.mapper(br))
                        if result_handler is not None:
                            result_handler(br)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            log.warning(f"Cancelling operation due to exception: {exc_type.__name__}")
        else:
            self.execute()