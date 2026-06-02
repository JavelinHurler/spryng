import inspect
from dataclasses import dataclass
from typing import Callable

from spryng.models.hook import PostCollectionHook
from spryng.injection.injection_graph_builder import InjectionGraphBuilder
from spryng.models.descriptors import ComponentDescriptor, DependencyDescriptor, DependencyMode

from spryng_web.decoration import ErrorHandlerDecoration, RouteDecoration, ControllerDecoration
from spryng_web.models import ErrorHandlerConfig, RouteDefinition, Handler

@dataclass
class WebProcessingPostCollectionHook(PostCollectionHook):
    def execute(self, injection_graph_builder: InjectionGraphBuilder):
        type_and_decoration_list = injection_graph_builder.get_decorated_types(ControllerDecoration)

        for controller_clazz, controller_decoration in type_and_decoration_list:
            functions = inspect.getmembers(controller_clazz, predicate=inspect.isfunction)

            error_handler_configs = build_error_handler_configs(functions)

            handler_descriptors = build_handler_descriptors(
                functions=functions,
                controller_clazz=controller_clazz,
                error_handler_configs=error_handler_configs,
                base_path=controller_decoration.base_path
            )

            for handler_descriptor in handler_descriptors:
                injection_graph_builder.add_descriptor(handler_descriptor)


def build_handler_descriptors(
    functions,
    controller_clazz: type,
    error_handler_configs: list[ErrorHandlerConfig],
    base_path: str | None,
) -> list[ComponentDescriptor]:
    handler_descriptors = []

    for name, func in functions:
        if name.startswith('__') and name.endswith('__'):
            continue

        meta = getattr(func, "__spryng_meta__", None)

        if meta is None:
            continue

        if not isinstance(meta, list):
            raise TypeError("meta must be a list")

        for decorator in meta:
            if isinstance(decorator, RouteDecoration):
                route_definition = decorator.route_definition.with_base_path(base_path)

                handler_descriptors.append(
                    build_handler_descriptor(
                        controller_clazz=controller_clazz,
                        error_handler_configs=error_handler_configs,
                        func=func,
                        route_definition=route_definition
                    )
                )

    return handler_descriptors


def build_handler_descriptor(
    controller_clazz: type,
    error_handler_configs: list[ErrorHandlerConfig],
    func: Callable,
    route_definition: RouteDefinition
) -> ComponentDescriptor:
    def handler_instantiator(component):
        return Handler(
            instance=component,
            method=func,
            matcher=route_definition,
            error_handlers=error_handler_configs
        )

    component_descriptor = ComponentDescriptor(
        name=f"handler-{route_definition.method}-{route_definition.path}",
        clazz=Handler,
        instantiator=handler_instantiator
    )

    component_descriptor.add_dependency(
        DependencyDescriptor(
            name="component",
            clazz=controller_clazz,
            mode=DependencyMode.REQUIRED
        )
    )

    return component_descriptor


def build_error_handler_configs(functions) -> list[ErrorHandlerConfig]:
    error_handler_configs = []
    for name, func in functions:
        if name.startswith('__') and name.endswith('__'):
            continue

        meta = getattr(func, "__spryng_meta__", None)
        if meta is None:
            continue

        if not isinstance(meta, list):
            raise TypeError("__spryng_meta__ must be a list")

        for decoration in meta:
            if isinstance(decoration, ErrorHandlerDecoration):
                error_handler_decoration: ErrorHandlerDecoration = decoration

                error_handler_configs.append(
                    ErrorHandlerConfig(
                        definition=error_handler_decoration.error_handler_definition,
                        func=func
                    )
                )

    return error_handler_configs
