from typing import Dict, Union, Tuple
from collections import defaultdict

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.units import Units
from sc2.unit import Unit
from sc2.game_data import UnitTypeData

not_attacking_combat_units = {UnitTypeId.BANELING, UnitTypeId.INFESTOR, UnitTypeId.OVERSEER,
    UnitTypeId.WARPPRISM,
    UnitTypeId.BUNKER, UnitTypeId.MEDIVAC, UnitTypeId.WIDOWMINE, UnitTypeId.RAVEN}

unit_range = {
    UnitTypeId.BUNKER: 7,
    UnitTypeId.BATTLECRUISER: 6,
    UnitTypeId.MEDIVAC: 4,
    UnitTypeId.WIDOWMINE: 5,
    UnitTypeId.RAVEN: 10,

    UnitTypeId.WARPPRISM: 6,

    UnitTypeId.OVERSEER: 5,
    UnitTypeId.BANELING: 4,
    UnitTypeId.INFESTOR: 6
}

zerg_structures = {UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE, UnitTypeId.EXTRACTOR, UnitTypeId.SPINECRAWLER, UnitTypeId.SPORECRAWLER,
UnitTypeId.BANELINGNEST, UnitTypeId.INFESTATIONPIT, UnitTypeId.SPIRE, UnitTypeId.GREATERSPIRE, UnitTypeId.EVOLUTIONCHAMBER,
    UnitTypeId.SPAWNINGPOOL, UnitTypeId.ROACHWARREN, UnitTypeId.HYDRALISKDEN, UnitTypeId.ULTRALISKCAVERN}

origin_type: Dict[Union[UnitTypeId, UpgradeId], UnitTypeId] = {
    UnitTypeId.DRONE: UnitTypeId.LARVA,
    UnitTypeId.OVERLORD: UnitTypeId.LARVA,
    UnitTypeId.OVERSEER: UnitTypeId.OVERLORD,
    UnitTypeId.ZERGLING: UnitTypeId.LARVA,
    UnitTypeId.BANELING: UnitTypeId.ZERGLING,
    UnitTypeId.ROACH: UnitTypeId.LARVA,
    UnitTypeId.RAVAGER: UnitTypeId.ROACH,
    UnitTypeId.HYDRALISK: UnitTypeId.LARVA,
    UnitTypeId.CORRUPTOR: UnitTypeId.LARVA,
    UnitTypeId.BROODLORD: UnitTypeId.CORRUPTOR,

    UnitTypeId.SPINECRAWLER: UnitTypeId.DRONE,
    UnitTypeId.SPORECRAWLER: UnitTypeId.DRONE,

    UnitTypeId.HATCHERY: UnitTypeId.DRONE,
    UnitTypeId.EXTRACTOR: UnitTypeId.DRONE,
    UnitTypeId.SPAWNINGPOOL: UnitTypeId.DRONE,
    UnitTypeId.BANELINGNEST: UnitTypeId.DRONE,
    UnitTypeId.ROACHWARREN: UnitTypeId.DRONE,
    UnitTypeId.HYDRALISKDEN: UnitTypeId.DRONE,
    UnitTypeId.INFESTATIONPIT: UnitTypeId.DRONE,
    UnitTypeId.SPIRE: UnitTypeId.DRONE,
    UnitTypeId.GREATERSPIRE: UnitTypeId.SPIRE,
    UnitTypeId.EVOLUTIONCHAMBER: UnitTypeId.DRONE,
    UnitTypeId.QUEEN: UnitTypeId.HATCHERY,
    UnitTypeId.LAIR: UnitTypeId.HATCHERY,
    UnitTypeId.HIVE: UnitTypeId.LAIR,

    UpgradeId.ZERGLINGMOVEMENTSPEED: UnitTypeId.SPAWNINGPOOL,
    UpgradeId.GLIALRECONSTITUTION: UnitTypeId.ROACHWARREN,
    UpgradeId.CENTRIFICALHOOKS: UnitTypeId.BANELINGNEST,
    UpgradeId.EVOLVEGROOVEDSPINES: UnitTypeId.HYDRALISKDEN,
    UpgradeId.EVOLVEMUSCULARAUGMENTS: UnitTypeId.HYDRALISKDEN,
    UpgradeId.OVERLORDSPEED: UnitTypeId.HATCHERY,
    UpgradeId.ZERGLINGATTACKSPEED: UnitTypeId.SPAWNINGPOOL,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL1: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL2: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMISSILEWEAPONSLEVEL3: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGGROUNDARMORSLEVEL1: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGGROUNDARMORSLEVEL2: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGGROUNDARMORSLEVEL3: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMELEEWEAPONSLEVEL1: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMELEEWEAPONSLEVEL2: UnitTypeId.EVOLUTIONCHAMBER,
    UpgradeId.ZERGMELEEWEAPONSLEVEL3: UnitTypeId.EVOLUTIONCHAMBER
}

#remember to add , at the end of 1-tuples Example:
#   (UnitTypeId.SPAWNINGPOOL,)
PREREQUISITE_MAPPING: Dict[UnitTypeId, Tuple] = {
    UnitTypeId.ZERGLING: (UnitTypeId.SPAWNINGPOOL,),
    UnitTypeId.BANELING: (UnitTypeId.BANELINGNEST,),
    UnitTypeId.ROACH: (UnitTypeId.ROACHWARREN,),
    UnitTypeId.RAVAGER: (UnitTypeId.ROACHWARREN,),
    UnitTypeId.QUEEN: (UnitTypeId.SPAWNINGPOOL, UnitTypeId.HATCHERY),
    UnitTypeId.OVERSEER: (UnitTypeId.LAIR,),
    UnitTypeId.HYDRALISK: (UnitTypeId.HYDRALISKDEN,),
    UnitTypeId.CORRUPTOR: (UnitTypeId.SPIRE,),
    UnitTypeId.BROODLORD: (UnitTypeId.GREATERSPIRE,)
}

def get_unit_origin_type(unit: Union[UnitTypeId, UpgradeId]) -> UnitTypeId:
    return origin_type[unit]

def get_prerequisite_structures(unit: UnitTypeId) -> (UnitTypeId):
    return PREREQUISITE_MAPPING[unit]

def get_larva_cost(type_id: UnitTypeId) -> int:
    return 1 if get_unit_origin_type(type_id) == UnitTypeId.LARVA else 0

def is_combat_unit(unit: Unit) -> bool:
    return unit.can_attack or unit.type_id in not_attacking_combat_units