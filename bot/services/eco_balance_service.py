import math
from typing import Dict
from collections import deque

from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit
from sc2.units import Units

from bot.services.state_service import StateService
from bot.services.action_service import ActionService
import bot.injector as injector

# TODO: Distribute workers on minerals/gas
# TODO: Request construction of an extractor or hatchery

class EcoBalanceService:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)

        self.req_mins: int = 0
        self.req_vespene: int = 0

        self.ratio = 0
        self.req_extractors = 0
        self.max_extractor_count = 1

        self.queue = deque([], 4)
        self.vespene_gatherer_history = deque([], 100)
        self.vespene_queue_on = False
        self.default_ratio = 16

    def init_step(self):
        self.req_mins: int = - self.state.resources.minerals
        self.req_vespene: int = - self.state.resources.vespene

        self.ratio = 0

    def set_vespene_queue(self, val : bool) -> None:
        '''If True is given, worker assignment returns the average value in self.vespene_gatherer_history.
        If False is given, worker assignment returns the vespene gatherers requested at the current moment.'''
        self.vespene_queue_on = val

    def set_default_workers_on_gas(self, val : int) -> None:
        '''Sets the default number of workers on gas desired. Used in request_eco.'''
        self.default_ratio = (self.state.get_unit_count(UnitTypeId.DRONE)/val) if val != 0 else math.inf

    def set_max_extractor_count(self, val : int) -> None:
        '''Sets the maximum amount of extractors that can be made to the given amount.'''
        self.max_extractor_count = val

    def request_eco(self, minerals, vespene):
        def temp(d):
            self.queue.append(d)
            a = 0
            for q in self.queue:
                a += q
            if len(self.queue) > 0:
                a = a / len(self.queue)
            self.ratio = a

        self.req_mins += minerals
        self.req_vespene += vespene
        
        temp(max(100, self.req_mins) / max(100, self.req_vespene)) if self.req_vespene > 0 else temp(self.default_ratio)

    def worker_assignment(self, count):
        '''return: mineral_gatherers, vespene_gatherers'''
        WORKER_MINERAL_GATHER_RATE = 56.75 #56.75 minerals on average per minute
        WORKER_VESPENE_GATHER_RATE = 54
        if self.ratio == math.inf:
            return count, 0
        ratio = int(self.ratio/(WORKER_MINERAL_GATHER_RATE/WORKER_VESPENE_GATHER_RATE))
        b = count // (ratio + 1)
        a = b * ratio

        self.vespene_gatherer_history.append(b)
        if self.vespene_queue_on:
            vespene_gatherer_avg = min(self.max_extractor_count * 3, math.floor(sum(val for val in self.vespene_gatherer_history)/len(self.vespene_gatherer_history)))
            self.req_extractors = vespene_gatherer_avg // 3
            return (a, vespene_gatherer_avg)
        else:
            b = min(self.max_extractor_count * 3, b)
            self.req_extractors = b // 3
            return (a, b)


    # legacy implementation:
    def distribute_workers(self):
        workers = self.state.own_units(UnitTypeId.DRONE)
        if not workers.exists:
            return
        townhalls = self.state.own_townhalls
        current_mineral_saturation = self.state.mineral_saturation
        current_gas_saturation = self.gas_harvester_count()
        m, v = self.worker_assignment(workers.amount)
        if current_gas_saturation > v:
            extractor_drones = self.state.own_units(UnitTypeId.DRONE).filter(
                lambda u: self.state.own_structures.find_by_tag(u.order_target) and self.state.own_structures.find_by_tag(u.order_target).type_id == UnitTypeId.EXTRACTOR
            )
            if extractor_drones.exists:
                u = extractor_drones.random_group_of(int(current_gas_saturation - v))
                self.action_service.command_group(u, AbilityId.HARVEST_GATHER, self.state.main_minerals.random)
    
    def redistribute_workers(self):
        drones: Units = self.state.own_units(UnitTypeId.DRONE).filter(lambda u: u.is_collecting or u.is_idle)
        unassigned_workers: Units = drones
        total_assigned = 0
        m, v = self.worker_assignment(drones.amount)
        self.req_extractors = int(v / 3)

        for extractor in self.state.own_structures(UnitTypeId.EXTRACTOR):
            extractor: Unit = extractor
            assigned = 1
            while (assigned < extractor.ideal_harvesters
                    and total_assigned < drones.amount
                    and total_assigned < v
                    and unassigned_workers.amount > 0):
                closest = unassigned_workers.closest_to(extractor)
                unassigned_workers = unassigned_workers.tags_not_in({closest.tag})
                if not (closest.order_target == extractor.tag or closest.order_target == extractor.tag or (len(closest.orders) > 0 and closest.orders[0].ability.id == AbilityId.HARVEST_RETURN)):
                    self.action_service.add(closest.tag, closest.gather(extractor), 10)
                assigned += 1
                total_assigned += 1

        for townhall in self.state.own_townhalls.sorted_by_distance_to(self.state.game_info.start_location):
            mins = self.state.get_mineral_fields_for_expansion(townhall.position)
            if mins.empty:
                continue
            mid_field = mins.closest_to(mins.center)
            assigned_count = 0
            ideal_harvesters = townhall.ideal_harvesters
            ex = self.state.own_structures(UnitTypeId.EXTRACTOR).closer_than(10, townhall.position).ready
            for e in ex:
                ideal_harvesters += 3
                ideal_harvesters -= e.assigned_harvesters
            while (assigned_count < ideal_harvesters
                   and total_assigned < drones.amount
                   and unassigned_workers.amount > 0):
                closest = unassigned_workers.closest_to(mid_field)
                if not (closest.order_target in mins.tags or closest.order_target == townhall.tag or (len(closest.orders) > 0 and closest.orders[0].ability.id == AbilityId.HARVEST_RETURN)):
                    self.action_service.add(closest.tag, closest.gather(mid_field), 10)
                unassigned_workers = unassigned_workers.tags_not_in({closest.tag})
                assigned_count += 1
                total_assigned += 1

    ###################################33

    def distribute_workers3(self):
        drones: Units = self.state.own_units(UnitTypeId.DRONE).filter(lambda u: u.is_collecting or u.is_idle)
        unassigned_workers: Units = drones
        total_assigned = 0
        m, v = self.worker_assignment(drones.amount)
        self.req_extractors = int(v / 3)

        # saturate extractors
        for extractor in self.state.own_structures(UnitTypeId.EXTRACTOR).ready:
            extractor: Unit = extractor
            assigned = 0

            assigned_but_not_inside_extractor = unassigned_workers.filter(lambda u: u.order_target == extractor.tag or (u.is_carrying_vespene and u.position.distance_to(extractor.position) < 8))
            if assigned_but_not_inside_extractor.exists and assigned_but_not_inside_extractor.amount < extractor.assigned_harvesters:
                # there must be a worker inside the extractor, lets ignore it
                assigned += 1
                total_assigned += 1

            for idx in range(extractor.assigned_harvesters):
                if total_assigned < v and assigned < 3:
                    closest = unassigned_workers.closest_to(extractor)
                    unassigned_workers = unassigned_workers.tags_not_in({closest.tag})
                    assigned += 1
                    total_assigned += 1
            while (assigned < 3
                    and total_assigned < drones.amount
                    and total_assigned < v
                    and unassigned_workers.amount > 0):
                closest = unassigned_workers.closest_to(extractor)
                unassigned_workers = unassigned_workers.tags_not_in({closest.tag})
                if not (closest.order_target == extractor.tag or closest.order_target == extractor.tag or (len(closest.orders) > 0 and closest.orders[0].ability.id == AbilityId.HARVEST_RETURN)):
                    self.action_service.add(closest.tag, closest.gather(extractor), 10)
                assigned += 1
                total_assigned += 1
        
        harvesters_on_townhall: Dict[Unit, int] = {}
        for townhall in self.state.own_townhalls:
            harvesters_on_townhall[townhall] = 0

        # keep drones mining minerals if not oversaturated
        for drone in unassigned_workers:
            drone: Unit = drone
            if len(drone.orders) > 0 and (drone.orders[0].ability.id == AbilityId.HARVEST_RETURN or drone.orders[0].ability.id == AbilityId.HARVEST_GATHER):
                townhall = self.state.own_townhalls.closest_to(drone)
                ideal_harvesters = townhall.ideal_harvesters
                ex = self.state.own_structures(UnitTypeId.EXTRACTOR).closer_than(10, townhall.position).ready
                for e in ex:
                    ideal_harvesters += 3
                    ideal_harvesters -= e.assigned_harvesters
                if townhall.assigned_harvesters <= ideal_harvesters:
                    harvesters_on_townhall[townhall] += 1
                    unassigned_workers = unassigned_workers.tags_not_in({drone.tag})
                    total_assigned += 1

        # saturate the rest
        for townhall in self.state.own_townhalls.sorted_by_distance_to(self.state.game_info.start_location):
            mins = self.state.get_mineral_fields_for_expansion(townhall.position)
            if mins.empty:
                continue
            mid_field = mins.closest_to(mins.center)
            assigned_count = harvesters_on_townhall[townhall]
            ideal_harvesters = townhall.ideal_harvesters
            ex = self.state.own_structures(UnitTypeId.EXTRACTOR).closer_than(10, townhall.position).ready
            for e in ex:
                ideal_harvesters += 3
                ideal_harvesters -= e.assigned_harvesters
            while (assigned_count < ideal_harvesters
                   and total_assigned < drones.amount
                   and unassigned_workers.amount > 0):
                closest = unassigned_workers.closest_to(mid_field)
                if not (closest.order_target in mins.tags or closest.order_target == townhall.tag or (len(closest.orders) > 0 and closest.orders[0].ability.id == AbilityId.HARVEST_RETURN)):
                    self.action_service.add(closest.tag, closest.gather(mid_field), 10)
                unassigned_workers = unassigned_workers.tags_not_in({closest.tag})
                assigned_count += 1
                total_assigned += 1


    def gas_harvester_count(self):
        n = 0
        for extractor in self.state.own_structures(UnitTypeId.EXTRACTOR):
            n += extractor.assigned_harvesters
        return n