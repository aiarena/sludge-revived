from collections import defaultdict
from typing import List, Dict

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from bot.logic.spending.build_order_v2.build_order_v2 import BOAction
from bot.services.state_service import StateService

'''Standard HLB is not meant to be used in ZvZ! Only ZvP and ZvT composition counters are written.'''

def all_standard_comp_extra(state : StateService):
    goal_army_composition: Dict[UnitTypeId, int] = {}

    if UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.CORRUPTOR] = 12 - (state.get_unit_count(UnitTypeId.CORRUPTOR) + state.get_unit_count(UnitTypeId.BROODLORD))

    own_corruptors = state.own_army_units(UnitTypeId.CORRUPTOR)
    if own_corruptors.exists and UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.BROODLORD] += own_corruptors.amount

    return goal_army_composition

build = {
    'automatic' : [
        #[name, supply, count, (prereq_buildings)]
        [BOAction.BUILD_OVERLORDS, 0, 4, ()],
        [BOAction.BUILD_HATCHERIES, 58, 4, ()],
        [BOAction.BUILD_QUEENS, 0, 0, (UnitTypeId.SPAWNINGPOOL,)],
        [BOAction.STABLE_VESPENE, 0, 55, ()]
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
        [19, 3],
        [33, 4]
    ],
    'bases' : [
        #[supply, base_count, worker_count]
        [16, 2, 0],
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
        [28, 3],
        [50, 12],
        [66, 18],
        [80, 24]
    ],
    'gas_max': [
        #[worker_count, extractor_count]
        [16, 1],
        [28, 4],
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
        [UnitTypeId.LAIR, 35, 35, (), 1],
        [UnitTypeId.BANELINGNEST, 38, 38, (), 1],
        [UnitTypeId.HYDRALISKDEN, 55, 55, (UnitTypeId.LAIR,), 1],
        [UnitTypeId.EVOLUTIONCHAMBER, 63, 63, (), 2],
        [UnitTypeId.INFESTATIONPIT, 180, 70, (), 1],
        [UnitTypeId.SPIRE, 180, 75, (), 1],
        [UnitTypeId.HIVE, 180, 75, (), 1],
        [UnitTypeId.GREATERSPIRE, 160, 75, (UnitTypeId.SPIRE, UnitTypeId.HIVE), 1] #TODO make sure no bugs with spire
    ],
    'units' : [
        #[id, supply, unit_count, (prereq_buildings)]
        [UnitTypeId.ZERGLING, 17, 2, (UnitTypeId.SPAWNINGPOOL,)],
        [UnitTypeId.QUEEN, 44, 5, (UnitTypeId.SPAWNINGPOOL,)],
        [UnitTypeId.OVERSEER, 40, 1, (UnitTypeId.LAIR,)]
    ],
    'upgrades' : [
        #[id, supply, (prereq_upgrades), (prereq_buildings), worker_count]
        [UpgradeId.ZERGLINGMOVEMENTSPEED, 17, (), (UnitTypeId.SPAWNINGPOOL,), 0],
        [UpgradeId.CENTRIFICALHOOKS, 0, (), (UnitTypeId.SPAWNINGPOOL, UnitTypeId.LAIR), 0],
        [UpgradeId.EVOLVEGROOVEDSPINES, 0, (), (UnitTypeId.HYDRALISKDEN,), 0],
        [UpgradeId.EVOLVEMUSCULARAUGMENTS, 0, (UpgradeId.EVOLVEGROOVEDSPINES,), (UnitTypeId.HYDRALISKDEN,), 0],

        [UpgradeId.ZERGMELEEWEAPONSLEVEL1, 0, (), (), 0],
        [UpgradeId.ZERGMELEEWEAPONSLEVEL2, 0, (UpgradeId.ZERGMELEEWEAPONSLEVEL1,), (UnitTypeId.LAIR,), 0],
        [UpgradeId.ZERGMELEEWEAPONSLEVEL3, 0, (UpgradeId.ZERGMELEEWEAPONSLEVEL1, UpgradeId.ZERGMELEEWEAPONSLEVEL2), (UnitTypeId.HIVE,), 0],

        [UpgradeId.ZERGGROUNDARMORSLEVEL1, 0, (), (), 0],
        [UpgradeId.ZERGGROUNDARMORSLEVEL2, 0, (UpgradeId.ZERGGROUNDARMORSLEVEL1,), (UnitTypeId.LAIR,), 0],
        [UpgradeId.ZERGGROUNDARMORSLEVEL3, 0, (UpgradeId.ZERGGROUNDARMORSLEVEL1, UpgradeId.ZERGGROUNDARMORSLEVEL2), (UnitTypeId.HIVE,), 0],

        [UpgradeId.OVERLORDSPEED, 70, (), (UnitTypeId.LAIR,), 70]
    ]
}

'''Syntax of army composition data:
unit_assignment_dict : Dict[UnitTypeId, Tuple[UnitTypeId]]
fallback units: List[UnitTypeId],
desperation units: List[UnitTypeId],
possible units: List[UnitTypeId],
(optional) extra considerations: function,
(optional, default=False) overriding considerations: bool

unit_assignment_dict is used to choose the appropriate unit to face the given enemy unit.
    - The bot chooses to build the first unit it has the tech/buildings to produce in the given tuple.
    - If None is given or the bot can't produce any of the units in the tuple, the bot will derive
    what unit to build based on which unit performs best vs the given enemy unit (based on unit_counters). 
    - possible units list includes all units considered for deriving units to build.

Put a list lists of units (army compositions) for fallback units.
    - the bot will choose the first army composition it can build all the units of, therefore
    put the highest tech army compositions first.

For desperation units, put the desperation units of the corresponding army composition in fallback units.
    - for example, early on, the only desperation unit will likely be a Queen, but later on
    zerglings should be included, since they won't be included in fallback units (for roach-hydra army comp)

Overriding considerations causes the goal army composition to be .update()
by the output of extra considerations, meaning any key-value pairs
defined in extra considerations will replace those in the automatically generated goal army comp.
    - can be useful if you don't want the bot making any ground units vs air (make all ground units equal to zero)
'''

comp = [
    defaultdict(lambda: (UnitTypeId.HYDRALISK, UnitTypeId.ZERGLING), 
    {   UnitTypeId.ZEALOT : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.ADEPT : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.SENTRY : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.COLOSSUS : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),

        UnitTypeId.PHOENIX : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.ORACLE : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.VOIDRAY : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.CARRIER : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.TEMPEST : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.MOTHERSHIP : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.WARPPRISM : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),

        UnitTypeId.SCV : None,
        UnitTypeId.MARINE : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.REAPER : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.GHOST : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.HELLION : (UnitTypeId.HYDRALISK, UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.HELLIONTANK : (UnitTypeId.BANELING, UnitTypeId.ZERGLING),
        UnitTypeId.WIDOWMINE : (UnitTypeId.HYDRALISK, UnitTypeId.BANELING, UnitTypeId.ZERGLING),

        UnitTypeId.BATTLECRUISER : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.RAVEN : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.MEDIVAC : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.LIBERATOR : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.VIKING : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.BANSHEE : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN)}),
    [ #fallback
        [UnitTypeId.BROODLORD, UnitTypeId.CORRUPTOR, UnitTypeId.HYDRALISK],
        [UnitTypeId.HYDRALISK, UnitTypeId.ZERGLING],
        [UnitTypeId.BANELING, UnitTypeId.ZERGLING],
        [UnitTypeId.ZERGLING]
    ],
    [ #desperation
        [UnitTypeId.BANELING, UnitTypeId.ZERGLING],
        [UnitTypeId.BANELING, UnitTypeId.ZERGLING],
        [UnitTypeId.QUEEN],
        [UnitTypeId.QUEEN]
    ],
    [UnitTypeId.BROODLORD, UnitTypeId.CORRUPTOR, UnitTypeId.HYDRALISK, UnitTypeId.BANELING, UnitTypeId.ZERGLING], #possible
    all_standard_comp_extra,
    False
]