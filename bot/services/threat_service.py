from typing import List, Tuple

import numpy as np
from scipy.spatial import ConvexHull

from sc2 import UnitTypeId, BotAI
from sc2.units import Units, Unit
from sc2.position import Point2

import bot.injector as injector
from bot.services.unit_type_service import UnitTypeService
from bot.util.reg_polygon import n_sided_polygon_rad

class Threat():
    location: Point2 = Point2()
    value: int = 0
    air_value: int = 0
    ground_value: int = 0
    cloak_value: int = 0
    units: Units = None
    distance_from_closest_townhall = 0
    hull: List[Tuple[Point2, Point2]] = []
    can_attack = True
    def __init__(self, units):
        self.units: Units = units

class ThreatService():
    def __init__(self):
        self.bot: BotAI = injector.inject(BotAI)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.threats: List[Threat] = []
        self.unassigned_units: Units = Units([], self.bot._game_data)
        self.assigned_units: Units = Units([], self.bot._game_data)

    def detect_threats(self, enemy_army_units: Units):
        self.threats = self.create_threats(enemy_army_units)

    def threats_further_than(self, n, position: Point2) -> List[Threat]:
        output = []
        for threat in self.threats:
            if threat.location.distance_to(position) > n:
                output.append(threat)
        return output
    
    def threats_further_than_plist(self, n, positions: List[Point2]) -> List[Threat]:
        output = []
        for threat in self.threats:
            outside = True
            for position in positions:
                if threat.location.distance_to(position) < n:
                    outside = False
            if outside:
                output.append(threat)
        return output
    
    def total_value_of(self, threats: Threat) -> int:
        total = 0
        for threat in threats:
            total += threat.value
        return total

    def calculate_convex_hull(self, threat: Threat) -> List[Tuple[Point2, Point2]]:
        points: List[Point2] = []
        for unit in threat.units:
            unit: Unit = unit
            max_range = max([unit.ground_range, unit.air_range])
            if unit.type_id == UnitTypeId.COLOSSUS:
                # account for colossus upgrade
                max_range += 2
            # account for movement speed
            max_range += unit.movement_speed
            poly = n_sided_polygon_rad(6, max(max_range, 2) + 1)
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
    
    ################################################################

    def create_threats(self, units: Units) -> List[Threat]:
        if not units.exists:
            return []
        unassigned: Units = units
        groups: List[Units] = []
        threats: List[Threat] = []
        while not unassigned.empty:
            unit: Unit = unassigned.random
            finder = NeighborFinder(unassigned, self.bot)
            group = finder.get_neighbors(unit)
            unassigned = unassigned.tags_not_in(group.tags)
            groups.append(group)
        for group in groups:
            threats.append(self.create_threat(group))
        return threats
            
    def create_threat(self, units: Units):
        threat = Threat(units)
        threat.location = units.center
        threat.hull = self.calculate_convex_hull(threat)

        threat.value, threat.ground_value, threat.air_value, threat.cloak_value = self.unit_type.calculate_combat_value_ground_air_cloak(threat.units)

        return threat

class NeighborFinder:
    def __init__(self, units: Units, bot):
        self.bot = bot
        self.unassigned = units
    def get_neighbors(self, unit: Unit) -> Units:
        """ including unit itself """
        output: Units = Units([], self.bot._game_data)
        output.append(unit)
        max_range = max([unit.ground_range, unit.air_range])
        if unit.type_id == UnitTypeId.COLOSSUS:
            # account for colossus upgrade
            max_range += 2
        # account for movement speed
        max_range += unit.movement_speed
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