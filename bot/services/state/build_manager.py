from typing import Dict, Union, Tuple

from sc2 import UnitTypeId, BotAI, Race
from sc2.units import Units
from sc2.unit import Unit
from sc2.game_data import UnitTypeData

from bot.services.state_service import StateService
from bot.model.scouting_information import ScoutingInformation
import bot.injector as injector
#TODO eliminate useless imports

class Build:
    '''Used to represent a reactionary build that can be switched to (and switched back from).'''
    def __init__(self, idx_val: int, check_prerequisites: 'func', check_complete: 'func', build_getter: 'func'):
        self.idx_val = idx_val
        self.check_prerequisites = check_prerequisites
        self.check_complete = check_complete
        self.build_getter = build_getter

class BuildManager():
    def __init__(self):
        self.state: StateService = injector.inject(StateService)

        self.build_switching: bool = True #disable if testing a specific build
        self.build_idx: int = 0 #used to prevent unnecessary recalculation/setting of build order and comp
        self.build_check_complete: 'func' = None
        self.possible_builds = {
            Build(1,
            lambda: self.state._bot.enemy_race == Race.Zerg and ScoutingInformation.ENEMY_THREE_BASE in self.state.scouting_information and self.state.resources.supply.used <= 52,
            lambda: ScoutingInformation.ENEMY_TWO_BASE in self.state.scouting_information or self.state.resources.supply.used >= 70,
            self.pressure_ling_bane),
            Build(2,
            lambda: False #self.state._bot.enemy_race == Race.Protoss and not self.enemy_has_natural_wall() and ScoutingInformation.ENEMY_TWO_BASE in self.state.scouting_information,
            ,
            lambda: ScoutingInformation.ENEMY_ONE_BASE in self.state.scouting_information or self.state.resources.supply.used >= 70 or self.enemy_has_natural_wall(),
            self.allin_speedling),
            Build(3,
            lambda: ScoutingInformation.ENEMY_ONE_BASE in self.state.scouting_information,
            lambda: not ScoutingInformation.ENEMY_ONE_BASE in self.state.scouting_information or self.state.resources.supply.used >= 70,
            self.defense_1base_roach)
        }

    _builds = {
        'standard_roach_hydra': 'zvall',
        'standard_roach_rav': 'zvz',
        'cheese_ling_bane': 'zvall',
        'pressure_ling_bane': 'zvz',
        'allin_speedling': 'zvp',
        'defense_1base_roach': 'zvall',
        'standard_hlb': 'zvall'
        }
    def __getattr__(self, name):
        '''Allows for self.{name of build} without having to write out a getter function for each build want to use.
        Just need to put the name of the build and its associated matchup in the above dictionary.'''
        #NOTE this might be inefficient, especially if rapid build order switching is taking place.
        #TODO can further reduce boilerplate by letting the bot automatically figure out where bos are and what their names are
        if name in self._builds:
            custom_globals = {}
            exec(f'from bot.logic.spending.build_order_v2.build_orders.{self._builds[name]}.{name} import build, comp', custom_globals)
            return custom_globals['build'], custom_globals['comp']
        else:
            raise AttributeError(f'build_manager.py.__getattr__: could not find attribute {name}')

    def first_iteration(self) -> ('build', 'comp'):
        '''Use starting build order. Called in on_first_iteration in State service.
        Also called as to return the default build order if on_step does not provide any special build orders.'''
        self.build_idx = 0
        self.build_check_complete = None

        #return self.cheese_ling_bane
        if self.state._bot.enemy_race == Race.Zerg:
            return self.standard_roach_rav
        elif self.state._bot.enemy_race == Race.Terran:
            return self.standard_roach_hydra
        elif self.state._bot.enemy_race == Race.Protoss:
            return self.standard_roach_hydra
        elif self.state._bot.enemy_race == Race.Random:
            return self.standard_roach_hydra

    def on_step(self) -> ('build', 'comp') or None:
        '''Checks to see if should change build order or comp.
        If they shouldn't be changed, return None.'''
        if self.build_switching:
            if self.build_check_complete is not None and not self.build_check_complete():
                return
            
            for build in self.possible_builds:
                if build.check_prerequisites() and not build.check_complete():
                    self.build_idx = build.idx_val
                    self.build_check_complete = build.check_complete
                    return build.build_getter
            
            #if shouldn't be using a conditional build order, then go back to the default (first iteration) build order
            if self.build_idx != 0:
                return self.first_iteration()

    '''Below are functions used in prerequisite/completion checking for conditional builds.'''

    def enemy_has_natural_wall(self) -> bool:
        '''Returns whether or not the enemy has a natural wall.'''
        pos = self.state.enemy_natural_position + 5 * self.state.enemy_natural_position.direction_vector(self.state.own_natural_position)
        enemy_structures = self.state.enemy_structures.closer_than(10, pos)
        amt = enemy_structures.amount if enemy_structures.exists else 0
        return amt >= 3