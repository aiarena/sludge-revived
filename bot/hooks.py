class Hooks:
    def __init__(self):
        self.d = {
            'on_init': [],
            'on_unit_created': [],
            'on_unit_destroyed': [],
            'on_building_construction_complete': [],
        }
    def add(self, a, fn):
        self.d[a].append(fn)
    def call(self, a, *args, **kwargs):
        for fn in self.d[a]:
            fn(*args, **kwargs)

hooks = Hooks()

def hookable(cls):
    class Child(cls):
        def __init__(self, *args, **kwargs):
            methods = dir(cls)
            for method in methods:
                if method in hooks.d:
                    hooks.add(method, self.__getattribute__(method))
            return super().__init__(*args, **kwargs)
    return Child