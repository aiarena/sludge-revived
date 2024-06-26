from typing import List, Dict

from sc2.position import Point2, Point3
from sc2.units import Units
from sc2 import BotAI

from .army_strategy_manager_interface import ArmyStrategyManagerInterface
from bot.services.state_service import StateService
import bot.injector as injector
from bot.services.action_service import ActionService
from bot.util.unit_type_utils import calculate_combat_value, get_resource_value
from bot.services.debug_service import DebugService

# Priority magnitude: 10

class StrategicBanner():
    def __init__(self):
        self.location: Point2 = None
        self.requested_value: int = 0
        self.assigned_value: int = 0
        self.assigned_units: Units = Units([], self.bot._game_data)
    

# BEHOLD, MASSIVE HACKS AHEAD
# TODO: move banners to a BannerService

class DefaultArmyStrategyManager(ArmyStrategyManagerInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.debug: DebugService = injector.inject(DebugService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.tag_to_banner: Dict[str, StrategicBanner] = {}
        self.banners: List[StrategicBanner] = []
        self.bot: BotAI = injector.inject(BotAI)
    async def on_step(self):
        # remove old banners
        for banner in list(self.banners):
            if not self.state.enemy_army_units.closer_than(8, banner.location).exists:
                self.banners.remove(banner)
                for unit in banner.assigned_units:
                    del self.tag_to_banner[unit.tag]

        # set up banners for nearby enemy groups
        for group in self.state.enemy_army_groups:
            if not self.state.point_closer_than_n_to_units(group.center, 30, self.state._bot.owned_expansions):
                continue
            cont = False
            for b in self.banners:
                if group.center.is_closer_than(8, b.location):
                    b.location = group.center
                    b.requested_value = 1.5 * calculate_combat_value(self.state._bot, group)
                    cont = True
                    break
            if cont:
                continue
            banner = StrategicBanner()
            banner.location = group.center
            banner.requested_value = 1.5 * calculate_combat_value(self.state._bot, group)
            self.banners.append(banner)

        # assign units to banners
        for banner in self.banners:
            if not self.state.own_army_units.exists:
                break
            units: Units = Units(self.state.own_army_units.filter(lambda u: not u.tag in self.tag_to_banner.keys()))
            while banner.assigned_value < banner.requested_value:
                if not units.exists:
                    break
                closest: Unit = units.closest_to(banner.location)
                if not closest:
                    break
                value: int = get_resource_value(self.state._bot, closest.type_id)
                banner.assigned_value += (value[0] + value[1])
                banner.assigned_units.append(closest)
                units.remove(closest)
                self.tag_to_banner[closest.tag] = banner
        
        # give assigned units actions
        for banner in self.banners:
            for unit in banner.assigned_units:
                self.action_service.add(unit.tag, unit.move(banner.location), 10)
        
        non_assigned_units: Units = self.state.own_army_units.tags_not_in(self.tag_to_banner.keys())
        if non_assigned_units.exists:
            if self.state.own_army_value > self.state.enemy_army_value:
                for non_assigned_unit in non_assigned_units:
                    self.action_service.add(non_assigned_unit.tag, non_assigned_unit.move(self.state._bot.enemy_start_locations[0]), 10)
            else:
                for non_assigned_unit in non_assigned_units:
                    if not non_assigned_unit.position.is_closer_than(15, self.state.game_info.start_location):
                        self.action_service.add(non_assigned_unit.tag, non_assigned_unit.move(self.state.game_info.start_location), 10)
    