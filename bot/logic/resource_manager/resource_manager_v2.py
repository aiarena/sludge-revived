from typing import List, Union, Dict
from collections import defaultdict

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from bot.util.priority_queue import PriorityQueue
from bot.logic.resource_manager.resource_manager_interface import ResourceManagerInterface
import bot.injector as injector
from bot.services.state_service import StateService
from bot.services.unit_type_service import UnitTypeService
from bot.services.debug_service import DebugService
from bot.model.unit_type_abstraction import UnitTypeAbstraction
from bot.services.state.army_composition_manager import ArmyCompositionManager
from bot.util.spending_helper import optimal_combination
from bot.util.unit_type_utils import get_unit_origin_type

class ResourceManagerv2(ResourceManagerInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.unit_type : UnitTypeService = injector.inject(UnitTypeService)
        self.debug: DebugService = injector.inject(DebugService)
        
    def get_spending_list(self, priorities: PriorityQueue) -> List[UnitTypeId]:
        minerals_left = self.state.resources.minerals
        vespene_left = self.state.resources.vespene
        supply_left = self.state.resources.supply.left
        larva_left = self.state.resources.larva
        spending_list = []
        for a in priorities.iterate2():
            p = a[0]
            priority = a[1]
            if isinstance(p, UnitTypeAbstraction):
                if p == UnitTypeAbstraction.ECONOMY:
                    while minerals_left > 50 and supply_left > 0 and larva_left > 0:
                        minerals_left, vespene_left, supply_left, larva_left, spending_list = self._appendUnit(UnitTypeId.DRONE, minerals_left, vespene_left, supply_left, larva_left, spending_list)
                if p == UnitTypeAbstraction.ARMY:
                    army, minerals_left, vespene_left, supply_left, larva_left = self.make_army(minerals_left, vespene_left, supply_left, larva_left)
                    spending_list.extend(army)
            else:
                if p == UnitTypeId.HATCHERY and priority > 50:
                    self.state.request_placement(p)
                minerals_left, vespene_left, supply_left, larva_left, spending_list = self._appendUnit(p, minerals_left, vespene_left, supply_left, larva_left, spending_list)
        return spending_list

    def _appendUnit(self, type_id: Union[UnitTypeId, UpgradeId], minerals_left, vespene_left, supply_left, larva_left, spending_list):
        '''Mutates the given spending list to include the given UnitTypeid or UpgradeId if it can be afforded.'''
        #TODO make this consider supply, using get_resource_value(type_id, detailed=True)
        if isinstance(type_id, UnitTypeId):
            m, v = self.unit_type.get_resource_value_creation(type_id)
        #If there is a structure that can currently make the desired upgrade, save money for it. Otherwise, don't.
        #   -> benefit: prevents upgrades being queued inefficiently (missile + armor upgrades, for example, both on one evo)
        #   -> potential issue: upgrades will just sit in priorities, meaning eco balance service will be balancing for those upgrades. Maybe that's fine though.
        #TODO might not be the right place for this logic
        elif isinstance(type_id, UpgradeId) and self.state.own_structures(get_unit_origin_type(type_id)).filter(lambda u: u.is_ready and u.is_idle).exists:
            m, v = self.unit_type.get_resource_value_upgrade(type_id)
        else:
            return minerals_left, vespene_left, supply_left, larva_left, spending_list
        l = 0
        if get_unit_origin_type(type_id) == UnitTypeId.LARVA:
            l = 1
        if m <= minerals_left and v <= max(vespene_left, 0) and l <= max(larva_left, 0): #and s <= max(supply_left, 0)
            spending_list.append(type_id)
        minerals_left -= m
        vespene_left -= v
        #supply_left -= s
        larva_left -= l
        return minerals_left, vespene_left, supply_left, larva_left, spending_list

    def make_army(self, minerals, vespene, supply, larva) -> List[UnitTypeId]:
        output: List[UnitTypeId] = []

        minerals_left = minerals
        vespene_left = vespene
        supply_left = supply
        larva_left = larva

        # make army composition units until any of the resources is negative
        # NOTE: by using deficit army comp instead of goal army comp, as before, bot relies a lot more on fallback units, which could be good or bad.
            #-maybe want to expand fallback unit logic, perhaps add some kind of ratio system to it
        deficit_army = self.get_deficit_army_comp(self.state.army_composition.goal_army_composition)
        for type_id, amt in deficit_army.items():
            cont = False
            for _ in range(amt):
                minerals_left, vespene_left, supply_left, larva_left, _ = self._appendUnit(type_id, minerals_left, vespene_left, supply_left, larva_left, output)
                if minerals_left < 0 or vespene_left < 0 or supply_left < 0 or larva_left < 0:
                    cont = True
                    break
            if cont:
                break

        '''If haven't completed goal army composition yet, save money until can afford all units in goal army comp
        (in this way, can't end up in a situation where need some expensive unit, like a queen, for goal army comp
        but can't get it because keep making roaches/lings in fallback army comp).'''
        #if not self.can_afford_all_units(deficit_army, minerals_left, vespene_left, supply_left, larva_left):
        #    return output, minerals_left, vespene_left, supply_left, larva_left
        minerals_left, vespene_left, supply_left, larva_left = self.reserve_res(deficit_army, minerals_left, vespene_left, supply_left, larva_left)
        
        #fallback units
        self.create_units_using(output, self.state.army_composition.fallback_units, minerals_left, vespene_left, supply_left, larva_left)

        #desperation units
        #TODO implement desperation mode in state service
        desperation_mode = self.state.resources.supply.used <= 50
        if desperation_mode:
            self.create_units_using(output, self.state.army_composition.desperation_units, minerals_left, vespene_left, supply_left, larva_left)

        return output, minerals_left, vespene_left, supply_left, larva_left

    def create_units_using(self, total_army, army_unit_ids: List[UnitTypeId], minerals_left, vespene_left, supply_left, larva_left) -> (int, int, int, int):
        minerals_left, vespene_left, supply_left, larva_left = self.reserve_res(army_unit_ids, minerals_left, vespene_left, supply_left, larva_left)
        army_unit_resource_values = [list(self.unit_type.get_resource_value_creation(unit_id)) for unit_id in army_unit_ids]
        return self.create_units_least_float(minerals_left, vespene_left, supply_left, larva_left, army_unit_resource_values, army_unit_ids, total_army)

    def create_units_least_float(self, minerals_left, vespene_left, supply_left, larva_left, army_unit_resource_values, army_unit_ids, spending_list) -> (int, int, int, int):
        if self.state.resources.supply.used < 200:
            try:
                #TODO only accounts for minerals/vespene right now
                #minimize supply and larva usage rather than maximum
                temporary_army_unit_resources_values = [[unit[0], unit[1]] for unit in army_unit_resource_values]
                optimal = optimal_combination([minerals_left, vespene_left], temporary_army_unit_resources_values)
                if optimal:
                    for amt, unit_id in zip(optimal, army_unit_ids):
                        for _ in range(amt):
                            minerals_left, vespene_left, supply_left, larva_left, _ = self._appendUnit(unit_id, minerals_left, vespene_left, supply_left, larva_left, spending_list)
            except BaseException as e:
                print(f'optimal combination error: {e}')
        return minerals_left, vespene_left, supply_left, larva_left

    def can_afford_all_units(self, army_unit_ids, minerals_left, vespene_left, supply_left, larva_left) -> bool:
        for unit_id in army_unit_ids:
            m, v, s, l = self.unit_type.get_resource_value_creation(unit_id, True)
            if not(m <= minerals_left and v <= max(vespene_left, 0) and s <= max(supply_left, 0) and l <= max(larva_left, 0)):
                return False
        return True

    def reserve_res(self, army_unit_ids, minerals_left, vespene_left, supply_left, larva_left) -> (int, int, int, int):
        '''Reserves resources based on the minimum minerals/vespene needed to be able to consider all units in army_unit_ids.
        Returns the amount of resources left after reservations are made (if there should be a negative resource return,
        it is instead capped out at 0).
        By reserving resources for units that cannot be produced, once the unit can be produced it can be considered.'''
        reserve_mins = 0
        reserve_vesp = 0

        #TODO consider supply, larva
        for unit_id in army_unit_ids:
            m, v = self.unit_type.get_resource_value_creation(unit_id)
            if minerals_left < m or vespene_left < v:
                reserve_mins = max(reserve_mins, m)
                reserve_vesp = max(reserve_vesp, v)

        minerals_left = max(0, minerals_left - reserve_mins)
        vespene_left = max(0, vespene_left - reserve_vesp)
        return minerals_left, vespene_left, supply_left, larva_left
                
    def get_deficit_army_comp(self, goal_army_comp : Dict[UnitTypeId, int]):
        return {unit_id : max(goal_army_comp[unit_id] - self.state.get_unit_count(unit_id), 0) for unit_id in goal_army_comp}