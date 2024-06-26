from typing import List

from sc2.units import Units
from sc2 import AbilityId
from sc2.position import Point3

from .army_tactics_manager_interface import ArmyTacticsManagerInterface
import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.action_service import ActionService
from bot.util.unit_utils import group_army
from bot.util.unit_type_utils import calculate_combat_value
from bot.services.debug_service import DebugService

class DefaultArmyTacticsManager(ArmyTacticsManagerInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.debug: DebugService = injector.inject(DebugService)
    async def on_step(self):
        groups: List[Units] = group_army(self.state.own_army_units, 15)
        for group in groups:
            nearby_enemies: Units = self.state.enemy_army_units.closer_than(20, group.center)
            if not nearby_enemies.exists:
                continue
            surrounding_units: Units = self.state.own_army_units.tags_not_in(group.tags).closer_than(20, nearby_enemies.center)
            surrounding_units_value = calculate_combat_value(self.state._bot, surrounding_units)
            group_value = calculate_combat_value(self.state._bot, group)
            total_value = surrounding_units_value + group_value
            group_center = group.center
            nearby_enemies_value = calculate_combat_value(self.state._bot, nearby_enemies)
            # self.debug.text_world(f'{total_value - nearby_enemies_value}', Point3((group_center.x, group_center.y, 10)), None, 12)
            if total_value > nearby_enemies_value:
                self.action_service.command_group(group, AbilityId.ATTACK, nearby_enemies.center, 100)
            else:
                sub_groups = group_army(group, 4)
                for sub_group in sub_groups:
                    if sub_group.center.distance_to(nearby_enemies.center) > 5:
                        direction = nearby_enemies.center.direction_vector(sub_group.center)
                        pos = sub_group.center + 10 * direction
                        self.action_service.command_group(sub_group, AbilityId.MOVE, pos, 100)
    