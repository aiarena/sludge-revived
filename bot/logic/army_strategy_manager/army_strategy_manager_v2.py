from typing import Dict, List
import random

from sc2.units import Units
from sc2.unit import Unit
from sc2 import AbilityId, UnitTypeId, BotAI
from sc2.position import Point3, Point2

from .army_strategy_manager_interface import ArmyStrategyManagerInterface
from bot.services.state_service import StateService
import bot.injector as injector
from bot.services.action_service import ActionService
from bot.services.debug_service import DebugService
from bot.services.threat_service import Threat
from bot.util.unit_type_utils import get_resource_value
from bot.model.scouting_information import ScoutingInformation

class AssignedUnits:
    units: Units
    value: int = 0
    antiair_value: int = 0
    antiground_value: int = 0

class ArmyStrategyManagerv2(ArmyStrategyManagerInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.debug: DebugService = injector.inject(DebugService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.bot = injector.inject(BotAI)
        self.threat_to_assigned_units: Dict[Threat, AssignedUnits] = {}
        self.unassigned_units: Units = Units([], self.bot._game_data)
        self.all_assigned_units: Units = Units([], self.bot._game_data)
        self.proxy_scouts: Units = Units([], self.bot._game_data)
    async def on_step(self):
        self.unassigned_units = self.state.own_army_units.tags_not_in(self.all_assigned_units.tags)
        # unassign units from threats that no longer exist
        threats_to_pop = []
        for threat in self.threat_to_assigned_units.keys():
            if not threat in self.state.threats:
                units = self.threat_to_assigned_units[threat].units
                for unit in units:
                    self.all_assigned_units.remove(unit)
                threats_to_pop.append(threat)
        for threat in threats_to_pop:
            self.threat_to_assigned_units.pop(threat)


        # Only consider threats that have moved out on the map
        positions: List[Point2] = [
            self.state._bot.enemy_start_locations[0],
            self.state.enemy_natural_position
        ]
        for townhall in self.state.enemy_townhalls:
            if not townhall.position == self.state._bot.enemy_start_locations[0] or townhall.position == self.state.enemy_natural_position:
                positions.append(townhall.position)

        threats = self.state.threat_service.threats_further_than_plist(30, positions)

        # ------------------------#
        # assign units to threats #
        # ------------------------#
        # TODO: send detection vs stealth units
        # TODO: send antiair vs air units

        self._assign_and_move_units(threats)

        #------------------------------------#
        # attack, send harassment units etc. #
        #------------------------------------#
        # attack closest enemy structure or base with all remaining units
        # HACK: stargate and moved out check to beat lvlup's voidray rush
        engage_threshold = 1.2
        if 200 - self.state.resources.supply.used < 10:
            engage_threshold = 0.8
        if engage_threshold * self.state.own_army_value > self.state.enemy_army_value or {ScoutingInformation.STARGATE, ScoutingInformation.ENEMY_MOVED_OUT}.issubset(self.state.scouting_information) or 200 - self.state.resources.supply.used < 10:
            for unit in self.unassigned_units.tags_not_in(self.proxy_scouts.tags):
                pos = self.state._bot.enemy_start_locations[0]
                if self.state.enemy_structures.exists:
                    closest_enemy_structure = self.state.enemy_structures.closest_to(unit)
                    if closest_enemy_structure:
                        pos = closest_enemy_structure.position
                elif self.state.own_units.closer_than(10, pos).exists:
                    pos = random.choice(list(self.state._bot.expansion_locations.keys()))
                    self.proxy_scouts.append(unit)
                self.action_service.add(unit.tag, unit.attack(pos), 10)
            self.unassigned_units = []
        else:
            for unit in self.unassigned_units.tags_not_in(self.proxy_scouts.tags):
                pos = random.choice(list(self.state._bot.expansion_locations.keys()))
                self.proxy_scouts.append(unit)
                self.action_service.add(unit.tag, unit.move(pos), 10)

        self.proxy_scouts = self.state.own_units.tags_in(self.proxy_scouts.tags)
        for scout in self.proxy_scouts.copy():
            if scout.is_idle or len(scout.orders) == 0:
                self.proxy_scouts = self.proxy_scouts.tags_not_in({scout.tag})

        #--------------------------------#
        # send leftover units to threats #
        #--------------------------------#
        # units are commanded to go to the nearest threat, but not assigned to it
        threat_count = len(threats)
        unassigned_count = len(self.unassigned_units)
        if threat_count > 0:
            units_per_threat = (unassigned_count // threat_count)
        else:
            units_per_threat = 0
        
        for threat in threats:
            for idx in range(units_per_threat):
                unit = self.unassigned_units.closest_to(threat.location)
                self.action_service.add(unit.tag, unit.move(threat.location), 10)
                self.unassigned_units.remove(unit)
                pos = unit.position
                self.debug.text_world(f'Extra', Point3((pos.x, pos.y, 10)), None, 12)


        #----------------------------------#
        # send leftovers to idle positions #
        #----------------------------------#

        # TODO: better logic for unassigned units
        # self.action_service.command_group(self.unassigned_units, AbilityId.MOVE, self.state._bot.enemy_start_locations[0], 9)


    def _assign_and_move_units(self, threats: List[Threat]):
        for threat in threats:
            # create assigned units object
            if not threat in self.threat_to_assigned_units:
                temp = AssignedUnits()
                temp.units = Units([], self.bot._game_data)
                temp.value = 0
                self.threat_to_assigned_units[threat] = temp
            assigned_units = self.threat_to_assigned_units[threat]
            # assign units to threat
            while threat.air_value > assigned_units.antiair_value and not self.unassigned_units.empty:
                can_attack_air = self.unassigned_units.filter(lambda u: u.can_attack_air)
                if can_attack_air.exists:
                    closest = can_attack_air.closest_to(threat.location)
                else:
                    break
                value: int = get_resource_value(self.state._bot, closest.type_id)
                assigned_units.value += (value[0] + value[1])
                assigned_units.antiair_value += (value[0] + value[1])
                assigned_units.units.append(closest)
                self.unassigned_units.remove(closest)
                self.all_assigned_units.append(closest)

            while threat.value > assigned_units.value and not self.unassigned_units.empty:
                if threat.ground_value - assigned_units.antiground_value <= 0 and not threat.units({UnitTypeId.MEDIVAC, UnitTypeId.WARPPRISM, UnitTypeId.OVERLORDTRANSPORT}).exists:
                    break
                antiground = self.unassigned_units.filter(lambda u: u.can_attack_ground)
                if antiground.exists:
                    closest: Unit = antiground.closest_to(threat.location)
                else:
                    break
                if not closest:
                    break
                value: int = get_resource_value(self.state._bot, closest.type_id)
                assigned_units.value += (value[0] + value[1])
                assigned_units.antiground_value += (value[0] + value[1])
                assigned_units.units.append(closest)
                self.unassigned_units.remove(closest)
                self.all_assigned_units.append(closest)
            
            # move assigned units
            pos: Point2 = threat.location
            if self.state.own_townhalls.exists:
                closest_base = self.state.own_townhalls.closest_to(threat.location)
                if threat.location.distance_to(closest_base.position) < 40 and threat.units({UnitTypeId.MEDIVAC, UnitTypeId.WARPPRISM, UnitTypeId.OVERLORDTRANSPORT}).exists and threat.ground_value == 0:
                    pos = closest_base.position
            for unit in assigned_units.units:
                self.action_service.add(unit.tag, unit.move(pos), 10)
            