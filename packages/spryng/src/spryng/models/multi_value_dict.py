from typing import TypeVar, Generic, Iterator

K = TypeVar("K")
V = TypeVar("V")


class MultiValueDict(Generic[K, V]):
    def __init__(self):
        self.dict: dict[K, set[V]] = {}

    def put(self, key: K, value: V):
        if key not in self.dict:
            self.dict[key] = set()

        self.dict[key].add(value)

    def get(self, key: K) -> set[V]:
        if key not in self.dict:
            return set()

        return self.dict[key]

    def items(self):
        return self.dict.items()

    def values(self) -> Iterator[V]:
        for values in self.dict.values():
            for value in values:
                yield value

    def __iter__(self) -> Iterator[tuple[K, set[V]]]:
        return iter(self.items())

    def __str__(self):
        return str(self.dict)
