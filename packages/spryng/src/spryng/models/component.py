class Component:
    name: str
    component: object

    def __init__(self, name: str, component: object):
        self.name = name
        self.component = component