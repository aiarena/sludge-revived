from typing import List, Dict

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

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

#TODO make army comp manager take three dicts, one for each race, rather than one huge dict
all_standard_comp = [
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
        UnitTypeId.HIGHTEMPLAR : None,
        UnitTypeId.DARKTEMPLAR : None,
        UnitTypeId.ARCHON : (UnitTypeId.HYDRALISK, UnitTypeId.ZERGLING), 
        UnitTypeId.IMMORTAL : (UnitTypeId.HYDRALISK, UnitTypeId.ZERGLING), 
        UnitTypeId.DISRUPTOR : None,
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

zvz_standard_comp = [
    {   UnitTypeId.DRONE : None,
        UnitTypeId.ZERGLING : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.BANELING : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.QUEEN : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.ROACH : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.RAVAGER : (UnitTypeId.RAVAGER, UnitTypeId.ROACH),
        UnitTypeId.HYDRALISK : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.LURKER : (UnitTypeId.RAVAGER, UnitTypeId.ROACH),
        UnitTypeId.INFESTOR : (UnitTypeId.ROACH, UnitTypeId.ZERGLING),
        UnitTypeId.SWARMHOSTMP : None,
        UnitTypeId.ULTRALISK : None,

        UnitTypeId.MUTALISK : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.CORRUPTOR : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.BROODLORD : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN),
        UnitTypeId.VIPER : (UnitTypeId.HYDRALISK, UnitTypeId.QUEEN)
    },
    [ #fallback
        [UnitTypeId.BROODLORD, UnitTypeId.CORRUPTOR, UnitTypeId.HYDRALISK],
        [UnitTypeId.ROACH, UnitTypeId.RAVAGER],
        [UnitTypeId.ROACH, UnitTypeId.ZERGLING],
        [UnitTypeId.ZERGLING]
    ],
    [ #desperation
        [UnitTypeId.RAVAGER, UnitTypeId.ROACH, UnitTypeId.ZERGLING],
        [UnitTypeId.ROACH, UnitTypeId.ZERGLING],
        [UnitTypeId.QUEEN],
        [UnitTypeId.QUEEN]
    ],
    [UnitTypeId.BROODLORD, UnitTypeId.CORRUPTOR, UnitTypeId.HYDRALISK, UnitTypeId.ROACH, UnitTypeId.RAVAGER,
    UnitTypeId.BANELING, UnitTypeId.ZERGLING], #possible
    all_standard_comp_extra,
    False
]