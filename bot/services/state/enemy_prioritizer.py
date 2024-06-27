import math
from collections import defaultdict

from sc2.units import Units, UnitTypeId
from sc2.position import Point2, Point3

import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.unit_group_service import UnitGroupService, UnitGroup
from bot.services.debug_service import DebugService

from bot.util.unit_type_utils import is_combat_unit
from bot.util.priority_queue import PriorityQueue
from bot.util.mapping_functions import steep_decline

class EnemyPrioritizer:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.debug: DebugService = injector.inject(DebugService)
        self.group_service: UnitGroupService = injector.inject(UnitGroupService)

    def group_and_prioritize_enemies(self, units: Units) -> PriorityQueue:
        res = PriorityQueue()
        unassigned = units.exclude_type({UnitTypeId.LARVA, UnitTypeId.EGG})

        unfinished_cannons = unassigned.filter(lambda u: u.type_id == UnitTypeId.PHOTONCANNON and not u.is_ready)
        groups = self.group_service.create_groups(unfinished_cannons, no_range=True)
        for group in groups:
            p = self.prioritize_group(group)
            res.enqueue(group, p)
            # self.debug.text_world(f'{group.value}, {round(p,2)}', Point3((group.location.x, group.location.y, 10)), Point3((255, 0 ,0)), 12)
        unassigned = unassigned.tags_not_in(unfinished_cannons.tags)

        can_attack = unassigned.filter(is_combat_unit)
        groups = self.group_service.create_groups(can_attack)
        for group in groups:
            p = self.prioritize_group(group)
            res.enqueue(group, p)
            # self.debug.text_world(f'{group.value}, {round(p,2)}', Point3((group.location.x, group.location.y, 10)), Point3((255, 0, 0)), 12)
        unassigned = unassigned.tags_not_in(can_attack.tags)

        groups = self.group_service.create_groups(unassigned, no_range=True)
        for group in groups:
            p = self.prioritize_group(group)
            res.enqueue(group, p)
            # self.debug.text_world(f'{group.value}, {round(p,2)}', Point3((group.location.x, group.location.y, 10)), Point3((255, 0 ,0)), 12)

        # for group in res:
        #     if group.range_hull:
        #         for edge in group.range_hull:
        #             self.debug.line_out(Point3((edge[0].x, edge[0].y, 10)), Point3((edge[1].x, edge[1].y, 10)), Point3((255, 0, 0)))

        return res

    def prioritize_group(self, group: UnitGroup) -> float:
        # percentage of enemy army value
        # TODO: implement better function to give lower boundary of 0.1
        dist = max(0, min(self.state.map_diagonal_len, self.state.get_dist_group_to_close_townhall(group) - 10))
        dist_per = dist / self.state.map_diagonal_len
        dist_mult = steep_decline(dist_per)

        priority = self.type_and_value_priority(group) * dist_mult

        return priority

    building_priority = defaultdict(lambda: 0.1,
    {
        UnitTypeId.NEXUS: 0.15,
        UnitTypeId.COMMANDCENTER: 0.15,
        UnitTypeId.ORBITALCOMMAND: 0.15,
        UnitTypeId.PLANETARYFORTRESS: 0.15,
        UnitTypeId.HATCHERY: 0.15,
        UnitTypeId.LAIR: 0.15,
        UnitTypeId.HIVE: 0.15,
        UnitTypeId.SPINECRAWLER: 0.5,
        UnitTypeId.SPORECRAWLER: 0.5,
        UnitTypeId.PHOTONCANNON: 0.5,
        UnitTypeId.SHIELDBATTERY: 0.5,
        UnitTypeId.BUNKER: 0.5,

        UnitTypeId.MISSILETURRET: 0.2,
        UnitTypeId.PYLON: 0.2,

        UnitTypeId.EVOLUTIONCHAMBER: 0.15,
        UnitTypeId.FORGE: 0.15,
        UnitTypeId.ENGINEERINGBAY: 0.15,
        UnitTypeId.TECHLAB: 0.15,
        UnitTypeId.REACTOR: 0.15,

        UnitTypeId.ROBOTICSFACILITY: 0.07,
        UnitTypeId.STARGATE: 0.07,
    })

    def type_and_value_priority(self, group: UnitGroup) -> float:
        '''
        buildings: 0-0.5 (based on type of the building)
        attackers = 0.5-1 (based on size of the group)
        '''
        building_priority = 0
        per_of_enemy_units = 0
        if group.units.not_structure.exists:
            per_of_enemy_units = max(0.001, min(1, group.value/self.state.enemy_army_value) if self.state.enemy_army_value else 1)
            return (0.8 + (per_of_enemy_units * (2/10)))
        else:
            # this group contains only structures... groups that contain structures can only contain one
            building_type = group.units.first.type_id
            if building_type == UnitTypeId.PHOTONCANNON and self.state.own_townhalls and group.location.distance_to_closest(self.state.own_townhalls) < 20:
                # proxy cannon
                building_priority = 1
            else:
                building_priority = self.building_priority[building_type]
            return building_priority
