import importlib
import inspect
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import grpc
from google.protobuf import symbol_database
from google.protobuf.descriptor import ServiceDescriptor, MethodDescriptor
from google.protobuf.symbol_database import SymbolDatabase
from grpc import Server, RpcMethodHandler, ServicerContext
from spryng.logging import LoggerManager, Logger
from spryng_grpc.decoration import GrpcHandlerDecoration
from spryng.injection.injection_graph_builder import InjectionGraphBuilder
from spryng.models.descriptors import ComponentDescriptor, DependencyMode
from spryng.models.hook import PostCollectionHook
from spryng.models.descriptors import DependencyDescriptor
from spryng_grpc.decoration import GrpcHandlerErrorHandlerDecoration


@LoggerManager.decorate
class ErrorHandlerRegistry:
    log: Logger
    error_handlers_by_type: dict[type[Exception], Callable[[Exception, ServicerContext], None]]

    def __init__(self):
        self.error_handlers_by_type = {}

    def add_error_handler(self, exception_type: type[Exception], handler: Callable[[Exception, ServicerContext], None]):
        self.error_handlers_by_type[exception_type] = handler

    def try_handle(self, error: Exception, context: ServicerContext):
        for error_type, handler in self.error_handlers_by_type.items():
            if isinstance(error, error_type):
                self.log.info(f"Handler {handler} selected to handle error {error.__class__.__name__}({error})")
                handler(error, context)

        self.log.error(f"No handler was found to handle {error.__class__.__name__}({error})")

        context.abort(
            grpc.StatusCode.UNKNOWN,
            f"Exception: {error.__class__.__name__}({error}) happened and no errorhandler for it was found"
        )


class RpcImplWrapper:
    def __init__(self, grpc_handler: object, method_name: str, error_handler_registry: ErrorHandlerRegistry) -> None:
        self.rpc_impl = getattr(grpc_handler, method_name)
        self.error_handler_registry = error_handler_registry
        self.method_name = method_name

    def __call__(self, request, context):
        try:
            result = self.rpc_impl(*(request, context))
        except Exception as error:
            self.error_handler_registry.try_handle(error, context)
            raise error

        if not inspect.isgenerator(result):
            return result

        result_iter = iter(result)

        while True:
            try:
                yield next(result_iter)
            except StopIteration:
                return
            except Exception as error:
                self.error_handler_registry.try_handle(error, context)

                raise error


@dataclass
class GrpcProcessingPostCollectionHook(PostCollectionHook):
    # TODO rgerhard check if a single grpc server can have many handlers added
    def execute(self, injection_graph_builder: InjectionGraphBuilder):
        type_and_decoration_list = injection_graph_builder.get_decorated_types(GrpcHandlerDecoration)
        for grpc_handler_clazz, grpc_handler_decoration in type_and_decoration_list:
            bean = build_grpc_server_bean(grpc_handler_decoration)

            descriptor = build_grpc_server_component_descriptor(bean, grpc_handler_clazz)

            injection_graph_builder.add_descriptor(descriptor)


def build_grpc_server_bean(grcp_handler_decoration: GrpcHandlerDecoration) -> Callable[[object], Server]:
    def bean(grpc_handler: object) -> Server:
        error_handler_registry = build_error_handler_registry(grpc_handler)

        # TODO rgerhard add thread pool as a dependency
        pool = ThreadPoolExecutor(max_workers=grcp_handler_decoration.max_workers)

        server = grpc.server(pool)

        service_descriptor = determine_service_descriptor(grpc_handler)
        server.add_registered_method_handlers(
            service_descriptor.full_name,
            build_handlers(service_descriptor, grpc_handler, error_handler_registry)
        )

        server.add_insecure_port(f"{grcp_handler_decoration.host}:{grcp_handler_decoration.port}")

        return server

    return bean


def build_error_handler_registry(grpc_handler) -> ErrorHandlerRegistry:
    error_handler_registry = ErrorHandlerRegistry()

    for name, func in inspect.getmembers(grpc_handler, predicate=inspect.ismethod):
        if name.startswith("__") and name.endswith("__"):
            continue

        meta = getattr(func, "__spryng_meta__", None)

        if meta is None:
            continue

        if not isinstance(meta, list):
            raise TypeError("meta must be a list")

        for decorator in meta:
            if isinstance(decorator, GrpcHandlerErrorHandlerDecoration):
                errors = decorator.errors
                for error in errors:
                    error_handler_registry.add_error_handler(error, func)

    return error_handler_registry


def build_grpc_server_component_descriptor(
    bean: Callable[[object], Server], grpc_handler_clazz: type
) -> ComponentDescriptor:
    server_descriptor = ComponentDescriptor(
        name=f"{grpc_handler_clazz.__module__}-{grpc_handler_clazz.__name__}-server",
        clazz=Server,
        instantiator=bean,
    )

    server_descriptor.add_dependency(
        DependencyDescriptor(
            clazz=grpc_handler_clazz,
            mode=DependencyMode.REQUIRED,
            name="grpc_handler"
        )
    )

    return server_descriptor


def build_handlers(
    service_descriptor: ServiceDescriptor, grpc_handler: object, error_handler_registry: ErrorHandlerRegistry
) -> dict[str, RpcMethodHandler]:
    sym_db = symbol_database.Default()

    return {
        method_descriptor.name: build_method_handler(sym_db, method_descriptor, grpc_handler, error_handler_registry)
        for method_descriptor in service_descriptor.methods
    }


def determine_service_descriptor(grpc_handler: object) -> ServiceDescriptor:
    grpc_base = grpc_handler.__class__.__bases__[0]

    pb2_module_name = grpc_base.__module__.replace("_pb2_grpc", "_pb2")

    service_name = grpc_base.__name__.replace("Servicer", "")

    pb2_module = importlib.import_module(pb2_module_name)

    return pb2_module.DESCRIPTOR.services_by_name[service_name]



def build_method_handler(
    sym_db: SymbolDatabase,
    method_descriptor: MethodDescriptor,
    grpc_handler: object,
    error_handler_registry: ErrorHandlerRegistry
) -> RpcMethodHandler:
    method_name = method_descriptor.name


    logging_wrapped_rpc_impl = RpcImplWrapper(grpc_handler, method_name, error_handler_registry)

    request_cls = sym_db.GetSymbol(method_descriptor.input_type.full_name)
    response_cls = sym_db.GetSymbol(method_descriptor.output_type.full_name)

    client_streaming = method_descriptor.client_streaming
    server_streaming = method_descriptor.server_streaming

    if not client_streaming and not server_streaming:
        return grpc.unary_unary_rpc_method_handler(
            logging_wrapped_rpc_impl,
            request_deserializer=request_cls.FromString,
            response_serializer=response_cls.SerializeToString
        )

    if not client_streaming and server_streaming:
        return grpc.unary_stream_rpc_method_handler(
            logging_wrapped_rpc_impl,
            request_deserializer=request_cls.FromString,
            response_serializer=response_cls.SerializeToString
        )

    if client_streaming and not server_streaming:
        return grpc.stream_unary_rpc_method_handler(
            logging_wrapped_rpc_impl,
            request_deserializer=request_cls.FromString,
            response_serializer=response_cls.SerializeToString
        )

    return grpc.stream_stream_rpc_method_handler(
        logging_wrapped_rpc_impl,
        request_deserializer=request_cls.FromString,
        response_serializer=response_cls.SerializeToString
    )


