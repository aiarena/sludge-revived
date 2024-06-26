from math import sqrt
from typing import Union
from collections import defaultdict
import math
import random

from sc2 import UnitTypeId
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
from .worker_distribution import WorkerDistributor
from bot.logic.spending_actions.default_spending_actions import DefaultSpendingActions
from bot.logic.overlord_manager import OverlordManager
from bot.logic.queen_manager.default_queen_manager import DefaultQueenManager

from bot.services.debug_service import DebugService

attacking_type_priority_value = defaultdict(lambda: 30, #default priority worth of every combat unit
{
    UnitTypeId.PROBE: 35,
    UnitTypeId.DRONE: 35,
    UnitTypeId.SCV: 35
})

non_attacking_type_priority_value = defaultdict(lambda: 15, #default priority worth of every building
{
    UnitTypeId.PYLON: 25,
    UnitTypeId.NEXUS: 27.5,

    UnitTypeId.COMMANDCENTER: 27.5,
    UnitTypeId.BARRACKS: 10,

    UnitTypeId.HATCHERY: 27.5
})

not_attacking_combat_units = {UnitTypeId.BANELING, UnitTypeId.INFESTOR, UnitTypeId.WARPPRISM, UnitTypeId.MEDIVAC, UnitTypeId.WIDOWMINE, UnitTypeId.RAVEN}
class UnitManager_v2_lstsqr:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.debug_service: DebugService = injector.inject(DebugService)
        self.group_service: UnitGroupService = injector.inject(UnitGroupService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.group_tactics: GroupTactics = GroupTactics()
        self.worker_distributor: WorkerDistributor = WorkerDistributor()
        self.spending_actions = DefaultSpendingActions()
        self.overlord_manager = OverlordManager()
        self.queen_manager = DefaultQueenManager()

        self.assigned_groups = []
        self.desperation_units = set(unit_desperation_threshold.keys())

    async def on_step(self):
        unassigned = self.state.own_units
        priorities: PriorityQueue = self.group_and_prioritize_enemies()
        self.assigned_groups = self.assign_groups3(unassigned, priorities)
        assigned_tags = set()
        for g in self.assigned_groups:
            assigned_tags = assigned_tags.union(self.group_tactics.manage_group(g))
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

        # use remaining units to do cool things
        '''Types of units that are unassigned at this point:
         [Unit(name='Larva', tag=4394844165), Unit(name='Extractor', tag=4422107139), Unit(name='Larva', tag=4374396931), Unit(name='Extractor', tag=4378329090),
          Unit(name='Larva', tag=4419485713), Unit(name='Larva', tag=4420272135), Unit(name='Extractor', tag=4353687554), Unit(name='Queen', tag=4359979010), 
          Unit(name='Overlord', tag=4369678339), Unit(name='Egg', tag=4348706831), Unit(name='Hatchery', tag=4364435457), Unit(name='Larva', tag=4430757915), 
          Unit(name='Egg', tag=4362862595), Unit(name='Larva', tag=4429185026), Unit(name='Lair', tag=4342939649), Unit(name='Larva', tag=4431020035),
           Unit(name='RoachWarren', tag=4368891906), Unit(name='Overlord', tag=4395892738), Unit(name='Overlord', tag=4343726082),
            Unit(name='Hatchery', tag=4374921218), Unit(name='Larva', tag=4427612161), Unit(name='Larva', tag=4390912029), Unit(name='Larva', tag=4428660742), 
            Unit(name='Queen', tag=4367843330), Unit(name='InfestationPit', tag=4427350023), Unit(name='Overlord', tag=4383834114)'''
            
    def group_and_prioritize_enemies(self) -> PriorityQueue:
        res = PriorityQueue()
        unassigned = self.state.enemy_units

        can_attack = unassigned.filter(lambda u: u.can_attack)
        can_attack.extend(self.state.enemy_units.of_type(not_attacking_combat_units))
        groups = self.group_service.create_groups(can_attack)
        for group in groups:
            p = self.prioritize_group2(group)
            res.enqueue(group, p)
            # self.debug_service.text_world(f'{group.value}, {round(p,2)}', Point3((group.location.x, group.location.y, 10)), Point3((255, 0, 0)), 12)
        unassigned = unassigned.tags_not_in(can_attack.tags)

        groups = self.group_service.create_groups(unassigned)
        for group in groups:
            p = self.prioritize_group2(group)
            res.enqueue(group, p)
            # self.debug_service.text_world(f'{group.value}, {round(p,2)}', Point3((group.location.x, group.location.y, 10)), Point3((255, 0 ,0)), 12)

        return res

    '''Below are functions used to determine priority of enemy groups.'''
    @staticmethod
    def get_dist_group_to_close_townhall(group : UnitGroup, state : StateService) -> float:
        mining_bases = state.own_townhalls.filter(lambda u: u.assigned_harvesters > 0)
        if mining_bases:
            return group.location.distance_to_closest(mining_bases)
        elif state.own_townhalls.exists:
            return group.location.distance_to_closest(state.own_townhalls)
        else:
            return 0.00001
    '''End of functions list.'''

    enemy_group_variables = [
        lambda group, state : UnitManager_v2_lstsqr.get_dist_group_to_close_townhall(group, state),
        lambda group, state : min(1, group.value/(state.enemy_army_value if state.enemy_army_value else math.inf))
        ]
    
    def god_function(self, x):
        return (0.11)/(x+0.1)-0.1

    # TODO: move to state
    def map_diagonal_len(self):
        p: Rect = self.state._bot.game_info.playable_area
        h = p.height
        w = p.width
        return sqrt(h ** 2 + w ** 2)

    def prioritize_group2(self, group: UnitGroup) -> int:
        # percentage of enemy army value
        per_of_enemy_army = min(1, group.value/(self.state.enemy_army_value if self.state.enemy_army_value else math.inf))
        dist = UnitManager_v2_lstsqr.get_dist_group_to_close_townhall(group, self.state) - 10
        dist = dist if dist >= 0 else 0.003
        dist_per = min(1, dist / self.map_diagonal_len())
        dist_mult = self.god_function(dist_per)

        priority = per_of_enemy_army * dist_mult

        return priority

    def priority_apply_unit_modifier2(self, priority, enemy_group: UnitGroup, unit: Unit):
        dist = distance_from_boundary(enemy_group.range_hull, unit.position)
        in_range = enemy_group.units.closer_than(max(unit.ground_range, unit.air_range), unit.position)
        if in_range.exists:
            priority = 1
        else:
            priority = min(1, dist / self.map_diagonal_len())
            priority = self.god_function(priority)
        return priority

    def prioritize_group(self, group: UnitGroup) -> int:
        priority = sum(enemy_group_priority[idx](func(group, self.state)) for idx, func in enumerate(self.enemy_group_variables))

        type_val = 0
        for unit in group.units:
            unit: Unit
            type_val += attacking_type_priority_value[unit] if unit.can_attack else non_attacking_type_priority_value[unit]

        #consider the types of units in the group, and how dangerous/important they are
        priority += (type_val//group.units.amount)
        #add priority for proxies
        if group.location.distance_to_closest(self.state.own_townhalls) < 20 and group.units.structure.exists:
            priority += 50

        return priority

    '''Below are functions used to determine priority of unit to groups.'''
    @staticmethod
    def distance_to_no_zero(unit : Unit, group : UnitGroup):
        '''Since zero breaks math.log, need to account for it.'''
        dist = unit.distance_to(group.location)
        return dist if dist != 0 else 0.0000000000000001
    '''End of functions list.'''

    unit_to_group_variables = [
        lambda u, g, s : UnitManager_v2_lstsqr.distance_to_no_zero(u, g)
    ]
    def priority_apply_unit_modifier(self, enemy_group: UnitGroup, unit: Unit):
        priority = sum(unit_to_group_priority[idx](func(unit, enemy_group, self.state)) for idx, func in enumerate(self.unit_to_group_variables))
        return priority

    class Temp:
            units: Units
            value = 0
            ground_value = 0
            air_value = 0
            cloak = 0

    def assign_groups3(self, unassigned: Units, priorities: PriorityQueue):
        groups = []
        units = unassigned.not_structure.filter(lambda u: u.can_attack)
        units.extend(unassigned.of_type(not_attacking_combat_units))
        #units = units.exclude_type(self.desperation_units)

        d = {}
        for enemy_group in priorities:
            t = self.Temp()
            t.units = Units([], self.state._bot._game_data)
            d[enemy_group] = t
        
        #assign army units
        unit_to_priorities = defaultdict(PriorityQueue)
        for unit in units:
            for p in priorities.iterate2():
                priority = self.priority_apply_unit_modifier2(p[1], p[0], unit)
                if priority >= unit_desperation_threshold[unit.type_id]:
                    unit_to_priorities[unit].enqueue(p[0], priority)

        #sort units so that those who have a very high priority for the first enemy group
        #and low priority for the rest are assigned first
        def sort_by_diff(unit: Unit):
            if not unit_to_priorities[unit].isEmpty():
                s = 2 * unit_to_priorities[unit].peek2()[1]
                for p in unit_to_priorities[unit].iterate2():
                    s -= p[1]
            else:
                s = 0
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
                    per = diff / (enemy_val if enemy_val else 1) * 0.25
                    mult = max(0.1, 1 - per)
                    priority *= mult
                
                sorted_enemy_groups.enqueue(p[0], priority)
            if sorted_enemy_groups.isEmpty():
                continue
            enemy_group = sorted_enemy_groups.peek()
            d[enemy_group].units.append(unit)
            # TODO consider cloak values
            # self.debug_service.text_world(f'{round(sorted_enemy_groups.peek2()[1],2)}', Point3((unit.position3d.x, unit.position3d.y - 0.35, unit.position3d.z)), Point3((0, 255, 0)), 12)
            d[enemy_group].value += self.unit_type.get_unit_combat_value_enemy_group(unit.type_id, enemy_group.units) * sum(self.unit_type.get_resource_value(unit.type_id))
        for key, value in d.items():
            a = AssignedGroup()
            a.enemies = key
            a.group = self.group_service.create_group(value.units)
            groups.append(a)
        
        return groups

    def get_value_from_threshold(self, val : int or float, threshold : dict) -> int or float:
        '''Gets the greatest value that val is greater than from the keys of the given dict.'''
        #TODO if want to improve efficiency, store an ordered dict (see Ordered Dict in python documentation)
        #instead of sorting every time

        sorted_keys = sorted(threshold)
        for idx, key in enumerate(sorted_keys):
            if val < key:
                return threshold[sorted_keys[idx - 1]]
        return threshold[sorted_keys[-1]]