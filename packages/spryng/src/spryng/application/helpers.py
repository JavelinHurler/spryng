from inspect import signature, Parameter, isfunction, isclass
from typing import Callable, get_type_hints, get_origin, get_args

from spryng.models.injection_types import OptionalInjection, ListInjection
from spryng.models.named_holder import NamedHolder
from spryng.models.descriptors import ComponentDescriptor, DependencyDescriptor, DependencyMode


def build_bean_descriptor(named_func: NamedHolder[Callable]) -> ComponentDescriptor:
    name = named_func.name if named_func.has_name() else named_func.element.__name__
    func = named_func.element

    type_hints = get_type_hints(func, include_extras=True)
    func_signature = signature(func)

    clazz = func_signature.return_annotation

    if clazz is Parameter.empty:
        raise "Bean without return type"

    descriptor = ComponentDescriptor(name=name, clazz=clazz, instantiator=func)

    for name, (param, type_hint) in join_dictionaries(func_signature.parameters, type_hints):
        if name == "return":
            continue

        validate_param(param)

        dependency_descriptor = determine_dependency_descriptor(name, type_hint)

        descriptor.add_dependency(dependency_descriptor)

    return descriptor


def build_component_descriptor(named_clazz: NamedHolder[type]) -> ComponentDescriptor:
    name = named_clazz.name if named_clazz.has_name() else named_clazz.element.__name__
    clazz = named_clazz.element

    descriptor = ComponentDescriptor(name=name, clazz=clazz, instantiator=clazz)

    # TODO for now beans need to have their own constructor as we do not explore super constructors
    if "__init__" not in clazz.__dict__:
        return descriptor

    parameters = signature(clazz.__init__).parameters
    type_hints = get_type_hints(clazz.__init__, include_extras=True)

    for name, (param, type_hint) in join_dictionaries(parameters, type_hints):
        if name == "self":
            continue

        validate_param(param)

        dependency_descriptor = determine_dependency_descriptor(name, type_hint)

        descriptor.add_dependency(dependency_descriptor)

    return descriptor


def join_dictionaries(*dictionaries):
    keys = set().union(*dictionaries)

    for key in keys:
        yield key, tuple(
            dictionary.get(key)
            for dictionary in dictionaries
        )


def validate_bean(func: Callable):
    if not isfunction(func):
        raise "Bean only allowed on functions"


def validate_component(clazz: type):
    if not isclass(clazz):
        raise "Component is only allowed on classes"


def validate_name(name: str):
    if name is None:
        return

    if not isinstance(name, str):
        raise "Name must be a string"

    if name.replace(" ", "") == "":
        raise "Name must not be empty"


def validate_param(param: Parameter):
    if param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
        raise f"Parameter '{param.name}' uses *args or **kwargs"

    if param.kind not in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY):
        raise f"Unsupported parameter kind for '{param.name}'"

    if param.annotation is Parameter.empty:
        raise f"Parameter '{param.name}' is missing type annotation"


def determine_dependency_descriptor(name, type_hint):
    origin = get_origin(type_hint)
    args = get_args(type_hint)

    if origin is OptionalInjection:
        if len(args) != 1:
            raise "OMG optional injection requires one type argument only"

        return DependencyDescriptor(name, args[0], DependencyMode.OPTIONAL)

    if origin is ListInjection:
        if len(args) != 1:
            raise "OMG list injection requires one type argument only"

        return DependencyDescriptor(name, args[0], DependencyMode.LIST)

    return DependencyDescriptor(name, type_hint, DependencyMode.REQUIRED)
