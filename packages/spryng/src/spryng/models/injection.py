from typing import Callable

from spryng.models.descriptors import DependencyMode


class InjectionNode:
    name: str
    clazz: type
    dependencies: set['InjectionDependency']
    instantiator: Callable

    def __init__(self, name: str, clazz: type, dependencies: set['InjectionDependency'], instantiator: Callable):
        self.name = name
        self.clazz = clazz
        self.instantiator = instantiator
        self.dependencies = dependencies

    def __str__(self):
        return f"InjectionNode(name={self.name}, clazz={self.clazz}, dependencies={self.dependencies})"

    def __repr__(self):
        return str(self)


class InjectionDependency:
    name: str
    mode: DependencyMode
    clazzes: set[type]
    injection_nodes: set[InjectionNode]

    def __init__(self, name: str, mode: DependencyMode, clazzes: set[type]):
        self.name = name
        self.mode = mode
        self.clazzes = clazzes
        self.injection_nodes = set()

    def add_dependency(self, dependency: InjectionNode):
        self.injection_nodes.add(dependency)

    def __str__(self):
        return (
            f"InjectionDependency("
            f"name={self.name}, mode={self.mode}, clazzes={self.clazzes}, injection_nodes={self.injection_nodes}"
            f")"
        )

    def __repr__(self):
        return str(self)
