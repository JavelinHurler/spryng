from grpc import StatusCode


class GrpcError(Exception):
    status_code: StatusCode
    details: str

    def __init__(self, status_code: StatusCode, details: str):
        self.status_code = status_code
        self.details = details