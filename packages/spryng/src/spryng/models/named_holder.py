from typing import TypeVar, Generic

T = TypeVar("T")


class NamedHolder(Generic[T]):
    name: str
    element: T

    def __init__(self, name: str, element: T):
        self.name = name
        self.element = element

    def has_name(self) -> bool:
        return self.name is not None
