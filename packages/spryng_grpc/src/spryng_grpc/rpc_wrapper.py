from typing import Callable

from google.protobuf.descriptor import MethodDescriptor
from grpc import StatusCode
from spryng_grpc.error import GrpcError


class RpcWrapper:
    def __init__(
            self,
            rpc_impl: Callable,
            method_descriptor: MethodDescriptor,
    ) -> None:
        self.rpc_impl = rpc_impl
        self.method_descriptor = method_descriptor

    def call_unary_response(self, request, context):
        try:
            return self.rpc_impl(request, context)
        except GrpcError as e:
            context.abort(e.status_code, e.details)

        except Exception as e:
            if context.code() is None:
                context.abort(StatusCode.INTERNAL, f"{e.__class__.__name__}: {e}")


    def call_stream_response(self, request, context):
        iterator = None

        try:
            iterator = self.rpc_impl(request, context)
        except GrpcError as e:
            context.abort(e.status_code, e.details)

        except Exception as e:
            if context.code() is None:
                context.abort(StatusCode.INTERNAL, f"{e.__class__.__name__}: {e}")

        try:
            yield from iterator
        except GrpcError as e:
            context.abort(e.status_code, e.details)

        except Exception as e:
            if context.code() is None:
                context.abort(StatusCode.INTERNAL, f"{e.__class__.__name__}: {e}")


    def __call__(self, request, context):
        if self.method_descriptor.server_streaming is True:
            return self.call_stream_response(request, context)
        else:
            return self.call_unary_response(request, context)
