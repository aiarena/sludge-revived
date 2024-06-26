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
        [30, 3, 24],
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
        [16, 4],
        [48, 20]
        #[38, 2],
        #[44, 4],
        #[50, 5],
        #[56, 6],
        #[63, 7],
        #[66, 12],
        #[80, 18]
    ],
    'buildings' : [
        #[id, supply, worker_count, (prereq_buildings), amount]
        [UnitTypeId.SPAWNINGPOOL, 17, 0, (UnitTypeId.EXTRACTOR,), 1],
        [UnitTypeId.BANELINGNEST, 30, 0, (UnitTypeId.EXTRACTOR,), 1],
        [UnitTypeId.ROACHWARREN, 44, 44, (), 1],
        [UnitTypeId.EVOLUTIONCHAMBER, 38, 38, (), 1],
        [UnitTypeId.LAIR, 44, 44, (), 1],
        [UnitTypeId.EVOLUTIONCHAMBER, 63, 63, (), 2],
        [UnitTypeId.HYDRALISKDEN, 120, 63, (UnitTypeId.LAIR,), 1]
    ],
    'units' : [
        #[id, supply, unit_count, (prereq_buildings)]
        [UnitTypeId.ZERGLING, 17, 28, ()],
        [UnitTypeId.BANELING, 30, 4, ()],
        [UnitTypeId.OVERSEER, 40, 1, ()]
    ],
    'upgrades' : [
        #[id, supply, (prereq_upgrades), (prereq_buildings), worker_count]
        [UpgradeId.ZERGLINGMOVEMENTSPEED, 17, (), (), 0],
        [UpgradeId.GLIALRECONSTITUTION, 40, (), (UnitTypeId.LAIR,), 0],
        [UpgradeId.EVOLVEGROOVEDSPINES, 0, (), (), 0],
        [UpgradeId.EVOLVEMUSCULARAUGMENTS, 0, (UpgradeId.EVOLVEGROOVEDSPINES,), (), 0],

        [UpgradeId.ZERGMISSILEWEAPONSLEVEL1, 0, (), (), 0],
        [UpgradeId.ZERGMISSILEWEAPONSLEVEL2, 0, (UpgradeId.ZERGMISSILEWEAPONSLEVEL1,), (), 0],
        [UpgradeId.ZERGMISSILEWEAPONSLEVEL3, 0, (UpgradeId.ZERGMISSILEWEAPONSLEVEL1, UpgradeId.ZERGMISSILEWEAPONSLEVEL2), (UnitTypeId.HIVE,), 0],

        [UpgradeId.ZERGGROUNDARMORSLEVEL1, 0, (), (), 0],
        [UpgradeId.ZERGGROUNDARMORSLEVEL2, 0, (UpgradeId.ZERGGROUNDARMORSLEVEL1,), (), 0],
        [UpgradeId.ZERGGROUNDARMORSLEVEL3, 0, (UpgradeId.ZERGGROUNDARMORSLEVEL1, UpgradeId.ZERGMISSILEWEAPONSLEVEL2), (UnitTypeId.HIVE,), 0],

        [UpgradeId.OVERLORDSPEED, 130, (), (UnitTypeId.LAIR,), 70]
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