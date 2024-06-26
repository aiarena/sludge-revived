from typing import List

from sc2.unit_command import UnitCommand

from ...util.priority_queue import PriorityQueue

class SpendingActionsInterface():
    async def get_spending_actions(self, spending_priority: PriorityQueue) -> List[UnitCommand]:
        raise NotImplementedError("Get spending actions not implemented")