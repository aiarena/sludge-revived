class Supply():
    def __init__(self, used = 0, cap = 0):
        self.used = used
        self.cap = cap

    @property
    def left(self):
        return self.cap - self.used

class Resources():
    def __init__(self, minerals = 0, vespene = 0, supply: Supply = Supply(), larvae = 0):
        self.minerals = minerals
        self.vespene = vespene
        self.supply: Supply = supply
        self.larva = 0
