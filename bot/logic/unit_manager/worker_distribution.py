from typing import Dict

from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit
from sc2.units import Units

from bot.services.state_service import StateService
from bot.services.action_service import ActionService
from bot.services.eco_balance_service import EcoBalanceService
import bot.injector as injector

class WorkerDistributor:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.action_service: ActionService = injector.inject(ActionService)
        self.eco_balance: EcoBalanceService = injector.inject(EcoBalanceService)

    # TODO: make race agnostic
    def distribute_workers(self, workers: Units):
        if not self.state.own_townhalls.exists: return

        unassigned_workers: Units = workers.filter(lambda u: u.is_collecting or u.is_idle or u.is_attacking or u.is_moving)
        total_assigned = 0
        
        m, v = self.eco_balance.worker_assignment(workers.amount)

        # saturate extractors
        for extractor in self.state.own_structures(UnitTypeId.EXTRACTOR).ready.sorted_by_distance_to(self.state.game_info.start_location):
            extractor: Unit = extractor
            assigned = 0
            def assign_worker(worker):
                nonlocal assigned, unassigned_workers, total_assigned
                assigned += 1
                total_assigned += 1
                unassigned_workers = unassigned_workers.tags_not_in({worker.tag})

            assigned_but_not_inside_extractor = self.get_workers_assigned_to_gas_structure(unassigned_workers, extractor)
            if assigned_but_not_inside_extractor.exists and assigned_but_not_inside_extractor.amount < extractor.assigned_harvesters:
                # there must be a worker inside the extractor, lets ignore it
                assigned += 1
                total_assigned += 1

            for _ in range(extractor.assigned_harvesters):
                if total_assigned < v and assigned < 3 and unassigned_workers.amount > 0:
                    closest = unassigned_workers.closest_to(extractor)
                    assign_worker(closest)

            while (assigned < 3
                    and total_assigned < workers.amount
                    and total_assigned < v
                    and unassigned_workers.amount > 0):
                closest = unassigned_workers.closest_to(extractor)
                assign_worker(closest)
                if not self.worker_mining_vespene(closest, extractor):
                    self.return_res_before_action(closest, extractor)
        
        harvesters_on_townhall: Dict[Unit, int] = {}
        for townhall in self.state.own_townhalls:
            harvesters_on_townhall[townhall] = 0

        vespene_gatherers = sum(gas.assigned_harvesters for gas in self.state.own_structures(UnitTypeId.EXTRACTOR))

        # keep drones mining if not oversaturated
        def assign_worker(worker, townhall):
            nonlocal unassigned_workers, harvesters_on_townhall, total_assigned
            harvesters_on_townhall[townhall] += 1
            total_assigned += 1
            unassigned_workers = unassigned_workers.tags_not_in({worker.tag})

        for drone in unassigned_workers:
            drone: Unit = drone
            if drone.is_collecting:
                townhall = self.state.own_townhalls.closest_to(drone)
                
                '''#if too many vespene gatherers, let vespene gatherers fall over into the next section of the function
                if vespene_gatherers > v and self.worker_mining_any_vespene(drone):
                    vespene_gatherers -= 1
                    mins = self.state.get_mineral_fields_for_expansion(townhall.position)
                    mid_field = mins.closest_to(mins.center)
                    self.action_service.add(drone.tag, [drone.gather(mid_field), drone.return_resource()], 10)
                    assign_worker(drone, townhall)
                    continue'''

                #if too many vespene gatherers, let them fall over into the next section of the function
                if vespene_gatherers > v and self.worker_mining_any_vespene(drone):
                    vespene_gatherers -= 1
                    continue

                ideal_harvesters = townhall.ideal_harvesters
                ex = self.state.own_structures(UnitTypeId.EXTRACTOR).closer_than(10, townhall.position).ready
                #TODO below is untested but should be more efficient than above, according to "Typical Bottlenecks" on documentation
                #ex = self.state.own_structures.filter(lambda u: u.type_id == UnitTypeId.EXTRACTOR and (u.distance_to(10, townhall.position)) and u.ready)
                for e in ex:
                    ideal_harvesters += 3
                    ideal_harvesters -= e.assigned_harvesters
                if townhall.assigned_harvesters <= ideal_harvesters:
                    assign_worker(drone, townhall)

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
                   and total_assigned < workers.amount
                   and unassigned_workers.amount > 0):
                closest = unassigned_workers.closest_to(mid_field)
                
                if not self.worker_mining_minerals(closest, mins, townhall):
                    self.return_res_before_action(closest, mid_field)
                unassigned_workers = unassigned_workers.tags_not_in({closest.tag})
                assigned_count += 1
                total_assigned += 1

    def return_res_before_action(self, worker : Unit, gather_location : Unit) -> None:
        '''Forces the given worker to return its resource if is carrying any before performing the given action.'''
        if worker.is_carrying_resource:
            #have the worker move to its own position to unassign it from the minerals/gas structure it was previously assigned to
            self.action_service.add(worker.tag, [worker.return_resource(), worker.gather(gather_location, queue=True)], 10)
        else:
            self.action_service.add(worker.tag, worker.gather(gather_location), 10)

    def get_workers_assigned_to_gas_structure(self, workers : Units, gas_structure : Unit) -> Units:
        '''Does not include workers that are currently in the Refinery/Assimilator/Extractor.'''
        return workers.filter(lambda u: u.order_target == gas_structure.tag or (u.is_carrying_vespene and u.position.distance_to(gas_structure.position) < 8))
        
    def worker_mining_minerals(self, worker : Unit, mins : Units, townhall : Unit) -> bool:
        '''Returns whether or not a worker is mining minerals from the given minerals/townhall.'''
        return worker.order_target in mins.tags or worker.order_target == townhall.tag or (worker.is_carrying_minerals and worker.is_returning)

    def worker_mining_any_vespene(self, worker : Unit) -> bool:
        '''Returns whether or not a worker is mining from any vespene geyser.'''
        return (worker.is_carrying_vespene and worker.is_returning) or worker.order_target in self.state.own_structures(UnitTypeId.EXTRACTOR).tags

    def worker_mining_vespene(self, worker : Unit, gas_structure : Unit) -> bool:
        '''Returns whether or not a worker is mining vespene from the given gas structure.'''
        return worker.order_target == gas_structure.tag or (worker.is_carrying_vespene and worker.position.distance_to(gas_structure.position) < 8)