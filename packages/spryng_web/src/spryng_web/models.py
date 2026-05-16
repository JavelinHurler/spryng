from dataclasses import dataclass
from typing import Callable

from spryng_web.request import RequestHolder


@dataclass
class ErrorHandlerDefinition:
    exception_types: set[type[Exception]]


@dataclass
class ErrorHandlerConfig:
    definition: ErrorHandlerDefinition
    func: Callable


@dataclass
class RouteDefinition:
    method: str
    path: str

    def with_base_path(self, base_path: str | None) -> 'RouteDefinition':
        if base_path is None or base_path == "":
            return self

        return RouteDefinition(
            method=self.method,
            path=base_path + self.path,
        )

    def match(self, request: RequestHolder) -> bool:
        return request.method == self.method and request.path == self.path


@dataclass
class Handler:
    instance: object
    method: Callable
    matcher: RouteDefinition
    error_handlers: list[ErrorHandlerConfig]

