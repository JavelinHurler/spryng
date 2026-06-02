from typing import TypeVar

from spryng.injection.injection_graph import InjectionGraph
from spryng.models.descriptors import ComponentDescriptor, DependencyDescriptor
from spryng.models.injection import InjectionNode, InjectionDependency
from spryng.models.multi_value_dict import MultiValueDict

T = TypeVar("T")

class InjectionGraphBuilder:
    dependency_clazzes: set[type]
    component_clazzes: set[type]
    component_descriptors: list[ComponentDescriptor]
    dependency_clazz_to_component_clazzes: MultiValueDict[type, type]
    injection_nodes_by_clazz: MultiValueDict[type, InjectionNode]

    def __init__(self):
        self.dependency_clazzes = set()
        self.component_clazzes = set()
        self.component_descriptors = []
        self.dependency_clazz_to_component_clazzes = MultiValueDict()
        self.injection_nodes_by_clazz = MultiValueDict()

    def add_descriptor(self, component_descriptor: ComponentDescriptor):
        self.component_descriptors.append(component_descriptor)
        self.component_clazzes.add(component_descriptor.clazz)

        for dependency_descriptor in component_descriptor.dependencies:
            self.dependency_clazzes.add(dependency_descriptor.clazz)

        self.register_component_for_dependencies(component_descriptor)
        self.register_dependencies_for_components(component_descriptor.dependencies)

    def register_component_for_dependencies(self, component_descriptor: ComponentDescriptor):
        component_clazz = component_descriptor.clazz

        for dependency_clazz in self.dependency_clazzes:
            if issubclass(component_clazz, dependency_clazz):
                self.dependency_clazz_to_component_clazzes.put(dependency_clazz, component_clazz)

    def register_dependencies_for_components(self, dependency_descriptors: list[DependencyDescriptor]):
        for component_clazz in self.component_clazzes:
            for dependency_descriptor in dependency_descriptors:
                dependency_clazz = dependency_descriptor.clazz

                if issubclass(component_clazz, dependency_clazz):
                    self.dependency_clazz_to_component_clazzes.put(dependency_clazz, component_clazz)

    def build(self) -> InjectionGraph:
        return self.build_injection_graph()

    def build_injection_graph(self) -> InjectionGraph:
        graph = InjectionGraph()

        for component_descriptor in self.component_descriptors:
            injection_dependencies: set[InjectionDependency] = set()

            for dependency_descriptor in component_descriptor.dependencies:
                component_clazzes = self.dependency_clazz_to_component_clazzes.get(dependency_descriptor.clazz)

                injection_dependencies.add(
                    InjectionDependency(
                        name=dependency_descriptor.name,
                        mode=dependency_descriptor.mode,
                        clazzes=component_clazzes,
                    )
                )

            graph.add_injection_node(
                InjectionNode(
                    name=component_descriptor.name,
                    clazz=component_descriptor.clazz,
                    instantiator=component_descriptor.instantiator,
                    dependencies=injection_dependencies,
                )
            )

        return graph

    def get_decorated_types(self, decoration_type: type[T]) -> list[tuple[type, T]]:
        result = []
        for component_descriptor in self.component_descriptors:
            meta = getattr(component_descriptor.clazz, "__spryng_meta__", None)

            if meta is None:
                continue

            if not isinstance(meta, list):
                raise TypeError("__spryng_meta__ must be a list")

            decorations = [
                decorator
                for decorator in meta
                if isinstance(decorator, decoration_type)
            ]

            if len(decorations) == 0:
                continue

            if len(decorations) > 1:
                raise TypeError(f"{decoration_type} decoration applied more then once")

            decoration = decorations[0]

            result.append((component_descriptor.clazz, decoration))

        return result

    def to_dict(self):
        return {
            "injection_nodes_by_clazz": {
                injection_node_clazz.__name__: [
                    {
                        "name": injection_node.name,
                        "clazz": injection_node.clazz.__name__,
                        "dependencies": [
                            {
                                "name": injection_dependency.name,
                                "mode": str(injection_dependency.mode),
                                "clazzes": [
                                    injection_dependency_clazz.__name__
                                    for injection_dependency_clazz in injection_dependency.clazzes
                                ],
                                "injection_nodes": [
                                    {
                                        "name": inner_injection_node.name,
                                        "clazz": inner_injection_node.clazz.__name__,
                                    }
                                    for inner_injection_node in injection_dependency.injection_nodes
                                ]
                            }
                            for injection_dependency in injection_node.dependencies
                        ]
                    }
                    for injection_node in injection_nodes
                ]
                for injection_node_clazz, injection_nodes in self.injection_nodes_by_clazz.items()
            }
        }

    def __str__(self):
        return f"InjectionContext(injection_nodes_by_clazz={self.injection_nodes_by_clazz}"



