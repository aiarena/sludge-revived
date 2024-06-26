from math import cos, sin
from typing import List

from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.pixel_map import PixelMap
from sc2 import BotAI

import bot.injector as injector
from bot.hooks import hookable

class UnitObservation:
    def __init__(self, unit: Unit, time_to_live: int, permanent = False):
        self.bot: BotAI = injector.inject(BotAI)
        self.unit = unit
        self.time_to_live = time_to_live
        self.permanent = permanent
        self.last_update = 0
    
    def iterate(self, time):
        # update unit position
        if self.last_update > 0 and self.unit.movement_speed > 0:
            movement_amount = self.unit.movement_speed * (time - self.last_update)
            direction = Point2((cos(self.unit.facing), sin(self.unit.facing)))
            new_position = self.unit.position + movement_amount * direction
            a: PixelMap = self.bot._game_info.pathing_grid
            if (
                new_position.x > 0 and new_position.x < a.width - 1 and
                new_position.y > 0 and new_position.y < a.height - 1 and
                (self.unit.is_flying or self.bot.in_pathing_grid(new_position))
                ):
                self.unit.set_position(new_position)
        self.last_update = time

        if self.permanent:
            return True
        self.time_to_live = self.time_to_live - 1
        if self.time_to_live == 0:
            return False
        return True

    def update_ttl(self, time_to_live: int):
        self.time_to_live = time_to_live
    
    def update_unit(self, unit: Unit):
        self.unit = unit

@hookable
class UnitMemory:
    def __init__(self, bot):
        self.bot: BotAI = bot
        self.unit_observations: List[UnitObservation] = []
        self.observed_enemy_units: Units = Units([], self.bot._game_data)

    def iterate(self, time):
        # Update unit observations based on known enemy units
        ttl = 240
        for unit in self.bot.known_enemy_units:
            updated = False
            for observation in self.unit_observations:
                if observation.unit.tag == unit.tag:
                    observation.update_unit(unit)
                    observation.update_ttl(ttl)
                    updated = True
            if not updated and unit.is_visible:
                if unit.is_structure:
                    self.unit_observations.append(UnitObservation(unit, ttl, True))
                else:
                    self.unit_observations.append(UnitObservation(unit, ttl))

        # Update observed_enemy_units then remove old observations
        temp: Units = Units([], self.bot._game_data)
        to_remove = []
        for observation in self.unit_observations:
            temp.append(observation.unit)
            if not observation.iterate(time):
                # forget unit if observation has expired or there's a friendly unit in vision range but the enemy unit can't be seen
                to_remove.append(observation)
            elif not self.bot.known_enemy_units.find_by_tag(observation.unit.tag) and self.bot.is_visible(observation.unit.position):
                observation.unit.set_position(self.bot.enemy_start_locations[0])
        for observation in to_remove:
            self.unit_observations.remove(observation)
        
        self.observed_enemy_units: Units = Units(temp, self.bot._game_data)
    
    def on_unit_destroyed(self, tag: str):
        to_remove = []
        for observation in self.unit_observations:
            observation: UnitObservation
            if observation.unit.tag == tag:
                to_remove.append(observation)
        for observation in to_remove:
            self.unit_observations.remove(observation)