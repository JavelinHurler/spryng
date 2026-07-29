from dataclasses import dataclass

from spryng.application.decorator import ClassDecoration, decorate


@dataclass
class GrpcHandlerDecoration(ClassDecoration):
    host: str
    port: int
    max_workers: int


def grpc_handler(host: str, port: int, max_workers: int):
    def decorator(clazz):
        decorator_func = decorate(
            GrpcHandlerDecoration(
                host=host,
                port=port,
                max_workers=max_workers
            )
        )

        decorator_func(clazz)

        return clazz

    return decorator
