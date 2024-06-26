from typing import List, Dict

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from bot.logic.spending.build_order_v2.build_order_v2 import BOStep, BOAction
from bot.services.state_service import StateService

def get_build(state : StateService):
    return [
            BOStep(
                13,
                lambda: state.get_unit_count(UnitTypeId.OVERLORD) >= 2,
                lambda: state.get_unit_count(UnitTypeId.OVERLORD) < 2,
                UnitTypeId.OVERLORD
            ),
            BOStep(
                17,
                lambda: state.pending_townhalls() >= 2,
                lambda: state.pending_townhalls() < 2,
                UnitTypeId.HATCHERY
            ),
            BOStep(
                18,
                lambda: state.get_unit_count(UnitTypeId.EXTRACTOR) > 1,
                lambda: state.get_unit_count(UnitTypeId.EXTRACTOR) < 1,
                UnitTypeId.EXTRACTOR
            ),
            BOStep(
                17,
                lambda: state.get_unit_count(UnitTypeId.SPAWNINGPOOL) > 1,
                lambda: (state.get_unit_count(UnitTypeId.SPAWNINGPOOL) < 1
                        and state.get_unit_count(UnitTypeId.EXTRACTOR) >= 1),
                UnitTypeId.SPAWNINGPOOL
            ),
            BOStep(
                17,
                lambda: state.get_unit_count(UnitTypeId.ZERGLING) > 1,
                lambda: state.own_structures(UnitTypeId.SPAWNINGPOOL).ready.exists,
                UnitTypeId.ZERGLING
            ),
            BOStep(
                17,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) > 0
                        or UpgradeId.ZERGLINGMOVEMENTSPEED in state.upgrades),
                lambda: (state.own_units(UnitTypeId.SPAWNINGPOOL).ready.exists
                        and state.get_unit_count(UnitTypeId.EXTRACTOR) > 0),
                UpgradeId.ZERGLINGMOVEMENTSPEED
            ),
            BOStep(
                19,
                lambda: state.get_unit_count(UnitTypeId.OVERLORD) >= 3,
                lambda: state.get_unit_count(UnitTypeId.OVERLORD) < 3,
                UnitTypeId.OVERLORD
            ),
            BOStep(
                0,
                lambda: False,
                lambda: state.get_unit_count(UnitTypeId.OVERLORD) >= 3,
                BOAction.BUILD_OVERLORDS, True
            ),
            BOStep(
                0,
                lambda: False,
                lambda: state.own_structures(UnitTypeId.SPAWNINGPOOL).ready.exists,
                BOAction.BUILD_QUEENS, True
            ),
            BOStep(
                30,
                lambda: state.pending_townhalls() >= 3,
                lambda: (state.pending_townhalls() < 3
                        and state.get_unit_count(UnitTypeId.DRONE) >= 24),
                UnitTypeId.HATCHERY
            ),
            BOStep(
                30,
                lambda: False,
                lambda: state.pending_townhalls() > 2,
                BOAction.BUILD_HATCHERIES, True
            ),
            BOStep(
                38,
                lambda: state.get_unit_count(UnitTypeId.BANELINGNEST) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.BANELINGNEST) < 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 38),
                UnitTypeId.BANELINGNEST
            ),
            #BOStep(
            #    38,
            #    lambda: state.get_unit_count(UnitTypeId.EXTRACTOR) >= 3,
            #    lambda: (state.get_unit_count(UnitTypeId.EXTRACTOR) < 3
            #            and state.get_unit_count(UnitTypeId.DRONE) >= 38),
            #    UnitTypeId.EXTRACTOR
            #),
            BOStep(
                40,
                lambda: (state.get_unit_count(UnitTypeId.LAIR) >= 1
                        or state.get_unit_count(UnitTypeId.HIVE) >= 1),
                lambda: state.get_unit_count(UnitTypeId.DRONE) >= 32,
                UnitTypeId.LAIR
            ),
            BOStep(
                40,
                lambda: state.get_unit_count(UnitTypeId.OVERSEER) >= 1,
                lambda: state.own_structures(UnitTypeId.LAIR).exists,
                UnitTypeId.OVERSEER
            ),
            BOStep(
                40,
                lambda: (state.already_pending_upgrade(UpgradeId.CENTRIFICALHOOKS) > 0
                        or UpgradeId.CENTRIFICALHOOKS in state.upgrades),
                lambda: state.own_structures(UnitTypeId.LAIR).exists,
                UpgradeId.CENTRIFICALHOOKS
            ),
            BOStep(
                63,
                lambda: state.get_unit_count(UnitTypeId.HYDRALISKDEN) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.HYDRALISKDEN) < 1
                        and state.get_unit_count(UnitTypeId.LAIR) > 0
                        and state.get_unit_count(UnitTypeId.DRONE) >= 63),
                UnitTypeId.HYDRALISKDEN
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.EVOLVEGROOVEDSPINES) > 0
                        or UpgradeId.EVOLVEGROOVEDSPINES in state.upgrades),
                lambda: state.own_structures(UnitTypeId.HYDRALISKDEN).ready.exists,
                UpgradeId.EVOLVEGROOVEDSPINES
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.EVOLVEMUSCULARAUGMENTS) > 0
                        or UpgradeId.EVOLVEMUSCULARAUGMENTS in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.HYDRALISKDEN).ready.exists
                        and UpgradeId.EVOLVEGROOVEDSPINES in state.upgrades),
                UpgradeId.EVOLVEMUSCULARAUGMENTS
            ),
            #BOStep(
            #    52,
            #    lambda: state.get_unit_count(UnitTypeId.EXTRACTOR) >= 5,
            #    lambda: (state.get_unit_count(UnitTypeId.EXTRACTOR) < 5
            #            and state.get_unit_count(UnitTypeId.DRONE) >= 52),
            #    UnitTypeId.EXTRACTOR
            #),
            BOStep(
                56,
                lambda: state.get_unit_count(UnitTypeId.EVOLUTIONCHAMBER) >= 2,
                lambda: (state.get_unit_count(UnitTypeId.EVOLUTIONCHAMBER) < 2
                        and state.get_unit_count(UnitTypeId.DRONE) >= 56),
                UnitTypeId.EVOLUTIONCHAMBER
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMELEEWEAPONSLEVEL1) > 0
                        or UpgradeId.ZERGMELEEWEAPONSLEVEL1 in state.upgrades),
                lambda: state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists,
                UpgradeId.ZERGMELEEWEAPONSLEVEL1
            ), 
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMELEEWEAPONSLEVEL2) > 0
                        or UpgradeId.ZERGMELEEWEAPONSLEVEL2 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and UpgradeId.ZERGMELEEWEAPONSLEVEL1 in state.upgrades),
                UpgradeId.ZERGMELEEWEAPONSLEVEL2
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMISSILEWEAPONSLEVEL1) > 0
                        or UpgradeId.ZERGMISSILEWEAPONSLEVEL1 in state.upgrades),
                lambda: state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists,
                UpgradeId.ZERGMISSILEWEAPONSLEVEL1
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMELEEWEAPONSLEVEL3) > 0
                        or UpgradeId.ZERGMELEEWEAPONSLEVEL3 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and state.own_structures(UnitTypeId.HIVE).ready.exists
                        and UpgradeId.ZERGMELEEWEAPONSLEVEL2 in state.upgrades),
                UpgradeId.ZERGMELEEWEAPONSLEVEL3
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGGROUNDARMORSLEVEL1) > 0
                        or UpgradeId.ZERGGROUNDARMORSLEVEL1 in state.upgrades),
                lambda: state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists,
                UpgradeId.ZERGGROUNDARMORSLEVEL1
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGGROUNDARMORSLEVEL2) > 0
                        or UpgradeId.ZERGGROUNDARMORSLEVEL2 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and UpgradeId.ZERGGROUNDARMORSLEVEL1 in state.upgrades),
                UpgradeId.ZERGGROUNDARMORSLEVEL2
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGLINGATTACKSPEED) > 0
                        or UpgradeId.ZERGLINGATTACKSPEED in state.upgrades),
                lambda: state.own_structures(UnitTypeId.HYDRALISKDEN).ready.exists,
                UpgradeId.ZERGLINGATTACKSPEED
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGGROUNDARMORSLEVEL3) > 0
                        or UpgradeId.ZERGGROUNDARMORSLEVEL3 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and state.own_structures(UnitTypeId.HIVE).ready.exists
                        and UpgradeId.ZERGGROUNDARMORSLEVEL2 in state.upgrades),
                UpgradeId.ZERGGROUNDARMORSLEVEL3
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMISSILEWEAPONSLEVEL2) > 0
                        or UpgradeId.ZERGMISSILEWEAPONSLEVEL2 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and UpgradeId.ZERGMISSILEWEAPONSLEVEL1 in state.upgrades),
                UpgradeId.ZERGMISSILEWEAPONSLEVEL2
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMISSILEWEAPONSLEVEL3) > 0
                        or UpgradeId.ZERGMISSILEWEAPONSLEVEL3 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and state.own_structures(UnitTypeId.HIVE).ready.exists
                        and UpgradeId.ZERGMISSILEWEAPONSLEVEL2 in state.upgrades),
                UpgradeId.ZERGMISSILEWEAPONSLEVEL3
            ),
            BOStep(
                58,
                lambda: (state.already_pending_upgrade(UpgradeId.OVERLORDSPEED) > 0
                        or UpgradeId.OVERLORDSPEED in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.LAIR).exists
                        and state.get_unit_count(UnitTypeId.DRONE) > 58),
                UpgradeId.OVERLORDSPEED
            ),
            BOStep(
                150,
                lambda: state.get_unit_count(UnitTypeId.INFESTATIONPIT) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.INFESTATIONPIT) < 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 70),
                UnitTypeId.INFESTATIONPIT
            ),
            BOStep(
                150,
                lambda: (state.get_unit_count(UnitTypeId.SPIRE) >= 1
                        or state.get_unit_count(UnitTypeId.GREATERSPIRE) >= 1),
                lambda: (state.get_unit_count(UnitTypeId.SPIRE) < 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 75),
                UnitTypeId.SPIRE
            ),
            BOStep(
                150,
                lambda: state.get_unit_count(UnitTypeId.HIVE) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.HIVE) < 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 75),
                UnitTypeId.HIVE
            ),
            #BOStep(
            #    75,
            #    lambda: state.get_unit_count(UnitTypeId.EXTRACTOR) >= 7,
            #    lambda: (state.get_unit_count(UnitTypeId.EXTRACTOR) < 7
            #            and state.get_unit_count(UnitTypeId.DRONE) >= 75),
            #    UnitTypeId.EXTRACTOR
            #),
            BOStep(
                160,
                lambda: state.get_unit_count(UnitTypeId.GREATERSPIRE) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.GREATERSPIRE) < 1
                        and state.get_unit_count(UnitTypeId.SPIRE) >= 1
                        and state.get_unit_count(UnitTypeId.HIVE) >= 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 75),
                UnitTypeId.GREATERSPIRE
            ),
            #BOStep(
            #    75,
            #    lambda: state.get_unit_count(UnitTypeId.EXTRACTOR) >= 8,
            #    lambda: (state.get_unit_count(UnitTypeId.EXTRACTOR) < 8
            #            and state.get_unit_count(UnitTypeId.DRONE) >= 75),
            #    UnitTypeId.EXTRACTOR
            #),
        ]
    
def get_army_comp(state : StateService):
    goal_army_composition: Dict[UnitTypeId, int] = {}
    fallback_units: List[UnitTypeId] = []

    own_roaches = state.own_army_units(UnitTypeId.ROACH)

    # ORDER IS PRIORITY
    if state.own_structures(UnitTypeId.GREATERSPIRE).ready:
        goal_army_composition[UnitTypeId.BROODLORD] = 0
    if state.own_structures({UnitTypeId.SPIRE, UnitTypeId.GREATERSPIRE}).ready:
        goal_army_composition[UnitTypeId.CORRUPTOR] = 0
    if state.own_structures(UnitTypeId.HYDRALISKDEN).ready:
        goal_army_composition[UnitTypeId.HYDRALISK] = 0
    if state.own_structures(UnitTypeId.BANELINGNEST).ready:
        goal_army_composition[UnitTypeId.BANELING] = 0
    if state.own_structures(UnitTypeId.SPAWNINGPOOL).ready:
        goal_army_composition[UnitTypeId.ZERGLING] = 0
        fallback_units.append(UnitTypeId.ZERGLING)
    goal_army_composition[UnitTypeId.QUEEN] = 0

    
    if own_roaches.exists and UnitTypeId.ROACH in goal_army_composition and own_roaches.amount >= 25:
        goal_army_composition[UnitTypeId.RAVAGER] += own_roaches.amount // 5

    if UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.CORRUPTOR] = 12 - (state.get_unit_count(UnitTypeId.CORRUPTOR) + state.get_unit_count(UnitTypeId.BROODLORD))

    own_corruptors = state.own_army_units(UnitTypeId.CORRUPTOR)
    if own_corruptors.exists and UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.BROODLORD] += own_corruptors.amount

    # ----#
    # ZvT #
    # ----#

    marines = state.enemy_army_units(UnitTypeId.MARINE)
    if marines.exists:
        if UnitTypeId.BANELING in goal_army_composition:
            goal_army_composition[UnitTypeId.BANELING] += marines.amount // 4
            goal_army_composition[UnitTypeId.ZERGLING] += int(1.5 * marines.amount)
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 2 * marines.amount

    marauders = state.enemy_army_units(UnitTypeId.MARAUDER)
    if marauders.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += marauders.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 2 * marauders.amount

    hellions = state.enemy_army_units(UnitTypeId.HELLION)
    if marauders.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += hellions.amount
        elif UnitTypeId.BANELING in goal_army_composition:
            goal_army_composition[UnitTypeId.BANELING] += hellions.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 2 * hellions.amount

    siege_tanks = state.enemy_army_units(UnitTypeId.SIEGETANK)
    if siege_tanks.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += 2 * siege_tanks.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 4 * siege_tanks.amount

    thors = state.enemy_army_units(UnitTypeId.THOR)
    if thors.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += 3 * thors.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 6 * thors.amount

    medivacs = state.enemy_army_units(UnitTypeId.MEDIVAC)
    if medivacs.exists and UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.HYDRALISK] += medivacs.amount

    liberators = state.enemy_army_units(UnitTypeId.LIBERATOR)
    if liberators.exists and UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.HYDRALISK] += liberators.amount

    banshees = state.enemy_army_units(UnitTypeId.BANSHEE)
    if banshees.exists and UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.HYDRALISK] += banshees.amount

    ravens = state.enemy_army_units(UnitTypeId.RAVEN)
    if ravens.exists and UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.HYDRALISK] += ravens.amount

    battlecruisers = state.enemy_army_units(UnitTypeId.BATTLECRUISER)
    if battlecruisers.exists and UnitTypeId.CORRUPTOR in goal_army_composition:
        goal_army_composition[UnitTypeId.CORRUPTOR] += 3 * battlecruisers.amount
    elif battlecruisers.exists and UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.HYDRALISK] += 5 * battlecruisers.amount

    return goal_army_composition, fallback_units, []