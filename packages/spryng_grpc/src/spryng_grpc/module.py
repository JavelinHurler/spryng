from sys import maxsize

from spryng.application.module import Module

from spryng_grpc.grpc_server_collection import GrpcServerCollection
from spryng_grpc.post_collection_hook import GrpcProcessingPostCollectionHook

module = Module(__name__)

module.add_hook(GrpcProcessingPostCollectionHook(order=maxsize))
module.component()(GrpcServerCollection)