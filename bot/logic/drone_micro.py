from sc2 import UnitTypeId, AbilityId

from bot.services.state_service import StateService
import bot.injector as injector
from bot.services.action_service import ActionService
from bot.services.debug_service import DebugService
from bot.services.unit_type_service import UnitTypeService

class DroneMicro:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.debug: DebugService = injector.inject(DebugService)

    async def on_step(self, iteration):
        for threat in self.state.threats:
            drones = self.state.own_units(UnitTypeId.DRONE).closer_than(10, threat.location)
            if drones.exists and threat.value > 140 and threat.units.filter(lambda u: u.can_attack_ground).exists:
                direction = threat.location.direction_vector(drones.center)
                pos = drones.center + 10 * direction
                self.action_service.command_group(drones, AbilityId.MOVE, pos, 15)
            #closest_townhall = self.state.own_townhalls.closest_to(threat.location)
            #if threat.location.distance_to(self.state.get_mineral_fields_for_expansion(closest_townhall.position).center) < 15 and threat.value > 140:
            #    nearby_drones = self.state.own_units(UnitTypeId.DRONE).closer_than(10, closest_townhall.position)
            #    if nearby_drones.exists:
            #        direction = threat.location.direction_vector(nearby_drones.center)
            #        pos = nearby_drones.center + 10 * direction
            #        self.action_service.command_group(nearby_drones, AbilityId.MOVE, pos, 15)
        
        enemies_near_start = self.state.enemy_units.closer_than(10, self.state.main_minerals.center)
        if enemies_near_start.amount > 2:
            drones = self.state.own_units(UnitTypeId.DRONE).closer_than(10, self.state.main_minerals.center)
            if self.unit_type.calculate_combat_value(enemies_near_start) < 1.5 * self.unit_type.calculate_combat_value(drones):
                self.action_service.command_group(drones, AbilityId.ATTACK, self.state.game_info.start_location, 20)

        # Counter cannon rush
        buildings = self.state.enemy_structures({UnitTypeId.PYLON, UnitTypeId.PHOTONCANNON})
        if buildings.exists and self.state.own_army_value < 50:
            for structure in buildings.filter(lambda u: u.position.distance_to_closest(self.state.own_townhalls) < 20):
                assigned = 0
                drones = self.state.own_units_that_can_attack(UnitTypeId.DRONE)
                if not drones.exists:
                    break
                already_targeted = drones.filter(lambda u: u.order_target == structure.tag)
                assigned += already_targeted.amount
                
                while assigned < 4:
                    drones_that_arent_attacking = drones.filter(lambda u: len(u.orders) > 0 and not u.orders[0].ability.id == AbilityId.ATTACK)
                    if not drones_that_arent_attacking.exists:
                        break
                    closest = drones_that_arent_attacking.closest_to(structure)
                    self.action_service.repeat_until_dead(closest.tag, closest.attack(structure), 25)
                    assigned += 1
