from typing import List, Tuple
from enum import Enum

import numpy as np
from scipy.spatial import ConvexHull

from sc2 import UnitTypeId, BotAI
from sc2.units import Units, Unit
from sc2.position import Point2

import bot.injector as injector
from bot.services.unit_type_service import UnitTypeService
from bot.util.reg_polygon import n_sided_polygon_rad
from bot.util.unit_type_utils import unit_range

class UnitGroup():
    location: Point2 = Point2()
    value: int = 0
    air_value: int = 0
    ground_value: int = 0
    cloak_value: int = 0
    units: Units = None
    range_hull: List[Tuple[Point2, Point2]] = []
    verticies = []
    percentage_of_air_in_group = 0

    def __init__(self, units):
        self.units: Units = units
    
    def __str__(self):
        return 'UnitGroup(units={units}, location={location}, value={value}'.format(
            units = self.units if self.units.amount <= 10 else 'more than 10 units',
            value = self.value,
            location = self.location)


class UnitGroupService():
    def __init__(self):
        self.bot: BotAI = injector.inject(BotAI)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
    
    def create_groups(self, units: Units, no_range=False) -> List[UnitGroup]:
        groups: List[UnitGroup] = []
        if not units.exists:
            return groups
        if no_range:
            for unit in units:
                groups.append(self.create_group(Units([unit], self.bot._game_data), no_range=True))
            return groups
        unassigned: Units = units
        sub_groups: List[Units] = []
        while not unassigned.empty:
            unit: Unit = unassigned.random
            finder = NeighborFinder(unassigned, self.bot)
            neighbors = finder.get_neighbors(unit)
            unassigned = unassigned.tags_not_in(neighbors.tags)
            unassigned = unassigned.tags_not_in({unit.tag})
            sub_groups.append(neighbors)
        for neighbors in sub_groups:
            if neighbors.exists:
                groups.append(self.create_group(neighbors))
        return groups
            
    def create_group(self, units: Units, no_range=False) -> UnitGroup:
        group = UnitGroup(units)
        if not units.exists:
            group.value = 0
            return group
        group.location = units.center
        if no_range:
            group.range_hull = None
        else:
            group.range_hull = calculate_range_hull(group.units)
        group.value, group.ground_value, group.air_value, group.cloak_value = self.unit_type.get_value_ground_air_cloak(group.units)
        group.percentage_of_air_in_group = get_percentage_of_air_in_group(group)

        return group

def calculate_range_hull(units: Units) -> List[Tuple[Point2, Point2]]:
    points: List[Point2] = []
    for unit in units:
        unit: Unit = unit
        max_range = get_max_range_of_unit(unit)

        # account for movement speed
        max_range += unit.movement_speed
        poly = n_sided_polygon_rad(6, max_range + 1)
        for p in poly:
            points.append(unit.position + p)
    arr = np.array([[point.x, point.y] for point in points])
    edges: List[Tuple[Point2, Point2]] = []
    hull = ConvexHull(arr)
    for simplex in hull.simplices:
        p1 = points[simplex[0]]
        p2 = points[simplex[1]]
        edges.append((p1, p2))
    return edges

class NeighborFinder:
    def __init__(self, units: Units, bot):
        self.bot = bot
        self.unassigned = units
    def get_neighbors(self, unit: Unit) -> Units:
        """ including unit itself """
        output: Units = Units([], self.bot._game_data)
        output.append(unit)
        max_range = get_max_range_of_unit(unit)
        max_range += unit.movement_speed * 2
        neighbors = self.unassigned.closer_than(max_range, unit.position).tags_not_in({unit.tag})
        if not neighbors.exists:
            return output
        self.unassigned = self.unassigned.tags_not_in(neighbors.tags)
        if not self.unassigned.exists:
            output.extend(neighbors)
            return output
        for neighbor in neighbors:
            output.extend(self.get_neighbors(neighbor))
        return output

def get_max_range_of_unit(unit: Unit) -> float:
    if unit.type_id == UnitTypeId.COLOSSUS:
        max_range = unit.ground_range + 2
    elif unit.type_id in unit_range.keys():
        max_range = unit_range[unit.type_id]
    else:
        max_range = max([unit.ground_range, unit.air_range])
    return max_range

def get_percentage_of_air_in_group(group: UnitGroup):
    all_count = group.units.amount
    flying = group.units.filter(lambda u: u.is_flying and not u.type_id in {UnitTypeId.MEDIVAC, UnitTypeId.WARPPRISM, UnitTypeId.OVERLORDTRANSPORT})
    flying_count = flying.amount if flying.exists else 0
    return flying_count / all_count