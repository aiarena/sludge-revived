from sc2 import UnitTypeId, BotAI

from .supply_mechanic.supply_mechanic_interface import SupplyMechanicInterface
from .spending_interface import SpendingInterface
from ...util.priority_queue import PriorityQueue
from bot.services.state_service import StateService
import bot.injector as injector
from .build_order.build_order import BORepository, BORunner, BOStep

LARVA_RATE_PER_MINUTE = 11.658

class DefaultSpending(SpendingInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.supply_mechanic: SupplyMechanicInterface = injector.inject(SupplyMechanicInterface)
        self.build_repository: BORepository = BORepository(injector.inject(BotAI))
        # TODO: get build order from config
        self.build_order_runner: BORunner = BORunner(self.build_repository.hatch_first())
    def get_current_priorities(self) -> PriorityQueue:
        priorities: PriorityQueue = PriorityQueue()
        priorities.enqueue(UnitTypeId.DRONE, 10)
        if not self.build_order_runner.finished:
            unit_id: UnitTypeId = self.build_order_runner.iterate()
            if unit_id:
                priorities.enqueue(unit_id, 50)
        else:
            if self.supply_mechanic.need_supply():
                priorities.enqueue(UnitTypeId.OVERLORD, 15)
            if self.need_hatchery():
                priorities.enqueue(UnitTypeId.HATCHERY, 20)
            if self.need_queen():
                priorities.enqueue(UnitTypeId.QUEEN, 21)
        return priorities

    def need_hatchery(self) -> bool:
        return self.state.own_units(UnitTypeId.DRONE).amount > (self.state.own_units(UnitTypeId.HATCHERY).amount * LARVA_RATE_PER_MINUTE) and not self.state.already_pending(UnitTypeId.HATCHERY)

    def need_queen(self) -> bool:
        queen_count = self.state.own_units(UnitTypeId.QUEEN).amount + self.state.queen_already_pending()
        return self.state.own_units(UnitTypeId.SPAWNINGPOOL).exists and self.state.own_units(UnitTypeId.HATCHERY).amount > queen_count and queen_count < 6