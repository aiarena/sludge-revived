import random
from typing import Dict

from sc2 import UnitTypeId, AbilityId, Race
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3
from sc2.unit_command import UnitCommand

from bot.services.state_service import StateService
import bot.injector as injector
from bot.services.action_service import ActionService
from bot.services.debug_service import DebugService
from .group_tactics import unit_direction

class Micro:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.debug: DebugService = injector.inject(DebugService)
        self.action_service: ActionService = injector.inject(ActionService)

        self.roach_firing_cycle: Dict[str, int] = {}
    async def micro_units(self, units: Units, attacking_units: set):
        attacking_units: Units = units.tags_in(attacking_units)

        for blord in units(UnitTypeId.BROODLORD):
            if blord.weapon_cooldown < 8 and self.state.enemy_army_units.closer_than(blord.ground_range, blord.position).exists:
                self.action_service.add(blord.tag, blord.attack(blord.position), 1000)

        for unit in units({UnitTypeId.ROACH, UnitTypeId.RAVAGER, UnitTypeId.HYDRALISK}):
            unit: Unit
            command: UnitCommand = self.action_service.get(unit.tag)
            if command and command.ability == AbilityId.ATTACK:
                if unit.weapon_cooldown > 8 and self.state.enemy_army_units.exists:
                    closest: Unit = self.state.enemy_army_units.closest_to(unit.position) 
                    if closest and closest.ground_range < 1 and closest.position.distance_to(unit.position) < unit.ground_range or unit.type_id in {UnitTypeId.RAVAGER, UnitTypeId.HYDRALISK}:
                        pos = unit.position + unit.movement_speed * unit_direction(closest.position, unit.position)
                    else:
                        pos = command.target
                    self.action_service.add(unit.tag, unit.move(pos), 1000)
            elif command:
                if unit.weapon_cooldown == 0 and self.state.enemy_units.filter(lambda u: not u.is_flying).closer_than(unit.ground_range, unit.position).exists:
                    self.action_service.add(unit.tag, unit.attack(command.target), 1000)
            
        for ravager in units(UnitTypeId.RAVAGER):
            abilities = await self.state._bot.get_available_abilities(ravager)
            if abilities and len(abilities) > 0 and AbilityId.EFFECT_CORROSIVEBILE in abilities:
                nearby = self.state.enemy_units.closer_than(15, ravager)
                priority_targets = nearby({UnitTypeId.SIEGETANK, UnitTypeId.LIBERATOR})
                if priority_targets.exists:
                    self.action_service.add(ravager.tag, ravager(AbilityId.EFFECT_CORROSIVEBILE, priority_targets.closest_to(ravager).position), 1000)
                else:
                    enemies = nearby.closer_than(9, ravager.position)
                    if enemies.exists:
                        self.action_service.add(ravager.tag, ravager(AbilityId.EFFECT_CORROSIVEBILE, nearby.closest_to(enemies.center).position), 1000)
        
        for baneling in units(UnitTypeId.BANELING):
            baneling: Unit
            enemies: Units = self.state.enemy_army_units
            enemies.extend(self.state.enemy_units({UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.MULE}))
            if not enemies.exists:
                break
            nearby_enemies = enemies.closer_than(5, baneling.position)
            if not nearby_enemies.exists:
                continue
            targets_in_range = nearby_enemies.closer_than(2.2, baneling.position)
            if targets_in_range.amount >= 4:
                self.action_service.add(baneling.tag, baneling(AbilityId.EXPLODE_EXPLODE), 1000)
                continue
            closest = nearby_enemies.closest_to(nearby_enemies.center)
            commands = []
            behind = closest.position + (2 * baneling.position.direction_vector(closest.position))
            commands.append(baneling.move(behind, False))
            commands.append(baneling.move(baneling.position + 4 * closest.position.direction_vector(baneling.position), True))
            self.action_service.add(baneling.tag, commands, 1000)
        
        # Micro lings away from banes
        if self.state._bot.enemy_race == Race.Zerg:
            enemy_banes = self.state.enemy_banelings
            if enemy_banes.exists:
                for zergling in units(UnitTypeId.ZERGLING):
                    zergling: Unit
                    nearby_banes = enemy_banes.closer_than(5, zergling.position)
                    if not nearby_banes.exists:
                        continue
                    own_lings = units(UnitTypeId.ZERGLING).closer_than(7, enemy_banes.center)
                    if own_lings.exists and own_lings.amount > 1:
                        self.action_service.add(zergling.tag, zergling.move(zergling.position + (4 * nearby_banes.center.direction_vector(zergling.position))), 1001)
        
        if int(self.state.getTimeInSeconds()) % 5 == 0:
            for changeling in self.state.enemy_units({UnitTypeId.CHANGELING, UnitTypeId.CHANGELINGZERGLING, UnitTypeId.CHANGELINGZERGLINGWINGS}):
                nearby = units.filter(lambda u: u.can_attack_ground).closer_than(2, changeling.position)
                if nearby.exists:
                    self.action_service.command_group(nearby, AbilityId.ATTACK, changeling, 999)

        #drone drill back against worker rushers (TheMusZero)
        attacking_workers = attacking_units(UnitTypeId.DRONE)
        if attacking_workers:
            enemy_workers = self.state.enemy_units({UnitTypeId.DRONE, UnitTypeId.PROBE, UnitTypeId.SCV}).closer_than(10, self.state.game_info.start_location)
            if enemy_workers.exists:
                main_min_field = self.state.get_mineral_fields_for_expansion(self.state.game_info.start_location)
                mins_enemy_is_close_to: Units = main_min_field.filter(lambda min: enemy_workers.center.distance_to(min) <= 2)
                if mins_enemy_is_close_to.exists and mins_enemy_is_close_to.amount >= 3:
                    #find the farthest min (this is the one that will be drone drilled)
                    farthest_min: Unit = mins_enemy_is_close_to.sorted(lambda u: u.distance_to(self.state.game_info.start_location), reverse=True).first

                    #30% of the time attack instead of move
                    if self.state.getTimeInSeconds() % 1 >= 0.75:
                        self.action_service.command_group(attacking_workers, AbilityId.ATTACK, enemy_workers.center, 1001)
                    else:
                        self.action_service.command_group(attacking_workers, AbilityId.SMART, farthest_min, 1000)
