from http import HTTPStatus

class ResponseConvertable:
    def get_bytes(self) -> list[bytes]:
        pass

    def get_length(self) -> int:
        pass

    def get_content_type(self) -> str:
        pass


class StringResponse(ResponseConvertable):
    response: bytes

    def __init__(self, response: str):
        self.response = response.encode("utf-8")

    def get_bytes(self) -> list[bytes]:
        return [self.response]

    def get_length(self):
        return len(self.response)

    def get_content_type(self):
        return "text/plain"


class ResponseHolder:
    status: HTTPStatus
    body: ResponseConvertable
    headers: dict[str, str]

    def __init__(
            self,
            body: ResponseConvertable | str | int | bool | float,
            status: HTTPStatus = HTTPStatus.OK,
            headers=None
    ):
        if isinstance(body, str):
            self.body = StringResponse(body)
        elif isinstance(body, (int, float, bool)):
            self.body = StringResponse(str(body))
        else:
            self.body = body

        self.status = status
        self.headers = headers if headers is not None else {}


        self.headers["Content-Length"] = str(self.body.get_length())
        self.headers["Content-Type"] = self.body.get_content_type()
