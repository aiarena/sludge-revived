import math
import random
from typing import List

from sc2 import BotAI, UnitTypeId, AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.units import Units
from sc2.position import Point2

from .logic_interface import LogicInterface
import bot.injector as injector
from .spending.spending_interface import SpendingInterface
from .spending_actions.spending_actions_interface import SpendingActionsInterface
from bot.services.action_service import ActionService
from bot.model.unit_type_abstraction import UnitTypeAbstraction
from bot.logic.resource_manager.resource_manager_interface import ResourceManagerInterface
from bot.services.state_service import StateService
from bot.logic.queen_manager.queen_manager_interface import QueenManagerInterface
from bot.logic.unit_manager.unit_manager_v3 import UnitManager_v3
#from bot.logic.army_strategy_manager.army_strategy_manager_interface import ArmyStrategyManagerInterface
#from .army_tactics_manager.army_tactics_manager_interface import ArmyTacticsManagerInterface
from bot.services.debug_service import DebugService
#from .army_micro_manager.army_micro_manager_interface import ArmyMicroManagerInterface
from .overlord_manager import OverlordManager
from bot.services.eco_balance_service import EcoBalanceService
from bot.util.priority_queue import PriorityQueue
from bot.services.unit_type_service import UnitTypeService
from .drone_micro import DroneMicro

class DefaultLogic(LogicInterface):
    def __init__(self):
        self.debug: DebugService = injector.inject(DebugService)
        self.spending: SpendingInterface = injector.inject(SpendingInterface)
        self.spending_actions: SpendingActionsInterface = injector.inject(SpendingActionsInterface)
        self.action_service: ActionService = injector.inject(ActionService)
        self.resource_manager: ResourceManagerInterface = injector.inject(ResourceManagerInterface)
        self.eco_balance: EcoBalanceService = injector.inject(EcoBalanceService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.state: StateService = injector.inject(StateService)
        self.bot: BotAI = injector.inject(BotAI)
        self.queen_manager: QueenManagerInterface = injector.inject(QueenManagerInterface)
        #self.army_strategy_manager: ArmyStrategyManagerInterface = injector.inject(ArmyStrategyManagerInterface)
        #self.army_tactics_manager: ArmyTacticsManagerInterface = injector.inject(ArmyTacticsManagerInterface)
        #self.army_micro_manager: ArmyMicroManagerInterface = injector.inject(ArmyMicroManagerInterface)

        self.unit_manager = injector.inject(UnitManager_v3)

        self.drone_micro: DroneMicro = DroneMicro()
        self.overlord_manager: OverlordManager = OverlordManager()

        self.spawned = False

    def on_init(self) -> None:
        self.unit_manager.on_init()

    async def on_step(self, iteration):
        '''if self.state.getTimeInSeconds() > 4 * 60 and not self.spawned:
            for i in range(30):
                O = self.state.own_natural_position
                A = O.direction_vector(self.state._bot.game_info.map_center)
                pos: Point2 = O + 15*A
                pos = Point2((pos.x + random.randint(-20, 20), pos.y + random.randint(-20, 20)))
                await self.bot._client.debug_create_unit([[UnitTypeId.MARINE, 1, pos, 2]])
            self.spawned = True
        '''
        #if self.state.own_units(UnitTypeId.BATTLECRUISER).exists:
        #    bc = self.state.own_units(UnitTypeId.BATTLECRUISER).random
        #    print(bc.ground_range, bc.air_range)
        
        spending_priorities: PriorityQueue = self.spending.get_current_priorities()

        for idx, e in enumerate(spending_priorities.iterate2()):
            if e[1] > 5000:
                color = (255, 0, 0)
            elif e[1] > 500:
                color = (255, 165, 0)
            elif e[1] > 10:
                color = (0, 255, 0)
            else:
                color = (128, 128, 128)
            self.debug.text_screen_auto(f'{e[0].name}', idx, 0, color)
            self.debug.text_screen_auto(f'{e[1]}', idx, 1, color)
            
        m = 0
        v = 0
        for p in spending_priorities:
            if isinstance(p, UnitTypeId):
                value = self.unit_type.get_resource_value(p)
                m += value[0]
                v += value[1]
            if isinstance(p, UpgradeId):
                value = self.unit_type.get_resource_value_upgrade(p)
                m += value[0]
                v += value[1]

        self.eco_balance.request_eco(m, v)

        spending_list: List[UnitTypeId] = self.resource_manager.get_spending_list(spending_priorities)
        self.state.build_queue = spending_list

        #spending_actions = await self.spending_actions.get_spending_actions(spending_list)
        #for action in spending_actions:
        #    self.action_service.add(action.unit.tag, action)

        if math.floor(self.state.getTimeInSeconds()) % 25 == 0:
            self.set_rally_points()
        
        #await self.queen_manager.on_step(iteration)
        #if iteration % 3 == 0:
        #    await self.army_strategy_manager.on_step()
        #await self.army_tactics_manager.on_step()
        #await self.army_micro_manager.on_step(iteration)
        #await self.overlord_manager.on_step(iteration)
        #await self.drone_micro.on_step(iteration)

        await self.unit_manager.on_step()

        #if math.floor(self.state.getTimeInSeconds()) % 15 == 0:
            #await self.bot.distribute_workers()
        #if iteration % 4 == 0:
        #    self.eco_balance.distribute_workers3()
    
    def set_rally_points(self):
        unfinished_hatches: Units = self.state.own_units(UnitTypeId.HATCHERY).not_ready
        if unfinished_hatches.exists:
            for hatch in unfinished_hatches:
                mineral_fields = self.bot.state.mineral_field
                if mineral_fields.exists:
                    mineral_field = self.bot.state.mineral_field.closest_to(hatch.position)
                    self.action_service.add(hatch.tag, hatch(AbilityId.RALLY_HATCHERY_WORKERS, mineral_field))