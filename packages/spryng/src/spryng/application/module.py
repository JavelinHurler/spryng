from typing import Callable

from spryng.models.hook import PostCollectionHook
from spryng.models.named_holder import NamedHolder
from spryng.application.helpers import validate_bean, validate_component, validate_name


class Module:
    name: str
    named_clazzes: set[NamedHolder[type]]
    named_funcs: set[NamedHolder[Callable]]
    marked_clazzes: set[type]
    hooks: list[PostCollectionHook]

    def __init__(self, name: str):
        self.name = name
        self.named_clazzes = set()
        self.named_funcs = set()
        self.marked_clazzes = set()
        self.hooks = []

    def component(self, name=None):
        def decorator(clazz: type):
            validate_component(clazz)
            validate_name(name)

            self.named_clazzes.add(NamedHolder(name=name, element=clazz))

            return clazz

        return decorator

    def bean(self, name=None):
        def decorator(func: Callable):
            validate_bean(func)
            validate_name(name)

            self.named_funcs.add(NamedHolder(name=name, element=func))

            return func

        return decorator

    def add_hook(self, hook: PostCollectionHook):
        self.hooks.append(hook)


