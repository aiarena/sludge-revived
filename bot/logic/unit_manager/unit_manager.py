from typing import Union

from sc2 import UnitTypeId
from sc2.units import Units
from sc2.unit import Unit

from bot.model.unit_type_abstraction import UnitTypeAbstraction
from bot.logic.army_strategy_manager.army_strategy_manager_interface import ArmyStrategyManagerInterface
import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.unit_group_service import UnitGroupService, UnitGroup
from bot.services.unit_type_service import UnitTypeService
from bot.util.priority_queue import PriorityQueue
from bot.util.unit_type_utils import not_attacking_combat_units
from .group_tactics import GroupTactics, distance_from_boundary
from .assigned_group import AssignedGroup
from .worker_distribution import WorkerDistributor
from bot.logic.spending_actions.default_spending_actions import DefaultSpendingActions
from bot.logic.overlord_manager import OverlordManager
from bot.logic.queen_manager.default_queen_manager import DefaultQueenManager

type_priority_multiplier = {
    UnitTypeId.PYLON: 0.8,
    UnitTypeId.NEXUS: 0.9,
    UnitTypeId.BARRACKS: 0.2,
}

class UnitManager:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.group_service: UnitGroupService = injector.inject(UnitGroupService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.group_tactics: GroupTactics = GroupTactics()
        self.worker_distributor: WorkerDistributor = WorkerDistributor()
        self.spending_actions = DefaultSpendingActions()
        self.overlord_manager = OverlordManager()
        self.queen_manager = DefaultQueenManager()

        self.assigned_groups = []

    async def on_step(self):
        unassigned = self.state.own_units
        priorities: PriorityQueue = self.group_and_prioritize_enemies()
        self.assigned_groups = self.assign_groups3(unassigned, priorities)
        assigned_tags = set()
        for g in self.assigned_groups:
            assigned_tags = assigned_tags.union(g.group.units.tags)
            self.group_tactics.manage_group(g)
        unassigned = unassigned.tags_not_in(assigned_tags)

        a = await self.spending_actions.build(self.state.build_queue, unassigned)
        unassigned = unassigned.tags_not_in(a.tags)

        # saturate remaining workers
        unassigned_workers = unassigned({UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.MULE})
        self.worker_distributor.distribute_workers(unassigned_workers)
        unassigned = unassigned.tags_not_in(unassigned_workers.tags)

        unassigned_overlords = unassigned({UnitTypeId.OVERLORD, UnitTypeId.OVERSEER})
        await self.overlord_manager.on_step(unassigned_overlords)
        unassigned = unassigned.tags_not_in(unassigned_overlords)

        unassigned_queens = unassigned({UnitTypeId.QUEEN})
        await self.queen_manager.on_step(unassigned_queens)
        unassigned = unassigned.tags_not_in(unassigned_queens)
    
    def group_and_prioritize_enemies(self) -> PriorityQueue:
        res = PriorityQueue()
        unassigned = self.state.enemy_units

        can_attack = unassigned.filter(lambda u: u.can_attack)
        can_attack.extend(self.state.enemy_units.of_type(not_attacking_combat_units))
        groups = self.group_service.create_groups(can_attack)
        for group in groups:
            p = self.prioritize_group(group)
            res.enqueue(group, p)
        unassigned = unassigned.tags_not_in(can_attack.tags)

        groups = self.group_service.create_groups(unassigned)
        for group in groups:
            p = self.prioritize_group(group)
            res.enqueue(group, p)

        return res

    def prioritize_group(self, group: UnitGroup) -> int:
        val = 0
        for unit in group.units:
            unit: Unit
            res = self.unit_type.get_resource_value(unit.type_id)
            proxy_multiplier = 1
            type_multiplier = 1
            if unit.type_id in type_priority_multiplier.keys():
                type_multiplier = type_priority_multiplier[unit.type_id]
            elif not unit.can_attack:
                type_multiplier = 0.5
            if group.location.distance_to_closest(self.state.own_townhalls) < 20 and group.units.structure.exists:
                proxy_multiplier = 10
            val += self.unit_type.get_unit_combat_value_hp_multiplier(unit) * (res[0] + res[1]) * proxy_multiplier * type_multiplier
        
        mining_bases = self.state.own_townhalls.filter(lambda u: u.assigned_harvesters > 0)
        if mining_bases.exists:
            div = group.location.distance_to_closest(mining_bases)
        else:
            div = group.location.distance_to_closest(self.state.own_townhalls)
        return val / div

    def priority_apply_unit_modifier(self, priority, enemy_group: UnitGroup, unit: Unit):
        d = distance_from_boundary(enemy_group.range_hull, unit.position)
        if d == 0:
            return priority / 0.1
        elif d <= max(unit.ground_range, unit.air_range) + unit.movement_speed:
            return priority / d * 10
        else:
            return priority / d

    def assign_groups3(self, unassigned: Units, priorities: PriorityQueue):
        class Temp:
            units: Units
            value = 0
            ground_value = 0
            air_value = 0
            cloak = 0
        
        groups = []
        units = unassigned.not_structure.filter(lambda u: u.can_attack)
        units.extend(unassigned.of_type(not_attacking_combat_units))
        units = units.sorted(lambda u: self.unit_priority_threshold(u))
        d = {}
        for enemy_group in priorities:
            t = Temp()
            t.units = Units([], self.state._bot._game_data)
            d[enemy_group] = t
        
        unit_to_priorities = {}
        for unit in units:
            unit_to_priorities[unit] = PriorityQueue()
            for p in priorities.iterate2():
                priority = self.priority_apply_unit_modifier(p[1], p[0], unit)
                unit_to_priorities[unit].enqueue(p[0], priority)

        def sort_by_diff(unit: Unit):
            s = 2 * unit_to_priorities[unit].peek2()[1]
            for p in unit_to_priorities[unit].iterate2():
                s -= p[1]
            return s
        
        if not priorities.isEmpty():
            units = units.sorted(sort_by_diff)

        ##
        for unit in units:
            sorted_enemy_groups = PriorityQueue()
            for p in unit_to_priorities[unit].iterate2():
                priority = p[1]
                own_val = d[p[0]].value
                enemy_val = p[0].value
                if own_val > enemy_val:
                    diff = own_val - enemy_val
                    per = diff / enemy_val
                    mult = max(0.1, 1 - per)
                    priority *= mult
                if (priority > self.unit_priority_threshold(unit)):
                    sorted_enemy_groups.enqueue(p[0], priority)
            if sorted_enemy_groups.isEmpty():
                continue
            enemy_group = sorted_enemy_groups.peek()
            d[enemy_group].units.append(unit)
            # TODO consider cloak values
            d[enemy_group].value += self.unit_type.get_unit_combat_value_enemy_group(unit.type_id, enemy_group.units) * sum(self.unit_type.get_resource_value(unit.type_id))
        for key, value in d.items():
            a = AssignedGroup()
            a.enemies = key
            a.group = self.group_service.create_group(value.units)
            groups.append(a)
        
        return groups

    def unit_priority_threshold(self, unit: Unit):
        if unit.type_id in {UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.PROBE}:
            return max(2, unit.position.distance_to_closest(self.state.own_townhalls) / 10)
        elif unit.type_id in {UnitTypeId.QUEEN}:
            return unit.position.distance_to_closest(self.state.own_townhalls) / 10
        else:
            return 0
