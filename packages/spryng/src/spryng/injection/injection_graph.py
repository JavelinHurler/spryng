from typing import Iterator

from spryng.models.injection_types import OptionalInjection, ListInjection
from spryng.models.component import Component
from spryng.models.descriptors import DependencyMode
from spryng.models.injection import InjectionNode
from spryng.models.multi_value_dict import MultiValueDict

class InjectionGraph:
    injection_nodes_by_clazz: MultiValueDict[type, InjectionNode]
    components: list[Component]
    is_injection_done: bool

    def __init__(self):
        self.injection_nodes_by_clazz = MultiValueDict()
        self.components = []
        self.is_injection_done = False

    def add_injection_node(self, injection_node: InjectionNode):
        if self.is_injection_done:
            raise Exception("adding injection node after injection was done is not allowed")

        self.injection_nodes_by_clazz.put(injection_node.clazz, injection_node)

    def get_components(self) -> list[Component]:
        if not self.is_injection_done:
            raise Exception("getting components before injection was done is not allowed")

        return self.components

    def perform_injection(self):
        if self.is_injection_done:
            raise Exception("performing injection after injection was done is not allowed")

        self.is_injection_done = True

        self.enrich_graph()

        nodes_ready = set()
        node_to_component = {}

        done = False
        while not done:
            did_one = False
            for injection_node in self.injection_nodes_by_clazz.values():
                if injection_node in nodes_ready:
                    continue

                did_one = True

                if not is_injection_node_ready(nodes_ready, injection_node):
                    continue

                params = {}
                for dependency in injection_node.dependencies:
                    if dependency.mode == DependencyMode.REQUIRED:
                        if len(dependency.injection_nodes) != 1:
                            raise Exception("This is not possible. End of world error")

                        component = node_to_component.get(next(iter(dependency.injection_nodes)))
                        params[dependency.name] = component
                    elif dependency.mode == DependencyMode.OPTIONAL:
                        if len(dependency.injection_nodes) > 1:
                            raise Exception("This is not possible. End of world error")

                        if len(dependency.injection_nodes) == 1:
                            params[dependency.name] = OptionalInjection(
                                node_to_component.get(next(iter(dependency.injection_nodes)))
                            )
                        else:
                            params[dependency.name] = OptionalInjection(None)
                    elif dependency.mode == DependencyMode.LIST:
                        nodes = []
                        for node in dependency.injection_nodes:
                            nodes.append(node_to_component.get(node))

                        params[dependency.name] = ListInjection(nodes)

                component = injection_node.instantiator(**params)
                node_to_component[injection_node] = component

                self.components.append(
                    Component(
                        name=injection_node.name,
                        component=component,
                    )
                )

                nodes_ready.add(injection_node)

            if not did_one:
                done = True


    def enrich_graph(self):
        # loop over all nodes
        for injection_node in self.injection_nodes_by_clazz.values():
            # loop over all dependecies of node
            for dependency in injection_node.dependencies:
                # loop over all clazzes that satisfy the dependency
                for clazz in dependency.clazzes:
                    dependency_injection_nodes = self.injection_nodes_by_clazz.get(clazz)
                    for dependency_injection_node in dependency_injection_nodes:
                        dependency.add_dependency(dependency_injection_node)

                validate_injection_dependency(dependency)

        validate_injection_graph_is_acyclic(self.injection_nodes_by_clazz.values())


def is_injection_node_ready(nodes_ready: set[InjectionNode], injection_node: InjectionNode) -> bool:
    for dependency in injection_node.dependencies:
        for dependency_injection_node in dependency.injection_nodes:
            if dependency_injection_node not in nodes_ready:
                return False

    return True


def validate_injection_dependency(dependency):
    injection_nodes_len = len(dependency.injection_nodes)
    if dependency.mode == DependencyMode.REQUIRED and injection_nodes_len != 1:
        raise Exception(
            f"For dependency {dependency} not exactly 1 injection candidate but {injection_nodes_len}"
        )

    elif dependency.mode == DependencyMode.OPTIONAL and injection_nodes_len > 1:
        raise Exception(
            f"For dependency {dependency} not 0 or 1 injection candidate but {injection_nodes_len}"
        )


def validate_injection_graph_is_acyclic(injection_nodes: Iterator[InjectionNode]):
    visited_nodes = set()
    in_stack = set()

    for start_node in injection_nodes:
        if start_node in visited_nodes:
            continue

        stack: list[tuple[InjectionNode, bool]] = [(start_node, False)]

        while stack:
            node, processed = stack.pop()
            if processed:
                in_stack.remove(node)
                visited_nodes.add(node)
                continue

            if node in in_stack:
                raise Exception(f"Circular dependency detected on node {node}")

            if node in visited_nodes:
                continue

            in_stack.add(node)
            stack.append((node, True))

            for dependency in node.dependencies:
                for injection_node in dependency.injection_nodes:
                    stack.append((injection_node, False))

