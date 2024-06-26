from typing import List
import numpy as np
from collections import defaultdict
from enum import Enum

from sc2 import UnitTypeId

#from bot.logic.unit_manager.group_tactics import distance_from_boundary

'''Run this file to generate new weights (see below) rather than running every time the bot
    is started, since this function may become intensive as more variables are added on.'''

'''
unit_desperation_threshold : priority threshold before the given type of unit is considered to fight
    - all units not included in this mapping are always considered to fight

situations : A hard-coded matrix of values representing different situations in the game.
solutions : A list of the desired priority value for each of the solutions.

multiplier : Determines the kind of curve the effect of a variable should take. For example, 
if distance increases priority by a power of 2 (quadratic), use lambda x : x ** 2 to represent that.
    - x in the lambda is the variable in question, e.g. distance from nearest base or proportion army value.
priority_functions : The functions used to determine the variables considered in the situations.
    - All of these functions have group : UnitGroup and state : StateService as formal parameters.
'''
class PriorityType(Enum):
    ENEMY_GROUP = 0
    UNIT_TO_GROUP = 1

class PriorityInfo(Enum):
    SITUATIONS = 0
    SOLUTIONS = 1
    PRIORITIES = 2
    PRIORITY_FUNCTIONS = 3
    MULTIPLIER = 4

unit_desperation_threshold = defaultdict(lambda: 0,
{
    UnitTypeId.DRONE : 250,
    UnitTypeId.QUEEN : 180
})

def combine_priority_func_mult(priority_functions : list, multiplier : list) -> list:
    '''Combines multiplier functions with priority functions.'''
    return [lambda group, state : mult_func(prior_func(group, state)) for mult_func, prior_func in zip(multiplier, priority_functions)]

'''PriorityType.ENEMY_GROUP
        variables :
        0 -> proportion of enemy group value to enemy army value.
        1 -> distance of enemy group to nearest mining base or townhall.

    PriorityType.UNIT_TO_GROUP 
        variables :
        0 -> distance of unit to group boundary
'''
priority_info = {
    PriorityType.ENEMY_GROUP : {
        PriorityInfo.SITUATIONS : {
        0 : [0.8, 50], #general, large enemy army on own side of map
        1 : [0.5, 14] #general, decently sized enemy army within attacking range of base
        },
        PriorityInfo.SOLUTIONS : {
            0 : 100,
            1 : unit_desperation_threshold[UnitTypeId.DRONE]
        },
        PriorityInfo.PRIORITIES : [553.7870472008782, -0.13721185510428102],
        PriorityInfo.MULTIPLIER : [lambda x: x, lambda x: x**2],
        PriorityInfo.PRIORITY_FUNCTIONS : [
        lambda group, state : group.value/state.enemy_army_value,
        lambda group, state : group.location.distance_to_closest(state.own_townhalls.filter(lambda u: u.assigned_harvesters > 0))
        ]
    },
    PriorityType.UNIT_TO_GROUP : {
        PriorityInfo.SITUATIONS : {
            0 : [0],
            1 : [10]
        },
        PriorityInfo.SOLUTIONS : {
            0 : unit_desperation_threshold[UnitTypeId.DRONE],
            1 : 30
        },
        PriorityInfo.PRIORITIES : [],
        PriorityInfo.MULTIPLIER : [lambda x: x**3],
        PriorityInfo.PRIORITY_FUNCTIONS : [
            lambda u, g, s, *f : f[0](g.range_hull, u.position) #TODO fix this hack
        ]
    }
}

for priority_type in priority_info:
    funcs = priority_info[priority_type][PriorityInfo.PRIORITY_FUNCTIONS]
    mult = priority_info[priority_type][PriorityInfo.MULTIPLIER]
    priority_info[priority_type][PriorityInfo.PRIORITY_FUNCTIONS] = combine_priority_func_mult(funcs, mult)

def derive_new_weights(situations : dict, solutions : dict, multiplier) -> List[float]:
    def least_squares_approximation(situations, solutions):
        '''Uses least squares approximation method to scale
        constants as well as possible for all situations.'''
        A = np.array(situations)
        B = np.transpose(np.array([solutions]))
        return np.transpose(np.linalg.lstsq(A, B, None)[0]).tolist()[0]

    situations = [[multiplier[idx](val) for idx, val in enumerate(situation)] for situation in situations.values()]
    solutions = [solution for solution in solutions.values()]

    print('Situations : ', str(situations))
    print('Solutions : ', str(solutions))

    priorities = least_squares_approximation(situations, solutions)

    print('Priorities : ', str(priorities))

    return priorities

if __name__ == '__main__':
    print('Enemy group weights: ')
    situations = priority_info[PriorityType.ENEMY_GROUP][PriorityInfo.SITUATIONS]
    solutions = priority_info[PriorityType.ENEMY_GROUP][PriorityInfo.SOLUTIONS]
    multiplier = priority_info[PriorityType.ENEMY_GROUP][PriorityInfo.MULTIPLIER]
    derive_new_weights(situations, solutions, multiplier)

    print('Unit to group weights: ')
    situations = priority_info[PriorityType.UNIT_TO_GROUP][PriorityInfo.SITUATIONS]
    solutions = priority_info[PriorityType.UNIT_TO_GROUP][PriorityInfo.SOLUTIONS]
    multiplier = priority_info[PriorityType.UNIT_TO_GROUP][PriorityInfo.MULTIPLIER]
    derive_new_weights(situations, solutions, multiplier)