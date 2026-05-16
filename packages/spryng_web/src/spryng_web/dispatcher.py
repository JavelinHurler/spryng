from http import HTTPStatus
from typing import Optional

from spryng.logging import LoggerManager, Logger
from spryng.models.injection_types import ListInjection

from spryng_web.response import StringResponse, ResponseHolder
from spryng_web.request import RequestHolder
from spryng_web.models import Handler

class RequestDispatcher:
    def dispatch(self, method, path, query, headers, request_body) -> ResponseHolder:
        pass


@LoggerManager.decorate
class DefaultRequestDispatcher(RequestDispatcher):
    log: Logger

    def __init__(self, handlers: ListInjection[Handler]):
        self.handlers = handlers.values

    def find_handler(self, request_holder: RequestHolder) -> Optional[Handler]:
        for handler in self.handlers:
            if handler.matcher.match(request_holder):
                return handler

        return None

    def dispatch(self, method, path, query, headers, request_body) -> ResponseHolder:
        request_holder = RequestHolder(method, path, query, headers, request_body)

        handler = self.find_handler(request_holder=request_holder)

        if handler is None:
            self.log.error(f"'{method}' '{path}' '{query}' - no handler found")
            return ResponseHolder(StringResponse("The request could not be processed"), HTTPStatus.NOT_FOUND, {})

        try:
            result = handler.method(handler.instance, request_holder)
        except Exception as error:
            correct_error_handler = None
            for error_handler in handler.error_handlers:
                if error.__class__ in error_handler.definition.exception_types:
                    correct_error_handler = error_handler
                    break

            if correct_error_handler is None:
                raise error

            result = correct_error_handler.func(handler.instance, request_holder, error)

        if not isinstance(result, ResponseHolder):
            raise Exception(
                f"Expected Response Holder, got {type(result)}. Handler wrongly implemented. "
                f"{handler.instance.__class__.__module__}.{handler.instance.__class__.__name__}."
                f"{handler.method.__name__}"
            )

        self.log.info(f"{method} {path} {query} - {result.status.value}")

        return result
