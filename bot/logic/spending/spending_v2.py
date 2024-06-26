from typing import Dict

from sc2 import UnitTypeId, Race, BotAI

from bot.hooks import hookable
from bot.logic.spending.spending_interface import SpendingInterface
from bot.util.priority_queue import PriorityQueue
from bot.services.state_service import StateService
from bot.model.unit_type_abstraction import UnitTypeAbstraction
from bot.model.scouting_information import ScoutingInformation
import bot.injector as injector
from bot.logic.spending.build_order_v2.build_order_v2 import BORepository, BORunner, BOAction
from bot.services.eco_balance_service import EcoBalanceService

@hookable
class Spendingv2(SpendingInterface):
    def __init__(self):
        self.state: StateService = injector.inject(StateService)
        self.eco_balance: EcoBalanceService = injector.inject(EcoBalanceService)

        self.bo_repository = BORepository()
        self.bot: BotAI = injector.inject(BotAI)
        self.bo_runner = BORunner(self.bo_repository.get_standard_build_order()) #not used; state_service first iteration handles bo_runner
        self.base_to_worker_limit = None

        self.base_responses = {}

    def setBuild(self, build : list) -> None:
        self.bo_runner = BORunner(build)

    def on_init(self) -> None:
        self.base_responses = {
            ScoutingInformation.OPPONENT_HAS_POOL: self._build_pool,
            ScoutingInformation.THREAT_LEVEL_1: self._build_army,
            ScoutingInformation.TERRAN_1BASE_BIO: self._build_one_spine,
            ScoutingInformation.ENEMY_MOVED_OUT: self._build_army,
            ScoutingInformation.STARPORT_TECHLAB: self._spore_hydra,
            ScoutingInformation.HEAVY_DEFENSE: self._hydra,

            ScoutingInformation.THREAT_CLOAK: self._build_detection,
            ScoutingInformation.STARGATE: self._stargate
        }
        self.set_base_to_worker_limit()

    def set_base_to_worker_limit(self) -> None:
        '''Meant to be run on first iteration or after, since it requires the race of the opponent.
        Can be run multiple times; useful for future implementation of identifying enemy race if they're random.'''
        if self.state._bot.enemy_race == Race.Terran:
            self.base_to_worker_limit = {
                1: 28,
                2: 54,
                3: 70,
                4: 80
            }
        elif self.state._bot.enemy_race == Race.Zerg:
            self.base_to_worker_limit = {
                1: 24,
                2: 44,
                3: 66,
                4: 80
            }
        elif self.state._bot.enemy_race == Race.Protoss or self.state._bot.enemy_race == Race.Random:
            self.base_to_worker_limit = {
                1: 28,
                2: 41,
                3: 66,
                4: 80
            }
        self.base_responses.update(
            {
            ScoutingInformation.ENEMY_ONE_BASE: self._generate_limit_worker_count(1),
            ScoutingInformation.ENEMY_TWO_BASE: self._generate_limit_worker_count(2),
            ScoutingInformation.ENEMY_THREE_BASE: self._generate_limit_worker_count(3),
            ScoutingInformation.ENEMY_FOUR_BASE: self._generate_limit_worker_count(4),
            })

    def get_current_priorities(self) -> PriorityQueue:
        priorities = PriorityQueue()

        # Build order
        # priority magnitude 1000 for hardcoded build
        # priority magnitude 10-100 for generic stuff
        priorities.extend(self.bo_runner.on_step())

        ex = self.eco_balance.req_extractors
        if ex > self.state.get_unit_count(UnitTypeId.EXTRACTOR)+self.state.get_unit_count(UnitTypeId.EXTRACTORRICH):
            priorities.enqueue(UnitTypeId.EXTRACTOR, 1001)

        # Scouting responses
        # priority magnitude 10 000
        responses: Dict[ScoutingInformation, function] = self._getResponses()
        # apply responses...
        for scouting_info in responses.keys():
            if scouting_info in self.state.scouting_information:
                responses[scouting_info](priorities)
        
        return priorities

    def _getResponses(self) -> Dict:
        responses = self.base_responses
        if self.state.get_unit_count(UnitTypeId.SPAWNINGPOOL) > 0:
            responses[ScoutingInformation.OPPONENT_HAS_POOL] = self._noAction
        if self.state.own_townhalls.exists and self.state.own_townhalls.ready.amount < 3 and self.state._bot.enemy_race == Race.Protoss:
            responses[ScoutingInformation.ENEMY_THREE_BASE] = self._build_army
        return responses

    # Scouting responses. Must take priorities as argument
    # mutates priorities
    def _build_pool(self, priorities: PriorityQueue):
        pass

    def _build_army(self, priorities: PriorityQueue):
        if self.state.own_army_value < 2 * self.state.enemy_army_value:
            priorities.enqueue(UnitTypeAbstraction.ARMY, 10000)

    def _build_one_spine(self, priorities: PriorityQueue):
        if self.state.get_unit_count(UnitTypeId.SPINECRAWLER) < 1:
            priorities.enqueue(UnitTypeId.SPINECRAWLER, 10001)

    def _build_detection(self, priorities: PriorityQueue):
        # if we are dealing with a 1 base protoss, we only need 1 spore
        if self.state.pending_townhalls() <= 2 and ScoutingInformation.ENEMY_ONE_BASE in self.state.scouting_information:
            if self.state.get_unit_count(UnitTypeId.SPORECRAWLER) < 1:
                priorities.enqueue(UnitTypeId.SPORECRAWLER, 10005)
            return

        if self.state.get_unit_count(UnitTypeId.LAIR) < 1 and self.state.get_unit_count(UnitTypeId.HIVE) < 1:
            priorities.enqueue(UnitTypeId.LAIR, 10005)
        if ((self.state.get_unit_count(UnitTypeId.LAIR) >= 1 or self.state.get_unit_count(UnitTypeId.HIVE) >= 1)
            and self.state.get_unit_count(UnitTypeId.OVERSEER) < 1):
            priorities.enqueue(UnitTypeId.OVERSEER, 10005)
        if self.state.get_unit_count(UnitTypeId.SPORECRAWLER) < self.state.own_townhalls.ready.amount:
            priorities.enqueue(UnitTypeId.SPORECRAWLER, 10005)
    
    #TODO check if this scouting response is necessary anymore (voidrays should be automatically handled by army comp manager)
    def _stargate(self, priorities: PriorityQueue):
        if self.state.get_unit_count(UnitTypeId.LAIR) < 1 and self.state.get_unit_count(UnitTypeId.HIVE) < 1:
            priorities.enqueue(UnitTypeId.LAIR, 10005)
        if ((self.state.get_unit_count(UnitTypeId.LAIR) >= 1 or self.state.get_unit_count(UnitTypeId.HIVE) >= 1)
            and self.state.get_unit_count(UnitTypeId.HYDRALISKDEN) < 1):
            priorities.enqueue(UnitTypeId.HYDRALISKDEN, 10005)
        if (ScoutingInformation.ENEMY_MOVED_OUT in self.state.scouting_information
            and self.state.get_unit_count(UnitTypeId.HYDRALISKDEN) < 1
            and self.state.get_unit_count(UnitTypeId.QUEEN) < 8):
            priorities.enqueue(UnitTypeId.QUEEN, 10002)

    def _noAction(self, priorities: PriorityQueue):
        pass
    
    def _generate_limit_worker_count(self, base_count):
        base_to_min_army = {
            1: 0,
            2: 0,
            3: 1000,
            4: 2000
        }
        def limit_worker_count(priorities: PriorityQueue):
            base_worker_limit = self.base_to_worker_limit[base_count]
            self.state.update_worker_threshold(True) if self.state.drone_count >= base_worker_limit else self.state.update_worker_threshold(False)

            time_since_last_threshold = self.state.get_time_since_hit_last_worker_threshold()
            if time_since_last_threshold >= 75:
                multiplier = 1.2
                multiplier += 0.15*((time_since_last_threshold - 60) // 45)
            else:
                multiplier = 1

            worker_limit = base_worker_limit*multiplier
            if (self.state.drone_count >= worker_limit or self.state.own_army_value < base_to_min_army[base_count]):
                self.bo_runner.set_boaction(BOAction.WORKER_LIMIT, True)
            else:
                self.bo_runner.set_boaction(BOAction.WORKER_LIMIT, False)
        return limit_worker_count
    
    def _spore_hydra(self, priorities: PriorityQueue):
        if self.state.get_unit_count(UnitTypeId.SPORECRAWLER) < self.state.own_townhalls.ready.amount:
            priorities.enqueue(UnitTypeId.SPORECRAWLER, 10004)
        if ((self.state.get_unit_count(UnitTypeId.LAIR) >= 1 or self.state.get_unit_count(UnitTypeId.HIVE) >= 1)
            and self.state.get_unit_count(UnitTypeId.HYDRALISKDEN) < 1):
            priorities.enqueue(UnitTypeId.HYDRALISKDEN, 10005)
    
    def _hydra(self, priorities: PriorityQueue):
        if ((self.state.get_unit_count(UnitTypeId.LAIR) >= 1 or self.state.get_unit_count(UnitTypeId.HIVE) >= 1)
            and self.state.get_unit_count(UnitTypeId.HYDRALISKDEN) < 1):
            priorities.enqueue(UnitTypeId.HYDRALISKDEN, 10001)