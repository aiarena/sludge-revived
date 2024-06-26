from typing import List, Union

from sc2.unit_command import UnitCommand
from sc2 import UnitTypeId, BotAI, AbilityId
from sc2.units import Units
from sc2.position import Point2
from sc2.ids.upgrade_id import UpgradeId

from ...util.priority_queue import PriorityQueue
from .spending_actions_interface import SpendingActionsInterface
import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.action_service import ActionService
from bot.util.unit_type_utils import get_unit_origin_type
from bot.services.debug_service import DebugService

# Zerg specific spending actions
class DefaultSpendingActions(SpendingActionsInterface):
    def __init__(self):
        self._bot: BotAI = injector.inject(BotAI)
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.debug: DebugService = injector.inject(DebugService)
    
    async def build(self, spending_list: List, units: Units) -> 'assigned Units':
        assigned = Units([], self._bot._game_data)

        self.debug.text_screen_auto(f'{self.state.placement_requests}', 0, 4)
        for placement_request in self.state.placement_requests:
            if placement_request == UnitTypeId.HATCHERY:
                placement = await self.get_building_placement(placement_request)
                builder = self.get_builder(UnitTypeId.DRONE, units, placement)
                if builder:
                    self.action_service.add(builder.tag, builder.move(placement), 99)

        spending_actions = await self.get_spending_actions(spending_list, units)
        for action in spending_actions:
            self.action_service.add(action.unit.tag, action, 100)
            assigned.append(action.unit)
        return assigned

    async def get_spending_actions(self, ids: List[Union[UnitTypeId, UpgradeId]], units: Units) -> List[UnitCommand]:
        actions: List[UnitCommand] = []
        for type_id in ids:
            action = await self.get_spending_action(type_id, units)
            if action:
                actions.append(action)
        return actions
    
    async def get_spending_action(self, target_id: Union[UnitTypeId, UpgradeId], units: Units):
        origin_type: UnitTypeId = get_unit_origin_type(target_id)
        placement = Point2((0,0))
        if origin_type == UnitTypeId.DRONE:
            placement = await self.get_building_placement(target_id)
        builder: Unit = self.get_builder(origin_type, units, placement)
        if builder:
            if origin_type == UnitTypeId.DRONE:
                return builder.build(target_id, placement)
            if isinstance(target_id, UpgradeId):
                return builder.research(target_id)
            return builder.build(target_id)

    async def get_building_placement(self, unit_id: UnitTypeId):
        pos = Point2((0,0))
        if unit_id == UnitTypeId.HATCHERY:
            return await self._bot.get_next_expansion()
        if unit_id == UnitTypeId.EXTRACTOR:
            geysers = self.state.get_own_geysers()
            for geyser in geysers:
                if await self._bot.can_place(UnitTypeId.EXTRACTOR, geyser.position):
                    return geyser
        elif unit_id == UnitTypeId.SPINECRAWLER:
            natural_mins = self.state.get_mineral_fields_for_expansion(self.state.own_natural_position)
            if natural_mins.exists:
                direction = (2 * natural_mins.center.direction_vector(self.state.own_natural_position))
                pos = self.state.own_natural_position + direction
            else:
                pos = self.state.own_natural_position
        elif unit_id == UnitTypeId.SPORECRAWLER:
            cur_spore_crawlers_point2s = [spore.position for spore in self.state.own_units(UnitTypeId.SPORECRAWLER)]
            #TODO less hacky way of getting target position of workers who are going to make spore crawlers
            for w in self.state.own_units(UnitTypeId.DRONE):
                for o in w.orders:
                    if o.ability == self.state._bot._game_data.units[UnitTypeId.SPORECRAWLER.value].creation_ability:
                        target_pt = Point2((o.target.x, o.target.y))
                        cur_spore_crawlers_point2s.append(target_pt)

            for base in self.state.own_townhalls.sorted_by_distance_to(self.state.own_natural_position):
                #if the base does not already have a spore crawler, create one in the mineral line
                if cur_spore_crawlers_point2s and any(spore.distance_to(base) <= 10 for spore in cur_spore_crawlers_point2s):
                    continue
                base_mins = self.state.get_mineral_fields_for_expansion(base.position)
                if base_mins.exists:
                    direction = (0.5 * base_mins.center.direction_vector(base.position))
                    pos = base.position + direction
                    break
                else:
                    pos = base.position
                    break
        else:
            pos = self.state.game_info.start_location + (5 * self.state.main_minerals.center.direction_vector(self.state.game_info.start_location))
        return await self._bot.find_placement(unit_id, near = pos)


    def get_builder(self, type_id: UnitTypeId, units: Units, placement: Point2) -> 'sc2.unit.Unit' or None:
        if type_id == UnitTypeId.DRONE:
            drones = units(UnitTypeId.DRONE).filter(lambda u: not u.is_carrying_minerals and not u.is_carrying_vespene)
            if drones.exists and placement:
                return drones.closest_to(placement)
            elif placement and units(UnitTypeId.DRONE).exists:
                return units(UnitTypeId.DRONE).closest_to(placement)
            elif units(UnitTypeId.DRONE).exists:
                return units(UnitTypeId.DRONE).prefer_idle.first
        else:
            units = units(type_id)
            #have buildings do this instead of the typical check whenever there are multiple of the same building
            if type_id == UnitTypeId.HATCHERY or type_id == UnitTypeId.EVOLUTIONCHAMBER:
                available_structures = units.filter(lambda u: u.is_ready and u.is_idle)
                if available_structures.exists:
                    return available_structures.first
            if not units.empty:
                return units.furthest_to(self._bot.enemy_start_locations[0])