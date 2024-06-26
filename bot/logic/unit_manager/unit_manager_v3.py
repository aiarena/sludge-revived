from math import sqrt
from typing import Union
from collections import defaultdict
import math
import random

from sc2 import UnitTypeId, AbilityId
from sc2.units import Units
from sc2.unit import Unit
from sc2.position import Point3, Rect

from bot.model.unit_type_abstraction import UnitTypeAbstraction
from bot.logic.army_strategy_manager.army_strategy_manager_interface import ArmyStrategyManagerInterface
from bot.logic.unit_manager.priority_calculations_v2 import unit_desperation_threshold, enemy_group_priority, unit_to_group_priority
import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.action_service import ActionService
from bot.services.unit_group_service import UnitGroupService, UnitGroup
from bot.services.unit_type_service import UnitTypeService
from bot.util.priority_queue import PriorityQueue
from .group_tactics import GroupTactics, distance_from_boundary
from .assigned_group import AssignedGroup
from .micro import Micro
from .worker_distribution import WorkerDistributor
from bot.logic.spending_actions.default_spending_actions import DefaultSpendingActions
from bot.logic.overlord_manager import OverlordManager
from bot.logic.queen_manager.default_queen_manager import DefaultQueenManager

from bot.services.debug_service import DebugService
from bot.util.unit_type_utils import is_combat_unit, get_unit_origin_type
from bot.util.mapping_functions import steep_decline

class UnitManager_v3:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.debug_service: DebugService = injector.inject(DebugService)
        self.group_service: UnitGroupService = injector.inject(UnitGroupService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.group_tactics: GroupTactics = GroupTactics()
        self.micro: Micro = Micro()
        self.worker_distributor: WorkerDistributor = WorkerDistributor()
        self.spending_actions = DefaultSpendingActions()
        self.overlord_manager = OverlordManager()
        self.queen_manager = DefaultQueenManager()

        self.assigned_groups = []
        self.previously_assigned_units = {}
        self.proxy_scouts: Units = Units([], self.state._bot._game_data)
        self.proxy_scout_idx: int = 0
        self.expansion_locations: list = []

    def on_init(self) -> None:
        expansion_locations = list(self.state._bot.expansion_locations.keys())
        expansion_locations.append(self.state._bot.enemy_start_locations[0])
        expansion_locations.sort(key=lambda p: p.distance_to(self.state._bot.enemy_start_locations[0]))
        self.expansion_locations = expansion_locations

    async def on_step(self):
        unassigned = self.state.own_units
        enemy_groups: PriorityQueue = self.state.enemy_groups
        self.assigned_groups = self.assign_groups(unassigned, enemy_groups)
        builder_units: Units = self.get_builder_units(unassigned, self.state.enemy_groups)

        assigned_tags = set()
        for g in self.assigned_groups:
            assigned_tags = assigned_tags.union(self.group_tactics.manage_group(g))
            await self.micro.micro_units(g.group.units, assigned_tags)
        unassigned = unassigned.tags_not_in(assigned_tags)

        a = await self.spending_actions.build(self.state.build_queue, builder_units)
        unassigned = unassigned.tags_not_in(a.tags)

        # saturate remaining workers
        unassigned_workers = unassigned({UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.MULE})
        self.worker_distributor.distribute_workers(unassigned_workers)
        unassigned = unassigned.tags_not_in(unassigned_workers.tags)

        unassigned_overlords = unassigned({UnitTypeId.OVERLORD, UnitTypeId.OVERSEER})
        await self.overlord_manager.on_step(unassigned_overlords)
        unassigned = unassigned.tags_not_in(unassigned_overlords.tags)

        unassigned_queens = unassigned({UnitTypeId.QUEEN})
        unassigned = unassigned.tags_not_in(await self.queen_manager.on_step(unassigned_queens))

        # use remaining units to do cool things
        # scout enemy bases with idle units
        #TODO ideally, should only reassign idle proxy scouts. However, can't really figure out how to get that working, so just putting this hack for now.

        if unassigned.exists:
            to_remove = set()
            for s in self.proxy_scouts:
                s: Unit
                tag = s.tag
                s = self.state.own_units.find_by_tag(s.tag)
                if not s or s.tag not in unassigned.tags or s.is_idle:
                    to_remove.add(tag)
            self.proxy_scouts = self.proxy_scouts.tags_not_in(to_remove)
            missing_scouts = 4 - self.proxy_scouts.amount
            new_scouts = unassigned({UnitTypeId.ZERGLING, UnitTypeId.ROACH}).sorted(lambda u: u.movement_speed, reverse=True).take(missing_scouts, require_all=False)
            for scout in new_scouts:
                scout: Unit
                self.action_service.add(scout.tag, scout.move(random.choice(self.expansion_locations)))
                self.proxy_scouts.append(scout)
            unassigned = unassigned.tags_not_in(self.proxy_scouts.tags)

        '''
        if (int(self.state.getTimeInSeconds()) % 15) == 0:
            self.reassign_proxy_scouts()
        
        num_scouting_units = 4
        if self.proxy_scouts.amount < num_scouting_units and self.state.mode == 'defend':
            unassigned_scouts = unassigned.filter(self.is_scout)
            unassigned_scouts = unassigned_scouts.sorted(lambda u: u.movement_speed, reverse=True).take(num_scouting_units - self.proxy_scouts.amount, require_all=False)
            self.append_proxy_scouts(unassigned_scouts)
        elif self.state.mode == 'attack':
            unassigned_scouts = unassigned.filter(self.is_scout)
            self.append_proxy_scouts(unassigned_scouts)
        unassigned = unassigned.tags_not_in(self.proxy_scouts.tags)
        '''
        if self.state.own_townhalls:
            # idle position at nearest base
            for unit in unassigned:
                unit: Unit
                if unit.movement_speed > 0 and unit.type_id not in {UnitTypeId.OVERLORD, UnitTypeId.LARVA}:
                    pos = unit.position.closest(self.state.own_townhalls).position
                    if unit.distance_to(pos) < 10:
                        self.action_service.add(unit.tag, unit.attack(pos))
                    else:
                        self.action_service.add(unit.tag, unit.move(pos))
                    # self.debug_service.text_world(f'IDLE', unit.position3d, None, 16)
        

    def priority_apply_unit_modifier(self, priority, enemy_group: UnitGroup, unit: Unit):
        if enemy_group.range_hull:
            dist = distance_from_boundary(enemy_group.range_hull, unit.position)
        else:
            dist = unit.position.distance_to(enemy_group.location)
        dist = min(self.state.map_diagonal_len, max(0, dist))
        dist_mod = dist / self.state.map_diagonal_len
        dist_mod = (0.5 + steep_decline(dist_mod)) ** 2

        # increase priority by if unit was assigned to this group in the last iteration
        percentage_of_previously_assigned = 0
        if unit.tag in self.previously_assigned_units:
            intersection = enemy_group.units.tags.intersection(self.previously_assigned_units[unit.tag])
            percentage_of_previously_assigned = len(intersection) / len(enemy_group.units.tags)
        prev_mod = 1 + percentage_of_previously_assigned
        
        return priority * dist_mod * prev_mod

    class Temp:
            units: Units
            value = 0
            ground_value = 0
            air_value = 0
            cloak = 0
            retreaters: Units

    def unit_activation_function(self, unit: Unit, priority, enemy_group: UnitGroup, oversaturation = 0):
        if unit.type_id == UnitTypeId.DRONE:
            return priority > 0.1 and enemy_group.units.exclude_type(UnitTypeId.REAPER).exists and (oversaturation == 0 and (
                (
                    unit.distance_to(enemy_group.units.center) < 15
                    and (self.state.own_townhalls.exists
                    and (unit.distance_to(self.state.own_townhalls.closest_to(enemy_group.location).position) < 20))
                )
                or (enemy_group.location.distance_to(self.state.own_natural_position) < 10)
                or (
                    enemy_group.units({UnitTypeId.PHOTONCANNON, UnitTypeId.PYLON}).exists
                    and enemy_group.location.distance_to_closest(self.state.own_townhalls) < 20
                ))
            ) or (
                enemy_group.value > 100
                and enemy_group.units.exclude_type({UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE}).exists
                and enemy_group.range_hull
                and distance_from_boundary(enemy_group.range_hull, unit.position) <= 1
                and self.state.own_townhalls
                and unit.position.distance_to_closest(self.state.own_townhalls) < 15
            )
        elif unit.type_id == UnitTypeId.QUEEN:
            return priority > 0 and self.state.own_townhalls.ready and (enemy_group.location.distance_to_closest(self.state.own_townhalls.ready) < 20 or (self.state._bot.has_creep(enemy_group.location) and enemy_group.location.distance_to_closest(self.state.own_townhalls.ready) < 30))
        elif unit.type_id in {UnitTypeId.CHANGELING, UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD, UnitTypeId.CHANGELINGZEALOT, UnitTypeId.CHANGELINGZERGLING, UnitTypeId.CHANGELINGZERGLINGWINGS}:
            return False
        elif unit.type_id == UnitTypeId.OVERSEER:
            return enemy_group.cloak_value > 0
        else:
            return priority > 0

    def assign_groups(self, unassigned: Units, priorities: PriorityQueue):
        groups = []
        units = unassigned.not_structure.filter(is_combat_unit)

        d = {}
        for enemy_group in priorities:
            t = self.Temp()
            t.units = Units([], self.state._bot._game_data)
            t.retreaters = Units([], self.state._bot._game_data)
            d[enemy_group] = t
        
        #assign army units
        unit_to_priorities = defaultdict(PriorityQueue)
        for unit in units:
            for p in priorities.iterate2():
                priority = self.priority_apply_unit_modifier(p[1], p[0], unit)
                unit_to_priorities[unit].enqueue(p[0], priority)

        #sort units so that those who have a very high priority for the first enemy group
        #and low priority for the rest are assigned first
        def sort_by_diff(unit: Unit):
            s = 0
            if not unit_to_priorities[unit].isEmpty():
                prio = unit_to_priorities[unit].peek2()
                enemy_group = prio[0]
                priority = prio[1]
                percentage_of_previously_assigned = 0
                if unit.tag in self.previously_assigned_units:
                    intersection = enemy_group.units.tags.intersection(self.previously_assigned_units[unit.tag])
                    percentage_of_previously_assigned = len(intersection) / len(enemy_group.units.tags)
                    s = 0.5 + (percentage_of_previously_assigned / 2) * priority
            return s
        
        if not priorities.isEmpty():
            units = units.sorted(sort_by_diff, True)
        
        ##
        for unit in units:
            unit: Unit
            sorted_enemy_groups = PriorityQueue()
            for p in unit_to_priorities[unit].iterate2():
                priority = p[1]
                own_val = d[p[0]].value
                enemy_val = p[0].value

                #should_fight, val = self.group_tactics.evaluate_engagement(d[p[0]], p[0], show_group_vals=True)
                #own_val, enemy_val = val
                
                # dont send lings vs voidrays
                if not unit.can_attack_air:
                    # TODO performance: dont recalculate for every unit
                    priority -= p[0].percentage_of_air_in_group * priority
                
                # group oversaturation
                oversaturation = 0
                if own_val >= enemy_val:
                    diff = own_val - enemy_val
                    oversaturation = max(0.01, diff / (enemy_val if enemy_val else 1))
                    mult = max(0.01, 1 - oversaturation)
                    priority *= 0.5 + (mult / 2)
                
                if self.unit_activation_function(unit, priority, p[0], oversaturation):
                    sorted_enemy_groups.enqueue(p[0], priority)
            if sorted_enemy_groups.isEmpty():
                continue
            enemy_group: UnitGroup = sorted_enemy_groups.peek()
            # self.debug_service.text_world(f'{round(sorted_enemy_groups.peek2()[1],2)}', Point3((unit.position3d.x, unit.position3d.y - 0.35, unit.position3d.z)), Point3((0, 255, 0)), 12)
            if (not unit.can_attack_air and enemy_group.percentage_of_air_in_group > 0.8) or (unit.type_id in {UnitTypeId.DRONE} and d[enemy_group].value > enemy_group.value):
                d[enemy_group].retreaters.append(unit)
            else:
                d[enemy_group].units.append(unit)
                # TODO consider cloak values
                d[enemy_group].value += self.unit_type.get_unit_combat_value_enemy_group(unit.type_id, enemy_group.units) * sum(self.unit_type.get_resource_value(unit.type_id))
        self.previously_assigned_units = {}
        for key, value in d.items():
            a = AssignedGroup()
            a.enemies = key
            a.group = self.group_service.create_group(value.units)
            a.retreaters = self.group_service.create_group(value.retreaters)
            groups.append(a)
            for unit in a.group.units:
                self.previously_assigned_units[unit.tag] = a.enemies.units.tags
        
        return groups

    def get_builder_units(self, own_units: Units, enemy_groups: PriorityQueue) -> {'unit tags'}:
        '''Determines if any units in own group are in the ideal conditions to build into a different unit.
        Returns all units that can build.'''
        origins_build_queue = {get_unit_origin_type(unit_id) for unit_id in self.state.build_queue}.union({UnitTypeId.DRONE, UnitTypeId.PROBE, UnitTypeId.SCV})
        return own_units.of_type(origins_build_queue)

    def append_proxy_scouts(self, own_units : Units) -> None:
        '''Will append a unit even if that unit is already in self.proxy_scouts, so be careful!'''
        for unit in own_units:
            self.give_scouting_order(unit)
            self.proxy_scouts.append(unit)

    def give_scouting_order(self, scout: Unit) -> None:
        '''Gives a scouting order to the given scout unit.'''
        if self.proxy_scout_idx == len(self.expansion_locations) - 1:
            self.proxy_scout_idx = 0
        pos = self.expansion_locations[self.proxy_scout_idx]
        self.proxy_scout_idx += 1
        self.action_service.add(scout.tag, scout.move(pos), 10)

    def reassign_proxy_scouts(self) -> None:
        '''Reassigns proxy scouts that have completed their mission. Deletes proxy scouts who have died.'''
        #remove dead scouts from self.proxy_scouts
        #TODO only do this when unit dies (on_unit_destroyed), however need to be careful about making this hookable because on_step is explicitly called
        self.proxy_scouts = self.proxy_scouts.tags_in({scout.tag for scout in self.proxy_scouts if scout in self.state.own_units})
        #assign scouts that are done to a new task
        scouts_that_are_done: set = {scout for scout in self.proxy_scouts if scout.is_idle}
        for scout in scouts_that_are_done:
            self.give_scouting_order(scout)

    def is_scout(self, u: Unit) -> bool:
        '''Determines whether or not the given unit should be considered a scouting unit.'''
        return is_combat_unit(u) and u.type_id not in {UnitTypeId.DRONE, UnitTypeId.QUEEN} and not u in self.proxy_scouts
