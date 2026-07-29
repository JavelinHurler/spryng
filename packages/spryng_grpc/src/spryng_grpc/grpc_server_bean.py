import importlib
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, get_type_hints, get_origin, get_args
from collections.abc import Iterable, Iterator

import grpc
from google.protobuf import symbol_database
from google.protobuf.descriptor import ServiceDescriptor, MethodDescriptor
from google.protobuf.symbol_database import SymbolDatabase
from grpc import Server, RpcMethodHandler

from spryng_grpc.decoration import GrpcHandlerDecoration
from spryng_grpc.rpc_wrapper import RpcWrapper


def bind_server_bean(grpc_handler_decoration: GrpcHandlerDecoration) -> Callable:
    def bean(grpc_handler: object) -> Server:
        # TODO rgerhard add thread pool as a dependency
        # this requires config props to be able to configure the server

        pool = ThreadPoolExecutor(max_workers=grpc_handler_decoration.max_workers)

        server = grpc.server(pool)

        service_descriptor = determine_service_descriptor(grpc_handler)

        sym_db = symbol_database.Default()

        handlers = {}

        for method_descriptor in service_descriptor.methods:
            handler = build_method_handler(sym_db, method_descriptor, grpc_handler)
            handlers[method_descriptor.name] = handler

        server.add_registered_method_handlers(service_descriptor.full_name, handlers)

        server.add_insecure_port(f"{grpc_handler_decoration.host}:{grpc_handler_decoration.port}")

        return server

    return bean


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
) -> RpcMethodHandler:
    rpc_impl = getattr(grpc_handler, method_descriptor.name)

    request_cls = sym_db.GetSymbol(method_descriptor.input_type.full_name)
    response_cls = sym_db.GetSymbol(method_descriptor.output_type.full_name)

    validate_rpc_method(method_descriptor, request_cls, response_cls, rpc_impl)

    rpc_wrapper = RpcWrapper(rpc_impl, method_descriptor)

    request_parser = request_cls.FromString
    response_serializer = response_cls.SerializeToString

    client_streaming = method_descriptor.client_streaming
    server_streaming = method_descriptor.server_streaming

    # TODO proper exception type and error message
    if client_streaming is None:
        raise Exception("")
    if server_streaming is None:
        raise Exception("")

    if not client_streaming and not server_streaming:
        return grpc.unary_unary_rpc_method_handler(
            rpc_wrapper,
            request_deserializer=request_parser,
            response_serializer=response_serializer
        )

    if not client_streaming and server_streaming:
        return grpc.unary_stream_rpc_method_handler(
            rpc_wrapper,
            request_deserializer=request_parser,
            response_serializer=response_serializer
        )

    if client_streaming and not server_streaming:
        return grpc.stream_unary_rpc_method_handler(
            rpc_wrapper,
            request_deserializer=request_parser,
            response_serializer=response_serializer
        )

    return grpc.stream_stream_rpc_method_handler(
        rpc_wrapper,
        request_deserializer=request_parser,
        response_serializer=response_serializer
    )


def validate_rpc_method(method_descriptor, request_class, response_class, rpc_impl):
    sig = inspect.signature(rpc_impl)
    params = list(sig.parameters.values())

    if len(params) != 2:
        raise Exception("wrong number of parameters")

    request_param = params[0]
    context_param = params[1]

    hints = get_type_hints(rpc_impl)

    if request_param.name not in hints:
        raise Exception(f"Missing type annotation for '{request_param.name}' on {rpc_impl.__name__}")

    if context_param.name not in hints:
        raise Exception(f"Missing type annotation for '{context_param.name}'")

    if "return" not in hints:
        raise Exception("Missing return type annotation.")

    request_type = hints[request_param.name]
    context_type = hints[context_param.name]
    return_type = hints["return"]

    if not issubclass(context_type, grpc.ServicerContext):
        raise Exception("Second param is not ServicerContext")

    if method_descriptor.client_streaming is True:
        origin = get_origin(request_type)
        if origin not in {Iterator, Iterable}:
            raise Exception(f"Unexpected request type '{request_type}'")

        args = get_args(request_type)
        if len(args) != 1:
            raise Exception("Wrong number of type arguments for request type")

        if not issubclass(args[0], request_class):
            raise Exception(f"Wrong request type '{request_type}'")

    else:
        if not issubclass(request_type, request_class):
            raise Exception(f"Wrong request type '{request_type}'")

    if method_descriptor.server_streaming is True:
        origin = get_origin(return_type)
        if origin not in {Iterator, Iterable}:
            raise Exception(f"Unexpected return type '{return_type}'")

        args = get_args(return_type)
        if len(args) != 1:
            raise Exception("Wrong number of type arguments for return type")

        if not issubclass(args[0], response_class):
            raise Exception(f"Wrong return type '{return_type}'")

    else:
        if not issubclass(return_type, response_class):
            raise Exception(f"Wrong return type '{return_type}'")
