from dataclasses import dataclass

from spryng.injection.injection_graph_builder import InjectionGraphBuilder


@dataclass
class PostCollectionHook:
    order: int

    def execute(self, injection_graph_builder: InjectionGraphBuilder):
        pass
