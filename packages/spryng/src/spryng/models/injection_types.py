from typing import TypeVar, Generic

T = TypeVar("T")


class OptionalInjection(Generic[T]):
    value: T

    def __init__(self, value: T):
        self.value = value

class ListInjection(Generic[T]):
    values: list[T]

    def __init__(self, values: list[T]):
        self.values = values
