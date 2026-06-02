from threading import Event

from grpc import Server
from spryng.models.injection_types import ListInjection


class GrpcServerCollection:
    servers: list[Server]

    def __init__(self, servers: ListInjection[Server]):
        self.servers = servers.values

    def start(self):
        for server in self.servers:
            server.start()

    def terminate(self):
        events: list[Event] = []

        for server in self.servers:
            events.append(server.stop(grace=10))

        for event in events:
            event.wait(timeout=60)