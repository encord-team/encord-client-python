import dataclasses
import logging
from typing import Callable

log = logging.getLogger(__name__)


class BatchMapper:
    def __init__(self, mapper_predicate: str, continuation: Callable):
        self.key = mapper_predicate
        self.continuation = continuation


class Batch:
    def __init__(self):
        self._active = False
        self._requests = {}
        self._mappers = {}
        self._continuations = {}

    def add(self, batch_op, mapper, reducer, **kwargs) -> None:
        self._active = True
        payload, continuation = reducer(self._requests.get(batch_op, None), kwargs)
        self._mappers[batch_op] = mapper
        self._requests[batch_op] = payload
        self._continuations[batch_op] = (self._continuations.get(batch_op, [])) + [continuation]

    def execute(self) -> None:
        for op, kwargs in self._requests.items():
            result = op(**dataclasses.asdict(kwargs))

            if self._mappers[op] is not None:
                mapped_results = {self._mappers[op](entry): entry for entry in result}
                for cont in self._continuations[op]:
                    assert cont.key in mapped_results
                    cont.continuation(mapped_results[cont.key])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            log.warning(f"Cancelling operation due to exception: {exc_type.__name__}")
        else:
            if self._active:
                self.execute()
