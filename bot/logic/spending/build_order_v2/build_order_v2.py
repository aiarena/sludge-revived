from typing import List, Dict
from enum import Enum
from collections import defaultdict

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from bot.services.state_service import StateService
import bot.injector as injector
from bot.util.priority_queue import PriorityQueue
from bot.services.unit_type_service import UnitTypeService
from bot.model.unit_type_abstraction import UnitTypeAbstraction
from bot.logic.spending.supply_mechanic.supply_mechanic_interface import SupplyMechanicInterface
from bot.services.eco_balance_service import EcoBalanceService


"""

This is a less strict build order runner.

Each BOStep is checked every time the on_step method is called.

Build orders are designed in a way where you can switch build orders at any point in the game.

Older steps (earlier in the build) are higher priority so they will be done first if multiple conditions are met.

"""

# TODO: move somewhere else
LARVA_RATE_PER_MINUTE = 11.658

class BOAction(Enum):
    BUILD_HATCHERIES = 0
    BUILD_QUEENS = 1
    BUILD_OVERLORDS = 2
    BUILD_DRONES = 3
    
    REQUEST_UPGRADE = 4
    STABLE_VESPENE = 5 #used for both gas ratio and automatic setting of vespene queue
    MAX_EXTRACTOR = 6

    WORKER_LIMIT = 7

class BORequest:
    def __init__(self, request : BOAction, value):
        self.request = request
        self.value = value

class BOStep:
    def __init__(self, trigger_supply, check_complete, check_prerequisites, action, action_enabled = False):
        self.trigger_supply: int = trigger_supply
        self.check_complete: function = check_complete
        self.check_prerequisites: function = check_prerequisites
        self.action: Union[UnitTypeId, BOAction] = action
        self.action_enabled: bool = action_enabled

class BORunner:
    def __init__(self, build_order: List[BOStep]):
        self.build_order: List[BOStep] = build_order
        self.state: StateService = injector.inject(StateService)
        self.unit_type : UnitTypeService = injector.inject(UnitTypeService)
        self.eco_balance: EcoBalanceService = injector.inject(EcoBalanceService)
        self.actions: Dict[BOAction, bool] = defaultdict(bool)
        self.supply_mechanic: SupplyMechanicInterface = injector.inject(SupplyMechanicInterface)
    def on_step(self) -> PriorityQueue:
        priorities: PriorityQueue = PriorityQueue()
        step_priority = 1000
        for step in self.build_order:
            step: BOStep
            if (self.state.resources.supply.used >= step.trigger_supply
                and not step.check_complete()
                and step.check_prerequisites()):
                if isinstance(step.action, UnitTypeId) or isinstance(step.action, UpgradeId):
                    priorities.enqueue(step.action, step_priority)
                elif isinstance(step.action, BOAction):
                    self.actions[step.action] = step.action_enabled
                elif isinstance(step.action, BORequest):
                    if step.action.request == BOAction.REQUEST_UPGRADE:
                        self.eco_balance.request_eco(*self.unit_type.get_resource_value_upgrade(step.action.value))
                    if step.action.request == BOAction.STABLE_VESPENE:
                        self.eco_balance.set_default_workers_on_gas(step.action.value)
                    if step.action.request == BOAction.MAX_EXTRACTOR:
                        self.eco_balance.set_max_extractor_count(step.action.value)
                step_priority -= 1

        # ------------------------------------- #
        # automatic droning hatches queens etc. #
        # ------------------------------------- #
        if self.actions[BOAction.BUILD_DRONES] and not self.actions[BOAction.WORKER_LIMIT]:
            priorities.enqueue(UnitTypeAbstraction.ECONOMY, 10)
        else:
            priorities.enqueue(UnitTypeAbstraction.ARMY, 10)
        if self.actions[BOAction.BUILD_HATCHERIES]:
            if self.need_hatchery():
                # print(f'NEED HATCHERY!! bo action is: {self.actions[BOAction.BUILD_HATCHERIES]}')
                priorities.enqueue(UnitTypeId.HATCHERY, 20)
            elif self.state.already_pending(UnitTypeId.HATCHERY) < 2:
                priorities.enqueue(UnitTypeId.HATCHERY, 5)
        #turns on eco balance queue system for vespene gatherers, which helps prevent workers from switching between minerals and gas
        self.eco_balance.set_vespene_queue(True) if self.actions[BOAction.STABLE_VESPENE] else self.eco_balance.set_vespene_queue(False)
        if self.actions[BOAction.BUILD_QUEENS] and self.need_queen():
            priorities.enqueue(UnitTypeId.QUEEN, 21)
        if self.actions[BOAction.BUILD_OVERLORDS] and self.supply_mechanic.need_supply():
            priorities.enqueue(UnitTypeId.OVERLORD, 10001)
        return priorities

    # TODO: move to a different package
    def need_hatchery(self) -> bool:
        return self.state.own_units(UnitTypeId.DRONE).amount > (self.state.pending_townhalls() * LARVA_RATE_PER_MINUTE) and not self.state.already_pending(UnitTypeId.HATCHERY)

    def need_queen(self) -> bool:
        queen_count = self.state.own_units(UnitTypeId.QUEEN).amount + self.state.queen_already_pending()
        return self.state.own_units(UnitTypeId.SPAWNINGPOOL).exists and self.state.own_units(UnitTypeId.HATCHERY).amount > queen_count and queen_count < 6
    
    def set_boaction(self, b: BOAction, val: bool):
        self.actions[b] = val

class BORepository:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
    def get_standard_build_order(self) -> List[BOStep]:
        from bot.logic.spending.build_order_v2.standard_build_order import get_build
        return get_build(self.state)

    def get_standard_zerg_build(self) -> List[BOStep]:
        from bot.logic.spending.build_order_v2.standard_zerg_build import get_build
        return get_build(self.state)

    def get_standard_zvp_hl(self) -> List[BOStep]:
        from bot.logic.spending.build_order_v2.standard_zvp_hl import get_build
        return get_build(self.state)

    def get_standard_zvt_hlb(self) -> List[BOStep]:
        from bot.logic.spending.build_order_v2.standard_zvt_hlb import get_build
        return get_build(self.state)
    
    def standard_build_order_comp(self) -> (Dict[UnitTypeId, int], List[UnitTypeId]):
        from bot.logic.spending.build_order_v2.standard_build_order import get_army_comp
        return get_army_comp(self.state)
    
    def standard_zvp_hl_comp(self) -> (Dict[UnitTypeId, int], List[UnitTypeId]):
        from bot.logic.spending.build_order_v2.standard_zvp_hl import get_army_comp
        return get_army_comp(self.state)

    def standard_zvt_hlb_comp(self) -> (Dict[UnitTypeId, int], List[UnitTypeId]):
        from bot.logic.spending.build_order_v2.standard_zvt_hlb import get_army_comp
        return get_army_comp(self.state)