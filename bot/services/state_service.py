from typing import List, Set, Union
import math
import time
import numpy as np

from sc2 import BotAI, Race
from sc2.unit import Unit
from sc2.units import Units
from sc2 import UnitTypeId, AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2, Rect, Point3

import bot.injector as injector
from ..model.resources import Resources, Supply
from bot.model.scouting_information import ScoutingInformation
from bot.services.unit_type_service import UnitTypeService
from bot.util.unit_utils import group_army
from .state.unit_memory import UnitObservation, UnitMemory
from bot.services.debug_service import DebugService
from bot.util.reg_polygon import n_sided_polygon
from bot.logic.spending.spending_interface import SpendingInterface
from bot.services.unit_group_service import UnitGroup
from bot.util.unit_type_utils import zerg_structures


class StateService():
    def __init__(self, *args, **kwargs):
        self._bot: BotAI = injector.inject(BotAI)
        self.unit_type: UnitTypeService = injector.inject(UnitTypeService)
        self.debug: DebugService = injector.inject(DebugService)
        self.unit_memory = UnitMemory(self._bot)
        self.already_pending_upgrade = self._bot.already_pending_upgrade
        self.army_composition = None

        self.game_info = GameInfo()

        self.resources = Resources()

        self.previous_iter_own_units: Units = Units([], self._bot._game_data)

        self.own_units: Units = Units([], self._bot._game_data)
        self.enemy_units: Units = Units([], self._bot._game_data)
        self.own_army_units: Units = Units([], self._bot._game_data)
        self.enemy_army_units: Units = Units([], self._bot._game_data)

        self.build_queue = []
        self.enemy_tech: Set[UnitTypeId] = set()
        self.time_hit_last_worker_threshold: float = 0
        self.hit_worker_threshold: bool = False

        self.mineral_saturation = 0
        self.drone_count = 0

        self.injected_hatches: dict[str, str] = {}

        #self.enemy_army_groups: List[Units] = []

        self.scouting_information: Set[ScoutingInformation] = set()

        self.overlord_spots: List[Point2] = []

        self.mode = 'defend'

    def on_first_iteration(self):
        import bot.logic.spending.build_order_v2.bo_interpreter as bo_interpreter
        self.bo_interpreter = bo_interpreter
        from .state.army_composition_manager import ArmyCompositionManager
        self.army_composition: ArmyCompositionManager = ArmyCompositionManager()
        from .state.enemy_prioritizer import EnemyPrioritizer
        self.enemy_prioritizer: EnemyPrioritizer = EnemyPrioritizer()
        from bot.services.state.build_manager import BuildManager
        self.build_manager: BuildManager = BuildManager()

        self.game_info.start_location = self._bot.start_location
        self.main_minerals = self.get_mineral_fields_for_expansion(self.game_info.start_location)
        # TODO: use one function for calculating any base #
        self.own_natural_position: Point2 = self.calculate_own_natural()
        self.enemy_natural_position: Point2 = self.calculate_enemy_natural()
        self.enemy_third_position: Point2 = self.calculate_enemy_third()
        self.unit_type.on_first_iteration()

        p: Rect = self._bot.game_info.playable_area
        h = p.height
        w = p.width
        self.map_diagonal_len = math.sqrt(h ** 2 + w ** 2)

        polygon = n_sided_polygon(16, 21, 2)
        for vertex in polygon:
            pos = vertex + self.own_natural_position
            playable_area: Rect = self._bot.game_info.playable_area
            offset = 0
            if (
                pos.x > playable_area.x + offset and pos.x < playable_area.x + playable_area.width - offset
                and pos.y > playable_area.y + offset and pos.y < playable_area.y + playable_area.height - offset
            ):
                self.overlord_spots.append(pos)

        self.spending: SpendingInterface = injector.inject(SpendingInterface)

        build, comp = self.build_manager.first_iteration()

        self.change_build(build, comp)
        
        self.update()
        
    def update(self):
        # slow down time for debugging
        #if self.getTimeInSeconds() > 4 * 60:
        #    self._bot._client.game_step = 2
        #    time.sleep(0.05)

        self.placement_requests = []

        self.resources.minerals = self._bot.minerals
        self.resources.vespene = self._bot.vespene
        self.resources.supply.used = self._bot.supply_used
        self.resources.supply.cap = self._bot.supply_cap
        if self._bot.units(UnitTypeId.LARVA).exists:
            self.resources.larva = self._bot.units(UnitTypeId.LARVA).amount
        self.upgrades: Set[UpgradeId] = self._bot.state.upgrades

        self.own_units = self._bot.units.exclude_type(UnitTypeId.BROODLING)
        self.own_units_that_can_attack = self._bot.units.filter(lambda u: u.can_attack or u.type_id in {UnitTypeId.BANELING})
        self.own_structures = self._bot.units.structure
        self.own_townhalls: Units = self.own_structures.of_type({UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE})
        # TODO: remember enemy units for certain amount of time and structures permanently
        self.unit_memory.iterate(self.getTimeInSeconds())
        self.enemy_units = self.unit_memory.observed_enemy_units
        # self.debug.text_screen_auto(f'Currently observed enemy units: {self.enemy_units.amount}', 10, 0)
        cannons = self.enemy_units(UnitTypeId.PHOTONCANNON)
        ctags = set()
        for c in cannons:
            ctags.add(c.tag)
        # self.debug.text_screen_auto(f'Cannon tags amount: {len(ctags)}', 11, 0)
        # self.debug.text_screen_auto(f'Current build idx: {self.build_manager.build_idx}', 12, 0)
        #self.debug.text_screen_auto(f'bool: {self.hit_worker_threshold}, Current time since last hit worker limit: {self.get_time_since_hit_last_worker_threshold()}', 13, 0)
        self.enemy_units_that_can_attack = self.enemy_units.filter(lambda u: u.can_attack)
        self.enemy_structures: Units = self.unit_memory.observed_enemy_units.structure
        self.enemy_townhalls = self.enemy_structures.of_type({UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE, UnitTypeId.NEXUS, UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS})

        self.own_army_units = self.own_units_that_can_attack.not_structure.exclude_type({UnitTypeId.DRONE, UnitTypeId.QUEEN, UnitTypeId.OVERLORD, UnitTypeId.CHANGELING, UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINE, UnitTypeId.CHANGELINGMARINESHIELD, UnitTypeId.CHANGELINGZEALOT, UnitTypeId.CHANGELINGZERGLING, UnitTypeId.CHANGELINGZERGLINGWINGS})
        # TODO: queens should be considered army units if on the opposite side of the map
        self.enemy_medivacs = self.enemy_units(UnitTypeId.MEDIVAC)
        self.enemy_prisms = self.enemy_units(UnitTypeId.WARPPRISM)
        self.enemy_mines = self.enemy_units(UnitTypeId.WIDOWMINE)
        self.enemy_ravens = self.enemy_units(UnitTypeId.RAVEN)
        self.enemy_banelings = self.enemy_units(UnitTypeId.BANELING)
        self.enemy_army_units = self.enemy_units_that_can_attack.not_structure.filter(lambda u: not (u.type_id == UnitTypeId.DRONE or u.type_id == UnitTypeId.PROBE or u.type_id == UnitTypeId.SCV or u.type_id == UnitTypeId.QUEEN))
        self.enemy_army_units.extend(self.enemy_medivacs)
        self.enemy_army_units.extend(self.enemy_prisms)
        self.enemy_army_units.extend(self.enemy_mines)
        self.enemy_army_units.extend(self.enemy_ravens)
        self.enemy_army_units.extend(self.enemy_banelings)

        self.enemy_army_with_structures = self.enemy_army_units
        self.enemy_army_with_structures.extend(self.enemy_structures({UnitTypeId.BUNKER, UnitTypeId.PHOTONCANNON, UnitTypeId.SHIELDBATTERY, UnitTypeId.SPINECRAWLER, UnitTypeId.PLANETARYFORTRESS}).ready)

        self.pending_army_value = self.calculate_pending_army_value()
        self.own_army_value = self.unit_type.calculate_combat_value(self.own_army_units)
        self.total_army_value = self.pending_army_value + self.own_army_value
        self.own_ready_army_value = self.unit_type.calculate_combat_value(self.own_army_units.ready)
        self.enemy_army_value = self.unit_type.calculate_combat_value(self.enemy_army_units)
        self.total_enemy_value = sum(self.unit_type.get_resource_value(self.enemy_units))

        self.enemy_groups: PriorityQueue = self.enemy_prioritizer.group_and_prioritize_enemies(self.enemy_units)

        '''
        self.debug.text_screen_auto(f'Own army: {self.own_army_value}', 0)
        self.debug.text_screen_auto(f'Enemy army: {self.enemy_army_value}', 1)

        self.debug.text_screen_auto(f'Total army: {self.total_army_value}', 0, 1)
        '''

        self.mineral_saturation = self._calculate_mineral_saturation()
        self.drone_count = self.get_unit_count(UnitTypeId.DRONE)

        # ---------------------- #
        # ENEMY ARMY UNIT GROUPS #
        # ---------------------- #

        #self.enemy_army_groups = group_army(self.enemy_army_units)

        # ----------------------------#
        # UPDATE SCOUTING INFORMATION #
        # ----------------------------#
        self.scouting_information = set()
        if UnitTypeId.SPAWNINGPOOL in self.enemy_units:
            self.scouting_information.add(ScoutingInformation.OPPONENT_HAS_POOL)
        
        # THREAT LEVEL
        enemy_army_value = self.enemy_army_value - self.unit_type.calculate_combat_value(self.enemy_army_units.structure)

        mult = 1
        if enemy_army_value < 200:
            mult = 0.25
        elif enemy_army_value < 400:
            mult = 0.5
        elif enemy_army_value < 2000:
            mult = 0.75

        # if over 30% of enemy army is zerglings
        if self._bot.enemy_race == Race.Zerg and self.enemy_army_units.amount > 0 and self.enemy_army_units(UnitTypeId.ZERGLING).amount / self.enemy_army_units.amount > 0.3:
            mult = 1

        if self.total_army_value < mult * enemy_army_value:
            self.scouting_information.add(ScoutingInformation.THREAT_LEVEL_1)


        enemy_bases_outside_nat_and_main = self.enemy_townhalls.filter(lambda u: u.position.distance_to_closest([self.enemy_natural_position, self._bot.enemy_start_locations[0]]) > 10)
        if (enemy_bases_outside_nat_and_main.exists and enemy_bases_outside_nat_and_main.amount > 1):
            self.scouting_information.add(ScoutingInformation.ENEMY_FOUR_BASE)
        elif enemy_bases_outside_nat_and_main.exists and enemy_bases_outside_nat_and_main.amount > 0:
            self.scouting_information.add(ScoutingInformation.ENEMY_THREE_BASE)
        elif self.enemy_is_two_base():
            self.scouting_information.add(ScoutingInformation.ENEMY_TWO_BASE)
        else:
            self.scouting_information.add(ScoutingInformation.ENEMY_ONE_BASE)

        # for idx, info in enumerate(self.scouting_information):
        #     self.debug.text_screen_auto(f'{info.name}', 10 + idx, 2)
        
        enemy_moved_out = self.has_enemy_moved_out(0.5)
        if enemy_moved_out:
            self.scouting_information.add(ScoutingInformation.ENEMY_MOVED_OUT)
        if (self._bot.enemy_race == Race.Terran
            and self.enemy_townhalls.amount < 2
            and self.own_townhalls.amount < 3
            and self.drone_count < 30
            and 2 * self.own_army_value < enemy_army_value
            and enemy_army_value > 150):
            self.scouting_information.add(ScoutingInformation.TERRAN_1BASE_BIO)

        tech_unit_mapping = {
            UnitTypeId.DARKSHRINE : (UnitTypeId.DARKTEMPLAR,),
            UnitTypeId.STARPORTTECHLAB : (UnitTypeId.BANSHEE, UnitTypeId.RAVEN, UnitTypeId.BATTLECRUISER),
            UnitTypeId.STARGATE : (UnitTypeId.VOIDRAY, UnitTypeId.ORACLE, UnitTypeId.PHOENIX, UnitTypeId.CARRIER, UnitTypeId.TEMPEST)
        }
        #if see the enemy tech structure or see its associated units, add the structure to self.enemy_tech
        for structure, associated_units in tech_unit_mapping.items():
            if not structure in self.enemy_tech and (self.enemy_structures(structure).exists or any(self.enemy_units(unit_id).exists for unit_id in associated_units)):
                self.enemy_tech.add(structure)

        if (UnitTypeId.DARKSHRINE in self.enemy_tech or
        UnitTypeId.STARPORTTECHLAB in self.enemy_tech or
        self._bot.enemy_race == Race.Protoss and ScoutingInformation.ENEMY_ONE_BASE in self.scouting_information and self.getTimeInSeconds() >= 240):
            self.scouting_information.add(ScoutingInformation.THREAT_CLOAK)
        
        if UnitTypeId.STARPORTTECHLAB in self.enemy_tech:
            self.scouting_information.add(ScoutingInformation.STARPORT_TECHLAB)
        
        if UnitTypeId.STARGATE in self.enemy_tech:
            self.scouting_information.add(ScoutingInformation.STARGATE)
        
        condition = 0
        if self.enemy_units(UnitTypeId.BUNKER).exists:
            condition += self.enemy_units(UnitTypeId.BUNKER).amount
        try:
            condition += self.enemy_units(UnitTypeId.SIEGETANKSIEGED).closer_than(15, self.enemy_natural_position).amount
        except:
            pass
        if condition > 2:
            self.scouting_information.add(ScoutingInformation.HEAVY_DEFENSE)
        else:
            if ScoutingInformation.HEAVY_DEFENSE in self.scouting_information:
                self.scouting_information.remove(ScoutingInformation.HEAVY_DEFENSE)
        
        self.army_composition.update_army_compositions()
        
        # set current mode, TODO this should be done somewhere else
        dont_attack_nat = False
        tanks = self.enemy_army_units(UnitTypeId.SIEGETANKSIEGED)
        if tanks.exists and tanks.closer_than(10, self.enemy_natural_position).exists and self.resources.supply.used < 180:
            dont_attack_nat = True
        if self.own_army_value > (2 - self.resources.supply.used / 150) * self.enemy_army_value and ((self.enemy_townhalls.exists and self.enemy_townhalls.amount > 2) or not dont_attack_nat):
            self.update_mode('attack')
        else:
            self.update_mode('defend')


        build: ('build', 'comp') or None = self.build_manager.on_step()
        if build:
            self.change_build(*build)

        total_idx = 0
        for idx, u in enumerate(self.army_composition.goal_army_composition):
            # self.debug.text_screen_auto(f'{u.name}', total_idx, 2, (0, 255, 0))
            total_idx += 1
        for idx, u in enumerate(self.army_composition.fallback_units):
            # self.debug.text_screen_auto(f'{u.name}', total_idx, 2, (128, 184, 128))
            total_idx += 1
        for idx, u in enumerate(self.army_composition.desperation_units):
            # self.debug.text_screen_auto(f'{u.name}', total_idx, 2, (128, 128, 128))
            total_idx += 1
    
    def already_pending(self, unit_type: Union[UpgradeId, UnitTypeId], all_units: bool = True) -> int:
        """
        Returns a number of buildings or units already in progress, or if a
        worker is en route to build it. This also includes queued orders for
        workers and build queues of buildings.

        If all_units==True, then build queues of other units (such as Carriers
        (Interceptors) or Oracles (Stasis Ward)) are also included.
        """
        self = self._bot

        # TODO / FIXME: SCV building a structure might be counted as two units

        if isinstance(unit_type, UpgradeId):
            return self.already_pending_upgrade(unit_type)

        ability = self._game_data.units[unit_type.value].creation_ability

        amount = len(self.units(unit_type).not_ready)

        if all_units:
            amount += sum([o.ability == ability for u in self.units for o in u.orders])
        else:
            amount += sum([o.ability == ability for w in self.workers for o in w.orders])
            amount += sum([egg.orders[0].ability == ability for egg in self.units(UnitTypeId.EGG)])

        return amount
    
    def queen_already_pending(self) -> int:
        counter = 0
        for hatch in self.own_units(UnitTypeId.HATCHERY):
            for order in hatch.orders:
                if order.ability.id == AbilityId.TRAINQUEEN_QUEEN:
                    counter += 1
        return counter

    def _calculate_mineral_saturation(self):
        res = 0
        for own_expansion in self._bot.owned_expansions:
            res += self._bot.owned_expansions[own_expansion].assigned_harvesters
        return res

    def get_unit_count(self, type_id: UnitTypeId) -> int:
        if self.own_units(type_id).exists:
            if type_id == UnitTypeId.ZERGLING:
                return self.own_units(type_id).amount + (self.already_pending(type_id) * 2)
            if type_id in {UnitTypeId.DRONE, UnitTypeId.PROBE, UnitTypeId.SCV}:
                #calculate by hand because .amount doesn't account for workers in gas structures
                worker_amount = sum(townhall.assigned_harvesters for townhall in self.own_townhalls) +\
                     sum(ex.assigned_harvesters for ex in self.own_structures.of_type({UnitTypeId.EXTRACTOR,UnitTypeId.EXTRACTORRICH})) +\
                     self.own_units(type_id).filter(lambda u: u.is_idle or u.is_attacking or u.is_moving).amount +\
                    self.already_pending(type_id)
                return worker_amount

            return self.own_units(type_id).amount + self.already_pending(type_id)
        else:
            return self.already_pending(type_id)
    
    def pending_townhalls(self) -> int:
        townhall_ids = {UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE}
        if self.own_units(townhall_ids).exists:
            return self.own_units(townhall_ids).amount + sum(self.already_pending(townhall_id) for townhall_id in townhall_ids)
        else:
            return 0

    def get_own_geysers(self) -> Units:
        geysers: Units = Units([], self._bot._game_data)
        for townhall in self.own_townhalls.sorted_by_distance_to(self.game_info.start_location):
            temp = self._bot.state.vespene_geyser.closer_than(10, townhall)
            geysers.extend(temp)
        return geysers
    
    def point_closer_than_n_to_units(self, p: Point2, n: int, units: Units):
        for u in units:
            if p.is_closer_than(n, u.position):
                return True
        return False

    def get_mineral_fields_for_expansion(self, expansion_position: Point2) -> Units:
        exp = self._bot.state.mineral_field.closer_than(10, expansion_position)
        if exp.exists:
            return exp
        else:
            return Units([], self._bot._game_data)
    
    def getTimeInSeconds(self) -> float:
        # returns real time if game is played on "faster"
        return self._bot.state.game_loop * 0.725 * (1/16)
    
    def calculate_own_natural(self) -> Point2:
        best = None
        distance = math.inf
        for expansion in self._bot.expansion_locations:
            temp = expansion.distance2_to(self._bot.start_location)
            if temp < distance and temp > 0:
                distance = temp
                best = expansion
        return best

    def calculate_enemy_natural(self) -> Point2:
        enemy_base = self._bot.enemy_start_locations[0]
        best = None
        distance = math.inf
        for expansion in self._bot.expansion_locations:
            temp = expansion.distance2_to(enemy_base)
            if temp < distance and temp > 0:
                distance = temp
                best = expansion
        return best

    def calculate_enemy_third(self) -> Point2:
        enemy_base = self._bot.enemy_start_locations[0]
        best = None
        distance = math.inf
        for expansion in self._bot.expansion_locations:
            temp = expansion.distance2_to(enemy_base)
            if temp < distance and temp > 0 and expansion.distance_to(self.enemy_natural_position) > 1:
                distance = temp
                best = expansion
        return best

    def has_enemy_moved_out(self, mult: int) -> bool:
        positions: List[Point2] = [
            self._bot.enemy_start_locations[0],
            self.enemy_natural_position
        ]
        for townhall in self.enemy_townhalls:
            if not townhall.position == self._bot.enemy_start_locations[0] or townhall.position == self.enemy_natural_position:
                positions.append(townhall.position)
        threats = self.enemy_groups_further_than_plist(30, positions)
        value = self.total_value_of_groups(threats)
        return value > mult * (self.total_army_value + (self.get_unit_count(UnitTypeId.QUEEN) * 150))

    def can_afford_minerals(self, type_id: UnitTypeId, available_minerals):
        unitData: UnitTypeData = self._bot._game_data.units[type_id.value]
        return unitData.cost.minerals <= available_minerals

    def calculate_pending_army_value(self):
        return (
            self.already_pending(UnitTypeId.ZERGLING, all_units=False) * 50 +
            self.already_pending(UnitTypeId.ROACH, all_units=False) * 100 +
            self.already_pending(UnitTypeId.HYDRALISK, all_units=False) * 150
        )

    _valid_modes = {'attack', 'defend'}
    def update_mode(self, val : str):
        '''Modes are used in unit management and group tactics for decision making purposes.'''
        if val in self._valid_modes:
            self.mode = val

    def get_dist_group_to_close_townhall(self, group : UnitGroup) -> float:
        mining_bases = self.own_townhalls.filter(lambda u: u.assigned_harvesters > 0)
        if mining_bases:
            return group.location.distance_to_closest(mining_bases)
        elif self.own_townhalls.exists:
            return group.location.distance_to_closest(self.own_townhalls)
        else:
            return 0.00001

    def enemy_groups_further_than_plist(self, n, positions: List[Point2]) -> List[UnitGroup]:
        output = []
        for group in self.enemy_groups:
            outside = True
            for position in positions:
                if group.location.distance_to(position) < n:
                    outside = False
            if outside:
                output.append(group)
        return output

    def total_value_of_groups(self, groups: UnitGroup) -> int:
        total = 0
        for group in groups:
            total += group.value
        return total

    def change_build(self, build, comp) -> None:
        '''Changes the current build and army composition to the given ones.'''
        converted_build = self.bo_interpreter.convert(build, self)
        self.spending.setBuild(converted_build)
        self.army_composition.set_all_attributes(*comp)

    def request_placement(self, type_id: UnitTypeId):
        self.placement_requests.append(type_id)

    def update_worker_threshold(self, hit: bool) -> None:
        '''Tells the state service whether or not the worker threshold (given by BOAction.WORKER_LIMIT) has been hit.'''
        if hit and not self.hit_worker_threshold:
            self.hit_worker_threshold = True
            self.time_hit_last_worker_threshold = self.getTimeInSeconds()

        if not hit and self.hit_worker_threshold:
            self.hit_worker_threshold = False
    
    def get_time_since_hit_last_worker_threshold(self) -> float:
        '''Returns time since hit last worker threshold (seconds).'''
        return self.getTimeInSeconds() - self.time_hit_last_worker_threshold

    _defensive_structures = {
        UnitTypeId.BUNKER, UnitTypeId.MISSILETURRET,
        UnitTypeId.SPINECRAWLER, UnitTypeId.SPORECRAWLER,
        UnitTypeId.PHOTONCANNON, UnitTypeId.SHIELDBATTERY
    }

    # deprecated:
    def enemy_is_one_base(self) -> bool:
        '''Returns whether or not the enemy is one-base. Assumes the enemy is two-base in the early game.'''
        condition = 0
        if self.getTimeInSeconds() >= 150 and not self.enemy_townhalls.further_than(10, self._bot.enemy_start_locations[0]).exists:
            condition += 1
            if any(structure.distance_to(self.enemy_natural_position) <= 15 for structure in self.enemy_structures(self._defensive_structures)):
                condition -= 1
            if self.enemy_army_value >= 2 * self.own_army_value and self.enemy_army_value >= 250:
                condition += 1
            return condition >= 2
        else:
            return False

    def enemy_is_two_base(self) -> bool:
        base_outside_main_exists = self.enemy_townhalls.further_than(10, self._bot.enemy_start_locations[0]).exists
        defensive_structures = self.enemy_structures(self._defensive_structures)
        defensive_structures_exist = defensive_structures.exists
        return base_outside_main_exists or defensive_structures_exist

class GameInfo:
    start_location = Point2((0,0))
