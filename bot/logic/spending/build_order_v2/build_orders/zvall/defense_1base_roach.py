from typing import List, Dict

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from bot.logic.spending.build_order_v2.build_order_v2 import BOAction
from bot.services.state_service import StateService

def all_standard_comp_extra(state : StateService):
    goal_army_composition: Dict[UnitTypeId, int] = {}

    own_roaches = state.own_army_units(UnitTypeId.ROACH)

    if own_roaches.exists and UnitTypeId.ROACH in goal_army_composition and own_roaches.amount >= 25:
        goal_army_composition[UnitTypeId.RAVAGER] += own_roaches.amount // 5

    if UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.CORRUPTOR] = 12 - (state.get_unit_count(UnitTypeId.CORRUPTOR) + state.get_unit_count(UnitTypeId.BROODLORD))

    own_corruptors = state.own_army_units(UnitTypeId.CORRUPTOR)
    if own_corruptors.exists and UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.BROODLORD] += own_corruptors.amount

    #TODO can test if bot still responds to voidrays even if this is commented out
    '''if state._bot.enemy_race == Race.Protoss:
        voidrays = state.enemy_army_units(UnitTypeId.VOIDRAY)
        if voidrays.exists and UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += 3 * voidrays.amount
        if voidrays.exists and not UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.QUEEN] += 2 + 2 * voidrays.amount'''

    return goal_army_composition

build = {
    'automatic' : [
        #[name, supply, count, (prereq_buildings)]
        [BOAction.BUILD_OVERLORDS, 0, 3, ()],
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
        [19, 3]
    ],
    'bases' : [
        #[supply, base_count, worker_count]
        [16, 2, 0],
        [60, 3, 24]
    ],
    'gas' : [
        #[supply, count]
        [18, 1]
    ],
    'gas_ratio' : [
        #[worker_count, workers_on_gas]
        #order matters
        [0, 0],
        [16, 3],
        [32, 3],
        [50, 12],
        [66, 18],
        [80, 24]
    ],
    'gas_max': [
        #[worker_count, extractor_count]
        [16, 1],
        [24, 3],
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
        [UnitTypeId.ROACHWARREN, 24, 24, (UnitTypeId.SPAWNINGPOOL,), 1],
        [UnitTypeId.LAIR, 40, 32, (), 1],
        [UnitTypeId.EVOLUTIONCHAMBER, 58, 58, (), 2],
        [UnitTypeId.HYDRALISKDEN, 63, 63, (UnitTypeId.LAIR,), 1],
        [UnitTypeId.INFESTATIONPIT, 180, 70, (), 1],
        [UnitTypeId.SPIRE, 180, 75, (), 1],
        [UnitTypeId.HIVE, 180, 75, (), 1],
        [UnitTypeId.GREATERSPIRE, 160, 75, (UnitTypeId.SPIRE, UnitTypeId.HIVE), 1] #TODO make sure no bugs with spire
    ],
    'units' : [
        #[id, supply, unit_count, (prereq_buildings)]
        [UnitTypeId.ZERGLING, 17, 2, (UnitTypeId.SPAWNINGPOOL,)],
        [UnitTypeId.OVERSEER, 40, 1, (UnitTypeId.LAIR,)]
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

        [UpgradeId.OVERLORDSPEED, 57, (), (UnitTypeId.LAIR,), 57]
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
    {   UnitTypeId.DRONE : None,
        UnitTypeId.ZERGLING : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.BANELING : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.QUEEN : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.ROACH : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.RAVAGER : (UnitTypeId.RAVAGER, UnitTypeId.ROACH),
        UnitTypeId.HYDRALISK : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.LURKER : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.INFESTOR : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.SWARMHOSTMP : None,
        UnitTypeId.ULTRALISK : None,

        UnitTypeId.MUTALISK : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.CORRUPTOR : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.BROODLORD : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.VIPER : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),

        UnitTypeId.PROBE : None,
        UnitTypeId.ZEALOT : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.ADEPT : (UnitTypeId.ROACH, UnitTypeId.ZERGLING), 
        UnitTypeId.SENTRY : (UnitTypeId.RAVAGER, UnitTypeId.ROACH),
        UnitTypeId.STALKER : (UnitTypeId.HYDRALISK, UnitTypeId.ZERGLING), 
        UnitTypeId.HIGHTEMPLAR : (UnitTypeId.ROACH,),
        UnitTypeId.DARKTEMPLAR : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.ARCHON : (UnitTypeId.HYDRALISK, UnitTypeId.ZERGLING), 
        UnitTypeId.IMMORTAL : (UnitTypeId.HYDRALISK, UnitTypeId.ZERGLING), 
        UnitTypeId.DISRUPTOR : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.COLOSSUS : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),

        UnitTypeId.PHOENIX : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.ORACLE : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.VOIDRAY : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.CARRIER : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.TEMPEST : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.MOTHERSHIP : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.WARPPRISM : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),

        UnitTypeId.SCV : None,
        UnitTypeId.MARINE : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.MARAUDER : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.REAPER : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.GHOST : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.HELLION : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.HELLIONTANK : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.SIEGETANK : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.THOR : (UnitTypeId.HYDRALISK, UnitTypeId.ROACH),
        UnitTypeId.WIDOWMINE : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),

        UnitTypeId.BATTLECRUISER : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.RAVEN : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.MEDIVAC : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.LIBERATOR : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.VIKING : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.BANSHEE : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN)},
    [ #fallback
        [UnitTypeId.BROODLORD, UnitTypeId.CORRUPTOR, UnitTypeId.HYDRALISK],
        [UnitTypeId.HYDRALISK, UnitTypeId.ROACH],
        [UnitTypeId.ROACH, UnitTypeId.ZERGLING],
        [UnitTypeId.ZERGLING]
    ],
    [ #desperation
        [UnitTypeId.RAVAGER, UnitTypeId.ROACH, UnitTypeId.ZERGLING],
        [UnitTypeId.ZERGLING],
        [UnitTypeId.QUEEN],
        [UnitTypeId.QUEEN]
    ],
    [UnitTypeId.BROODLORD, UnitTypeId.CORRUPTOR, UnitTypeId.HYDRALISK, UnitTypeId.ROACH, UnitTypeId.RAVAGER,
    UnitTypeId.BANELING, UnitTypeId.ZERGLING], #possible
    all_standard_comp_extra,
    False
]