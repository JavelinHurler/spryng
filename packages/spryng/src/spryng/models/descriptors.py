from enum import Enum
from typing import Callable


class DependencyMode(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    LIST = "list"

    def __str__(self):
        return f"DependencyMode({self.value})"

    def __repr__(self):
        return str(self)


class DependencyDescriptor:
    name: str
    clazz: type
    mode: DependencyMode

    def __init__(self, name: str, clazz: type, mode: DependencyMode):
        self.name = name
        self.clazz = clazz
        self.mode = mode

    def __str__(self):
        return f"DependencyDescriptor(name={self.name}, class={self.clazz}, mode={self.mode})"

    def __repr__(self):
        return str(self)


class ComponentDescriptor:
    name: str
    clazz: type
    dependencies: list[DependencyDescriptor]
    instantiator: Callable

    def __init__(self, name: str, clazz: type, instantiator: Callable):
        self.name = name
        self.clazz = clazz
        self.instantiator = instantiator
        self.dependencies = []

    def add_dependency(self, dependency_descriptor: DependencyDescriptor):
        self.dependencies.append(dependency_descriptor)

    def __str__(self):
        return f"ComponentDescriptor(name={self.name}, class={self.clazz.__name__}, dependencies={self.dependencies})"

    def __repr__(self):
        return str(self)
