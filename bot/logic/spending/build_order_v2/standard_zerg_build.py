from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from bot.logic.spending.build_order_v2.build_order_v2 import BOStep, BOAction
from bot.services.state_service import StateService

def get_build(state : StateService):
    return [
             BOStep(
                0,
                lambda: False,
                lambda: True,
                BOAction.BUILD_DRONES, True
            ),
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
                29,
                lambda: state.get_unit_count(UnitTypeId.BANELINGNEST) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.BANELING) <= 0
                        and state.get_unit_count(UnitTypeId.EXTRACTOR) >= 1),
                UnitTypeId.BANELINGNEST
            ),
            BOStep(
                29,
                lambda: state.get_unit_count(UnitTypeId.BANELING) >= 2,
                lambda: state.own_structures(UnitTypeId.BANELINGNEST).ready.exists,
                UnitTypeId.BANELING
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
                lambda: state.get_unit_count(UnitTypeId.ROACHWARREN) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.ROACHWARREN) < 1
                        and state.get_unit_count(UnitTypeId.DRONE) >= 38),
                UnitTypeId.ROACHWARREN
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
                lambda: (state.already_pending_upgrade(UpgradeId.GLIALRECONSTITUTION) > 0
                        or UpgradeId.GLIALRECONSTITUTION in state.upgrades),
                lambda: state.own_structures(UnitTypeId.LAIR).exists,
                UpgradeId.GLIALRECONSTITUTION
            ),
            BOStep(
                52,
                lambda: state.get_unit_count(UnitTypeId.HYDRALISKDEN) >= 1,
                lambda: (state.get_unit_count(UnitTypeId.HYDRALISKDEN) < 1
                        and state.get_unit_count(UnitTypeId.LAIR) > 0
                        and state.get_unit_count(UnitTypeId.DRONE) >= 52),
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
                lambda: (state.already_pending_upgrade(UpgradeId.ZERGGROUNDARMORSLEVEL3) > 0
                        or UpgradeId.ZERGGROUNDARMORSLEVEL3 in state.upgrades),
                lambda: (state.own_structures(UnitTypeId.EVOLUTIONCHAMBER).ready.exists
                        and state.own_structures(UnitTypeId.HIVE).ready.exists
                        and UpgradeId.ZERGGROUNDARMORSLEVEL2 in state.upgrades),
                UpgradeId.ZERGGROUNDARMORSLEVEL3
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
                60,
                lambda: False,
                lambda: state.resources.supply.used <= 100 and state.get_unit_count(UnitTypeId.DRONE) >= 60,
                BOAction.BUILD_DRONES, False
            ),
            BOStep(
                100,
                lambda: False,
                lambda: state.resources.supply.used >= 101,
                BOAction.BUILD_DRONES, True
            ),
            BOStep(
                100,
                lambda: False,
                lambda: state.resources.supply.used <= 150 and state.get_unit_count(UnitTypeId.DRONE) >= 70,
                BOAction.BUILD_DRONES, False
            ),
            BOStep(
                100,
                lambda: False,
                lambda: state.resources.supply.used >= 151,
                BOAction.BUILD_DRONES, True
            ),
            BOStep(
                100,
                lambda: False,
                lambda: state.get_unit_count(UnitTypeId.DRONE) >= 80,
                BOAction.BUILD_DRONES, False
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