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
                lambda: state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) > 1,
                lambda: state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) < 1,
                UnitTypeId.EXTRACTOR
            ),
            BOStep(
                17,
                lambda: state.get_unit_count(UnitTypeId.SPAWNINGPOOL) > 1,
                lambda: (state.get_unit_count(UnitTypeId.SPAWNINGPOOL) < 1
                        and state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) >= 1),
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
                        and state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) > 0),
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
                lambda: state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) >= 3,
                lambda: (state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) < 3
                        and state.get_unit_count(UnitTypeId.DRONE) >= 38),
                UnitTypeId.EXTRACTOR
            ),
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
                44,
                lambda: state.get_unit_count(UnitTypeId.HYDRALISKDEN) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.HYDRALISKDEN) < 1
                        and state.get_unit_count(UnitTypeId.LAIR) > 0
                        and state.get_unit_count(UnitTypeId.DRONE) >= 44),
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
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMISSILEWEAPONSLEVEL1) > 0
                        or UpgradeId.ZERGMISSILEWEAPONSLEVEL1 in state.upgrades),
                lambda: state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists,
                UpgradeId.ZERGMISSILEWEAPONSLEVEL1
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
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMELEEWEAPONSLEVEL1) > 0
                        or UpgradeId.ZERGMELEEWEAPONSLEVEL1 in state.upgrades),
                lambda: state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists,
                UpgradeId.ZERGMELEEWEAPONSLEVEL1
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMELEEWEAPONSLEVEL2) > 0
                        or UpgradeId.ZERGGROUNDARMORSLEVEL2 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and UpgradeId.ZERGMELEEWEAPONSLEVEL1 in state.upgrades),
                UpgradeId.ZERGMELEEWEAPONSLEVEL2
            ),
            BOStep(
                0,
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGMELEEWEAPONSLEVEL3) > 0
                        or UpgradeId.ZERGGROUNDARMORSLEVEL3 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and state.own_structures(UnitTypeId.HIVE).ready.exists
                        and UpgradeId.ZERGMELEEWEAPONSLEVEL2 in state.upgrades),
                UpgradeId.ZERGMELEEWEAPONSLEVEL3
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
                180,
                lambda: state.get_unit_count(UnitTypeId.INFESTATIONPIT) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.INFESTATIONPIT) < 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 70),
                UnitTypeId.INFESTATIONPIT
            ),
            BOStep(
                180,
                lambda: (state.get_unit_count(UnitTypeId.SPIRE) >= 1
                        or state.get_unit_count(UnitTypeId.GREATERSPIRE) >= 1),
                lambda: (state.get_unit_count(UnitTypeId.SPIRE) < 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 75),
                UnitTypeId.SPIRE
            ),
            BOStep(
                180,
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

    if UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.CORRUPTOR] = 12 - (state.get_unit_count(UnitTypeId.CORRUPTOR) + state.get_unit_count(UnitTypeId.BROODLORD))

    own_corruptors = state.own_army_units(UnitTypeId.CORRUPTOR)
    if own_corruptors.exists and UnitTypeId.BROODLORD in goal_army_composition:
        goal_army_composition[UnitTypeId.BROODLORD] += own_corruptors.amount

        # ----#
        # ZvP # (only matchup implemented)
        # ----#

    zealots = state.enemy_army_units(UnitTypeId.ZEALOT)
    if zealots.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += zealots.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 4 * zealots.amount
    
    adepts = state.enemy_army_units(UnitTypeId.ADEPT)
    if adepts.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += adepts.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 4 * adepts.amount

    sentries = state.enemy_army_units(UnitTypeId.SENTRY)
    if sentries.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            goal_army_composition[UnitTypeId.HYDRALISK] += sentries.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 4 * sentries.amount

    stalkers = state.enemy_army_units(UnitTypeId.STALKER)
    if stalkers.exists:
        if UnitTypeId.HYDRALISK in goal_army_composition:
            if 2 * state.get_unit_count(UnitTypeId.ZERGLING) < stalkers.amount:
                goal_army_composition[UnitTypeId.ZERGLING] += 4 * stalkers.amount
            else:
                goal_army_composition[UnitTypeId.HYDRALISK] += stalkers.amount
        elif UnitTypeId.ZERGLING in goal_army_composition:
            goal_army_composition[UnitTypeId.ZERGLING] += 4 * stalkers.amount

    immortals = state.enemy_army_units(UnitTypeId.IMMORTAL)
    if immortals.exists:
        if UnitTypeId.ZERGLING in goal_army_composition:
            if state.enemy_army_units(UnitTypeId.COLOSSUS).exists:
                goal_army_composition[UnitTypeId.ZERGLING] += 8 * immortals.amount
            else:
                goal_army_composition[UnitTypeId.ZERGLING] += 16 * immortals.amount

    voidrays = state.enemy_army_units(UnitTypeId.VOIDRAY)
    if voidrays.exists and UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.HYDRALISK] += 3 * voidrays.amount
    if voidrays.exists and not UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.QUEEN] += 2 + 2 * voidrays.amount

    prisms = state.enemy_army_units(UnitTypeId.WARPPRISM)
    if prisms.exists and UnitTypeId.HYDRALISK in goal_army_composition:
        goal_army_composition[UnitTypeId.HYDRALISK] += 2 * prisms.amount

    colossi = state.enemy_army_units(UnitTypeId.COLOSSUS)
    if colossi.exists and UnitTypeId.CORRUPTOR in goal_army_composition:
        goal_army_composition[UnitTypeId.CORRUPTOR] += 3 * colossi.amount
        goal_army_composition[UnitTypeId.ZERGLING] += 4 * colossi.amount
    
    return goal_army_composition, fallback_units, []