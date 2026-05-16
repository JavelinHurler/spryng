from typing import Any
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
from wsgiref.types import StartResponse

from spryng.logging import LoggerManager, Logger
from spryng_web.dispatcher import RequestDispatcher


@LoggerManager.decorate
class Server:
    log: Logger

    def __init__(self, dispatcher: RequestDispatcher):
        self.dispatcher = dispatcher

    def __call__(self, environ, start_response):
        return self.handle(environ, start_response)

    def handle(self, environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
        method = environ["REQUEST_METHOD"]
        path = environ["PATH_INFO"]
        query = parse_qs(environ.get("QUERY_STRING"))
        headers = extract_request_headers(environ)
        request_body = extract_request_body(environ)

        try:
            response_holder = self.dispatcher.dispatch(method, path, query, headers, request_body)
        except Exception as e:
            self.log.error(f"{method} {path} {query} - {e}")
            start_response("500 Internal Server Error", [])
            return []

        start_response(
            f"{response_holder.status.value} {response_holder.status.phrase}",
            list(response_holder.headers.items())
        )

        return response_holder.body.get_bytes()


    def start_dev(self, host, port):
        server = make_server(
            host=host,
            port=port,
            app=self.handle,
        )

        self.log.info(f"Starting server on {host}:{port}")

        server.serve_forever()


def extract_request_body(environ) -> bytes:
    content_length = environ.get("CONTENT_LENGTH")
    length = int(content_length) if content_length else 0
    request_body = environ["wsgi.input"].read(length) if length > 0 else b""
    return request_body


def extract_request_headers(environ) -> dict[str, str]:
    headers = {
        key[5:].replace("_", "-").lower(): value
        for key, value in environ.items()
        if key.startswith("HTTP_")
    }

    if "CONTENT_TYPE" in environ:
        headers["content-type"] = environ["CONTENT_TYPE"]
    if "CONTENT_LENGTH" in environ:
        headers["content-length"] = environ["CONTENT_LENGTH"]

    return headers
