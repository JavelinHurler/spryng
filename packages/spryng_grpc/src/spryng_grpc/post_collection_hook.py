from dataclasses import dataclass

from grpc import Server
from spryng_grpc.decoration import GrpcHandlerDecoration
from spryng.injection.injection_graph_builder import InjectionGraphBuilder
from spryng.models.descriptors import ComponentDescriptor, DependencyMode
from spryng.models.hook import PostCollectionHook
from spryng.models.descriptors import DependencyDescriptor
from spryng_grpc.grpc_server_bean import bind_server_bean


@dataclass
class GrpcProcessingPostCollectionHook(PostCollectionHook):
    # TODO rgerhard check if a single grpc server can have many handlers added
    def execute(self, injection_graph_builder: InjectionGraphBuilder):
        type_and_decoration_list = injection_graph_builder.get_decorated_types(GrpcHandlerDecoration)
        for grpc_handler_clazz, grpc_handler_decoration in type_and_decoration_list:
            server_descriptor = ComponentDescriptor(
                name=f"{grpc_handler_clazz.__module__}-{grpc_handler_clazz.__name__}-server",
                clazz=Server,
                instantiator=bind_server_bean(grpc_handler_decoration),
            )

            server_descriptor.add_dependency(
                DependencyDescriptor(
                    clazz=grpc_handler_clazz,
                    mode=DependencyMode.REQUIRED,
                    name="grpc_handler"
                )
            )

            injection_graph_builder.add_descriptor(server_descriptor)
