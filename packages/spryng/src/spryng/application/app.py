from typing import TypeVar

from spryng.application.module import Module
from spryng.application.helpers import build_bean_descriptor, build_component_descriptor
from spryng.injection.injection_graph_builder import InjectionGraphBuilder
from spryng.logging import LoggerManager, Logger
from spryng.models.component import Component

S = TypeVar("S")

@LoggerManager.decorate
class Application:
    log: Logger

    def __init__(self):
        self.components: list[Component] = []
        self.modules: list[Module] = []
        self.is_started = False


    def get_component(self, clazz: type[S]) -> S:
        components = self.get_components(clazz)
        if len(components) != 1:
            raise Exception(f"Found {len(components)} components for {clazz} but expected 1")

        return components[0]

    def get_component_exact(self, clazz: type[S]) -> S:
        components = self.get_components_exact(clazz)
        if len(components) != 1:
            raise Exception(f"Found {len(components)} components for {clazz} but expected 1")

        return components[0]

    def get_components(self, clazz: type[S]) -> list[S]:
        if not self.is_started:
            raise Exception("getting components from app before start is not allowed")

        result = []
        for component in self.components:
            if isinstance(component.component, clazz):
                result.append(component.component)

        return result

    def get_components_exact(self, clazz: type[S]) -> list[S]:
        if not self.is_started:
            raise Exception("getting components from app before start is not allowed")

        result = []
        for component in self.components:
            if component.component.__class__ == clazz:
                result.append(component.component)

        return result

    def add_modules(self, *modules: Module) -> None:
        if self.is_started:
            raise Exception("adding modules after app start is not allowed")

        for module in modules:
            self.add_module(module)

    def add_module(self, module: Module) -> None:
        if self.is_started:
            raise Exception("adding module after app start is not allowed")

        self.log.info(f"Adding module {module.name}")
        self.modules.append(module)

    def start(self) -> None:
        if self.is_started:
            raise Exception("starting app twice is not allowed")

        self.is_started = True

        self.log.info("Building app")

        injection_graph_builder = InjectionGraphBuilder()

        for module in self.modules:
            for named_clazz in module.named_clazzes:
                injection_graph_builder.add_descriptor(build_component_descriptor(named_clazz))

            for named_func in module.named_funcs:
                injection_graph_builder.add_descriptor(build_bean_descriptor(named_func))

        for hook in sorted(
            [
                _hook
                for module in self.modules
                for _hook in module.hooks
            ],
            key=lambda _hook: _hook.order,
        ):
            hook.execute(injection_graph_builder)

        injection_graph = injection_graph_builder.build()

        injection_graph.perform_injection()

        self.log.info("Starting app")

        self.components.extend(injection_graph.components)
