from dataclasses import dataclass

from spryng.application.decorator import ClassDecoration, decorate, FunctionDecoration


@dataclass
class GrpcHandlerDecoration(ClassDecoration):
    host: str
    port: int
    max_workers: int


@dataclass
class GrpcHandlerErrorHandlerDecoration(FunctionDecoration):
    errors: list[type[Exception]]


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


def grpc_error_handler(errors: list[type[Exception]]):
    def decorator(clazz):
        decorator_func = decorate(
            GrpcHandlerErrorHandlerDecoration(
                errors=errors
            )
        )
        decorator_func(clazz)

        return clazz

    return decorator