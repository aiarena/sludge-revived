from typing import List, Tuple
import numpy as np
import math
from collections import defaultdict

from sc2 import UnitTypeId

'''To add new data/variables: #TODO could use refactoring
    1. add the variable to "variables" class attribute in unit_manager_v2_lstsqr.py
    2. add the variable's multiplier function to the multiplier list for the type of priority (enemy group, unit to group, etc.)
    3. add a new list in the data for the type of priority (under the if __name__ == '__main__')
    4. Run the file (see below comments) and copy the given priority list and place it in the type of priority.
        - for example, if wanted to recalculate enemy group priority, run the file and copy it into the variable
        "enemy_group_priority"
'''

'''Run this file to generate new weights (see below) rather than running every time the bot
    is started, since this function may become intensive as more variables are added on.
    
unit_desperation_threshold : priority threshold before the given type of unit is considered to fight
    - all units not included in this mapping are always considered to fight
data : contains a list of variable-priority pairings for each variable being considered
    
multiplier : Determines the kind of curve a variable should take. For example, 
use lambda x : x ** 2 to represent distance because the priority for a close enemy
should be much more than a far enemy.
    - x in the lambda is the variable in question, e.g. distance from nearest base or proportion army value.'''

unit_desperation_threshold = defaultdict(lambda: 0,
{
    UnitTypeId.DRONE : 0.9,
    UnitTypeId.QUEEN : 0.6
})

def turn_list_to_linear_func(weights : [float, float], func : 'multiplier function') -> 'lambda':
    '''Turns a list [a, b] into a function of the form (a * func(x)) + b.'''
    return lambda x, a=weights[0], b=weights[1], c=func: a * c(x) + b

enemy_group_multipliers = [lambda x: math.log(x), lambda x: x]
unit_to_group_multipliers = [lambda x: math.log(x)]


if not __name__ == '__main__':
    '''Make sure to run this file and copy what it outputs to these variables.
    The value of these variables is used when the bot runs.'''
    #[[-68.3468428016, 287.3744213881], [100.0, -0.0]]
    enemy_group_priority = [[-43.4934454192, 190.1473590651], [100.0, -0.0]]
    enemy_group_priority = [turn_list_to_linear_func(weights, func) for weights, func in zip(enemy_group_priority, enemy_group_multipliers)]

    unit_to_group_priority = [[-166.5518726871, 605.1110995021]]
    unit_to_group_priority = [turn_list_to_linear_func(weights, func) for weights, func in zip(unit_to_group_priority, unit_to_group_multipliers)]
else:
    #data = (
    # [[value_of_variable, desired_priority_for_value]]
    # )
    def get_enemy_group_data():
        data = (
        [[50, 20], [10, (unit_desperation_threshold[UnitTypeId.QUEEN]/2)]],
        [[0.8, 80], [0.5, 50], [0.2, 20], [0, 0]]
        )
        multiplier = enemy_group_multipliers
        return data, multiplier

    def get_unit_group_data():
        data = (
            [[50, 1], [20, 20], 
            [10, unit_desperation_threshold[UnitTypeId.DRONE]], [2, 2*unit_desperation_threshold[UnitTypeId.DRONE]]],
        )
        multiplier = unit_to_group_multipliers
        return data, multiplier

    def least_squares_approximation(situations, solutions):
        '''Uses least squares approximation method to scale
        constants as well as possible for all situations.'''
        A = np.array(situations)
        B = np.transpose(np.array([solutions]))
        return np.transpose(np.linalg.lstsq(A, B, None)[0]).tolist()[0]

    def get_priority_values(data, multiplier):
        priority_values = []
        for idx, variable in enumerate(data):
            situations = []
            priorities = []
            for val, priority in variable:
                situations.append([multiplier[idx](val), 1]) #the 1 allows for a constant to be added/subtracted to help match the data better
                priorities.append(priority)

            priority_value = least_squares_approximation(situations, priorities)
            priority_values.append([round(val, 10) for val in priority_value]) #round so that numbers that are practically an int or 0 are that number (avoids certain issue with unit manager)

        return priority_values

    print('Enemy group priorities : ', str(get_priority_values(*get_enemy_group_data())))

    print('Unit to group priorities : ', str(get_priority_values(*get_unit_group_data())))

