from typing import List
from math import sqrt

import numpy as np

from sc2.units import Units, Unit
from sc2 import AbilityId, UnitTypeId, BotAI
from sc2.position import Point3, Point2

from .army_tactics_manager_interface import ArmyTacticsManagerInterface
import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.action_service import ActionService
from bot.util.unit_utils import group_army
from bot.util.unit_type_utils import calculate_combat_value
from bot.services.debug_service import DebugService

class ArmyTacticsv2(ArmyTacticsManagerInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.debug: DebugService = injector.inject(DebugService)
        self.bot: BotAI = injector.inject(BotAI)
        self.attacking_mode_units : 'set of tags' = set()
    async def on_step(self):
        for threat in self.state.threats:
            nearby_army = Units([], self.state._bot._game_data)
            for unit in self.state.own_army_units:
                if distance_from_boundary(threat.hull, unit.position) < 10:
                    nearby_army.append(unit)
            
            nearby_queens_value = 0
            for queen in self.state.own_units_that_can_attack(UnitTypeId.QUEEN):
                if distance_from_boundary(threat.hull, queen.position) < 10:
                    nearby_queens_value += 150

            nearby_army_value = calculate_combat_value(self.state._bot, nearby_army) + nearby_queens_value

            spine_spore = self.state.own_structures.filter(lambda u: u.can_attack)
            if spine_spore.exists:
                spine_spore_in_range = Units([], self.bot._game_data)
                for unit in spine_spore:
                    if threat.units.closer_than(max(unit.ground_range, unit.air_range), unit.position).exists:
                        spine_spore_in_range.append(unit)
                nearby_army_value += calculate_combat_value(self.state._bot, spine_spore_in_range)

            if threat.ground_value <= 0 and not nearby_army.filter(lambda u: u.can_attack_air).exists and nearby_army.exists:
                direction = threat.location.direction_vector(nearby_army.center)
                pos = nearby_army.center + 5 * direction
                self.action_service.command_group(nearby_army, AbilityId.MOVE, pos, 0)
                continue

            # if theres only medivacs attack even with less value
            enemy_value = threat.value
            if not threat.units.filter(lambda u: u.can_attack).exists:
                enemy_value = 0

            engage_threshold = 1.2

            '''Based on our supply or how close the enemy is to our base, we may be more willing to attack them.'''
            if 200 - self.state.resources.supply.used < 10:
                engage_threshold = 0.8
            if threat.distance_from_closest_townhall < 20:
                # at 1000 army value mult is 0.8
                # TODO: consider several desperation factors: can we move the workers to another base, how many bases enemy has etc.
                if self.state.own_townhalls.closest_to(threat.location).assigned_harvesters > 4:
                    engage_threshold = max(0.7, 1 - (0.0002 * nearby_army_value))
            if threat.location.distance_to(self.state.game_info.start_location) < 10:
                engage_threshold = 0.5

            disengage_threshold = (2/3)*engage_threshold
            outcome = self.calculate_fight_outcome(nearby_army, nearby_army_value, threat.units, enemy_value)
            
            #TODO the logic below might cause a bug where only a few units in nearby_army are attacking units, and once they die,
            #the rest of the army decides to retreat because there are no more attacking units and outcome <= engage_threshold
            #(but outcome not <= disengage_threshold). To fix can add elif attacking unit in nearby_units: make all them attacking units
            if outcome <= disengage_threshold:
                self.attacking_mode_units = self.attacking_mode_units - nearby_army.tags
            elif outcome >= engage_threshold:
                self.attacking_mode_units = self.attacking_mode_units | nearby_army.tags
            if nearby_army.tags_in(self.attacking_mode_units).amount <= 0:
                retreat_distance = 5
                if threat.value > 2 * nearby_army_value:
                    retreat_distance = 15
                sub_groups = group_army(nearby_army, 3)
                for sub_group in sub_groups:
                    closest_enemy = threat.units.closest_to(sub_group.center)
                    #distance = sub_group.center.distance_to(closest_enemy.position)
                    distance = distance_from_boundary(threat.hull, sub_group.center)
                    # self.debug.text_world(f'd = {round(distance, 3)}, val = {nearby_army_value - threat.value}', Point3((sub_group.center.x, sub_group.center.y, 10)), None, 12)
                    if distance < 6:
                        direction = unit_direction(threat.location, sub_group.center)

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
                            is_positive = lambda u: which_side_of_a_to_b(threat.location, sub_group.center, u.position)
                            is_negative = lambda u: not which_side_of_a_to_b(threat.location, sub_group.center, u.position)
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
            else:
                if threat.units.filter(lambda u: u.is_flying and not u.type_id in {UnitTypeId.MEDIVAC, UnitTypeId.WARPPRISM, UnitTypeId.OVERLORDTRANSPORT}).exists:
                    if nearby_army.filter(lambda u: u.can_attack_air).exists:
                        self.action_service.command_group(nearby_army, AbilityId.ATTACK, threat.location, 100)
                else:
                    self.action_service.command_group(nearby_army, AbilityId.ATTACK, threat.location, 100)

    def calculate_fight_outcome(self, nearby_army : Units, nearby_army_value : int,
                                 enemy_army : Units, nearby_enemy_value : int) -> float:
        """Calculates the odds of winning a fight."""
        own_lings = nearby_army(UnitTypeId.ZERGLING)
        if own_lings.exists:
            stalkers = enemy_army(UnitTypeId.STALKER)
            if stalkers.exists:
                matches = min(own_lings.amount // 4, stalkers.amount)
                nearby_army_value += matches * 25

        #if enemy units have no health, consider them 40% of their army value
        base_val = 0.4
        if nearby_army.amount >= 1 and enemy_army.amount >= 1:
            nearby_army_value *= ((1 - base_val)*(sum(u.health_percentage for u in nearby_army)/nearby_army.amount) + base_val)
            nearby_enemy_value *=  ((1 - base_val)*(sum(u.health_percentage for u in enemy_army)/enemy_army.amount) + base_val)

        current_ratio = nearby_army_value/max(nearby_enemy_value, 1)
        return current_ratio

def unit_direction(a: Point2, b: Point2) -> Point2:
    dv = Point2((b.x - a.x, b.y - a.y))
    magnitude = sqrt((dv.x ** 2) + (dv.y ** 2))
    if magnitude == 0:
        magnitude = 1
    return Point2((dv.x / magnitude, dv.y / magnitude))

def which_side_of_a_to_b(a: Point2, b: Point2, c: Point2) -> bool:
    d = (c.x - a.x) * (b.y - a.y) - (c.y - a.y) * (b.x - a.x)
    return d > 0

def distance_from_boundary(edges, point: Point2):
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
