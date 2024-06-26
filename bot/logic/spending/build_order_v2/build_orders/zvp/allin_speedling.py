from collections import defaultdict

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from bot.logic.spending.build_order_v2.build_order_v2 import BOAction

build = {
    'automatic' : [
        #[name, supply, count, (prereq_buildings)]
        [BOAction.BUILD_OVERLORDS, 0, 3, ()],
        [BOAction.BUILD_HATCHERIES, 58, 4, ()],
        [BOAction.BUILD_QUEENS, 0, 0, (UnitTypeId.SPAWNINGPOOL,)],
        [BOAction.STABLE_VESPENE, 0, 35, ()]
    ],
    'economy' : [
        #[supply_threshold, max_worker_count]
        #order matters
        [120, 66],
        [200, 80]
    ],
    'supply' : [
        #[supply, count]
        [13, 2],
        [19, 3]
    ],
    'bases' : [
        #[supply, base_count, worker_count]
        [17, 2, 0],
        [30, 3, 20],
        [58, 4, 58]
    ],
    'gas' : [
        #[supply, count]
        [18, 1]
    ],
    'gas_ratio' : [
        #[worker_count, workers_on_gas]
        #order matters
        [0, 0],
        [16, 1],
        [32, 3],
        [50, 12],
        [66, 18],
        [80, 24]
    ],
    'gas_max': [
        #[worker_count, extractor_count]
        [38, 2],
        [44, 3],
        [56, 5],
        [63, 6],
        [66, 12],
        [80, 18]
    ],
    'buildings' : [
        #[id, supply, worker_count, (prereq_buildings), amount]
        [UnitTypeId.SPAWNINGPOOL, 17, 0, (UnitTypeId.EXTRACTOR,), 1]
    ],
    'units' : [
        #[id, supply, unit_count, (prereq_buildings)]
        [UnitTypeId.ZERGLING, 17, 60, ()]
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