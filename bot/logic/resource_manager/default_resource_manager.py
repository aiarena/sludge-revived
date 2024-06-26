from typing import List, Union

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from bot.util.priority_queue import PriorityQueue
from bot.util.unit_type_utils import get_resource_value, get_unit_origin_type, get_resource_value_upgrade
from bot.logic.resource_manager.resource_manager_interface import ResourceManagerInterface
import bot.injector as injector
from bot.services.state_service import StateService
from bot.model.unit_type_abstraction import UnitTypeAbstraction
from bot.services.state.army_composition_manager import ArmyCompositionManager
from bot.util.spending_helper import optimal_combination

class DefaultResourceManager(ResourceManagerInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        
    def get_spending_list(self, priorities: PriorityQueue) -> List[UnitTypeId]:
        minerals_left = self.state.resources.minerals
        vespene_left = self.state.resources.vespene
        supply_left = self.state.resources.supply.left
        larva_left = self.state.resources.larva
        spending_list = []
        for p in priorities:
            if isinstance(p, UnitTypeAbstraction):
                if p == UnitTypeAbstraction.ECONOMY:
                    while minerals_left > 50 and supply_left > 0 and larva_left > 0:
                        minerals_left, vespene_left, supply_left, larva_left, spending_list = self._appendUnit(UnitTypeId.DRONE, minerals_left, vespene_left, supply_left, larva_left, spending_list)
                if p == UnitTypeAbstraction.ARMY:
                    army, minerals_left, vespene_left, supply_left, larva_left = self.make_army(minerals_left, vespene_left, supply_left, larva_left)
                    spending_list.extend(army)
            else:
                minerals_left, vespene_left, supply_left, larva_left, spending_list = self._appendUnit(p, minerals_left, vespene_left, supply_left, larva_left, spending_list)
        return spending_list

    def _appendUnit(self, type_id: Union[UnitTypeId, UpgradeId], minerals_left, vespene_left, supply_left, larva_left, spending_list):
        if isinstance(type_id, UnitTypeId):
            m, v, s = get_resource_value(self.state._bot, type_id)
        elif isinstance(type_id, UpgradeId):
            m, v = get_resource_value_upgrade(self.state._bot, type_id)
            s = 0
        else:
            return minerals_left, vespene_left, supply_left, larva_left, spending_list
        l = 0
        if get_unit_origin_type(type_id) == UnitTypeId.LARVA:
            l = 1
        if m <= minerals_left and v <= max(vespene_left, 0) and s <= max(supply_left, 0) and l <= max(larva_left, 0):
            spending_list.append(type_id)
        minerals_left -= m
        vespene_left -= v
        supply_left -= s
        larva_left -= l
        return minerals_left, vespene_left, supply_left, larva_left, spending_list

    def make_army(self, minerals, vespene, supply, larva) -> List[UnitTypeId]:
        output: List[UnitTypeId] = []

        minerals_left = minerals
        vespene_left = vespene
        supply_left = supply
        larva_left = larva

        comp = self.state.army_composition
        # make army composition units until any of the resources is negative
        for type_id in comp.goal_army_composition.keys():
            cont = False
            for idx in range(comp.goal_army_composition[type_id]):
                m, v, s = get_resource_value(self.state._bot, type_id)
                l = 0
                if get_unit_origin_type(type_id) == UnitTypeId.LARVA:
                    l = 1
                if m <= minerals_left and v <= vespene_left and s <= supply_left and l <= larva_left:
                    output.append(type_id)
                    minerals_left -= m
                    vespene_left -= v
                    supply_left -= s
                    larva_left -= l
                if minerals_left < 0 or vespene_left < 0 or supply_left < 0 or larva_left < 0:
                    cont = True
                    break
            if cont:
                break

        if minerals_left < 0:
            minerals_left = 0
        elif minerals_left > 500:
            minerals_left = 500
        if vespene_left < 0:
            vespene_left = 0
        elif vespene_left > 500:
            vespene_left = 500
        if larva_left < 0:
            larva_left = 0
        if supply_left < 0:
            supply_left = 0

        army_unit_ids = self.state.army_composition.fallback_units

        # wait until can afford any army unit
        temp = False
        for id in army_unit_ids:
            if not self.state.can_afford_minerals(id, minerals_left):
                temp = True
        if temp:
            return output, minerals_left, vespene_left, supply_left, larva_left

        army_unit_resource_values = []
        for unit_id in army_unit_ids:
            # resource value including larva cost
            # TODO: map larva cost for different units (eg. ravager has 0)
            val = get_resource_value(self.state._bot, unit_id)
            if unit_id == UnitTypeId.ZERGLING:
                cost = (50, 0)
            else:
                cost = (val[0], val[1])
            army_unit_resource_values.append(list(cost))
        
        try:
            if self.state.resources.supply.used < 200:
                optimal = optimal_combination([minerals_left, vespene_left], army_unit_resource_values)
                if optimal:
                    for idx, o in enumerate(optimal):
                        for i in range(o):
                            output.append(army_unit_ids[idx])
                            minerals_left -= army_unit_resource_values[idx][0]
                            vespene_left -= army_unit_resource_values[idx][1]
        except:
            pass
            # print('optimal combination error')

        return output, minerals_left, vespene_left, supply_left, larva_left