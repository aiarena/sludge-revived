from typing import Dict, List, Union
from collections import defaultdict

from sc2.unit_command import UnitCommand
from sc2.units import Units
from sc2.unit import Unit
from sc2.position import Point2

from ..util.priority_queue import PriorityQueue
import bot.injector as injector
from bot.services.state_service import StateService

class ActionService():
    def __init__(self, actions: Dict[str, PriorityQueue] = defaultdict(PriorityQueue)):
        self.state: StateService = injector.inject(StateService)
        self.actions: Dict[str, PriorityQueue] = actions
        self.repeat = []
    
    def add(self, tag, action: Union[UnitCommand, List[UnitCommand]], priority = 0):
        self.actions[tag].enqueue(action, priority)
        
    # returns the highest priority action for a given tag
    def get(self, tag: str) -> Union[UnitCommand, List[UnitCommand], None]:
        if tag in self.actions:
            actions = self.actions[tag].peek()
            return actions
        else:
            return None
    
    # returns the highest priority action for all tags
    def get_all(self) -> List[UnitCommand]:
        output = []
        for tag in self.actions.keys():
            actions = self.get(tag)
            if isinstance(actions, List):
                for a in actions:
                    output.append(a)
            else:
                output.append(actions)
        return output

    def clear(self):
        self.actions = defaultdict(PriorityQueue)

        to_remove = []
        for r in self.repeat:
            if self.state.own_units.find_by_tag(r[0]) and self.state.enemy_units.find_by_tag(r[1].target.tag):
                self.actions[r[0]].enqueue(r[1], r[2])
            else:
                to_remove.append(r)
        for r in to_remove:
            self.repeat.remove(r)
    
    def command_group(self, units: Units, command: UnitCommand, target: Union[Unit, Point2], priority = 0):
        for unit in units:
            self.add(unit.tag, unit(command, target), priority)

    def repeat_until_dead(self, tag: str, command: UnitCommand, priority = 0):
        self.actions[tag].enqueue(command, priority)
        self.repeat.append((tag, command, priority))