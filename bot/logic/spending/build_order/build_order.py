from typing import List

from sc2 import UnitTypeId

class BOStep():
    def __init__(self, start_condition, end_condition, unit_id: UnitTypeId):
        self.start_condition = start_condition
        self.end_condition = end_condition
        self.unit_id = unit_id

class BORunner():
    def __init__(self, build_order: List[BOStep]):
        self.build_order = build_order
        self.step = 0
        self.finished = False
    
    def iterate(self) -> UnitTypeId:
        if self.step >= len(self.build_order):
            self.finished = True
            return None

        if (self.step == 0 or self.build_order[self.step-1].end_condition()) and self.build_order[self.step].start_condition():
            self.step += 1
            return self.build_order[self.step - 1].unit_id
        elif self.step > 0 and not self.build_order[self.step-1].end_condition(): return self.build_order[self.step-1].unit_id
        else: return None

class BORepository():
    def __init__(self, bot):
        self.bot = bot
    
    def hatch_first(self):
        return [
            (BOStep(
                lambda: self.bot.supply_used >= 13,
                lambda: self.bot.already_pending(UnitTypeId.OVERLORD) or self.bot.units(UnitTypeId.OVERLORD).amount == 2,
                UnitTypeId.OVERLORD
            )),
            BOStep(
                lambda: True,
                lambda: self.bot.already_pending(UnitTypeId.DRONE) + self.bot.units(UnitTypeId.DRONE).amount >= 17,
                UnitTypeId.DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(UnitTypeId.HATCHERY) or self.bot.units(UnitTypeId.HATCHERY).amount == 2,
                UnitTypeId.HATCHERY
            )),
            BOStep(
                lambda: True,
                lambda: self.bot.already_pending(UnitTypeId.DRONE) + self.bot.units(UnitTypeId.DRONE).amount >= 18,
                UnitTypeId.DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 18,
                lambda: self.bot.already_pending(UnitTypeId.EXTRACTOR) or self.bot.units(UnitTypeId.EXTRACTOR).exists,
                UnitTypeId.EXTRACTOR
            )),
            (BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(UnitTypeId.SPAWNINGPOOL) or self.bot.units(UnitTypeId.SPAWNINGPOOL).exists,
                UnitTypeId.SPAWNINGPOOL
            )),
            BOStep(
                lambda: True,
                lambda: self.bot.already_pending(UnitTypeId.DRONE) + self.bot.units(UnitTypeId.DRONE).amount >= 19,
                UnitTypeId.DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 19,
                lambda: self.bot.already_pending(UnitTypeId.OVERLORD) or self.bot.units(UnitTypeId.OVERLORD).amount == 3,
                UnitTypeId.OVERLORD
            ))
        ]
    
    def pool_first_zvz(self):
        return [
            BOStep(
                lambda: self.bot.supply_used >= 13,
                lambda: self.bot.already_pending(UnitTypeId.OVERLORD) or self.bot.units(UnitTypeId.OVERLORD).amount == 2,
                UnitTypeId.OVERLORD
            ),
            BOStep(
                lambda: True,
                lambda: self.bot.already_pending(UnitTypeId.DRONE) + self.bot.units(UnitTypeId.DRONE).amount >= 16,
                UnitTypeId.DRONE
            ),
            BOStep(
                lambda: self.bot.supply_used >= 16,
                lambda: self.bot.already_pending(UnitTypeId.SPAWNINGPOOL) or self.bot.units(UnitTypeId.SPAWNINGPOOL).exists,
                UnitTypeId.SPAWNINGPOOL
            ),
            BOStep(
                lambda: True,
                lambda: self.bot.already_pending(UnitTypeId.DRONE) + self.bot.units(UnitTypeId.DRONE).amount >= 17,
                UnitTypeId.DRONE
            ),
            BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(UnitTypeId.HATCHERY) or self.bot.units(UnitTypeId.HATCHERY).amount == 2,
                UnitTypeId.HATCHERY
            ),
            BOStep(
                lambda: True,
                lambda: self.bot.already_pending(UnitTypeId.DRONE) + self.bot.units(UnitTypeId.DRONE).amount >= 17,
                UnitTypeId.DRONE
            ),
            (BOStep(
                lambda: self.bot.supply_used >= 17,
                lambda: self.bot.already_pending(UnitTypeId.EXTRACTOR) or self.bot.units(UnitTypeId.EXTRACTOR).exists,
                UnitTypeId.EXTRACTOR
            )),
            (BOStep(
                lambda: True,
                lambda: self.bot.units(UnitTypeId.ZERGLING).amount + self.bot.already_pending(UnitTypeId.ZERGLING) >= 3,
                UnitTypeId.ZERGLING
            )),
            (BOStep(
                lambda: self.bot.supply_used >= 19,
                lambda: self.bot.UnitTypeId.QUEEN_already_pending() or self.bot.units(UnitTypeId.QUEEN).exists,
                UnitTypeId.QUEEN
            )),
            (BOStep(
                lambda: True,
                lambda: self.bot.already_pending(UnitTypeId.OVERLORD) or self.bot.units(UnitTypeId.OVERLORD).amount == 3,
                UnitTypeId.OVERLORD
            ))
        ]
