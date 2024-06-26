from typing import List

from sc2 import UnitTypeId, Race, AbilityId
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2, Point3

import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.action_service import ActionService
from bot.services.debug_service import DebugService
from bot.hooks import hookable

@hookable
class OverlordManager:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.debug: DebugService = injector.inject(DebugService)

        self.assigned_ovies: Dict[str, Point2] = {}
        self.unassigned_spots: List[Point2] = []
        self.ignore_orders = set()

        self.first_overlord_tag = None

    async def on_step(self, overlords: Units):
        # for pos in self.unassigned_spots:
        #     self.debug.text_world('ovie', Point3((pos.x, pos.y, 10)), None, 12)
        
        if self.first_overlord_tag:
            O = self.state.enemy_natural_position
            A = O.direction_vector(self.state._bot.game_info.map_center)
            if self.state.enemy_is_two_base():
                pos: Point2 = O + 15*A
            else:
                pos: Point2 = O + 9*A
            self.assigned_ovies[self.first_overlord_tag] = pos
        
        overlords = overlords.tags_not_in(self.ignore_orders)
        if overlords.exists:
            for ovie in overlords:
                nearby_enemies = self.state.enemy_units.closer_than(15, ovie.position).filter(lambda u: u.can_attack_air)
                if not nearby_enemies.exists:
                    nearby_enemies = self.state.enemy_units.closer_than(5, ovie.position)
                if nearby_enemies.exists:
                    destination: Point2 = ovie.position + 4 * nearby_enemies.center.direction_vector(ovie.position)
                    self.action_service.add(ovie.tag, ovie.move(destination))
                elif ovie.tag in self.assigned_ovies.keys():
                    spot = self.assigned_ovies[ovie.tag]
                    if ovie.position.distance_to(spot) > 1:
                        self.action_service.add(ovie.tag,ovie.move(spot))
        
        # send overseers to cloaked units
        # TODO: move below logic to UnitManager
        '''
        for threat in self.state.threats:
            if threat.cloak_value > 0 or (threat.units(UnitTypeId.SENTRY).exists and threat.distance_from_closest_townhall < 20):
                seers = self.state.own_units(UnitTypeId.OVERSEER)
                if seers.exists:
                    closest = seers.closest_to(threat.location)
                    self.action_service.add(closest.tag, closest.move(threat.location), 10)
        '''

        # OVERSEERS
        overseers: Units = self.state.own_units(UnitTypeId.OVERSEER).tags_not_in(self.ignore_orders)
        if overseers.exists:
            for overseer in overseers:
                if overseer.tag in self.assigned_ovies.keys():
                    self.unassigned_spots.append(self.assigned_ovies[overseer.tag])
                    del self.assigned_ovies[overseer.tag]
                abilities = await self.state._bot.get_available_abilities(overseer)
                if AbilityId.SPAWNCHANGELING_SPAWNCHANGELING in abilities:
                    self.action_service.add(overseer.tag, overseer(AbilityId.SPAWNCHANGELING_SPAWNCHANGELING), 15)

        # CHANGELINGS
        changelings: Units = self.state.own_units(UnitTypeId.CHANGELING)
        if changelings.exists:
            for changeling in changelings:
                self.action_service.add(changeling.tag, changeling.move(self.state.enemy_natural_position))

        # Overlords stop ignoring orders when they are idle
        to_remove = set()
        for tag in self.ignore_orders:
            unit = self.state.own_units.find_by_tag(tag)
            if not unit or (unit.is_idle and not self.action_service.get(tag)):
                to_remove.add(tag)
        self.ignore_orders = self.ignore_orders - to_remove

    def on_init(self):
        self.unassigned_spots.extend(self.state.overlord_spots)

        unit = self.state.own_units(UnitTypeId.OVERLORD).first
        O = self.state.enemy_natural_position
        A = O.direction_vector(self.state._bot.game_info.map_center)
        pos1: Point2 = O + 9*A
        self.action_service.add(unit.tag, unit.move(pos1))
        self.assigned_ovies[unit.tag] = pos1
        self.ignore_orders.add(unit.tag)
        self.first_overlord_tag = unit.tag

    def on_unit_created(self, unit: Unit):
        # WARNING: called before state service update
        if unit.type_id == UnitTypeId.OVERLORD and self.state._bot.units(UnitTypeId.OVERLORD).amount == 2:
            if self.state._bot.enemy_race == Race.Protoss:
                self.action_service.add(unit.tag, unit.move(self.state.own_natural_position))
            elif self.state._bot.enemy_race == Race.Terran:
                if self.state._bot._game_info.map_name == 'Redshift LE':
                    self.action_service.add(unit.tag, unit.move(self.state.enemy_third_position))
                else:
                    # Scout for proxy rax
                    positions = []
                    for expansion in self.state._bot.expansion_locations:
                        if expansion == self.state._bot.start_location or expansion == self.state.own_natural_position:
                            continue
                        if expansion.distance_to(self.state._bot.start_location) < 50 or expansion.distance_to(self.state.own_natural_position) < 50:
                            positions.append(expansion)
                    commands = []
                    for position in positions:
                        commands.append(unit.move(position, True))
                    self.action_service.add(unit.tag, commands)
            else:
                # ZvZ
                exps = self.state._bot.expansion_locations
                exps2 = []
                for exp in exps:
                    exp: Point2
                    if exp.distance_to(self.state._bot.enemy_start_locations[0]) > 5 and exp.distance_to(self.state.enemy_natural_position) > 5:
                        exps2.append(exp)
                position = self.state.enemy_natural_position.closest(exps2)
                self.action_service.add(unit.tag, unit.move(position))
            return

        if unit.type_id == UnitTypeId.OVERLORD and len(self.unassigned_spots) > 0:
            spot = self.unassigned_spots.pop()
            self.assigned_ovies[unit.tag] = spot
            self.action_service.add(unit.tag, unit.move(spot))
    
    def on_unit_destroyed(self, unit_tag: str):
        if unit_tag in self.assigned_ovies.keys():
            pos: Point2 = self.assigned_ovies[unit_tag]
            self.unassigned_spots.append(pos)
            del self.assigned_ovies[unit_tag]
