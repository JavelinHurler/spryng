from inspect import isfunction, isclass

class Decoration:
    def validate(self, obj) -> None:
        pass

    def apply(self, obj):
        self.validate(obj)

        meta = getattr(obj, "__spryng_meta__", [])

        if not isinstance(meta, list):
            raise TypeError("spryng_meta must be a list or None")

        meta.append(self)

        setattr(obj, "__spryng_meta__", meta)


class FunctionDecoration(Decoration):
    def validate(self, obj) -> None:
        if not isfunction(obj):
            raise TypeError("FunctionDecoration must be applied to a function")


class ClassDecoration(Decoration):
    def validate(self, obj) -> None:
        if not isclass(obj):
            raise TypeError("ClassDecoration must be applied to a class")



def decorate(decoration: Decoration):
    if not isinstance(decoration, Decoration):
        raise TypeError("decoration must be a Decoration")

    def decorator(func):
        decoration.apply(func)

        return func
    return decorator
