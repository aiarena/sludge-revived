from typing import Dict, Union, Tuple
from collections import defaultdict

from sc2 import UnitTypeId, BotAI, Race
from sc2.ids.upgrade_id import UpgradeId
from sc2.units import Units
from sc2.unit import Unit
from sc2.game_data import UnitTypeData

import bot.injector as injector


def get_resource_mapping(race : Race) -> Dict[UnitTypeId, Tuple[int, int, int, int]]:
    '''Resource mapping per unit rather than per unit of creation, so use get_resource_value_creation instead for zerglings.
        Format: (minerals, vespene, supply, larva)'''
    if race == Race.Zerg:
        return {
    UnitTypeId.DRONE: (50, 0, 1, 1),
    UnitTypeId.OVERLORD: (100, 0, 0, 1),
    UnitTypeId.OVERSEER: (50, 50, 0, 0),
    UnitTypeId.ZERGLING: (25, 0, 0.5, 0.5),
    UnitTypeId.QUEEN: (150, 0, 2, 0),
    UnitTypeId.BANELING: (25, 25, 0, 0),
    UnitTypeId.ROACH: (75, 25, 2, 1),
    UnitTypeId.RAVAGER: (25, 75, 1, 0),
    UnitTypeId.HYDRALISK: (100, 50, 2, 1),
    UnitTypeId.CORRUPTOR: (150, 100, 2,1),
    UnitTypeId.BROODLORD: (150, 150, 2, 0)
                }

def get_creation_resource_mapping(race: Race):
    if race == Race.Zerg:
        return {
            UnitTypeId.ZERGLING: (50, 0, 1, 1),
            UnitTypeId.BANELING: (25, 25, 0, 0),
            UnitTypeId.RAVAGER: (25, 75, 1, 0),
            UnitTypeId.LURKER: (50, 100, 1, 0),
            UnitTypeId.BROODLORD: (150, 150, 2, 0),
            UnitTypeId.OVERSEER: (50, 50, 0, 0),

            UnitTypeId.LAIR: (150, 100, 0, 0),
            UnitTypeId.HIVE: (200, 150, 0, 0),
            UnitTypeId.GREATERSPIRE: (100, 150, 0, 0)
        }

def get_unit_counters(own_race : Race, enemy_race : Race) -> Dict[UnitTypeId,Dict[UnitTypeId, float or int]]:
    if own_race == Race.Zerg:
        mus_possible = {Race.Zerg: 'zvz', Race.Protoss: 'zvp', Race.Terran: 'zvt',  Race.Random: 'zvr'}
        own_locals = locals().copy()
        exec(f'from bot.util.zerg_unit_counters import unit_counters_{mus_possible[enemy_race]} as unit_counters', globals(), own_locals)
        return defaultdict(lambda: defaultdict(lambda: 1), {unit_id : defaultdict(lambda: 1, counters) for unit_id, counters in own_locals['unit_counters'].items()})

class UnitTypeService():
    def __init__(self):
        self._bot: BotAI = injector.inject(BotAI)
        self._resource_mapping = None
        self._creation_resource_mapping = None
        self.unit_counters = None

    def on_first_iteration(self):
        self._resource_mapping = get_resource_mapping(self._bot.race)
        self._creation_resource_mapping = get_creation_resource_mapping(self._bot.race)
        self.unit_counters = get_unit_counters(self._bot.race, self._bot.enemy_race)

    def get_resource_value(self, id: Union[UnitTypeId, Units], detailed=False) -> (int, int) or (int, int, int, int):
        if isinstance(id, Units):
            return (sum(resource) for resource in zip(*tuple(self.get_resource_value(unit.type_id, detailed) for unit in id)))

        '''if id in self._resource_mapping:
            res = self._resource_mapping[id]
            return res if detailed else res[0], res[1]
        else:'''
        unit_data: UnitTypeData = self._bot._game_data.units[id.value]
        if detailed:
            resources = self._resource_mapping[id]
            return (unit_data.cost_zerg_corrected.minerals, unit_data.cost_zerg_corrected.vespene, resources[2], resources[3])
        else:
            return (unit_data.cost_zerg_corrected.minerals, unit_data.cost_zerg_corrected.vespene)

    combat_values = {
                UnitTypeId.DRONE : (10, 0),
                UnitTypeId.PROBE : (10, 0),
                UnitTypeId.SCV : (10, 0),
                UnitTypeId.BUNKER : (300, 0),
                UnitTypeId.INFESTEDTERRANSEGG : (20, 0),
                UnitTypeId.INFESTEDTERRAN : (30, 0)
            }
    def get_resource_value_combat(self, id: UnitTypeId, detailed=False) -> (int, int) or (int, int, int, int):
        pass
        
    def get_resource_value_creation(self, id: UnitTypeId, detailed=False) -> (int, int) or (int, int, int, int):
        '''Used instead of get_resources_value_v2 if resource values are needed for unit creation
        (e.g., can't create only 1 zergling at a time).'''
        if id in self._creation_resource_mapping:
            res = self._creation_resource_mapping[id]
            return res if detailed else res[0], res[1]
        else:
            return self.get_resource_value(id, True) if detailed else self.get_resource_value(id)

    def get_resource_value_upgrade(self, uid: UpgradeId) -> (int, int):
        upgrade_data = self._bot._game_data.upgrades[uid.value]
        return (upgrade_data.cost.minerals, upgrade_data.cost.vespene)

    def get_unit_type_resource_mapping(self, units: Units) -> 'defaultdict(lambda: 0, Dict[UnitTypeId, int])':
        '''Given a Units object, return a default dictionary of each unit_id
        to its corresponding resource value. E.g. if given 10 zerglings,
        this will return {UnitTypeId.ZERGLING : 250}.'''
        types = defaultdict(int)
        res_val_cache = dict()

        for unit_id in units:
            unit_type = unit_id.type_id
            if unit_type not in res_val_cache:
                res_val_cache[unit_type] = sum(self.get_resource_value(unit_type))
            types[unit_type] += res_val_cache[unit_type]

        return types

    def get_unit_combat_value(self, unit_id : UnitTypeId, enemy_id : UnitTypeId) -> float:
        '''The lower the return value, the better efficiency unit_id has vs enemy_id.'''
        #hp_mult = self.get_unit_combat_value_hp_multiplier(enemy_id)/self.get_unit_combat_value_hp_multiplier(unit_id)
        return self.unit_counters[unit_id][enemy_id]

    def get_unit_combat_value_enemy_group(self, unit_id : UnitTypeData, enemy_group : Units) -> float:
        '''Used to gauge the combat value of one unit vs an enemy group.'''
        enemy_group_types = self.get_unit_type_resource_mapping(enemy_group)
        enemy_value = sum(enemy_group_types.values())
        
        if sum(enemy_group_types.values()) == 0:
            return 1

        #calculate individual effectiveness of the unit vs the enemy's composition
        value = []
        for enemy_unit_id, amt in enemy_group_types.items():
            effectiveness = 1/self.get_unit_combat_value(unit_id, enemy_unit_id) #note the reciprocal of the unit counter value is used
            value.append(effectiveness*(amt/enemy_value))
        #sum up individual effectiveness to make general effectiveness
        return sum(value)

    def get_unit_combat_value_hp_multiplier(self, units : Union[Units, Unit]) -> float:
        HEALTH_MINIMUM = 0.3 #the percent value of a unit that has no health

        if isinstance(units, Unit):
            return HEALTH_MINIMUM + (1-HEALTH_MINIMUM)*(units.health_percentage)
            
        units_hp_percent = sum(unit.health_percentage for unit in units)/units.amount

        return HEALTH_MINIMUM + (1-HEALTH_MINIMUM)*units_hp_percent

    def calculate_combat_value(self, units: Union[Units, Unit]) -> int:
        value = 0
        if isinstance(units, Unit):
            units = Units([units], self._bot._game_data)
        for unit in units.filter(lambda u: u.can_attack or u.type_id in {UnitTypeId.RAVEN, UnitTypeId.MEDIVAC, UnitTypeId.WIDOWMINE, UnitTypeId.BANELING, UnitTypeId.INFESTOR, UnitTypeId.VIPER, UnitTypeId.SWARMHOSTMP, UnitTypeId.WARPPRISM, UnitTypeId.ORACLE, UnitTypeId.CARRIER}):
            if unit.type_id in self.combat_values:
                minerals, vespene = self.combat_values[unit.type_id]
            else:
                minerals, vespene = self.get_resource_value(unit.type_id)
            value += (minerals + vespene)
        return value
    
    def calculate_combat_value_ground_air_cloak(self, units: Units):
        value = 0
        ground_value = 0
        air_value = 0
        cloak_value = 0
        for unit in units.filter(lambda u: u.can_attack or u.type_id in {UnitTypeId.RAVEN, UnitTypeId.MEDIVAC, UnitTypeId.WIDOWMINE, UnitTypeId.BANELING, UnitTypeId.INFESTOR, UnitTypeId.VIPER, UnitTypeId.SWARMHOSTMP, UnitTypeId.WARPPRISM, UnitTypeId.ORACLE, UnitTypeId.CARRIER}):
            if unit.type_id == UnitTypeId.DRONE or unit.type_id == UnitTypeId.PROBE or unit.type_id == UnitTypeId.SCV:
                resources = (10, 0)
            elif unit.type_id == UnitTypeId.BUNKER:
                resources = (300, 0)
            else:
                resources = self.get_resource_value(unit.type_id)
            minerals = resources[0]
            vespene = resources[1]
            value += (minerals + vespene)
            if not unit.is_flying:
                ground_value += (minerals + vespene)
            else:
                air_value += (minerals + vespene)
            if unit.is_cloaked or unit.type_id == UnitTypeId.BANSHEE or unit.type_id == UnitTypeId.WIDOWMINE:
                cloak_value += (minerals + vespene)

        return value, ground_value, air_value, cloak_value

    def get_value_ground_air_cloak(self, units: Units):
        value = 0
        ground_value = 0
        air_value = 0
        cloak_value = 0
        for unit in units:
            resources = self.get_resource_value(unit.type_id)
            minerals = resources[0]
            vespene = resources[1]
            value += (minerals + vespene)
            if not unit.is_flying:
                ground_value += (minerals + vespene)
            else:
                air_value += (minerals + vespene)
            if unit.is_cloaked or unit.type_id == UnitTypeId.BANSHEE or unit.type_id == UnitTypeId.WIDOWMINE:
                cloak_value += (minerals + vespene)

        return value, ground_value, air_value, cloak_value
