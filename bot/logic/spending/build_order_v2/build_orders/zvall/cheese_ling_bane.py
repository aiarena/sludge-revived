from collections import defaultdict

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from bot.logic.spending.build_order_v2.build_order_v2 import BOAction

''' - Put 0 for integer entries not used (e.g. supply or worker_count) and 
    () for tuple entries not used (e.g. prereq_buildings).
    - If just-1 tuple entry, make sure to use (thing,) notation.'''

#'automatic', BOAction.STABLE_VESPENE
#   when not activated, the bot is quicker to change between minerals and vespene and takes gas geysers faster
#   when activated, the bot is more hesitant to switch workers between minerals and vespene and takes gas geysers slower
build = {
    'automatic' : [
        #[name, supply, count, (prereq_buildings)]
        [BOAction.BUILD_OVERLORDS, 0, 4, ()],
        [BOAction.BUILD_HATCHERIES, 58, 4, ()],
        [BOAction.BUILD_QUEENS, 0, 0, (UnitTypeId.SPAWNINGPOOL,)],
        [BOAction.STABLE_VESPENE, 0, 44, ()]
    ],
    'economy' : [
        #[supply_threshold, max_worker_count]
        #order matters
        [70, 19],
        [200, 80]
    ],
    'supply' : [
        #[supply, count]
        [14, 2],
        [19, 3],
        [26, 4]
    ],
    'gas' : [
        #[supply, count]
        [13, 1]
    ],
    'gas_ratio' : [
        #[worker_count, workers_on_gas]
        #order matters
        [0, 0],
        [11, 2],
        [14, 3]
    ],
    'gas_max': [
        #[worker_count, extractor_count]
        [13, 1]
    ],
    'bases' : [
        #[supply, base_count, worker_count]
        [29, 2, 0]
    ],
    'buildings' : [
        #[id, supply, worker_count, (prereq_buildings), amount]
        [UnitTypeId.SPAWNINGPOOL, 12, 0, (UnitTypeId.EXTRACTOR,), 1],
        [UnitTypeId.BANELINGNEST, 19, 0, (UnitTypeId.EXTRACTOR, UnitTypeId.SPAWNINGPOOL), 1]
    ],
    'units' : [
        #[id, supply, unit_count, (prereq_buildings)]
        [UnitTypeId.BANELING, 17, 4, (UnitTypeId.SPAWNINGPOOL, UnitTypeId.BANELINGNEST)],
        [UnitTypeId.ZERGLING, 17, 60, (UnitTypeId.SPAWNINGPOOL,)]
    ],
    'upgrades' : [
        #[id, supply, (prereq_upgrades), (prereq_buildings), worker_count]
        [UpgradeId.ZERGLINGMOVEMENTSPEED, 17, (), (), 0]
    ]
}

comp = [
    defaultdict(lambda: (UnitTypeId.ZERGLING, UnitTypeId.BANELING)),
    [ #fallback
        [UnitTypeId.BANELING, UnitTypeId.ZERGLING],
        [UnitTypeId.ZERGLING]
    ],
    [ #desperation
        [UnitTypeId.ZERGLING],
        [UnitTypeId.QUEEN],
        [UnitTypeId.QUEEN]
    ],
    [UnitTypeId.BANELING, UnitTypeId.ZERGLING], #possible
    None,
    False
]