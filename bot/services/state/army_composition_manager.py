from typing import Dict, List
from collections import defaultdict
from math import ceil

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

import bot.injector as injector
from bot.services.state_service import StateService
from bot.util.priority_queue import PriorityQueue
from bot.services.unit_type_service import UnitTypeService
from bot.util.unit_type_utils import get_prerequisite_structures
from bot.services.eco_balance_service import EcoBalanceService

def add_dicts(dict1 : defaultdict, dict2 : defaultdict or dict) -> dict:
    return_dict = dict1.copy()
    for key, value in dict2.items():
        return_dict[key] += value
    return return_dict

class ArmyCompositionManager:
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.eco_balance: EcoBalanceService = injector.inject(EcoBalanceService)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.fallback_units = self.fallback_units_possible = self.desperation_units = self.desperation_units_possible = self.possible_units = self.extra_considerations = self.overriding_considerations = None

    def set_all_attributes(self, unit_assignment_dict : Dict[UnitTypeId, float or int], fallback_units : List[List[UnitTypeId]],
        desperation_units : List[List[UnitTypeId]], possible_units : List[UnitTypeId], extra_considerations : 'function' = None, overriding_considerations : bool = False) -> None:
        self.unit_assignment_dict = defaultdict(lambda:None, unit_assignment_dict)
        self.set_fallback_units(fallback_units)
        self.set_desperation_units(desperation_units)
        self.set_possible_units(possible_units)
        self.extra_considerations = extra_considerations
        self.overriding_considerations = overriding_considerations

    def set_fallback_units(self, fallback_units: [UnitTypeId]) -> None:
        self.fallback_units_possible = fallback_units

    def set_desperation_units(self, desperation_units: [UnitTypeId]) -> None:
        self.desperation_units_possible = desperation_units

    def set_possible_units(self, possible_units : List[UnitTypeId]) -> None:
        self.possible_units = possible_units

    def update_army_compositions(self):
        self.update_goal_army_composition()
        index, self.fallback_units = self.generate_highest_tech_army_comp(self.fallback_units_possible)
        self.desperation_units = self.desperation_units_possible[index] if self.fallback_units else []
        
        m = 0
        v = 0
        for type_id in self.goal_army_composition.keys():
            value = self.unit_type.get_resource_value(type_id)
            for _ in range(self.goal_army_composition[type_id]):
                m += value[0]
                v += value[1]

        self.eco_balance.request_eco(m, v)

    def generate_highest_tech_army_comp(self, units : List[List[UnitTypeId]]) -> (int, [UnitTypeId]):
        """The first list for which the bot can make every one of its units is returned."""
        for idx, army_comp in enumerate(units):
            if len(army_comp) == len(self.can_buy_units(army_comp)):
                return idx, army_comp
        return 0, []

    def update_goal_army_composition(self) -> None:
        goal_army_composition = defaultdict(int)
        enemy_types = self.unit_type.get_unit_type_resource_mapping(self.state.enemy_army_units)

        available_army_units = self.get_available_army_units()
        if len(available_army_units) >= 1:
            for enemy_id, amount in enemy_types.items():
                '''Find the best unit to make for the given enemy unit, considering the unit_assignment_dict or the 
                strength of each possible own unit against the given enemy unit.'''
                ideal_units = self.unit_assignment_dict[enemy_id]
                best_unit_id = None
                if ideal_units:
                    for unit_id in ideal_units:
                        if self.can_buy_unit(unit_id):
                            best_unit_id, combat_value = unit_id, self.unit_type.get_unit_combat_value(unit_id, enemy_id)
                            break
                if best_unit_id is None: #if can't buy any ideal units or no ideal units are set, derive the best unit for the given enemy unit
                    own_units = []
                    for unit_id in available_army_units:
                        combat_value = self.unit_type.get_unit_combat_value(unit_id, enemy_id)
                        if combat_value < 100:
                            own_units.append((unit_id, combat_value))
                    
                    if own_units: #avoid crash when own_units is empty
                        best_unit_id, combat_value = min(own_units, key = lambda x: x[1])
                
                if best_unit_id:
                    goal_army_composition[best_unit_id] += ceil(combat_value*amount/(sum(self.unit_type.get_resource_value(best_unit_id))))

        if self.extra_considerations:
            if self.overriding_considerations:
                goal_army_composition.update(self.extra_considerations(self.state))
            else:
                goal_army_composition = add_dicts(goal_army_composition, self.extra_considerations(self.state))

        self.goal_army_composition = goal_army_composition

    def can_buy_units(self, units : [UnitTypeId]) -> [UnitTypeId]:
        '''Returns the units that can be bought from the list of units given.'''
        return [unit for unit in units if self.can_buy_unit(unit)]

    def can_buy_unit(self, unit : UnitTypeId) -> bool:
        '''Returns whether or not the given unit can be bought (if the bot has the tech/buildings for it).'''
        for structure in get_prerequisite_structures(unit):
            if self.state.own_structures(structure).empty or not self.state.own_structures(structure).ready:
                return False
        return True

    def get_available_army_units(self) -> (UnitTypeId):
        return self.can_buy_units(self.possible_units)

    def get_largest_deficit(self) -> UnitTypeId:
        # doesnt take into consideration lings being produced in pairs....

        for key in self.goal_army_composition.keys():
            if self.goal_army_composition[key] > 0:
                return key
        return None

        # getting largest deficit too temporally expensive? (overridin old logic with above)
        largest_deficit = 0
        largest_deficit_id = None
        for type_id in self.goal_army_composition.keys():
            resource_deficit = self.get_resource_deficit(type_id)
            if resource_deficit > largest_deficit:
                largest_deficit = resource_deficit
                largest_deficit_id = type_id
        return largest_deficit_id


    def get_resource_deficit(self, type_id: UnitTypeId) -> int:
        unit_count = self.state.get_unit_count(type_id)
        unit_deficit = self.goal_army_composition[type_id] - unit_count
        resource_value = self.unit_type.get_resource_value(type_id)
        resource_deficit = (unit_deficit * resource_value[0]) + (unit_deficit * resource_value[1])
        return resource_deficit
