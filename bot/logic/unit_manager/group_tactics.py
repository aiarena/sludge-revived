from math import sqrt
from typing import Union, Dict, Tuple
import random

from sc2 import AbilityId, UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point3, Point2
from sc2.unit_command import UnitCommand

from .assigned_group import AssignedGroup
from bot.util.unit_type_utils import not_attacking_combat_units

from bot.services.state_service import StateService
from bot.services.action_service import ActionService
from bot.services.debug_service import DebugService
from bot.services.unit_group_service import UnitGroup, UnitGroupService
from bot.services.unit_type_service import UnitTypeService
from bot.services.pathing_service import PathingService
import bot.injector as injector

from bot.util.unit_utils import group_army
from bot.util.unit_type_utils import get_unit_origin_type

class GroupTactics:
    #distance constant used to figure out whether units are nearby, range at which can safety retreat home, etc.
    danger_dist_const = 14

    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.group_service: UnitGroupService = injector.inject(UnitGroupService)
        self.pathing: PathingService = injector.inject(PathingService)
        self.debug: DebugService = injector.inject(DebugService)

    def manage_group(self, group: AssignedGroup) -> Units:
        '''Manages units in the group and returns all units that should be considered as unassigned
        (so that they can be used in other processes, such as workers for worker distribution).'''

        self.assigned_tags = set()
        
        self.move_retreaters(group)

        if not group.group.units.exists:
            return self.assigned_tags

        attack_mode = (self.state.mode == 'attack'
                       or (not self.state._bot.enemy_race == Race.Zerg and self.state._bot.has_creep(group.enemies.location))
                       or (
                           (self.state.enemy_townhalls.exists and group.enemies.location.distance_to_closest(self.state.enemy_townhalls) > 40)
                           or (not self.state.enemy_townhalls.exists and group.enemies.location.distance_to(self.state.enemy_natural_position) > 40)
                       )
                       or distance_from_boundary(group.group.range_hull, group.enemies.units.closest_to(group.group.location).position) <= 1)
        
        # self.debug_group(group)

        own_units = group.group.units
        nearby_units = Units([], self.state._bot._game_data)

        nearby_consider_threshold = 5
        for unit in own_units:
            unit: Unit
            if group.enemies.range_hull:
                dist_from_bounds = distance_from_boundary(group.enemies.range_hull, unit.position)
            else:
                dist_from_bounds = unit.position.distance_to(group.enemies.location)
            if dist_from_bounds < nearby_consider_threshold:
                nearby_units.append(unit)

        if self.evaluate_engagement(group.group, group.enemies) and attack_mode:
            '''If the entire group can win the fight, then check to see if there are enough nearby units to win the fight.
            If not enough nearby units, then should do subgroup retreating with nearby units.'''
            far_units = own_units.tags_not_in(nearby_units.tags)

            #nearby units should fight if they are favored, otherwise they should split into subgroups and retreat out of range
            should_fight, (own_val, enemy_val) = self.evaluate_engagement(nearby_units, group.enemies, consider_disengage_proximity=True, show_group_vals=True, debug=True)

            #far away units should simply move towards the fight
            # for u in far_units:
            #     self.debug.text_world(f'far', Point3((u.position3d.x, u.position3d.y, u.position3d.z)), None, 12)
            self.action_service.command_group(far_units, AbilityId.ATTACK, group.enemies.location)
            self.assigned_tags = self.assigned_tags.union(far_units.tags)

            (own_val - enemy_val) / group.group.value

            '''
            shouldnt attack if without full force
            unless our force is 2x larger than opponents
            '''
            if should_fight:
                #NOTE a bug may exist involving workers being pulled too early because of how special combat considerations uses advantage to leave some drones mining
                '''
                special_assigned, unassigned = self.special_combat_considerations(nearby_units, group.enemies, advantage)
                no_assignment_units = special_assigned.union(unassigned)
                nearby_units = nearby_units.tags_not_in(no_assignment_units)
                own_units = own_units.tags_not_in(no_assignment_units)
                '''
                if group.enemies.units.amount == 1:
                    self.action_service.command_group(nearby_units, AbilityId.ATTACK, group.enemies.units.first)
                    self.assigned_tags = self.assigned_tags.union(nearby_units.tags)
                else:
                    self.action_service.command_group(nearby_units, AbilityId.ATTACK, group.enemies.location)
                    self.assigned_tags = self.assigned_tags.union(nearby_units.tags)
            else:
                self.pathing_retreat(nearby_units, group.enemies)
                #self.subgroup_retreat(nearby_units, group.enemies)
        else:
            self.pathing_retreat(nearby_units, group.enemies)
            #self.subgroup_retreat(nearby_units, group.enemies)
            #own_units = own_units.tags_not_in(nearby_units.tags)

            #should_attack = group.enemies.location.distance_to_closest(self.state.own_townhalls) >= 30
            '''# If in attacking mode, scatter units to set up multiprong and scout out enemy units
            if self.state.mode == 'attack' and should_attack:
                unassigned_units.union(own_units.tags)'''
            
            #let unit manager deal with idle troops, only return nearby units as assigned units
            #return nearby_units.tags
        
        return self.assigned_tags
    
    def calculate_fight_outcome(self, units1: Units, units2: Units, detailed = False):
        units1 = units1.filter(lambda u: (u.can_attack or u.type_id in not_attacking_combat_units) and u.is_ready)
        units2 = units2.filter(lambda u: (u.can_attack or u.type_id in not_attacking_combat_units) and u.is_ready)

        if units1.amount == 0 or units2.amount == 0:
            return sum(self.unit_type.get_resource_value(units1)), sum(self.unit_type.get_resource_value(units2))

        # consider unit counters
        #TODO figure out what to do about cloak and medivacs/support units
        units1_types = self.unit_type.get_unit_type_resource_mapping(units1)
        units2_value = sum(sum(self.unit_type.get_resource_value(unit.type_id)) for unit in units2)

        units1_value = sum(self.unit_type.get_unit_combat_value_enemy_group(unit, units2)*amt for unit, amt in units1_types.items())

        # consider health percentage
        units1_value *= self.unit_type.get_unit_combat_value_hp_multiplier(units1)
        units2_value *= self.unit_type.get_unit_combat_value_hp_multiplier(units2)

        units1_value *= 0.5 + (self.get_range_dist_multiplier(units1, units2) / 2)
        units2_value *= 0.5 + (self.get_range_dist_multiplier(units2, units1) / 2)

        return units1_value, units2_value
    
    def get_range_dist_multiplier(self, units1: Units, units2: Units):
        multipliers = []
        for unit in units1:
            unit: Unit
            range_dist = max(1, unit.position.distance_to_closest(units2) - (max(unit.ground_range, unit.air_range))/max(0.1, unit.movement_speed))
            multipliers.append(min(1, 1 / range_dist))
        out = sum(multipliers) / units1.amount
        self.debug.text_world(f'{round(out, 2)}', Point3((units1.center.x, units1.center.y, 12)), None, 24)
        return out

    def evaluate_engagement(self, own_group: Union[UnitGroup, Units], enemy_group: Union[UnitGroup, Units], consider_disengage_proximity=False, show_group_vals = False, debug = False) -> bool or (bool, (float, float)):
        '''Should attack the enemy if True, else should retreat.'''
        engage_threshold = 1

        if isinstance(own_group, Units):
            own_group = self.group_service.create_group(own_group)
        if isinstance(enemy_group, Units):
            enemy_group = self.group_service.create_group(enemy_group)

        # if debug and enemy_group.range_hull:
        #     for edge in own_group.range_hull:
        #         self.debug.line_out(Point3((edge[0].x, edge[0].y, 10)), Point3((edge[1].x, edge[1].y, 10)), Point3((0, 0, 255)))

        '''Based on our supply or how close the enemy is to our base, we may be more willing to attack them.'''
        if 200 - self.state.resources.supply.used < 10:
            engage_threshold = 0.8
        if self.state.own_townhalls.exists and enemy_group.location.distance_to_closest(self.state.own_townhalls) < 20:
            # at 1000 army value mult is 0.8
            # TODO: consider several desperation factors: can we move the workers to another base, how many bases enemy has etc.
            if self.state.own_townhalls.closest_to(enemy_group.location).assigned_harvesters > 4:
                engage_threshold = max(0.7, 1 - (0.0002 * own_group.value))
        if enemy_group.location.distance_to(self.state.game_info.start_location) < 10:
            engage_threshold = 0.5

        own_val, enemy_val = self.calculate_fight_outcome(own_group.units, enemy_group.units)
        outcome = own_val/(enemy_val if enemy_val else 1)

        disengage_proximity_mult = 1
        if consider_disengage_proximity:
            if isinstance(own_group, UnitGroup):
                own_units = own_group.units
            else:
                own_units = own_group
            disengage_proximity_mult = (1 + (percentage_of_units_inside_polygon(own_units, enemy_group.range_hull) / 2))
        if own_val * disengage_proximity_mult >= enemy_val * engage_threshold:
            should_fight = True
        else:
            should_fight = False

        if (
            not own_group.units.exclude_type({UnitTypeId.QUEEN, UnitTypeId.ZERGLING}).exists
            and not enemy_group.units.exclude_type({UnitTypeId.ADEPT, UnitTypeId.REAPER}).exists
            and not UpgradeId.ZERGLINGMOVEMENTSPEED in self.state.upgrades
            and not self.state._bot.has_creep(enemy_group.location)
            #and enemy_group.location.distance_to_closest(self.state.own_townhalls) > 8
           ):
           should_fight = False

        return (should_fight, (own_val, enemy_val)) if show_group_vals else should_fight
        
    def debug_group(self, group : AssignedGroup) -> None:
        #for edge in group.group.range_hull:
        #    self.debug.line_out(Point3((edge[0].x, edge[0].y, 10)), Point3((edge[1].x, edge[1].y, 10)))
        pos = group.group.location
        self.debug.text_world(f'{group.group.value}, {group.group.ground_value}, {group.group.air_value}, {group.group.cloak_value}', Point3((pos.x, pos.y, 10)), None, 12)
        #pos = group.enemies.location
        #self.debug.text_world(f'{group.enemies.value}, {group.enemies.ground_value}, {group.enemies.air_value}, {group.enemies.cloak_value}', Point3((pos.x, pos.y, 10)), None, 12)

        pos1 = group.group.location
        pos2 = group.enemies.location
        self.debug.line_out(Point3((pos1.x, pos1.y, group.group.units.random.position3d.z + 0.1)), Point3((pos2.x, pos2.y, group.enemies.units.random.position3d.z + 0.1)))
        # for unit in group.group.units:
        #     unit: Unit
        #     self.debug.line_out(Point3((unit.position.x, unit.position.y, unit.position3d.z + 0.1)), Point3((pos2.x, pos2.y, group.enemies.units.random.position3d.z + 0.1)), Point3((128, 128, 128)))


    def special_combat_considerations(self, own_group : UnitGroup, enemy_group : UnitGroup, outcome : float) -> ({'unit tags'}, {'unit tags'}):
        '''Applies special actions to units that are applicable and returns the tags of units assigned.
            Returns the specially assigned units, and units that should be considered as unassigned for future steps in the program.'''
        special_assigned = set()
        unassigned = set()

        if isinstance(own_group, Units):
            own_group = self.group_service.create_group(own_group)
        if isinstance(enemy_group, Units):
            enemy_group = self.group_service.create_group(enemy_group)

        workers = own_group.units.of_type(UnitTypeId.DRONE)
        if workers:
            worker_efficiency = self.unit_type.get_unit_combat_value_enemy_group(UnitTypeId.DRONE, enemy_group.units) * sum(self.unit_type.get_resource_value(UnitTypeId.DRONE))
            while workers.exists and outcome >= worker_efficiency:
                outcome -= worker_efficiency
                worker = workers.closest_to(enemy_group.location)
                workers = workers.tags_not_in({worker.tag})
                unassigned.add(worker.tag)
                continue

        return special_assigned, unassigned
    
    def pathing_retreat(self, own_units: Units, enemy_group: UnitGroup):
        sub_groups = group_army(own_units, 3)
        for group in sub_groups:
            destination = self.state.own_units.not_structure.closest_to(self.state._bot.start_location).position
            path, dist = self.pathing.find_path(group.center, destination, consider_threats=True)
            if len(path) == 0:
                path, dist = self.pathing.find_path(group.center, destination)
            if len(path) == 0 or dist < 10:
                self.subgroup_retreat(group, enemy_group)
            else:
                self.action_service.command_group(group, AbilityId.MOVE, Point2(path[min(10, len(path)-1)]))
                self.assigned_tags = self.assigned_tags.union(group.tags)

    def subgroup_retreat(self, own_units: Units, enemy_group: UnitGroup) -> None:
        sub_groups = group_army(own_units, 3)
        for sub_group in sub_groups:
            # if subgroup closer than x from boundary --> retreat
            retreat_distance = 4
            closest_enemy = enemy_group.units.closest_to(sub_group.center)
            #distance = sub_group.center.distance_to(closest_enemy.position)
            if enemy_group.range_hull:
                distance = distance_from_boundary(enemy_group.range_hull, sub_group.center)
            else:
                distance = sub_group.center.distance_to(enemy_group.location)
            if distance < 6:
                direction = unit_direction(enemy_group.location, sub_group.center)

                if distance > 2:
                    # spread units
                    multiplier = 1
                    if distance > 3:
                        multiplier = 2
                    elif distance > 5:
                        direction = Point2((0, 0))
                    perpendicular = multiplier * Point2((direction.y, -direction.x))
                    army_without_group = self.state.own_army_units.tags_not_in(sub_group.tags)

                    sub_army = self.state.own_army_units.tags_not_in(sub_group.tags).closer_than(12, sub_group.center)
                    is_positive = lambda u: which_side_of_a_to_b(enemy_group.location, sub_group.center, u.position)
                    is_negative = lambda u: not which_side_of_a_to_b(enemy_group.location, sub_group.center, u.position)
                    units_to_positive = sub_army.filter(is_positive)
                    units_to_negative = sub_army.filter(is_negative)

                    negative_direction = Point2((direction.x + perpendicular.x, direction.y + perpendicular.y))
                    positive_direction = Point2((direction.x - perpendicular.x, direction.y - perpendicular.y))
                    if units_to_negative.exists and units_to_positive.exists:
                        if units_to_positive.amount > units_to_negative.amount:
                            pos = sub_group.center + retreat_distance * positive_direction
                        else:
                            pos = sub_group.center + retreat_distance * negative_direction
                    elif units_to_positive.exists:
                        pos = sub_group.center + retreat_distance * negative_direction
                    elif units_to_negative.exists:
                        pos = sub_group.center + retreat_distance * positive_direction
                    else:
                        pos = sub_group.center + retreat_distance * direction
                else:
                    pos = sub_group.center + retreat_distance * direction
                self.action_service.command_group(sub_group, AbilityId.MOVE, pos, 101)
                self.assigned_tags = self.assigned_tags.union(sub_group.tags)
    
    def move_retreaters(self, group: AssignedGroup):
        self.subgroup_retreat(group.retreaters.units, group.enemies)

######################################################

def distance_from_boundary(edges, point: Point2):
    # distance is 0 if point is contained within polygon
    if polygon_contains_point(edges, point):
        return 0
    distances = []
    for edge in edges:
        distances.append(dist_to_segment(point, Point2(edge[0]), Point2(edge[1])))
    if len(distances) > 0:
        return min(distances)
    else:
        return 1000

def dist2(v: Point2, w: Point2):
    return v.distance2_to(w)

def distToSegmentSquared(p: Point2, v: Point2, w: Point2):
    l2 = dist2(v, w)
    if (l2 == 0):
        return dist2(p, v)
    t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2
    t = max(0, min(1, t))
    a = Point2((v.x + t * (w.x - v.x), v.y + t * (w.y - v.y)))
    return dist2(p, a)

def dist_to_segment(p, v, w):
    return sqrt(distToSegmentSquared(p, v, w))

def unit_direction(a: Point2, b: Point2) -> Point2:
    dv = Point2((b.x - a.x, b.y - a.y))
    magnitude = sqrt((dv.x ** 2) + (dv.y ** 2))
    if magnitude == 0:
        magnitude = 1
    return Point2((dv.x / magnitude, dv.y / magnitude))

def which_side_of_a_to_b(a: Point2, b: Point2, c: Point2) -> bool:
    d = (c.x - a.x) * (b.y - a.y) - (c.y - a.y) * (b.x - a.x)
    return d > 0

def polygon_contains_point(edges, point: Point2) -> bool:
    # implemented using ray casting
    intersections = 0
    ray = (Point2((0,0)), point)
    for edge in edges:
        edge = (Point2((edge[0][0], edge[0][1])), Point2((edge[1][0], edge[1][1])))
        if segment_intersects_segment(edge, ray):
            intersections += 1
    return not intersections % 2 == 0

def ccw(A,B,C):
    return (C.y-A.y) * (B.x-A.x) > (B.y-A.y) * (C.x-A.x)

def segment_intersects_segment(seg1: Tuple[Point2, Point2], seg2: Tuple[Point2, Point2]) -> bool:
    def _intersect(A, B, C, D):
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)
    return _intersect(seg1[0], seg1[1], seg2[0], seg2[1])

def percentage_of_units_inside_polygon(units: Units, edges):
    if not units.exists or not edges:
        return 0
    total = units.amount
    amt = 0
    for unit in units:
        amt += 1 if polygon_contains_point(edges, unit.position) else 0
    return amt / total