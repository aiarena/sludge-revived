from typing import List, Dict, Tuple

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from bot.logic.spending.build_order_v2.build_order_v2 import BOStep, BOAction, BORequest
from bot.services.state_service import StateService
from bot.util.unit_type_utils import get_prerequisite_structures, get_unit_origin_type

#POSSIBLE EFFICIENCY ISSUES:
    #generator may be inefficient (see line 23) compared to just making a function that does a for loop
    #checking truth values for things always true (drone count >= 0)

"""All counts are done with ge or le."""
def convert(build_dict : dict, state : StateService) -> List[BOStep]:
    build_order = [BOStep(0, lambda: False, lambda: True, BOAction.BUILD_DRONES, True)]
    
    #economy (order matters)
    if 'economy' in build_dict:
        for sup_thres, count in build_dict['economy']:
            build_order.extend([
                BOStep(
                    count,
                    lambda: False,
                    lambda x=sup_thres, y=count: (state.resources.supply.used <= x and state.get_unit_count(UnitTypeId.DRONE) >= y),
                    BOAction.BUILD_DRONES, False
                ),
                BOStep(
                    count,
                    lambda: False,
                    lambda x=sup_thres: state.resources.supply.used > x,
                    BOAction.BUILD_DRONES, True
                )
            ])
        
    #supply
    if 'supply' in build_dict:
        for supply, count in build_dict['supply']:
            build_order.append(BOStep(
                supply,
                lambda x=count: state.get_unit_count(UnitTypeId.OVERLORD) >= x,
                lambda x=count: state.get_unit_count(UnitTypeId.OVERLORD) < x,
                UnitTypeId.OVERLORD
            ))

    #bases
    if 'bases' in build_dict:
        for supply, base_count, worker_count in build_dict['bases']:
            build_order.append(BOStep(
                supply,
                lambda x=base_count: state.pending_townhalls() >= x,
                lambda x=base_count, y=worker_count: (state.pending_townhalls() < x and
                        state.get_unit_count(UnitTypeId.DRONE) >= y),
                UnitTypeId.HATCHERY
            ))

    #gas
    if 'gas' in build_dict:
        for supply, count in build_dict['gas']:
            build_order.append(BOStep(
                    supply,
                    lambda x=count: state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) >= x,
                    lambda x=count: state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) < x,
                    UnitTypeId.EXTRACTOR
            ))

    #gas ratio (order matters)
    if 'gas_ratio' in build_dict:
        for worker_count, workers_on_gas in build_dict['gas_ratio']:
            build_order.append(BOStep(
                0,
                lambda: False,
                lambda a=worker_count: state.get_unit_count(UnitTypeId.DRONE) >= a,
                BORequest(BOAction.STABLE_VESPENE, workers_on_gas)
            ))
            
    #extractor max (order matters)
    if 'gas_max' in build_dict:
        for worker_count, extractor_count in build_dict['gas_max']:
            build_order.append(BOStep(
                0,
                lambda: False,
                lambda a=worker_count: state.get_unit_count(UnitTypeId.DRONE) >= a,
                BORequest(BOAction.MAX_EXTRACTOR, extractor_count)
            ))

    #automatic
    if 'automatic' in build_dict:
        count_mapping = {BOAction.BUILD_HATCHERIES : UnitTypeId.HATCHERY,
                        BOAction.BUILD_OVERLORDS : UnitTypeId.OVERLORD,
                        BOAction.BUILD_QUEENS : UnitTypeId.QUEEN,
                        BOAction.STABLE_VESPENE : UnitTypeId.DRONE}
        for setting_id, supply, count, prereq_buildings in build_dict['automatic']:
            build_order.append(BOStep(supply,
            lambda: False,
            lambda a=count_mapping[setting_id], b=count, c=prereq_buildings: (state.get_unit_count(a) >= b and
            prereq_building_bool(c, state)),
            setting_id,
            True))

    #buildings
    if 'buildings' in build_dict:
        for unit_id, supply, worker_count, prereq_buildings, amount in build_dict['buildings']:
            build_order.append(BOStep(
                supply,
                lambda x=unit_id, y=amount: state.get_unit_count(x) >= y,
                lambda a=unit_id, b=amount, c=prereq_buildings, d=worker_count: (state.get_unit_count(a) < b
                and prereq_building_bool(c, state)
                and state.get_unit_count(UnitTypeId.DRONE) >= d),
                unit_id
            ))

    #units (order matters)
    if 'units' in build_dict:
        for unit_id, supply, unit_count, prereq_buildings in build_dict['units']:
            build_order.append(BOStep(
                    supply,
                    lambda a=unit_id, b=unit_count: state.get_unit_count(a) >= b,
                    lambda a=get_prerequisite_structures(unit_id), b=prereq_buildings: (prereq_building_bool(a, state) and prereq_building_bool(b, state)),
                    unit_id
            ))

    #upgrades
    if 'upgrades' in build_dict:
        for upgrade_id, supply, prereq_upgrades, prereq_buildings, worker_count in build_dict['upgrades']:
            build_order.extend([BOStep(
                supply,
                lambda a=upgrade_id: (state.already_pending_upgrade(a) > 0
                            or a in state.upgrades),
                lambda a=prereq_buildings, b=worker_count, c=prereq_upgrades, d=[get_unit_origin_type(upgrade_id)]: (prereq_building_bool(a, state)
                and state.get_unit_count(UnitTypeId.DRONE) >= b
                and prereq_upgrade_bool(c, state)
                and prereq_building_bool(d, state)),
                upgrade_id
            ),
            BOStep( #does not take into consideration prereq upgrades (e.g. bot will request 200/200 when hydra den starts, even though only get 1 upgrade at a time)
                supply,
                lambda: False,
                lambda a=get_unit_origin_type(upgrade_id): (state.already_pending(a) and not state.own_structures(a).ready.exists),
                BORequest(BOAction.REQUEST_UPGRADE, upgrade_id)
            )])

    return build_order

#TODO for prereq buildings, do .ready.exists unless its an extractor, in which case just check how many exist
#for lair, count both lair and hive
#for spire, count both spire and greater spire
#remember that tech_alias property for unittypeids exists
def prereq_building_bool(buildings : Tuple[UnitTypeId], state : StateService) -> bool:
    for building in buildings:
        if building in {UnitTypeId.EXTRACTOR,UnitTypeId.EXTRACTORRICH}:
            if state.get_unit_count(UnitTypeId.EXTRACTOR)+state.get_unit_count(UnitTypeId.EXTRACTORRICH) < 1:
                return False
        else:
            if not state.own_structures(building).ready.exists:
                return False
    return True

def prereq_upgrade_bool(upgrades : Tuple[UpgradeId], state : StateService) -> bool:
    for upgrade in upgrades:
        if upgrade not in state.upgrades:
            return False
    return True