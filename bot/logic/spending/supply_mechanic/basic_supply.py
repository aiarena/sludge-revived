from sc2 import UnitTypeId

from .supply_mechanic_interface import SupplyMechanicInterface
import bot.injector as injector
from bot.services.state_service import StateService


class BasicSupply(SupplyMechanicInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)    

    def need_supply(self) -> bool:
        DRONE_MINERALS_PER_SECOND = 0.933
        if self.state.resources.supply.cap >= 200:
            return False
        mineral_saturation = self.state.mineral_saturation
        mineral_income = mineral_saturation * DRONE_MINERALS_PER_SECOND
        overlords_in_progress = self.state.already_pending(UnitTypeId.OVERLORD)
        mineral_cost = 50
        supply_cost = 1
        overlord_buildtime = 18
        if mineral_income == 0:
            mineral_income = 1
        time_until_supplyblock = (self.state.resources.supply.left + (overlords_in_progress * 8)) / (supply_cost / mineral_cost * mineral_income)
        return (time_until_supplyblock < overlord_buildtime
                or self.state.resources.supply.left < 0 and overlords_in_progress == 0)