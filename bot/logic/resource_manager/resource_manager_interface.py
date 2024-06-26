from typing import List

from sc2 import UnitTypeId

from bot.util.priority_queue import PriorityQueue

class ResourceManagerInterface:
    def get_spending_list(self, priorities: PriorityQueue) -> List[UnitTypeId]:
        raise NotImplementedError("Resource manager not implemented")
