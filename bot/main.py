import json
from pathlib import Path
import typing

import sc2
from sc2.unit_command import UnitCommand
from sc2.unit import Unit
from sc2.position import Point2, Point3
from sc2 import UnitTypeId

from .debug.debug_utils import PrintExecutionTime
from .chat.chat_interface import ChatInterface
import bot.injector as injector
from .configuration.configuration_interface import ConfigurationInterface
from .configuration.basic_configuration import BasicConfiguration
from .services.state_service import StateService
from .services.action_service import ActionService
from .logic.logic_interface import LogicInterface
from .services.role_service import RoleService
from .model.unit_role import UnitRole
from .services.debug_service import DebugService
from bot.services.pathing_service import PathingService
#from .logic.army_strategy_manager.default_army_strategy_manager import DefaultArmyStrategyManager
from bot.services.unit_type_service import UnitTypeService
from bot.services.eco_balance_service import EcoBalanceService
from bot.configuration.basic_configuration import BasicConfiguration
from bot.hooks import Hooks, hooks

class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        config: BasicConfiguration = BasicConfiguration()
        injector.injector.init(config, self)
        self.hooks: Hooks = hooks
        self.chat: ChatInterface = injector.inject(ChatInterface)
        self.logic: LogicInterface = injector.inject(LogicInterface)
        self.state_service: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.role_service: RoleService = injector.inject(RoleService)
        self.debug_service: DebugService = injector.inject(DebugService)
        self.eco_balance: EcoBalanceService = injector.inject(EcoBalanceService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.pathing_service: PathingService = injector.inject(PathingService)
        super().__init__()

    async def on_unit_destroyed(self, unit_tag):
        self.hooks.call('on_unit_destroyed', unit_tag)

        if unit_tag in self.role_service.tags:
            self.role_service.removeTag(unit_tag)

    async def on_unit_created(self, unit: Unit):
        self.hooks.call('on_unit_created', unit)
    
    async def on_building_construction_complete(self, unit):
        self.hooks.call('on_building_construction_complete', unit)
    
    async def saturate_gas(self, unit: Unit):
        actions = []
        for drone in self.units(UnitTypeId.DRONE).closer_than(15, unit.position).take(3, require_all = False):
            actions.append(drone.gather(unit))
        await self.do_actions(actions)

    # @PrintExecutionTime
    async def on_step(self, iteration):
        if iteration == 0:
            await self.do(self.units(UnitTypeId.LARVA).random.train(UnitTypeId.DRONE))
            await self.worker_split()
            self.state_service.on_first_iteration()
            self.hooks.call('on_init')
            self.logic.on_init()
        self.eco_balance.init_step()
        self.state_service.update()
        self.pathing_service.update()
        await self.chat.on_step(iteration)
        await self.logic.on_step(iteration)
        actions = self.action_service.get_all()
        await self.do_actions(actions)

        # render debug text for banners
        #for banner in self.strategy.banners:
        #    pos = banner.location
        #    self.debug_service.text_world(f'Banner: {banner.requested_value - banner.assigned_value}', Point3((pos.x, pos.y, 10)), None, 12)
        #for threat in self.state_service.threats:
        #    pos = threat.location
        #    self.debug_service.text_world(f'Threat: {threat.value}, {threat.ground_value}, {threat.air_value}, {threat.cloak_value}', Point3((pos.x, pos.y, 10)), None, 12)
        # await self.debug_service.render_debug()
        self.action_service.clear()
        self.state_service.previous_iter_own_units = self.state_service.own_units
    
    async def worker_split(self):
        for worker in self.workers:
            closest_mineral_patch = self.state.mineral_field.closest_to(worker)
            await self.do(worker.gather(closest_mineral_patch))