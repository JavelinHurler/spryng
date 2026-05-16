from dataclasses import dataclass

from spryng.application.decorator import FunctionDecoration, ClassDecoration, decorate
from spryng_web.models import ErrorHandlerDefinition, RouteDefinition


@dataclass
class ControllerDecoration(ClassDecoration):
    base_path: str | None


class RouteDecoration(FunctionDecoration):
    route_definition: RouteDefinition

    def __init__(self, method: str, path: str):
        self.route_definition = RouteDefinition(method=method, path=path)


class ErrorHandlerDecoration(FunctionDecoration):
   error_handler_definition: ErrorHandlerDefinition

   def __init__(self, exception_types: set[type[Exception]]):
       self.error_handler_definition = ErrorHandlerDefinition(exception_types=exception_types)


def controller(base_path: str):
    def decorator(clazz):
        decorator_func = decorate(ControllerDecoration(base_path=base_path))

        decorator_func(clazz)

        return clazz

    return decorator


def route(method: str, path: str):
    def decorator(func):
        decorator_func = decorate(RouteDecoration(method, path))

        decorator_func(func)

        return func

    return decorator


def error_handler(exception_types: set[type[Exception]]):
    def decorator(func):
        decorator_func = decorate(ErrorHandlerDecoration(exception_types=exception_types))

        decorator_func(func)

        return func

    return decorator
